const assert = require("assert");
const fs = require("fs");
const os = require("os");
const path = require("path");

const {
  buildRuntimeEvidenceTreeModel,
  buildRuntimeFrameworkTreeModel,
  buildRuntimeTreeModel,
} = require("./tree_runtime_models");

const repoRoot = path.resolve(__dirname, "..", "..", "..");

function writeFile(filePath, content) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, content, "utf8");
}

function createStaleFrameworkRepoFixture() {
  const fixtureRoot = fs.mkdtempSync(path.join(os.tmpdir(), "shelf-tree-runtime-"));
  const frameworkL0 = path.join(fixtureRoot, "framework", "demo", "L0-M0-source.md");
  const frameworkL1 = path.join(fixtureRoot, "framework", "demo", "L1-M0-aggregate.md");
  const projectFile = path.join(fixtureRoot, "projects", "demo", "project.toml");
  const canonicalPath = path.join(fixtureRoot, "projects", "demo", "generated", "canonical.json");

  writeFile(frameworkL0, "# L0-M0 Source Module\n");
  writeFile(frameworkL1, "# L1-M0 Aggregate Module\n");
  writeFile(
    projectFile,
    [
      "[project]",
      "project_id = \"demo\"",
      "",
      "[[framework]]",
      "framework_file = \"framework/demo/L0-M0-source.md\"",
      "",
      "[[framework]]",
      "framework_file = \"framework/demo/L1-M0-aggregate.md\"",
      "",
    ].join("\n")
  );
  writeFile(
    canonicalPath,
    JSON.stringify(
      {
        framework: {
          modules: [
            {
              module_id: "demo.L0.M0",
              framework_file: "framework/demo/L0-M0-source.md",
              title_cn: "source module",
              source_ref: { file_path: "framework/demo/L0-M0-source.md", line: 1 },
              export_surface: {
                source_ref: { file_path: "framework/demo/L0-M0-source.md", line: 1 },
                upstream_module_ids: [],
                rule_ids: [],
              },
            },
            {
              module_id: "demo.L1.M0",
              framework_file: "framework/demo/L1-M0-aggregate.md",
              title_cn: "aggregate module",
              source_ref: { file_path: "framework/demo/L1-M0-aggregate.md", line: 1 },
              export_surface: {
                source_ref: { file_path: "framework/demo/L1-M0-aggregate.md", line: 1 },
                upstream_module_ids: ["demo.L0.M0"],
                rule_ids: ["demo.L1.M0.R1"],
              },
            },
          ],
        },
        config: { modules: [] },
        code: { modules: [] },
        evidence: { modules: [] },
      },
      null,
      2
    )
  );

  const canonicalMtime = fs.statSync(canonicalPath).mtimeMs;
  const staleTime = new Date(canonicalMtime + 5000);
  fs.utimesSync(frameworkL1, staleTime, staleTime);

  return fixtureRoot;
}

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
    frameworkModel.objectIndex && typeof frameworkModel.objectIndex === "object",
    "framework model should expose correspondence object index"
  );
  assert(
    frameworkModel.validationSummary && typeof frameworkModel.validationSummary === "object",
    "framework model should expose correspondence validation summary"
  );
  const workbenchNode = frameworkModel.nodes.find((node) => node.id === "knowledge_base.L2.M0");
  assert(workbenchNode, "framework model should include knowledge_base.L2.M0 module node");
  assert.strictEqual(workbenchNode.objectId, "knowledge_base.L2.M0");
  assert(workbenchNode.defaultTarget, "module node should expose a primary navigation target");
  assert.strictEqual(
    workbenchNode.defaultTarget.target_kind,
    frameworkModel.objectIndex["knowledge_base.L2.M0"].primary_nav_target_kind,
    "tree node open target should follow correspondence primary_nav_target_kind"
  );
  assert(
    Array.isArray(workbenchNode.relatedObjectIds) && workbenchNode.relatedObjectIds.includes("knowledge_base.L2.M0.R1"),
    "module node should expose correspondence-related objects for the existing inspector"
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

  const staleFixtureRoot = createStaleFrameworkRepoFixture();
  try {
    const staleFrameworkModel = buildRuntimeFrameworkTreeModel(staleFixtureRoot);
    assert(
      staleFrameworkModel.edges.length > 0,
      "stale canonical should still keep framework module edges for authoring view"
    );
    assert(
      staleFrameworkModel.description.includes("Stale canonical topology is shown"),
      "stale canonical mode should be explicitly visible in description"
    );
    assert(
      !staleFrameworkModel.objectIndex,
      "stale canonical should not expose correspondence projection as formal navigation source"
    );
  } finally {
    fs.rmSync(staleFixtureRoot, { recursive: true, force: true });
  }
}

main();
