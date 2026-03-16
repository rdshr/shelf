export type TreeKind = "framework" | "evidence";
export type FocusMode = "all" | "upstream" | "downstream";
export type RuntimeTreeLayoutMode = "global_levels" | "framework_columns";

export interface HoverItem {
  token: string;
  text: string;
}

export interface RuntimeTreeNode {
  id: string;
  label: string;
  detail: string;
  file: string;
  line: number;
  depth: number;
  kind: string;
  group?: string;
  order?: number;
  title?: string;
  moduleName?: string;
  moduleRef?: string;
  sourceLine?: number;
  docLine?: number;
  hoverKicker?: string;
  capabilityItems?: HoverItem[];
  baseItems?: HoverItem[];
}

export interface RuntimeTreeEdge {
  id: string;
  from: string;
  to: string;
  relation: string;
  rules?: string;
  terms?: string;
  file?: string;
  line?: number;
}

export interface RuntimeFrameworkGroup {
  name: string;
  order: number;
  localLevels: number[];
  levelNodeCounts: Record<number, number>;
}

export interface RuntimeTreeLayoutSettings {
  frameworkNodeHorizontalGap: number;
  frameworkLevelVerticalGap: number;
}

export interface RuntimeTreeViewSettings {
  zoomMinScale: number;
  zoomMaxScale: number;
  wheelSensitivity: number;
  inspectorWidth: number;
  inspectorRailWidth: number;
}

export interface RuntimeTreeModel {
  title: string;
  description: string;
  kind: TreeKind;
  nodes: RuntimeTreeNode[];
  edges: RuntimeTreeEdge[];
  footText?: string;
  layoutMode?: RuntimeTreeLayoutMode;
  levelLabels?: Record<number, string>;
  frameworkGroups?: RuntimeFrameworkGroup[];
  relationCounts?: Record<string, number>;
}

export interface RuntimeTreeBootstrap {
  version: number;
  kind: TreeKind;
  model: RuntimeTreeModel;
  layoutSettings: RuntimeTreeLayoutSettings;
  viewSettings: RuntimeTreeViewSettings;
}

export interface PersistedTreeUiState {
  selectedNodeId: string;
  focusMode: FocusMode;
  searchQuery: string;
  inspectorPinned: boolean;
  zoomScale: number;
  zoomX: number;
  zoomY: number;
}

export interface GraphNode extends RuntimeTreeNode {
  width: number;
  height: number;
}

export interface GraphEdge extends RuntimeTreeEdge {}

export interface GraphFrameworkGroup extends RuntimeFrameworkGroup {}

export interface LayoutNode extends GraphNode {
  x: number;
  y: number;
}

export interface LayoutEdge extends GraphEdge {
  fromX: number;
  fromY: number;
  toX: number;
  toY: number;
}

export interface DepthBand {
  depth: number;
  label: string;
  x: number;
  y: number;
  width: number;
  height: number;
  groupName?: string;
}

export interface LayoutGroupFrame {
  name: string;
  x: number;
  y: number;
  width: number;
  height: number;
  localLevels: number[];
  order: number;
}

export interface LayoutSnapshot {
  width: number;
  height: number;
  nodes: Map<string, LayoutNode>;
  edges: LayoutEdge[];
  bands: DepthBand[];
  groupFrames: LayoutGroupFrame[];
}

export interface FilterResult {
  visibleNodeIds: Set<string>;
  visibleEdgeIds: Set<string>;
}

export type TreeSelection =
  | { kind: "none" }
  | { kind: "node"; nodeId: string }
  | { kind: "edge"; edgeId: string };
