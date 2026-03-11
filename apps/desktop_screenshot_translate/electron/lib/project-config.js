const fs = require('node:fs');
const path = require('node:path');

const { resolveAppRoot } = require('./runtime-overrides');

function getRepoRoot() {
  return path.resolve(__dirname, '../../../../');
}

function getProjectRoot() {
  return path.join(getRepoRoot(), 'projects', 'desktop_screenshot_translate');
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
}

function getGeneratedDirCandidates() {
  const resourcesPath =
    typeof process.resourcesPath === 'string' && process.resourcesPath.trim()
      ? process.resourcesPath
      : '';

  return [
    resourcesPath ? path.join(resourcesPath, 'project-generated') : null,
    path.join(resolveAppRoot(), 'project-generated'),
    path.join(getProjectRoot(), 'generated'),
  ].filter(Boolean);
}

function extractEmbeddedJson(bundleText, variableName) {
  const pattern = new RegExp(`${variableName} = json\\.loads\\(r'''([\\s\\S]*?)'''\\)`);
  const match = bundleText.match(pattern);
  if (!match) {
    throw new Error(`missing embedded ${variableName} payload in implementation bundle`);
  }
  return JSON.parse(match[1]);
}

function loadProjectConfig() {
  let generatedDir = null;
  let productSpecPath = null;
  let manifestPath = null;
  let implementationBundlePath = null;

  for (const candidate of getGeneratedDirCandidates()) {
    const nextProductSpec = path.join(candidate, 'product_spec.json');
    const nextManifest = path.join(candidate, 'generation_manifest.json');
    const nextImplementationBundle = path.join(candidate, 'implementation_bundle.py');
    if (
      fs.existsSync(nextProductSpec)
      && fs.existsSync(nextManifest)
      && fs.existsSync(nextImplementationBundle)
    ) {
      generatedDir = candidate;
      productSpecPath = nextProductSpec;
      manifestPath = nextManifest;
      implementationBundlePath = nextImplementationBundle;
      break;
    }
  }

  if (!generatedDir || !productSpecPath || !manifestPath || !implementationBundlePath) {
    throw new Error(`missing generated project artifacts; searched: ${getGeneratedDirCandidates().join(', ')}`);
  }

  const productSpec = readJson(productSpecPath);
  const manifest = readJson(manifestPath);
  const implementationBundleText = fs.readFileSync(implementationBundlePath, 'utf-8');
  const implementationConfig = extractEmbeddedJson(implementationBundleText, 'IMPLEMENTATION_CONFIG');
  const runtimeBundle = extractEmbeddedJson(implementationBundleText, 'RUNTIME_BUNDLE');
  const shortcut = process.env.AITRANS_CAPTURE_SHORTCUT || 'CommandOrControl+Shift+1';

  return {
    repoRoot: getRepoRoot(),
    projectRoot: getProjectRoot(),
    generatedDir,
    productSpecPath,
    manifestPath,
    implementationBundlePath,
    productSpec,
    manifest,
    implementationConfig,
    runtimeBundle,
    shortcut,
  };
}

module.exports = {
  getRepoRoot,
  getProjectRoot,
  loadProjectConfig,
};
