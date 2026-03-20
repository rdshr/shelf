const assert = require("assert");
const fs = require("fs");
const os = require("os");
const path = require("path");

const {
  buildRuntimeEvidenceTreeModel,
  buildRuntimeFrameworkTreeModel,
  buildRuntimeTreeModel,
} = require("./tree_runtime_models");

function writeFile(filePath, content) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, content, "utf8");
}

function setMtime(filePath, timeMs) {
  const time = new Date(timeMs);
  fs.utimesSync(filePath, time, time);
}

function createFreshFrameworkRepoFixture() {
  const fixtureRoot = fs.mkdtempSync(path.join(os.tmpdir(), "shelf-tree-runtime-fresh-"));
  const frameworkL0 = path.join(fixtureRoot, "framework", "demo", "L0-M0-source.md");
  const frameworkL1 = path.join(fixtureRoot, "framework", "demo", "L1-M0-aggregate.md");
  const projectFile = path.join(fixtureRoot, "projects", "demo", "project.toml");
  const canonicalPath = path.join(fixtureRoot, "projects", "demo", "generated", "canonical.json");
  const codeLayerPath = path.join(fixtureRoot, "src", "project_runtime", "code_layer.py");
  const evidenceLayerPath = path.join(fixtureRoot, "src", "project_runtime", "evidence_layer.py");

  writeFile(frameworkL0, "# L0-M0 Source Module\n");
  writeFile(frameworkL1, "# L1-M0 Aggregate Module\n");
  writeFile(
    projectFile,
    [
      "[project]",
      "project_id = \"demo\"",
      "",
      "[framework]",
      "",
      "[[framework.modules]]",
      "role = \"demo\"",
      "framework_file = \"framework/demo/L0-M0-source.md\"",
      "",
      "[[framework.modules]]",
      "role = \"demo\"",
      "framework_file = \"framework/demo/L1-M0-aggregate.md\"",
      "",
    ].join("\n")
  );
  writeFile(codeLayerPath, "def demo():\n    return 'ok'\n");
  writeFile(evidenceLayerPath, "def evidence():\n    return 'ok'\n");

  const l0CodeTarget = {
    target_kind: "framework_definition",
    layer: "framework",
    file_path: "framework/demo/L0-M0-source.md",
    start_line: 1,
    end_line: 1,
    symbol: "demo.L0.M0",
    label: "L0 module",
    is_primary: true,
    is_editable: true,
    is_deprecated_alias: false,
  };
  const l1CodeTarget = {
    target_kind: "code_correspondence",
    layer: "code",
    file_path: "src/project_runtime/code_layer.py",
    start_line: 1,
    end_line: 1,
    symbol: "demo.L1.M0",
    label: "L1 module",
    is_primary: true,
    is_editable: true,
    is_deprecated_alias: false,
  };
  writeFile(
    canonicalPath,
    JSON.stringify(
      {
        project: {
          project_id: "demo",
          display_name: "demo",
          version: "0.0.1",
          description: "demo fixture",
        },
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
        config: {
          modules: [
            {
              module_id: "demo.L0.M0",
              source_ref: { file_path: "projects/demo/project.toml", line: 1 },
            },
            {
              module_id: "demo.L1.M0",
              source_ref: { file_path: "projects/demo/project.toml", line: 1 },
            },
          ],
        },
        code: {
          modules: [
            {
              module_id: "demo.L0.M0",
              source_ref: { file_path: "src/project_runtime/code_layer.py", line: 1 },
            },
            {
              module_id: "demo.L1.M0",
              source_ref: { file_path: "src/project_runtime/code_layer.py", line: 1 },
            },
          ],
        },
        evidence: {
          modules: [
            {
              module_id: "demo.L0.M0",
              source_ref: { file_path: "src/project_runtime/evidence_layer.py", line: 1 },
            },
            {
              module_id: "demo.L1.M0",
              source_ref: { file_path: "src/project_runtime/evidence_layer.py", line: 1 },
            },
          ],
        },
        correspondence: {
          correspondence_schema_version: 1,
          objects: [
            {
              object_kind: "module",
              object_id: "demo.L0.M0",
              owner_module_id: "demo.L0.M0",
              display_name: "demo.L0.M0",
              materialization_kind: "static_class",
              primary_nav_target_kind: "framework_definition",
              primary_edit_target_kind: "framework_definition",
              correspondence_anchor: l0CodeTarget,
              implementation_anchor: l0CodeTarget,
              navigation_targets: [l0CodeTarget],
            },
            {
              object_kind: "module",
              object_id: "demo.L1.M0",
              owner_module_id: "demo.L1.M0",
              display_name: "demo.L1.M0",
              materialization_kind: "static_class",
              primary_nav_target_kind: "code_correspondence",
              primary_edit_target_kind: "code_correspondence",
              correspondence_anchor: l1CodeTarget,
              implementation_anchor: l1CodeTarget,
              navigation_targets: [l1CodeTarget],
            },
          ],
          tree: [
            {
              module_id: "demo.L0.M0",
              module_object_id: "demo.L0.M0",
              bases: [],
              rules: [],
              boundaries: [],
              static_params: [],
              runtime_params: [],
            },
            {
              module_id: "demo.L1.M0",
              module_object_id: "demo.L1.M0",
              bases: [],
              rules: ["demo.L1.M0.R1"],
              boundaries: [],
              static_params: [],
              runtime_params: [],
            },
          ],
          validation_summary: {
            passed: true,
            rule_count: 0,
            error_count: 0,
            issues: [],
            issue_count_by_object: {},
          },
        },
      },
      null,
      2
    )
  );

  const baseTime = Date.now() - 60_000;
  setMtime(projectFile, baseTime);
  setMtime(frameworkL0, baseTime);
  setMtime(frameworkL1, baseTime);
  setMtime(codeLayerPath, baseTime);
  setMtime(evidenceLayerPath, baseTime);
  setMtime(canonicalPath, baseTime + 5_000);

  return fixtureRoot;
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
  const freshFixtureRoot = createFreshFrameworkRepoFixture();
  try {
    const frameworkModel = buildRuntimeFrameworkTreeModel(freshFixtureRoot);
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
    const linkedNode = frameworkModel.nodes.find((node) =>
      node.objectId
      && frameworkModel.objectIndex
      && frameworkModel.objectIndex[node.objectId]
    );
    assert(linkedNode, "framework model should include at least one node linked to correspondence object index");
    assert(linkedNode.defaultTarget, "module node should expose a primary navigation target");
    assert.strictEqual(
      linkedNode.defaultTarget.target_kind,
      frameworkModel.objectIndex[linkedNode.objectId].primary_nav_target_kind,
      "tree node open target should follow correspondence primary_nav_target_kind"
    );
    assert(
      Array.isArray(linkedNode.relatedObjectIds),
      "module node should expose correspondence-related object ids for inspector usage"
    );
    assert(
      frameworkModel.edges.length > 0 || frameworkModel.description.includes("fallback"),
      "framework model should either include canonical edges or clearly mark fallback mode"
    );

    const evidenceModel = buildRuntimeEvidenceTreeModel(freshFixtureRoot);
    assert.strictEqual(evidenceModel.kind, "evidence");
    assert(evidenceModel.nodes.length > 0, "evidence model should have nodes");
    assert(evidenceModel.layoutMode === "global_levels", "evidence model should keep global layout");
    assert(
      evidenceModel.edges.every((edge) => edge.relation === "tree_child"),
      "evidence edges should stay in tree_child relation"
    );

    const frameworkViaDispatcher = buildRuntimeTreeModel(freshFixtureRoot, "framework");
    const evidenceViaDispatcher = buildRuntimeTreeModel(freshFixtureRoot, "evidence");
    assert.strictEqual(frameworkViaDispatcher.kind, "framework");
    assert.strictEqual(evidenceViaDispatcher.kind, "evidence");
  } finally {
    fs.rmSync(freshFixtureRoot, { recursive: true, force: true });
  }

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
