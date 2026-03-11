const fs = require('node:fs');
const path = require('node:path');

const OFFICIAL_OPENAI_BASE_URL = 'https://api.openai.com/v1';

function resolveAppRoot() {
  return path.resolve(__dirname, '..');
}

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
  return normalizeBaseUrl(process.env.AITRANS_OPENAI_BASE_URL || process.env.OPENAI_BASE_URL || '');
}

function resolveOpenAiApiKey(baseUrl) {
  const apiKey = (process.env.OPENAI_API_KEY || process.env.AITRANS_OPENAI_API_KEY || '').trim();
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

function resolveTesseractExecutable(implementationConfig) {
  const allowEnvFallback = implementationConfig?.providers?.ocr_dev_fallback === 'allow_env_binary_path';
  const bundled = getBundledTesseractCandidates().find((candidate) => fs.existsSync(candidate));
  if (bundled) {
    return { executable: bundled, source: 'bundled' };
  }

  if (allowEnvFallback && process.env.AITRANS_TESSERACT_PATH?.trim()) {
    return { executable: process.env.AITRANS_TESSERACT_PATH.trim(), source: 'env_override' };
  }

  return { executable: 'tesseract', source: 'path_lookup' };
}

module.exports = {
  OFFICIAL_OPENAI_BASE_URL,
  getBundledTesseractCandidates,
  normalizeBaseUrl,
  resolveAppRoot,
  resolveOpenAiApiKey,
  resolveOpenAiBaseUrl,
  resolveTesseractExecutable,
};
