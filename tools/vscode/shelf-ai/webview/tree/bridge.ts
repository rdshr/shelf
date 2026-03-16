import type {
  PersistedTreeUiState,
  RuntimeTreeBootstrap,
  RuntimeTreeLayoutSettings,
  RuntimeTreeViewSettings,
} from "./types";

interface VsCodeApiLike {
  postMessage: (message: unknown) => void;
  setState: (newState: unknown) => void;
  getState: () => unknown;
}

interface WindowWithAcquire extends Window {
  acquireVsCodeApi?: () => VsCodeApiLike;
}

function asWindowWithAcquire(value: Window): WindowWithAcquire {
  return value as WindowWithAcquire;
}

function normalizePersistedState(candidate: unknown): PersistedTreeUiState | null {
  if (!candidate || typeof candidate !== "object") {
    return null;
  }
  const raw = candidate as Partial<PersistedTreeUiState>;
  return {
    selectedNodeId: String(raw.selectedNodeId || ""),
    focusMode: raw.focusMode === "upstream" || raw.focusMode === "downstream" ? raw.focusMode : "all",
    searchQuery: String(raw.searchQuery || ""),
    inspectorPinned: raw.inspectorPinned === true,
    zoomScale: Number.isFinite(Number(raw.zoomScale)) ? Math.max(0.2, Number(raw.zoomScale)) : 1,
    zoomX: Number.isFinite(Number(raw.zoomX)) ? Number(raw.zoomX) : 0,
    zoomY: Number.isFinite(Number(raw.zoomY)) ? Number(raw.zoomY) : 0,
  };
}

function clampInt(value: unknown, minimum: number, maximum: number, fallback: number): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    return fallback;
  }
  return Math.min(maximum, Math.max(minimum, Math.round(parsed)));
}

function normalizeLayoutSettings(candidate: unknown): RuntimeTreeLayoutSettings {
  const raw = candidate && typeof candidate === "object"
    ? candidate as Partial<RuntimeTreeLayoutSettings>
    : {};
  return {
    frameworkNodeHorizontalGap: clampInt(raw.frameworkNodeHorizontalGap, 0, 40, 8),
    frameworkLevelVerticalGap: clampInt(raw.frameworkLevelVerticalGap, 48, 180, 80),
  };
}

function clampNumber(value: unknown, minimum: number, maximum: number, fallback: number): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    return fallback;
  }
  return Math.min(maximum, Math.max(minimum, parsed));
}

function normalizeViewSettings(candidate: unknown): RuntimeTreeViewSettings {
  const raw = candidate && typeof candidate === "object"
    ? candidate as Partial<RuntimeTreeViewSettings>
    : {};
  const zoomMinScale = clampNumber(raw.zoomMinScale, 0.2, 3, 0.68);
  const zoomMaxScale = clampNumber(raw.zoomMaxScale, zoomMinScale, 5, 1.55);
  return {
    zoomMinScale,
    zoomMaxScale,
    wheelSensitivity: clampNumber(raw.wheelSensitivity, 0.25, 3, 1),
    inspectorWidth: clampInt(raw.inspectorWidth, 240, 520, 338),
    inspectorRailWidth: clampInt(raw.inspectorRailWidth, 32, 72, 42),
  };
}

export class WebviewBridge {
  private readonly vscodeApi: VsCodeApiLike | null;

  constructor(hostWindow: Window = window) {
    const host = asWindowWithAcquire(hostWindow);
    this.vscodeApi = typeof host.acquireVsCodeApi === "function"
      ? host.acquireVsCodeApi()
      : null;
  }

  readPersistedState(): PersistedTreeUiState | null {
    if (!this.vscodeApi) {
      return null;
    }
    return normalizePersistedState(this.vscodeApi.getState());
  }

  persistState(state: PersistedTreeUiState): void {
    if (!this.vscodeApi) {
      return;
    }
    this.vscodeApi.setState(state);
  }

  openSource(file: string, line: number): void {
    if (!this.vscodeApi) {
      return;
    }
    this.vscodeApi.postMessage({
      type: "shelf.openSource",
      file,
      line: Math.max(1, Math.floor(Number(line || 1))),
    });
  }
}

function readBootstrapElement(): HTMLScriptElement {
  const element = document.getElementById("shelf-tree-bootstrap");
  if (!(element instanceof HTMLScriptElement)) {
    throw new Error("Missing #shelf-tree-bootstrap payload.");
  }
  return element;
}

export function readRuntimeBootstrap(): RuntimeTreeBootstrap {
  const element = readBootstrapElement();
  const raw = JSON.parse(element.textContent || "{}") as Partial<RuntimeTreeBootstrap>;
  const model = raw.model;
  if (!model || typeof model !== "object") {
    throw new Error("Invalid bootstrap payload: missing model.");
  }
  const kind = raw.kind === "evidence" ? "evidence" : "framework";
  return {
    version: Number(raw.version || 1),
    kind,
    layoutSettings: normalizeLayoutSettings(raw.layoutSettings),
    viewSettings: normalizeViewSettings(raw.viewSettings),
    model: {
      title: String(model.title || ""),
      description: String(model.description || ""),
      kind,
      nodes: Array.isArray(model.nodes) ? model.nodes : [],
      edges: Array.isArray(model.edges) ? model.edges : [],
      footText: typeof model.footText === "string" ? model.footText : "",
      layoutMode: model.layoutMode === "framework_columns" ? "framework_columns" : "global_levels",
      levelLabels: model.levelLabels && typeof model.levelLabels === "object"
        ? model.levelLabels
        : {},
      frameworkGroups: Array.isArray(model.frameworkGroups) ? model.frameworkGroups : [],
      relationCounts: model.relationCounts && typeof model.relationCounts === "object"
        ? model.relationCounts
        : {},
    },
  };
}
