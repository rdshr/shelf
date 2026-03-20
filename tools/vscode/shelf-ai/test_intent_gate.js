const assert = require("assert");
const fs = require("fs");
const os = require("os");
const path = require("path");
const {
  TEMP_BYPASS_ALL_TOKEN,
  TEMP_BYPASS_SCOPES,
  analyzeIntentMapping,
  collectBoundaryEntries,
  isTemporaryBypassScopeEnabled,
  normalizeTemporaryBypassScopes,
} = require("./intent_gate");

function writeFixtureProjectCanonical(repoRoot, canonicalPayload) {
  const fixtureProjectDir = path.join(repoRoot, "projects", "demo");
  const fixtureGeneratedDir = path.join(fixtureProjectDir, "generated");
  fs.mkdirSync(fixtureGeneratedDir, { recursive: true });
  fs.writeFileSync(
    path.join(fixtureProjectDir, "project.toml"),
    `
[project]
project_id = "demo"

[framework]

[[framework.modules]]
role = "demo"
framework_file = "framework/demo/L0-M0-示例模块.md"
`,
    "utf8"
  );
  fs.mkdirSync(path.join(repoRoot, "framework", "demo"), { recursive: true });
  fs.writeFileSync(path.join(repoRoot, "framework", "demo", "L0-M0-示例模块.md"), "# demo\n", "utf8");
  fs.writeFileSync(
    path.join(fixtureGeneratedDir, "canonical.json"),
    JSON.stringify(canonicalPayload),
    "utf8"
  );
}

function main() {
  assert.deepStrictEqual(
    normalizeTemporaryBypassScopes(["save_guard", " SAVE_GUARD ", "unknown", "mapping_echo"]),
    ["mapping_echo", "save_guard"],
    "temporary bypass scopes should be normalized, deduplicated, and filtered"
  );
  assert.deepStrictEqual(
    normalizeTemporaryBypassScopes(["all", "save_guard"]),
    [TEMP_BYPASS_ALL_TOKEN],
    "all token should normalize to *"
  );
  for (const scope of TEMP_BYPASS_SCOPES) {
    assert(
      isTemporaryBypassScopeEnabled([TEMP_BYPASS_ALL_TOKEN], scope),
      `* should enable temporary bypass scope: ${scope}`
    );
  }

  const oneToOneFixtureRoot = fs.mkdtempSync(path.join(os.tmpdir(), "shelf-intent-gate-one-to-one-"));
  try {
    writeFixtureProjectCanonical(oneToOneFixtureRoot, {
      config: {
        modules: [
          {
            module_id: "demo.L0.M0",
            compiled_config_export: {
              boundary_bindings: [
                {
                  boundary_id: "DEMO_BOUNDARY",
                  primary_exact_path: "exact.demo.chat",
                  related_exact_paths: ["exact.demo.chat"],
                  primary_communication_path: "communication.demo.chat",
                  related_communication_paths: ["communication.demo.chat"],
                },
              ],
            },
          },
        ],
      },
    });

    const collected = collectBoundaryEntries(oneToOneFixtureRoot);
    assert(collected.entries.length > 0, "should load boundary entries from canonical");
    const sampleEntry = collected.entries[0];
    assert(sampleEntry && sampleEntry.moduleId && sampleEntry.boundaryId, "sample entry should expose module/boundary");
    assert(
      collected.entries.every((item) => item.exactPaths.length === 1 && item.exactPaths[0] === item.primaryExactPath),
      "boundary entries should map one-to-one on primary exact path"
    );
    assert(
      collected.entries.every((item) => item.communicationPaths.length === 1 && item.communicationPaths[0] === item.primaryCommunicationPath),
      "boundary entries should map one-to-one on primary communication path"
    );

    const mapped = analyzeIntentMapping({
      repoRoot: oneToOneFixtureRoot,
      intentText: `调整 ${sampleEntry.boundaryId} 映射到 ${sampleEntry.primaryExactPath}`,
      minimumScore: 1,
    });
    assert(mapped.passed, "sample boundary intent should pass mapping");
    assert(mapped.mappings.length > 0, "should return at least one mapping");
    assert(
      mapped.allowedExactPaths.some((item) => item === sampleEntry.primaryExactPath),
      "mapping should include sample primary exact path"
    );
    assert(
      mapped.matchedModuleIds.some((item) => item === sampleEntry.moduleId),
      "mapping should include sample module id"
    );

    const unmapped = analyzeIntentMapping({
      repoRoot: oneToOneFixtureRoot,
      intentText: "把火星地形引擎接入量子虫洞协议并自动修改银河配置",
      minimumScore: 12,
    });
    assert(!unmapped.passed, "nonsense intent should fail under high threshold");
  } finally {
    fs.rmSync(oneToOneFixtureRoot, { recursive: true, force: true });
  }

  const nonOneToOneFixtureRoot = fs.mkdtempSync(path.join(os.tmpdir(), "shelf-intent-gate-non-one-to-one-"));
  try {
    writeFixtureProjectCanonical(nonOneToOneFixtureRoot, {
      config: {
        modules: [
          {
            module_id: "demo.L0.M0",
            compiled_config_export: {
              boundary_bindings: [
                {
                  boundary_id: "DEMO_BOUNDARY",
                  primary_exact_path: "exact.demo.chat",
                  related_exact_paths: ["exact.demo.chat", "exact.demo.preview"],
                  primary_communication_path: "communication.demo.chat",
                  related_communication_paths: ["communication.demo.chat"],
                },
              ],
            },
          },
        ],
      },
    });
    const nonOneToOne = analyzeIntentMapping({
      repoRoot: nonOneToOneFixtureRoot,
      intentText: "调整 demo_boundary 的聊天路径映射",
    });
    assert(!nonOneToOne.passed, "non one-to-one boundary projection should fail mapping");
    assert(
      String(nonOneToOne.reason || "").includes("not one-to-one"),
      "mapping rejection reason should mention one-to-one requirement"
    );

    const nonOneToOneBypassed = analyzeIntentMapping({
      repoRoot: nonOneToOneFixtureRoot,
      intentText: "调整 demo_boundary 的聊天路径映射",
      allowNonOneToOneMapping: true,
    });
    assert(nonOneToOneBypassed.passed, "non one-to-one boundary projection should pass only when bypass flag is enabled");
    assert(
      nonOneToOneBypassed.mappings.some((item) => item.boundaryId === "DEMO_BOUNDARY"),
      "bypassed mapping result should keep non one-to-one boundary entries"
    );
  } finally {
    fs.rmSync(nonOneToOneFixtureRoot, { recursive: true, force: true });
  }
}

main();
