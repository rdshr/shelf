const assert = require("assert");
const fs = require("fs");
const os = require("os");
const path = require("path");

const { classifyWorkspaceChanges, readEvidenceTree, summarizeChangeContext } = require("./evidence_tree");

function writeFile(filePath, text) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, text);
}

function createFixtureRepo() {
  const repoRoot = fs.mkdtempSync(path.join(os.tmpdir(), "shelf-evidence-tree-"));
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
              framework_file: "framework/demo/L0-M0-示例模块.md",
            },
          ],
        },
        config: {
          modules: [
            {
              module_id: "demo.L0.M0",
              source_ref: {
                file_path: "projects/demo/project.toml",
                line: 1,
              },
            },
          ],
        },
        code: {
          modules: [
            {
              module_id: "demo.L0.M0",
              source_ref: {
                file_path: "src/project_runtime/code_layer.py",
                line: 1,
              },
            },
          ],
        },
        evidence: {
          modules: [
            {
              module_id: "demo.L0.M0",
              source_ref: {
                file_path: "src/project_runtime/evidence_layer.py",
                line: 1,
              },
            },
          ],
        },
      },
      null,
      2
    )
  );

  return {
    repoRoot,
    cleanup: () => fs.rmSync(repoRoot, { recursive: true, force: true }),
  };
}

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
  const fixture = createFixtureRepo();
  try {
    const repoRoot = fixture.repoRoot;
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
  } finally {
    fixture.cleanup();
  }
}

main();
