const assert = require("assert");
const path = require("path");

const { classifyWorkspaceChanges, readEvidenceTree, summarizeChangeContext } = require("./evidence_tree");

const repoRoot = path.resolve(__dirname, "..", "..", "..");

function firstProjectIdFromPayload(payload) {
  const nodes = Array.isArray(payload?.root?.nodes) ? payload.root.nodes : [];
  for (const node of nodes) {
    const nodeId = String(node?.id || "");
    const match = /^project:([^:]+)$/.exec(nodeId);
    if (match) {
      return match[1];
    }
  }
  return "";
}

function main() {
  const payload = readEvidenceTree(repoRoot, "");
  const projectId = firstProjectIdFromPayload(payload);
  assert(projectId, "evidence tree should include at least one project node");
  const projectTomlRelPath = `projects/${projectId}/project.toml`;
  const projectCanonicalRelPath = `projects/${projectId}/generated/canonical.json`;

  const projectPlan = classifyWorkspaceChanges(
    repoRoot,
    [projectTomlRelPath],
    payload
  );
  assert(projectPlan.shouldMaterialize, "project config changes should trigger materialization");
  assert(
    projectPlan.materializeProjects.some((item) => item.endsWith(projectTomlRelPath)),
    "project config should map back to the owning project"
  );
  assert(
    projectPlan.changeContext.touchedNodes.some((item) => item === `project:${projectId}`),
    "project config change should touch the project node"
  );
  assert(
    projectPlan.changeContext.affectedNodes.some((item) => item === `project:${projectId}:canonical`),
    "project config change should affect the canonical node"
  );

  const generatedPlan = classifyWorkspaceChanges(
    repoRoot,
    [projectCanonicalRelPath],
    payload
  );
  assert.strictEqual(generatedPlan.shouldMaterialize, false, "generated canonical edits should not auto-materialize");
  assert(
    generatedPlan.changeContext.touchedNodes.some((item) => item === `project:${projectId}:canonical`),
    "generated canonical edits should touch the canonical node"
  );

  const summary = summarizeChangeContext(payload, projectPlan.changeContext, 2);
  assert(summary.touchedCount >= 1, "change summary should expose touched-node count");
  assert(summary.affectedCount >= summary.touchedCount, "change summary should expose affected-node count");
}

main();
