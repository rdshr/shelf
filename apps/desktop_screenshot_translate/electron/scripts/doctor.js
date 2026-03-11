const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');

const {
  getBundledTesseractCandidates,
  resolveAppRoot,
  resolveOpenAiApiKey,
  resolveOpenAiBaseUrl,
  resolveTesseractExecutable,
} = require('../lib/provider-runtime');
const { loadProjectConfig } = require('../lib/project-config');

function resolveRepoRoot() {
  return path.resolve(resolveAppRoot(), '../../..');
}

function resolveProjectGeneratedDir() {
  return path.join(resolveRepoRoot(), 'projects', 'desktop_screenshot_translate', 'generated');
}

function checkFile(label, filePath, failures) {
  if (fs.existsSync(filePath)) {
    console.log(`[OK] ${label}: ${filePath}`);
    return;
  }
  console.log(`[FAIL] ${label}: ${filePath}`);
  failures.push(`missing ${label}`);
}

function checkTranslationEndpoint(config, failures) {
  const baseUrl = resolveOpenAiBaseUrl();
  console.log(`[INFO] openai_translation base URL: ${baseUrl}`);
  try {
    const apiKey = resolveOpenAiApiKey(baseUrl);
    if (apiKey) {
      console.log('[OK] translation credential is set');
    } else {
      console.log('[OK] local compatible endpoint does not require OPENAI_API_KEY');
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.log(`[WARN] ${message}; translation will fall back to local stub`);
    failures.push('missing translation credential');
  }
}

function checkTesseract(config, failures) {
  const bundledCandidates = getBundledTesseractCandidates();
  for (const candidate of bundledCandidates) {
    if (fs.existsSync(candidate)) {
      console.log(`[OK] bundled tesseract candidate found: ${candidate}`);
    }
  }

  const { executable, source } = resolveTesseractExecutable(config.implementationConfig);
  try {
    const output = execFileSync(executable, ['--version'], {
      encoding: 'utf-8',
      stdio: ['ignore', 'pipe', 'pipe'],
      windowsHide: true,
    });
    const versionLine = output.split(/\r?\n/).find(Boolean) || 'unknown version';
    console.log(`[OK] tesseract available (${source}): ${executable} -> ${versionLine}`);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.log(`[FAIL] tesseract unavailable (${source}): ${executable}`);
    console.log(`       ${message}`);
    failures.push('missing tesseract');
  }
}

function checkPlatform() {
  if (process.platform === 'win32') {
    console.log('[OK] running on Windows');
    return;
  }
  console.log(`[WARN] current platform is ${process.platform}; Windows GUI validation still needs native Windows`);
}

function main() {
  const failures = [];
  const generatedDir = resolveProjectGeneratedDir();

  console.log('desktop_screenshot_translate Windows MVP doctor');
  console.log(`app root: ${resolveAppRoot()}`);
  console.log(`repo root: ${resolveRepoRoot()}`);

  checkPlatform();
  checkFile('generated/product_spec.json', path.join(generatedDir, 'product_spec.json'), failures);
  checkFile('generated/generation_manifest.json', path.join(generatedDir, 'generation_manifest.json'), failures);
  checkFile('generated/implementation_bundle.py', path.join(generatedDir, 'implementation_bundle.py'), failures);

  let config = null;
  if (failures.length === 0) {
    config = loadProjectConfig();
  }

  if (config) {
    checkTesseract(config, failures);
    checkTranslationEndpoint(config, failures);
  }

  if (failures.length > 0) {
    console.log('');
    console.log('[SUMMARY] doctor found issues:');
    for (const item of failures) {
      console.log(`- ${item}`);
    }
    console.log('');
    if (failures.some((item) => item.startsWith('missing generated/'))) {
      console.log('[NEXT] generate project artifacts from repo root:');
      console.log('       uv run python scripts/materialize_project.py --project projects/desktop_screenshot_translate/product_spec.toml');
    }
    if (failures.includes('missing tesseract')) {
      console.log('[NEXT] place bundled tesseract under electron/vendor/tesseract, or set AITRANS_TESSERACT_PATH in the current session');
    }
    if (failures.includes('missing translation credential')) {
      console.log('[NEXT] set OPENAI_API_KEY for the official endpoint, or set AITRANS_OPENAI_BASE_URL to a reachable local compatible endpoint');
    }
    process.exitCode = 1;
    return;
  }

  console.log('');
  console.log('[SUMMARY] doctor passed; Windows MVP can proceed to npm run dev');
}

main();
