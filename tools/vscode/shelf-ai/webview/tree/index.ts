import { WebviewBridge, readRuntimeBootstrap } from "./bridge";
import { computeTreeLayout } from "./layout";
import { TreeGraphModel } from "./model";
import { TreeCanvasRenderer, type CanvasElements } from "./render";
import type { FocusMode, TreeSelection } from "./types";

function requiredElementById<T extends Element>(elementId: string, ctor: { new(...args: never[]): T }): T {
  const element = document.getElementById(elementId);
  if (!(element instanceof ctor)) {
    throw new Error(`Missing required element #${elementId}`);
  }
  return element;
}

function normalizeFocusMode(value: string): FocusMode {
  if (value === "upstream" || value === "downstream") {
    return value;
  }
  return "all";
}

function escapeHtml(value: string): string {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function detailList(items: string[]): string {
  if (!items.length) {
    return '<li class="detail-item">无</li>';
  }
  return items.map((item) => `<li class="detail-item">${escapeHtml(item)}</li>`).join("");
}

function main(): void {
  const bootstrap = readRuntimeBootstrap();
  const bridge = new WebviewBridge();
  const persistedState = bridge.readPersistedState();
  const model = new TreeGraphModel(bootstrap.model);
  const layout = computeTreeLayout(model, bootstrap.layoutSettings);
  document.documentElement.style.setProperty("--inspector-width-px", `${bootstrap.viewSettings.inspectorWidth}px`);
  document.documentElement.style.setProperty("--inspector-rail-width-px", `${bootstrap.viewSettings.inspectorRailWidth}px`);

  const elements: CanvasElements = {
    scrollElement: requiredElementById("treeCanvasScroll", HTMLElement),
    svgElement: requiredElementById("treeCanvas", SVGSVGElement),
    viewportElement: requiredElementById("treeViewport", SVGGElement),
    groupLayerElement: requiredElementById("treeGroupLayer", SVGGElement),
    bandLayerElement: requiredElementById("treeBandLayer", SVGGElement),
    edgeLayerElement: requiredElementById("treeEdgeLayer", SVGGElement),
    nodeLayerElement: requiredElementById("treeNodeLayer", SVGGElement),
    hoverCardElement: requiredElementById("treeHoverCard", HTMLElement),
    statusElement: requiredElementById("treeStatusText", HTMLElement),
    zoomChipElement: requiredElementById("treeZoomChip", HTMLElement),
    countChipElement: requiredElementById("treeCountChip", HTMLElement),
    visibleChipElement: requiredElementById("treeVisibleChip", HTMLElement),
  };

  const searchInput = requiredElementById("treeSearchInput", HTMLInputElement);
  const focusSelect = requiredElementById("treeFocusSelect", HTMLSelectElement);
  const clearFilterButton = requiredElementById("treeClearFilterBtn", HTMLButtonElement);
  const fitButton = requiredElementById("treeFitBtn", HTMLButtonElement);
  const resetButton = requiredElementById("treeResetBtn", HTMLButtonElement);
  const zoomInButton = requiredElementById("treeZoomInBtn", HTMLButtonElement);
  const zoomOutButton = requiredElementById("treeZoomOutBtn", HTMLButtonElement);
  const inspectorShell = requiredElementById("treeInspector", HTMLElement);
  const inspectorRail = requiredElementById("treeInspectorRail", HTMLElement);
  const inspectorRailValue = requiredElementById("inspectorRailValue", HTMLElement);
  const inspectorSummaryValue = requiredElementById("inspectorSummaryValue", HTMLElement);
  const selectionKindPill = requiredElementById("selectionKindPill", HTMLElement);
  const pinInspectorButton = requiredElementById("pinInspectorBtn", HTMLButtonElement);
  const inspectorDetailBox = requiredElementById("inspectorDetailBox", HTMLElement);

  if (persistedState) {
    searchInput.value = persistedState.searchQuery;
    focusSelect.value = persistedState.focusMode;
  }

  let inspectorPinned = Boolean(persistedState?.inspectorPinned);
  const setInspectorExpandedState = (expanded: boolean): void => {
    inspectorRail.setAttribute("aria-expanded", String(expanded || inspectorPinned));
  };
  let isApplyingFilters = false;

  let persistTimer: number | null = null;
  const schedulePersist = (): void => {
    if (persistTimer !== null) {
      window.clearTimeout(persistTimer);
    }
    persistTimer = window.setTimeout(() => {
      persistTimer = null;
      bridge.persistState(renderer.persistableState({
        searchQuery: searchInput.value,
        focusMode: normalizeFocusMode(focusSelect.value),
        inspectorPinned,
      }));
    }, 120);
  };

  const applyInspectorPinnedState = (nextPinned: boolean, options?: { persist?: boolean }): void => {
    inspectorPinned = nextPinned;
    inspectorShell.dataset.pinned = String(nextPinned);
    setInspectorExpandedState(nextPinned);
    pinInspectorButton.textContent = nextPinned ? "Unpin" : "Pin";
    pinInspectorButton.setAttribute("aria-pressed", String(nextPinned));
    if (options?.persist !== false) {
      schedulePersist();
    }
  };

  const attachDetailActions = (): void => {
    inspectorDetailBox.querySelectorAll<HTMLElement>("[data-open-source='1']").forEach((element) => {
      element.addEventListener("click", (event) => {
        event.stopPropagation();
        const filePath = element.getAttribute("data-file") || "";
        const lineNumber = Number(element.getAttribute("data-line") || "1");
        if (filePath) {
          bridge.openSource(filePath, lineNumber);
        }
      });
    });
  };

  const renderEmptyDetail = (): void => {
    selectionKindPill.textContent = "none";
    selectionKindPill.className = "pill kind-pill";
    inspectorRailValue.textContent = "No selection";
    inspectorRailValue.title = "No selection";
    inspectorSummaryValue.textContent = "Click a node or edge to inspect details.";
    inspectorDetailBox.innerHTML = `
      <p class="detail-empty">
        Click a node or edge to inspect details. Search, focus mode, hover, and source jumps stay available while the canvas remains primary.
      </p>
    `;
  };

  const renderNodeDetail = (nodeId: string): void => {
    const node = layout.nodes.get(nodeId);
    if (!node) {
      renderEmptyDetail();
      return;
    }
    const upstream = model.incomingEdges(nodeId).map((edge) => {
      const peer = model.node(edge.from);
      return `${peer?.label || edge.from} · ${edge.relation}`;
    });
    const downstream = model.outgoingEdges(nodeId).map((edge) => {
      const peer = model.node(edge.to);
      return `${peer?.label || edge.to} · ${edge.relation}`;
    });
    const sourceFile = node.file;
    const docLine = node.docLine || node.line;
    const sourceLine = node.sourceLine || node.line;
    const levelLabel = node.moduleName
      ? `${node.moduleName} · ${model.levelLabel(node.depth)}`
      : model.levelLabel(node.depth);

    selectionKindPill.textContent = node.kind;
    selectionKindPill.className = `pill kind-pill ${node.kind.replace(/[^a-zA-Z0-9_-]/g, "-")}`;
    inspectorRailValue.textContent = node.title || node.label;
    inspectorRailValue.title = node.title || node.label;
    inspectorSummaryValue.textContent = node.moduleRef
      ? `${node.moduleName || ""} · ${node.moduleRef}`.replace(/^\s*·\s*/, "")
      : node.label;
    inspectorDetailBox.innerHTML = `
      <section class="detail-group">
        <h3 class="detail-section-title">节点概览</h3>
        <div class="detail-kv"><span class="detail-key">ID</span><span class="detail-value mono">${escapeHtml(node.id)}</span></div>
        <div class="detail-kv"><span class="detail-key">标题</span><span class="detail-value">${escapeHtml(node.title || node.label)}</span></div>
        <div class="detail-kv"><span class="detail-key">层级</span><span class="detail-value">${escapeHtml(levelLabel)}</span></div>
        <div class="detail-kv"><span class="detail-key">标签</span><span class="detail-value">${escapeHtml(node.label)}</span></div>
        <div class="detail-kv"><span class="detail-key">描述</span><span class="detail-value">${escapeHtml(node.detail || "无")}</span></div>
      </section>
      <section class="detail-group">
        <h3 class="detail-section-title">来源与跳转</h3>
        <div class="detail-kv"><span class="detail-key">文档位置</span><span class="detail-value mono">${sourceFile ? `${escapeHtml(sourceFile)}:${docLine}` : "无"}</span></div>
        <div class="detail-kv"><span class="detail-key">结构来源</span><span class="detail-value mono">${sourceFile ? `${escapeHtml(sourceFile)}:${sourceLine}` : "无"}</span></div>
        <div class="action-row">
          ${sourceFile ? `<button type="button" class="detail-action" data-open-source="1" data-file="${escapeHtml(sourceFile)}" data-line="${docLine}">打开文档</button>` : "无"}
        </div>
      </section>
      <section class="detail-group">
        <h3 class="detail-section-title">上游节点</h3>
        <ul class="detail-list">${detailList(upstream)}</ul>
      </section>
      <section class="detail-group">
        <h3 class="detail-section-title">下游节点</h3>
        <ul class="detail-list">${detailList(downstream)}</ul>
      </section>
    `;
    attachDetailActions();
  };

  const renderEdgeDetail = (edgeId: string): void => {
    const edge = model.edge(edgeId);
    if (!edge) {
      renderEmptyDetail();
      return;
    }
    const fromNode = model.node(edge.from);
    const toNode = model.node(edge.to);
    const sourceFile = edge.file || "";
    const sourceLine = edge.line || 1;

    selectionKindPill.textContent = "edge";
    selectionKindPill.className = "pill kind-pill edge-selection";
    inspectorRailValue.textContent = edge.relation;
    inspectorRailValue.title = edge.relation;
    inspectorSummaryValue.textContent = `${fromNode?.label || edge.from} -> ${toNode?.label || edge.to}`;
    inspectorDetailBox.innerHTML = `
      <section class="detail-group">
        <h3 class="detail-section-title">关系概览</h3>
        <div class="detail-kv"><span class="detail-key">起点</span><span class="detail-value">${escapeHtml(fromNode?.label || edge.from)}</span></div>
        <div class="detail-kv"><span class="detail-key">终点</span><span class="detail-value">${escapeHtml(toNode?.label || edge.to)}</span></div>
        <div class="detail-kv"><span class="detail-key">关系</span><span class="detail-value mono">${escapeHtml(edge.relation)}</span></div>
      </section>
      <section class="detail-group">
        <h3 class="detail-section-title">规则与术语</h3>
        <div class="detail-kv"><span class="detail-key">规则</span><span class="detail-value mono">${escapeHtml(edge.rules || "无")}</span></div>
        <div class="detail-kv"><span class="detail-key">术语</span><span class="detail-value mono">${escapeHtml(edge.terms || "无")}</span></div>
      </section>
      <section class="detail-group">
        <h3 class="detail-section-title">来源与跳转</h3>
        <div class="detail-kv"><span class="detail-key">结构来源</span><span class="detail-value mono">${sourceFile ? `${escapeHtml(sourceFile)}:${sourceLine}` : "无"}</span></div>
        <div class="action-row">
          ${sourceFile ? `<button type="button" class="detail-action" data-open-source="1" data-file="${escapeHtml(sourceFile)}" data-line="${sourceLine}">打开来源</button>` : "无"}
        </div>
      </section>
    `;
    attachDetailActions();
  };

  const updateInspector = (selection: TreeSelection): void => {
    if (selection.kind === "node") {
      renderNodeDetail(selection.nodeId);
      return;
    }
    if (selection.kind === "edge") {
      renderEdgeDetail(selection.edgeId);
      return;
    }
    renderEmptyDetail();
  };

  const renderer = new TreeCanvasRenderer(elements, model, layout, bootstrap.viewSettings, {
    onSelectionChanged: (selection) => {
      if (!isApplyingFilters && selection.kind === "node" && normalizeFocusMode(focusSelect.value) !== "all") {
        applyFilters();
        return;
      }
      updateInspector(selection);
    },
    onNodeOpened: (nodeId) => {
      const node = layout.nodes.get(nodeId);
      if (node?.file) {
        bridge.openSource(node.file, node.docLine || node.line);
      }
    },
    onEdgeOpened: (edgeId) => {
      const edge = model.edge(edgeId);
      if (edge?.file) {
        bridge.openSource(edge.file, edge.line || 1);
      }
    },
    onStateChanged: () => {
      schedulePersist();
    },
  });

  const applyFilters = (): void => {
    isApplyingFilters = true;
    try {
      const filter = model.computeFilterResult({
        query: searchInput.value,
        focusMode: normalizeFocusMode(focusSelect.value),
        selectedNodeId: renderer.selectedNodeIdOrEmpty(),
      });
      renderer.applyFilter(filter);
      const selectedNodeId = renderer.selectedNodeIdOrEmpty();
      elements.statusElement.textContent = selectedNodeId ? `Selected ${selectedNodeId}` : "Ready";
      schedulePersist();
    } finally {
      isApplyingFilters = false;
    }
  };

  renderer.mount(persistedState);
  applyInspectorPinnedState(inspectorPinned, { persist: false });

  if (persistedState?.selectedNodeId) {
    renderer.selectNode(persistedState.selectedNodeId);
  } else {
    updateInspector({ kind: "none" });
  }

  searchInput.addEventListener("input", () => {
    applyFilters();
  });
  focusSelect.addEventListener("change", () => {
    applyFilters();
  });
  clearFilterButton.addEventListener("click", () => {
    searchInput.value = "";
    focusSelect.value = "all";
    renderer.clearSelection();
    applyFilters();
    renderer.focusAll();
  });
  fitButton.addEventListener("click", () => {
    renderer.focusVisible();
    schedulePersist();
  });
  resetButton.addEventListener("click", () => {
    renderer.resetLayout();
    applyFilters();
  });
  zoomInButton.addEventListener("click", () => {
    renderer.zoomIn();
    schedulePersist();
  });
  zoomOutButton.addEventListener("click", () => {
    renderer.zoomOut();
    schedulePersist();
  });
  inspectorRail.addEventListener("click", () => {
    applyInspectorPinnedState(!inspectorPinned);
  });
  inspectorShell.addEventListener("mouseenter", () => {
    setInspectorExpandedState(true);
  });
  inspectorShell.addEventListener("mouseleave", () => {
    if (!inspectorPinned) {
      setInspectorExpandedState(false);
    }
  });
  inspectorShell.addEventListener("focusin", () => {
    setInspectorExpandedState(true);
  });
  inspectorShell.addEventListener("focusout", () => {
    window.setTimeout(() => {
      if (!inspectorPinned && !inspectorShell.contains(document.activeElement)) {
        setInspectorExpandedState(false);
      }
    }, 0);
  });
  inspectorRail.addEventListener("keydown", (event) => {
    if (!(event instanceof KeyboardEvent)) {
      return;
    }
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      applyInspectorPinnedState(!inspectorPinned);
    }
  });
  pinInspectorButton.addEventListener("click", () => {
    applyInspectorPinnedState(!inspectorPinned);
  });

  elements.scrollElement.addEventListener("keydown", (event) => {
    if (!(event instanceof KeyboardEvent)) {
      return;
    }
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      renderer.moveSelection("left");
      applyFilters();
      return;
    }
    if (event.key === "ArrowRight") {
      event.preventDefault();
      renderer.moveSelection("right");
      applyFilters();
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      renderer.moveSelection("up");
      applyFilters();
      return;
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      renderer.moveSelection("down");
      applyFilters();
      return;
    }
    if (event.key === "Enter") {
      event.preventDefault();
      renderer.openSelectedSource();
      return;
    }
    if (event.key === "/") {
      event.preventDefault();
      searchInput.focus();
      searchInput.select();
    }
  });

  applyFilters();
}

main();
