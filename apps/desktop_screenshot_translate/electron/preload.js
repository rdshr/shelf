const { contextBridge, ipcRenderer } = require('electron');

function subscribe(channel, callback) {
  const listener = (_event, payload) => callback(payload);
  ipcRenderer.on(channel, listener);
  return () => ipcRenderer.removeListener(channel, listener);
}

contextBridge.exposeInMainWorld('aitransDesktop', {
  onOverlayStart(callback) {
    return subscribe('overlay:start', callback);
  },
  onPanelData(callback) {
    return subscribe('panel:set-data', callback);
  },
  submitSelection(selection) {
    return ipcRenderer.invoke('overlay:submit-selection', selection);
  },
  cancelCapture(reason) {
    return ipcRenderer.invoke('overlay:cancel', { reason });
  },
  copyTranslation(text) {
    return ipcRenderer.invoke('panel:copy-translation', { text });
  },
  closePanel() {
    return ipcRenderer.invoke('panel:close');
  },
  recapture() {
    return ipcRenderer.invoke('panel:recapture');
  },
  retryTranslation() {
    return ipcRenderer.invoke('panel:retry-translation');
  },
  getProjectSummary() {
    return ipcRenderer.invoke('panel:get-project-summary');
  },
  onSetupData(callback) {
    return subscribe('setup:set-data', callback);
  },
  getSetupGuideState() {
    return ipcRenderer.invoke('setup:get-guide-state');
  },
  openConfigDirectory() {
    return ipcRenderer.invoke('setup:open-config-directory');
  },
  openConfigFile() {
    return ipcRenderer.invoke('setup:open-config-file');
  },
  copyConfigPath() {
    return ipcRenderer.invoke('setup:copy-config-path');
  },
  saveSetupConfig(payload) {
    return ipcRenderer.invoke('setup:save-config', payload);
  },
  closeSetupGuide() {
    return ipcRenderer.invoke('setup:close');
  },
});
