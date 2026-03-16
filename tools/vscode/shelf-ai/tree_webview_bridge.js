/**
 * @typedef {import("./tree_runtime_models").RuntimeTreeModel} RuntimeTreeModel
 */

/**
 * @typedef {"framework"|"evidence"} TreeKind
 */

/**
 * @typedef {Object} RuntimeTreeHtmlParams
 * @property {TreeKind} kind
 * @property {RuntimeTreeModel} model
 * @property {{ frameworkNodeHorizontalGap: number, frameworkLevelVerticalGap: number }} layoutSettings
 * @property {{ zoomMinScale: number, zoomMaxScale: number, wheelSensitivity: number, inspectorWidth: number, inspectorRailWidth: number }} viewSettings
 * @property {string} scriptUri
 * @property {string} styleUri
 * @property {string} cspSource
 */

/**
 * @param {TreeKind} kind
 * @returns {string}
 */
function treeTitleForKind(kind) {
  return kind === "evidence"
    ? "Shelf · Evidence Tree"
    : "Shelf · Framework Tree";
}

/**
 * @param {TreeKind} kind
 * @returns {string}
 */
function treeRefreshCommandForKind(kind) {
  return kind === "evidence"
    ? "Shelf: Refresh Evidence Tree"
    : "Shelf: Refresh Framework Tree";
}

/**
 * @returns {string}
 */
function createNonce() {
  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let value = "";
  for (let index = 0; index < 32; index += 1) {
    value += alphabet[Math.floor(Math.random() * alphabet.length)];
  }
  return value;
}

/**
 * @param {unknown} value
 * @returns {string}
 */
function safeJsonForScript(value) {
  return JSON.stringify(value)
    .replaceAll("<", "\\u003c")
    .replaceAll(">", "\\u003e")
    .replaceAll("&", "\\u0026")
    .replaceAll("\u2028", "\\u2028")
    .replaceAll("\u2029", "\\u2029");
}

/**
 * @param {string} value
 * @returns {string}
 */
function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

/**
 * @param {RuntimeTreeHtmlParams} params
 * @returns {string}
 */
function buildRuntimeTreeHtml(params) {
  const kind = params.kind;
  const title = escapeHtml(params.model?.title || treeTitleForKind(kind));
  const pageTitle = escapeHtml(treeTitleForKind(kind));
  const description = escapeHtml(params.model?.description || "");
  const refreshCommand = escapeHtml(treeRefreshCommandForKind(kind));
  const scriptUri = escapeHtml(params.scriptUri);
  const styleUri = escapeHtml(params.styleUri);
  const cspSource = escapeHtml(params.cspSource);
  const nonce = createNonce();
  const payload = {
    version: 1,
    kind,
    model: params.model,
    layoutSettings: params.layoutSettings,
    viewSettings: params.viewSettings,
  };

  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta
    http-equiv="Content-Security-Policy"
    content="default-src 'none'; img-src data: https:; style-src 'unsafe-inline' ${cspSource}; script-src 'nonce-${nonce}';"
  />
  <title>${pageTitle}</title>
  <link rel="stylesheet" href="${styleUri}" />
</head>
<body>
  <div class="layout">
    <section class="card graph-card">
      <header class="head">
        <h1 id="treeTitle">${title}</h1>
        <p id="treeDescription" class="desc">${description}</p>
      </header>

      <div class="legend">
        <span class="pill"><strong>Refresh</strong> <code>${refreshCommand}</code></span>
        <span class="pill" id="treeCountChip">Nodes 0 / Edges 0</span>
        <span class="pill" id="treeVisibleChip">Visible 0</span>
      </div>

      <div class="graph-shell">
        <div class="graph-toolbar">
          <div class="toolbar-row">
            <input
              id="treeSearchInput"
              class="field search"
              type="search"
              placeholder="Search node id / label / detail"
              aria-label="Search nodes"
            />
            <select id="treeFocusSelect" class="field select" aria-label="Focus mode">
              <option value="all">All Nodes</option>
              <option value="upstream">Upstream Only</option>
              <option value="downstream">Downstream Only</option>
            </select>
            <button id="treeClearFilterBtn" class="btn ghost" type="button">Clear</button>
          </div>
          <div class="toolbar-tail">
            <span class="pill zoom-pill" id="treeZoomChip">100%</span>
            <button id="treeFitBtn" class="btn ghost" type="button">Fit</button>
            <button id="treeResetBtn" class="btn ghost" type="button">Reset View</button>
            <button id="treeZoomOutBtn" class="btn ghost" type="button">Zoom -</button>
            <button id="treeZoomInBtn" class="btn ghost" type="button">Zoom +</button>
          </div>
        </div>

        <div class="graph-stage-shell">
          <div id="treeCanvasScroll" class="graph-scroll" tabindex="0" aria-label="${pageTitle}">
            <svg id="treeCanvas" class="graph-canvas" role="img" aria-label="${pageTitle}">
              <g id="treeViewport">
                <g id="treeGroupLayer"></g>
                <g id="treeBandLayer"></g>
                <g id="treeEdgeLayer"></g>
                <g id="treeNodeLayer"></g>
              </g>
            </svg>
          </div>

          <aside id="treeInspector" class="card inspector-card" data-pinned="false">
            <div
              id="treeInspectorRail"
              class="inspector-rail"
              tabindex="0"
              role="button"
              aria-controls="treeInspectorPanel"
              aria-expanded="false"
              aria-label="Node inspector"
            >
              <span class="inspector-rail-label">Inspector</span>
              <span id="inspectorRailValue" class="inspector-rail-value">No selection</span>
            </div>

            <div id="treeInspectorPanel" class="inspector-panel">
              <div class="inspector-head">
                <div class="inspector-head-copy">
                  <h2>Inspector</h2>
                  <p id="inspectorSummaryValue" class="inspector-summary">Hover the rail to inspect nodes.</p>
                </div>
                <div class="inspector-head-actions">
                  <span id="selectionKindPill" class="pill kind-pill">none</span>
                  <button id="pinInspectorBtn" class="btn ghost inspector-pin-btn" type="button" aria-pressed="false">Pin</button>
                </div>
              </div>
              <div id="inspectorDetailBox" class="inspector-detail-box">
                <p class="detail-empty">Click a node or edge to inspect details.</p>
              </div>
              <div class="hint-box">
                <p>Tree view is rendered from runtime projection only.</p>
                <p>Machine truth still comes from <code>projects/*/generated/canonical.json</code>.</p>
              </div>
            </div>
          </aside>
        </div>
      </div>

      <footer class="graph-foot">
        <span id="treeStatusText">Ready</span>
        <span>Pan: Drag canvas · Layout: Layer-fixed auto sort · Open source: Double click / Enter</span>
      </footer>
    </section>
  </div>

  <div id="treeHoverCard" class="node-hover" aria-hidden="true"></div>

  <script id="shelf-tree-bootstrap" type="application/json">${safeJsonForScript(payload)}</script>
  <script nonce="${nonce}" src="${scriptUri}"></script>
</body>
</html>`;
}

module.exports = {
  buildRuntimeTreeHtml,
  treeTitleForKind,
  treeRefreshCommandForKind,
};
