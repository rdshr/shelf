const fs = require('node:fs');
const path = require('node:path');

const { buildTesseractLanguages } = require('../lib/ocr-adapters');
const { loadProjectConfig } = require('../lib/project-config');

function resolveAppRoot() {
  return path.resolve(__dirname, '..');
}

function resolveBundledTesseractExecutable() {
  const appRoot = resolveAppRoot();
  const candidates = [
    path.join(appRoot, 'vendor', 'tesseract', 'tesseract.exe'),
    path.join(appRoot, 'vendor', 'tesseract', 'bin', 'tesseract.exe'),
  ];
  return candidates.find((candidate) => fs.existsSync(candidate)) || null;
}

function resolveBundledTessdataDir() {
  const appRoot = resolveAppRoot();
  const candidates = [
    path.join(appRoot, 'vendor', 'tesseract', 'tessdata'),
    path.join(appRoot, 'vendor', 'tesseract', 'bin', 'tessdata'),
  ];
  return candidates.find((candidate) => fs.existsSync(candidate)) || null;
}

function checkGeneratedArtifacts(config, failures) {
  const required = [
    config.productSpecPath,
    config.manifestPath,
    config.implementationBundlePath,
  ];
  for (const item of required) {
    if (!fs.existsSync(item)) {
      failures.push(`missing generated artifact: ${item}`);
    }
  }
}

function checkBundledTesseract(config, failures) {
  const executable = resolveBundledTesseractExecutable();
  if (!executable) {
    failures.push('missing bundled tesseract.exe under electron/vendor/tesseract');
    return;
  }

  const tessdataDir = resolveBundledTessdataDir();
  if (!tessdataDir) {
    failures.push('missing bundled tessdata directory under electron/vendor/tesseract');
    return;
  }

  const requiredLanguages = buildTesseractLanguages(config.productSpec)
    .split('+')
    .filter(Boolean);
  for (const language of requiredLanguages) {
    const traineddata = path.join(tessdataDir, `${language}.traineddata`);
    if (!fs.existsSync(traineddata)) {
      failures.push(`missing bundled tessdata: ${traineddata}`);
    }
  }
}

function checkRuntimeOverrideExample(failures) {
  const examplePath = path.join(resolveAppRoot(), 'config', 'runtime-overrides.example.json');
  if (!fs.existsSync(examplePath)) {
    failures.push(`missing runtime override example: ${examplePath}`);
  }
}

function main() {
  const failures = [];
  const warnings = [];
  const config = loadProjectConfig();

  console.log('desktop_screenshot_translate Windows release check');
  console.log(`app root: ${resolveAppRoot()}`);
  console.log(`generated dir: ${config.generatedDir}`);

  checkGeneratedArtifacts(config, failures);
  checkBundledTesseract(config, failures);
  checkRuntimeOverrideExample(failures);

  warnings.push(
    'translation endpoint credentials are not embedded into the installer; use runtime-overrides.json or environment variables on target machines',
  );

  if (warnings.length > 0) {
    console.log('');
    console.log('[WARNINGS]');
    for (const item of warnings) {
      console.log(`- ${item}`);
    }
  }

  if (failures.length > 0) {
    console.log('');
    console.log('[FAILURES]');
    for (const item of failures) {
      console.log(`- ${item}`);
    }
    process.exitCode = 1;
    return;
  }

  console.log('');
  console.log('[SUMMARY] release check passed; Windows installer build can proceed');
}

main();
