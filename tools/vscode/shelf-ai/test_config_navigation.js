const assert = require("assert");
const fs = require("fs");
const path = require("path");
const {
  findCurrentTomlSection,
  isProjectConfigFile,
  resolveConfigToCodeTarget,
} = require("./config_navigation");

const repoRoot = path.resolve(__dirname, "..", "..", "..");

function discoverWorkspaceProjectFile() {
  const projectsDir = path.join(repoRoot, "projects");
  if (!fs.existsSync(projectsDir) || !fs.statSync(projectsDir).isDirectory()) {
    return "";
  }
  const projectFiles = fs.readdirSync(projectsDir)
    .map((entry) => path.join(projectsDir, entry, "project.toml"))
    .filter((filePath) => fs.existsSync(filePath) && fs.statSync(filePath).isFile())
    .sort();
  return projectFiles[0] || "";
}

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

function findFirstExactSection(text) {
  const lines = String(text || "").split(/\r?\n/);
  for (let index = 0; index < lines.length; index += 1) {
    const match = /^\s*\[(exact\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)\]\s*$/.exec(lines[index] || "");
    if (match) {
      return {
        sectionName: match[1],
        line: index,
      };
    }
  }
  return null;
}

function main() {
  const projectFilePath = discoverWorkspaceProjectFile();
  assert(projectFilePath, "at least one workspace project.toml should exist");
  assert(isProjectConfigFile(projectFilePath, repoRoot), "project.toml should be recognized as project config file");

  const text = fs.readFileSync(projectFilePath, "utf8");
  const firstExactSection = findFirstExactSection(text);
  assert(firstExactSection, "at least one exact.<framework>.<boundary> section should exist");
  const exactSectionLine = firstExactSection.line;
  const exactSectionName = firstExactSection.sectionName;
  const boundaryToken = exactSectionName.split(".").pop();
  assert(boundaryToken, "exact section should include boundary token");

  const sectionInfo = findCurrentTomlSection(text, exactSectionLine + 1);
  assert(sectionInfo, "section info should be resolved inside exact boundary section");
  assert.strictEqual(sectionInfo.sectionName, exactSectionName);

  const codeTarget = resolveConfigToCodeTarget({
    repoRoot,
    filePath: projectFilePath,
    text,
    line: exactSectionLine + 1,
    character: 0,
  });
  assert(codeTarget, "config section should resolve to code anchor target");
  assert.strictEqual(codeTarget.boundaryId, boundaryToken.toUpperCase());
  assert(codeTarget.objectId.includes(`::static_param::${boundaryToken}`));
  assert.strictEqual(codeTarget.targetKind, "code_correspondence");
  assert(codeTarget.filePath.endsWith(path.join("src", "project_runtime", "code_layer.py")));
  assert(Number.isInteger(codeTarget.line) && codeTarget.line >= 0, "code target should include valid line");

  const codeLayerPath = path.join(repoRoot, "src", "project_runtime", "code_layer.py");
  const codeLayerText = fs.readFileSync(codeLayerPath, "utf8");
  const expectedBoundaryLine = findLineContaining(
    codeLayerText,
    `_require_boundary_context_value(boundary_context, "${boundaryToken.toUpperCase()}")`
  );
  if (expectedBoundaryLine > 0) {
    assert.strictEqual(
      codeTarget.line,
      expectedBoundaryLine - 1,
      "exact boundary section should resolve to module static params consumer anchor"
    );
  }

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
