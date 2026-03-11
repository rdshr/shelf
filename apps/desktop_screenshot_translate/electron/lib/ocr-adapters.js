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

function detectSourceLanguageFromText(text) {
  if (typeof text !== 'string' || !text.trim()) {
    return {
      code: 'auto',
      strategy: 'empty_text_fallback',
    };
  }

  let latin = 0;
  let kana = 0;
  let han = 0;

  for (const char of text) {
    const codePoint = char.codePointAt(0) || 0;
    if ((codePoint >= 0x0041 && codePoint <= 0x007A) || (codePoint >= 0x00C0 && codePoint <= 0x024F)) {
      latin += 1;
      continue;
    }
    if (
      (codePoint >= 0x3040 && codePoint <= 0x309F)
      || (codePoint >= 0x30A0 && codePoint <= 0x30FF)
      || (codePoint >= 0x31F0 && codePoint <= 0x31FF)
    ) {
      kana += 1;
      continue;
    }
    if (
      (codePoint >= 0x3400 && codePoint <= 0x4DBF)
      || (codePoint >= 0x4E00 && codePoint <= 0x9FFF)
      || (codePoint >= 0xF900 && codePoint <= 0xFAFF)
    ) {
      han += 1;
    }
  }

  if (kana > 0) {
    return {
      code: 'ja',
      strategy: 'heuristic_post_ocr',
    };
  }
  if (han > 0) {
    return {
      code: 'zh',
      strategy: 'heuristic_post_ocr',
    };
  }
  if (latin > 0) {
    return {
      code: 'en',
      strategy: 'heuristic_post_ocr',
    };
  }
  return {
    code: 'auto',
    strategy: 'heuristic_post_ocr',
  };
}

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
  const { executable, source, tessdataDir } = resolveTesseractExecutable(implementationConfig);
  const languages = buildTesseractLanguages(productSpec);
  const args = [imagePath, 'stdout', '-l', languages, '--psm', '6'];
  if (tessdataDir) {
    args.push('--tessdata-dir', tessdataDir);
  }
  const result = await execFileAsync(executable, args, {
    windowsHide: true,
    maxBuffer: 16 * 1024 * 1024,
  });
  const text = (result.stdout || '').trim();
  if (!text) {
    const stderr = (result.stderr || '').trim();
    throw new Error(stderr || 'tesseract returned empty OCR text');
  }
  const sourceLanguage = detectSourceLanguageFromText(text);
  return {
    provider: 'tesseract',
    text,
    sourceLanguage: sourceLanguage.code,
    diagnostics: {
      languages,
      executable,
      executableSource: source,
      tessdataDir,
      stderr: (result.stderr || '').trim(),
      sourceLanguageDetection: sourceLanguage.strategy,
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
  buildTesseractLanguages,
  recognizeText,
};
