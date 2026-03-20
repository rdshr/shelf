const assert = require("assert");
const path = require("path");

const {
  SUPPORTED_CORRESPONDENCE_SCHEMA_VERSION,
  buildValidationIssues,
  loadCorrespondenceSnapshot,
  mergeIssueLists,
  normalizeCorrespondencePayload,
  readCorrespondenceApi,
  resolvePrimaryNavigationTarget,
} = require("./correspondence_runtime");

const repoRoot = path.resolve(__dirname, "..", "..", "..");

function discoverWorkspaceProjectFile() {
  const projectsDir = path.join(repoRoot, "projects");
  if (!projectsDir || !require("fs").existsSync(projectsDir)) {
    return "";
  }
  const fs = require("fs");
  const projectFiles = fs.readdirSync(projectsDir)
    .map((entry) => path.join(projectsDir, entry, "project.toml"))
    .filter((filePath) => fs.existsSync(filePath) && fs.statSync(filePath).isFile())
    .sort();
  return projectFiles[0] || "";
}

function deepClone(value) {
  return JSON.parse(JSON.stringify(value));
}

function makeTarget(overrides = {}) {
  return {
    target_kind: "code_correspondence",
    layer: "code",
    file_path: "src/project_runtime/code_layer.py",
    start_line: 10,
    end_line: 12,
    symbol: "demo.symbol",
    label: "Demo target",
    is_primary: true,
    is_editable: true,
    is_deprecated_alias: false,
    ...overrides,
  };
}

function makeObject(overrides = {}) {
  return {
    object_kind: "module",
    object_id: "demo.L0.M0",
    owner_module_id: "demo.L0.M0",
    display_name: "DemoModule",
    materialization_kind: "runtime_dynamic_type",
    primary_nav_target_kind: "code_correspondence",
    primary_edit_target_kind: "framework_definition",
    correspondence_anchor: makeTarget({ target_kind: "code_correspondence", is_primary: true }),
    implementation_anchor: makeTarget({
      target_kind: "code_implementation",
      start_line: 20,
      end_line: 21,
      is_primary: false,
    }),
    navigation_targets: [
      makeTarget({ target_kind: "code_correspondence", is_primary: true }),
      makeTarget({
        target_kind: "framework_definition",
        layer: "framework",
        file_path: "framework/demo/L0-M0-示例模块.md",
        start_line: 1,
        end_line: 12,
        symbol: "demo.L0.M0",
        label: "Framework definition",
        is_primary: false,
      }),
      makeTarget({
        target_kind: "code_implementation",
        start_line: 20,
        end_line: 21,
        is_primary: false,
      }),
    ],
    ...overrides,
  };
}

function main() {
  const projectFilePath = discoverWorkspaceProjectFile();
  assert(projectFilePath, "at least one workspace project.toml should exist");
  const snapshot = loadCorrespondenceSnapshot(repoRoot, { projectFilePath });
  assert(snapshot, "correspondence snapshot should load from fresh canonical");
  assert.strictEqual(
    snapshot.payload.correspondence_schema_version,
    SUPPORTED_CORRESPONDENCE_SCHEMA_VERSION
  );

  const rootPayload = readCorrespondenceApi(repoRoot, snapshot.endpoints.root, { projectFilePath });
  assert(rootPayload && typeof rootPayload === "object", "root correspondence endpoint should return payload");
  const objectIds = Object.keys(rootPayload.object_index || {});
  const moduleObjectId = objectIds.find((item) => /\.L\d+\.M\d+$/.test(item));
  assert(moduleObjectId, "root payload should expose at least one module object");

  const treePayload = readCorrespondenceApi(repoRoot, snapshot.endpoints.tree, { projectFilePath });
  assert(treePayload && typeof treePayload === "object", "tree endpoint should return payload");
  assert(Array.isArray(treePayload.tree) && treePayload.tree.length > 0, "tree endpoint should expose module entries");

  const ruleObjectId = objectIds.find((item) => /\.R\d+/.test(item));
  assert(ruleObjectId, "root payload should expose at least one rule object");
  const ruleObject = readCorrespondenceApi(
    repoRoot,
    `${snapshot.endpoints.objectBase}${encodeURIComponent(ruleObjectId)}`,
    { projectFilePath }
  );
  assert(ruleObject && typeof ruleObject === "object", "object endpoint should return a correspondence object");
  assert.strictEqual(ruleObject.object_id, ruleObjectId);
  assert.strictEqual(resolvePrimaryNavigationTarget(ruleObject)?.target_kind, ruleObject.primary_nav_target_kind);

  const moduleObject = rootPayload.object_index[moduleObjectId];
  assert(moduleObject && typeof moduleObject === "object");
  assert(moduleObject.materialization_kind);
  assert(
    moduleObject.navigation_targets.some((target) =>
      target.target_kind === "framework_definition"
      || target.target_kind === "config_source"
      || target.target_kind === "code_correspondence"
    ),
    "module objects should retain at least one stable cross-layer navigation target"
  );

  const correspondenceIssues = buildValidationIssues(
    {
      passed: false,
      rule_count: 1,
      error_count: 1,
      issues: [
        {
          issue_kind: "demo_issue",
          level: "error",
          reason: "Demo correspondence failure",
          object_ids: [ruleObjectId],
          primary_object_id: ruleObjectId,
        },
      ],
      issue_count_by_object: {
        [ruleObjectId]: 1,
      },
    },
    rootPayload.object_index
  );
  assert.strictEqual(correspondenceIssues.length, 1);
  assert(
    correspondenceIssues[0].message.includes(`[${ruleObjectId}]`),
    "validation issues should carry the primary object id"
  );
  assert.strictEqual(
    correspondenceIssues[0].file,
    resolvePrimaryNavigationTarget(ruleObject)?.file_path,
    "validation summary issues should anchor to the primary navigation target"
  );

  const mergedIssues = mergeIssueLists(correspondenceIssues, [
    {
      message: "Legacy validation issue",
      file: "projects/demo/project.toml",
      line: 1,
      column: 1,
      code: "ARCHSYNC_MAPPING",
    },
  ]);
  assert.strictEqual(mergedIssues.length, 2, "merged issues should keep correspondence issues and legacy fallbacks");
  assert.strictEqual(
    mergedIssues[0].code,
    "SHELF_CORRESPONDENCE",
    "correspondence validation issues should remain the primary issue source"
  );

  const invalidSchemaPayload = deepClone(rootPayload);
  invalidSchemaPayload.correspondence_schema_version = SUPPORTED_CORRESPONDENCE_SCHEMA_VERSION + 1;
  assert.throws(
    () => normalizeCorrespondencePayload(invalidSchemaPayload),
    /unsupported correspondence schema version/
  );

  assert.throws(
    () => normalizeCorrespondencePayload({
      correspondence_schema_version: SUPPORTED_CORRESPONDENCE_SCHEMA_VERSION,
      objects: [
        makeObject({
          object_id: "demo.L0.M1",
          navigation_targets: [
            makeTarget({
              target_kind: "code_implementation",
              is_primary: true,
            }),
          ],
          primary_nav_target_kind: "code_implementation",
          primary_edit_target_kind: "code_implementation",
          correspondence_anchor: makeTarget({
            target_kind: "code_implementation",
            is_primary: true,
          }),
        }),
      ],
      object_index: {},
      tree: [],
      validation_summary: {},
    }),
    /runtime_dynamic_type requires a fallback target/
  );
}

main();
