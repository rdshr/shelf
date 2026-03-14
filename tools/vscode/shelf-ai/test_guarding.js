const assert = require("assert");
const path = require("path");

const {
  classifyWorkspaceChanges,
  discoverProjectFiles,
  inferConfiguredFrameworks,
  isProtectedGeneratedPath,
  isWatchedPath,
  resolveProjectFilePath,
  shouldRunMypyForRelPath,
} = require("./guarding");

const repoRoot = path.resolve(__dirname, "..", "..", "..");

function main() {
  assert(isWatchedPath("projects/knowledge_base_basic/project.toml"));
  assert(isWatchedPath("scripts/validate_strict_mapping.py"));
  assert(isWatchedPath("tools/vscode/shelf-ai/extension.js"));
  assert(!isWatchedPath("../outside.txt"));

  assert(isProtectedGeneratedPath("projects/knowledge_base_basic/generated/canonical_graph.json"));
  assert(isProtectedGeneratedPath("docs/hierarchy/shelf_framework_tree.json"));
  assert(isProtectedGeneratedPath("docs/hierarchy/shelf_governance_tree.json"));
  assert(!isProtectedGeneratedPath("projects/knowledge_base_basic/project.toml"));

  assert(shouldRunMypyForRelPath("src/project_runtime/knowledge_base.py"));
  assert(shouldRunMypyForRelPath("scripts/materialize_project.py"));
  assert(shouldRunMypyForRelPath("tests/test_project_runtime.py"));
  assert(!shouldRunMypyForRelPath("tools/vscode/shelf-ai/extension.js"));

  assert.strictEqual(
    resolveProjectFilePath(repoRoot, "projects/knowledge_base_basic/project.toml"),
    path.join(repoRoot, "projects", "knowledge_base_basic", "project.toml")
  );
  assert.strictEqual(
    resolveProjectFilePath(repoRoot, "projects/knowledge_base_basic/generated/canonical_graph.json"),
    path.join(repoRoot, "projects", "knowledge_base_basic", "project.toml")
  );

  const projectFiles = discoverProjectFiles(repoRoot);
  assert(projectFiles.some((item) => item.endsWith("projects/knowledge_base_basic/project.toml")));

  const frameworks = inferConfiguredFrameworks(`
[selection.root_modules]
frontend = "framework/frontend/L2-M0-前端框架标准模块.md"
knowledge_base = "framework/knowledge_base/L2-M0-知识库工作台场景模块.md"
backend = "framework/backend/L2-M0-知识库接口框架标准模块.md"
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

  const generatedPlan = classifyWorkspaceChanges(repoRoot, ["projects/knowledge_base_basic/generated/canonical_graph.json"]);
  assert.strictEqual(generatedPlan.protectedGeneratedPaths.length, 1);
  assert.strictEqual(generatedPlan.materializeProjects.length, 0);
  assert.strictEqual(generatedPlan.protectedProjectFiles.length, 1);
}

main();
