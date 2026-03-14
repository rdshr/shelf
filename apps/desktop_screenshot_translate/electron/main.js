const fs = require('node:fs');
const crypto = require('node:crypto');
const path = require('node:path');
const { app, BrowserWindow, Menu, Tray, globalShortcut, ipcMain, nativeImage, clipboard, screen, shell, dialog } = require('electron');

const { loadProjectConfig } = require('./lib/project-config');
const {
  captureSelectionImage,
  probeScreenCaptureCapability,
  recognizeText,
  translateText,
} = require('./lib/local-pipeline');
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
const {
  isWindowsFocusSupported,
  restoreForegroundWindow,
  snapshotForegroundWindow,
} = require('./lib/windows-focus');
const { createAutoUpdateRuntime } = require('./lib/update-runtime');

app.setName('AiTrans');
const stateNamespace = 'AiTrans';
const singleInstanceLock = app.requestSingleInstanceLock();

if (!singleInstanceLock) {
  app.quit();
  process.exit(0);
}

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

function resolveEventLogFilePath() {
  const appData = process.env.APPDATA || process.env.LOCALAPPDATA;
  const baseDir = appData
    ? path.join(appData, 'AiTrans', 'logs')
    : path.join(__dirname, '.runtime-logs');
  fs.mkdirSync(baseDir, { recursive: true });
  return path.join(baseDir, 'pipeline-events.jsonl');
}

function appendPipelineEvent(eventName, audit, details = {}) {
  const record = {
    timestamp: new Date().toISOString(),
    event_name: eventName,
    capture_session_id: audit?.captureSessionId || null,
    task_id: audit?.taskId || null,
    provider: details.provider || null,
    result_state: details.resultState || null,
    stage_status: details.stageStatus || null,
    source_language: details.sourceLanguage || null,
    shortcut: currentCaptureShortcut || config?.shortcut || null,
    details,
  };
  fs.appendFileSync(resolveEventLogFilePath(), `${JSON.stringify(record)}\n`, 'utf-8');
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
let currentCaptureShortcut = null;
let updateRuntime = null;
const runtimeCapabilities = {
  shortcutAvailable: null,
  shortcutMessage: null,
  screenCaptureAvailable: null,
  screenCaptureMessage: null,
  entryMode: 'tray_and_shortcut',
};
const focusRestoreState = {
  target: null,
  preferInactivePanel: false,
};
const captureUiState = {
  overlayVisible: false,
  pipelineBusy: false,
};
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

function createAuditContext(selection) {
  return {
    captureSessionId: `capture_${crypto.randomUUID()}`,
    taskId: `task_${crypto.randomUUID()}`,
    selection,
    startedAt: Date.now(),
  };
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
  overlayWindow.on('show', () => {
    captureUiState.overlayVisible = true;
  });
  overlayWindow.on('hide', () => {
    captureUiState.overlayVisible = false;
  });
  overlayWindow.on('closed', () => {
    captureUiState.overlayVisible = false;
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
    width: savedState?.width || 560,
    height: savedState?.height || 420,
    minWidth: 480,
    minHeight: 340,
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

function focusBestAvailableWindow() {
  clearFocusRestoreSession();
  if (setupWindow && !setupWindow.isDestroyed()) {
    setupWindow.show();
    setupWindow.focus();
    return;
  }
  if (panelWindow && !panelWindow.isDestroyed()) {
    panelWindow.show();
    panelWindow.focus();
    return;
  }
  if (!getSetupGuideState().configured) {
    showSetupGuide();
    return;
  }
  showPanel(buildStubResult(lastSelection || getFallbackSelection()));
}

function setShortcutCapability(available, message = null) {
  runtimeCapabilities.shortcutAvailable = available;
  runtimeCapabilities.shortcutMessage = message;
  runtimeCapabilities.entryMode = available ? 'tray_and_shortcut' : 'tray_only';
}

function setScreenCaptureCapability(available, message = null) {
  runtimeCapabilities.screenCaptureAvailable = available;
  runtimeCapabilities.screenCaptureMessage = message;
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

function isFocusRestoreEnabled() {
  return Boolean(config.productSpec.desktop.focus_restore) && isWindowsFocusSupported();
}

function clearFocusRestoreSession() {
  focusRestoreState.target = null;
  focusRestoreState.preferInactivePanel = false;
}

async function captureExternalFocusTarget() {
  if (!isFocusRestoreEnabled()) {
    clearFocusRestoreSession();
    return;
  }

  try {
    const snapshot = await snapshotForegroundWindow(process.pid);
    if (!snapshot || snapshot.isCurrentProcess) {
      clearFocusRestoreSession();
      appendStartupLog('focus-restore:snapshot-skipped', {
        reason: snapshot?.isCurrentProcess ? 'foreground_is_aitrans' : 'no_foreground_window',
      });
      return;
    }

    focusRestoreState.target = {
      hwnd: snapshot.hwnd,
      pid: snapshot.pid,
    };
    focusRestoreState.preferInactivePanel = true;
    appendStartupLog('focus-restore:snapshot-captured', {
      hwnd: snapshot.hwnd,
      pid: snapshot.pid,
    });
  } catch (error) {
    clearFocusRestoreSession();
    appendStartupLog('focus-restore:snapshot-failed', {
      message: error instanceof Error ? error.message : String(error),
    });
  }
}

async function restoreCapturedFocusTarget(reason) {
  if (!isFocusRestoreEnabled() || !focusRestoreState.target) {
    return false;
  }

  try {
    const outcome = await restoreForegroundWindow(focusRestoreState.target);
    appendStartupLog('focus-restore:restore-attempt', {
      reason,
      target: focusRestoreState.target,
      outcome,
    });
    if (outcome.ok || outcome.reason === 'missing_window') {
      focusRestoreState.target = null;
    }
    return Boolean(outcome.ok);
  } catch (error) {
    appendStartupLog('focus-restore:restore-failed', {
      reason,
      message: error instanceof Error ? error.message : String(error),
    });
    return false;
  }
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

function resolveConfiguredCaptureShortcut() {
  const overrides = loadRuntimeOverrides().values;
  const configuredShortcut = (
    process.env.AITRANS_CAPTURE_SHORTCUT
    || overrides.desktop?.capture_shortcut
    || config.shortcut
    || 'CommandOrControl+Shift+1'
  ).trim();
  return configuredShortcut || 'CommandOrControl+Shift+1';
}

function buildTrayMenu() {
  const updateState = updateRuntime ? updateRuntime.getState() : null;
  return Menu.buildFromTemplate([
    { label: '开始截图翻译', click: () => showOverlay() },
    {
      label: runtimeCapabilities.shortcutAvailable === false
        ? '快捷键暂不可用，已降级为托盘入口'
        : `快捷键：${currentCaptureShortcut || config.shortcut}`,
      enabled: false,
    },
    { type: 'separator' },
    { label: '显示结果面板', click: () => showPanel(buildStubResult(lastSelection || getFallbackSelection())) },
    { label: '首次配置指引', click: () => showSetupGuide() },
    { label: '打开配置目录', click: () => shell.openPath(path.dirname(getActiveRuntimeOverridePath())) },
    { type: 'separator' },
    {
      label: updateRuntime ? updateRuntime.getTrayStatusLabel() : '自动更新：未初始化',
      enabled: false,
    },
    {
      label: '检查更新',
      enabled: Boolean(updateState?.enabled || config.implementationConfig.release.auto_update),
      click: async () => {
        if (!updateRuntime) {
          return;
        }
        const outcome = await updateRuntime.checkForUpdates(true);
        if (!outcome.ok && outcome.error) {
          dialog.showErrorBox('AiTrans 检查更新失败', outcome.error);
        }
      },
    },
    {
      label: '安装已下载更新',
      enabled: Boolean(updateState?.updateDownloaded),
      click: () => {
        if (!updateRuntime) {
          return;
        }
        const outcome = updateRuntime.installDownloadedUpdate();
        if (!outcome.ok && outcome.error) {
          dialog.showErrorBox('AiTrans 安装更新失败', outcome.error);
        }
      },
    },
    { type: 'separator' },
    { label: '退出', click: () => { app.isQuitting = true; app.quit(); } },
  ]);
}

function refreshTrayMenu() {
  if (!tray) {
    return;
  }
  tray.setContextMenu(buildTrayMenu());
}

function applyCaptureShortcut(nextShortcut) {
  const normalized = (nextShortcut || '').trim() || 'CommandOrControl+Shift+1';
  const previousShortcut = currentCaptureShortcut || config.shortcut || 'CommandOrControl+Shift+1';

  globalShortcut.unregisterAll();

  try {
    const registered = globalShortcut.register(normalized, () => {
      showOverlay();
    });
    if (!registered) {
      throw new Error('shortcut registration was rejected by the operating system');
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    if (previousShortcut && previousShortcut !== normalized) {
      try {
        const fallbackRegistered = globalShortcut.register(previousShortcut, () => {
          showOverlay();
        });
        if (fallbackRegistered) {
          currentCaptureShortcut = previousShortcut;
          config.shortcut = previousShortcut;
          setShortcutCapability(true, null);
          refreshTrayMenu();
          return { ok: false, error: `invalid shortcut: ${message}` };
        }
      } catch {
        // fall through to degraded tray-only mode
      }
    }
    currentCaptureShortcut = null;
    setShortcutCapability(false, message);
    refreshTrayMenu();
    return { ok: false, error: `invalid shortcut: ${message}` };
  }

  currentCaptureShortcut = normalized;
  config.shortcut = normalized;
  setShortcutCapability(true, null);
  refreshTrayMenu();
  return { ok: true, shortcut: normalized };
}

async function probeAndStoreScreenCaptureCapability() {
  const probe = await probeScreenCaptureCapability();
  setScreenCaptureCapability(Boolean(probe.available), probe.reason || null);
  if (!probe.available) {
    appendStartupLog('capture:probe-failed', { message: probe.reason || 'unknown capture error' });
  }
  return probe;
}

async function ensureScreenCaptureCapability() {
  if (runtimeCapabilities.screenCaptureAvailable === true) {
    return true;
  }
  const probe = await probeAndStoreScreenCaptureCapability();
  return Boolean(probe.available);
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

async function showOverlay() {
  if (captureUiState.overlayVisible || captureUiState.pipelineBusy) {
    appendStartupLog('overlay:show-skipped', {
      overlayVisible: captureUiState.overlayVisible,
      pipelineBusy: captureUiState.pipelineBusy,
    });
    return;
  }
  if (!(await ensureScreenCaptureCapability())) {
    showSetupGuide();
    return;
  }
  await captureExternalFocusTarget();
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
    sourceLanguage: 'auto',
    stageStatus: 'idle',
    errorOrigin: null,
    selection,
    shortcut: currentCaptureShortcut || config.shortcut,
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
  const desktopOverrides =
    overrides.values && typeof overrides.values.desktop === 'object'
      ? overrides.values.desktop
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
    desktopDraft: {
      captureShortcut:
        typeof desktopOverrides.capture_shortcut === 'string' && desktopOverrides.capture_shortcut.trim()
          ? desktopOverrides.capture_shortcut.trim()
          : currentCaptureShortcut || config.shortcut,
    },
    capabilities: {
      shortcutAvailable: runtimeCapabilities.shortcutAvailable !== false,
      shortcutMessage: runtimeCapabilities.shortcutMessage,
      screenCaptureAvailable: runtimeCapabilities.screenCaptureAvailable !== false,
      screenCaptureMessage: runtimeCapabilities.screenCaptureMessage,
      entryMode: runtimeCapabilities.entryMode,
    },
  };
}

function shouldAutoOpenSetupGuide() {
  const guide = getSetupGuideState();
  return (
    !guide.configured
    || guide.capabilities.shortcutAvailable === false
    || guide.capabilities.screenCaptureAvailable === false
  );
}

function getActiveRuntimeOverridePath() {
  return loadRuntimeOverrides().path || getPrimaryRuntimeOverridePath();
}

function showSetupGuide() {
  clearFocusRestoreSession();
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
    if (focusRestoreState.preferInactivePanel && typeof window.showInactive === 'function') {
      window.showInactive();
      return;
    }
    window.show();
    window.focus();
  };

  if (window.webContents.isLoadingMainFrame()) {
    window.webContents.once('did-finish-load', sendPayload);
  } else {
    sendPayload();
  }
}

function rememberPipelineState(selection, capture, ocrResult, translatedText, translationDiagnostics, audit) {
  lastPipelineState = {
    selection,
    sourceText: ocrResult?.text?.trim() || '',
    sourceLanguage: ocrResult?.sourceLanguage || 'auto',
    capturePreviewDataUrl: capture?.dataUrl || null,
    captureMeta: {
      width: capture?.size?.width || null,
      height: capture?.size?.height || null,
      targetLanguage: config.productSpec.pipeline.target_language,
      captureSessionId: audit?.captureSessionId || null,
      taskId: audit?.taskId || null,
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
  refreshTrayMenu();
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
  const result = applyCaptureShortcut(resolveConfiguredCaptureShortcut());
  if (!result.ok) {
    throw new Error(result.error);
  }
}

ipcMain.handle('overlay:submit-selection', async (_event, selection) => {
  lastSelection = selection;
  lastPipelineState = null;
  const audit = createAuditContext(selection);
  captureUiState.pipelineBusy = true;
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.hide();
  }
  await restoreCapturedFocusTarget('capture_submitted');
  try {
    appendPipelineEvent('capture_started', audit, {
      resultState: 'capturing',
      stageStatus: 'capturing',
    });
    showPanel(buildStageResult(selection, {
      sourceLanguage: 'auto',
      stageStatus: 'capturing',
      sourceText: '正在抓取选区位图…',
      translatedText: '正在从 Windows 桌面获取截图区域，请稍候。',
    }));

    const { capture, ocrResult, retries } = await captureAndRecognize(selection);
    appendPipelineEvent('capture_completed', audit, {
      resultState: 'captured',
      stageStatus: 'capturing',
    });
    appendPipelineEvent('ocr_requested', audit, {
      provider: config.implementationConfig.providers.ocr_chain[0],
      resultState: 'ocr_processing',
      stageStatus: 'ocr_processing',
    });
    showPanel(buildStageResult(selection, {
      sourceLanguage: ocrResult.sourceLanguage || 'auto',
      stageStatus: 'ocr_processing',
      sourceText: retries > 0 ? '截图已稳定，正在执行本地 OCR…' : '截图完成，正在执行本地 OCR…',
      translatedText: retries > 0 ? '首次识别未返回文本，已自动重试一次并继续…' : 'OCR 完成后将进入翻译阶段…',
      capturePreviewDataUrl: capture.dataUrl,
      captureMeta: {
        width: capture.size.width,
        height: capture.size.height,
        targetLanguage: config.productSpec.pipeline.target_language,
        captureSessionId: audit.captureSessionId,
        taskId: audit.taskId,
        ocrProvider: 'pending',
        translationProvider: config.implementationConfig.providers.translation_chain[0],
        autoRetryCount: retries,
      },
    }));
    const recognizedText = ocrResult.text.trim();
    rememberPipelineState(selection, capture, ocrResult, '', null, audit);
    appendPipelineEvent('trans_requested', audit, {
      provider: config.implementationConfig.providers.translation_chain[0],
      resultState: 'translation_processing',
      stageStatus: 'translation_processing',
      sourceLanguage: ocrResult.sourceLanguage || 'auto',
    });

    showPanel(buildStageResult(selection, {
      sourceLanguage: ocrResult.sourceLanguage || 'auto',
      stageStatus: 'translation_processing',
      sourceText: recognizedText || 'OCR 未返回可用文本。',
      translatedText: '正在调用翻译 provider…',
      capturePreviewDataUrl: capture.dataUrl,
      captureMeta: {
        width: capture.size.width,
        height: capture.size.height,
        targetLanguage: config.productSpec.pipeline.target_language,
        captureSessionId: audit.captureSessionId,
        taskId: audit.taskId,
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
    rememberPipelineState(selection, capture, ocrResult, translationResult.translatedText, translationResult, audit);

    const result = buildStageResult(selection, {
      sourceLanguage: ocrResult.sourceLanguage || 'auto',
      stageStatus: 'translation_ready',
      sourceText: recognizedText,
      translatedText: translationResult.translatedText,
      capturePreviewDataUrl: capture.dataUrl,
      captureMeta: {
        width: capture.size.width,
        height: capture.size.height,
        targetLanguage: config.productSpec.pipeline.target_language,
        captureSessionId: audit.captureSessionId,
        taskId: audit.taskId,
        ocrProvider: ocrResult.provider,
        translationProvider: translationResult.provider,
        ocrDiagnostics: ocrResult.diagnostics || null,
        translationDiagnostics: translationResult.diagnostics || null,
        autoRetryCount: retries,
      },
    });
    showPanel(result);
    appendPipelineEvent('result_rendered', audit, {
      provider: translationResult.provider,
      resultState: 'translation_ready',
      stageStatus: 'translation_ready',
      sourceLanguage: ocrResult.sourceLanguage || 'auto',
    });
    captureUiState.pipelineBusy = false;
    return { ok: true };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    if (message.includes('no desktop capture source available')) {
      setScreenCaptureCapability(false, message);
      showSetupGuide();
    }
    const failureResult = {
      ...(lastPipelineState
        ? buildStageResult(lastPipelineState.selection || selection, {
            sourceText: lastPipelineState.sourceText || '等待本地主链输出结果。',
            sourceLanguage: lastPipelineState.sourceLanguage || 'auto',
            capturePreviewDataUrl: lastPipelineState.capturePreviewDataUrl,
            captureMeta: lastPipelineState.captureMeta,
          })
        : buildStubResult(selection)),
      stageStatus: 'failed',
      translatedText: 'OCR 或翻译主链执行失败，请检查 desktopCapturer、内置或外部 tesseract、OPENAI_API_KEY、AITRANS_OPENAI_BASE_URL 或当前 Windows 权限状态。',
      errorOrigin: message,
    };
    showPanel(failureResult);
    appendPipelineEvent('failure_raised', audit, {
      provider: lastPipelineState?.captureMeta?.translationProvider || lastPipelineState?.captureMeta?.ocrProvider || null,
      resultState: 'failed',
      stageStatus: 'failed',
      sourceLanguage: lastPipelineState?.sourceLanguage || 'auto',
      error: message,
    });
    captureUiState.pipelineBusy = false;
    return { ok: false, error: message };
  }
});

ipcMain.handle('overlay:cancel', async () => {
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.hide();
  }
  captureUiState.pipelineBusy = false;
  await restoreCapturedFocusTarget('capture_cancelled');
  clearFocusRestoreSession();
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
  await restoreCapturedFocusTarget('panel_closed');
  clearFocusRestoreSession();
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
    appendPipelineEvent('trans_requested', {
      captureSessionId: lastPipelineState.captureMeta?.captureSessionId || null,
      taskId: lastPipelineState.captureMeta?.taskId || null,
    }, {
      provider: config.implementationConfig.providers.translation_chain[0],
      resultState: 'translation_processing',
      stageStatus: 'translation_processing',
      sourceLanguage: lastPipelineState.sourceLanguage || 'auto',
    });
    showPanel(buildStageResult(lastPipelineState.selection || getFallbackSelection(), {
      sourceLanguage: lastPipelineState.sourceLanguage || 'auto',
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
        sourceLanguage: lastPipelineState.sourceLanguage || 'auto',
      },
      translationResult.translatedText,
      translationResult,
      {
        captureSessionId: lastPipelineState.captureMeta?.captureSessionId || null,
        taskId: lastPipelineState.captureMeta?.taskId || null,
      },
    );

    showPanel(buildStageResult(lastPipelineState.selection || getFallbackSelection(), {
      sourceLanguage: lastPipelineState.sourceLanguage || 'auto',
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
    appendPipelineEvent('result_rendered', {
      captureSessionId: lastPipelineState.captureMeta?.captureSessionId || null,
      taskId: lastPipelineState.captureMeta?.taskId || null,
    }, {
      provider: translationResult.provider,
      resultState: 'translation_ready',
      stageStatus: 'translation_ready',
      sourceLanguage: lastPipelineState.sourceLanguage || 'auto',
    });
    return { ok: true };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    showPanel(buildStageResult(lastPipelineState.selection || getFallbackSelection(), {
      sourceLanguage: lastPipelineState.sourceLanguage || 'auto',
      stageStatus: 'failed',
      sourceText: lastPipelineState.sourceText,
      translatedText: config.productSpec.presentation.copy.failure_title,
      capturePreviewDataUrl: lastPipelineState.capturePreviewDataUrl,
      captureMeta: lastPipelineState.captureMeta,
      errorOrigin: message,
    }));
    appendPipelineEvent('failure_raised', {
      captureSessionId: lastPipelineState.captureMeta?.captureSessionId || null,
      taskId: lastPipelineState.captureMeta?.taskId || null,
    }, {
      provider: lastPipelineState.captureMeta?.translationProvider || lastPipelineState.captureMeta?.ocrProvider || null,
      resultState: 'failed',
      stageStatus: 'failed',
      sourceLanguage: lastPipelineState.sourceLanguage || 'auto',
      error: message,
    });
    return { ok: false, error: message };
  }
});

ipcMain.handle('panel:get-project-summary', async () => {
  return {
    displayName: config.productSpec.project.display_name,
    shortcut: currentCaptureShortcut || config.shortcut,
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
  const shortcutInput =
    payload && typeof payload.captureShortcut === 'string'
      ? payload.captureShortcut.trim()
      : resolveConfiguredCaptureShortcut();

  if (!baseUrlInput) {
    return { ok: false, error: 'missing translation.base_url' };
  }

  const normalizedBaseUrl = normalizeBaseUrl(baseUrlInput);
  if (normalizedBaseUrl === OFFICIAL_OPENAI_BASE_URL && !apiKeyInput) {
    return { ok: false, error: 'official OpenAI endpoint requires api_key' };
  }

  const shortcutResult = applyCaptureShortcut(shortcutInput);
  if (!shortcutResult.ok) {
    return { ok: false, error: shortcutResult.error };
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
    desktop: {
      ...(currentValues.desktop && typeof currentValues.desktop === 'object'
        ? currentValues.desktop
        : {}),
      capture_shortcut: shortcutResult.shortcut,
    },
  });

  appendStartupLog('setup-guide:config-saved', {
    configPath: saved.path,
    usingOfficialEndpoint: normalizedBaseUrl === OFFICIAL_OPENAI_BASE_URL,
    apiKeyPresent: Boolean(apiKeyInput),
    captureShortcut: shortcutResult.shortcut,
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

app.on('second-instance', () => {
  focusBestAvailableWindow();
});

app.whenReady().then(async () => {
  appendStartupLog('app:ready');
  runtimeBootstrap = ensureRuntimeOverridesTemplate();
  appendStartupLog('runtime-overrides:bootstrap', runtimeBootstrap);
  updateRuntime = createAutoUpdateRuntime({
    app,
    appendStartupLog,
    appendPipelineEvent,
    refreshTrayMenu,
    dialog,
    implementationConfig: config.implementationConfig,
  });
  createTray();
  createPanelWindow();
  await probeAndStoreScreenCaptureCapability();
  try {
    registerShortcuts();
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    appendStartupLog('shortcut:register-failed', { message });
    dialog.showErrorBox('AiTrans 快捷键注册失败', `${message}\n\n请在首次配置窗口中重新设置快捷键。`);
    showSetupGuide();
  }
  if (shouldAutoOpenSetupGuide()) {
    appendStartupLog('setup-guide:auto-open');
    showSetupGuide();
  }
  if (updateRuntime) {
    updateRuntime.scheduleStartupCheck();
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
