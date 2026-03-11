const fs = require('node:fs');
const path = require('node:path');

const { buildTesseractLanguages } = require('../lib/ocr-adapters');
const { loadProjectConfig } = require('../lib/project-config');

function resolveAppRoot() {
  return path.resolve(__dirname, '..');
}

function findSourceRoot() {
  const explicitExecutable = (process.env.AITRANS_TESSERACT_PATH || '').trim();
  const explicitRoot = (process.env.AITRANS_TESSERACT_STAGE_FROM || '').trim();

  const candidates = [
    explicitRoot,
    explicitExecutable ? path.dirname(explicitExecutable) : '',
    'C:\\Program Files\\Tesseract-OCR',
    'C:\\Program Files (x86)\\Tesseract-OCR',
  ].filter(Boolean);

  for (const candidate of candidates) {
    const executableCandidates = [
      path.join(candidate, 'tesseract.exe'),
      path.join(candidate, 'bin', 'tesseract.exe'),
    ];
    const executable = executableCandidates.find((item) => fs.existsSync(item));
    if (executable) {
      return {
        root: candidate,
        executable,
        tessdataDir: [
          path.join(candidate, 'tessdata'),
          path.join(candidate, 'bin', 'tessdata'),
        ].find((item) => fs.existsSync(item)) || null,
      };
    }
  }

  return null;
}

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function copyFile(sourcePath, targetPath) {
  ensureDir(path.dirname(targetPath));
  fs.copyFileSync(sourcePath, targetPath);
  console.log(`[OK] copied ${sourcePath} -> ${targetPath}`);
}

function copyRuntimeLibraries(sourceExecutable, vendorRoot) {
  const executableDir = path.dirname(sourceExecutable);
  const runtimeFiles = fs.readdirSync(executableDir)
    .filter((item) => {
      const lower = item.toLowerCase();
      return lower.endsWith('.dll') || lower.endsWith('.manifest');
    });

  for (const item of runtimeFiles) {
    copyFile(path.join(executableDir, item), path.join(vendorRoot, item));
  }
}

function main() {
  const config = loadProjectConfig();
  const source = findSourceRoot();
  if (!source) {
    throw new Error('unable to locate installed Tesseract; set AITRANS_TESSERACT_PATH or AITRANS_TESSERACT_STAGE_FROM');
  }
  if (!source.tessdataDir) {
    throw new Error(`missing tessdata directory under ${source.root}`);
  }

  const vendorRoot = path.join(resolveAppRoot(), 'vendor', 'tesseract');
  const vendorTessdata = path.join(vendorRoot, 'tessdata');

  const requiredLanguages = buildTesseractLanguages(config.productSpec)
    .split('+')
    .filter(Boolean);
  const extraLanguages = ['osd'];
  const languages = [...new Set([...requiredLanguages, ...extraLanguages])];

  const missing = languages.filter((language) => {
    const sourceFile = path.join(source.tessdataDir, `${language}.traineddata`);
    return !fs.existsSync(sourceFile);
  });
  if (missing.length > 0) {
    throw new Error(
      `missing traineddata in installed Tesseract: ${missing.join(', ')} (expected under ${source.tessdataDir})`,
    );
  }

  ensureDir(vendorTessdata);

  copyFile(source.executable, path.join(vendorRoot, 'tesseract.exe'));
  copyRuntimeLibraries(source.executable, vendorRoot);

  for (const language of languages) {
    const sourceFile = path.join(source.tessdataDir, `${language}.traineddata`);
    copyFile(sourceFile, path.join(vendorTessdata, `${language}.traineddata`));
  }

  console.log('');
  console.log('[SUMMARY] bundled Tesseract runtime staged under electron/vendor/tesseract');
}

main();
