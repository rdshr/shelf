const fs = require("fs");
const path = require("path");
const correspondenceRuntime = require("./correspondence_runtime");
const evidenceTree = require("./evidence_tree");
const workspaceGuard = require("./guarding");

const MODULE_ID_PATTERN = /^(?<framework>[A-Za-z][A-Za-z0-9_]*)\.L(?<level>\d+)\.M(?<module>\d+)$/;
const MODULE_FILE_PATTERN = /^L(?<level>\d+)-M(?<module>\d+)-/;

/**
 * @typedef {Object} HoverItem
 * @property {string} token
 * @property {string} text
 */

/**
 * @typedef {Object} RuntimeTreeNode
 * @property {string} id
 * @property {string} label
 * @property {string} detail
 * @property {string} file
 * @property {number} line
 * @property {number} depth
 * @property {string} kind
 * @property {string} [group]
 * @property {number} [order]
 * @property {string} [title]
 * @property {string} [moduleName]
 * @property {string} [moduleRef]
 * @property {number} [sourceLine]
 * @property {number} [docLine]
 * @property {string} [hoverKicker]
 * @property {HoverItem[]} [capabilityItems]
 * @property {HoverItem[]} [baseItems]
 * @property {string} [objectId]
 * @property {Record<string, unknown>} [defaultTarget]
 * @property {Record<string, unknown>} [editTarget]
 * @property {Record<string, unknown>} [correspondenceAnchor]
 * @property {Record<string, unknown>} [implementationAnchor]
 * @property {Record<string, unknown>[]} [secondaryTargets]
 * @property {string[]} [relatedObjectIds]
 */

/**
 * @typedef {Object} RuntimeTreeEdge
 * @property {string} id
 * @property {string} from
 * @property {string} to
 * @property {string} relation
 * @property {string} [rules]
 * @property {string} [terms]
 * @property {string} [file]
 * @property {number} [line]
 */

/**
 * @typedef {Object} RuntimeFrameworkGroup
 * @property {string} name
 * @property {number} order
 * @property {number[]} localLevels
 * @property {Record<number, number>} levelNodeCounts
 */

/**
 * @typedef {Object} RuntimeTreeModel
 * @property {string} title
 * @property {string} description
 * @property {("framework"|"evidence")} kind
 * @property {RuntimeTreeNode[]} nodes
 * @property {RuntimeTreeEdge[]} edges
 * @property {string} [footText]
 * @property {"global_levels"|"framework_columns"} [layoutMode]
 * @property {Record<number, string>} [levelLabels]
 * @property {RuntimeFrameworkGroup[]} [frameworkGroups]
 * @property {Record<string, number>} [relationCounts]
 * @property {Record<string, unknown>} [objectIndex]
 * @property {Record<string, unknown>} [validationSummary]
 */

/**
 * @typedef {{ frameworkName: string, level: number, module: number }} ParsedModuleId
 */

/**
 * @param {unknown} value
 * @returns {string}
 */
function asText(value) {
  return String(value ?? "").trim();
}

/**
 * @param {unknown} value
 * @param {number} fallback
 * @returns {number}
 */
function asPositiveInt(value, fallback) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return fallback;
  }
  return Math.max(1, Math.floor(parsed));
}

/**
 * @param {string} moduleId
 * @returns {ParsedModuleId | null}
 */
function parseModuleId(moduleId) {
  const match = MODULE_ID_PATTERN.exec(moduleId);
  if (!match || !match.groups) {
    return null;
  }
  return {
    frameworkName: String(match.groups.framework || ""),
    level: asPositiveInt(match.groups.level, 0),
    module: asPositiveInt(match.groups.module, 0),
  };
}

/**
 * @param {string} fileName
 * @returns {{ level: number, module: number } | null}
 */
function parseModuleFileName(fileName) {
  const match = MODULE_FILE_PATTERN.exec(fileName);
  if (!match || !match.groups) {
    return null;
  }
  return {
    level: asPositiveInt(match.groups.level, 0),
    module: asPositiveInt(match.groups.module, 0),
  };
}

/**
 * @param {string} filePath
 * @returns {{ title: string, line: number }}
 */
function firstMarkdownHeading(filePath) {
  try {
    const lines = fs.readFileSync(filePath, "utf8").split(/\r?\n/);
    for (let index = 0; index < lines.length; index += 1) {
      const match = /^\s*#\s+(.+)\s*$/.exec(lines[index] || "");
      if (match) {
        return {
          title: String(match[1] || "").trim(),
          line: index + 1,
        };
      }
    }
  } catch {
    return { title: "", line: 1 };
  }
  return { title: "", line: 1 };
}

/**
 * @param {unknown} sourceRef
 * @returns {{ filePath: string, line: number }}
 */
function sourceRefInfo(sourceRef) {
  return {
    filePath: workspaceGuard.normalizeRelPath(asText(sourceRef && typeof sourceRef === "object" ? sourceRef.file_path : "")),
    line: asPositiveInt(sourceRef && typeof sourceRef === "object" ? sourceRef.line : 1, 1),
  };
}

/**
 * @param {unknown[]} entries
 * @param {string} tokenKey
 * @param {(entry: Record<string, unknown>) => string} textBuilder
 * @returns {HoverItem[]}
 */
function hoverItems(entries, tokenKey, textBuilder) {
  /** @type {HoverItem[]} */
  const items = [];
  for (const entry of entries) {
    if (!entry || typeof entry !== "object") {
      continue;
    }
    const token = asText(entry[tokenKey]);
    const text = asText(textBuilder(/** @type {Record<string, unknown>} */ (entry)));
    if (!token && !text) {
      continue;
    }
    items.push({
      token,
      text: text || token,
    });
  }
  return items;
}

/**
 * @param {Map<string, Map<number, number>>} countsByFramework
 * @returns {RuntimeFrameworkGroup[]}
 */
function frameworkGroupsFromCounts(countsByFramework) {
  return [...countsByFramework.entries()]
    .sort((left, right) => left[0].localeCompare(right[0]))
    .map(([frameworkName, levelCounts], index) => ({
      name: frameworkName,
      order: index,
      localLevels: [...levelCounts.keys()].sort((left, right) => left - right),
      levelNodeCounts: Object.fromEntries(
        [...levelCounts.entries()].sort((left, right) => left[0] - right[0])
      ),
    }));
}

/**
 * @param {Iterable<number>} levels
 * @returns {Record<number, string>}
 */
function levelLabelsFor(levels) {
  return Object.fromEntries(
    [...new Set(levels)]
      .sort((left, right) => left - right)
      .map((level) => [level, `L${level} 标准层`])
  );
}

/**
 * @param {Record<string, unknown> | null | undefined} entry
 * @returns {string[]}
 */
function flattenModuleRelatedObjectIds(entry) {
  if (!entry || typeof entry !== "object") {
    return [];
  }
  const keys = ["bases", "rules", "boundaries", "static_params", "runtime_params"];
  const values = [];
  for (const key of keys) {
    const entries = entry[key];
    if (!Array.isArray(entries)) {
      continue;
    }
    for (const value of entries) {
      const objectId = asText(value);
      if (objectId) {
        values.push(objectId);
      }
    }
  }
  return values;
}

/**
 * @param {string} repoRoot
 * @returns {{ payload: Record<string, unknown>, treeEntriesByModuleId: Map<string, Record<string, unknown>> } | null}
 */
function loadFrameworkCorrespondenceProjection(repoRoot) {
  const projectFilePath = correspondenceRuntime.resolvePreferredProjectFile(repoRoot);
  if (!projectFilePath) {
    return null;
  }
  const canonical = correspondenceRuntime.readProjectCanonical(projectFilePath);
  if (!canonical || !canonical.correspondence) {
    return null;
  }
  const endpoints = correspondenceRuntime.resolveCorrespondenceApiPaths(canonical);
  const payload = correspondenceRuntime.readCorrespondenceApi(
    repoRoot,
    endpoints.root,
    { projectFilePath }
  );
  const treePayload = correspondenceRuntime.readCorrespondenceApi(
    repoRoot,
    endpoints.tree,
    { projectFilePath }
  );
  if (!payload || !treePayload || typeof payload !== "object") {
    return null;
  }
  const treeEntries = Array.isArray(treePayload.tree)
    ? treePayload.tree.filter((item) => item && typeof item === "object")
    : [];
  const treeEntriesByModuleId = new Map();
  const objectIndex = payload.object_index && typeof payload.object_index === "object"
    ? { ...payload.object_index }
    : {};
  for (const entry of treeEntries) {
    const moduleId = asText(entry.module_id);
    if (moduleId) {
      treeEntriesByModuleId.set(moduleId, entry);
    }
    const moduleObjectId = asText(entry.module_object_id);
    if (moduleObjectId) {
      const moduleObject = correspondenceRuntime.readCorrespondenceApi(
        repoRoot,
        `${endpoints.objectBase}${encodeURIComponent(moduleObjectId)}`,
        { projectFilePath }
      );
      if (moduleObject && typeof moduleObject === "object") {
        objectIndex[moduleObjectId] = moduleObject;
      }
    }
  }
  return {
    payload,
    objectIndex,
    treeEntriesByModuleId,
  };
}

/**
 * @param {string} repoRoot
 * @returns {{ modules: Record<string, unknown>[], excludedProjectIds: string[] }}
 */
function collectFreshCanonicalFrameworkModules(repoRoot) {
  const freshnessSummary = workspaceGuard.summarizeCanonicalFreshness(repoRoot);
  /** @type {Map<string, Record<string, unknown>>} */
  const moduleById = new Map();

  for (const project of freshnessSummary.projects) {
    if (project.status !== "fresh") {
      continue;
    }
    try {
      const canonical = JSON.parse(fs.readFileSync(project.canonicalPath, "utf8"));
      const rawModules = Array.isArray(canonical?.framework?.modules)
        ? canonical.framework.modules
        : [];
      for (const rawModule of rawModules) {
        if (!rawModule || typeof rawModule !== "object") {
          continue;
        }
        const moduleId = asText(rawModule.module_id);
        if (!moduleId || moduleById.has(moduleId)) {
          continue;
        }
        moduleById.set(moduleId, rawModule);
      }
    } catch {
      // Freshness guards parseability, but ignore unexpected runtime read failures.
    }
  }

  return {
    modules: [...moduleById.values()],
    excludedProjectIds: freshnessSummary.blockingProjects.map((project) => String(project.projectId || "")),
  };
}

/**
 * @param {string} repoRoot
 * @returns {RuntimeTreeModel | null}
 */
function buildCanonicalFrameworkTreeModel(repoRoot) {
  const collected = collectFreshCanonicalFrameworkModules(repoRoot);
  if (!collected.modules.length) {
    return null;
  }
  const correspondenceProjection = loadFrameworkCorrespondenceProjection(repoRoot);
  const objectIndex = correspondenceProjection
    && correspondenceProjection.objectIndex
    && typeof correspondenceProjection.objectIndex === "object"
      ? correspondenceProjection.objectIndex
      : {};

  const orderedModules = collected.modules
    .map((item) => {
      const moduleId = asText(item.module_id);
      const parsed = parseModuleId(moduleId);
      if (!parsed) {
        return null;
      }
      return {
        raw: item,
        moduleId,
        ...parsed,
      };
    })
    .filter(Boolean)
    .sort((left, right) => {
      if (!left || !right) {
        return 0;
      }
      if (left.frameworkName !== right.frameworkName) {
        return left.frameworkName.localeCompare(right.frameworkName);
      }
      if (left.level !== right.level) {
        return left.level - right.level;
      }
      return left.module - right.module;
    });

  /** @type {RuntimeTreeNode[]} */
  const nodes = [];
  /** @type {RuntimeTreeEdge[]} */
  const edges = [];
  /** @type {Map<string, Map<number, number>>} */
  const frameworkCounts = new Map();
  /** @type {Record<string, number>} */
  const relationCounts = {};

  for (const item of orderedModules) {
    if (!item) {
      continue;
    }
    const moduleSource = sourceRefInfo(item.raw.source_ref);
    const exportSource = sourceRefInfo(item.raw.export_surface && typeof item.raw.export_surface === "object"
      ? item.raw.export_surface.source_ref
      : null);
    const sourceFile = moduleSource.filePath || exportSource.filePath || workspaceGuard.normalizeRelPath(asText(item.raw.framework_file));
    const docLine = moduleSource.line || exportSource.line || 1;
    const sourceLine = exportSource.line || moduleSource.line || 1;
    const title = asText(item.raw.title_cn) || asText(item.raw.title_en) || item.moduleId;
    const moduleObject = objectIndex && typeof objectIndex === "object"
      ? objectIndex[item.moduleId]
      : null;
    const moduleTreeEntry = correspondenceProjection?.treeEntriesByModuleId.get(item.moduleId) || null;
    const defaultTarget = correspondenceRuntime.resolvePrimaryNavigationTarget(moduleObject);
    const editTarget = correspondenceRuntime.resolvePrimaryEditTarget(moduleObject);
    const secondaryTargets = correspondenceRuntime.resolveSecondaryTargets(moduleObject);
    const relatedObjectIds = flattenModuleRelatedObjectIds(moduleTreeEntry);
    const capabilities = hoverItems(
      Array.isArray(item.raw.capabilities) ? item.raw.capabilities : [],
      "capability_id",
      (entry) => {
        const name = asText(entry.name);
        const statement = asText(entry.statement);
        return [name, statement].filter(Boolean).join("：");
      }
    );
    const bases = hoverItems(
      Array.isArray(item.raw.bases) ? item.raw.bases : [],
      "base_id",
      (entry) => {
        const name = asText(entry.name);
        const statement = asText(entry.statement);
        return [name, statement].filter(Boolean).join("：");
      }
    );

    if (!frameworkCounts.has(item.frameworkName)) {
      frameworkCounts.set(item.frameworkName, new Map());
    }
    const levelCounts = frameworkCounts.get(item.frameworkName);
    if (levelCounts) {
      levelCounts.set(item.level, (levelCounts.get(item.level) || 0) + 1);
    }

    nodes.push({
      id: item.moduleId,
      label: `L${item.level}.${item.frameworkName}.M${item.module}`,
      detail: title,
      file: sourceFile,
      line: docLine,
      depth: item.level,
      kind: "framework_module",
      group: item.frameworkName,
      order: item.module,
      title,
      moduleName: item.frameworkName,
      moduleRef: `L${item.level}.M${item.module}`,
      sourceLine,
      docLine,
      hoverKicker: "Framework Module",
      capabilityItems: capabilities,
      baseItems: bases,
      ...(moduleObject ? {
        objectId: moduleObject.object_id,
        defaultTarget,
        editTarget,
        correspondenceAnchor: moduleObject.correspondence_anchor || null,
        implementationAnchor: moduleObject.implementation_anchor || null,
        secondaryTargets,
        relatedObjectIds,
      } : {}),
    });

    const exportSurface = item.raw.export_surface && typeof item.raw.export_surface === "object"
      ? item.raw.export_surface
      : {};
    const upstreamIds = Array.isArray(exportSurface.upstream_module_ids)
      ? exportSurface.upstream_module_ids.map((value) => asText(value)).filter(Boolean)
      : [];
    const ruleIds = Array.isArray(exportSurface.rule_ids)
      ? exportSurface.rule_ids.map((value) => asText(value)).filter(Boolean)
      : [];

    for (const upstreamId of upstreamIds) {
      relationCounts.framework_module_growth = (relationCounts.framework_module_growth || 0) + 1;
      edges.push({
        id: `${upstreamId}=>${item.moduleId}`,
        from: upstreamId,
        to: item.moduleId,
        relation: "framework_module_growth",
        rules: ruleIds.join(", "),
        terms: upstreamId,
        file: sourceFile,
        line: sourceLine,
      });
    }
  }

  const nodeIds = new Set(nodes.map((node) => node.id));
  const filteredEdges = edges.filter((edge) => nodeIds.has(edge.from) && nodeIds.has(edge.to));
  const descriptionParts = [
    "Runtime projection from fresh canonical framework modules.",
    "Interactive graph only; no persisted tree artifact.",
  ];
  if (correspondenceProjection) {
    descriptionParts.push("Correspondence protocol is the primary navigation source; legacy canonical fields remain fallback-only.");
  }
  if (collected.excludedProjectIds.length) {
    descriptionParts.push(
      `Stale/invalid projects excluded from canonical projection: ${collected.excludedProjectIds.slice(0, 3).join(", ")}.`
    );
  }

  return {
    title: "Shelf Framework Tree",
    description: descriptionParts.join(" "),
    kind: "framework",
    nodes,
    edges: filteredEdges,
    footText: "Grouped by framework; each panel keeps its own local Lx bands.",
    layoutMode: "framework_columns",
    levelLabels: levelLabelsFor(nodes.map((node) => node.depth)),
    frameworkGroups: frameworkGroupsFromCounts(frameworkCounts),
    relationCounts,
    ...(correspondenceProjection ? {
      objectIndex,
      validationSummary: correspondenceProjection.payload.validation_summary || null,
    } : {}),
  };
}

/**
 * @param {string} repoRoot
 * @returns {RuntimeTreeModel}
 */
function buildAuthorFallbackFrameworkTreeModel(repoRoot) {
  const frameworkRoot = path.join(repoRoot, "framework");
  if (!fs.existsSync(frameworkRoot) || !fs.statSync(frameworkRoot).isDirectory()) {
    throw new Error("framework/ directory is missing");
  }

  /** @type {RuntimeTreeNode[]} */
  const nodes = [];
  /** @type {Map<string, Map<number, number>>} */
  const frameworkCounts = new Map();

  const frameworkDirs = fs.readdirSync(frameworkRoot)
    .map((entry) => ({
      name: entry,
      absPath: path.join(frameworkRoot, entry),
    }))
    .filter((entry) => fs.existsSync(entry.absPath) && fs.statSync(entry.absPath).isDirectory())
    .sort((left, right) => left.name.localeCompare(right.name));

  for (const frameworkDir of frameworkDirs) {
    const moduleFiles = fs.readdirSync(frameworkDir.absPath)
      .filter((entry) => entry.endsWith(".md"))
      .sort((left, right) => left.localeCompare(right));

    if (!frameworkCounts.has(frameworkDir.name)) {
      frameworkCounts.set(frameworkDir.name, new Map());
    }
    const levelCounts = frameworkCounts.get(frameworkDir.name);

    for (const fileName of moduleFiles) {
      const parsed = parseModuleFileName(fileName);
      if (!parsed) {
        continue;
      }
      const absPath = path.join(frameworkDir.absPath, fileName);
      const relPath = workspaceGuard.normalizeRelPath(path.relative(repoRoot, absPath));
      const heading = firstMarkdownHeading(absPath);
      levelCounts?.set(parsed.level, (levelCounts?.get(parsed.level) || 0) + 1);
      nodes.push({
        id: `framework-source:${relPath}`,
        label: `L${parsed.level}.${frameworkDir.name}.M${parsed.module}`,
        detail: heading.title || fileName,
        file: relPath,
        line: heading.line,
        depth: parsed.level,
        kind: "framework_module",
        group: frameworkDir.name,
        order: parsed.module,
        title: heading.title || fileName,
        moduleName: frameworkDir.name,
        moduleRef: `L${parsed.level}.M${parsed.module}`,
        sourceLine: heading.line,
        docLine: heading.line,
        hoverKicker: "Framework Module (Author Source)",
        capabilityItems: [],
        baseItems: [],
      });
    }
  }

  return {
    title: "Shelf Framework Tree",
    description: [
      "Author-source fallback view.",
      "Canonical is not fresh, so cross-module growth edges and rich hover metadata are unavailable.",
    ].join(" "),
    kind: "framework",
    nodes,
    edges: [],
    footText: "Fallback mode keeps framework columns and local Lx bands, but does not infer missing machine relationships.",
    layoutMode: "framework_columns",
    levelLabels: levelLabelsFor(nodes.map((node) => node.depth)),
    frameworkGroups: frameworkGroupsFromCounts(frameworkCounts),
    relationCounts: {},
  };
}

/**
 * @param {string} repoRoot
 * @returns {RuntimeTreeModel}
 */
function buildRuntimeFrameworkTreeModel(repoRoot) {
  return buildCanonicalFrameworkTreeModel(repoRoot) || buildAuthorFallbackFrameworkTreeModel(repoRoot);
}

/**
 * @param {string} repoRoot
 * @returns {RuntimeTreeModel}
 */
function buildRuntimeEvidenceTreeModel(repoRoot) {
  const payload = evidenceTree.readEvidenceTree(repoRoot, "");
  const rawNodes = Array.isArray(payload?.root?.nodes) ? payload.root.nodes : [];
  /** @type {RuntimeTreeNode[]} */
  const nodes = rawNodes
    .filter((node) => node && typeof node === "object")
    .map((node) => {
      const nodeId = asText(node.id);
      const nodeKind = asText(node.node_kind) || "evidence_node";
      const sourceInfo = sourceRefInfo(node.source_ref);
      const sourceFile = sourceInfo.filePath || workspaceGuard.normalizeRelPath(asText(node.source_file));
      return {
        id: nodeId,
        label: asText(node.label) || nodeId || "node",
        detail: asText(node.description) || nodeKind,
        file: sourceFile,
        line: sourceInfo.line || 1,
        depth: Math.max(0, Number(node.level || 0)),
        kind: nodeKind,
        group: nodeKind.split(":")[0] || "evidence",
        title: asText(node.label) || nodeId,
      };
    })
    .filter((node) => node.id)
    .sort((left, right) => {
      if (left.depth !== right.depth) {
        return left.depth - right.depth;
      }
      return left.label.localeCompare(right.label);
    });

  const nodeIds = new Set(nodes.map((node) => node.id));
  const rawEdges = Array.isArray(payload?.root?.edges) ? payload.root.edges : [];
  /** @type {RuntimeTreeEdge[]} */
  const edges = rawEdges
    .filter((edge) => edge && String(edge.relation || "") === "tree_child")
    .map((edge, index) => {
      const sourceInfo = sourceRefInfo(edge.source_ref);
      return {
        id: asText(edge.id) || `${index}:${asText(edge.from)}=>${asText(edge.to)}`,
        from: asText(edge.from),
        to: asText(edge.to),
        relation: "tree_child",
        file: sourceInfo.filePath || workspaceGuard.normalizeRelPath(asText(edge.source_file)),
        line: sourceInfo.line || 1,
      };
    })
    .filter((edge) => edge.from && edge.to && nodeIds.has(edge.from) && nodeIds.has(edge.to));

  return {
    title: "Shelf Evidence Tree",
    description: "Runtime projection from canonical graph. Interactive graph, no persisted tree artifact.",
    kind: "evidence",
    nodes,
    edges,
    footText: "Evidence tree remains canonical-derived and opens only when canonical is fresh.",
    layoutMode: "global_levels",
    levelLabels: levelLabelsFor(nodes.map((node) => node.depth)),
    relationCounts: Object.fromEntries(
      edges.reduce((counts, edge) => {
        counts.set(edge.relation, (counts.get(edge.relation) || 0) + 1);
        return counts;
      }, new Map())
    ),
  };
}

/**
 * @param {string} repoRoot
 * @param {"framework"|"evidence"} kind
 * @returns {RuntimeTreeModel}
 */
function buildRuntimeTreeModel(repoRoot, kind) {
  return kind === "evidence"
    ? buildRuntimeEvidenceTreeModel(repoRoot)
    : buildRuntimeFrameworkTreeModel(repoRoot);
}

module.exports = {
  buildRuntimeEvidenceTreeModel,
  buildRuntimeFrameworkTreeModel,
  buildRuntimeTreeModel,
};
