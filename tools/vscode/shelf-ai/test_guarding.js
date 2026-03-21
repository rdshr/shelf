const assert = require("assert");
const fs = require("fs");
const os = require("os");
const path = require("path");

const {
  canonicalPathForProjectFile,
  classifyWorkspaceChanges,
  discoverProjectFiles,
  getProjectCanonicalFreshness,
  inferConfiguredFrameworks,
  isProtectedGeneratedPath,
  isWatchedPath,
  resolveProjectFilePath,
  shouldRunMypyForRelPath,
  summarizeCanonicalFreshness,
} = require("./guarding");

const repoRoot = path.resolve(__dirname, "..", "..", "..");

function writeFile(filePath, text) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, text);
}

function setMtime(filePath, timeMs) {
  const time = new Date(timeMs);
  fs.utimesSync(filePath, time, time);
}

function main() {
  const projectFiles = discoverProjectFiles(repoRoot);
  assert(projectFiles.length >= 1);
  const firstProjectFile = projectFiles[0];
  const firstProjectId = path.basename(path.dirname(firstProjectFile));
  const firstProjectRelPath = `projects/${firstProjectId}/project.toml`;
  const firstProjectCanonicalRelPath = `projects/${firstProjectId}/generated/canonical.json`;

  assert(isWatchedPath(firstProjectRelPath));
  assert(isWatchedPath("scripts/validate_canonical.py"));
  assert(isWatchedPath("tools/vscode/shelf-ai/extension.js"));
  assert(!isWatchedPath("../outside.txt"));

  assert(isProtectedGeneratedPath(firstProjectCanonicalRelPath));
  assert(!isProtectedGeneratedPath("docs/hierarchy/shelf_framework_tree.json"));
  assert(!isProtectedGeneratedPath("docs/hierarchy/shelf_evidence_tree.json"));
  assert(!isProtectedGeneratedPath(firstProjectRelPath));

  assert(shouldRunMypyForRelPath("src/project_runtime/compiler.py"));
  assert(shouldRunMypyForRelPath("scripts/materialize_project.py"));
  assert(shouldRunMypyForRelPath("tests/test_knowledge_base_runtime.py"));
  assert(!shouldRunMypyForRelPath("tools/vscode/shelf-ai/extension.js"));

  assert.strictEqual(
    resolveProjectFilePath(repoRoot, firstProjectRelPath),
    firstProjectFile
  );
  assert.strictEqual(
    resolveProjectFilePath(repoRoot, firstProjectCanonicalRelPath),
    firstProjectFile
  );

  const frameworks = inferConfiguredFrameworks(`
[[framework.modules]]
role = "frontend"
framework_file = "framework/frontend/L2-M0-前端框架标准模块.md"

[[framework.modules]]
role = "knowledge_base"
framework_file = "framework/knowledge_base/L2-M0-知识库工作台场景模块.md"

[[framework.modules]]
role = "backend"
framework_file = "framework/backend/L2-M0-知识库接口框架标准模块.md"
`);
  assert(frameworks.has("frontend"));
  assert(frameworks.has("knowledge_base"));
  assert(frameworks.has("backend"));

  const projectPlan = classifyWorkspaceChanges(repoRoot, [firstProjectRelPath]);
  assert(projectPlan.shouldMaterialize, "project config changes should trigger materialization");
  assert.strictEqual(projectPlan.materializeProjects.length, 1);
  assert.strictEqual(projectPlan.materializeProjects[0], firstProjectFile);

  const configuredFrameworks = inferConfiguredFrameworks(fs.readFileSync(firstProjectFile, "utf8"));
  assert(configuredFrameworks.size >= 1, "project should configure at least one framework");
  const configuredFrameworkName = [...configuredFrameworks][0];
  const frameworkPlan = classifyWorkspaceChanges(
    repoRoot,
    [`framework/${configuredFrameworkName}/L0-M0-示例模块.md`]
  );
  assert(frameworkPlan.shouldMaterialize, "framework changes should trigger materialization");
  assert(
    frameworkPlan.materializeProjects.some((item) => item === firstProjectFile),
    "changed framework should materialize at least one matching project"
  );

  const generatedPlan = classifyWorkspaceChanges(
    repoRoot,
    [`projects/${firstProjectId}/generated/canonical.json`]
  );
  assert.strictEqual(generatedPlan.protectedGeneratedPaths.length, 1);
  assert.strictEqual(generatedPlan.materializeProjects.length, 0);
  assert.strictEqual(generatedPlan.protectedProjectFiles.length, 1);

  const tempRepoRoot = fs.mkdtempSync(path.join(os.tmpdir(), "shelf-guarding-"));
  try {
    const tempProjectPath = path.join(tempRepoRoot, "projects", "demo", "project.toml");
    const tempFrameworkPath = path.join(tempRepoRoot, "framework", "demo", "L0-M0-示例模块.md");
    const tempCodePath = path.join(tempRepoRoot, "src", "demo_runtime.js");
    const tempEvidencePath = path.join(tempRepoRoot, "src", "demo_evidence.js");
    const tempCanonicalPath = canonicalPathForProjectFile(tempProjectPath);

    writeFile(
      tempProjectPath,
      `
[project]
project_id = "demo"

[framework]

[[framework.modules]]
role = "demo"
framework_file = "framework/demo/L0-M0-示例模块.md"
`
    );
    writeFile(tempFrameworkPath, "# 示例模块\n");
    writeFile(tempCodePath, "module.exports = {};\n");
    writeFile(tempEvidencePath, "module.exports = {};\n");
    writeFile(
      tempCanonicalPath,
      JSON.stringify(
        {
          framework: {
            modules: [
              {
                module_id: "demo.L0.M0",
                framework_file: "framework/demo/L0-M0-示例模块.md",
              },
            ],
          },
          config: {
            modules: [
              {
                module_id: "demo.L0.M0",
                source_ref: { file_path: "projects/demo/project.toml" },
              },
            ],
          },
          code: {
            modules: [
              {
                module_id: "demo.L0.M0",
                source_ref: { file_path: "src/demo_runtime.js" },
              },
            ],
          },
          evidence: {
            modules: [
              {
                module_id: "demo.L0.M0",
                source_ref: { file_path: "src/demo_evidence.js" },
              },
            ],
          },
        },
        null,
        2
      )
    );

    const baseTime = Date.now() - 60 * 1000;
    setMtime(tempProjectPath, baseTime);
    setMtime(tempFrameworkPath, baseTime);
    setMtime(tempCodePath, baseTime);
    setMtime(tempEvidencePath, baseTime);
    setMtime(tempCanonicalPath, baseTime + 5_000);

    const fresh = getProjectCanonicalFreshness(tempRepoRoot, tempProjectPath);
    assert.strictEqual(fresh.status, "fresh");
    assert(fresh.authoritativeSourceRelPaths.includes("framework/demo/L0-M0-示例模块.md"));
    assert(fresh.authoritativeSourceRelPaths.includes("src/demo_runtime.js"));

    setMtime(tempFrameworkPath, baseTime + 10_000);
    const stale = getProjectCanonicalFreshness(tempRepoRoot, tempProjectPath);
    assert.strictEqual(stale.status, "stale");
    assert(stale.newerSourceRelPaths.includes("framework/demo/L0-M0-示例模块.md"));

    fs.unlinkSync(tempCanonicalPath);
    const missing = getProjectCanonicalFreshness(tempRepoRoot, tempProjectPath);
    assert.strictEqual(missing.status, "missing");

    writeFile(tempCanonicalPath, "{not-json");
    const invalid = getProjectCanonicalFreshness(tempRepoRoot, tempProjectPath);
    assert.strictEqual(invalid.status, "invalid");

    const summary = summarizeCanonicalFreshness(tempRepoRoot);
    assert.strictEqual(summary.projects.length, 1);
    assert.strictEqual(summary.blockingProjects.length, 1);
    assert.strictEqual(summary.blockingProjects[0].status, "invalid");
  } finally {
    fs.rmSync(tempRepoRoot, { recursive: true, force: true });
  }
}

main();
