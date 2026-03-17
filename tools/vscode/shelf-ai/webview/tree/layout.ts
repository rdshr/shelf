import dagre from "dagre";
import type {
  DepthBand,
  GraphFrameworkGroup,
  GraphNode,
  LayoutEdge,
  LayoutGroupFrame,
  LayoutNode,
  LayoutSnapshot,
  RuntimeTreeLayoutSettings,
} from "./types";
import { TreeGraphModel } from "./model";

const FRAMEWORK_PANEL_Y = 16;
const FRAMEWORK_PANEL_HEADER_HEIGHT = 40;
const FRAMEWORK_PANEL_MIN_WIDTH = 192;
const FRAMEWORK_PANEL_LEFT_MARGIN = 18;
const FRAMEWORK_PANEL_RIGHT_MARGIN = 14;
const FRAMEWORK_PANEL_BOTTOM_MARGIN = 18;
const FRAMEWORK_PANEL_GAP = 12;
const FRAMEWORK_PANEL_PADDING_LEFT = 10;
const FRAMEWORK_PANEL_PADDING_RIGHT = 10;
const FRAMEWORK_LEVEL_GAP = 80;
const FRAMEWORK_LEVEL_BAND_HEIGHT = 68;
const FRAMEWORK_NODE_Y_OFFSET = FRAMEWORK_LEVEL_BAND_HEIGHT / 2;
const FRAMEWORK_BOTTOM_PADDING = 16;
const FRAMEWORK_TOP_PADDING = 8;
const FRAMEWORK_ROW_NODE_GAP = 8;
const FRAMEWORK_ROW_EDGE_PADDING = 2;
const FRAMEWORK_LEVEL_GAP_MIN = 48;
const FRAMEWORK_LEVEL_GAP_MAX = 180;
const FRAMEWORK_ROW_NODE_GAP_MIN = 0;
const FRAMEWORK_ROW_NODE_GAP_MAX = 40;

interface NormalizedLayoutSettings {
  frameworkNodeHorizontalGap: number;
  frameworkLevelVerticalGap: number;
}

function clampInt(value: unknown, minimum: number, maximum: number, fallback: number): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    return fallback;
  }
  return Math.min(maximum, Math.max(minimum, Math.round(parsed)));
}

function normalizeLayoutSettings(settings?: RuntimeTreeLayoutSettings): NormalizedLayoutSettings {
  return {
    frameworkNodeHorizontalGap: clampInt(
      settings?.frameworkNodeHorizontalGap,
      FRAMEWORK_ROW_NODE_GAP_MIN,
      FRAMEWORK_ROW_NODE_GAP_MAX,
      FRAMEWORK_ROW_NODE_GAP
    ),
    frameworkLevelVerticalGap: clampInt(
      settings?.frameworkLevelVerticalGap,
      FRAMEWORK_LEVEL_GAP_MIN,
      FRAMEWORK_LEVEL_GAP_MAX,
      FRAMEWORK_LEVEL_GAP
    ),
  };
}

function buildLayoutEdges(
  model: TreeGraphModel,
  nodesById: Map<string, LayoutNode>
): LayoutEdge[] {
  const edges: LayoutEdge[] = [];
  for (const edge of model.edges) {
    const from = nodesById.get(edge.from);
    const to = nodesById.get(edge.to);
    if (!from || !to) {
      continue;
    }
    edges.push({
      ...edge,
      fromX: from.x,
      fromY: from.y,
      toX: to.x,
      toY: to.y,
    });
  }
  return edges;
}

function depthBands(model: TreeGraphModel, nodes: Iterable<LayoutNode>): DepthBand[] {
  const buckets = new Map<number, LayoutNode[]>();
  for (const node of nodes) {
    if (!buckets.has(node.depth)) {
      buckets.set(node.depth, []);
    }
    buckets.get(node.depth)?.push(node);
  }

  const bands: DepthBand[] = [];
  for (const [depth, items] of buckets.entries()) {
    let minX = Number.POSITIVE_INFINITY;
    let maxX = Number.NEGATIVE_INFINITY;
    let minY = Number.POSITIVE_INFINITY;
    let maxY = Number.NEGATIVE_INFINITY;
    for (const node of items) {
      minX = Math.min(minX, node.x - node.width / 2);
      maxX = Math.max(maxX, node.x + node.width / 2);
      minY = Math.min(minY, node.y - node.height / 2);
      maxY = Math.max(maxY, node.y + node.height / 2);
    }
    bands.push({
      depth,
      label: model.levelLabel(depth),
      x: minX - 28,
      y: minY - 26,
      width: Math.max(1, maxX - minX + 56),
      height: Math.max(1, maxY - minY + 52),
    });
  }

  return bands.sort((left, right) => left.depth - right.depth);
}

function nodeSortKey(node: GraphNode): [number, number, string] {
  return [
    node.order === undefined ? 1 : 0,
    node.order ?? 0,
    node.id,
  ];
}

function refineLevelOrders(
  levels: number[],
  levelOrders: Map<number, string[]>,
  nodeById: Map<string, GraphNode>,
  incoming: Map<string, string[]>,
  outgoing: Map<string, string[]>
): void {
  const sweep = (levelSequence: number[], neighborsOf: Map<string, string[]>): void => {
    const nodeSlot = new Map<string, number>();
    for (const level of levels) {
      const row = levelOrders.get(level) || [];
      row.forEach((nodeId, index) => {
        nodeSlot.set(nodeId, index);
      });
    }

    for (const level of levelSequence) {
      const row = [...(levelOrders.get(level) || [])];
      row.sort((leftId, rightId) => {
        const leftNode = nodeById.get(leftId);
        const rightNode = nodeById.get(rightId);
        if (!leftNode || !rightNode) {
          return leftId.localeCompare(rightId);
        }
        if (leftNode.order !== undefined || rightNode.order !== undefined) {
          const leftKey = nodeSortKey(leftNode);
          const rightKey = nodeSortKey(rightNode);
          if (leftKey[0] !== rightKey[0]) {
            return leftKey[0] - rightKey[0];
          }
          if (leftKey[1] !== rightKey[1]) {
            return leftKey[1] - rightKey[1];
          }
          return leftKey[2].localeCompare(rightKey[2]);
        }

        const barycenterFor = (nodeId: string): number => {
          const rankedNeighbors = (neighborsOf.get(nodeId) || [])
            .map((neighborId) => nodeSlot.get(neighborId))
            .filter((slot): slot is number => slot !== undefined);
          if (!rankedNeighbors.length) {
            const index = row.indexOf(nodeId);
            return index >= 0 ? index : 0;
          }
          return rankedNeighbors.reduce((sum, slot) => sum + slot, 0) / rankedNeighbors.length;
        };

        const leftCenter = barycenterFor(leftId);
        const rightCenter = barycenterFor(rightId);
        if (leftCenter !== rightCenter) {
          return leftCenter - rightCenter;
        }
        return leftId.localeCompare(rightId);
      });
      levelOrders.set(level, row);
    }
  };

  if (levels.length <= 1) {
    return;
  }

  for (let iteration = 0; iteration < 6; iteration += 1) {
    sweep(levels.slice(1), incoming);
    sweep(levels.slice(0, -1).reverse(), outgoing);
  }
}

function computeFrameworkColumnsLayout(
  model: TreeGraphModel,
  settings: NormalizedLayoutSettings
): LayoutSnapshot {
  const groups = model.frameworkGroups.length
    ? model.frameworkGroups
    : [...new Set(model.nodes.map((node) => node.group).filter((value): value is string => Boolean(value)))]
      .sort((left, right) => left.localeCompare(right))
      .map((name, index) => ({
        name,
        order: index,
        localLevels: model.nodes
          .filter((node) => node.group === name)
          .map((node) => node.depth)
          .sort((left, right) => left - right),
        levelNodeCounts: Object.fromEntries(
          model.nodes
            .filter((node) => node.group === name)
            .reduce((counts, node) => {
              counts.set(node.depth, (counts.get(node.depth) || 0) + 1);
              return counts;
            }, new Map<number, number>())
            .entries()
        ),
      }));

  if (!groups.length) {
    return computeGlobalLayout(model);
  }

  const nodeById = new Map(model.nodes.map((node) => [node.id, node]));
  const nodeIdsByFramework = new Map<string, string[]>();
  for (const node of model.nodes) {
    const frameworkName = node.group || node.moduleName;
    if (!frameworkName) {
      continue;
    }
    const nodeIds = nodeIdsByFramework.get(frameworkName) || [];
    nodeIds.push(node.id);
    nodeIdsByFramework.set(frameworkName, nodeIds);
  }

  const incoming = new Map<string, string[]>();
  const outgoing = new Map<string, string[]>();
  for (const node of model.nodes) {
    incoming.set(node.id, []);
    outgoing.set(node.id, []);
  }
  for (const edge of model.edges) {
    incoming.get(edge.to)?.push(edge.from);
    outgoing.get(edge.from)?.push(edge.to);
  }

  const nodesById = new Map<string, LayoutNode>();
  const groupFrames: LayoutGroupFrame[] = [];
  const bands: DepthBand[] = [];
  let cursorX = FRAMEWORK_PANEL_LEFT_MARGIN;
  let maxHeight = FRAMEWORK_PANEL_Y + FRAMEWORK_PANEL_HEADER_HEIGHT + FRAMEWORK_BOTTOM_PADDING;

  for (const group of groups.sort((left, right) => {
    if (left.order !== right.order) {
      return left.order - right.order;
    }
    return left.name.localeCompare(right.name);
  })) {
    const groupNodeIds = nodeIdsByFramework.get(group.name) || [];
    if (!groupNodeIds.length) {
      continue;
    }

    const levelOrders = new Map<number, string[]>();
    const localLevels = [...new Set(group.localLevels)].sort((left, right) => left - right);
    for (const localLevel of localLevels) {
      const rowIds = groupNodeIds
        .filter((nodeId) => nodeById.get(nodeId)?.depth === localLevel)
        .sort((leftId, rightId) => {
          const leftNode = nodeById.get(leftId);
          const rightNode = nodeById.get(rightId);
          if (!leftNode || !rightNode) {
            return leftId.localeCompare(rightId);
          }
          const leftKey = nodeSortKey(leftNode);
          const rightKey = nodeSortKey(rightNode);
          if (leftKey[0] !== rightKey[0]) {
            return leftKey[0] - rightKey[0];
          }
          if (leftKey[1] !== rightKey[1]) {
            return leftKey[1] - rightKey[1];
          }
          return leftKey[2].localeCompare(rightKey[2]);
        });
      if (rowIds.length) {
        levelOrders.set(localLevel, rowIds);
      }
    }
    if (!levelOrders.size) {
      continue;
    }

    const sortedLevels = [...levelOrders.keys()].sort((left, right) => left - right);
    refineLevelOrders(sortedLevels, levelOrders, nodeById, incoming, outgoing);

    const rowWidthByLevel = new Map<number, number>();
    for (const level of sortedLevels) {
      const rowIds = levelOrders.get(level) || [];
      const rowWidth = rowIds.reduce((sum, nodeId) => {
        const node = nodeById.get(nodeId);
        return sum + (node?.width || 0);
      }, 0) + Math.max(0, rowIds.length - 1) * settings.frameworkNodeHorizontalGap;
      rowWidthByLevel.set(level, rowWidth);
    }
    const widestRowWidth = Math.max(...sortedLevels.map((level) => rowWidthByLevel.get(level) || 0));
    const usableWidth = Math.max(
      FRAMEWORK_PANEL_MIN_WIDTH - FRAMEWORK_PANEL_PADDING_LEFT - FRAMEWORK_PANEL_PADDING_RIGHT,
      widestRowWidth + FRAMEWORK_ROW_EDGE_PADDING * 2
    );
    const groupWidth = Math.max(
      FRAMEWORK_PANEL_MIN_WIDTH,
      usableWidth + FRAMEWORK_PANEL_PADDING_LEFT + FRAMEWORK_PANEL_PADDING_RIGHT
    );
    const levelStackHeight = (Math.max(0, sortedLevels.length - 1) * settings.frameworkLevelVerticalGap)
      + FRAMEWORK_LEVEL_BAND_HEIGHT;
    const groupHeight = FRAMEWORK_PANEL_HEADER_HEIGHT
      + FRAMEWORK_TOP_PADDING
      + levelStackHeight
      + FRAMEWORK_BOTTOM_PADDING;

    groupFrames.push({
      name: group.name,
      x: cursorX,
      y: FRAMEWORK_PANEL_Y,
      width: groupWidth,
      height: groupHeight,
      localLevels: sortedLevels,
      order: group.order,
    });

    for (const [levelIndex, level] of sortedLevels.entries()) {
      const rowIds = levelOrders.get(level) || [];
      const bandY = FRAMEWORK_PANEL_Y + FRAMEWORK_PANEL_HEADER_HEIGHT + FRAMEWORK_TOP_PADDING
        + levelIndex * settings.frameworkLevelVerticalGap;
      bands.push({
        depth: level,
        label: model.levelLabel(level),
        x: cursorX + 10,
        y: bandY,
        width: groupWidth - 20,
        height: FRAMEWORK_LEVEL_BAND_HEIGHT,
        groupName: group.name,
      });

      const y = bandY + FRAMEWORK_NODE_Y_OFFSET;
      const rowWidth = rowWidthByLevel.get(level) || 0;
      const centeredStart = cursorX + (groupWidth - rowWidth) / 2;
      const minStart = cursorX + FRAMEWORK_PANEL_PADDING_LEFT;
      const maxStart = cursorX + groupWidth - FRAMEWORK_PANEL_PADDING_RIGHT - rowWidth;
      let rowCursorX = Math.min(
        Math.max(centeredStart, minStart),
        Math.max(minStart, maxStart)
      );

      rowIds.forEach((nodeId) => {
        const node = nodeById.get(nodeId);
        if (!node) {
          return;
        }
        const x = rowCursorX + node.width / 2;
        rowCursorX += node.width + settings.frameworkNodeHorizontalGap;
        nodesById.set(nodeId, {
          ...node,
          x,
          y,
        });
      });
    }

    cursorX += groupWidth + FRAMEWORK_PANEL_GAP;
    maxHeight = Math.max(maxHeight, FRAMEWORK_PANEL_Y + groupHeight + FRAMEWORK_PANEL_BOTTOM_MARGIN);
  }

  const width = Math.max(1080, Math.round(cursorX - FRAMEWORK_PANEL_GAP + FRAMEWORK_PANEL_RIGHT_MARGIN));
  const height = Math.max(600, Math.round(maxHeight));
  const edges = buildLayoutEdges(model, nodesById);

  return {
    width,
    height,
    nodes: nodesById,
    edges,
    bands,
    groupFrames,
  };
}

function computeGlobalLayout(model: TreeGraphModel): LayoutSnapshot {
  const graph = new dagre.graphlib.Graph({ multigraph: false, compound: false });
  graph.setGraph({
    rankdir: "LR",
    align: "UL",
    ranksep: 132,
    nodesep: 32,
    edgesep: 20,
    marginx: 84,
    marginy: 56,
  });
  graph.setDefaultEdgeLabel(() => ({}));

  for (const node of model.nodes) {
    graph.setNode(node.id, {
      width: node.width,
      height: node.height,
      rank: node.depth,
    });
  }
  for (const edge of model.edges) {
    graph.setEdge(edge.from, edge.to);
  }
  dagre.layout(graph);

  const nodesById = new Map<string, LayoutNode>();
  for (const node of model.nodes) {
    const point = graph.node(node.id) as { x?: number; y?: number } | undefined;
    const fallbackX = 180 + node.depth * 240;
    const fallbackY = 120 + nodesById.size * 90;
    nodesById.set(node.id, {
      ...node,
      x: Number(point?.x || fallbackX),
      y: Number(point?.y || fallbackY),
    });
  }

  const edges = buildLayoutEdges(model, nodesById);
  const graphLabel = graph.graph() as {
    width?: number;
    height?: number;
  };
  const width = Math.max(980, Number(graphLabel.width || 0) + 180);
  const height = Math.max(620, Number(graphLabel.height || 0) + 160);

  return {
    width,
    height,
    nodes: nodesById,
    edges,
    bands: depthBands(model, nodesById.values()),
    groupFrames: [],
  };
}

export function computeTreeLayout(
  model: TreeGraphModel,
  rawSettings?: RuntimeTreeLayoutSettings
): LayoutSnapshot {
  const settings = normalizeLayoutSettings(rawSettings);
  return model.layoutMode === "framework_columns"
    ? computeFrameworkColumnsLayout(model, settings)
    : computeGlobalLayout(model);
}

export function cloneLayoutNode(node: GraphNode & { x: number; y: number }): LayoutNode {
  return {
    ...node,
    x: Number(node.x),
    y: Number(node.y),
  };
}
