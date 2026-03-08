from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class HierarchyNode:
    node_id: str
    label: str
    level: int
    description: str
    order: int | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class HierarchyEdge:
    source: str
    target: str
    relation: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class HierarchyGraph:
    title: str
    description: str
    level_labels: dict[int, str]
    nodes: list[HierarchyNode]
    edges: list[HierarchyEdge]


def _expect_dict(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object")
    return value


def _expect_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _expect_int(value: Any, field_name: str) -> int:
    if not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer")
    return value


def _expect_optional_int(value: Any, field_name: str) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer")
    return value


def load_hierarchy(path: Path) -> HierarchyGraph:
    raw = json.loads(path.read_text(encoding="utf-8"))
    root = _expect_dict(raw.get("root"), "root")

    title = _expect_str(root.get("title"), "title")
    description = _expect_str(root.get("description"), "description")

    raw_level_labels = _expect_dict(root.get("level_labels"), "level_labels")
    level_labels: dict[int, str] = {}
    for raw_key, raw_label in raw_level_labels.items():
        if not isinstance(raw_key, str) or not raw_key.isdigit():
            raise ValueError("level_labels keys must be level integers encoded as strings")
        level = int(raw_key)
        level_labels[level] = _expect_str(raw_label, f"level_labels[{raw_key}]")

    raw_nodes = root.get("nodes")
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise ValueError("nodes must be a non-empty list")

    nodes: list[HierarchyNode] = []
    node_ids: set[str] = set()
    for idx, raw_node in enumerate(raw_nodes):
        node_obj = _expect_dict(raw_node, f"nodes[{idx}]")
        node_id = _expect_str(node_obj.get("id"), f"nodes[{idx}].id")
        if node_id in node_ids:
            raise ValueError(f"duplicate node id: {node_id}")
        node_ids.add(node_id)

        node = HierarchyNode(
            node_id=node_id,
            label=_expect_str(node_obj.get("label"), f"nodes[{idx}].label"),
            level=_expect_int(node_obj.get("level"), f"nodes[{idx}].level"),
            description=_expect_str(node_obj.get("description"), f"nodes[{idx}].description"),
            order=_expect_optional_int(node_obj.get("order"), f"nodes[{idx}].order"),
            metadata={
                str(key): value
                for key, value in node_obj.items()
                if key not in {"id", "label", "level", "description", "order"}
            },
        )
        nodes.append(node)

    raw_edges = root.get("edges")
    if not isinstance(raw_edges, list):
        raise ValueError("edges must be a list")

    edges: list[HierarchyEdge] = []
    for idx, raw_edge in enumerate(raw_edges):
        edge_obj = _expect_dict(raw_edge, f"edges[{idx}]")
        source = _expect_str(edge_obj.get("from"), f"edges[{idx}].from")
        target = _expect_str(edge_obj.get("to"), f"edges[{idx}].to")
        relation = _expect_str(edge_obj.get("relation"), f"edges[{idx}].relation")
        if source not in node_ids or target not in node_ids:
            raise ValueError(f"edge references unknown node: {source} -> {target}")
        metadata = {
            str(key): value
            for key, value in edge_obj.items()
            if key not in {"from", "to", "relation"}
        }
        edges.append(
            HierarchyEdge(
                source=source,
                target=target,
                relation=relation,
                metadata=metadata,
            )
        )

    _validate_acyclic(nodes, edges)

    return HierarchyGraph(
        title=title,
        description=description,
        level_labels=level_labels,
        nodes=nodes,
        edges=edges,
    )


def _validate_acyclic(nodes: list[HierarchyNode], edges: list[HierarchyEdge]) -> None:
    graph: dict[str, list[str]] = {node.node_id: [] for node in nodes}
    for edge in edges:
        graph[edge.source].append(edge.target)

    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(node_id: str) -> None:
        if node_id in visited:
            return
        if node_id in visiting:
            raise ValueError(f"cycle detected at node: {node_id}")
        visiting.add(node_id)
        for child_id in graph[node_id]:
            dfs(child_id)
        visiting.remove(node_id)
        visited.add(node_id)

    for node_id in graph:
        dfs(node_id)


def _refine_level_orders(
    levels: list[int],
    level_orders: dict[int, list[str]],
    node_by_id: dict[str, HierarchyNode],
    incoming: dict[str, list[str]],
    outgoing: dict[str, list[str]],
) -> None:
    def sweep(level_iter: list[int], neighbors_of: dict[str, list[str]]) -> None:
        node_slot: dict[str, int] = {}
        for level in levels:
            for idx, node_id in enumerate(level_orders[level]):
                node_slot[node_id] = idx

        for level in level_iter:
            row = level_orders[level]
            sorted_row = sorted(
                row,
                key=lambda node_id: _node_sort_key(
                    node_id=node_id,
                    row=row,
                    neighbors_of=neighbors_of,
                    node_by_id=node_by_id,
                    node_slot=node_slot,
                ),
            )
            level_orders[level] = sorted_row

    if len(levels) <= 1:
        return

    for _ in range(6):
        sweep(levels[1:], incoming)
        sweep(list(reversed(levels[:-1])), outgoing)


def _node_sort_key(
    node_id: str,
    row: list[str],
    neighbors_of: dict[str, list[str]],
    node_by_id: dict[str, HierarchyNode],
    node_slot: dict[str, int],
) -> tuple[int, float, str]:
    node = node_by_id[node_id]
    if node.order is not None:
        return (0, float(node.order), node_id)

    neighbors = neighbors_of.get(node_id, [])
    ranked_neighbors = [node_slot[n_id] for n_id in neighbors if n_id in node_slot]

    if ranked_neighbors:
        barycenter = sum(ranked_neighbors) / float(len(ranked_neighbors))
    else:
        barycenter = float(row.index(node_id))

    return (1, barycenter, node_id)


def compute_layout(graph: HierarchyGraph, width: int = 1520, height: int = 980) -> dict[str, tuple[float, float]]:
    level_to_nodes: dict[int, list[HierarchyNode]] = {}
    for node in graph.nodes:
        level_to_nodes.setdefault(node.level, []).append(node)

    levels = sorted(level_to_nodes)
    if not levels:
        return {}

    level_orders: dict[int, list[str]] = {}
    for level in levels:
        row_nodes = sorted(
            level_to_nodes[level],
            key=lambda item: (
                item.order is None,
                item.order if item.order is not None else 0,
                item.node_id,
            ),
        )
        level_orders[level] = [node.node_id for node in row_nodes]

    incoming: dict[str, list[str]] = {node.node_id: [] for node in graph.nodes}
    outgoing: dict[str, list[str]] = {node.node_id: [] for node in graph.nodes}
    for edge in graph.edges:
        incoming[edge.target].append(edge.source)
        outgoing[edge.source].append(edge.target)

    node_by_id = {node.node_id: node for node in graph.nodes}
    _refine_level_orders(
        levels=levels,
        level_orders=level_orders,
        node_by_id=node_by_id,
        incoming=incoming,
        outgoing=outgoing,
    )

    top_margin = 132.0
    bottom_margin = 120.0
    left_margin = 210.0
    right_margin = 96.0

    vertical_span = max(1.0, float(height) - top_margin - bottom_margin)
    y_step = vertical_span / max(1, len(levels) - 1)

    positions: dict[str, tuple[float, float]] = {}
    for level_idx, level in enumerate(levels):
        row_ids = level_orders[level]
        count = len(row_ids)
        if count == 1:
            xs = [float(width) / 2.0]
        else:
            span = max(1.0, float(width) - left_margin - right_margin)
            cell = span / float(count + 1)
            xs = [left_margin + cell * float(i + 1) for i in range(count)]

        y = top_margin + level_idx * y_step
        for node_id, x in zip(row_ids, xs):
            positions[node_id] = (x, y)

    return positions


def _build_payload(
    graph: HierarchyGraph,
    positions: dict[str, tuple[float, float]],
    width: int,
    height: int,
) -> dict[str, Any]:
    level_values = sorted({node.level for node in graph.nodes})

    level_to_node_count: dict[int, int] = {}
    for node in graph.nodes:
        level_to_node_count[node.level] = level_to_node_count.get(node.level, 0) + 1

    relation_counts: dict[str, int] = {}
    for edge in graph.edges:
        relation_counts[edge.relation] = relation_counts.get(edge.relation, 0) + 1

    nodes_payload: list[dict[str, Any]] = []
    for node in graph.nodes:
        x, y = positions[node.node_id]
        item: dict[str, Any] = {
            "id": node.node_id,
            "label": node.label,
            "level": node.level,
            "description": node.description,
            "x": x,
            "y": y,
        }
        if node.metadata:
            item.update(node.metadata)
        nodes_payload.append(item)

    edges_payload: list[dict[str, Any]] = []
    for edge in graph.edges:
        edge_item: dict[str, Any] = {
            "from": edge.source,
            "to": edge.target,
            "relation": edge.relation,
        }
        edge_item.update(edge.metadata)
        edges_payload.append(edge_item)

    return {
        "title": graph.title,
        "description": graph.description,
        "width": width,
        "height": height,
        "nodes": nodes_payload,
        "edges": edges_payload,
        "level_labels": {
            str(level): graph.level_labels.get(level, f"层级 {level}") for level in level_values
        },
        "level_node_counts": {str(level): level_to_node_count.get(level, 0) for level in level_values},
        "relation_counts": relation_counts,
    }


def render_html(graph: HierarchyGraph, output_path: Path, width: int = 1520, height: int = 980) -> None:
    positions = compute_layout(graph, width=width, height=height)
    payload = _build_payload(graph, positions, width=width, height=height)
    payload_json = json.dumps(payload, ensure_ascii=False)

    html = """<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>M Hierarchy Graph</title>
  <style>
    :root {
      color-scheme: light dark;
      --bg: var(--vscode-editor-background, #1e1e1e);
      --card: var(--vscode-editorWidget-background, rgba(255, 255, 255, 0.03));
      --card-muted: rgba(255, 255, 255, 0.04);
      --text: var(--vscode-editor-foreground, var(--vscode-foreground, #cccccc));
      --sub: var(--vscode-descriptionForeground, #9da1a6);
      --border: var(--vscode-panel-border, rgba(128, 128, 128, 0.3));
      --accent: var(--vscode-textLink-foreground, #3794ff);
      --accent-strong: var(--vscode-focusBorder, var(--vscode-textLink-foreground, #3794ff));
      --button-bg: var(--vscode-button-secondaryBackground, rgba(255, 255, 255, 0.06));
      --button-bg-hover: var(--vscode-button-secondaryHoverBackground, rgba(255, 255, 255, 0.10));
      --button-fg: var(--vscode-button-secondaryForeground, var(--text));
      --pill-bg: var(--vscode-badge-background, rgba(90, 93, 94, 0.35));
      --pill-fg: var(--vscode-badge-foreground, var(--text));
      --canvas: var(--vscode-editor-background, #1e1e1e);
      --graph-shell-bg: rgba(255, 255, 255, 0.02);
      --graph-stage: rgba(255, 255, 255, 0.015);
      --graph-guide: rgba(255, 255, 255, 0.10);
      --graph-band-a: rgba(255, 255, 255, 0.04);
      --graph-band-b: rgba(255, 255, 255, 0.02);
      --graph-edge: rgba(158, 174, 190, 0.58);
      --graph-edge-active: var(--accent);
      --graph-edge-muted: rgba(255, 255, 255, 0.08);
      --graph-label: var(--text);
      --graph-label-bg: rgba(30, 30, 30, 0.82);
      --graph-label-border: rgba(255, 255, 255, 0.08);
      --graph-node-active: var(--accent);
    }

    body.vscode-light {
      --card: #ffffff;
      --card-muted: #f6f8fa;
      --border: var(--vscode-panel-border, rgba(0, 0, 0, 0.12));
      --button-bg: #eef2f7;
      --button-bg-hover: #e4ebf3;
      --pill-bg: #edf1f5;
      --pill-fg: #445366;
      --canvas: #ffffff;
      --graph-shell-bg: rgba(0, 0, 0, 0.025);
      --graph-stage: rgba(0, 0, 0, 0.018);
      --graph-guide: rgba(0, 0, 0, 0.08);
      --graph-band-a: rgba(0, 0, 0, 0.04);
      --graph-band-b: rgba(0, 0, 0, 0.02);
      --graph-edge: rgba(78, 103, 131, 0.45);
      --graph-edge-muted: rgba(0, 0, 0, 0.08);
      --graph-label-bg: rgba(255, 255, 255, 0.86);
      --graph-label-border: rgba(0, 0, 0, 0.09);
    }

    body.vscode-high-contrast,
    body.vscode-high-contrast-light {
      --border: var(--vscode-contrastBorder, #ffffff);
      --graph-guide: var(--vscode-contrastBorder, #ffffff);
      --graph-edge: var(--vscode-contrastActiveBorder, #f38518);
      --graph-edge-active: var(--vscode-contrastActiveBorder, #f38518);
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      color: var(--text);
      font-family: var(--vscode-font-family, \"Segoe WPC\", \"Segoe UI\", sans-serif);
      background: var(--bg);
    }

    .layout {
      max-width: none;
      margin: 0 auto;
      padding: 12px;
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(300px, 320px);
      gap: 12px;
      align-items: start;
    }

    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      overflow: hidden;
    }

    .graph-card {
      padding: 0;
      display: grid;
    }

    .head {
      padding: 12px 14px 10px;
      border-bottom: 1px solid var(--border);
      background: transparent;
    }

    h1 {
      margin: 0;
      font-size: 14px;
      font-weight: 600;
      letter-spacing: 0.01em;
      line-height: 1.2;
    }

    .desc {
      margin: 6px 0 0;
      color: var(--sub);
      font-size: 12px;
      line-height: 1.55;
    }

    .legend {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      padding: 10px 12px;
      border-bottom: 1px solid var(--border);
      background: transparent;
    }

    .graph-shell {
      padding: 12px;
      background:
        linear-gradient(180deg, rgba(55, 148, 255, 0.06), transparent 40%),
        var(--graph-shell-bg);
      border-bottom: 1px solid var(--border);
    }

    .graph-scroll {
      overflow: auto;
      max-height: min(76vh, 980px);
      border: 1px solid var(--border);
      border-radius: 12px;
      background: var(--graph-stage);
    }

    .graph-stage {
      width: max-content;
      min-width: 100%;
      padding: 14px;
    }

    .pill {
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 3px 8px;
      font-size: 11px;
      color: var(--pill-fg);
      border: 1px solid var(--border);
      background: var(--pill-bg);
      white-space: nowrap;
    }

    .switch-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border-radius: 999px;
      padding: 3px 8px;
      font-size: 11px;
      color: var(--pill-fg);
      border: 1px solid var(--border);
      background: var(--card-muted);
    }

    .switch-pill input {
      margin: 0;
      accent-color: var(--accent);
    }

    #graphSvg {
      width: auto;
      height: auto;
      display: block;
      background: transparent;
    }

    .foot {
      margin: 0;
      padding: 10px 12px;
      color: var(--sub);
      font-size: 11px;
      border-top: 1px solid var(--border);
      background: transparent;
    }

    .side {
      display: grid;
      gap: 12px;
      align-content: start;
      position: sticky;
      top: 12px;
    }

    .info-card,
    .detail-card {
      padding: 12px;
    }

    .detail-card {
      max-height: calc(100vh - 24px);
      overflow: auto;
    }

    .info-title,
    .detail-title {
      margin: 0 0 8px;
      font-size: 11px;
      font-weight: 600;
      color: var(--sub);
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }

    .meta {
      margin: 0;
      color: var(--sub);
      font-size: 12px;
      line-height: 1.55;
    }

    .stat-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 12px;
      padding: 8px 0;
      border-bottom: 1px solid var(--border);
      font-size: 12px;
      line-height: 1.45;
    }

    .stat-row:first-child {
      padding-top: 0;
    }

    .stat-row:last-child {
      border-bottom: 0;
      padding-bottom: 0;
    }

    .stat-key {
      color: var(--sub);
      overflow-wrap: anywhere;
    }

    .stat-value {
      color: var(--text);
      font-weight: 600;
      text-align: right;
      white-space: nowrap;
    }

    .detail-empty {
      margin: 0;
    }

    .detail-group {
      display: grid;
      gap: 8px;
      padding: 10px 0;
      border-bottom: 1px solid var(--border);
    }

    .detail-group:first-child {
      padding-top: 0;
    }

    .detail-group:last-child {
      border-bottom: 0;
      padding-bottom: 0;
    }

    .detail-section-title {
      margin: 0;
      font-size: 11px;
      font-weight: 600;
      color: var(--sub);
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }

    .detail-kv {
      display: grid;
      gap: 4px;
    }

    .detail-key {
      font-size: 11px;
      line-height: 1.4;
      color: var(--sub);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .detail-value {
      font-size: 12px;
      line-height: 1.55;
      color: var(--text);
      overflow-wrap: anywhere;
    }

    .mono {
      font-family: var(--vscode-editor-font-family, \"Cascadia Code\", monospace);
      font-size: 11px;
    }

    .kv {
      margin: 0 0 8px;
      font-size: 12px;
      line-height: 1.55;
    }

    .kv b {
      color: var(--sub);
      font-weight: 600;
    }

    ul {
      margin: 6px 0 0 18px;
      padding: 0;
    }

    li {
      margin: 3px 0;
      font-size: 12px;
      color: var(--text);
      line-height: 1.45;
    }

    button {
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 5px 9px;
      font: inherit;
      font-size: 11px;
      color: var(--button-fg);
      background: var(--button-bg);
      cursor: pointer;
    }

    button:hover {
      background: var(--button-bg-hover);
    }

    button:focus-visible {
      outline: 1px solid var(--accent-strong);
      outline-offset: -1px;
    }

    .action-row {
      margin: 0 0 8px;
    }

    .detail-list {
      margin: 0;
      padding-left: 18px;
    }

    .detail-item {
      margin: 0 0 6px;
      color: var(--text);
      overflow-wrap: anywhere;
    }

    .detail-action {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 28px;
      padding-inline: 10px;
    }

    .level-band {
      fill: var(--graph-band-a);
      stroke: var(--border);
      stroke-width: 1;
    }

    .level-band.alt {
      fill: var(--graph-band-b);
    }

    .level-guide {
      stroke: var(--graph-guide);
      stroke-width: 1;
      stroke-dasharray: 4 6;
    }

    .level-label {
      font-size: 11px;
      fill: var(--sub);
      font-weight: 600;
      letter-spacing: 0.04em;
    }

    .edge {
      fill: none;
      stroke: var(--graph-edge);
      stroke-width: 1.8;
      stroke-linecap: round;
      marker-end: url(#arrowDefault);
      opacity: 0.86;
      transition: opacity 140ms ease, stroke 140ms ease;
    }

    .edge.faded {
      opacity: 0.12;
      stroke: var(--graph-edge-muted);
    }

    .edge.active {
      stroke: var(--graph-edge-active);
      marker-end: url(#arrowActive);
      opacity: 1;
      stroke-width: 2.6;
      filter: drop-shadow(0 0 8px rgba(55, 148, 255, 0.24));
    }

    .arrow-default {
      fill: var(--graph-edge);
    }

    .arrow-active {
      fill: var(--graph-edge-active);
    }

    .node-circle {
      fill: var(--node-fill, var(--graph-node-active));
      stroke: var(--canvas);
      stroke-width: 2.4;
      cursor: pointer;
      transition: transform 140ms ease, opacity 140ms ease, filter 140ms ease;
      transform-origin: center;
    }

    .node-circle:hover {
      transform: scale(1.02);
    }

    .node-circle.faded {
      opacity: 0.24;
    }

    .node-circle.active {
      fill: var(--graph-node-active);
      transform: scale(1.06);
      filter: drop-shadow(0 0 12px rgba(55, 148, 255, 0.32));
    }

    .node-label {
      fill: var(--graph-label);
      font-size: 11px;
      font-weight: 600;
      text-anchor: middle;
      dominant-baseline: hanging;
      pointer-events: none;
      letter-spacing: 0.2px;
      transition: opacity 120ms ease;
    }

    .node-label.faded {
      opacity: 0.3;
    }

    .node-label.hidden {
      opacity: 0;
    }

    .node-label-box {
      fill: var(--graph-label-bg);
      stroke: var(--graph-label-border);
      stroke-width: 1;
      pointer-events: none;
      transition: opacity 120ms ease;
    }

    .node-label-box.faded {
      opacity: 0.22;
    }

    .node-label-box.hidden {
      opacity: 0;
    }

    @media (max-width: 1220px) {
      .layout {
        grid-template-columns: 1fr;
      }

      .side {
        grid-template-columns: 1fr 1fr;
        position: static;
      }

      .detail-card {
        grid-column: 1 / -1;
      }
    }

    @media (max-width: 760px) {
      body {
        font-size: 13px;
      }

      .layout {
        padding: 10px;
      }

      .head {
        padding: 12px;
      }

      h1 {
        font-size: 13px;
      }

      .desc {
        font-size: 12px;
      }

      .legend {
        padding: 10px 12px;
        gap: 8px;
      }

      .side {
        grid-template-columns: 1fr;
        position: static;
      }
    }
  </style>
</head>
<body>
  <div class=\"layout\">
    <section class=\"card graph-card\">
      <div class=\"head\">
        <h1 id=\"title\"></h1>
        <p id=\"description\" class=\"desc\"></p>
      </div>
      <div class=\"legend\">
        <span class=\"pill\" id=\"summaryNodes\"></span>
        <span class=\"pill\" id=\"summaryEdges\"></span>
        <span class=\"pill\" id=\"summaryFan\"></span>
        <label class=\"switch-pill\">
          <input type=\"checkbox\" id=\"toggleLabels\" checked />
          显示全部标签
        </label>
        <span class=\"pill\">点击节点查看直连上游/下游关系</span>
      </div>
      <div class=\"graph-shell\">
        <div class=\"graph-scroll\">
          <div class=\"graph-stage\">
            <svg id=\"graphSvg\" role=\"img\" aria-label=\"M hierarchy graph\"></svg>
          </div>
        </div>
      </div>
      <p class=\"foot\">图中只展示 M 结构层级与组合关系，不包含代码规范与框架规范条目。</p>
    </section>

    <aside class=\"side\">
      <section class=\"card info-card\">
        <h2 class=\"info-title\">层级统计</h2>
        <div id=\"levelStats\"></div>
      </section>

      <section class=\"card info-card\">
        <h2 class=\"info-title\">关系统计</h2>
        <div id=\"relationStats\"></div>
      </section>

      <section class=\"card detail-card\">
        <h2 class=\"detail-title\">节点详情</h2>
        <div id=\"detailBox\"><p class=\"meta detail-empty\">点击左侧节点查看详情。</p></div>
      </section>
    </aside>
  </div>

  <script>
    const graphData = __PAYLOAD_JSON__;
    const SVG_NS = "http://www.w3.org/2000/svg";
    const vscodeApi = typeof acquireVsCodeApi === "function" ? acquireVsCodeApi() : null;

    const svg = document.getElementById("graphSvg");
    const titleEl = document.getElementById("title");
    const descriptionEl = document.getElementById("description");
    const summaryNodesEl = document.getElementById("summaryNodes");
    const summaryEdgesEl = document.getElementById("summaryEdges");
    const summaryFanEl = document.getElementById("summaryFan");
    const toggleLabelsEl = document.getElementById("toggleLabels");
    const levelStatsEl = document.getElementById("levelStats");
    const relationStatsEl = document.getElementById("relationStats");
    const detailBoxEl = document.getElementById("detailBox");

    function appendStatRow(container, label, value) {
      const row = document.createElement("div");
      row.className = "stat-row";

      const key = document.createElement("span");
      key.className = "stat-key";
      key.textContent = label;

      const val = document.createElement("span");
      val.className = "stat-value";
      val.textContent = value;

      row.append(key, val);
      container.appendChild(row);
    }

    titleEl.textContent = graphData.title;
    descriptionEl.textContent = graphData.description;
    summaryNodesEl.textContent = `节点数: ${graphData.nodes.length}`;
    summaryEdgesEl.textContent = `关系边: ${graphData.edges.length}`;

    svg.setAttribute("viewBox", `0 0 ${graphData.width} ${graphData.height}`);
    svg.setAttribute("width", String(graphData.width));
    svg.setAttribute("height", String(graphData.height));

    const byId = new Map(graphData.nodes.map((node) => [node.id, node]));
    const incoming = new Map(graphData.nodes.map((node) => [node.id, []]));
    const outgoing = new Map(graphData.nodes.map((node) => [node.id, []]));

    for (const edge of graphData.edges) {
      const inList = incoming.get(edge.to);
      if (inList) inList.push(edge);
      const outList = outgoing.get(edge.from);
      if (outList) outList.push(edge);
    }

    let maxFanOut = 0;
    let maxFanIn = 0;
    for (const [nodeId] of byId.entries()) {
      maxFanOut = Math.max(maxFanOut, (outgoing.get(nodeId) ?? []).length);
      maxFanIn = Math.max(maxFanIn, (incoming.get(nodeId) ?? []).length);
    }
    summaryFanEl.textContent = `最大扇出/扇入: ${maxFanOut}/${maxFanIn}`;

    const levelEntries = Object.entries(graphData.level_labels)
      .map(([rawLevel, name]) => [Number(rawLevel), String(name)])
      .sort((a, b) => a[0] - b[0]);

    const levelCenters = new Map();
    for (const [level] of levelEntries) {
      const nodesInLevel = graphData.nodes.filter((node) => node.level === level);
      const avgY =
        nodesInLevel.reduce((sum, node) => sum + node.y, 0) / Math.max(1, nodesInLevel.length);
      levelCenters.set(level, avgY);

      appendStatRow(
        levelStatsEl,
        graphData.level_labels[String(level)] ?? `层级 ${level}`,
        `${graphData.level_node_counts[String(level)] ?? 0} 个节点`
      );
    }

    for (const [relation, count] of Object.entries(graphData.relation_counts ?? {})) {
      appendStatRow(relationStatsEl, relation, String(count));
    }

    if (!relationStatsEl.children.length) {
      appendStatRow(relationStatsEl, "状态", "无关系类型统计");
    }

    const defs = document.createElementNS(SVG_NS, "defs");
    defs.innerHTML = `
      <marker id=\"arrowDefault\" markerWidth=\"10\" markerHeight=\"10\" refX=\"8\" refY=\"3\" orient=\"auto\" markerUnits=\"strokeWidth\">
        <path class=\"arrow-default\" d=\"M0,0 L0,6 L9,3 z\"></path>
      </marker>
      <marker id=\"arrowActive\" markerWidth=\"10\" markerHeight=\"10\" refX=\"8\" refY=\"3\" orient=\"auto\" markerUnits=\"strokeWidth\">
        <path class=\"arrow-active\" d=\"M0,0 L0,6 L9,3 z\"></path>
      </marker>
    `;
    svg.appendChild(defs);

    for (let index = 0; index < levelEntries.length; index += 1) {
      const [level, levelName] = levelEntries[index];
      const centerY = levelCenters.get(level) ?? 0;
      const prevCenter = index > 0 ? levelCenters.get(levelEntries[index - 1][0]) ?? centerY : centerY;
      const nextCenter =
        index < levelEntries.length - 1
          ? levelCenters.get(levelEntries[index + 1][0]) ?? centerY
          : centerY;

      const top = index === 0 ? 26 : (prevCenter + centerY) / 2;
      const bottom =
        index === levelEntries.length - 1 ? graphData.height - 26 : (centerY + nextCenter) / 2;

      const band = document.createElementNS(SVG_NS, "rect");
      band.setAttribute("x", "58");
      band.setAttribute("y", String(top));
      band.setAttribute("width", String(Math.max(1, graphData.width - 86)));
      band.setAttribute("height", String(Math.max(1, bottom - top)));
      band.setAttribute("rx", "12");
      band.setAttribute("ry", "12");
      band.setAttribute("class", `level-band${index % 2 === 1 ? " alt" : ""}`);
      svg.appendChild(band);

      const guide = document.createElementNS(SVG_NS, "line");
      guide.setAttribute("x1", "74");
      guide.setAttribute("x2", String(graphData.width - 26));
      guide.setAttribute("y1", String(centerY));
      guide.setAttribute("y2", String(centerY));
      guide.setAttribute("class", "level-guide");
      svg.appendChild(guide);

      const label = document.createElementNS(SVG_NS, "text");
      label.setAttribute("x", "76");
      label.setAttribute("y", String(top + 24));
      label.setAttribute("class", "level-label");
      label.textContent = levelName;
      svg.appendChild(label);
    }

    function edgePath(fromNode, toNode) {
      const dx = toNode.x - fromNode.x;
      const dy = toNode.y - fromNode.y;
      const curve = Math.max(44, Math.min(136, Math.abs(dy) * 0.44));
      const sidePull =
        dx === 0 ? 0 : Math.sign(dx) * Math.max(26, Math.min(116, Math.abs(dx) * 0.28));
      const c1x = fromNode.x + sidePull;
      const c1y = fromNode.y + curve;
      const c2x = toNode.x - sidePull;
      const c2y = toNode.y - curve;
      return `M ${fromNode.x} ${fromNode.y} C ${c1x} ${c1y}, ${c2x} ${c2y}, ${toNode.x} ${toNode.y}`;
    }

    const levelNumbers = levelEntries.map(([level]) => level);
    const minLevel = Math.min(...levelNumbers);
    const maxLevel = Math.max(...levelNumbers);
    const levelSpan = Math.max(1, maxLevel - minLevel);

    function currentThemeMode() {
      const classList = document.body.classList;
      if (
        classList.contains("vscode-high-contrast") ||
        classList.contains("vscode-high-contrast-light")
      ) {
        return "hc";
      }
      if (classList.contains("vscode-light")) {
        return "light";
      }
      if (!classList.contains("vscode-dark")) {
        if (typeof window.matchMedia === "function") {
          return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
        }
        return "dark";
      }
      return "dark";
    }

    function nodeColorForLevel(level) {
      const t = (level - minLevel) / levelSpan;
      const mode = currentThemeMode();
      if (mode === "hc") {
        const light = 76 - Math.round(t * 16);
        return `hsl(210 24% ${light}%)`;
      }
      if (mode === "light") {
        const hue = 210 - Math.round(t * 12);
        const sat = 30 + Math.round(t * 8);
        const light = 58 - Math.round(t * 10);
        return `hsl(${hue} ${sat}% ${light}%)`;
      }
      const hue = 214 - Math.round(t * 14);
      const sat = 34 + Math.round(t * 10);
      const light = 48 - Math.round(t * 10);
      return `hsl(${hue} ${sat}% ${light}%)`;
    }

    const edgeElements = [];
    for (const edge of graphData.edges) {
      const fromNode = byId.get(edge.from);
      const toNode = byId.get(edge.to);
      if (!fromNode || !toNode) continue;

      const path = document.createElementNS(SVG_NS, "path");
      path.setAttribute("d", edgePath(fromNode, toNode));
      path.setAttribute("class", "edge");
      path.setAttribute("data-from", edge.from);
      path.setAttribute("data-to", edge.to);
      path.setAttribute("data-relation", edge.relation);
      const edgeRule = edge.rule ? `, rule=${edge.rule}` : "";
      const edgeConstraint = edge.constraint ? `, constraint=${edge.constraint}` : "";
      path.appendChild(document.createElementNS(SVG_NS, "title")).textContent = `${edge.from} -> ${edge.to} (${edge.relation}${edgeRule}${edgeConstraint})`;
      svg.appendChild(path);
      edgeElements.push(path);
    }

    const nodeCircleMap = new Map();
    const nodeLabelMap = new Map();
    const nodeLabelBoxMap = new Map();

    for (const node of graphData.nodes) {
      const group = document.createElementNS(SVG_NS, "g");

      const circle = document.createElementNS(SVG_NS, "circle");
      circle.setAttribute("cx", String(node.x));
      circle.setAttribute("cy", String(node.y));
      circle.setAttribute("r", "24");
      circle.setAttribute("class", "node-circle");
      circle.setAttribute("data-id", node.id);
      circle.style.setProperty("--node-fill", nodeColorForLevel(node.level));
      group.appendChild(circle);

      const labelBox = document.createElementNS(SVG_NS, "rect");
      labelBox.setAttribute("class", "node-label-box");
      labelBox.setAttribute("rx", "7");
      labelBox.setAttribute("ry", "7");
      group.appendChild(labelBox);

      const label = document.createElementNS(SVG_NS, "text");
      label.setAttribute("x", String(node.x));
      label.setAttribute("y", String(node.y + 31));
      label.setAttribute("class", "node-label");
      label.textContent = node.label;
      group.appendChild(label);

      group.addEventListener("click", (event) => {
        event.stopPropagation();
        selectNode(node.id);
      });

      svg.appendChild(group);
      const bbox = label.getBBox();
      const padX = 7;
      const padY = 2;
      labelBox.setAttribute("x", String(bbox.x - padX));
      labelBox.setAttribute("y", String(bbox.y - padY));
      labelBox.setAttribute("width", String(Math.max(10, bbox.width + padX * 2)));
      labelBox.setAttribute("height", String(Math.max(10, bbox.height + padY * 2)));
      group.insertBefore(labelBox, label);

      nodeCircleMap.set(node.id, circle);
      nodeLabelMap.set(node.id, label);
      nodeLabelBoxMap.set(node.id, labelBox);
    }

    function applyThemeState() {
      for (const node of graphData.nodes) {
        const circle = nodeCircleMap.get(node.id);
        if (!circle) continue;
        circle.style.setProperty("--node-fill", nodeColorForLevel(node.level));
      }
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }

    function toList(items) {
      if (!Array.isArray(items) || items.length === 0) {
        return '<li class="detail-item">无</li>';
      }
      return items.map((item) => `<li class="detail-item">${escapeHtml(item)}</li>`).join("");
    }

    function formatEdgeItem(edge, mode) {
      const peerId = mode === "up" ? edge.from : edge.to;
      const peerLabel = byId.get(peerId)?.label ?? peerId;
      const extras = [];
      if (edge.rule) extras.push(`rule=${edge.rule}`);
      if (edge.principle) extras.push(`principle=${edge.principle}`);
      if (edge.constraint) extras.push(`constraint=${edge.constraint}`);
      if (edge.source_file && edge.source_line) {
        extras.push(`source=${edge.source_file}:${edge.source_line}`);
      }
      const extraText = extras.length ? ` · ${extras.join(" · ")}` : "";
      return `${peerId} (${peerLabel}) · ${edge.relation}${extraText}`;
    }

    function openSourceFile(filePath, lineNumber) {
      const safeLine = Number.isFinite(Number(lineNumber)) ? Math.max(1, Number(lineNumber)) : 1;
      if (vscodeApi) {
        vscodeApi.postMessage({
          type: "archSync.openSource",
          file: String(filePath || ""),
          line: safeLine
        });
        return;
      }
      const uri = `vscode://file/${encodeURI(String(filePath || ""))}:${safeLine}`;
      window.location.href = uri;
    }

    function selectNode(nodeId) {
      const related = new Set([nodeId]);
      const upEdges = incoming.get(nodeId) ?? [];
      const downEdges = outgoing.get(nodeId) ?? [];

      for (const edge of upEdges) related.add(edge.from);
      for (const edge of downEdges) related.add(edge.to);

      for (const [id, circle] of nodeCircleMap.entries()) {
        circle.classList.remove("active", "faded");
        const label = nodeLabelMap.get(id);
        const labelBox = nodeLabelBoxMap.get(id);
        if (label) label.classList.remove("faded");
        if (labelBox) labelBox.classList.remove("faded");

        if (id === nodeId) {
          circle.classList.add("active");
        } else if (!related.has(id)) {
          circle.classList.add("faded");
          if (label) label.classList.add("faded");
          if (labelBox) labelBox.classList.add("faded");
        }
      }

      for (const edgeEl of edgeElements) {
        edgeEl.classList.remove("active", "faded");
        const from = edgeEl.getAttribute("data-from");
        const to = edgeEl.getAttribute("data-to");
        if (from === nodeId || to === nodeId) {
          edgeEl.classList.add("active");
        } else {
          edgeEl.classList.add("faded");
        }
      }

      const node = byId.get(nodeId);
      if (!node) return;

      const levelName = graphData.level_labels[String(node.level)] ?? `层级 ${node.level}`;
      const upItems = upEdges.map((edge) => formatEdgeItem(edge, "up"));
      const downItems = downEdges.map((edge) => formatEdgeItem(edge, "down"));
      const sourceFile = typeof node.source_file === "string" ? node.source_file : "";
      const sourceLine =
        Number.isFinite(Number(node.source_line)) && Number(node.source_line) > 0
          ? Number(node.source_line)
          : 1;
      const sourceAction = sourceFile
        ? `<button type="button" class="detail-action" data-open-source="1" data-file="${escapeHtml(sourceFile)}" data-line="${sourceLine}">打开源文件</button>`
        : "无";

      detailBoxEl.innerHTML = `
        <section class=\"detail-group\">
          <h3 class=\"detail-section-title\">节点概览</h3>
          <div class=\"detail-kv\">
            <span class=\"detail-key\">ID</span>
            <span class=\"detail-value mono\">${escapeHtml(node.id)}</span>
          </div>
          <div class=\"detail-kv\">
            <span class=\"detail-key\">标签</span>
            <span class=\"detail-value\">${escapeHtml(node.label)}</span>
          </div>
          <div class=\"detail-kv\">
            <span class=\"detail-key\">层级</span>
            <span class=\"detail-value\">${escapeHtml(levelName)}</span>
          </div>
          <div class=\"detail-kv\">
            <span class=\"detail-key\">描述</span>
            <span class=\"detail-value\">${escapeHtml(node.description)}</span>
          </div>
        </section>
        <section class=\"detail-group\">
          <h3 class=\"detail-section-title\">来源与跳转</h3>
          <div class=\"detail-kv\">
            <span class=\"detail-key\">源文件</span>
            <span class=\"detail-value mono\">${sourceFile ? `${escapeHtml(sourceFile)}:${sourceLine}` : "无"}</span>
          </div>
          <div class=\"action-row\">${sourceAction}</div>
        </section>
        <section class=\"detail-group\">
          <h3 class=\"detail-section-title\">上游节点</h3>
          <ul class=\"detail-list\">${toList(upItems)}</ul>
        </section>
        <section class=\"detail-group\">
          <h3 class=\"detail-section-title\">下游节点</h3>
          <ul class=\"detail-list\">${toList(downItems)}</ul>
        </section>
      `;

      const openBtn = detailBoxEl.querySelector("[data-open-source='1']");
      if (openBtn) {
        openBtn.addEventListener("click", (event) => {
          event.stopPropagation();
          const filePath = openBtn.getAttribute("data-file") || "";
          const lineNumber = Number(openBtn.getAttribute("data-line") || "1");
          openSourceFile(filePath, lineNumber);
        });
      }
    }

    function updateLabelVisibility() {
      const visible = toggleLabelsEl?.checked ?? true;
      for (const label of nodeLabelMap.values()) {
        label.classList.toggle("hidden", !visible);
      }
      for (const box of nodeLabelBoxMap.values()) {
        box.classList.toggle("hidden", !visible);
      }
    }

    function resetSelection() {
      for (const circle of nodeCircleMap.values()) {
        circle.classList.remove("active", "faded");
      }
      for (const label of nodeLabelMap.values()) {
        label.classList.remove("faded");
      }
      for (const box of nodeLabelBoxMap.values()) {
        box.classList.remove("faded");
      }
      for (const edgeEl of edgeElements) {
        edgeEl.classList.remove("active", "faded");
      }
      detailBoxEl.innerHTML =
        '<p class="meta detail-empty">点击左侧节点查看详情；可通过“显示全部标签”控制整体标签密度。</p>';
      updateLabelVisibility();
    }

    applyThemeState();
    const themeObserver = new MutationObserver(() => {
      applyThemeState();
    });
    themeObserver.observe(document.body, {
      attributes: true,
      attributeFilter: ["class"]
    });

    svg.addEventListener("click", resetSelection);
    if (toggleLabelsEl) {
      toggleLabelsEl.addEventListener("change", () => {
        updateLabelVisibility();
      });
    }
    resetSelection();
  </script>
</body>
</html>
"""
    html = html.replace("__PAYLOAD_JSON__", payload_json)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate interactive HTML graph from a hierarchy JSON payload."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("docs/hierarchy/shelf_framework_tree.json"),
        help="Input hierarchy JSON path",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/hierarchy/shelf_framework_tree.html"),
        help="Output HTML path",
    )
    parser.add_argument("--width", type=int, default=1520, help="SVG width")
    parser.add_argument("--height", type=int, default=980, help="SVG height")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    graph = load_hierarchy(args.input)
    render_html(graph, args.output, width=args.width, height=args.height)
    print(f"[OK] hierarchy graph generated: {args.output}")


if __name__ == "__main__":
    main()
