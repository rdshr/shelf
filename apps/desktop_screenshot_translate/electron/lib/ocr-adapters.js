const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const { execFile } = require('node:child_process');
const { promisify } = require('node:util');

const { resolveTesseractExecutable } = require('./provider-runtime');

const execFileAsync = promisify(execFile);

const TESSERACT_LANGUAGE_MAP = {
  auto: null,
  en: 'eng',
  zh: 'chi_sim',
  'zh-Hans': 'chi_sim',
  ja: 'jpn',
};

function buildTesseractLanguages(productSpec) {
  const mapped = [];
  for (const item of productSpec.pipeline.source_languages || []) {
    const token = TESSERACT_LANGUAGE_MAP[item];
    if (token && !mapped.includes(token)) {
      mapped.push(token);
    }
  }
  if (mapped.length === 0) {
    return 'eng';
  }
  return mapped.join('+');
}

async function withTemporaryImage(pngBuffer, callback) {
  const tmpRoot = await fs.mkdtemp(path.join(os.tmpdir(), 'aitrans-ocr-'));
  const imagePath = path.join(tmpRoot, 'capture.png');
  await fs.writeFile(imagePath, pngBuffer);
  try {
    return await callback(imagePath);
  } finally {
    await fs.rm(tmpRoot, { recursive: true, force: true });
  }
}

async function recognizeWithTesseract(imagePath, productSpec, implementationConfig) {
  const { executable, source } = resolveTesseractExecutable(implementationConfig);
  const languages = buildTesseractLanguages(productSpec);
  const args = [imagePath, 'stdout', '-l', languages, '--psm', '6'];
  const result = await execFileAsync(executable, args, {
    windowsHide: true,
    maxBuffer: 16 * 1024 * 1024,
  });
  const text = (result.stdout || '').trim();
  if (!text) {
    const stderr = (result.stderr || '').trim();
    throw new Error(stderr || 'tesseract returned empty OCR text');
  }
  return {
    provider: 'tesseract',
    text,
    diagnostics: {
      languages,
      executable,
      executableSource: source,
      stderr: (result.stderr || '').trim(),
    },
  };
}

async function recognizeWithWindowsOcr() {
  throw new Error(
    'windows_ocr_api requires packaged Windows app identity; unpackaged Electron MVP should fall back to tesseract first',
  );
}

async function recognizeText(capture, productSpec, implementationConfig) {
  const failures = [];
  return withTemporaryImage(capture.pngBuffer, async (imagePath) => {
    for (const provider of implementationConfig.providers.ocr_chain) {
      try {
        if (provider === 'windows_ocr_api') {
          return await recognizeWithWindowsOcr(imagePath, productSpec);
        }
        if (provider === 'tesseract') {
          return await recognizeWithTesseract(imagePath, productSpec, implementationConfig);
        }
        failures.push(`${provider}: unsupported provider`);
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        failures.push(`${provider}: ${message}`);
      }
    }
    throw new Error(`no OCR provider succeeded: ${failures.join(' | ')}`);
  });
}

module.exports = {
  recognizeText,
};
