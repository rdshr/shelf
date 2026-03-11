const fs = require('node:fs');
const path = require('node:path');

const { loadRuntimeOverrides, resolveAppRoot } = require('./runtime-overrides');

const OFFICIAL_OPENAI_BASE_URL = 'https://api.openai.com/v1';

function normalizeBaseUrl(input) {
  if (typeof input !== 'string') {
    return OFFICIAL_OPENAI_BASE_URL;
  }
  const trimmed = input.trim();
  if (!trimmed) {
    return OFFICIAL_OPENAI_BASE_URL;
  }
  return trimmed.replace(/\/+$/, '');
}

function resolveOpenAiBaseUrl() {
  const runtimeOverrides = loadRuntimeOverrides().values;
  return normalizeBaseUrl(
    process.env.AITRANS_OPENAI_BASE_URL
      || process.env.OPENAI_BASE_URL
      || runtimeOverrides.translation?.base_url
      || '',
  );
}

function resolveOpenAiApiKey(baseUrl) {
  const runtimeOverrides = loadRuntimeOverrides().values;
  const apiKey = (
    process.env.OPENAI_API_KEY
    || process.env.AITRANS_OPENAI_API_KEY
    || runtimeOverrides.translation?.api_key
    || ''
  ).trim();
  if (apiKey) {
    return apiKey;
  }
  if (normalizeBaseUrl(baseUrl) === OFFICIAL_OPENAI_BASE_URL) {
    throw new Error('missing OPENAI_API_KEY for official OpenAI endpoint');
  }
  return '';
}

function getBundledTesseractCandidates() {
  const appRoot = resolveAppRoot();
  const resourcesPath =
    typeof process.resourcesPath === 'string' && process.resourcesPath.trim()
      ? process.resourcesPath
      : null;

  const candidates = [
    path.join(appRoot, 'vendor', 'tesseract', 'tesseract.exe'),
    path.join(appRoot, 'vendor', 'tesseract', 'bin', 'tesseract.exe'),
  ];

  if (resourcesPath) {
    candidates.push(
      path.join(resourcesPath, 'tesseract', 'tesseract.exe'),
      path.join(resourcesPath, 'vendor', 'tesseract', 'tesseract.exe'),
      path.join(resourcesPath, 'vendor', 'tesseract', 'bin', 'tesseract.exe'),
    );
  }

  return [...new Set(candidates)];
}

function resolveTessdataDirectory(executable, runtimeOverrides) {
  const manualDir = runtimeOverrides.ocr?.tessdata_dir;
  if (typeof manualDir === 'string' && manualDir.trim()) {
    return manualDir.trim();
  }

  const executableDir = path.dirname(executable);
  const candidates = [
    path.join(executableDir, 'tessdata'),
    path.join(executableDir, '..', 'tessdata'),
  ];
  return candidates.find((candidate) => fs.existsSync(candidate)) || null;
}

function resolveTesseractExecutable(implementationConfig) {
  const runtimeOverrides = loadRuntimeOverrides().values;
  const allowEnvFallback = implementationConfig?.providers?.ocr_dev_fallback === 'allow_env_binary_path';
  const bundled = getBundledTesseractCandidates().find((candidate) => fs.existsSync(candidate));
  if (bundled) {
    return {
      executable: bundled,
      source: 'bundled',
      tessdataDir: resolveTessdataDirectory(bundled, runtimeOverrides),
    };
  }

  const overridePath = (
    process.env.AITRANS_TESSERACT_PATH
    || runtimeOverrides.ocr?.tesseract_path
    || ''
  ).trim();
  if (allowEnvFallback && overridePath) {
    return {
      executable: overridePath,
      source: 'env_override',
      tessdataDir: resolveTessdataDirectory(overridePath, runtimeOverrides),
    };
  }

  return {
    executable: 'tesseract',
    source: 'path_lookup',
    tessdataDir: resolveTessdataDirectory('tesseract', runtimeOverrides),
  };
}

module.exports = {
  OFFICIAL_OPENAI_BASE_URL,
  getBundledTesseractCandidates,
  loadRuntimeOverrides,
  normalizeBaseUrl,
  resolveAppRoot,
  resolveOpenAiApiKey,
  resolveOpenAiBaseUrl,
  resolveTesseractExecutable,
};
