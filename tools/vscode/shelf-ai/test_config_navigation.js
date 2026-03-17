const assert = require("assert");
const fs = require("fs");
const path = require("path");
const {
  findCurrentTomlSection,
  isProjectConfigFile,
  resolveConfigToCodeTarget,
} = require("./config_navigation");

const repoRoot = path.resolve(__dirname, "..", "..", "..");
const projectFilePath = path.join(repoRoot, "projects", "knowledge_base_basic", "project.toml");

function findLineBySection(text, sectionName) {
  const lines = String(text || "").split(/\r?\n/);
  for (let index = 0; index < lines.length; index += 1) {
    if (lines[index].trim() === `[${sectionName}]`) {
      return index;
    }
  }
  return -1;
}

function findLineContaining(text, token) {
  const lines = String(text || "").split(/\r?\n/);
  for (let index = 0; index < lines.length; index += 1) {
    if (lines[index].includes(token)) {
      return index + 1;
    }
  }
  return -1;
}

function main() {
  assert(isProjectConfigFile(projectFilePath, repoRoot), "project.toml should be recognized as project config file");

  const text = fs.readFileSync(projectFilePath, "utf8");
  const exactSectionLine = findLineBySection(text, "exact.knowledge_base.fileset");
  assert(exactSectionLine >= 0, "exact.knowledge_base.fileset section should exist");

  const sectionInfo = findCurrentTomlSection(text, exactSectionLine + 1);
  assert(sectionInfo, "section info should be resolved inside exact boundary section");
  assert.strictEqual(sectionInfo.sectionName, "exact.knowledge_base.fileset");

  const codeTarget = resolveConfigToCodeTarget({
    repoRoot,
    filePath: projectFilePath,
    text,
    line: exactSectionLine + 1,
    character: 0,
  });
  assert(codeTarget, "config section should resolve to code anchor target");
  assert.strictEqual(codeTarget.boundaryId, "FILESET");
  assert.strictEqual(codeTarget.objectId, "knowledge_base.L0.M0::static_param::fileset");
  assert.strictEqual(codeTarget.targetKind, "code_correspondence");
  assert(codeTarget.filePath.endsWith(path.join("src", "project_runtime", "code_layer.py")));
  assert(Number.isInteger(codeTarget.line) && codeTarget.line >= 0, "code target should include valid line");

  const frontendSurfaceLine = findLineBySection(text, "exact.frontend.surface");
  assert(frontendSurfaceLine >= 0, "exact.frontend.surface section should exist");
  const frontendTarget = resolveConfigToCodeTarget({
    repoRoot,
    filePath: projectFilePath,
    text,
    line: frontendSurfaceLine + 1,
    character: 0,
  });
  assert(frontendTarget, "shared frontend surface section should resolve");
  assert.strictEqual(frontendTarget.moduleId, "frontend.L2.M0");
  assert.strictEqual(frontendTarget.boundaryId, "SURFACE");
  assert.strictEqual(frontendTarget.objectId, "frontend.L2.M0::static_param::surface");
  const codeLayerPath = path.join(repoRoot, "src", "project_runtime", "code_layer.py");
  const codeLayerText = fs.readFileSync(codeLayerPath, "utf8");
  const expectedSurfaceLine = findLineContaining(
    codeLayerText,
    '_require_boundary_context_value(boundary_context, "SURFACE")'
  );
  assert(expectedSurfaceLine > 0, "code layer should expose SURFACE boundary context anchor");
  assert.strictEqual(
    frontendTarget.line,
    expectedSurfaceLine - 1,
    "frontend surface should resolve to module static params consumer anchor"
  );

  const projectSectionLine = findLineBySection(text, "project");
  assert(projectSectionLine >= 0, "project section should exist");
  const noTarget = resolveConfigToCodeTarget({
    repoRoot,
    filePath: projectFilePath,
    text,
    line: projectSectionLine,
    character: 0,
  });
  assert.strictEqual(noTarget, null, "non-boundary sections should not resolve to code anchors");
}

main();
