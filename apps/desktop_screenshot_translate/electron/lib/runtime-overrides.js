const fs = require('node:fs');
const path = require('node:path');

function resolveAppRoot() {
  return path.resolve(__dirname, '..');
}

function resolveRuntimeConfigBaseDir() {
  const appData = process.env.APPDATA || process.env.LOCALAPPDATA || '';
  if (!appData) {
    return path.join(resolveAppRoot(), 'config');
  }
  return path.join(appData, 'AiTrans');
}

function resolveLegacyRuntimeConfigBaseDir() {
  const appData = process.env.APPDATA || process.env.LOCALAPPDATA || '';
  if (!appData) {
    return '';
  }
  return path.join(appData, 'desktop_screenshot_translate');
}

function getPrimaryRuntimeOverridePath() {
  return path.join(resolveRuntimeConfigBaseDir(), 'runtime-overrides.json');
}

function getRuntimeOverrideExampleCandidates() {
  const resourcesPath =
    typeof process.resourcesPath === 'string' && process.resourcesPath.trim()
      ? process.resourcesPath
      : '';

  return uniquePaths([
    resourcesPath ? path.join(resourcesPath, 'config', 'runtime-overrides.example.json') : '',
    path.join(resolveAppRoot(), 'config', 'runtime-overrides.example.json'),
  ]);
}

function uniquePaths(items) {
  return [...new Set(items.filter(Boolean))];
}

function getRuntimeOverrideCandidates() {
  const resourcesPath =
    typeof process.resourcesPath === 'string' && process.resourcesPath.trim()
      ? process.resourcesPath
      : '';

  return uniquePaths([
    process.env.AITRANS_RUNTIME_OVERRIDES_PATH,
    getPrimaryRuntimeOverridePath(),
    resolveLegacyRuntimeConfigBaseDir()
      ? path.join(resolveLegacyRuntimeConfigBaseDir(), 'runtime-overrides.json')
      : '',
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

function ensureRuntimeOverridesTemplate() {
  const configPath = getPrimaryRuntimeOverridePath();
  const configDir = path.dirname(configPath);
  const legacyConfigDir = resolveLegacyRuntimeConfigBaseDir();
  const legacyConfigPath = legacyConfigDir
    ? path.join(legacyConfigDir, 'runtime-overrides.json')
    : '';

  if (legacyConfigPath && fs.existsSync(legacyConfigPath)) {
    return {
      created: false,
      configPath: legacyConfigPath,
      configDir: path.dirname(legacyConfigPath),
      reusedLegacy: true,
    };
  }

  fs.mkdirSync(configDir, { recursive: true });

  if (fs.existsSync(configPath)) {
    return {
      created: false,
      configPath,
      configDir,
    };
  }

  const examplePath = getRuntimeOverrideExampleCandidates().find((candidate) => fs.existsSync(candidate));
  if (examplePath) {
    fs.copyFileSync(examplePath, configPath);
    return {
      created: true,
      configPath,
      configDir,
      examplePath,
    };
  }

  const fallbackTemplate = {
    _comment: 'Fill translation.base_url and translation.api_key before using remote translation.',
    translation: {
      base_url: '',
      api_key: '',
    },
    ocr: {
      tesseract_path: '',
      tessdata_dir: '',
    },
  };
  fs.writeFileSync(configPath, JSON.stringify(fallbackTemplate, null, 2), 'utf-8');
  return {
    created: true,
    configPath,
    configDir,
  };
}

module.exports = {
  ensureRuntimeOverridesTemplate,
  getPrimaryRuntimeOverridePath,
  getRuntimeOverrideExampleCandidates,
  getRuntimeOverrideCandidates,
  loadRuntimeOverrides,
  resolveRuntimeConfigBaseDir,
  resolveAppRoot,
};
