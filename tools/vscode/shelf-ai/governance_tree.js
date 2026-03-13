const fs = require("fs");
const path = require("path");
const workspaceGuard = require("./guarding");

function readGovernanceTree(repoRoot, relativeJsonPath) {
  const jsonPath = path.resolve(repoRoot, relativeJsonPath);
  const raw = JSON.parse(fs.readFileSync(jsonPath, "utf8"));
  if (!raw || typeof raw !== "object") {
    throw new Error("governance tree JSON must decode into an object");
  }
  if (!raw.root || typeof raw.root !== "object") {
    throw new Error("governance tree JSON is missing root");
  }
  if (!raw.governance || typeof raw.governance !== "object") {
    throw new Error("governance tree JSON is missing governance metadata");
  }
  return raw;
}

function resolveChangeContext(payload, relPaths) {
  const governance = payload.governance || {};
  const fileIndex = governance.file_index || {};
  const parentIndex = governance.parent_index || {};
  const childrenIndex = governance.children_index || {};
  const derivedIndex = governance.derived_index || {};
  const reverseDerivedIndex = governance.reverse_derived_index || {};
  const projectIndex = governance.project_index || {};

  const normalizedRelPaths = [...new Set((relPaths || []).map(workspaceGuard.normalizeRelPath).filter(Boolean))];
  const touchedNodes = new Set();
  for (const relPath of normalizedRelPaths) {
    for (const nodeId of fileIndex[relPath] || []) {
      touchedNodes.add(String(nodeId));
    }
  }

  const affectedNodes = new Set(touchedNodes);
  const queue = [...touchedNodes];
  while (queue.length) {
    const nodeId = queue.pop();
    const parent = parentIndex[nodeId];
    if (typeof parent === "string" && parent && !affectedNodes.has(parent)) {
      affectedNodes.add(parent);
      queue.push(parent);
    }
    for (const childId of childrenIndex[nodeId] || []) {
      const normalizedChild = String(childId);
      if (!affectedNodes.has(normalizedChild)) {
        affectedNodes.add(normalizedChild);
        queue.push(normalizedChild);
      }
    }
    for (const upstreamId of derivedIndex[nodeId] || []) {
      const normalizedUpstream = String(upstreamId);
      if (!affectedNodes.has(normalizedUpstream)) {
        affectedNodes.add(normalizedUpstream);
        queue.push(normalizedUpstream);
      }
    }
    for (const dependentId of reverseDerivedIndex[nodeId] || []) {
      const normalizedDependent = String(dependentId);
      if (!affectedNodes.has(normalizedDependent)) {
        affectedNodes.add(normalizedDependent);
        queue.push(normalizedDependent);
      }
    }
  }

  const rootNodes = Array.isArray(payload.root?.nodes) ? payload.root.nodes : [];
  const nodeLookup = new Map(
    rootNodes
      .filter((node) => node && typeof node === "object" && typeof node.id === "string")
      .map((node) => [node.id, node])
  );

  const affectedProjects = new Map();
  const materializeProjects = new Map();
  let runStandardChecks = false;
  let runProjectChecks = false;

  for (const nodeId of affectedNodes) {
    const node = nodeLookup.get(nodeId);
    if (!node) {
      continue;
    }
    const projectId = typeof node.project_id === "string" ? node.project_id : "";
    if (projectId && projectIndex[projectId] && typeof projectIndex[projectId].product_spec_file === "string") {
      affectedProjects.set(projectId, projectIndex[projectId].product_spec_file);
      runProjectChecks = true;
    }
    if (node.layer === "Standards") {
      runStandardChecks = true;
    }
  }

  for (const nodeId of touchedNodes) {
    const node = nodeLookup.get(nodeId);
    if (!node) {
      continue;
    }
    const projectId = typeof node.project_id === "string" ? node.project_id : "";
    if (!projectId || !projectIndex[projectId]) {
      continue;
    }
    if (node.layer === "Framework" || node.layer === "Product Spec" || node.layer === "Implementation Config") {
      const productSpecFile = projectIndex[projectId].product_spec_file;
      if (typeof productSpecFile === "string" && productSpecFile) {
        materializeProjects.set(projectId, productSpecFile);
      }
    }
  }

  for (const relPath of normalizedRelPaths) {
    if (
      relPath.startsWith("framework/") ||
      relPath.startsWith("specs/") ||
      relPath.startsWith("mapping/")
    ) {
      runStandardChecks = true;
    }
  }

  return {
    touchedNodes: [...touchedNodes].sort(),
    affectedNodes: [...affectedNodes].sort(),
    affectedProjectSpecFiles: [...affectedProjects.values()].sort(),
    materializeProjectSpecFiles: [...materializeProjects.values()].sort(),
    runStandardChecks,
    runProjectChecks,
  };
}

function summarizeChangeContext(payload, changeContext, limit = 4) {
  const rootNodes = Array.isArray(payload?.root?.nodes) ? payload.root.nodes : [];
  const nodeLookup = new Map(
    rootNodes
      .filter((node) => node && typeof node === "object" && typeof node.id === "string")
      .map((node) => [node.id, node])
  );

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
          layer: typeof node.layer === "string" ? node.layer : "",
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
  const normalizedRelPaths = [...new Set((relPaths || []).map(workspaceGuard.normalizeRelPath).filter(Boolean))];
  const watchedRelPaths = normalizedRelPaths.filter(workspaceGuard.isWatchedPath);
  const protectedGeneratedPaths = watchedRelPaths.filter(workspaceGuard.isProtectedGeneratedPath);
  const protectedWorkspaceArtifacts = protectedGeneratedPaths.filter((relPath) =>
    workspaceGuard.isWorkspaceGovernanceArtifact(relPath) || workspaceGuard.isWorkspaceFrameworkArtifact(relPath)
  );
  const protectedGovernanceArtifacts = protectedGeneratedPaths.filter(
    workspaceGuard.isWorkspaceGovernanceArtifact
  );
  const protectedFrameworkArtifacts = protectedGeneratedPaths.filter(
    workspaceGuard.isWorkspaceFrameworkArtifact
  );
  const protectedProjectSpecs = protectedGeneratedPaths
    .filter(
      (relPath) =>
        !workspaceGuard.isWorkspaceGovernanceArtifact(relPath)
        && !workspaceGuard.isWorkspaceFrameworkArtifact(relPath)
    )
    .map((relPath) => workspaceGuard.resolveProjectProductSpecPath(repoRoot, relPath))
    .filter(Boolean)
    .sort();
  const changeContext = resolveChangeContext(payload, watchedRelPaths);

  return {
    relPaths: watchedRelPaths,
    shouldRunMypy: watchedRelPaths.some(workspaceGuard.shouldRunMypyForRelPath),
    shouldMaterialize: changeContext.materializeProjectSpecFiles.length > 0,
    materializeProjects: changeContext.materializeProjectSpecFiles,
    protectedGeneratedPaths,
    protectedWorkspaceArtifacts,
    protectedGovernanceArtifacts,
    protectedFrameworkArtifacts,
    protectedProjectSpecs,
    changeContext,
  };
}

module.exports = {
  classifyWorkspaceChanges,
  readGovernanceTree,
  resolveChangeContext,
  summarizeChangeContext,
};
