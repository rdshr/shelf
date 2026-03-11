const fs = require('node:fs');
const path = require('node:path');
const { app, BrowserWindow, Menu, Tray, globalShortcut, ipcMain, nativeImage, clipboard, screen, shell, dialog } = require('electron');

const { loadProjectConfig } = require('./lib/project-config');
const { captureSelectionImage, recognizeText, translateText } = require('./lib/local-pipeline');
const {
  ensureRuntimeOverridesTemplate,
  getPrimaryRuntimeOverridePath,
  loadRuntimeOverrides,
  writeRuntimeOverrides,
} = require('./lib/runtime-overrides');
const {
  OFFICIAL_OPENAI_BASE_URL,
  normalizeBaseUrl,
  resolveOpenAiApiKey,
  resolveOpenAiBaseUrl,
} = require('./lib/provider-runtime');
const { createWindowStateStore } = require('./lib/window-state');

app.setName('AiTrans');
const stateNamespace = 'AiTrans';

function resolveLogFilePath() {
  const appData = process.env.APPDATA || process.env.LOCALAPPDATA;
  const baseDir = appData
    ? path.join(appData, 'AiTrans', 'logs')
    : path.join(__dirname, '.runtime-logs');
  fs.mkdirSync(baseDir, { recursive: true });
  return path.join(baseDir, 'main.log');
}

function appendStartupLog(message, extra) {
  const logFile = resolveLogFilePath();
  const line = `[${new Date().toISOString()}] ${message}${extra ? ` ${JSON.stringify(extra)}` : ''}\n`;
  fs.appendFileSync(logFile, line, 'utf-8');
}

let config;
try {
  appendStartupLog('boot:loadProjectConfig:start');
  config = loadProjectConfig();
  appendStartupLog('boot:loadProjectConfig:ok', { generatedDir: config.generatedDir });
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  appendStartupLog('boot:loadProjectConfig:failed', { message });
  dialog.showErrorBox('AiTrans startup failed', `${message}\n\n日志位置：${resolveLogFilePath()}`);
  throw error;
}

const stateStore = createWindowStateStore(app, stateNamespace);

app.setAppUserModelId('com.aitrans.desktop_screenshot_translate');

let tray = null;
let overlayWindow = null;
let panelWindow = null;
let setupWindow = null;
let lastSelection = null;
let lastPipelineState = null;
let runtimeBootstrap = null;
const CAPTURE_SETTLE_MS = 180;
const RETRYABLE_OCR_ERROR_FRAGMENT = 'tesseract returned empty OCR text';

process.on('uncaughtException', (error) => {
  appendStartupLog('process:uncaughtException', { message: error.message, stack: error.stack });
});

process.on('unhandledRejection', (reason) => {
  const message = reason instanceof Error ? reason.message : String(reason);
  const stack = reason instanceof Error ? reason.stack : null;
  appendStartupLog('process:unhandledRejection', { message, stack });
});

function getWindowIconPath() {
  return path.join(__dirname, 'assets', 'app-icon.ico');
}

function createTrayImage() {
  const iconPath = path.join(__dirname, 'assets', 'tray-icon@2x.png');
  const image = nativeImage.createFromPath(iconPath);
  if (image.isEmpty()) {
    return nativeImage.createEmpty();
  }
  return image.resize({ width: 16, height: 16, quality: 'best' });
}

function getOverlayDisplay() {
  return screen.getDisplayNearestPoint(screen.getCursorScreenPoint());
}

function createOverlayWindow() {
  const display = getOverlayDisplay();
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.setBounds(display.bounds);
    return overlayWindow;
  }

  overlayWindow = new BrowserWindow({
    x: display.bounds.x,
    y: display.bounds.y,
    width: display.bounds.width,
    height: display.bounds.height,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    movable: false,
    resizable: false,
    fullscreenable: false,
    backgroundColor: '#00000000',
    icon: getWindowIconPath(),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  overlayWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
  overlayWindow.setAlwaysOnTop(true, 'screen-saver');
  overlayWindow.loadFile(path.join(__dirname, 'renderer', 'overlay', 'index.html'));
  overlayWindow.on('closed', () => {
    overlayWindow = null;
  });
  return overlayWindow;
}

function createPanelWindow() {
  const savedState = stateStore.load().panel;
  if (panelWindow && !panelWindow.isDestroyed()) {
    return panelWindow;
  }

  panelWindow = new BrowserWindow({
    width: savedState?.width || 440,
    height: savedState?.height || 360,
    x: savedState?.x,
    y: savedState?.y,
    show: false,
    frame: false,
    transparent: false,
    resizable: true,
    movable: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    backgroundColor: '#f4f8f6',
    icon: getWindowIconPath(),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  panelWindow.loadFile(path.join(__dirname, 'renderer', 'panel-dist', 'index.html'));
  panelWindow.webContents.on('did-fail-load', (_event, code, description, validatedUrl) => {
    console.error('[panel] load failed', { code, description, validatedUrl });
  });
  panelWindow.webContents.on('render-process-gone', (_event, details) => {
    console.error('[panel] render process gone', details);
  });
  panelWindow.on('close', (event) => {
    if (!app.isQuitting) {
      event.preventDefault();
      panelWindow.hide();
    }
  });
  panelWindow.on('moved', savePanelBounds);
  panelWindow.on('resized', savePanelBounds);
  panelWindow.on('closed', () => {
    panelWindow = null;
  });
  return panelWindow;
}

function createSetupWindow() {
  if (setupWindow && !setupWindow.isDestroyed()) {
    return setupWindow;
  }

  setupWindow = new BrowserWindow({
    width: 560,
    height: 620,
    show: false,
    resizable: false,
    minimizable: false,
    maximizable: false,
    autoHideMenuBar: true,
    title: `${config.productSpec.project.display_name} 首次配置`,
    backgroundColor: '#ecf8f4',
    icon: getWindowIconPath(),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  setupWindow.loadFile(path.join(__dirname, 'renderer', 'setup', 'index.html'));
  setupWindow.on('closed', () => {
    setupWindow = null;
  });
  return setupWindow;
}

function savePanelBounds() {
  if (!panelWindow || panelWindow.isDestroyed()) {
    return;
  }
  stateStore.save('panel', panelWindow.getBounds());
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function hideAuxiliaryWindowsForCapture() {
  if (setupWindow && !setupWindow.isDestroyed() && setupWindow.isVisible()) {
    setupWindow.hide();
  }
  if (panelWindow && !panelWindow.isDestroyed() && panelWindow.isVisible()) {
    panelWindow.hide();
  }
}

async function settleBeforeCapture() {
  await sleep(CAPTURE_SETTLE_MS);
}

function isRetryableOcrFailure(error) {
  const message = error instanceof Error ? error.message : String(error);
  return message.includes(RETRYABLE_OCR_ERROR_FRAGMENT);
}

async function captureAndRecognize(selection) {
  await settleBeforeCapture();
  let capture = await captureSelectionImage(selection);
  try {
    const ocrResult = await recognizeText(capture, config.productSpec, config.implementationConfig);
    return { capture, ocrResult, retries: 0 };
  } catch (error) {
    if (!isRetryableOcrFailure(error)) {
      throw error;
    }

    await settleBeforeCapture();
    capture = await captureSelectionImage(selection);
    const ocrResult = await recognizeText(capture, config.productSpec, config.implementationConfig);
    return { capture, ocrResult, retries: 1 };
  }
}

function showOverlay() {
  const display = getOverlayDisplay();
  const window = createOverlayWindow();
  hideAuxiliaryWindowsForCapture();
  window.setBounds(display.bounds);
  window.show();
  window.focus();

  const payload = {
    hint: config.productSpec.surface.copy.capture_hint,
    display,
    modes: config.productSpec.capture.modes,
  };
  if (window.webContents.isLoadingMainFrame()) {
    window.webContents.once('did-finish-load', () => {
      window.webContents.send('overlay:start', payload);
    });
  } else {
    window.webContents.send('overlay:start', payload);
  }
}

function buildStubResult(selection) {
  return {
    sourceText: '等待本地主链输出结果。',
    translatedText: '纯 Electron 主链已启用，下一次截图会进入本地截图、OCR 和翻译 provider 流程。',
    stageStatus: 'idle',
    errorOrigin: null,
    selection,
    shortcut: config.shortcut,
    capturePreviewDataUrl: null,
    captureMeta: null,
  };
}

function buildStageResult(selection, overrides = {}) {
  return {
    ...buildStubResult(selection),
    ...overrides,
  };
}

function getSetupGuideState() {
  const overrides = loadRuntimeOverrides();
  const baseUrl = resolveOpenAiBaseUrl();
  const translationOverrides =
    overrides.values && typeof overrides.values.translation === 'object'
      ? overrides.values.translation
      : {};
  let configured = true;
  let credentialMode = 'configured';

  try {
    const apiKey = resolveOpenAiApiKey(baseUrl);
    if (!apiKey && baseUrl !== OFFICIAL_OPENAI_BASE_URL) {
      credentialMode = 'local_endpoint_without_key';
    }
  } catch {
    configured = false;
    credentialMode = 'missing_translation_credential';
  }

  return {
    configured,
    credentialMode,
    baseUrl,
    usingOfficialEndpoint: baseUrl === OFFICIAL_OPENAI_BASE_URL,
    runtimeOverridesPath: overrides.path || getPrimaryRuntimeOverridePath(),
    runtimeOverridesDetected: Boolean(overrides.path),
    bootstrapCreated: Boolean(runtimeBootstrap?.created),
    runtimeDraft: {
      baseUrl:
        typeof translationOverrides.base_url === 'string'
          ? translationOverrides.base_url
          : '',
      apiKeyPresent:
        typeof translationOverrides.api_key === 'string'
        && translationOverrides.api_key.trim().length > 0,
    },
  };
}

function getActiveRuntimeOverridePath() {
  return loadRuntimeOverrides().path || getPrimaryRuntimeOverridePath();
}

function showSetupGuide() {
  const window = createSetupWindow();
  const payload = {
    product: {
      displayName: config.productSpec.project.display_name,
    },
    guide: getSetupGuideState(),
  };

  const sendPayload = () => {
    window.webContents.send('setup:set-data', payload);
    window.show();
    window.focus();
  };

  if (window.webContents.isLoadingMainFrame()) {
    window.webContents.once('did-finish-load', sendPayload);
  } else {
    sendPayload();
  }
}

function showPanel(result) {
  const window = createPanelWindow();
  const payload = {
    product: {
      displayName: config.productSpec.project.display_name,
      presentation: config.productSpec.presentation,
      copy: config.productSpec.presentation.copy,
    },
    result,
  };

  const sendPayload = () => {
    window.webContents.send('panel:set-data', payload);
    window.show();
    window.focus();
  };

  if (window.webContents.isLoadingMainFrame()) {
    window.webContents.once('did-finish-load', sendPayload);
  } else {
    sendPayload();
  }
}

function rememberPipelineState(selection, capture, ocrResult, translatedText, translationDiagnostics) {
  lastPipelineState = {
    selection,
    sourceText: ocrResult?.text?.trim() || '',
    capturePreviewDataUrl: capture?.dataUrl || null,
    captureMeta: {
      width: capture?.size?.width || null,
      height: capture?.size?.height || null,
      targetLanguage: config.productSpec.pipeline.target_language,
      ocrProvider: ocrResult?.provider || null,
      translationProvider: translationDiagnostics?.provider || null,
      ocrDiagnostics: ocrResult?.diagnostics || null,
      translationDiagnostics: translationDiagnostics?.diagnostics || null,
    },
    translatedText: translatedText || '',
  };
}

function createTray() {
  tray = new Tray(createTrayImage());
  tray.setToolTip(config.productSpec.project.display_name);
  appendStartupLog('tray:created');
  const menu = Menu.buildFromTemplate([
    { label: '开始截图翻译', click: () => showOverlay() },
    { label: `快捷键：${config.shortcut}`, enabled: false },
    { type: 'separator' },
    { label: '显示结果面板', click: () => showPanel(buildStubResult(lastSelection || getFallbackSelection())) },
    { label: '首次配置指引', click: () => showSetupGuide() },
    { label: '打开配置目录', click: () => shell.openPath(path.dirname(getActiveRuntimeOverridePath())) },
    { type: 'separator' },
    { label: '退出', click: () => { app.isQuitting = true; app.quit(); } },
  ]);
  tray.setContextMenu(menu);
  tray.on('click', () => showOverlay());
}

function getFallbackSelection() {
  const display = getOverlayDisplay();
  return {
    displayId: display.id,
    x: display.bounds.x + 160,
    y: display.bounds.y + 140,
    width: 360,
    height: 220,
    scaleFactor: display.scaleFactor,
  };
}

function registerShortcuts() {
  globalShortcut.register(config.shortcut, () => {
    showOverlay();
  });
}

ipcMain.handle('overlay:submit-selection', async (_event, selection) => {
  lastSelection = selection;
  lastPipelineState = null;
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.hide();
  }
  try {
    showPanel(buildStageResult(selection, {
      stageStatus: 'capturing',
      sourceText: '正在抓取选区位图…',
      translatedText: '正在从 Windows 桌面获取截图区域，请稍候。',
    }));

    const { capture, ocrResult, retries } = await captureAndRecognize(selection);
    showPanel(buildStageResult(selection, {
      stageStatus: 'ocr_processing',
      sourceText: retries > 0 ? '截图已稳定，正在执行本地 OCR…' : '截图完成，正在执行本地 OCR…',
      translatedText: retries > 0 ? '首次识别未返回文本，已自动重试一次并继续…' : 'OCR 完成后将进入翻译阶段…',
      capturePreviewDataUrl: capture.dataUrl,
      captureMeta: {
        width: capture.size.width,
        height: capture.size.height,
        targetLanguage: config.productSpec.pipeline.target_language,
        ocrProvider: 'pending',
        translationProvider: config.implementationConfig.providers.translation_chain[0],
        autoRetryCount: retries,
      },
    }));
    const recognizedText = ocrResult.text.trim();
    rememberPipelineState(selection, capture, ocrResult, '', null);

    showPanel(buildStageResult(selection, {
      stageStatus: 'translation_processing',
      sourceText: recognizedText || 'OCR 未返回可用文本。',
      translatedText: '正在调用翻译 provider…',
      capturePreviewDataUrl: capture.dataUrl,
      captureMeta: {
        width: capture.size.width,
        height: capture.size.height,
        targetLanguage: config.productSpec.pipeline.target_language,
        ocrProvider: ocrResult.provider,
        translationProvider: 'pending',
        ocrDiagnostics: ocrResult.diagnostics || null,
        autoRetryCount: retries,
      },
    }));

    const translationResult = await translateText(
      recognizedText,
      config.productSpec,
      config.implementationConfig,
    );
    rememberPipelineState(selection, capture, ocrResult, translationResult.translatedText, translationResult);

    const result = buildStageResult(selection, {
      stageStatus: 'translation_ready',
      sourceText: recognizedText,
      translatedText: translationResult.translatedText,
      capturePreviewDataUrl: capture.dataUrl,
      captureMeta: {
        width: capture.size.width,
        height: capture.size.height,
        targetLanguage: config.productSpec.pipeline.target_language,
        ocrProvider: ocrResult.provider,
        translationProvider: translationResult.provider,
        ocrDiagnostics: ocrResult.diagnostics || null,
        translationDiagnostics: translationResult.diagnostics || null,
        autoRetryCount: retries,
      },
    });
    showPanel(result);
    return { ok: true };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    const failureResult = {
      ...(lastPipelineState
        ? buildStageResult(lastPipelineState.selection || selection, {
            sourceText: lastPipelineState.sourceText || '等待本地主链输出结果。',
            capturePreviewDataUrl: lastPipelineState.capturePreviewDataUrl,
            captureMeta: lastPipelineState.captureMeta,
          })
        : buildStubResult(selection)),
      stageStatus: 'failed',
      translatedText: 'OCR 或翻译主链执行失败，请检查 desktopCapturer、内置或外部 tesseract、OPENAI_API_KEY、AITRANS_OPENAI_BASE_URL 或当前 Windows 权限状态。',
      errorOrigin: message,
    };
    showPanel(failureResult);
    return { ok: false, error: message };
  }
});

ipcMain.handle('overlay:cancel', async () => {
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.hide();
  }
  return { ok: true };
});

ipcMain.handle('panel:copy-translation', async (_event, payload) => {
  clipboard.writeText(payload.text || '');
  return { ok: true };
});

ipcMain.handle('panel:close', async () => {
  if (panelWindow && !panelWindow.isDestroyed()) {
    panelWindow.hide();
  }
  return { ok: true };
});

ipcMain.handle('panel:recapture', async () => {
  showOverlay();
  return { ok: true };
});

ipcMain.handle('panel:retry-translation', async () => {
  if (!lastPipelineState || !lastPipelineState.sourceText) {
    return { ok: false, error: 'missing OCR source text for retry' };
  }

  try {
    showPanel(buildStageResult(lastPipelineState.selection || getFallbackSelection(), {
      stageStatus: 'translation_processing',
      sourceText: lastPipelineState.sourceText,
      translatedText: '正在重新调用翻译 provider…',
      capturePreviewDataUrl: lastPipelineState.capturePreviewDataUrl,
      captureMeta: {
        ...lastPipelineState.captureMeta,
        translationProvider: 'pending',
      },
    }));

    const translationResult = await translateText(
      lastPipelineState.sourceText,
      config.productSpec,
      config.implementationConfig,
    );

    rememberPipelineState(
      lastPipelineState.selection || getFallbackSelection(),
      { dataUrl: lastPipelineState.capturePreviewDataUrl, size: { width: lastPipelineState.captureMeta?.width, height: lastPipelineState.captureMeta?.height } },
      {
        provider: lastPipelineState.captureMeta?.ocrProvider,
        diagnostics: lastPipelineState.captureMeta?.ocrDiagnostics || null,
        text: lastPipelineState.sourceText,
      },
      translationResult.translatedText,
      translationResult,
    );

    showPanel(buildStageResult(lastPipelineState.selection || getFallbackSelection(), {
      stageStatus: 'translation_ready',
      sourceText: lastPipelineState.sourceText,
      translatedText: translationResult.translatedText,
      capturePreviewDataUrl: lastPipelineState.capturePreviewDataUrl,
      captureMeta: {
        ...lastPipelineState.captureMeta,
        translationProvider: translationResult.provider,
        translationDiagnostics: translationResult.diagnostics || null,
      },
    }));
    return { ok: true };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    showPanel(buildStageResult(lastPipelineState.selection || getFallbackSelection(), {
      stageStatus: 'failed',
      sourceText: lastPipelineState.sourceText,
      translatedText: config.productSpec.presentation.copy.failure_title,
      capturePreviewDataUrl: lastPipelineState.capturePreviewDataUrl,
      captureMeta: lastPipelineState.captureMeta,
      errorOrigin: message,
    }));
    return { ok: false, error: message };
  }
});

ipcMain.handle('panel:get-project-summary', async () => {
  return {
    displayName: config.productSpec.project.display_name,
    shortcut: config.shortcut,
    pipeline: config.productSpec.pipeline,
    governance: config.productSpec.governance,
  };
});

ipcMain.handle('setup:get-guide-state', async () => {
  return getSetupGuideState();
});

ipcMain.handle('setup:open-config-directory', async () => {
  const configDir = path.dirname(getActiveRuntimeOverridePath());
  await shell.openPath(configDir);
  return { ok: true, configDir };
});

ipcMain.handle('setup:open-config-file', async () => {
  const configPath = getActiveRuntimeOverridePath();
  await shell.openPath(configPath);
  return { ok: true, configPath };
});

ipcMain.handle('setup:copy-config-path', async () => {
  const configPath = getActiveRuntimeOverridePath();
  clipboard.writeText(configPath);
  return { ok: true, configPath };
});

ipcMain.handle('setup:save-config', async (_event, payload) => {
  const baseUrlInput =
    payload && typeof payload.baseUrl === 'string'
      ? payload.baseUrl.trim()
      : '';
  const apiKeyInput =
    payload && typeof payload.apiKey === 'string'
      ? payload.apiKey.trim()
      : '';

  if (!baseUrlInput) {
    return { ok: false, error: 'missing translation.base_url' };
  }

  const normalizedBaseUrl = normalizeBaseUrl(baseUrlInput);
  if (normalizedBaseUrl === OFFICIAL_OPENAI_BASE_URL && !apiKeyInput) {
    return { ok: false, error: 'official OpenAI endpoint requires api_key' };
  }

  const currentValues = loadRuntimeOverrides().values;
  const saved = writeRuntimeOverrides({
    ...currentValues,
    translation: {
      ...(currentValues.translation && typeof currentValues.translation === 'object'
        ? currentValues.translation
        : {}),
      base_url: normalizedBaseUrl,
      api_key: apiKeyInput,
    },
  });

  appendStartupLog('setup-guide:config-saved', {
    configPath: saved.path,
    usingOfficialEndpoint: normalizedBaseUrl === OFFICIAL_OPENAI_BASE_URL,
    apiKeyPresent: Boolean(apiKeyInput),
  });

  return {
    ok: true,
    configPath: saved.path,
    guide: getSetupGuideState(),
  };
});

ipcMain.handle('setup:close', async () => {
  if (setupWindow && !setupWindow.isDestroyed()) {
    setupWindow.close();
  }
  return { ok: true };
});

app.whenReady().then(() => {
  appendStartupLog('app:ready');
  runtimeBootstrap = ensureRuntimeOverridesTemplate();
  appendStartupLog('runtime-overrides:bootstrap', runtimeBootstrap);
  createTray();
  createPanelWindow();
  registerShortcuts();
  if (!getSetupGuideState().configured) {
    appendStartupLog('setup-guide:auto-open');
    showSetupGuide();
  }
});

app.on('activate', () => {
  if (!panelWindow || panelWindow.isDestroyed()) {
    createPanelWindow();
  }
});

app.on('will-quit', () => {
  app.isQuitting = true;
  globalShortcut.unregisterAll();
});

app.on('window-all-closed', () => {
  // Keep the tray app alive; explicit quit is exposed via tray menu.
});
