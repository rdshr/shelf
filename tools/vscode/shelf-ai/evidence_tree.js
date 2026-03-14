const fs = require("fs");
const path = require("path");
const workspaceGuard = require("./guarding");

function readEvidenceTree(repoRoot, relativeJsonPath) {
  const jsonPath = path.resolve(repoRoot, relativeJsonPath);
  const raw = JSON.parse(fs.readFileSync(jsonPath, "utf8"));
  if (!raw || typeof raw !== "object") {
    throw new Error("evidence tree JSON must decode into an object");
  }
  if (!raw.root || typeof raw.root !== "object") {
    throw new Error("evidence tree JSON is missing root");
  }
  if (!Array.isArray(raw.root.nodes) || !Array.isArray(raw.root.edges)) {
    throw new Error("evidence tree JSON is missing nodes or edges");
  }
  return raw;
}

function buildIndexes(payload) {
  const nodes = Array.isArray(payload?.root?.nodes) ? payload.root.nodes : [];
  const edges = Array.isArray(payload?.root?.edges) ? payload.root.edges : [];
  const nodeLookup = new Map();
  const fileIndex = new Map();
  const parentIndex = new Map();
  const childrenIndex = new Map();

  for (const node of nodes) {
    if (!node || typeof node !== "object" || typeof node.id !== "string") {
      continue;
    }
    nodeLookup.set(node.id, node);
    const sourceFile = typeof node.source_file === "string" ? workspaceGuard.normalizeRelPath(node.source_file) : "";
    if (sourceFile) {
      if (!fileIndex.has(sourceFile)) {
        fileIndex.set(sourceFile, []);
      }
      fileIndex.get(sourceFile).push(node.id);
    }
  }

  for (const edge of edges) {
    if (!edge || edge.relation !== "tree_child") {
      continue;
    }
    const from = String(edge.from || "");
    const to = String(edge.to || "");
    if (!from || !to) {
      continue;
    }
    parentIndex.set(to, from);
    if (!childrenIndex.has(from)) {
      childrenIndex.set(from, []);
    }
    childrenIndex.get(from).push(to);
  }

  return {
    nodeLookup,
    fileIndex,
    parentIndex,
    childrenIndex,
  };
}

function resolveChangeContext(repoRoot, payload, relPaths, baselinePlan = null) {
  const normalizedRelPaths = [...new Set((relPaths || []).map(workspaceGuard.normalizeRelPath).filter(Boolean))];
  const indexes = buildIndexes(payload);
  const touchedNodes = new Set();

  for (const relPath of normalizedRelPaths) {
    for (const nodeId of indexes.fileIndex.get(relPath) || []) {
      touchedNodes.add(String(nodeId));
    }
  }

  for (const projectFile of baselinePlan?.materializeProjects || []) {
    const relProjectFile = workspaceGuard.normalizeRelPath(path.relative(repoRoot, projectFile));
    for (const nodeId of indexes.fileIndex.get(relProjectFile) || []) {
      touchedNodes.add(String(nodeId));
    }
  }

  const affectedNodes = new Set(touchedNodes);
  const queue = [...touchedNodes];
  while (queue.length) {
    const nodeId = queue.pop();

    const parent = indexes.parentIndex.get(nodeId);
    if (parent && !affectedNodes.has(parent)) {
      affectedNodes.add(parent);
      queue.push(parent);
    }

    for (const childId of indexes.childrenIndex.get(nodeId) || []) {
      if (!affectedNodes.has(childId)) {
        affectedNodes.add(childId);
        queue.push(childId);
      }
    }
  }

  return {
    touchedNodes: [...touchedNodes].sort(),
    affectedNodes: [...affectedNodes].sort(),
  };
}

function summarizeChangeContext(payload, changeContext, limit = 4) {
  const { nodeLookup } = buildIndexes(payload);

  const summarizeNodeIds = (nodeIds) =>
    (Array.isArray(nodeIds) ? nodeIds : [])
      .map((nodeId) => {
        const node = nodeLookup.get(String(nodeId));
        if (!node) {
          return {
            id: String(nodeId),
            label: String(nodeId),
            layer: "",
            file: "",
          };
        }
        return {
          id: String(node.id),
          label: typeof node.label === "string" && node.label ? node.label : String(node.id),
          layer: typeof node.node_kind === "string" ? node.node_kind : "",
          file: typeof node.source_file === "string" ? node.source_file : "",
        };
      })
      .slice(0, Math.max(0, Number(limit) || 0));

  return {
    touchedCount: Array.isArray(changeContext?.touchedNodes) ? changeContext.touchedNodes.length : 0,
    affectedCount: Array.isArray(changeContext?.affectedNodes) ? changeContext.affectedNodes.length : 0,
    touched: summarizeNodeIds(changeContext?.touchedNodes),
    affected: summarizeNodeIds(changeContext?.affectedNodes),
  };
}

function classifyWorkspaceChanges(repoRoot, relPaths, payload) {
  const baselinePlan = workspaceGuard.classifyWorkspaceChanges(repoRoot, relPaths);
  const protectedProjectFiles = baselinePlan.protectedGeneratedPaths
    .filter(
      (relPath) =>
        !workspaceGuard.isWorkspaceEvidenceArtifact(relPath)
        && !workspaceGuard.isWorkspaceFrameworkArtifact(relPath)
    )
    .map((relPath) => workspaceGuard.resolveProjectFilePath(repoRoot, relPath))
    .filter(Boolean)
    .sort();
  const changeContext = resolveChangeContext(repoRoot, payload, baselinePlan.relPaths, baselinePlan);

  return {
    relPaths: baselinePlan.relPaths,
    shouldRunMypy: baselinePlan.shouldRunMypy,
    shouldMaterialize: baselinePlan.shouldMaterialize,
    materializeProjects: baselinePlan.materializeProjects,
    protectedGeneratedPaths: baselinePlan.protectedGeneratedPaths,
    protectedWorkspaceArtifacts: baselinePlan.protectedWorkspaceArtifacts,
    protectedEvidenceArtifacts: baselinePlan.protectedEvidenceArtifacts,
    protectedFrameworkArtifacts: baselinePlan.protectedFrameworkArtifacts,
    protectedProjectFiles,
    changeContext,
  };
}

module.exports = {
  classifyWorkspaceChanges,
  readEvidenceTree,
  resolveChangeContext,
  summarizeChangeContext,
};
