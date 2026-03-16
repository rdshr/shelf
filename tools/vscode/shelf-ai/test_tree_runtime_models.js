const assert = require("assert");
const path = require("path");

const {
  buildRuntimeEvidenceTreeModel,
  buildRuntimeFrameworkTreeModel,
  buildRuntimeTreeModel,
} = require("./tree_runtime_models");

const repoRoot = path.resolve(__dirname, "..", "..", "..");

function main() {
  const frameworkModel = buildRuntimeFrameworkTreeModel(repoRoot);
  assert.strictEqual(frameworkModel.kind, "framework");
  assert(frameworkModel.nodes.length > 0, "framework model should have nodes");
  assert(
    frameworkModel.layoutMode === "framework_columns",
    "framework model should use framework_columns layout"
  );
  assert(
    Array.isArray(frameworkModel.frameworkGroups) && frameworkModel.frameworkGroups.length > 0,
    "framework model should include framework groups"
  );
  assert(
    frameworkModel.nodes.some((node) => node.kind === "framework_module" && node.file.endsWith(".md") && node.group),
    "framework model should include module nodes with source file path and framework group"
  );
  assert(
    frameworkModel.nodes.some((node) => Array.isArray(node.capabilityItems) && Array.isArray(node.baseItems)),
    "framework model should expose hover metadata arrays"
  );
  assert(
    frameworkModel.edges.length > 0 || frameworkModel.description.includes("fallback"),
    "framework model should either include canonical edges or clearly mark fallback mode"
  );

  const evidenceModel = buildRuntimeEvidenceTreeModel(repoRoot);
  assert.strictEqual(evidenceModel.kind, "evidence");
  assert(evidenceModel.nodes.length > 0, "evidence model should have nodes");
  assert(evidenceModel.layoutMode === "global_levels", "evidence model should keep global layout");
  assert(
    evidenceModel.edges.every((edge) => edge.relation === "tree_child"),
    "evidence edges should stay in tree_child relation"
  );

  const frameworkViaDispatcher = buildRuntimeTreeModel(repoRoot, "framework");
  const evidenceViaDispatcher = buildRuntimeTreeModel(repoRoot, "evidence");
  assert.strictEqual(frameworkViaDispatcher.kind, "framework");
  assert.strictEqual(evidenceViaDispatcher.kind, "evidence");
}

main();
