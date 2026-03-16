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
  assert(isWatchedPath("projects/knowledge_base_basic/project.toml"));
  assert(isWatchedPath("scripts/validate_canonical.py"));
  assert(isWatchedPath("tools/vscode/shelf-ai/extension.js"));
  assert(!isWatchedPath("../outside.txt"));

  assert(isProtectedGeneratedPath("projects/knowledge_base_basic/generated/canonical.json"));
  assert(!isProtectedGeneratedPath("docs/hierarchy/shelf_framework_tree.json"));
  assert(!isProtectedGeneratedPath("docs/hierarchy/shelf_evidence_tree.json"));
  assert(!isProtectedGeneratedPath("projects/knowledge_base_basic/project.toml"));

  assert(shouldRunMypyForRelPath("src/project_runtime/compiler.py"));
  assert(shouldRunMypyForRelPath("scripts/materialize_project.py"));
  assert(shouldRunMypyForRelPath("tests/test_knowledge_base_runtime.py"));
  assert(!shouldRunMypyForRelPath("tools/vscode/shelf-ai/extension.js"));

  assert.strictEqual(
    resolveProjectFilePath(repoRoot, "projects/knowledge_base_basic/project.toml"),
    path.join(repoRoot, "projects", "knowledge_base_basic", "project.toml")
  );
  assert.strictEqual(
    resolveProjectFilePath(repoRoot, "projects/knowledge_base_basic/generated/canonical.json"),
    path.join(repoRoot, "projects", "knowledge_base_basic", "project.toml")
  );

  const projectFiles = discoverProjectFiles(repoRoot);
  assert(projectFiles.some((item) => item.endsWith("projects/knowledge_base_basic/project.toml")));

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

  const projectPlan = classifyWorkspaceChanges(repoRoot, ["projects/knowledge_base_basic/project.toml"]);
  assert(projectPlan.shouldMaterialize, "project config changes should trigger materialization");
  assert.strictEqual(projectPlan.materializeProjects.length, 1);
  assert(projectPlan.materializeProjects[0].endsWith("projects/knowledge_base_basic/project.toml"));

  const frameworkPlan = classifyWorkspaceChanges(repoRoot, ["framework/knowledge_base/L1-M0-知识库界面骨架模块.md"]);
  assert(frameworkPlan.shouldMaterialize, "framework changes should trigger materialization");
  assert(
    frameworkPlan.materializeProjects.some((item) => item.endsWith("projects/knowledge_base_basic/project.toml")),
    "knowledge_base framework changes should materialize the matching project"
  );

  const generatedPlan = classifyWorkspaceChanges(repoRoot, ["projects/knowledge_base_basic/generated/canonical.json"]);
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
