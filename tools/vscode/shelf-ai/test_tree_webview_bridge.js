const assert = require("assert");

const {
  buildRuntimeTreeHtml,
  treeRefreshCommandForKind,
  treeTitleForKind,
} = require("./tree_webview_bridge");

function main() {
  assert.strictEqual(treeTitleForKind("framework"), "Shelf · Framework Tree");
  assert.strictEqual(treeTitleForKind("evidence"), "Shelf · Evidence Tree");
  assert.strictEqual(treeRefreshCommandForKind("framework"), "Shelf: Refresh Framework Tree");
  assert.strictEqual(treeRefreshCommandForKind("evidence"), "Shelf: Refresh Evidence Tree");

  const html = buildRuntimeTreeHtml({
    kind: "framework",
    model: {
      title: "Demo Framework",
      description: "Demo description",
      kind: "framework",
      nodes: [
        {
          id: "framework:root",
          label: "framework",
          detail: "root",
          file: "",
          line: 1,
          depth: 0,
          kind: "framework_root",
        },
      ],
      edges: [],
    },
    layoutSettings: {
      frameworkNodeHorizontalGap: 11,
      frameworkLevelVerticalGap: 92,
    },
    viewSettings: {
      zoomMinScale: 0.52,
      zoomMaxScale: 2.4,
      wheelSensitivity: 1.4,
      inspectorWidth: 360,
      inspectorRailWidth: 46,
    },
    scriptUri: "vscode-resource://tree_view_bundle.js",
    styleUri: "vscode-resource://tree_view.css",
    cspSource: "vscode-webview-resource:",
  });

  assert(html.includes("shelf-tree-bootstrap"), "html should include bootstrap payload");
  assert(html.includes("tree_view_bundle.js"), "html should include script uri");
  assert(html.includes("tree_view.css"), "html should include style uri");
  assert(html.includes("Demo Framework"), "html should include model title");
  assert(html.includes('"frameworkNodeHorizontalGap":11'), "html should include horizontal gap setting");
  assert(html.includes('"frameworkLevelVerticalGap":92'), "html should include vertical gap setting");
  assert(html.includes('"zoomMinScale":0.52'), "html should include min zoom setting");
  assert(html.includes('"zoomMaxScale":2.4'), "html should include max zoom setting");
  assert(html.includes('"wheelSensitivity":1.4'), "html should include wheel sensitivity setting");
  assert(html.includes('"inspectorWidth":360'), "html should include inspector width setting");
  assert(html.includes('"inspectorRailWidth":46'), "html should include inspector rail width setting");
  assert(html.includes('id="treeInspector"'), "html should include inspector shell");
  assert(html.includes('id="treeInspectorRail"'), "html should include inspector rail");
  assert(html.includes('id="pinInspectorBtn"'), "html should include inspector pin toggle");
  assert(html.includes('id="treeGroupLayer"'), "html should include framework group svg layer");
  assert(html.includes('id="inspectorDetailBox"'), "html should include inspector detail box");
  assert(html.includes('id="treeHoverCard"'), "html should include hover card container");
  assert(
    html.includes("vscode-webview-resource:"),
    "html should include provided csp source in CSP"
  );
  assert(
    !html.includes("<script>alert(1)</script>"),
    "html should not accidentally include arbitrary script content"
  );
}

main();
