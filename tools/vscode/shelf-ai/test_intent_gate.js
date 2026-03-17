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

const repoRoot = path.resolve(__dirname, "..", "..", "..");

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

  const collected = collectBoundaryEntries(repoRoot);
  assert(collected.entries.length > 0, "should load boundary entries from canonical");
  assert(
    collected.entries.some((item) => item.moduleId === "knowledge_base.L0.M2" && item.boundaryId === "CITATION"),
    "knowledge_base.L0.M2/CITATION mapping should exist"
  );
  assert(
    collected.entries.every((item) => item.exactPaths.length === 1 && item.exactPaths[0] === item.primaryExactPath),
    "boundary entries should map one-to-one on primary exact path"
  );
  assert(
    collected.entries.every((item) => item.communicationPaths.length === 1 && item.communicationPaths[0] === item.primaryCommunicationPath),
    "boundary entries should map one-to-one on primary communication path"
  );

  const mapped = analyzeIntentMapping({
    repoRoot,
    intentText: "给知识库加一个前端页面，支持 @ 来引用文档，并且有动态图效果",
  });
  assert(mapped.passed, "knowledge-base citation + visual page intent should pass mapping");
  assert(mapped.mappings.length > 0, "should return at least one mapping");
  assert(
    mapped.allowedExactPaths.some((item) => item === "exact.frontend.interact"),
    "mapping should include exact.frontend.interact"
  );
  assert(
    mapped.allowedExactPaths.some((item) => item === "exact.frontend.route" || item === "exact.frontend.surface"),
    "mapping should include frontend page-related exact paths"
  );
  assert(
    !mapped.allowedExactPaths.some((item) => item === "exact.knowledge_base.context"),
    "allowed exact paths should only keep primary exact mappings"
  );
  assert(
    mapped.matchedModuleIds.some((item) => item === "frontend.L2.M0"),
    "mapping should include matched module ids"
  );

  const unmapped = analyzeIntentMapping({
    repoRoot,
    intentText: "把火星地形引擎接入量子虫洞协议并自动修改银河配置",
    minimumScore: 12,
  });
  assert(!unmapped.passed, "nonsense intent should fail under high threshold");

  const fixtureRoot = fs.mkdtempSync(path.join(os.tmpdir(), "shelf-intent-gate-"));
  const fixtureProjectDir = path.join(fixtureRoot, "projects", "demo");
  const fixtureGeneratedDir = path.join(fixtureProjectDir, "generated");
  fs.mkdirSync(fixtureGeneratedDir, { recursive: true });
  fs.writeFileSync(
    path.join(fixtureProjectDir, "project.toml"),
    "[framework]\nmodules = []\n",
    "utf8"
  );
  fs.writeFileSync(
    path.join(fixtureGeneratedDir, "canonical.json"),
    JSON.stringify({
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
    }),
    "utf8"
  );
  const nonOneToOne = analyzeIntentMapping({
    repoRoot: fixtureRoot,
    intentText: "调整 demo_boundary 的聊天路径映射",
  });
  assert(!nonOneToOne.passed, "non one-to-one boundary projection should fail mapping");
  assert(
    String(nonOneToOne.reason || "").includes("not one-to-one"),
    "mapping rejection reason should mention one-to-one requirement"
  );

  const nonOneToOneBypassed = analyzeIntentMapping({
    repoRoot: fixtureRoot,
    intentText: "调整 demo_boundary 的聊天路径映射",
    allowNonOneToOneMapping: true,
  });
  assert(nonOneToOneBypassed.passed, "non one-to-one boundary projection should pass only when bypass flag is enabled");
  assert(
    nonOneToOneBypassed.mappings.some((item) => item.boundaryId === "DEMO_BOUNDARY"),
    "bypassed mapping result should keep non one-to-one boundary entries"
  );
}

main();
