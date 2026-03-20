const assert = require("assert");
const fs = require("fs");
const os = require("os");
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

function writeFile(filePath, text) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, text);
}

function setMtime(filePath, timeMs) {
  const time = new Date(timeMs);
  fs.utimesSync(filePath, time, time);
}

function createFixtureRepo() {
  const repoRoot = fs.mkdtempSync(path.join(os.tmpdir(), "shelf-correspondence-runtime-"));
  const projectFilePath = path.join(repoRoot, "projects", "demo", "project.toml");
  const frameworkFilePath = path.join(repoRoot, "framework", "demo", "L0-M0-示例模块.md");
  const canonicalPath = path.join(repoRoot, "projects", "demo", "generated", "canonical.json");

  writeFile(
    projectFilePath,
    `
[project]
project_id = "demo"

[framework]

[[framework.modules]]
role = "demo"
framework_file = "framework/demo/L0-M0-示例模块.md"
`
  );
  writeFile(frameworkFilePath, "# demo framework\n");

  const moduleCodeTarget = makeTarget({
    target_kind: "code_correspondence",
    layer: "code",
    file_path: "src/project_runtime/code_layer.py",
    symbol: "demo.L0.M0",
    is_primary: true,
  });
  const moduleFrameworkTarget = makeTarget({
    target_kind: "framework_definition",
    layer: "framework",
    file_path: "framework/demo/L0-M0-示例模块.md",
    start_line: 1,
    end_line: 8,
    symbol: "demo.L0.M0",
    label: "demo module",
    is_primary: false,
  });
  const ruleFrameworkTarget = makeTarget({
    target_kind: "framework_definition",
    layer: "framework",
    file_path: "framework/demo/L0-M0-示例模块.md",
    start_line: 2,
    end_line: 4,
    symbol: "demo.L0.M0.R0",
    label: "demo rule",
    is_primary: true,
  });

  writeFile(
    canonicalPath,
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
          modules: [],
        },
        code: {
          modules: [],
        },
        evidence: {
          modules: [],
        },
        correspondence: {
          correspondence_schema_version: SUPPORTED_CORRESPONDENCE_SCHEMA_VERSION,
          objects: [
            {
              object_kind: "module",
              object_id: "demo.L0.M0",
              owner_module_id: "demo.L0.M0",
              display_name: "DemoModule",
              materialization_kind: "runtime_dynamic_type",
              primary_nav_target_kind: "code_correspondence",
              primary_edit_target_kind: "framework_definition",
              correspondence_anchor: moduleCodeTarget,
              implementation_anchor: moduleCodeTarget,
              navigation_targets: [moduleCodeTarget, moduleFrameworkTarget],
            },
            {
              object_kind: "rule",
              object_id: "demo.L0.M0.R0",
              owner_module_id: "demo.L0.M0",
              display_name: "R0",
              materialization_kind: "static_class",
              primary_nav_target_kind: "framework_definition",
              primary_edit_target_kind: "framework_definition",
              correspondence_anchor: ruleFrameworkTarget,
              implementation_anchor: ruleFrameworkTarget,
              navigation_targets: [ruleFrameworkTarget],
            },
          ],
          tree: [
            {
              object_id: "demo.L0.M0",
              children: [
                {
                  object_id: "demo.L0.M0.R0",
                  children: [],
                },
              ],
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
  setMtime(projectFilePath, baseTime);
  setMtime(frameworkFilePath, baseTime);
  setMtime(canonicalPath, baseTime + 5_000);

  return {
    repoRoot,
    projectFilePath,
    cleanup: () => fs.rmSync(repoRoot, { recursive: true, force: true }),
  };
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
  const fixture = createFixtureRepo();
  try {
    const repoRoot = fixture.repoRoot;
    const projectFilePath = fixture.projectFilePath;
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
    assert(
      correspondenceIssues[0].message.includes("Demo correspondence failure"),
      "custom correspondence reasons should be preserved when no localization rule matches"
    );
    assert.strictEqual(
      correspondenceIssues[0].file,
      resolvePrimaryNavigationTarget(ruleObject)?.file_path,
      "validation summary issues should anchor to the primary navigation target"
    );

    const localizedIssues = buildValidationIssues(
      {
        passed: false,
        rule_count: 1,
        error_count: 0,
        issues: [
          {
            issue_kind: "audit_drift",
            level: "warning",
            reason: `declared boundary not effectively read by base: ${moduleObjectId}.B1 -> CAPACITY`,
            object_ids: [moduleObjectId],
            primary_object_id: moduleObjectId,
          },
          {
            issue_kind: "audit_drift",
            level: "warning",
            reason: `declared rule boundary not effectively read: ${ruleObjectId} -> MESSAGE`,
            object_ids: [ruleObjectId],
            primary_object_id: ruleObjectId,
          },
        ],
        issue_count_by_object: {
          [moduleObjectId]: 1,
          [ruleObjectId]: 1,
        },
      },
      rootPayload.object_index
    );
    assert(
      localizedIssues[0].message.includes("基类声明的参数边界未被有效读取"),
      "base-boundary drift should be localized to Chinese by default"
    );
    assert(
      localizedIssues[1].message.includes("规则声明的参数边界未被有效读取"),
      "rule-boundary drift should be localized to Chinese by default"
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
      /不支持的 correspondence schema 版本/
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
      /runtime_dynamic_type 缺少可回退目标/
    );
  } finally {
    fixture.cleanup();
  }
}

main();
