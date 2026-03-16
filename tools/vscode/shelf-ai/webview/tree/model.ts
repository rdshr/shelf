import type {
  FilterResult,
  FocusMode,
  GraphEdge,
  GraphFrameworkGroup,
  GraphNode,
  HoverItem,
  RuntimeFrameworkGroup,
  RuntimeTreeLayoutMode,
  RuntimeTreeModel,
} from "./types";

const NODE_DIMENSIONS: Record<string, { width: number; height: number }> = {
  framework_root: { width: 142, height: 40 },
  framework_group: { width: 166, height: 44 },
};

function nodeDimensions(kind: string): { width: number; height: number } {
  if (NODE_DIMENSIONS[kind]) {
    return NODE_DIMENSIONS[kind];
  }
  if (kind.includes("root")) {
    return { width: 142, height: 40 };
  }
  if (kind.includes("group")) {
    return { width: 166, height: 44 };
  }
  if (kind.includes("project") || kind.includes("evidence")) {
    return { width: 168, height: 44 };
  }
  return { width: 160, height: 42 };
}

function normalizeText(value: unknown): string {
  return String(value ?? "").trim();
}

function normalizePositiveInt(value: unknown, fallback: number): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return fallback;
  }
  return Math.max(1, Math.floor(parsed));
}

function normalizeHoverItems(candidate: unknown): HoverItem[] {
  if (!Array.isArray(candidate)) {
    return [];
  }
  return candidate
    .map((entry) => {
      if (!entry || typeof entry !== "object") {
        return null;
      }
      const token = normalizeText((entry as Partial<HoverItem>).token);
      const text = normalizeText((entry as Partial<HoverItem>).text);
      if (!token && !text) {
        return null;
      }
      return {
        token,
        text: text || token,
      };
    })
    .filter((entry): entry is HoverItem => Boolean(entry));
}

function visualLength(value: string): number {
  let length = 0;
  for (const char of value) {
    length += /[\u1100-\u11ff\u2e80-\u9fff\uf900-\ufaff]/.test(char) ? 1.9 : 1;
  }
  return length;
}

function moduleDimensionsFromText(compactId: string): { width: number; height: number } {
  // Layout width controls node pitch more than the visible circle size.
  const width = Math.min(118, Math.max(72, Math.round(28 + visualLength(compactId) * 3.85)));
  const height = 38;
  return { width, height };
}

function normalizeNode(node: unknown): GraphNode | null {
  if (!node || typeof node !== "object") {
    return null;
  }
  const candidate = node as Partial<GraphNode>;
  const id = normalizeText(candidate.id);
  if (!id) {
    return null;
  }
  const kind = normalizeText(candidate.kind) || "node";
  const group = normalizeText(candidate.group);
  const title = normalizeText(candidate.title);
  const detail = normalizeText(candidate.detail);
  const label = normalizeText(candidate.label) || id;
  const moduleName = normalizeText(candidate.moduleName);
  const moduleRef = normalizeText(candidate.moduleRef);
  const compactModuleId = moduleName && moduleRef
    ? `${moduleName}.${moduleRef}`
    : label;
  const size = kind.includes("module")
    ? moduleDimensionsFromText(compactModuleId)
    : nodeDimensions(kind);
  const hoverKicker = normalizeText(candidate.hoverKicker);
  const order = Number.isFinite(Number(candidate.order)) ? Math.max(0, Number(candidate.order)) : null;
  const sourceLine = Number.isFinite(Number(candidate.sourceLine))
    ? normalizePositiveInt(candidate.sourceLine, 1)
    : null;
  const docLine = Number.isFinite(Number(candidate.docLine))
    ? normalizePositiveInt(candidate.docLine, 1)
    : null;
  return {
    id,
    label,
    detail,
    file: normalizeText(candidate.file),
    line: normalizePositiveInt(candidate.line, 1),
    depth: Math.max(0, Number(candidate.depth || 0)),
    kind,
    ...(group ? { group } : {}),
    ...(order !== null ? { order } : {}),
    ...(title ? { title } : {}),
    ...(moduleName ? { moduleName } : {}),
    ...(moduleRef ? { moduleRef } : {}),
    ...(sourceLine !== null ? { sourceLine } : {}),
    ...(docLine !== null ? { docLine } : {}),
    ...(hoverKicker ? { hoverKicker } : {}),
    capabilityItems: normalizeHoverItems(candidate.capabilityItems),
    baseItems: normalizeHoverItems(candidate.baseItems),
    width: size.width,
    height: size.height,
  };
}

function normalizeEdge(edge: unknown): GraphEdge | null {
  if (!edge || typeof edge !== "object") {
    return null;
  }
  const candidate = edge as Partial<GraphEdge>;
  const from = normalizeText(candidate.from);
  const to = normalizeText(candidate.to);
  if (!from || !to) {
    return null;
  }
  const rules = normalizeText(candidate.rules);
  const terms = normalizeText(candidate.terms);
  const file = normalizeText(candidate.file);
  const line = Number.isFinite(Number(candidate.line))
    ? normalizePositiveInt(candidate.line, 1)
    : null;
  return {
    id: normalizeText(candidate.id) || `${from}->${to}`,
    from,
    to,
    relation: normalizeText(candidate.relation) || "tree_child",
    ...(rules ? { rules } : {}),
    ...(terms ? { terms } : {}),
    ...(file ? { file } : {}),
    ...(line !== null ? { line } : {}),
  };
}

function normalizeLevelLabels(candidate: unknown): Map<number, string> {
  const labels = new Map<number, string>();
  if (!candidate || typeof candidate !== "object") {
    return labels;
  }
  for (const [rawKey, rawValue] of Object.entries(candidate as Record<string, unknown>)) {
    const level = Number(rawKey);
    if (!Number.isFinite(level)) {
      continue;
    }
    const label = normalizeText(rawValue);
    if (!label) {
      continue;
    }
    labels.set(level, label);
  }
  return labels;
}

function normalizeFrameworkGroup(candidate: unknown): RuntimeFrameworkGroup | null {
  if (!candidate || typeof candidate !== "object") {
    return null;
  }
  const raw = candidate as Partial<RuntimeFrameworkGroup>;
  const name = normalizeText(raw.name);
  if (!name) {
    return null;
  }
  const localLevels = Array.isArray(raw.localLevels)
    ? raw.localLevels
      .map((value) => Number(value))
      .filter((value) => Number.isFinite(value))
      .map((value) => Math.max(0, Math.floor(value)))
      .sort((left, right) => left - right)
    : [];
  const levelNodeCounts = new Map<number, number>();
  if (raw.levelNodeCounts && typeof raw.levelNodeCounts === "object") {
    for (const [rawKey, rawValue] of Object.entries(raw.levelNodeCounts as Record<string, unknown>)) {
      const level = Number(rawKey);
      const count = Number(rawValue);
      if (!Number.isFinite(level) || !Number.isFinite(count)) {
        continue;
      }
      levelNodeCounts.set(Math.max(0, Math.floor(level)), Math.max(0, Math.floor(count)));
    }
  }
  return {
    name,
    order: Number.isFinite(Number(raw.order)) ? Math.max(0, Number(raw.order)) : 0,
    localLevels,
    levelNodeCounts: Object.fromEntries(levelNodeCounts.entries()),
  };
}

export class TreeGraphModel {
  readonly title: string;
  readonly description: string;
  readonly footText: string;
  readonly layoutMode: RuntimeTreeLayoutMode;
  readonly nodes: GraphNode[];
  readonly edges: GraphEdge[];
  readonly nodeById: Map<string, GraphNode>;
  readonly outgoingById: Map<string, Set<string>>;
  readonly incomingById: Map<string, Set<string>>;
  readonly outgoingEdgesById: Map<string, GraphEdge[]>;
  readonly incomingEdgesById: Map<string, GraphEdge[]>;
  readonly edgeById: Map<string, GraphEdge>;
  readonly frameworkGroups: GraphFrameworkGroup[];
  readonly frameworkGroupByName: Map<string, GraphFrameworkGroup>;
  readonly levelLabels: Map<number, string>;
  readonly relationCounts: Map<string, number>;

  constructor(rawModel: RuntimeTreeModel) {
    this.title = normalizeText(rawModel.title) || "Shelf Tree";
    this.description = normalizeText(rawModel.description);
    this.footText = normalizeText(rawModel.footText);
    this.layoutMode = rawModel.layoutMode === "framework_columns" ? "framework_columns" : "global_levels";

    const nodeById = new Map<string, GraphNode>();
    const nodes: GraphNode[] = [];
    for (const candidate of rawModel.nodes || []) {
      const node = normalizeNode(candidate);
      if (!node || nodeById.has(node.id)) {
        continue;
      }
      nodeById.set(node.id, node);
      nodes.push(node);
    }

    const edgeById = new Map<string, GraphEdge>();
    const edges: GraphEdge[] = [];
    for (const candidate of rawModel.edges || []) {
      const edge = normalizeEdge(candidate);
      if (!edge) {
        continue;
      }
      if (!nodeById.has(edge.from) || !nodeById.has(edge.to)) {
        continue;
      }
      if (edgeById.has(edge.id)) {
        continue;
      }
      edgeById.set(edge.id, edge);
      edges.push(edge);
    }

    this.nodes = nodes;
    this.edges = edges;
    this.nodeById = nodeById;
    this.edgeById = edgeById;
    this.outgoingById = new Map<string, Set<string>>();
    this.incomingById = new Map<string, Set<string>>();
    this.outgoingEdgesById = new Map<string, GraphEdge[]>();
    this.incomingEdgesById = new Map<string, GraphEdge[]>();
    this.levelLabels = normalizeLevelLabels(rawModel.levelLabels);
    this.frameworkGroups = (rawModel.frameworkGroups || [])
      .map((candidate) => normalizeFrameworkGroup(candidate))
      .filter((entry): entry is GraphFrameworkGroup => Boolean(entry))
      .sort((left, right) => {
        if (left.order !== right.order) {
          return left.order - right.order;
        }
        return left.name.localeCompare(right.name);
      });
    this.frameworkGroupByName = new Map(this.frameworkGroups.map((group) => [group.name, group]));
    this.relationCounts = new Map<string, number>();

    for (const node of nodes) {
      this.outgoingById.set(node.id, new Set());
      this.incomingById.set(node.id, new Set());
      this.outgoingEdgesById.set(node.id, []);
      this.incomingEdgesById.set(node.id, []);
    }
    for (const edge of edges) {
      this.outgoingById.get(edge.from)?.add(edge.to);
      this.incomingById.get(edge.to)?.add(edge.from);
      this.outgoingEdgesById.get(edge.from)?.push(edge);
      this.incomingEdgesById.get(edge.to)?.push(edge);
      this.relationCounts.set(edge.relation, (this.relationCounts.get(edge.relation) || 0) + 1);
    }

    if (rawModel.relationCounts && typeof rawModel.relationCounts === "object") {
      for (const [relation, count] of Object.entries(rawModel.relationCounts)) {
        const normalizedCount = Number(count);
        if (!Number.isFinite(normalizedCount)) {
          continue;
        }
        this.relationCounts.set(relation, Math.max(0, Math.floor(normalizedCount)));
      }
    }
  }

  hasNode(nodeId: string): boolean {
    return this.nodeById.has(nodeId);
  }

  node(nodeId: string): GraphNode | null {
    return this.nodeById.get(nodeId) || null;
  }

  edge(edgeId: string): GraphEdge | null {
    return this.edgeById.get(edgeId) || null;
  }

  outgoingEdges(nodeId: string): GraphEdge[] {
    return [...(this.outgoingEdgesById.get(nodeId) || [])];
  }

  incomingEdges(nodeId: string): GraphEdge[] {
    return [...(this.incomingEdgesById.get(nodeId) || [])];
  }

  levelLabel(level: number): string {
    return this.levelLabels.get(level) || `L${level}`;
  }

  matchNodeIdsByQuery(rawQuery: string): Set<string> {
    const query = normalizeText(rawQuery).toLowerCase();
    if (!query) {
      return new Set(this.nodeById.keys());
    }
    const matched = new Set<string>();
    for (const node of this.nodes) {
      const haystack = [
        node.id,
        node.label,
        node.detail,
        node.group || "",
        node.title || "",
        node.moduleName || "",
        node.moduleRef || "",
      ].join(" ").toLowerCase();
      if (haystack.includes(query)) {
        matched.add(node.id);
      }
    }
    return matched;
  }

  collectReachable(nodeId: string, direction: "incoming" | "outgoing"): Set<string> {
    if (!this.nodeById.has(nodeId)) {
      return new Set();
    }
    const visited = new Set<string>();
    const queue: string[] = [nodeId];
    while (queue.length) {
      const current = queue.shift() || "";
      if (!current || visited.has(current)) {
        continue;
      }
      visited.add(current);
      const neighbors = direction === "incoming"
        ? this.incomingById.get(current)
        : this.outgoingById.get(current);
      for (const neighbor of neighbors || []) {
        if (!visited.has(neighbor)) {
          queue.push(neighbor);
        }
      }
    }
    return visited;
  }

  computeFilterResult(params: {
    query: string;
    focusMode: FocusMode;
    selectedNodeId: string;
  }): FilterResult {
    const queryMatches = this.matchNodeIdsByQuery(params.query);
    const selectedNodeId = normalizeText(params.selectedNodeId);
    let focusSet = new Set<string>(this.nodeById.keys());
    if (selectedNodeId && params.focusMode !== "all" && this.nodeById.has(selectedNodeId)) {
      focusSet = this.collectReachable(
        selectedNodeId,
        params.focusMode === "upstream" ? "incoming" : "outgoing"
      );
      focusSet.add(selectedNodeId);
    }

    const visibleNodeIds = new Set<string>();
    for (const nodeId of focusSet) {
      if (queryMatches.has(nodeId)) {
        visibleNodeIds.add(nodeId);
      }
    }

    if (selectedNodeId && this.nodeById.has(selectedNodeId)) {
      visibleNodeIds.add(selectedNodeId);
    }

    const visibleEdgeIds = new Set<string>();
    for (const edge of this.edges) {
      if (visibleNodeIds.has(edge.from) && visibleNodeIds.has(edge.to)) {
        visibleEdgeIds.add(edge.id);
      }
    }

    return {
      visibleNodeIds,
      visibleEdgeIds,
    };
  }

  adjacentNodeIds(nodeId: string): Set<string> {
    const adjacent = new Set<string>();
    for (const upstream of this.incomingById.get(nodeId) || []) {
      adjacent.add(upstream);
    }
    for (const downstream of this.outgoingById.get(nodeId) || []) {
      adjacent.add(downstream);
    }
    return adjacent;
  }
}
