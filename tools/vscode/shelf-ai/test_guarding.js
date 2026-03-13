const assert = require("assert");
const path = require("path");

const {
  classifyWorkspaceChanges,
  inferConfiguredFrameworks,
  isProtectedGeneratedPath,
  isWatchedPath,
  resolveProjectProductSpecPath,
  shouldRunMypyForRelPath,
} = require("./guarding");

const repoRoot = path.resolve(__dirname, "..", "..", "..");

function main() {
  assert(isWatchedPath("projects/knowledge_base_basic/product_spec.toml"));
  assert(isWatchedPath("scripts/validate_strict_mapping.py"));
  assert(isWatchedPath("tools/vscode/shelf-ai/extension.js"));
  assert(!isWatchedPath("../outside.txt"));

  assert(isProtectedGeneratedPath("projects/knowledge_base_basic/generated/product_spec.json"));
  assert(isProtectedGeneratedPath("docs/hierarchy/shelf_framework_tree.json"));
  assert(isProtectedGeneratedPath("docs/hierarchy/shelf_governance_tree.json"));
  assert(!isProtectedGeneratedPath("projects/knowledge_base_basic/product_spec.toml"));

  assert(shouldRunMypyForRelPath("src/project_runtime/knowledge_base.py"));
  assert(shouldRunMypyForRelPath("scripts/materialize_project.py"));
  assert(shouldRunMypyForRelPath("tests/test_project_runtime.py"));
  assert(!shouldRunMypyForRelPath("tools/vscode/shelf-ai/extension.js"));

  assert.strictEqual(
    resolveProjectProductSpecPath(repoRoot, "projects/knowledge_base_basic/implementation_config.toml"),
    path.join(repoRoot, "projects", "knowledge_base_basic", "product_spec.toml")
  );
  assert.strictEqual(
    resolveProjectProductSpecPath(repoRoot, "projects/knowledge_base_basic/product_spec/chat.toml"),
    path.join(repoRoot, "projects", "knowledge_base_basic", "product_spec.toml")
  );
  assert.strictEqual(
    resolveProjectProductSpecPath(repoRoot, "projects/knowledge_base_basic/generated/product_spec.json"),
    path.join(repoRoot, "projects", "knowledge_base_basic", "product_spec.toml")
  );

  const frameworks = inferConfiguredFrameworks(`
[framework]
frontend = "framework/frontend/L2-M0-前端框架标准模块.md"
domain = "framework/knowledge_base/L2-M0-知识库工作台场景模块.md"
backend = "framework/backend/L2-M0-知识库接口框架标准模块.md"
`);
  assert(frameworks.has("frontend"));
  assert(frameworks.has("knowledge_base"));
  assert(frameworks.has("backend"));

  const productPlan = classifyWorkspaceChanges(repoRoot, ["projects/knowledge_base_basic/product_spec.toml"]);
  assert(productPlan.shouldMaterialize, "product spec changes should trigger materialization");
  assert.strictEqual(productPlan.materializeProjects.length, 1);
  assert(productPlan.materializeProjects[0].endsWith("projects/knowledge_base_basic/product_spec.toml"));

  const splitProductPlan = classifyWorkspaceChanges(repoRoot, ["projects/knowledge_base_basic/product_spec/chat.toml"]);
  assert(splitProductPlan.shouldMaterialize, "split product spec changes should trigger materialization");
  assert.strictEqual(splitProductPlan.materializeProjects.length, 1);
  assert(splitProductPlan.materializeProjects[0].endsWith("projects/knowledge_base_basic/product_spec.toml"));

  const frameworkPlan = classifyWorkspaceChanges(repoRoot, ["framework/knowledge_base/L1-M0-知识库界面骨架模块.md"]);
  assert(frameworkPlan.shouldMaterialize, "framework changes should trigger materialization");
  assert(
    frameworkPlan.materializeProjects.some((item) => item.endsWith("projects/knowledge_base_basic/product_spec.toml")),
    "knowledge_base framework changes should materialize the matching project"
  );

  const generatedPlan = classifyWorkspaceChanges(repoRoot, ["projects/knowledge_base_basic/generated/product_spec.json"]);
  assert.strictEqual(generatedPlan.protectedGeneratedPaths.length, 1);
  assert.strictEqual(generatedPlan.materializeProjects.length, 0);

  const workspaceTreePlan = classifyWorkspaceChanges(repoRoot, ["docs/hierarchy/shelf_governance_tree.json"]);
  assert.strictEqual(workspaceTreePlan.protectedGeneratedPaths.length, 1);

  const frameworkTreePlan = classifyWorkspaceChanges(repoRoot, ["docs/hierarchy/shelf_framework_tree.json"]);
  assert.strictEqual(frameworkTreePlan.protectedGeneratedPaths.length, 1);
}

main();
