const assert = require("assert");
const path = require("path");

const { classifyWorkspaceChanges, readEvidenceTree, summarizeChangeContext } = require("./evidence_tree");

const repoRoot = path.resolve(__dirname, "..", "..", "..");

function main() {
  const payload = readEvidenceTree(repoRoot, "");

  const projectPlan = classifyWorkspaceChanges(
    repoRoot,
    ["projects/knowledge_base_basic/project.toml"],
    payload
  );
  assert(projectPlan.shouldMaterialize, "project config changes should trigger materialization");
  assert(
    projectPlan.materializeProjects.some((item) => item.endsWith("projects/knowledge_base_basic/project.toml")),
    "project config should map back to the owning project"
  );
  assert(
    projectPlan.changeContext.touchedNodes.some((item) => item === "project:knowledge_base_basic"),
    "project config change should touch the project node"
  );
  assert(
    projectPlan.changeContext.affectedNodes.some((item) => item === "project:knowledge_base_basic:canonical"),
    "project config change should affect the canonical node"
  );

  const generatedPlan = classifyWorkspaceChanges(
    repoRoot,
    ["projects/knowledge_base_basic/generated/canonical.json"],
    payload
  );
  assert.strictEqual(generatedPlan.shouldMaterialize, false, "generated canonical edits should not auto-materialize");
  assert(
    generatedPlan.changeContext.touchedNodes.some((item) => item === "project:knowledge_base_basic:canonical"),
    "generated canonical edits should touch the canonical node"
  );

  const summary = summarizeChangeContext(payload, projectPlan.changeContext, 2);
  assert(summary.touchedCount >= 1, "change summary should expose touched-node count");
  assert(summary.affectedCount >= summary.touchedCount, "change summary should expose affected-node count");
}

main();
