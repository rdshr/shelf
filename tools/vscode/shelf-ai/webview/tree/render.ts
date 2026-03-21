import { select, type Selection } from "d3-selection";
import { zoom, zoomIdentity, zoomTransform, type ZoomBehavior, type ZoomTransform } from "d3-zoom";
import { TreeGraphModel } from "./model";
import type {
  FilterResult,
  LayoutEdge,
  LayoutNode,
  LayoutSnapshot,
  PersistedTreeUiState,
  RuntimeTreeViewSettings,
  TreeSelection,
} from "./types";

export interface CanvasElements {
  scrollElement: HTMLElement;
  svgElement: SVGSVGElement;
  viewportElement: SVGGElement;
  groupLayerElement: SVGGElement;
  bandLayerElement: SVGGElement;
  edgeLayerElement: SVGGElement;
  nodeLayerElement: SVGGElement;
  hoverCardElement: HTMLElement;
  statusElement: HTMLElement;
  zoomChipElement: HTMLElement;
  countChipElement: HTMLElement;
  visibleChipElement: HTMLElement;
}

export interface CanvasCallbacks {
  onSelectionChanged: (selection: TreeSelection) => void;
  onNodeOpened: (nodeId: string) => void;
  onEdgeOpened: (edgeId: string) => void;
  onStateChanged: () => void;
}

interface EdgeRenderRefs {
  visiblePath: SVGPathElement;
  hitPath: SVGPathElement;
}

const EDGE_ARROW_DEFAULT_MARKER_ID = "tree-edge-arrow-default";
const EDGE_ARROW_ACTIVE_MARKER_ID = "tree-edge-arrow-active";
const DEFAULT_ZOOM_MIN_SCALE = 0.68;
const DEFAULT_ZOOM_MAX_SCALE = 1.55;
const DEFAULT_WHEEL_SENSITIVITY = 1;
const ZOOM_WHEEL_DELTA_BASE_MIN = -0.08;
const ZOOM_WHEEL_DELTA_BASE_MAX = 0.08;
const MODULE_NODE_RADIUS = 18;
const DEFAULT_NODE_RADIUS = 16;

function clampNumber(value: unknown, minimum: number, maximum: number, fallback: number): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    return fallback;
  }
  return Math.min(maximum, Math.max(minimum, parsed));
}

function normalizeViewSettings(settings?: RuntimeTreeViewSettings): RuntimeTreeViewSettings {
  const zoomMinScale = clampNumber(settings?.zoomMinScale, 0.2, 3, DEFAULT_ZOOM_MIN_SCALE);
  const zoomMaxScale = clampNumber(settings?.zoomMaxScale, zoomMinScale, 5, DEFAULT_ZOOM_MAX_SCALE);
  return {
    zoomMinScale,
    zoomMaxScale,
    wheelSensitivity: clampNumber(settings?.wheelSensitivity, 0.25, 3, DEFAULT_WHEEL_SENSITIVITY),
    inspectorWidth: Number.isFinite(Number(settings?.inspectorWidth)) ? Number(settings?.inspectorWidth) : 338,
    inspectorRailWidth: Number.isFinite(Number(settings?.inspectorRailWidth)) ? Number(settings?.inspectorRailWidth) : 42,
  };
}

function shortText(value: string, maxLength: number): string {
  if (value.length <= maxLength) {
    return value;
  }
  return `${value.slice(0, Math.max(0, maxLength - 1))}…`;
}

function escapeHtml(value: string): string {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function kindClass(kind: string): string {
  if (kind.includes("root")) {
    return "node-root";
  }
  if (kind.includes("group")) {
    return "node-group";
  }
  if (kind.includes("module")) {
    return "node-module";
  }
  if (kind.includes("project")) {
    return "node-project";
  }
  if (kind.includes("config")) {
    return "node-config";
  }
  if (kind.includes("code")) {
    return "node-code";
  }
  if (kind.includes("evidence")) {
    return "node-evidence";
  }
  return "node-generic";
}

function compactNodeId(node: LayoutNode): string {
  const moduleName = String(node.moduleName || "").trim();
  const moduleRef = String(node.moduleRef || "").trim();
  if (moduleName && moduleRef) {
    return `${moduleName}.${moduleRef}`;
  }
  if (moduleRef) {
    return moduleRef;
  }
  if (node.label) {
    return node.label;
  }
  return node.id;
}

function nodeRadius(node: LayoutNode): number {
  return node.kind.includes("module")
    ? MODULE_NODE_RADIUS
    : DEFAULT_NODE_RADIUS;
}

function edgeEndpoints(fromNode: LayoutNode, toNode: LayoutNode): {
  startX: number;
  startY: number;
  endX: number;
  endY: number;
} {
  const dx = toNode.x - fromNode.x;
  const dy = toNode.y - fromNode.y;
  const distance = Math.max(1, Math.hypot(dx, dy));
  const ux = dx / distance;
  const uy = dy / distance;
  const maxPad = Math.max(0, distance / 2 - 6);
  const startPad = Math.min(nodeRadius(fromNode) + 4, maxPad);
  const endPad = Math.min(nodeRadius(toNode) + 3, maxPad);
  return {
    startX: fromNode.x + ux * startPad,
    startY: fromNode.y + uy * startPad,
    endX: toNode.x - ux * endPad,
    endY: toNode.y - uy * endPad,
  };
}

function edgePath(fromNode: LayoutNode, toNode: LayoutNode): string {
  const points = edgeEndpoints(fromNode, toNode);
  const dx = points.endX - points.startX;
  const dy = points.endY - points.startY;
  const curve = Math.max(28, Math.min(92, Math.abs(dy) * 0.36));
  const sidePull = dx === 0
    ? 0
    : Math.sign(dx) * Math.max(20, Math.min(84, Math.abs(dx) * 0.22));
  const c1x = points.startX + sidePull;
  const c1y = points.startY + curve;
  const c2x = points.endX - sidePull;
  const c2y = points.endY - curve;
  return `M ${points.startX} ${points.startY} C ${c1x} ${c1y}, ${c2x} ${c2y}, ${points.endX} ${points.endY}`;
}

function sanitizeState(
  state: PersistedTreeUiState | null,
  viewSettings: RuntimeTreeViewSettings
): PersistedTreeUiState {
  return {
    selectedNodeId: String(state?.selectedNodeId || ""),
    focusMode: state?.focusMode === "upstream" || state?.focusMode === "downstream"
      ? state.focusMode
      : "all",
    searchQuery: String(state?.searchQuery || ""),
    inspectorPinned: state?.inspectorPinned === true,
    zoomScale: Number.isFinite(Number(state?.zoomScale))
      ? Math.min(viewSettings.zoomMaxScale, Math.max(viewSettings.zoomMinScale, Number(state?.zoomScale)))
      : Math.min(viewSettings.zoomMaxScale, Math.max(viewSettings.zoomMinScale, 1)),
    zoomX: Number.isFinite(Number(state?.zoomX)) ? Number(state?.zoomX) : 0,
    zoomY: Number.isFinite(Number(state?.zoomY)) ? Number(state?.zoomY) : 0,
  };
}

function computeNodeBounds(nodes: LayoutNode[]): {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
} | null {
  if (!nodes.length) {
    return null;
  }
  let minX = Number.POSITIVE_INFINITY;
  let minY = Number.POSITIVE_INFINITY;
  let maxX = Number.NEGATIVE_INFINITY;
  let maxY = Number.NEGATIVE_INFINITY;
  for (const node of nodes) {
    minX = Math.min(minX, node.x - node.width / 2);
    minY = Math.min(minY, node.y - node.height / 2);
    maxX = Math.max(maxX, node.x + node.width / 2);
    maxY = Math.max(maxY, node.y + node.height / 2);
  }
  return { minX, minY, maxX, maxY };
}

function hoverList(items: { token: string; text: string }[], emptyText: string, maxItems = 3): string {
  if (!items.length) {
    return `<li class="hover-item">${escapeHtml(emptyText)}</li>`;
  }
  const visibleItems = items.slice(0, maxItems).map((item) => {
    const token = escapeHtml(item.token);
    const text = escapeHtml(item.text);
    return `<li class="hover-item">${token ? `<b>${token}</b> ` : ""}${text}</li>`;
  });
  if (items.length > maxItems) {
    visibleItems.push(`<li class="hover-item">还有 ${items.length - maxItems} 项</li>`);
  }
  return visibleItems.join("");
}

export class TreeCanvasRenderer {
  private readonly elements: CanvasElements;
  private readonly callbacks: CanvasCallbacks;
  private readonly model: TreeGraphModel;
  private readonly layout: LayoutSnapshot;
  private readonly viewSettings: RuntimeTreeViewSettings;
  private readonly svgSelection: Selection<SVGSVGElement, unknown, null, undefined>;
  private readonly viewportSelection: Selection<SVGGElement, unknown, null, undefined>;
  private readonly zoomBehavior: ZoomBehavior<SVGSVGElement, unknown>;
  private readonly nodeElementById: Map<string, SVGGElement>;
  private readonly edgeElementById: Map<string, EdgeRenderRefs>;
  private readonly initialPositions: Map<string, { x: number; y: number }>;
  private selectedNodeId: string;
  private selectedEdgeId: string;
  private hoveredNodeId: string;
  private hoveredEdgeId: string;
  private visibleNodeIds: Set<string>;
  private visibleEdgeIds: Set<string>;
  private geometryFrame: number | null;

  constructor(
    elements: CanvasElements,
    model: TreeGraphModel,
    layout: LayoutSnapshot,
    viewSettings: RuntimeTreeViewSettings,
    callbacks: CanvasCallbacks
  ) {
    this.elements = elements;
    this.model = model;
    this.layout = layout;
    this.viewSettings = normalizeViewSettings(viewSettings);
    this.callbacks = callbacks;
    this.svgSelection = select(elements.svgElement);
    this.viewportSelection = select(elements.viewportElement);
    this.zoomBehavior = zoom<SVGSVGElement, unknown>()
      .scaleExtent([this.viewSettings.zoomMinScale, this.viewSettings.zoomMaxScale])
      .wheelDelta((event) => {
        const factor = (event.deltaMode === 1 ? 0.006 : 0.0009) * this.viewSettings.wheelSensitivity;
        const delta = -event.deltaY * factor;
        const minDelta = ZOOM_WHEEL_DELTA_BASE_MIN * this.viewSettings.wheelSensitivity;
        const maxDelta = ZOOM_WHEEL_DELTA_BASE_MAX * this.viewSettings.wheelSensitivity;
        return Math.max(minDelta, Math.min(maxDelta, delta));
      })
      .on("zoom", (event) => {
        this.viewportSelection.attr("transform", event.transform.toString());
        this.elements.zoomChipElement.textContent = `${Math.round(event.transform.k * 100)}%`;
        this.hideHoverCard();
        this.callbacks.onStateChanged();
      });
    this.nodeElementById = new Map();
    this.edgeElementById = new Map();
    this.initialPositions = new Map(
      [...this.layout.nodes.entries()].map(([nodeId, node]) => [nodeId, { x: node.x, y: node.y }])
    );
    this.selectedNodeId = "";
    this.selectedEdgeId = "";
    this.hoveredNodeId = "";
    this.hoveredEdgeId = "";
    this.visibleNodeIds = new Set();
    this.visibleEdgeIds = new Set();
    this.geometryFrame = null;
  }

  mount(initialState: PersistedTreeUiState | null): void {
    this.svgSelection.call(this.zoomBehavior);
    this.ensureEdgeMarker();
    this.renderGroups();
    this.renderBands();
    this.renderEdges();
    this.renderNodes();
    this.elements.svgElement.setAttribute("viewBox", `0 0 ${this.layout.width} ${this.layout.height}`);
    this.elements.countChipElement.textContent = `Nodes ${this.model.nodes.length} / Edges ${this.model.edges.length}`;
    this.applyPersistedState(initialState);
  }

  applyFilter(result: FilterResult): void {
    this.visibleNodeIds = result.visibleNodeIds;
    this.visibleEdgeIds = result.visibleEdgeIds;
    this.elements.visibleChipElement.textContent = `Visible ${this.visibleNodeIds.size}`;

    for (const [nodeId, element] of this.nodeElementById.entries()) {
      const isVisible = this.visibleNodeIds.has(nodeId);
      element.classList.toggle("hidden", !isVisible);
    }
    for (const [edgeId, refs] of this.edgeElementById.entries()) {
      const isVisible = this.visibleEdgeIds.has(edgeId);
      refs.visiblePath.classList.toggle("hidden", !isVisible);
      refs.hitPath.classList.toggle("hidden", !isVisible);
    }

    if (this.selectedNodeId && !this.visibleNodeIds.has(this.selectedNodeId)) {
      this.selectedNodeId = "";
    }
    if (this.selectedEdgeId && !this.visibleEdgeIds.has(this.selectedEdgeId)) {
      this.selectedEdgeId = "";
    }

    this.refreshHighlightState();
    this.callbacks.onSelectionChanged(this.selectedSelection());
  }

  selectNode(nodeId: string): void {
    this.selectedNodeId = nodeId && this.model.hasNode(nodeId) ? nodeId : "";
    this.selectedEdgeId = "";
    this.refreshHighlightState();
    this.callbacks.onSelectionChanged(this.selectedSelection());
    this.callbacks.onStateChanged();
  }

  selectEdge(edgeId: string): void {
    this.selectedEdgeId = edgeId && this.model.edge(edgeId) ? edgeId : "";
    this.selectedNodeId = "";
    this.refreshHighlightState();
    this.callbacks.onSelectionChanged(this.selectedSelection());
  }

  clearSelection(): void {
    this.selectedNodeId = "";
    this.selectedEdgeId = "";
    this.refreshHighlightState();
    this.callbacks.onSelectionChanged({ kind: "none" });
  }

  selectedNodeIdOrEmpty(): string {
    return this.selectedNodeId;
  }

  selectedNode(): LayoutNode | null {
    if (!this.selectedNodeId) {
      return null;
    }
    return this.layout.nodes.get(this.selectedNodeId) || null;
  }

  selectedEdge(): LayoutEdge | null {
    if (!this.selectedEdgeId) {
      return null;
    }
    return this.layout.edges.find((edge) => edge.id === this.selectedEdgeId) || null;
  }

  selectedSelection(): TreeSelection {
    if (this.selectedNodeId) {
      return { kind: "node", nodeId: this.selectedNodeId };
    }
    if (this.selectedEdgeId) {
      return { kind: "edge", edgeId: this.selectedEdgeId };
    }
    return { kind: "none" };
  }

  focusVisible(): void {
    const nodes = [...this.layout.nodes.values()].filter((node) => this.visibleNodeIds.has(node.id));
    this.fitNodes(nodes);
  }

  focusAll(): void {
    this.fitNodes([...this.layout.nodes.values()]);
  }

  zoomIn(): void {
    this.svgSelection.call(this.zoomBehavior.scaleBy, 1.08);
  }

  zoomOut(): void {
    this.svgSelection.call(this.zoomBehavior.scaleBy, 0.92);
  }

  currentTransform(): ZoomTransform {
    return zoomTransform(this.elements.svgElement);
  }

  moveSelection(direction: "left" | "right" | "up" | "down"): void {
    const visibleNodes = [...this.layout.nodes.values()].filter((node) => this.visibleNodeIds.has(node.id));
    if (!visibleNodes.length) {
      return;
    }

    if (!this.selectedNodeId || !this.visibleNodeIds.has(this.selectedNodeId)) {
      const firstNode = [...visibleNodes].sort((left, right) => left.label.localeCompare(right.label))[0];
      if (firstNode) {
        this.selectNode(firstNode.id);
      }
      return;
    }

    const current = this.layout.nodes.get(this.selectedNodeId);
    if (!current) {
      return;
    }

    let best: LayoutNode | null = null;
    let bestScore = Number.POSITIVE_INFINITY;
    for (const node of visibleNodes) {
      if (node.id === current.id) {
        continue;
      }
      const dx = node.x - current.x;
      const dy = node.y - current.y;
      if (direction === "left" && dx >= 0) {
        continue;
      }
      if (direction === "right" && dx <= 0) {
        continue;
      }
      if (direction === "up" && dy >= 0) {
        continue;
      }
      if (direction === "down" && dy <= 0) {
        continue;
      }
      const major = direction === "left" || direction === "right" ? Math.abs(dx) : Math.abs(dy);
      const minor = direction === "left" || direction === "right" ? Math.abs(dy) : Math.abs(dx);
      const score = major * 2 + minor;
      if (score < bestScore) {
        bestScore = score;
        best = node;
      }
    }
    if (best) {
      this.selectNode(best.id);
    }
  }

  openSelectedSource(): void {
    if (this.selectedNodeId) {
      this.callbacks.onNodeOpened(this.selectedNodeId);
      return;
    }
    if (this.selectedEdgeId) {
      this.callbacks.onEdgeOpened(this.selectedEdgeId);
    }
  }

  resetLayout(): void {
    for (const [nodeId, point] of this.initialPositions.entries()) {
      const node = this.layout.nodes.get(nodeId);
      if (!node) {
        continue;
      }
      node.x = point.x;
      node.y = point.y;
    }
    this.hideHoverCard();
    this.scheduleGeometryUpdate();
    this.focusAll();
    this.callbacks.onStateChanged();
  }

  persistableState(extraState: {
    searchQuery: string;
    focusMode: "all" | "upstream" | "downstream";
    inspectorPinned: boolean;
  }): PersistedTreeUiState {
    const transform = this.currentTransform();
    return {
      selectedNodeId: this.selectedNodeId,
      searchQuery: extraState.searchQuery,
      focusMode: extraState.focusMode,
      inspectorPinned: extraState.inspectorPinned,
      zoomScale: transform.k,
      zoomX: transform.x,
      zoomY: transform.y,
    };
  }

  private renderGroups(): void {
    const groupLayer = this.elements.groupLayerElement;
    while (groupLayer.firstChild) {
      groupLayer.removeChild(groupLayer.firstChild);
    }
    for (const groupFrame of this.layout.groupFrames) {
      const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
      group.setAttribute("class", "framework-group-panel");
      group.setAttribute("data-framework-group", groupFrame.name);
      groupLayer.appendChild(group);

      const frame = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      frame.setAttribute("x", String(groupFrame.x));
      frame.setAttribute("y", String(groupFrame.y));
      frame.setAttribute("width", String(groupFrame.width));
      frame.setAttribute("height", String(groupFrame.height));
      frame.setAttribute("rx", "22");
      frame.setAttribute("ry", "22");
      frame.setAttribute("class", "framework-group-frame");
      group.appendChild(frame);

      const header = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      header.setAttribute("x", String(groupFrame.x));
      header.setAttribute("y", String(groupFrame.y));
      header.setAttribute("width", String(groupFrame.width));
      header.setAttribute("height", "54");
      header.setAttribute("rx", "22");
      header.setAttribute("ry", "22");
      header.setAttribute("class", "framework-group-header");
      group.appendChild(header);

      const title = document.createElementNS("http://www.w3.org/2000/svg", "text");
      title.setAttribute("x", String(groupFrame.x + 20));
      title.setAttribute("y", String(groupFrame.y + 34));
      title.setAttribute("class", "framework-group-title");
      title.textContent = groupFrame.name;
      group.appendChild(title);

      const subtitle = document.createElementNS("http://www.w3.org/2000/svg", "text");
      subtitle.setAttribute("x", String(groupFrame.x + groupFrame.width - 18));
      subtitle.setAttribute("y", String(groupFrame.y + 34));
      subtitle.setAttribute("text-anchor", "end");
      subtitle.setAttribute("class", "framework-group-meta");
      subtitle.textContent = `${groupFrame.localLevels.length} level${groupFrame.localLevels.length === 1 ? "" : "s"}`;
      group.appendChild(subtitle);
    }
  }

  private renderBands(): void {
    const bandLayer = this.elements.bandLayerElement;
    while (bandLayer.firstChild) {
      bandLayer.removeChild(bandLayer.firstChild);
    }
    for (const band of this.layout.bands) {
      const bandRect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      bandRect.setAttribute("x", String(band.x));
      bandRect.setAttribute("y", String(band.y));
      bandRect.setAttribute("width", String(band.width));
      bandRect.setAttribute("height", String(band.height));
      bandRect.setAttribute("rx", "16");
      bandRect.setAttribute("ry", "16");
      bandRect.setAttribute("class", `depth-band depth-${Math.max(0, band.depth % 6)}`);
      bandLayer.appendChild(bandRect);

      const bandLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
      bandLabel.setAttribute("x", String(band.x + 14));
      bandLabel.setAttribute("y", String(band.y + 22));
      bandLabel.setAttribute("class", "depth-label");
      bandLabel.textContent = band.label;
      bandLayer.appendChild(bandLabel);
    }
  }

  private renderEdges(): void {
    const edgeLayer = this.elements.edgeLayerElement;
    while (edgeLayer.firstChild) {
      edgeLayer.removeChild(edgeLayer.firstChild);
    }
    this.edgeElementById.clear();
    for (const edge of this.layout.edges) {
      const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
      group.setAttribute("class", "graph-edge-group");
      group.setAttribute("data-edge-id", edge.id);
      edgeLayer.appendChild(group);

      const visiblePath = document.createElementNS("http://www.w3.org/2000/svg", "path");
      visiblePath.setAttribute("class", "graph-edge");
      visiblePath.setAttribute("data-edge-id", edge.id);
      visiblePath.setAttribute("marker-end", `url(#${EDGE_ARROW_DEFAULT_MARKER_ID})`);
      group.appendChild(visiblePath);

      const hitPath = document.createElementNS("http://www.w3.org/2000/svg", "path");
      hitPath.setAttribute("class", "graph-edge-hit");
      hitPath.setAttribute("data-edge-id", edge.id);
      group.appendChild(hitPath);

      hitPath.addEventListener("click", (event) => {
        event.stopPropagation();
        this.selectEdge(edge.id);
      });
      hitPath.addEventListener("dblclick", (event) => {
        event.stopPropagation();
        this.selectEdge(edge.id);
        this.callbacks.onEdgeOpened(edge.id);
      });
      hitPath.addEventListener("mouseenter", () => {
        this.hoveredEdgeId = edge.id;
        this.refreshHighlightState();
      });
      hitPath.addEventListener("mouseleave", () => {
        this.hoveredEdgeId = "";
        this.refreshHighlightState();
      });

      this.edgeElementById.set(edge.id, { visiblePath, hitPath });
    }
  }

  private renderNodes(): void {
    const nodeLayer = this.elements.nodeLayerElement;
    while (nodeLayer.firstChild) {
      nodeLayer.removeChild(nodeLayer.firstChild);
    }
    this.nodeElementById.clear();

    const nodeSelection = select(nodeLayer)
      .selectAll<SVGGElement, LayoutNode>("g.graph-node")
      .data([...this.layout.nodes.values()], (d) => d.id)
      .join((enter) => {
        const group = enter.append("g")
          .attr("class", (d) => `graph-node ${kindClass(d.kind)}`)
          .attr("data-node-id", (d) => d.id)
          .on("click", (event, d) => {
            event.stopPropagation();
            this.selectNode(d.id);
            const mouseEvent = event as MouseEvent;
            if (mouseEvent.metaKey || mouseEvent.ctrlKey) {
              this.callbacks.onNodeOpened(d.id);
            }
          })
          .on("dblclick", (event, d) => {
            event.stopPropagation();
            this.selectNode(d.id);
            this.callbacks.onNodeOpened(d.id);
          })
          .on("mouseenter", (event, d) => {
            const target = event.currentTarget as SVGGElement | null;
            target?.classList.add("hovered");
            this.hoveredNodeId = d.id;
            this.refreshHighlightState();
            const mouseEvent = event as MouseEvent;
            this.showNodeHover(d, mouseEvent.clientX, mouseEvent.clientY);
          })
          .on("mousemove", (event, d) => {
            const mouseEvent = event as MouseEvent;
            this.showNodeHover(d, mouseEvent.clientX, mouseEvent.clientY);
          })
          .on("mouseleave", (event) => {
            const target = event.currentTarget as SVGGElement | null;
            target?.classList.remove("hovered");
            this.hoveredNodeId = "";
            this.refreshHighlightState();
            this.hideHoverCard();
          });

        group.append("circle")
          .attr("cx", 0)
          .attr("cy", 0)
          .attr("r", (d) => String(nodeRadius(d)))
          .attr("class", "node-circle");

        group.append("rect")
          .attr("class", "node-label-box")
          .attr("rx", 7)
          .attr("ry", 7);

        group.append("text")
          .attr("class", "node-label")
          .attr("x", 0)
          .attr("y", 26)
          .attr("text-anchor", "middle")
          .attr("dominant-baseline", "hanging")
          .text((d) => shortText(compactNodeId(d), 32));

        group.append("rect")
          .attr("class", "node-hit-area");

        return group;
      });

    nodeSelection.each((node, index, groups) => {
      const element = groups[index];
      if (element) {
        this.nodeElementById.set(node.id, element);
        const label = element.querySelector<SVGTextElement>("text.node-label");
        const labelBox = element.querySelector<SVGRectElement>("rect.node-label-box");
        const hitArea = element.querySelector<SVGRectElement>("rect.node-hit-area");
        if (label && labelBox && hitArea) {
          const labelBounds = label.getBBox();
          const padX = 5;
          const padY = 1;
          labelBox.setAttribute("x", String(labelBounds.x - padX));
          labelBox.setAttribute("y", String(labelBounds.y - padY));
          labelBox.setAttribute("width", String(Math.max(10, labelBounds.width + padX * 2)));
          labelBox.setAttribute("height", String(Math.max(10, labelBounds.height + padY * 2)));

          const radius = nodeRadius(node);
          const hitPadding = 10;
          const minX = Math.min(-radius - hitPadding, labelBounds.x - padX - hitPadding);
          const maxX = Math.max(radius + hitPadding, labelBounds.x + labelBounds.width + padX + hitPadding);
          const minY = Math.min(-radius - hitPadding, labelBounds.y - padY - hitPadding);
          const maxY = Math.max(radius + hitPadding, labelBounds.y + labelBounds.height + padY + hitPadding);
          hitArea.setAttribute("x", String(minX));
          hitArea.setAttribute("y", String(minY));
          hitArea.setAttribute("width", String(Math.max(1, maxX - minX)));
          hitArea.setAttribute("height", String(Math.max(1, maxY - minY)));
          hitArea.setAttribute("rx", "14");
          hitArea.setAttribute("ry", "14");
        }
      }
    });

    select(this.elements.svgElement).on("click.canvas", () => {
      this.clearSelection();
    });

    this.scheduleGeometryUpdate();
  }

  private scheduleGeometryUpdate(): void {
    if (this.geometryFrame !== null) {
      return;
    }
    this.geometryFrame = window.requestAnimationFrame(() => {
      this.geometryFrame = null;
      this.updateGeometry();
    });
  }

  private updateGeometry(): void {
    for (const edge of this.layout.edges) {
      const fromNode = this.layout.nodes.get(edge.from);
      const toNode = this.layout.nodes.get(edge.to);
      const refs = this.edgeElementById.get(edge.id);
      if (!fromNode || !toNode || !refs) {
        continue;
      }
      edge.fromX = fromNode.x;
      edge.fromY = fromNode.y;
      edge.toX = toNode.x;
      edge.toY = toNode.y;
      const path = edgePath(fromNode, toNode);
      refs.visiblePath.setAttribute("d", path);
      refs.hitPath.setAttribute("d", path);
    }

    for (const [nodeId, element] of this.nodeElementById.entries()) {
      const node = this.layout.nodes.get(nodeId);
      if (!node) {
        continue;
      }
      element.setAttribute("transform", `translate(${node.x} ${node.y})`);
    }

    this.refreshHighlightState();
  }

  private refreshHighlightState(): void {
    const selectedNodes = new Set<string>();
    const neighborNodes = new Set<string>();
    const activeEdges = new Set<string>();
    const fadedNodes = new Set<string>();
    const fadedEdges = new Set<string>();

    if (this.selectedEdgeId) {
      const edge = this.model.edge(this.selectedEdgeId);
      if (edge) {
        selectedNodes.add(edge.from);
        selectedNodes.add(edge.to);
        activeEdges.add(edge.id);
        for (const node of this.layout.nodes.keys()) {
          if (!selectedNodes.has(node)) {
            fadedNodes.add(node);
          }
        }
        for (const layoutEdge of this.layout.edges) {
          if (layoutEdge.id !== edge.id) {
            fadedEdges.add(layoutEdge.id);
          }
        }
      }
    } else if (this.selectedNodeId) {
      selectedNodes.add(this.selectedNodeId);
      for (const adjacent of this.model.adjacentNodeIds(this.selectedNodeId)) {
        neighborNodes.add(adjacent);
      }
      for (const edge of this.layout.edges) {
        if (edge.from === this.selectedNodeId || edge.to === this.selectedNodeId) {
          activeEdges.add(edge.id);
        } else {
          fadedEdges.add(edge.id);
        }
      }
      for (const nodeId of this.layout.nodes.keys()) {
        if (nodeId !== this.selectedNodeId && !neighborNodes.has(nodeId)) {
          fadedNodes.add(nodeId);
        }
      }
    }

    if (!this.selectedEdgeId && !this.selectedNodeId) {
      if (this.hoveredNodeId) {
        selectedNodes.add(this.hoveredNodeId);
        for (const adjacent of this.model.adjacentNodeIds(this.hoveredNodeId)) {
          neighborNodes.add(adjacent);
        }
        for (const edge of this.layout.edges) {
          if (edge.from === this.hoveredNodeId || edge.to === this.hoveredNodeId) {
            activeEdges.add(edge.id);
          }
        }
      } else if (this.hoveredEdgeId) {
        const hoveredEdge = this.model.edge(this.hoveredEdgeId);
        if (hoveredEdge) {
          selectedNodes.add(hoveredEdge.from);
          selectedNodes.add(hoveredEdge.to);
          activeEdges.add(hoveredEdge.id);
        }
      }
    }

    for (const [nodeId, element] of this.nodeElementById.entries()) {
      const selected = this.selectedNodeId === nodeId
        || Boolean(this.selectedEdgeId && selectedNodes.has(nodeId));
      const neighbor = neighborNodes.has(nodeId) && !selected;
      const faded = fadedNodes.has(nodeId);
      element.classList.toggle("selected", selected);
      element.classList.toggle("neighbor", neighbor);
      element.classList.toggle("faded", faded);
    }

    for (const [edgeId, refs] of this.edgeElementById.entries()) {
      const active = activeEdges.has(edgeId);
      const faded = fadedEdges.has(edgeId);
      refs.visiblePath.classList.toggle("active", active);
      refs.visiblePath.classList.toggle("faded", faded);
      refs.hitPath.classList.toggle("active", active);
    }
  }

  private applyPersistedState(rawState: PersistedTreeUiState | null): void {
    const state = sanitizeState(rawState, this.viewSettings);
    const hasCustomViewport = Math.abs(state.zoomScale - 1) > 0.001
      || Math.abs(state.zoomX) > 0.01
      || Math.abs(state.zoomY) > 0.01;
    if (hasCustomViewport) {
      const transform = zoomIdentity.translate(state.zoomX, state.zoomY).scale(state.zoomScale);
      this.svgSelection.call(this.zoomBehavior.transform, transform);
    } else {
      this.focusAll();
    }
    if (state.selectedNodeId && this.model.hasNode(state.selectedNodeId)) {
      this.selectNode(state.selectedNodeId);
    } else {
      this.clearSelection();
    }
  }

  private fitNodes(nodes: LayoutNode[]): void {
    const bounds = computeNodeBounds(nodes);
    if (!bounds) {
      return;
    }
    const container = this.elements.scrollElement.getBoundingClientRect();
    const containerWidth = Math.max(320, container.width || 1280);
    const containerHeight = Math.max(260, container.height || 760);
    const pad = 36;
    const contentWidth = Math.max(1, bounds.maxX - bounds.minX);
    const contentHeight = Math.max(1, bounds.maxY - bounds.minY);
    const scaleX = (containerWidth - pad * 2) / contentWidth;
    const scaleY = (containerHeight - pad * 2) / contentHeight;
    const scale = Math.max(
      this.viewSettings.zoomMinScale,
      Math.min(this.viewSettings.zoomMaxScale, Math.min(scaleX, scaleY))
    );
    const tx = (containerWidth - contentWidth * scale) / 2 - bounds.minX * scale;
    const ty = (containerHeight - contentHeight * scale) / 2 - bounds.minY * scale;
    const transform = zoomIdentity.translate(tx, ty).scale(scale);
    this.svgSelection.call(this.zoomBehavior.transform, transform);
    this.callbacks.onStateChanged();
  }

  private renderHoverContent(node: LayoutNode): string {
    const kicker = escapeHtml(node.hoverKicker || "Hierarchy Node");
    const title = escapeHtml(node.title || node.label || node.id);
    const subtitle = escapeHtml(
      [node.moduleName || "", node.moduleRef || ""].filter(Boolean).join(" · ") || node.label
    );
    const footer = escapeHtml(
      node.file
        ? `${node.file}:${node.docLine || node.line} · Ctrl/⌘ + 点击跳转到文档`
        : "Ctrl/⌘ + 点击跳转到文档"
    );
    return `
      <p class="hover-kicker">${kicker}</p>
      <h3 class="hover-title">${title}</h3>
      <p class="hover-subtitle">${subtitle}</p>
      <div class="hover-grid">
        <section class="hover-section">
          <h4 class="hover-section-title">能力声明</h4>
          <ul class="hover-list">${hoverList(node.capabilityItems || [], "无能力声明", 2)}</ul>
        </section>
        <section class="hover-section">
          <h4 class="hover-section-title">最小结构基</h4>
          <ul class="hover-list">${hoverList(node.baseItems || [], "无最小结构基", 2)}</ul>
        </section>
      </div>
      <div class="hover-footer">${footer}</div>
    `;
  }

  private positionHoverCard(clientX: number, clientY: number): void {
    const card = this.elements.hoverCardElement;
    const margin = 18;
    const rect = card.getBoundingClientRect();
    let left = clientX + margin;
    let top = clientY + margin;
    if (left + rect.width > window.innerWidth - 12) {
      left = clientX - rect.width - margin;
    }
    if (top + rect.height > window.innerHeight - 12) {
      top = clientY - rect.height - margin;
    }
    card.style.left = `${Math.max(12, left)}px`;
    card.style.top = `${Math.max(12, top)}px`;
  }

  private showNodeHover(node: LayoutNode, clientX: number, clientY: number): void {
    if (!this.elements.hoverCardElement || this.currentTransform().k <= 0) {
      return;
    }
    this.elements.hoverCardElement.innerHTML = this.renderHoverContent(node);
    this.elements.hoverCardElement.classList.add("visible");
    this.elements.hoverCardElement.setAttribute("aria-hidden", "false");
    this.positionHoverCard(clientX, clientY);
  }

  private hideHoverCard(): void {
    this.elements.hoverCardElement.classList.remove("visible");
    this.elements.hoverCardElement.setAttribute("aria-hidden", "true");
  }

  private ensureEdgeMarker(): void {
    const svg = this.elements.svgElement;
    let defs = svg.querySelector("defs#tree-edge-defs");
    if (!defs) {
      defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
      defs.setAttribute("id", "tree-edge-defs");
      svg.insertBefore(defs, svg.firstChild);
    }
    if (
      defs.querySelector(`marker#${EDGE_ARROW_DEFAULT_MARKER_ID}`)
      && defs.querySelector(`marker#${EDGE_ARROW_ACTIVE_MARKER_ID}`)
    ) {
      return;
    }

    const buildMarker = (id: string, shapeClass: string): SVGMarkerElement => {
      const marker = document.createElementNS("http://www.w3.org/2000/svg", "marker");
      marker.setAttribute("id", id);
      marker.setAttribute("viewBox", "0 0 12 9");
      marker.setAttribute("refX", "10.5");
      marker.setAttribute("refY", "4.5");
      marker.setAttribute("markerWidth", "12");
      marker.setAttribute("markerHeight", "12");
      marker.setAttribute("orient", "auto");
      marker.setAttribute("markerUnits", "userSpaceOnUse");

      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", "M0,0 L0,9 L12,4.5 z");
      path.setAttribute("class", shapeClass);
      marker.appendChild(path);
      return marker;
    };

    if (!defs.querySelector(`marker#${EDGE_ARROW_DEFAULT_MARKER_ID}`)) {
      defs.appendChild(buildMarker(EDGE_ARROW_DEFAULT_MARKER_ID, "graph-edge-arrow-default"));
    }
    if (!defs.querySelector(`marker#${EDGE_ARROW_ACTIVE_MARKER_ID}`)) {
      defs.appendChild(buildMarker(EDGE_ARROW_ACTIVE_MARKER_ID, "graph-edge-arrow-active"));
    }
  }
}
