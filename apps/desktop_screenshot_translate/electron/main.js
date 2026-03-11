const path = require('node:path');
const { app, BrowserWindow, Menu, Tray, globalShortcut, ipcMain, nativeImage, clipboard, screen } = require('electron');

const { loadProjectConfig } = require('./lib/project-config');
const { captureSelectionImage, recognizeText, translateText } = require('./lib/local-pipeline');
const { createWindowStateStore } = require('./lib/window-state');

const config = loadProjectConfig();
const stateStore = createWindowStateStore(app, 'desktop_screenshot_translate');

let tray = null;
let overlayWindow = null;
let panelWindow = null;
let lastSelection = null;

function createTrayImage() {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
      <rect x="4" y="4" width="24" height="24" rx="7" fill="#0f766e" />
      <path d="M10 11h12v2H10zm0 4h7v2h-7zm0 4h12v2H10z" fill="#f8fafc" />
    </svg>
  `;
  return nativeImage.createFromDataURL(`data:image/svg+xml;base64,${Buffer.from(svg).toString('base64')}`);
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
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  panelWindow.loadFile(path.join(__dirname, 'renderer', 'panel-dist', 'index.html'));
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

function savePanelBounds() {
  if (!panelWindow || panelWindow.isDestroyed()) {
    return;
  }
  stateStore.save('panel', panelWindow.getBounds());
}

function showOverlay() {
  const display = getOverlayDisplay();
  const window = createOverlayWindow();
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

function createTray() {
  tray = new Tray(createTrayImage());
  tray.setToolTip(config.productSpec.project.display_name);
  const menu = Menu.buildFromTemplate([
    { label: '开始截图翻译', click: () => showOverlay() },
    { label: `快捷键：${config.shortcut}`, enabled: false },
    { type: 'separator' },
    { label: '显示结果面板', click: () => showPanel(buildStubResult(lastSelection || getFallbackSelection())) },
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
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.hide();
  }
  try {
    showPanel(buildStageResult(selection, {
      stageStatus: 'capturing',
      sourceText: '正在抓取选区位图…',
      translatedText: '正在从 Windows 桌面获取截图区域，请稍候。',
    }));

    const capture = await captureSelectionImage(selection);
    showPanel(buildStageResult(selection, {
      stageStatus: 'ocr_processing',
      sourceText: '截图完成，正在执行本地 OCR…',
      translatedText: 'OCR 完成后将进入翻译阶段…',
      capturePreviewDataUrl: capture.dataUrl,
      captureMeta: {
        width: capture.size.width,
        height: capture.size.height,
        targetLanguage: config.productSpec.pipeline.target_language,
        ocrProvider: 'pending',
        translationProvider: config.implementationConfig.providers.translation_chain[0],
      },
    }));

    const ocrResult = await recognizeText(capture, config.productSpec, config.implementationConfig);
    const recognizedText = ocrResult.text.trim();

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
      },
    }));

    const translationResult = await translateText(
      recognizedText,
      config.productSpec,
      config.implementationConfig,
    );

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
      },
    });
    showPanel(result);
    return { ok: true };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    showPanel({
      ...buildStubResult(selection),
      stageStatus: 'failed',
      translatedText: 'OCR 或翻译主链执行失败，请检查 desktopCapturer、内置或外部 tesseract、OPENAI_API_KEY、AITRANS_OPENAI_BASE_URL 或当前 Windows 权限状态。',
      errorOrigin: message,
    });
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

ipcMain.handle('panel:get-project-summary', async () => {
  return {
    displayName: config.productSpec.project.display_name,
    shortcut: config.shortcut,
    pipeline: config.productSpec.pipeline,
    governance: config.productSpec.governance,
  };
});

app.whenReady().then(() => {
  createTray();
  createPanelWindow();
  registerShortcuts();
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
