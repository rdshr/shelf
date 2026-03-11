const fs = require('node:fs');
const path = require('node:path');

function resolveAppRoot() {
  return path.resolve(__dirname, '..');
}

function uniquePaths(items) {
  return [...new Set(items.filter(Boolean))];
}

function getRuntimeOverrideCandidates() {
  const appData = process.env.APPDATA || process.env.LOCALAPPDATA || '';
  const resourcesPath =
    typeof process.resourcesPath === 'string' && process.resourcesPath.trim()
      ? process.resourcesPath
      : '';

  return uniquePaths([
    process.env.AITRANS_RUNTIME_OVERRIDES_PATH,
    appData ? path.join(appData, 'desktop_screenshot_translate', 'runtime-overrides.json') : '',
    resourcesPath ? path.join(resourcesPath, 'config', 'runtime-overrides.json') : '',
    path.join(resolveAppRoot(), 'config', 'runtime-overrides.json'),
  ]);
}

function readJsonIfExists(filePath) {
  if (!filePath || !fs.existsSync(filePath)) {
    return null;
  }
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
}

function loadRuntimeOverrides() {
  for (const candidate of getRuntimeOverrideCandidates()) {
    try {
      const values = readJsonIfExists(candidate);
      if (values && typeof values === 'object') {
        return {
          path: candidate,
          values,
        };
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      throw new Error(`invalid runtime overrides file ${candidate}: ${message}`);
    }
  }

  return {
    path: null,
    values: {},
  };
}

module.exports = {
  getRuntimeOverrideCandidates,
  loadRuntimeOverrides,
  resolveAppRoot,
};
