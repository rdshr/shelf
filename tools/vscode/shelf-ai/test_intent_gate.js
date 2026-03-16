const assert = require("assert");
const path = require("path");
const {
  analyzeIntentMapping,
  collectBoundaryEntries,
} = require("./intent_gate");

const repoRoot = path.resolve(__dirname, "..", "..", "..");

function main() {
  const collected = collectBoundaryEntries(repoRoot);
  assert(collected.entries.length > 0, "should load boundary entries from canonical");
  assert(
    collected.entries.some((item) => item.moduleId === "knowledge_base.L0.M2" && item.boundaryId === "CITATION"),
    "knowledge_base.L0.M2/CITATION mapping should exist"
  );

  const mapped = analyzeIntentMapping({
    repoRoot,
    intentText: "给知识库加一个前端页面，支持 @ 来引用文档，并且有动态图效果",
  });
  assert(mapped.passed, "knowledge-base citation + visual page intent should pass mapping");
  assert(mapped.mappings.length > 0, "should return at least one mapping");
  assert(
    mapped.allowedExactPaths.some((item) => item === "exact.knowledge_base.chat"),
    "mapping should include exact.knowledge_base.chat"
  );
  assert(
    mapped.allowedExactPaths.some((item) => item === "exact.frontend.route" || item === "exact.frontend.surface"),
    "mapping should include frontend page-related exact paths"
  );
  assert(
    mapped.matchedModuleIds.some((item) => item === "knowledge_base.L0.M2"),
    "mapping should include matched module ids"
  );

  const unmapped = analyzeIntentMapping({
    repoRoot,
    intentText: "把火星地形引擎接入量子虫洞协议并自动修改银河配置",
    minimumScore: 12,
  });
  assert(!unmapped.passed, "nonsense intent should fail under high threshold");
}

main();
