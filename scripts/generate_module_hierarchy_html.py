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
class HierarchyFrameworkGroup:
    name: str
    order: int
    local_levels: list[int]
    level_node_counts: dict[int, int]


@dataclass(frozen=True)
class HierarchyGraph:
    title: str
    description: str
    level_labels: dict[int, str]
    nodes: list[HierarchyNode]
    edges: list[HierarchyEdge]
    layout_mode: str = "global_levels"
    framework_groups: list[HierarchyFrameworkGroup] | None = None


@dataclass(frozen=True)
class LayoutResult:
    positions: dict[str, tuple[float, float]]
    width: int
    height: int


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


def _expect_optional_str(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
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

    raw_layout_mode = _expect_optional_str(root.get("layout_mode"), "layout_mode")
    layout_mode = raw_layout_mode or "global_levels"

    raw_framework_groups = root.get("framework_groups")
    framework_groups: list[HierarchyFrameworkGroup] | None = None
    if raw_framework_groups is not None:
        if not isinstance(raw_framework_groups, list):
            raise ValueError("framework_groups must be a list")
        framework_groups = []
        for idx, raw_group in enumerate(raw_framework_groups):
            group_obj = _expect_dict(raw_group, f"framework_groups[{idx}]")
            name = _expect_str(group_obj.get("name"), f"framework_groups[{idx}].name")
            order = _expect_int(group_obj.get("order"), f"framework_groups[{idx}].order")

            raw_local_levels = group_obj.get("local_levels")
            if not isinstance(raw_local_levels, list):
                raise ValueError(f"framework_groups[{idx}].local_levels must be a list")
            local_levels: list[int] = []
            for level_idx, raw_level in enumerate(raw_local_levels):
                if not isinstance(raw_level, int):
                    raise ValueError(
                        f"framework_groups[{idx}].local_levels[{level_idx}] must be an integer"
                    )
                local_levels.append(raw_level)

            raw_level_node_counts = _expect_dict(
                group_obj.get("level_node_counts"),
                f"framework_groups[{idx}].level_node_counts",
            )
            level_node_counts: dict[int, int] = {}
            for raw_key, raw_count in raw_level_node_counts.items():
                if not isinstance(raw_key, str) or not raw_key.isdigit():
                    raise ValueError(
                        f"framework_groups[{idx}].level_node_counts keys must be digit strings"
                    )
                if not isinstance(raw_count, int):
                    raise ValueError(
                        f"framework_groups[{idx}].level_node_counts[{raw_key}] must be an integer"
                    )
                level_node_counts[int(raw_key)] = raw_count

            framework_groups.append(
                HierarchyFrameworkGroup(
                    name=name,
                    order=order,
                    local_levels=local_levels,
                    level_node_counts=level_node_counts,
                )
            )

    _validate_acyclic(nodes, edges)

    return HierarchyGraph(
        title=title,
        description=description,
        level_labels=level_labels,
        nodes=nodes,
        edges=edges,
        layout_mode=layout_mode,
        framework_groups=framework_groups,
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


def _compute_global_level_layout(
    graph: HierarchyGraph,
    width: int,
    height: int,
) -> LayoutResult:
    level_to_nodes: dict[int, list[HierarchyNode]] = {}
    for node in graph.nodes:
        level_to_nodes.setdefault(node.level, []).append(node)

    levels = sorted(level_to_nodes)
    if not levels:
        return LayoutResult(positions={}, width=width, height=height)

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

    return LayoutResult(positions=positions, width=width, height=height)


def _compute_framework_columns_layout(
    graph: HierarchyGraph,
    width: int,
    height: int,
) -> LayoutResult:
    if not graph.nodes:
        return LayoutResult(positions={}, width=width, height=height)

    framework_groups = sorted(
        graph.framework_groups or [],
        key=lambda item: (item.order, item.name),
    )
    if not framework_groups:
        return _compute_global_level_layout(graph, width=width, height=height)

    node_by_id = {node.node_id: node for node in graph.nodes}
    node_ids_by_framework: dict[str, list[str]] = {}
    for node in graph.nodes:
        framework_name = str((node.metadata or {}).get("module_name") or "")
        if not framework_name:
            continue
        node_ids_by_framework.setdefault(framework_name, []).append(node.node_id)

    incoming: dict[str, list[str]] = {node.node_id: [] for node in graph.nodes}
    outgoing: dict[str, list[str]] = {node.node_id: [] for node in graph.nodes}
    for edge in graph.edges:
        incoming[edge.target].append(edge.source)
        outgoing[edge.source].append(edge.target)

    group_min_width = 236.0
    group_gap = 44.0
    group_padding_left = 52.0
    group_padding_right = 40.0
    left_margin = 40.0
    right_margin = 28.0
    top_margin = 118.0
    bottom_margin = 72.0
    level_gap = 164.0

    positions: dict[str, tuple[float, float]] = {}
    max_required_height = 0.0
    cursor_x = left_margin

    for group in framework_groups:
        group_node_ids = node_ids_by_framework.get(group.name, [])
        if not group_node_ids:
            cursor_x += group_min_width + group_gap
            continue

        level_orders: dict[int, list[str]] = {}
        for local_level in sorted(group.local_levels):
            row_ids = [
                node_id
                for node_id in group_node_ids
                if node_by_id[node_id].level == local_level
            ]
            if not row_ids:
                continue
            ordered_row = sorted(
                row_ids,
                key=lambda item: (
                    node_by_id[item].order is None,
                    node_by_id[item].order if node_by_id[item].order is not None else 0,
                    item,
                ),
            )
            level_orders[local_level] = ordered_row

        local_levels = sorted(level_orders)
        if not local_levels:
            continue

        _refine_level_orders(
            levels=local_levels,
            level_orders=level_orders,
            node_by_id=node_by_id,
            incoming=incoming,
            outgoing=outgoing,
        )

        max_row_count = max(len(level_orders[level]) for level in local_levels)
        usable_width = max(group_min_width - group_padding_left - group_padding_right, 1.0)
        if max_row_count > 1:
            min_cell = 96.0
            usable_width = max(usable_width, float(max_row_count + 1) * min_cell)
        group_width = max(group_min_width, usable_width + group_padding_left + group_padding_right)

        group_height = top_margin + bottom_margin + (len(local_levels) - 1) * level_gap
        max_required_height = max(
            max_required_height,
            group_height,
        )

        for level_idx, local_level in enumerate(local_levels):
            row_ids = level_orders[local_level]
            count = len(row_ids)
            row_usable_width = max(1.0, group_width - group_padding_left - group_padding_right)
            if count == 1:
                xs = [cursor_x + group_width / 2.0]
            else:
                cell = row_usable_width / float(count + 1)
                xs = [cursor_x + group_padding_left + cell * float(i + 1) for i in range(count)]

            y = top_margin + level_idx * level_gap
            for node_id, x in zip(row_ids, xs):
                positions[node_id] = (x, y)

        cursor_x += group_width + group_gap

    layout_width = int(max(width, round(cursor_x - group_gap + right_margin)))
    layout_height = int(max(620, round(max_required_height)))
    return LayoutResult(positions=positions, width=layout_width, height=layout_height)


def compute_layout(graph: HierarchyGraph, width: int = 1520, height: int = 980) -> LayoutResult:
    if graph.layout_mode == "framework_columns":
        return _compute_framework_columns_layout(graph, width=width, height=height)
    return _compute_global_level_layout(graph, width=width, height=height)


def _build_payload(
    graph: HierarchyGraph,
    layout: LayoutResult,
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
        x, y = layout.positions[node.node_id]
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
        "width": layout.width,
        "height": layout.height,
        "nodes": nodes_payload,
        "edges": edges_payload,
        "level_labels": {
            str(level): graph.level_labels.get(level, f"层级 {level}") for level in level_values
        },
        "level_node_counts": {str(level): level_to_node_count.get(level, 0) for level in level_values},
        "relation_counts": relation_counts,
        "layout_mode": graph.layout_mode,
        "framework_groups": [
            {
                "name": group.name,
                "order": group.order,
                "local_levels": group.local_levels,
                "level_node_counts": {
                    str(level): count for level, count in sorted(group.level_node_counts.items())
                },
            }
            for group in sorted(graph.framework_groups or [], key=lambda item: (item.order, item.name))
        ],
    }


def render_html(graph: HierarchyGraph, output_path: Path, width: int = 1520, height: int = 980) -> None:
    layout = compute_layout(graph, width=width, height=height)
    payload = _build_payload(graph, layout)
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
      --graph-edge: rgba(176, 192, 210, 0.72);
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
      --graph-edge: rgba(74, 98, 128, 0.62);
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

    .graph-toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 10px;
      flex-wrap: wrap;
    }

    .toolbar-tail {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }

    .zoom-controls {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
    }

    .zoom-btn {
      width: auto;
      min-width: 36px;
      min-height: 28px;
      padding: 0 10px;
      text-align: center;
      border-radius: 999px;
    }

    .zoom-indicator {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 58px;
      min-height: 28px;
      padding: 0 10px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: var(--card-muted);
      color: var(--text);
      font-size: 11px;
      font-weight: 600;
    }

    .graph-hint {
      color: var(--sub);
      font-size: 11px;
      line-height: 1.45;
      white-space: nowrap;
    }

    .graph-scroll {
      overflow: auto;
      max-height: min(76vh, 980px);
      border: 1px solid var(--border);
      border-radius: 12px;
      background: var(--graph-stage);
      cursor: grab;
      touch-action: none;
    }

    .graph-scroll.dragging {
      cursor: grabbing;
    }

    .graph-stage {
      width: max-content;
      min-width: 100%;
      padding: 14px;
      user-select: none;
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

    .layout.side-collapsed {
      grid-template-columns: minmax(0, 1fr);
    }

    .layout.side-collapsed .side {
      display: none;
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

    .framework-panel {
      fill: rgba(255, 255, 255, 0.018);
      stroke: var(--border);
      stroke-width: 1;
    }

    .framework-panel.alt {
      fill: rgba(255, 255, 255, 0.028);
    }

    .framework-title {
      font-size: 12px;
      fill: var(--text);
      font-weight: 700;
      letter-spacing: 0.03em;
      text-transform: uppercase;
      pointer-events: none;
    }

    .framework-kicker {
      font-size: 10px;
      fill: var(--sub);
      font-weight: 600;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      pointer-events: none;
    }

    .framework-summary {
      font-size: 10px;
      fill: var(--sub);
      font-weight: 500;
      letter-spacing: 0.02em;
      pointer-events: none;
    }

    .framework-handle {
      fill: rgba(255, 255, 255, 0.001);
      pointer-events: all;
      cursor: grab;
    }

    .framework-toggle-surface {
      fill: var(--button-bg);
      stroke: var(--border);
      stroke-width: 1;
      cursor: pointer;
    }

    .framework-toggle-surface:hover {
      fill: var(--button-bg-hover);
    }

    .framework-toggle-label {
      font-size: 10px;
      fill: var(--text);
      font-weight: 600;
      letter-spacing: 0.04em;
      pointer-events: none;
      text-anchor: middle;
      dominant-baseline: central;
    }

    .edge {
      fill: none;
      stroke: var(--graph-edge);
      stroke-width: 2.15;
      stroke-linecap: round;
      stroke-linejoin: round;
      marker-end: url(#arrowDefault);
      opacity: 0.94;
      pointer-events: none;
      vector-effect: non-scaling-stroke;
      transition: opacity 140ms ease, stroke 140ms ease, stroke-width 140ms ease;
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

    .edge-hit-area {
      fill: none;
      stroke: transparent;
      stroke-width: 14;
      stroke-linecap: round;
      stroke-linejoin: round;
      pointer-events: stroke;
      cursor: pointer;
      vector-effect: non-scaling-stroke;
    }

    .arrow-default {
      fill: var(--graph-edge);
    }

    .arrow-active {
      fill: var(--graph-edge-active);
    }

    .node-group {
      cursor: pointer;
    }

    .node-hit-area {
      fill: transparent;
      pointer-events: all;
      cursor: pointer;
    }

    .node-circle {
      fill: var(--node-fill, var(--graph-node-active));
      stroke: var(--canvas);
      stroke-width: 2.4;
      pointer-events: none;
      transform-box: fill-box;
      transition:
        transform 140ms ease,
        opacity 140ms ease,
        filter 140ms ease,
        stroke 140ms ease,
        stroke-width 140ms ease;
      transform-origin: center center;
    }

    .node-group.hovered .node-circle {
      transform: scale(1.05);
      stroke: rgba(198, 223, 255, 0.82);
      stroke-width: 2.9;
      filter: brightness(1.12) saturate(1.05) drop-shadow(0 0 10px rgba(55, 148, 255, 0.22));
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
      transition: opacity 120ms ease, fill 120ms ease;
    }

    .node-group.hovered .node-label {
      fill: var(--fg);
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
      transition: opacity 120ms ease, fill 120ms ease, stroke 120ms ease;
    }

    .node-group.hovered .node-label-box {
      fill: rgba(50, 83, 126, 0.84);
      stroke: rgba(136, 188, 255, 0.38);
    }

    .node-label-box.faded {
      opacity: 0.22;
    }

    .node-label-box.hidden {
      opacity: 0;
    }

    .node-hover {
      position: fixed;
      z-index: 50;
      max-width: 360px;
      padding: 12px;
      border: 1px solid var(--border);
      border-radius: 12px;
      background: color-mix(in srgb, var(--card) 92%, var(--bg) 8%);
      box-shadow: 0 18px 48px rgba(0, 0, 0, 0.28);
      pointer-events: none;
      opacity: 0;
      transform: translateY(4px);
      transition: opacity 90ms ease, transform 90ms ease;
    }

    .node-hover.visible {
      opacity: 1;
      transform: translateY(0);
    }

    .hover-kicker {
      margin: 0 0 6px;
      font-size: 10px;
      line-height: 1.45;
      letter-spacing: 0.08em;
      color: var(--sub);
      text-transform: uppercase;
    }

    .hover-title {
      margin: 0;
      font-size: 13px;
      line-height: 1.4;
      font-weight: 600;
      color: var(--text);
    }

    .hover-subtitle {
      margin: 4px 0 0;
      font-size: 11px;
      line-height: 1.5;
      color: var(--sub);
      overflow-wrap: anywhere;
    }

    .hover-grid {
      display: grid;
      gap: 10px;
      margin-top: 10px;
      padding-top: 10px;
      border-top: 1px solid var(--border);
    }

    .hover-section {
      display: grid;
      gap: 6px;
    }

    .hover-section-title {
      margin: 0;
      font-size: 10px;
      line-height: 1.45;
      letter-spacing: 0.07em;
      color: var(--sub);
      text-transform: uppercase;
    }

    .hover-list {
      margin: 0;
      padding-left: 16px;
      display: grid;
      gap: 4px;
    }

    .hover-item {
      margin: 0;
      font-size: 11px;
      line-height: 1.5;
      color: var(--text);
      overflow-wrap: anywhere;
    }

    .hover-footer {
      margin-top: 10px;
      padding-top: 10px;
      border-top: 1px solid var(--border);
      font-size: 10px;
      line-height: 1.45;
      color: var(--sub);
      overflow-wrap: anywhere;
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
        <span class=\"pill\">点击节点或连线查看关系</span>
      </div>
      <div class=\"graph-shell\">
        <div class=\"graph-toolbar\">
          <div class=\"zoom-controls\">
            <button type=\"button\" class=\"zoom-btn\" data-zoom=\"out\" aria-label=\"缩小\">-</button>
            <button type=\"button\" class=\"zoom-btn\" data-zoom=\"reset\">100%</button>
            <button type=\"button\" class=\"zoom-btn\" data-zoom=\"fit\">适配</button>
            <button type=\"button\" class=\"zoom-btn\" data-zoom=\"in\" aria-label=\"放大\">+</button>
            <span class=\"zoom-indicator\" id=\"zoomIndicator\">100%</span>
          </div>
          <div class=\"toolbar-tail\">
            <button type=\"button\" class=\"zoom-btn\" id=\"resetLayoutButton\">恢复布局</button>
            <button type=\"button\" class=\"zoom-btn\" id=\"sideToggleButton\" aria-expanded=\"true\">隐藏侧栏</button>
            <span class=\"graph-hint\">左键拖动画布，拖动框标题移动 framework，点击框右上角折叠/展开，Ctrl/⌘ + 滚轮缩放，Ctrl/⌘ + 点击节点或连线打开来源文档</span>
          </div>
        </div>
        <div class=\"graph-scroll\">
          <div class=\"graph-stage\">
            <svg id=\"graphSvg\" role=\"img\" aria-label=\"M hierarchy graph\"></svg>
          </div>
        </div>
      </div>
      <p class=\"foot\" id=\"graphFoot\">图中只展示 M 结构层级与组合关系，不包含代码规范与框架规范条目。</p>
    </section>

    <aside class=\"side\">
      <section class=\"card info-card\">
        <h2 class=\"info-title\" id=\"levelStatsTitle\">层级统计</h2>
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

  <div id=\"nodeHover\" class=\"node-hover\" aria-hidden=\"true\"></div>

  <script>
    const graphData = __PAYLOAD_JSON__;
    const SVG_NS = "http://www.w3.org/2000/svg";
    const vscodeApi = typeof acquireVsCodeApi === "function" ? acquireVsCodeApi() : null;
    const SIDE_VISIBILITY_KEY = "archsync.frameworkTree.sideVisible";

    const layoutEl = document.querySelector(".layout");
    const graphCardEl = document.querySelector(".graph-card");
    const sideEl = document.querySelector(".side");
    const svg = document.getElementById("graphSvg");
    const graphScrollEl = document.querySelector(".graph-scroll");
    const titleEl = document.getElementById("title");
    const descriptionEl = document.getElementById("description");
    const summaryNodesEl = document.getElementById("summaryNodes");
    const summaryEdgesEl = document.getElementById("summaryEdges");
    const summaryFanEl = document.getElementById("summaryFan");
    const toggleLabelsEl = document.getElementById("toggleLabels");
    const zoomIndicatorEl = document.getElementById("zoomIndicator");
    const sideToggleButtonEl = document.getElementById("sideToggleButton");
    const levelStatsEl = document.getElementById("levelStats");
    const relationStatsEl = document.getElementById("relationStats");
    const detailBoxEl = document.getElementById("detailBox");
    const hoverCardEl = document.getElementById("nodeHover");
    const zoomButtons = Array.from(document.querySelectorAll("[data-zoom]"));
    const levelStatsTitleEl = document.getElementById("levelStatsTitle");
    const graphFootEl = document.getElementById("graphFoot");
    const resetLayoutButtonEl = document.getElementById("resetLayoutButton");

    const layoutMode = graphData.layout_mode || "global_levels";
    const isFrameworkColumns = layoutMode === "framework_columns";
    const frameworkGroups = Array.isArray(graphData.framework_groups)
      ? [...graphData.framework_groups].sort((a, b) => {
          const orderDelta = Number(a?.order ?? 0) - Number(b?.order ?? 0);
          if (orderDelta !== 0) {
            return orderDelta;
          }
          return String(a?.name || "").localeCompare(String(b?.name || ""));
        })
      : [];

    const BASE_WIDTH = graphData.width;
    const BASE_HEIGHT = graphData.height;
    const MIN_ZOOM = 0.45;
    const MAX_ZOOM = 2.4;
    const ZOOM_STEP = 1.15;
    const DRAG_THRESHOLD = 4;
    const NODE_RADIUS = 24;
    const EDGE_START_PADDING = NODE_RADIUS + 2;
    const EDGE_END_PADDING = NODE_RADIUS + 1;
    let zoomLevel = 1;
    let sideVisible = true;
    let selectedNodeId = null;
    let selectedEdgeKey = null;
    let canvasWidth = graphData.width;
    let canvasHeight = graphData.height;
    const panState = {
      active: false,
      pointerId: null,
      startClientX: 0,
      startClientY: 0,
      startScrollLeft: 0,
      startScrollTop: 0,
      captured: false,
      moved: false,
      suppressClick: false
    };
    const groupDragState = {
      active: false,
      pointerId: null,
      frameworkName: "",
      startClientX: 0,
      startClientY: 0,
      startDx: 0,
      startDy: 0,
      moved: false,
      suppressClick: false
    };

    function readStoredBool(key, fallbackValue) {
      try {
        const raw = window.localStorage.getItem(key);
        if (raw === null) {
          return fallbackValue;
        }
        return raw === "1";
      } catch {
        return fallbackValue;
      }
    }

    function writeStoredBool(key, value) {
      try {
        window.localStorage.setItem(key, value ? "1" : "0");
      } catch {}
    }

    function renderSideVisibility() {
      const isNarrowLayout = typeof window.matchMedia === "function"
        ? window.matchMedia("(max-width: 1220px)").matches
        : window.innerWidth <= 1220;
      if (layoutEl) {
        layoutEl.classList.toggle("side-collapsed", !sideVisible);
        layoutEl.style.gridTemplateColumns = sideVisible
          ? (isNarrowLayout ? "1fr" : "minmax(0, 1fr) minmax(300px, 320px)")
          : "minmax(0, 1fr)";
      }
      if (graphCardEl) {
        graphCardEl.style.gridColumn = sideVisible ? "" : "1 / -1";
      }
      if (sideEl) {
        sideEl.style.display = sideVisible ? "grid" : "none";
      }
      if (sideToggleButtonEl) {
        sideToggleButtonEl.textContent = sideVisible ? "隐藏侧栏" : "显示侧栏";
        sideToggleButtonEl.setAttribute("aria-expanded", String(sideVisible));
      }
    }

    function hideNodeHover() {
      if (!hoverCardEl) {
        return;
      }
      hoverCardEl.classList.remove("visible");
      hoverCardEl.setAttribute("aria-hidden", "true");
    }

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
    if (levelStatsTitleEl) {
      levelStatsTitleEl.textContent = isFrameworkColumns ? "框架层级统计" : "层级统计";
    }
    if (graphFootEl && isFrameworkColumns) {
      graphFootEl.textContent = "图中按 framework 分组展示 M 模块关系；每个分组内部保留自己的本地 Lx 层。";
    }

    svg.setAttribute("viewBox", `0 0 ${graphData.width} ${graphData.height}`);
    svg.setAttribute("width", String(graphData.width));
    svg.setAttribute("height", String(graphData.height));

    function clampZoom(value) {
      return Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, value));
    }

    function renderZoom() {
      const scaledWidth = Math.round(canvasWidth * zoomLevel);
      const scaledHeight = Math.round(canvasHeight * zoomLevel);
      svg.style.width = `${scaledWidth}px`;
      svg.style.height = `${scaledHeight}px`;
      if (zoomIndicatorEl) {
        zoomIndicatorEl.textContent = `${Math.round(zoomLevel * 100)}%`;
      }
    }

    function computeFitZoom() {
      if (!graphScrollEl) {
        return 1;
      }
      const horizontalPadding = 36;
      const verticalPadding = 36;
      const widthScale = Math.max(0.1, (graphScrollEl.clientWidth - horizontalPadding) / canvasWidth);
      const heightScale = Math.max(0.1, (graphScrollEl.clientHeight - verticalPadding) / canvasHeight);
      return clampZoom(Math.min(widthScale, heightScale));
    }

    function zoomTo(nextZoom, options = {}) {
      if (!graphScrollEl) {
        zoomLevel = clampZoom(nextZoom);
        renderZoom();
        return;
      }

      const targetZoom = clampZoom(nextZoom);
      if (Math.abs(targetZoom - zoomLevel) < 0.001) {
        return;
      }

      const preserveCenter = options.preserveCenter !== false;
      const graphCenterX = preserveCenter
        ? (graphScrollEl.scrollLeft + graphScrollEl.clientWidth / 2) / zoomLevel
        : 0;
      const graphCenterY = preserveCenter
        ? (graphScrollEl.scrollTop + graphScrollEl.clientHeight / 2) / zoomLevel
        : 0;

      zoomLevel = targetZoom;
      renderZoom();

      if (preserveCenter) {
        graphScrollEl.scrollLeft = graphCenterX * zoomLevel - graphScrollEl.clientWidth / 2;
        graphScrollEl.scrollTop = graphCenterY * zoomLevel - graphScrollEl.clientHeight / 2;
      } else {
        graphScrollEl.scrollLeft = 0;
        graphScrollEl.scrollTop = 0;
      }
    }

    function zoomAtPoint(nextZoom, clientX, clientY) {
      if (!graphScrollEl) {
        zoomTo(nextZoom);
        return;
      }

      const targetZoom = clampZoom(nextZoom);
      if (Math.abs(targetZoom - zoomLevel) < 0.001) {
        return;
      }

      const rect = graphScrollEl.getBoundingClientRect();
      const offsetX = clientX - rect.left;
      const offsetY = clientY - rect.top;
      const graphX = (graphScrollEl.scrollLeft + offsetX) / zoomLevel;
      const graphY = (graphScrollEl.scrollTop + offsetY) / zoomLevel;

      zoomLevel = targetZoom;
      renderZoom();

      graphScrollEl.scrollLeft = graphX * zoomLevel - offsetX;
      graphScrollEl.scrollTop = graphY * zoomLevel - offsetY;
    }

    function initializeZoom() {
      const fitZoom = computeFitZoom();
      zoomLevel = fitZoom < 0.78 ? 0.78 : fitZoom;
      zoomLevel = clampZoom(zoomLevel);
      renderZoom();
      if (graphScrollEl) {
        graphScrollEl.scrollLeft = 0;
        graphScrollEl.scrollTop = 0;
      }
    }

    // Interaction contract:
    // - the whole graph surface can start a pan gesture
    // - node / edge click keeps relationship selection working until drag threshold is crossed
    // - framework header / toggle interactions stay isolated from canvas pan
    function shouldIgnorePanStart(target) {
      if (!target || typeof target.closest !== "function") {
        return false;
      }
      return Boolean(target.closest("button, input, label, a, [data-pan-ignore='1']"));
    }

    function safeSetPointerCapture(element, pointerId) {
      if (!element || typeof element.setPointerCapture !== "function") {
        return false;
      }
      try {
        element.setPointerCapture(pointerId);
        return true;
      } catch (_error) {
        return false;
      }
    }

    function safeReleasePointerCapture(element, pointerId) {
      if (
        !element ||
        typeof element.releasePointerCapture !== "function" ||
        typeof element.hasPointerCapture !== "function" ||
        pointerId === null
      ) {
        return;
      }
      try {
        if (element.hasPointerCapture(pointerId)) {
          element.releasePointerCapture(pointerId);
        }
      } catch (_error) {
        // Ignore capture teardown failures so drag cleanup still completes.
      }
    }

    function beginPan(event) {
      if (!graphScrollEl || panState.active || event.button !== 0) {
        return;
      }
      if (!graphScrollEl.contains(event.target)) {
        return;
      }
      if (shouldIgnorePanStart(event.target)) {
        return;
      }
      panState.active = true;
      panState.pointerId = event.pointerId;
      panState.startClientX = event.clientX;
      panState.startClientY = event.clientY;
      panState.startScrollLeft = graphScrollEl.scrollLeft;
      panState.startScrollTop = graphScrollEl.scrollTop;
      panState.captured = false;
      panState.moved = false;
      hideNodeHover();
    }

    function updatePan(event) {
      if (!graphScrollEl || !panState.active || event.pointerId !== panState.pointerId) {
        return;
      }
      const dx = event.clientX - panState.startClientX;
      const dy = event.clientY - panState.startClientY;
      if (!panState.moved && Math.hypot(dx, dy) >= DRAG_THRESHOLD) {
        panState.moved = true;
        panState.suppressClick = true;
        if (typeof event.preventDefault === "function") {
          event.preventDefault();
        }
        graphScrollEl.classList.add("dragging");
        panState.captured = safeSetPointerCapture(graphScrollEl, event.pointerId);
      }
      if (!panState.moved) {
        return;
      }
      graphScrollEl.scrollLeft = panState.startScrollLeft - dx;
      graphScrollEl.scrollTop = panState.startScrollTop - dy;
    }

    function endPan(event) {
      if (!graphScrollEl || !panState.active) {
        return;
      }
      if (event && event.pointerId !== undefined && event.pointerId !== panState.pointerId) {
        return;
      }
      if (panState.captured) {
        safeReleasePointerCapture(graphScrollEl, panState.pointerId);
      }
      panState.active = false;
      panState.pointerId = null;
      panState.captured = false;
      graphScrollEl.classList.remove("dragging");
      window.setTimeout(() => {
        panState.suppressClick = false;
      }, 0);
    }

    function beginGroupDrag(event, frameworkName) {
      if (event.button !== 0) {
        return;
      }
      event.stopPropagation();
      hideNodeHover();
      const current = groupState.get(frameworkName);
      if (!current) {
        return;
      }
      groupDragState.active = true;
      groupDragState.pointerId = event.pointerId;
      groupDragState.frameworkName = frameworkName;
      groupDragState.startClientX = event.clientX;
      groupDragState.startClientY = event.clientY;
      groupDragState.startDx = current.dx;
      groupDragState.startDy = current.dy;
      groupDragState.moved = false;
      safeSetPointerCapture(svg, event.pointerId);
    }

    function endGroupDrag(event) {
      if (!groupDragState.active) {
        return;
      }
      if (event && event.pointerId !== undefined && event.pointerId !== groupDragState.pointerId) {
        return;
      }
      safeReleasePointerCapture(svg, groupDragState.pointerId);
      groupDragState.active = false;
      groupDragState.pointerId = null;
      groupDragState.frameworkName = "";
      window.setTimeout(() => {
        groupDragState.suppressClick = false;
      }, 0);
    }

    const graphEdges = graphData.edges.map((edge, index) => ({
      ...edge,
      __edgeKey: [
        String(edge.from ?? ""),
        String(edge.to ?? ""),
        String(edge.relation ?? ""),
        String(edge.source_file ?? ""),
        String(edge.source_line ?? ""),
        String(index)
      ].join("::")
    }));

    summaryEdgesEl.textContent = `关系边: ${graphEdges.length}`;

    const byId = new Map(graphData.nodes.map((node) => [node.id, node]));
    const incoming = new Map(graphData.nodes.map((node) => [node.id, []]));
    const outgoing = new Map(graphData.nodes.map((node) => [node.id, []]));

    for (const edge of graphEdges) {
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

    const fallbackFrameworkGroups = Array.from(
      new Set(
        graphData.nodes
          .map((node) => (typeof node.module_name === "string" ? node.module_name : ""))
          .filter(Boolean)
      )
    )
      .sort((a, b) => a.localeCompare(b))
      .map((name, order) => {
        const nodesInGroup = graphData.nodes.filter((node) => node.module_name === name);
        const localLevels = Array.from(new Set(nodesInGroup.map((node) => Number(node.level)))).sort(
          (a, b) => a - b
        );
        const levelNodeCounts = {};
        for (const level of localLevels) {
          levelNodeCounts[String(level)] = nodesInGroup.filter((node) => node.level === level).length;
        }
        return { name, order, local_levels: localLevels, level_node_counts: levelNodeCounts };
      });

    const activeFrameworkGroups = frameworkGroups.length ? frameworkGroups : fallbackFrameworkGroups;

    function formatFrameworkLevelSummary(group) {
      const rawLevels = Array.isArray(group?.local_levels)
        ? group.local_levels
        : Array.isArray(group?.localLevels)
          ? group.localLevels
          : [];
      const localLevels = rawLevels
        .map((value) => Number(value))
        .filter((value) => Number.isFinite(value));
      if (!localLevels.length) {
        return "无节点";
      }
      const counts = group?.level_node_counts ?? group?.levelNodeCounts ?? {};
      return localLevels
        .sort((a, b) => a - b)
        .map((level) => `L${level} ${counts[String(level)] ?? 0}`)
        .join(" | ");
    }

    const frameworkDescriptors = activeFrameworkGroups
      .map((group) => {
        const nodesInGroup = graphData.nodes.filter((node) => node.module_name === group.name);
        if (!nodesInGroup.length) {
          return null;
        }
        const localLevels = Array.isArray(group?.local_levels)
          ? group.local_levels.map((value) => Number(value)).filter((value) => Number.isFinite(value))
          : Array.from(new Set(nodesInGroup.map((node) => Number(node.level))));
        const sortedLevels = localLevels.sort((a, b) => a - b);
        const levelCenters = new Map();
        for (const level of sortedLevels) {
          const nodesInLevel = nodesInGroup.filter((node) => Number(node.level) === level);
          if (!nodesInLevel.length) {
            continue;
          }
          const avgY =
            nodesInLevel.reduce((sum, node) => sum + Number(node.y), 0) / Math.max(1, nodesInLevel.length);
          levelCenters.set(level, avgY);
        }
        const xs = nodesInGroup.map((node) => Number(node.x));
        const minX = Math.min(...xs);
        const maxX = Math.max(...xs);
        return {
          name: String(group.name),
          order: Number(group.order ?? 0),
          levelNodeCounts: group.level_node_counts ?? {},
          localLevels: sortedLevels,
          levelCenters,
          nodes: nodesInGroup,
          minX,
          maxX,
          centerX: (minX + maxX) / 2
        };
      })
      .filter(Boolean)
      .sort((a, b) => {
        const orderDelta = Number(a.order) - Number(b.order);
        if (orderDelta !== 0) {
          return orderDelta;
        }
        return String(a.name).localeCompare(String(b.name));
      });

    for (let index = 0; index < frameworkDescriptors.length; index += 1) {
      const group = frameworkDescriptors[index];
      const prevGroup = index > 0 ? frameworkDescriptors[index - 1] : null;
      const nextGroup = index < frameworkDescriptors.length - 1 ? frameworkDescriptors[index + 1] : null;
      const panelLeft = prevGroup ? (prevGroup.maxX + group.minX) / 2 : Math.max(16, group.minX - 56);
      const panelRight = nextGroup
        ? (group.maxX + nextGroup.minX) / 2
        : Math.min(graphData.width - 16, group.maxX + 56);
      group.panelLeft = panelLeft;
      group.panelRight = panelRight;
      group.panelTop = 18;
      group.panelBottom = graphData.height - 18;
      group.panelWidth = Math.max(1, panelRight - panelLeft);
      group.panelHeight = Math.max(1, group.panelBottom - group.panelTop);
      group.bandTopFloor = group.panelTop + 52;
      group.bandBottomCeil = group.panelBottom - 12;
    }

    const frameworkByNodeId = new Map(
      graphData.nodes.map((node) => [node.id, typeof node.module_name === "string" ? node.module_name : ""])
    );
    const descriptorByName = new Map(frameworkDescriptors.map((group) => [group.name, group]));
    const groupState = new Map(
      frameworkDescriptors.map((group) => [group.name, { dx: 0, dy: 0, collapsed: false }])
    );

    if (isFrameworkColumns) {
      for (const group of frameworkDescriptors) {
        appendStatRow(levelStatsEl, String(group.name), formatFrameworkLevelSummary(group));
      }
    } else {
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
    }

    for (const [relation, count] of Object.entries(graphData.relation_counts ?? {})) {
      appendStatRow(relationStatsEl, relation, String(count));
    }

    if (!relationStatsEl.children.length) {
      appendStatRow(relationStatsEl, "状态", "无关系类型统计");
    }

    const defs = document.createElementNS(SVG_NS, "defs");
    defs.innerHTML = `
      <marker id=\"arrowDefault\" markerWidth=\"12\" markerHeight=\"12\" viewBox=\"0 0 12 9\" refX=\"10.5\" refY=\"4.5\" orient=\"auto\" markerUnits=\"userSpaceOnUse\">
        <path class=\"arrow-default\" d=\"M0,0 L0,9 L12,4.5 z\"></path>
      </marker>
      <marker id=\"arrowActive\" markerWidth=\"12\" markerHeight=\"12\" viewBox=\"0 0 12 9\" refX=\"10.5\" refY=\"4.5\" orient=\"auto\" markerUnits=\"userSpaceOnUse\">
        <path class=\"arrow-active\" d=\"M0,0 L0,9 L12,4.5 z\"></path>
      </marker>
    `;

    function edgeEndpoints(fromNode, toNode) {
      const dx = toNode.x - fromNode.x;
      const dy = toNode.y - fromNode.y;
      const distance = Math.max(1, Math.hypot(dx, dy));
      const ux = dx / distance;
      const uy = dy / distance;
      const maxPad = Math.max(0, distance / 2 - 6);
      const startPad = Math.min(EDGE_START_PADDING, maxPad);
      const endPad = Math.min(EDGE_END_PADDING, maxPad);
      return {
        startX: fromNode.x + ux * startPad,
        startY: fromNode.y + uy * startPad,
        endX: toNode.x - ux * endPad,
        endY: toNode.y - uy * endPad
      };
    }

    function edgePath(fromNode, toNode) {
      const endpoints = edgeEndpoints(fromNode, toNode);
      const dx = endpoints.endX - endpoints.startX;
      const dy = endpoints.endY - endpoints.startY;
      const curve = Math.max(44, Math.min(136, Math.abs(dy) * 0.44));
      const sidePull =
        dx === 0 ? 0 : Math.sign(dx) * Math.max(26, Math.min(116, Math.abs(dx) * 0.28));
      const c1x = endpoints.startX + sidePull;
      const c1y = endpoints.startY + curve;
      const c2x = endpoints.endX - sidePull;
      const c2y = endpoints.endY - curve;
      return `M ${endpoints.startX} ${endpoints.startY} C ${c1x} ${c1y}, ${c2x} ${c2y}, ${endpoints.endX} ${endpoints.endY}`;
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

    let edgeElements = [];
    let edgeElementMap = new Map();
    let nodeCircleMap = new Map();
    let nodeLabelMap = new Map();
    let nodeLabelBoxMap = new Map();
    let nodeGroupMap = new Map();
    let currentNodeSnapshots = new Map();

    function getCollapsedMetrics(group) {
      return {
        width: Math.max(208, Math.min(252, Math.round(group.panelWidth))),
        height: 86
      };
    }

    function clampGroupOffset(group, desiredDx, desiredDy, collapsed) {
      const metrics = collapsed ? getCollapsedMetrics(group) : { width: group.panelWidth, height: group.panelHeight };
      const minDx = 20 - group.panelLeft;
      const maxDx = Math.max(minDx, graphData.width - metrics.width - group.panelLeft - 20);
      const minDy = 20 - group.panelTop;
      const maxDy = Math.max(minDy, graphData.height - metrics.height - group.panelTop - 20);
      return {
        dx: Math.min(maxDx, Math.max(minDx, desiredDx)),
        dy: Math.min(maxDy, Math.max(minDy, desiredDy))
      };
    }

    function getGroupLayout(group) {
      const state = groupState.get(group.name) ?? { dx: 0, dy: 0, collapsed: false };
      if (state.collapsed) {
        const metrics = getCollapsedMetrics(group);
        const left = group.panelLeft + state.dx;
        const top = group.panelTop + state.dy;
        return {
          left,
          top,
          right: left + metrics.width,
          bottom: top + metrics.height,
          width: metrics.width,
          height: metrics.height,
          collapsed: true,
          anchorX: left + metrics.width / 2,
          anchorY: top + metrics.height / 2 + 4,
          headerTop: top,
          headerBottom: top + 42
        };
      }
      return {
        left: group.panelLeft + state.dx,
        top: group.panelTop + state.dy,
        right: group.panelRight + state.dx,
        bottom: group.panelBottom + state.dy,
        width: group.panelWidth,
        height: group.panelHeight,
        collapsed: false,
        anchorX: group.centerX + state.dx,
        anchorY: group.panelTop + state.dy + 38,
        headerTop: group.panelTop + state.dy,
        headerBottom: group.panelTop + state.dy + 44
      };
    }

    function buildNodeSnapshots() {
      const snapshots = new Map();
      for (const node of graphData.nodes) {
        const frameworkName = frameworkByNodeId.get(node.id);
        const group = frameworkName ? descriptorByName.get(frameworkName) : null;
        const state = frameworkName ? groupState.get(frameworkName) : null;
        if (group && state?.collapsed) {
          const layout = getGroupLayout(group);
          snapshots.set(node.id, {
            ...node,
            x: layout.anchorX,
            y: layout.anchorY,
            frameworkName,
            visible: false
          });
          continue;
        }
        snapshots.set(node.id, {
          ...node,
          x: node.x + Number(state?.dx ?? 0),
          y: node.y + Number(state?.dy ?? 0),
          frameworkName,
          visible: true
        });
      }
      return snapshots;
    }

    function appendFrameworkToggle(groupLayer, x, y, collapsed, frameworkName) {
      const surface = document.createElementNS(SVG_NS, "rect");
      surface.setAttribute("x", String(x));
      surface.setAttribute("y", String(y));
      surface.setAttribute("width", "48");
      surface.setAttribute("height", "22");
      surface.setAttribute("rx", "11");
      surface.setAttribute("ry", "11");
      surface.setAttribute("class", "framework-toggle-surface");
      surface.setAttribute("data-framework-toggle", "1");
      surface.setAttribute("data-pan-ignore", "1");
      groupLayer.appendChild(surface);

      const label = document.createElementNS(SVG_NS, "text");
      label.setAttribute("x", String(x + 24));
      label.setAttribute("y", String(y + 12));
      label.setAttribute("class", "framework-toggle-label");
      label.textContent = collapsed ? "展开" : "折叠";
      groupLayer.appendChild(label);

      const toggle = (event) => {
        event.stopPropagation();
        const current = groupState.get(frameworkName);
        if (!current) {
          return;
        }
        groupState.set(frameworkName, { ...current, collapsed: !current.collapsed });
        if (selectedNodeId) {
          const selectedFramework = frameworkByNodeId.get(selectedNodeId);
          if (selectedFramework === frameworkName && !current.collapsed) {
            selectedNodeId = null;
          }
        }
        renderGraph();
      };

      surface.addEventListener("click", toggle);
      label.addEventListener("click", toggle);
    }

    function renderGlobalLevelBands() {
      const levelCenters = new Map();
      for (const [level] of levelEntries) {
        const nodesInLevel = graphData.nodes.filter((node) => node.level === level);
        const avgY =
          nodesInLevel.reduce((sum, node) => sum + node.y, 0) / Math.max(1, nodesInLevel.length);
        levelCenters.set(level, avgY);
      }

      for (let index = 0; index < levelEntries.length; index += 1) {
        const [level, levelName] = levelEntries[index];
        const centerY = levelCenters.get(level) ?? 0;
        const prevCenter =
          index > 0 ? levelCenters.get(levelEntries[index - 1][0]) ?? centerY : centerY;
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
    }

    function renderFrameworkGroups() {
      for (let index = 0; index < frameworkDescriptors.length; index += 1) {
        const group = frameworkDescriptors[index];
        const layout = getGroupLayout(group);
        const groupLayer = document.createElementNS(SVG_NS, "g");
        groupLayer.setAttribute("data-framework-group", group.name);
        svg.appendChild(groupLayer);

        const panel = document.createElementNS(SVG_NS, "rect");
        panel.setAttribute("x", String(layout.left));
        panel.setAttribute("y", String(layout.top));
        panel.setAttribute("width", String(layout.width));
        panel.setAttribute("height", String(layout.height));
        panel.setAttribute("rx", "16");
        panel.setAttribute("ry", "16");
        panel.setAttribute("class", `framework-panel${index % 2 === 1 ? " alt" : ""}`);
        groupLayer.appendChild(panel);

        const handle = document.createElementNS(SVG_NS, "rect");
        handle.setAttribute("x", String(layout.left));
        handle.setAttribute("y", String(layout.headerTop));
        handle.setAttribute("width", String(layout.width));
        handle.setAttribute("height", String(Math.max(28, layout.headerBottom - layout.headerTop)));
        handle.setAttribute("class", "framework-handle");
        handle.setAttribute("data-framework-handle", "1");
        handle.setAttribute("data-pan-ignore", "1");
        handle.addEventListener("pointerdown", (event) => beginGroupDrag(event, group.name));
        handle.addEventListener("click", (event) => event.stopPropagation());
        groupLayer.appendChild(handle);

        const kicker = document.createElementNS(SVG_NS, "text");
        kicker.setAttribute("x", String(layout.left + 18));
        kicker.setAttribute("y", String(layout.top + 18));
        kicker.setAttribute("class", "framework-kicker");
        kicker.textContent = "framework";
        groupLayer.appendChild(kicker);

        const title = document.createElementNS(SVG_NS, "text");
        title.setAttribute("x", String(layout.left + 18));
        title.setAttribute("y", String(layout.top + 38));
        title.setAttribute("class", "framework-title");
        title.textContent = String(group.name);
        groupLayer.appendChild(title);

        appendFrameworkToggle(groupLayer, layout.right - 60, layout.top + 12, layout.collapsed, group.name);

        if (layout.collapsed) {
          const summary = document.createElementNS(SVG_NS, "text");
          summary.setAttribute("x", String(layout.left + 18));
          summary.setAttribute("y", String(layout.top + 62));
          summary.setAttribute("class", "framework-summary");
          summary.textContent = `${group.nodes.length} 模块 · ${formatFrameworkLevelSummary(group)}`;
          groupLayer.appendChild(summary);
          continue;
        }

        const localLevels = group.localLevels;
        for (let levelIndex = 0; levelIndex < localLevels.length; levelIndex += 1) {
          const level = localLevels[levelIndex];
          const defaultCenterY = group.levelCenters.get(level) ?? group.bandTopFloor;
          const centerY = defaultCenterY + (groupState.get(group.name)?.dy ?? 0);
          const prevCenter =
            levelIndex > 0
              ? (group.levelCenters.get(localLevels[levelIndex - 1]) ?? defaultCenterY) + (groupState.get(group.name)?.dy ?? 0)
              : centerY;
          const nextCenter =
            levelIndex < localLevels.length - 1
              ? (group.levelCenters.get(localLevels[levelIndex + 1]) ?? defaultCenterY) + (groupState.get(group.name)?.dy ?? 0)
              : centerY;
          const top = levelIndex === 0 ? group.bandTopFloor + (groupState.get(group.name)?.dy ?? 0) : (prevCenter + centerY) / 2;
          const bottom =
            levelIndex === localLevels.length - 1
              ? group.bandBottomCeil + (groupState.get(group.name)?.dy ?? 0)
              : (centerY + nextCenter) / 2;

          const band = document.createElementNS(SVG_NS, "rect");
          band.setAttribute("x", String(layout.left + 12));
          band.setAttribute("y", String(top));
          band.setAttribute("width", String(Math.max(1, layout.width - 24)));
          band.setAttribute("height", String(Math.max(1, bottom - top)));
          band.setAttribute("rx", "12");
          band.setAttribute("ry", "12");
          band.setAttribute("class", `level-band${levelIndex % 2 === 1 ? " alt" : ""}`);
          groupLayer.appendChild(band);

          const guide = document.createElementNS(SVG_NS, "line");
          guide.setAttribute("x1", String(layout.left + 18));
          guide.setAttribute("x2", String(layout.right - 18));
          guide.setAttribute("y1", String(centerY));
          guide.setAttribute("y2", String(centerY));
          guide.setAttribute("class", "level-guide");
          groupLayer.appendChild(guide);

          const label = document.createElementNS(SVG_NS, "text");
          label.setAttribute("x", String(layout.left + 20));
          label.setAttribute("y", String(top + 24));
          label.setAttribute("class", "level-label");
          label.textContent = graphData.level_labels[String(level)] ?? `L${level}`;
          groupLayer.appendChild(label);
        }
      }
    }

    function renderNodesAndEdges() {
      currentNodeSnapshots = buildNodeSnapshots();
      edgeElements = [];
      edgeElementMap = new Map();
      nodeCircleMap = new Map();
      nodeLabelMap = new Map();
      nodeLabelBoxMap = new Map();
      nodeGroupMap = new Map();

      for (const edge of graphEdges) {
        const fromNode = currentNodeSnapshots.get(edge.from);
        const toNode = currentNodeSnapshots.get(edge.to);
        if (!fromNode || !toNode) {
          continue;
        }
        if (!fromNode.visible && !toNode.visible && fromNode.frameworkName === toNode.frameworkName) {
          continue;
        }

        const edgeKey = edge.__edgeKey;
        const pathData = edgePath(fromNode, toNode);
        const path = document.createElementNS(SVG_NS, "path");
        path.setAttribute("d", pathData);
        path.setAttribute("class", "edge");
        path.setAttribute("data-edge-key", edgeKey);
        path.setAttribute("data-from", edge.from);
        path.setAttribute("data-to", edge.to);
        path.setAttribute("data-relation", edge.relation);
        const edgeRule = edge.rule ? `, rule=${edge.rule}` : "";
        const edgeConstraint = edge.constraint ? `, constraint=${edge.constraint}` : "";
        path.appendChild(document.createElementNS(SVG_NS, "title")).textContent = `${edge.from} -> ${edge.to} (${edge.relation}${edgeRule}${edgeConstraint})`;
        svg.appendChild(path);

        const hitArea = document.createElementNS(SVG_NS, "path");
        hitArea.setAttribute("d", pathData);
        hitArea.setAttribute("class", "edge-hit-area");
        hitArea.setAttribute("data-edge-hit", "1");
        hitArea.setAttribute("data-edge-key", edgeKey);
        hitArea.setAttribute("data-from", edge.from);
        hitArea.setAttribute("data-to", edge.to);
        hitArea.addEventListener("click", (event) => {
          if (panState.suppressClick || groupDragState.suppressClick) {
            event.stopPropagation();
            return;
          }
          event.stopPropagation();
          if ((event.ctrlKey || event.metaKey) && typeof edge.source_file === "string" && edge.source_file) {
            hideNodeHover();
            openSourceFile(edge.source_file, edge.source_line);
            return;
          }
          hideNodeHover();
          selectEdge(edgeKey);
        });
        svg.appendChild(hitArea);

        edgeElements.push(path);
        edgeElementMap.set(edgeKey, { edge, path, hitArea });
      }

      for (const node of graphData.nodes) {
        const snapshot = currentNodeSnapshots.get(node.id);
        if (!snapshot || !snapshot.visible) {
          continue;
        }

        const group = document.createElementNS(SVG_NS, "g");
        group.setAttribute("class", "node-group");
        group.setAttribute("data-node-group", "1");
        group.setAttribute("data-node-id", node.id);

        const circle = document.createElementNS(SVG_NS, "circle");
        circle.setAttribute("cx", String(snapshot.x));
        circle.setAttribute("cy", String(snapshot.y));
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
        label.setAttribute("x", String(snapshot.x));
        label.setAttribute("y", String(snapshot.y + 31));
        label.setAttribute("class", "node-label");
        label.textContent = node.label;
        group.appendChild(label);

        svg.appendChild(group);
        const bbox = label.getBBox();
        const padX = 7;
        const padY = 2;
        labelBox.setAttribute("x", String(bbox.x - padX));
        labelBox.setAttribute("y", String(bbox.y - padY));
        labelBox.setAttribute("width", String(Math.max(10, bbox.width + padX * 2)));
        labelBox.setAttribute("height", String(Math.max(10, bbox.height + padY * 2)));
        group.insertBefore(labelBox, label);

        const hitPadding = 10;
        const circleRadius = NODE_RADIUS;
        const minX = Math.min(snapshot.x - circleRadius - hitPadding, bbox.x - padX - hitPadding);
        const maxX = Math.max(snapshot.x + circleRadius + hitPadding, bbox.x + bbox.width + padX + hitPadding);
        const minY = Math.min(snapshot.y - circleRadius - hitPadding, bbox.y - padY - hitPadding);
        const maxY = Math.max(snapshot.y + circleRadius + hitPadding, bbox.y + bbox.height + padY + hitPadding);

        const hitArea = document.createElementNS(SVG_NS, "rect");
        hitArea.setAttribute("class", "node-hit-area");
        hitArea.setAttribute("data-node-hit", "1");
        hitArea.setAttribute("data-node-id", node.id);
        hitArea.setAttribute("x", String(minX));
        hitArea.setAttribute("y", String(minY));
        hitArea.setAttribute("width", String(Math.max(1, maxX - minX)));
        hitArea.setAttribute("height", String(Math.max(1, maxY - minY)));
        hitArea.setAttribute("rx", "14");
        hitArea.setAttribute("ry", "14");
        group.insertBefore(hitArea, circle);

        hitArea.addEventListener("click", (event) => {
          if (panState.suppressClick || groupDragState.suppressClick) {
            event.stopPropagation();
            return;
          }
          event.stopPropagation();
          const docLine =
            Number.isFinite(Number(node.doc_line)) && Number(node.doc_line) > 0
              ? Number(node.doc_line)
              : Number.isFinite(Number(node.source_line)) && Number(node.source_line) > 0
                ? Number(node.source_line)
                : 1;
          if ((event.ctrlKey || event.metaKey) && typeof node.source_file === "string" && node.source_file) {
            hideNodeHover();
            openSourceFile(node.source_file, docLine);
            return;
          }
          hideNodeHover();
          selectNode(node.id);
        });

        hitArea.addEventListener("mouseenter", (event) => {
          group.classList.add("hovered");
          showNodeHover(node, event.clientX, event.clientY);
        });

        hitArea.addEventListener("mousemove", (event) => {
          if (!hoverCardEl?.classList.contains("visible")) {
            showNodeHover(node, event.clientX, event.clientY);
            return;
          }
          positionHoverCard(event.clientX, event.clientY);
        });

        hitArea.addEventListener("mouseleave", () => {
          group.classList.remove("hovered");
          hideNodeHover();
        });

        nodeCircleMap.set(node.id, circle);
        nodeLabelMap.set(node.id, label);
        nodeLabelBoxMap.set(node.id, labelBox);
        nodeGroupMap.set(node.id, group);
      }
    }

    function renderGraph() {
      hideNodeHover();
      svg.replaceChildren();
      svg.appendChild(defs);
      canvasWidth = graphData.width;
      canvasHeight = graphData.height;
      svg.setAttribute("viewBox", `0 0 ${canvasWidth} ${canvasHeight}`);
      svg.setAttribute("width", String(canvasWidth));
      svg.setAttribute("height", String(canvasHeight));

      if (isFrameworkColumns) {
        renderFrameworkGroups();
      } else {
        renderGlobalLevelBands();
      }
      renderNodesAndEdges();
      applyThemeState();
      updateLabelVisibility();
      if (selectedNodeId && !currentNodeSnapshots.get(selectedNodeId)?.visible) {
        selectedNodeId = null;
      }
      if (selectedEdgeKey && !edgeElementMap.has(selectedEdgeKey)) {
        selectedEdgeKey = null;
      }
      if (selectedNodeId || selectedEdgeKey) {
        applySelectionState();
      } else {
        renderDetailEmpty();
      }
      renderZoom();
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

    function formatHoverItems(items, emptyText, maxItems = 3) {
      if (!Array.isArray(items) || items.length === 0) {
        return `<li class="hover-item">${escapeHtml(emptyText)}</li>`;
      }
      const visibleItems = items.slice(0, maxItems);
      const rows = visibleItems.map((item) => {
        const token = escapeHtml(item?.token || "");
        const text = escapeHtml(item?.text || "");
        return `<li class="hover-item">${token ? `<b>${token}</b> ` : ""}${text}</li>`;
      });
      if (items.length > maxItems) {
        rows.push(`<li class="hover-item">还有 ${items.length - maxItems} 项</li>`);
      }
      return rows.join("");
    }

    function renderHoverContent(node) {
      const title = escapeHtml(node.module_title || node.label || node.id);
      const refParts = [];
      if (node.module_name) {
        refParts.push(String(node.module_name));
      }
      if (node.module_ref) {
        refParts.push(String(node.module_ref));
      }
      const fallbackSubtitle = node.label || node.id;
      const subtitle = escapeHtml(refParts.join(" · ") || fallbackSubtitle);
      const capabilities = formatHoverItems(node.capability_items, "无能力声明");
      const bases = formatHoverItems(node.base_items, "无最小可行基");
      const sourceFile = escapeHtml(node.source_file || "");
      const footerText = sourceFile
        ? `${sourceFile} · Ctrl/⌘ + 点击跳转到文档`
        : "Ctrl/⌘ + 点击跳转到文档";
      return `
        <p class="hover-kicker">Framework Module</p>
        <h3 class="hover-title">${title}</h3>
        <p class="hover-subtitle">${subtitle}</p>
        <div class="hover-grid">
          <section class="hover-section">
            <h4 class="hover-section-title">能力声明</h4>
            <ul class="hover-list">${capabilities}</ul>
          </section>
          <section class="hover-section">
            <h4 class="hover-section-title">最小可行基</h4>
            <ul class="hover-list">${bases}</ul>
          </section>
        </div>
        <div class="hover-footer">${footerText}</div>
      `;
    }

    function positionHoverCard(clientX, clientY) {
      if (!hoverCardEl) {
        return;
      }
      const margin = 18;
      const rect = hoverCardEl.getBoundingClientRect();
      let left = clientX + margin;
      let top = clientY + margin;
      if (left + rect.width > window.innerWidth - 12) {
        left = clientX - rect.width - margin;
      }
      if (top + rect.height > window.innerHeight - 12) {
        top = clientY - rect.height - margin;
      }
      hoverCardEl.style.left = `${Math.max(12, left)}px`;
      hoverCardEl.style.top = `${Math.max(12, top)}px`;
    }

    function showNodeHover(node, clientX, clientY) {
      if (!hoverCardEl || panState.active) {
        return;
      }
      hoverCardEl.innerHTML = renderHoverContent(node);
      hoverCardEl.classList.add("visible");
      hoverCardEl.setAttribute("aria-hidden", "false");
      positionHoverCard(clientX, clientY);
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

    function renderDetailEmpty() {
      detailBoxEl.innerHTML =
        isFrameworkColumns
          ? '<p class="meta detail-empty">点击左侧节点或连线查看详情；框标题可拖动，框右上角可折叠或展开，恢复布局按钮可回到默认紧凑位置。</p>'
          : '<p class="meta detail-empty">点击左侧节点或连线查看详情；可通过“显示全部标签”控制整体标签密度。</p>';
    }

    function renderEdgeDetail(edge) {
      const fromNode = byId.get(edge.from);
      const toNode = byId.get(edge.to);
      const sourceFile = typeof edge.source_file === "string" ? edge.source_file : "";
      const sourceLine =
        Number.isFinite(Number(edge.source_line)) && Number(edge.source_line) > 0
          ? Number(edge.source_line)
          : 1;
      const sourceAction = sourceFile
        ? `<button type="button" class="detail-action" data-open-source="1" data-file="${escapeHtml(sourceFile)}" data-line="${sourceLine}">打开来源</button>`
        : "无";

      detailBoxEl.innerHTML = `
        <section class=\"detail-group\">
          <h3 class=\"detail-section-title\">关系概览</h3>
          <div class=\"detail-kv\">
            <span class=\"detail-key\">起点</span>
            <span class=\"detail-value\">${escapeHtml(fromNode?.label ?? edge.from)}</span>
          </div>
          <div class=\"detail-kv\">
            <span class=\"detail-key\">终点</span>
            <span class=\"detail-value\">${escapeHtml(toNode?.label ?? edge.to)}</span>
          </div>
          <div class=\"detail-kv\">
            <span class=\"detail-key\">关系</span>
            <span class=\"detail-value mono\">${escapeHtml(edge.relation ?? "")}</span>
          </div>
        </section>
        <section class=\"detail-group\">
          <h3 class=\"detail-section-title\">规则与术语</h3>
          <div class=\"detail-kv\">
            <span class=\"detail-key\">规则</span>
            <span class=\"detail-value mono\">${escapeHtml(edge.rules || edge.rule || "无")}</span>
          </div>
          <div class=\"detail-kv\">
            <span class=\"detail-key\">术语</span>
            <span class=\"detail-value mono\">${escapeHtml(edge.terms || "无")}</span>
          </div>
        </section>
        <section class=\"detail-group\">
          <h3 class=\"detail-section-title\">来源与跳转</h3>
          <div class=\"detail-kv\">
            <span class=\"detail-key\">结构来源</span>
            <span class=\"detail-value mono\">${sourceFile ? `${escapeHtml(sourceFile)}:${sourceLine}` : "无"}</span>
          </div>
          <div class=\"action-row\">${sourceAction}</div>
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

    function applySelectionState() {
      const nodeId = selectedNodeId;
      const edgeKey = selectedEdgeKey;
      if (!nodeId && !edgeKey) {
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
        updateLabelVisibility();
        return;
      }

      if (edgeKey) {
        const selectedEdge = edgeElementMap.get(edgeKey)?.edge;
        if (!selectedEdge) {
          resetSelection();
          return;
        }
        const related = new Set([selectedEdge.from, selectedEdge.to]);

        for (const [id, circle] of nodeCircleMap.entries()) {
          circle.classList.remove("active", "faded");
          const label = nodeLabelMap.get(id);
          const labelBox = nodeLabelBoxMap.get(id);
          if (label) label.classList.remove("faded");
          if (labelBox) labelBox.classList.remove("faded");

          if (related.has(id)) {
            circle.classList.add("active");
          } else {
            circle.classList.add("faded");
            if (label) label.classList.add("faded");
            if (labelBox) labelBox.classList.add("faded");
          }
        }

        for (const edgeEl of edgeElements) {
          edgeEl.classList.remove("active", "faded");
          if (edgeEl.getAttribute("data-edge-key") === edgeKey) {
            edgeEl.classList.add("active");
          } else {
            edgeEl.classList.add("faded");
          }
        }

        renderEdgeDetail(selectedEdge);
        updateLabelVisibility();
        return;
      }

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

      const levelBaseName = graphData.level_labels[String(node.level)] ?? `层级 ${node.level}`;
      const levelName =
        isFrameworkColumns && node.module_name
          ? `${String(node.module_name)} · ${levelBaseName}`
          : levelBaseName;
      const upItems = upEdges.map((edge) => formatEdgeItem(edge, "up"));
      const downItems = downEdges.map((edge) => formatEdgeItem(edge, "down"));
      const sourceFile = typeof node.source_file === "string" ? node.source_file : "";
      const docLine =
        Number.isFinite(Number(node.doc_line)) && Number(node.doc_line) > 0
          ? Number(node.doc_line)
          : 1;
      const sourceLine =
        Number.isFinite(Number(node.source_line)) && Number(node.source_line) > 0
          ? Number(node.source_line)
          : 1;
      const sourceAction = sourceFile
        ? `<button type="button" class="detail-action" data-open-source="1" data-file="${escapeHtml(sourceFile)}" data-line="${docLine}">打开文档</button>`
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
            <span class=\"detail-key\">文档位置</span>
            <span class=\"detail-value mono\">${sourceFile ? `${escapeHtml(sourceFile)}:${docLine}` : "无"}</span>
          </div>
          <div class=\"detail-kv\">
            <span class=\"detail-key\">结构来源</span>
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

    function selectNode(nodeId) {
      selectedNodeId = nodeId;
      selectedEdgeKey = null;
      applySelectionState();
    }

    function selectEdge(edgeKey) {
      selectedNodeId = null;
      selectedEdgeKey = edgeKey;
      applySelectionState();
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
      hideNodeHover();
      selectedNodeId = null;
      selectedEdgeKey = null;
      for (const group of nodeGroupMap.values()) {
        group.classList.remove("hovered");
      }
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
      renderDetailEmpty();
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

    for (const button of zoomButtons) {
      button.addEventListener("click", () => {
        const action = button.getAttribute("data-zoom");
        if (action === "in") {
          zoomTo(zoomLevel * ZOOM_STEP);
        } else if (action === "out") {
          zoomTo(zoomLevel / ZOOM_STEP);
        } else if (action === "reset") {
          zoomTo(1);
        } else if (action === "fit") {
          zoomTo(computeFitZoom(), { preserveCenter: false });
        }
      });
    }

    if (sideToggleButtonEl) {
      sideToggleButtonEl.addEventListener("click", () => {
        sideVisible = !sideVisible;
        renderSideVisibility();
        writeStoredBool(SIDE_VISIBILITY_KEY, sideVisible);
      });
    }

    if (resetLayoutButtonEl) {
      resetLayoutButtonEl.addEventListener("click", () => {
        for (const [name] of groupState.entries()) {
          groupState.set(name, { dx: 0, dy: 0, collapsed: false });
        }
        selectedNodeId = null;
        selectedEdgeKey = null;
        renderGraph();
        if (graphScrollEl) {
          graphScrollEl.scrollLeft = 0;
          graphScrollEl.scrollTop = 0;
        }
      });
    }

    if (graphScrollEl) {
      graphScrollEl.addEventListener("scroll", () => {
        hideNodeHover();
      });
      graphScrollEl.addEventListener(
        "wheel",
        (event) => {
          if (!(event.ctrlKey || event.metaKey)) {
            return;
          }
          event.preventDefault();
          const factor = event.deltaY < 0 ? ZOOM_STEP : 1 / ZOOM_STEP;
          zoomAtPoint(zoomLevel * factor, event.clientX, event.clientY);
        },
        { passive: false }
      );
    }

    graphScrollEl.addEventListener("pointerdown", beginPan, true);
    svg.addEventListener("pointerdown", beginPan, true);
    window.addEventListener("pointermove", updatePan);
    window.addEventListener("pointerup", endPan);
    window.addEventListener("pointercancel", endPan);

    svg.addEventListener("pointermove", (event) => {
      if (!groupDragState.active || event.pointerId !== groupDragState.pointerId) {
        return;
      }
      const descriptor = descriptorByName.get(groupDragState.frameworkName);
      const current = groupState.get(groupDragState.frameworkName);
      if (!descriptor || !current) {
        return;
      }
      const dx = (event.clientX - groupDragState.startClientX) / zoomLevel;
      const dy = (event.clientY - groupDragState.startClientY) / zoomLevel;
      if (!groupDragState.moved && Math.hypot(dx, dy) >= DRAG_THRESHOLD / Math.max(zoomLevel, 0.1)) {
        groupDragState.moved = true;
        groupDragState.suppressClick = true;
      }
      const clamped = clampGroupOffset(
        descriptor,
        groupDragState.startDx + dx,
        groupDragState.startDy + dy,
        current.collapsed
      );
      groupState.set(groupDragState.frameworkName, { ...current, dx: clamped.dx, dy: clamped.dy });
      renderGraph();
    });
    svg.addEventListener("pointerup", endGroupDrag);
    svg.addEventListener("pointercancel", endGroupDrag);
    svg.addEventListener("pointerleave", (event) => {
      if (groupDragState.active) {
        endGroupDrag(event);
      }
    });

    sideVisible = readStoredBool(SIDE_VISIBILITY_KEY, true);
    renderSideVisibility();
    window.addEventListener("resize", () => {
      if (Math.abs(zoomLevel - computeFitZoom()) < 0.02) {
        zoomTo(computeFitZoom(), { preserveCenter: false });
      }
    });

    svg.addEventListener("click", (event) => {
      if (panState.suppressClick) {
        event.stopPropagation();
        return;
      }
      resetSelection();
    });
    if (toggleLabelsEl) {
      toggleLabelsEl.addEventListener("change", () => {
        updateLabelVisibility();
      });
    }
    initializeZoom();
    renderGraph();
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
