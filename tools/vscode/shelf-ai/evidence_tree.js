const fs = require("fs");
const path = require("path");
const workspaceGuard = require("./guarding");

function discoverCanonicalFiles(repoRoot) {
  const projectsDir = path.join(repoRoot, "projects");
  if (!fs.existsSync(projectsDir) || !fs.statSync(projectsDir).isDirectory()) {
    return [];
  }
  const canonicalFiles = [];
  for (const entry of fs.readdirSync(projectsDir)) {
    const canonicalPath = path.join(projectsDir, entry, "generated", "canonical.json");
    if (fs.existsSync(canonicalPath) && fs.statSync(canonicalPath).isFile()) {
      canonicalFiles.push(canonicalPath);
    }
  }
  return canonicalFiles.sort();
}

function readCanonicalFile(canonicalPath) {
  const raw = JSON.parse(fs.readFileSync(canonicalPath, "utf8"));
  if (!raw || typeof raw !== "object") {
    throw new Error(`canonical JSON must decode into an object: ${canonicalPath}`);
  }
  return raw;
}

function normalizeNode(node) {
  return {
    id: String(node.id),
    label: String(node.label),
    level: Number(node.level) || 0,
    description: String(node.description || ""),
    source_file: String(node.source_file || ""),
    node_kind: String(node.node_kind || ""),
  };
}

function addNode(nodes, edges, node) {
  nodes.push(normalizeNode(node));
  if (node.parentId) {
    edges.push({
      from: String(node.parentId),
      to: String(node.id),
      relation: "tree_child",
    });
  }
}

function buildCanonicalEvidencePayload(repoRoot) {
  const nodes = [];
  const edges = [];
  const canonicalFiles = discoverCanonicalFiles(repoRoot);
  if (!canonicalFiles.length) {
    throw new Error("no generated canonical.json files found");
  }

  for (const canonicalFile of canonicalFiles) {
    const canonical = readCanonicalFile(canonicalFile);
    const project = canonical.project;
    if (!project || typeof project !== "object") {
      continue;
    }
    const projectId = String(project.project_id || "");
    if (!projectId) {
      continue;
    }
    const relCanonical = workspaceGuard.normalizeRelPath(path.relative(repoRoot, canonicalFile));
    const projectFile = workspaceGuard.normalizeRelPath(
      path.relative(repoRoot, path.join(path.dirname(path.dirname(canonicalFile)), "project.toml"))
    );
    const projectNodeId = `project:${projectId}`;
    const canonicalNodeId = `${projectNodeId}:canonical`;
    addNode(nodes, edges, {
      id: projectNodeId,
      label: projectNodeId,
      level: 0,
      description: `project=${projectId} | file=${projectFile}`,
      source_file: projectFile,
      node_kind: "project",
    });
    addNode(nodes, edges, {
      id: canonicalNodeId,
      parentId: projectNodeId,
      label: "canonical.json",
      level: 1,
      description: `artifact=canonical.json | file=${relCanonical}`,
      source_file: relCanonical,
      node_kind: "canonical",
    });

    const frameworkModules = Array.isArray(canonical.framework?.modules) ? canonical.framework.modules : [];
    const configModules = new Map(
      (Array.isArray(canonical.config?.modules) ? canonical.config.modules : [])
        .filter((item) => item && typeof item === "object" && typeof item.module_id === "string")
        .map((item) => [String(item.module_id), item])
    );
    const codeModules = new Map(
      (Array.isArray(canonical.code?.modules) ? canonical.code.modules : [])
        .filter((item) => item && typeof item === "object" && typeof item.module_id === "string")
        .map((item) => [String(item.module_id), item])
    );
    const evidenceModules = new Map(
      (Array.isArray(canonical.evidence?.modules) ? canonical.evidence.modules : [])
        .filter((item) => item && typeof item === "object" && typeof item.module_id === "string")
        .map((item) => [String(item.module_id), item])
    );

    for (const frameworkModule of frameworkModules) {
      if (!frameworkModule || typeof frameworkModule !== "object" || typeof frameworkModule.module_id !== "string") {
        continue;
      }
      const moduleId = String(frameworkModule.module_id);
      const frameworkNodeId = `framework:${moduleId}`;
      const configNodeId = `config:${moduleId}`;
      const codeNodeId = `code:${moduleId}`;
      const evidenceNodeId = `evidence:${moduleId}`;
      const relFrameworkFile = workspaceGuard.normalizeRelPath(String(frameworkModule.framework_file || ""));
      const configModule = configModules.get(moduleId) || {};
      const codeModule = codeModules.get(moduleId) || {};
      const evidenceModule = evidenceModules.get(moduleId) || {};
      const configSource = workspaceGuard.normalizeRelPath(
        String(configModule.source_ref?.file_path || projectFile)
      );
      const codeSource = workspaceGuard.normalizeRelPath(
        String(codeModule.source_ref?.file_path || path.join("src", "project_runtime", "code_layer.py"))
      );
      const evidenceSource = workspaceGuard.normalizeRelPath(
        String(evidenceModule.source_ref?.file_path || path.join("src", "project_runtime", "evidence_layer.py"))
      );
      addNode(nodes, edges, {
        id: frameworkNodeId,
        parentId: canonicalNodeId,
        label: frameworkNodeId,
        level: 2,
        description: `layer=framework | module=${moduleId} | file=${relFrameworkFile}`,
        source_file: relFrameworkFile,
        node_kind: "framework_module",
      });
      addNode(nodes, edges, {
        id: configNodeId,
        parentId: frameworkNodeId,
        label: configNodeId,
        level: 3,
        description: `layer=config | module=${moduleId} | file=${configSource}`,
        source_file: configSource,
        node_kind: "config_module",
      });
      addNode(nodes, edges, {
        id: codeNodeId,
        parentId: configNodeId,
        label: codeNodeId,
        level: 4,
        description: `layer=code | module=${moduleId} | file=${codeSource}`,
        source_file: codeSource,
        node_kind: "code_module",
      });
      addNode(nodes, edges, {
        id: evidenceNodeId,
        parentId: codeNodeId,
        label: evidenceNodeId,
        level: 5,
        description: `layer=evidence | module=${moduleId} | file=${evidenceSource}`,
        source_file: evidenceSource,
        node_kind: "evidence_module",
      });
    }
  }

  return {
    root: {
      title: "Shelf Evidence Tree",
      description: "Canonical-derived four-layer evidence graph.",
      nodes,
      edges,
    },
  };
}

function readEvidenceTree(repoRoot, _relativeJsonPath) {
  return buildCanonicalEvidencePayload(repoRoot);
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
