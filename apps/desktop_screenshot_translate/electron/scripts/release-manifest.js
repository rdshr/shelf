const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const { loadProjectConfig } = require('../lib/project-config');

function resolveAppRoot() {
  return path.resolve(__dirname, '..');
}

function resolveDistRoot() {
  return path.join(resolveAppRoot(), 'dist');
}

function resolveReleaseNotesPath(config) {
  return path.join(config.projectRoot, 'release-notes', `${config.productSpec.project.version}.md`);
}

function hashFile(filePath) {
  const hash = crypto.createHash('sha256');
  hash.update(fs.readFileSync(filePath));
  return hash.digest('hex');
}

function getDistFiles(distRoot) {
  if (!fs.existsSync(distRoot)) {
    return [];
  }

  return fs.readdirSync(distRoot, { withFileTypes: true })
    .filter((entry) => entry.isFile())
    .map((entry) => ({
      name: entry.name,
      path: path.join(distRoot, entry.name),
    }));
}

function pickArtifact(files, expectedName) {
  return files.find((item) => item.name === expectedName) || null;
}

function describeArtifact(file) {
  const stat = fs.statSync(file.path);
  return {
    file_name: file.name,
    relative_path: path.join('dist', file.name),
    size_bytes: stat.size,
    sha256: hashFile(file.path),
  };
}

function main() {
  const config = loadProjectConfig();
  const distRoot = resolveDistRoot();
  const files = getDistFiles(distRoot);
  const version = config.productSpec.project.version;
  const arch = 'x64';
  const installerName = `desktop-screenshot-translate-${version}-${arch}.exe`;
  const portableName = `desktop-screenshot-translate-${version}-${arch}-portable.exe`;
  const installerBlockmapName = `${installerName}.blockmap`;

  const installer = pickArtifact(files, installerName);
  const portable = pickArtifact(files, portableName);
  const installerBlockmap = pickArtifact(files, installerBlockmapName);

  const failures = [];
  if (!installer) {
    failures.push(`missing installer artifact: ${path.join(distRoot, installerName)}`);
  }
  if (!portable) {
    failures.push(`missing portable artifact: ${path.join(distRoot, portableName)}`);
  }
  if (!installerBlockmap) {
    failures.push(`missing installer blockmap: ${path.join(distRoot, installerBlockmapName)}`);
  }

  if (failures.length > 0) {
    console.log('[FAILURES]');
    for (const item of failures) {
      console.log(`- ${item}`);
    }
    process.exitCode = 1;
    return;
  }

  const releaseNotesPath = resolveReleaseNotesPath(config);
  const manifest = {
    project_id: config.productSpec.project.project_id,
    display_name: config.productSpec.project.display_name,
    version,
    generated_at: new Date().toISOString(),
    channel: config.implementationConfig.release.channel,
    release_notes: path.relative(config.repoRoot, releaseNotesPath),
    artifacts: [describeArtifact(installer), describeArtifact(installerBlockmap), describeArtifact(portable)],
  };

  const outputPath = path.join(distRoot, `release-manifest-${version}.json`);
  fs.writeFileSync(outputPath, `${JSON.stringify(manifest, null, 2)}\n`, 'utf-8');

  console.log(`[OK] release manifest -> ${outputPath}`);
}

main();
