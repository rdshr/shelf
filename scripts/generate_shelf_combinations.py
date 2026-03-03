from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from shelf_framework import Module


STANDARD_L2_PATH = REPO_ROOT / "standards" / "L2" / "置物架框架标准.md"
DEFAULT_OUTPUT_DIR = Path("artifacts")
EPS = 1e-9


@dataclass(frozen=True)
class StandardProfile:
    goal_statement: str
    module_symbols: list[str]
    combination_rules: list[str]
    verification_requirements: list[str]
    baseline_efficiency: float
    boundary_limit_a: float | None
    source_file: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal_statement": self.goal_statement,
            "module_symbols": self.module_symbols,
            "combination_rules": self.combination_rules,
            "verification_requirements": self.verification_requirements,
            "baseline_efficiency": self.baseline_efficiency,
            "boundary_limit_a": self.boundary_limit_a,
            "source_file": self.source_file,
        }


@dataclass(frozen=True)
class EnumerationDomain:
    connectors: dict[str, tuple[float, float, float]]
    rod_candidates: list[dict[str, Any]]
    panel_candidates: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "connector_slots": len(self.connectors),
            "rod_candidates": len(self.rod_candidates),
            "panel_candidates": len(self.panel_candidates),
        }


def round3(v: float) -> float:
    return round(float(v), 3)


def section_lines(markdown: str, heading_prefix: str) -> list[str]:
    lines = markdown.splitlines()
    start = None
    for idx, line in enumerate(lines):
        if line.strip().startswith(heading_prefix):
            start = idx + 1
            break
    if start is None:
        return []

    out: list[str] = []
    for line in lines[start:]:
        stripped = line.strip()
        if stripped.startswith("## "):
            break
        out.append(line)
    return out


def parse_goal(markdown: str) -> str:
    lines = section_lines(markdown, "## 1. 目标（Goal）")
    for line in lines:
        stripped = line.strip()
        if stripped:
            return stripped
    raise ValueError("failed to parse goal statement from L2 standard")


def parse_baseline_efficiency(markdown: str) -> float:
    match = re.search(r"baseline_efficiency\s*=\s*([0-9]+(?:\.[0-9]+)?)", markdown)
    if not match:
        return 1.0
    return float(match.group(1))


def parse_boundary_limit_a(markdown: str) -> float | None:
    boundary_text = "\n".join(section_lines(markdown, "## 2. 边界定义（Boundary）"))
    verify_text = "\n".join(section_lines(markdown, "## 5. 验证（Verification）"))
    merged = f"{boundary_text}\n{verify_text}"

    patterns = [
        r"footprint(?:_projection_boundary_area)?\s*(?:<=|<|=)\s*([0-9]+(?:\.[0-9]+)?)",
        r"BoundaryDefinition\.footprint_a\s*(?:<=|<|=)\s*([0-9]+(?:\.[0-9]+)?)",
        r"\bA\s*(?:<=|<|=)\s*([0-9]+(?:\.[0-9]+)?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, merged)
        if match:
            return float(match.group(1))
    return None


def load_standard_profile() -> StandardProfile:
    if not STANDARD_L2_PATH.exists():
        raise FileNotFoundError(f"missing standard file: {STANDARD_L2_PATH}")

    text = STANDARD_L2_PATH.read_text(encoding="utf-8")
    goal_statement = parse_goal(text)

    module_symbols = sorted(set(re.findall(r"Module\.[A-Z_]+", text)))
    expected = {"Module.ROD", "Module.CONNECTOR", "Module.PANEL"}
    if not expected.issubset(module_symbols):
        raise ValueError(
            "L2 standard missing required module symbols. "
            f"expected={sorted(expected)} actual={module_symbols}"
        )

    combination_rules: list[str] = []
    for line in section_lines(text, "## 4. 组合原则（Combination Principles）"):
        stripped = line.strip()
        match = re.match(r"-\s*`(R\d+)`：\s*(.+)", stripped)
        if match:
            combination_rules.append(f"{match.group(1)}: {match.group(2)}")

    verification_requirements: list[str] = []
    for line in section_lines(text, "## 5. 验证（Verification）"):
        stripped = line.strip()
        if re.match(r"^\d+\.\s", stripped):
            verification_requirements.append(stripped)

    return StandardProfile(
        goal_statement=goal_statement,
        module_symbols=module_symbols,
        combination_rules=combination_rules,
        verification_requirements=verification_requirements,
        baseline_efficiency=parse_baseline_efficiency(text),
        boundary_limit_a=parse_boundary_limit_a(text),
        source_file=STANDARD_L2_PATH.relative_to(REPO_ROOT).as_posix(),
    )


def build_enumeration_domain() -> EnumerationDomain:
    x_values = [0.0, 1.2]
    z_values = [0.0, 0.62]
    y_values = [0.36, 0.78]

    connectors: dict[str, tuple[float, float, float]] = {}
    slot: dict[tuple[int, int, int], str] = {}
    for iy, y in enumerate(y_values):
        for iz, z in enumerate(z_values):
            for ix, x in enumerate(x_values):
                node_id = f"N{len(connectors):03d}"
                connectors[node_id] = (round3(x), round3(y), round3(z))
                slot[(ix, iz, iy)] = node_id

    rod_candidates: list[dict[str, Any]] = []
    for iz in range(len(z_values)):
        for ix in range(len(x_values)):
            rod_candidates.append(
                {
                    "id": f"R{len(rod_candidates):03d}",
                    "from": slot[(ix, iz, 0)],
                    "to": slot[(ix, iz, 1)],
                    "role": "vertical",
                }
            )

    panel_candidates: list[dict[str, Any]] = []
    panel_size = (round3(x_values[-1] - x_values[0]), 0.05, round3(z_values[-1] - z_values[0]))
    panel_center_x = round3((x_values[-1] + x_values[0]) * 0.5)
    panel_center_z = round3((z_values[-1] + z_values[0]) * 0.5)

    for iy, y in enumerate(y_values):
        supports = [
            slot[(0, 0, iy)],
            slot[(1, 0, iy)],
            slot[(0, 1, iy)],
            slot[(1, 1, iy)],
        ]
        panel_candidates.append(
            {
                "id": f"P{len(panel_candidates):03d}",
                "center": [panel_center_x, round3(y - 0.03), panel_center_z],
                "size": [panel_size[0], panel_size[1], panel_size[2]],
                "supports": supports,
                "role": "storage_surface",
            }
        )

    return EnumerationDomain(
        connectors=connectors,
        rod_candidates=rod_candidates,
        panel_candidates=panel_candidates,
    )


def iter_candidates(domain: EnumerationDomain):
    connector_ids = sorted(domain.connectors)
    rod_count = len(domain.rod_candidates)
    panel_count = len(domain.panel_candidates)

    for rod_mask in range(1 << rod_count):
        selected_rods = [domain.rod_candidates[idx] for idx in range(rod_count) if (rod_mask >> idx) & 1]

        for panel_mask in range(1 << panel_count):
            selected_panels = [
                domain.panel_candidates[idx]
                for idx in range(panel_count)
                if (panel_mask >> idx) & 1
            ]

            required_connectors: set[str] = set()
            for rod in selected_rods:
                required_connectors.add(rod["from"])
                required_connectors.add(rod["to"])
            for panel in selected_panels:
                required_connectors.update(panel["supports"])

            optional_connectors = [
                node_id for node_id in connector_ids if node_id not in required_connectors
            ]
            for optional_mask in range(1 << len(optional_connectors)):
                selected_connectors = set(required_connectors)
                for idx, node_id in enumerate(optional_connectors):
                    if (optional_mask >> idx) & 1:
                        selected_connectors.add(node_id)

                yield {
                    "node_ids": sorted(selected_connectors),
                    "rods": selected_rods,
                    "panels": selected_panels,
                }


def materialize_graph(candidate: dict[str, Any], domain: EnumerationDomain) -> dict[str, Any]:
    node_ids = candidate["node_ids"]
    node_set = set(node_ids)

    nodes = [
        {
            "id": node_id,
            "position": [
                domain.connectors[node_id][0],
                domain.connectors[node_id][1],
                domain.connectors[node_id][2],
            ],
        }
        for node_id in node_ids
    ]

    rods = [
        {
            "from": rod["from"],
            "to": rod["to"],
            "role": rod.get("role", "support"),
        }
        for rod in candidate["rods"]
        if rod["from"] in node_set and rod["to"] in node_set
    ]

    panels: list[dict[str, Any]] = []
    for panel in candidate["panels"]:
        supports = [node_id for node_id in panel.get("supports", []) if node_id in node_set]
        if len(supports) < 2:
            continue
        panels.append(
            {
                "id": panel["id"],
                "center": list(panel["center"]),
                "size": list(panel["size"]),
                "supports": sorted(set(supports)),
                "role": panel.get("role", "storage_surface"),
            }
        )

    return {"nodes": nodes, "rods": rods, "panels": panels}


def convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    unique = sorted(set(points))
    if len(unique) <= 1:
        return unique

    def cross(o: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list[tuple[float, float]] = []
    for p in unique:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    upper: list[tuple[float, float]] = []
    for p in reversed(unique):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    return lower[:-1] + upper[:-1]


def polygon_area(points: list[tuple[float, float]]) -> float:
    if len(points) < 3:
        return 0.0
    acc = 0.0
    for idx in range(len(points)):
        x1, y1 = points[idx]
        x2, y2 = points[(idx + 1) % len(points)]
        acc += x1 * y2 - x2 * y1
    return abs(acc) * 0.5


def rectangle_union_area(rectangles: list[tuple[float, float, float, float]]) -> float:
    if not rectangles:
        return 0.0

    xs = sorted({x1 for x1, _, _, _ in rectangles} | {x2 for _, x2, _, _ in rectangles})
    if len(xs) < 2:
        return 0.0

    area = 0.0
    for idx in range(len(xs) - 1):
        left = xs[idx]
        right = xs[idx + 1]
        dx = right - left
        if dx <= 0:
            continue

        intervals: list[tuple[float, float]] = []
        for x1, x2, z1, z2 in rectangles:
            if x1 < right and x2 > left:
                intervals.append((min(z1, z2), max(z1, z2)))
        if not intervals:
            continue

        intervals.sort(key=lambda item: item[0])
        merged: list[tuple[float, float]] = []
        for start, end in intervals:
            if not merged or start > merged[-1][1]:
                merged.append((start, end))
            else:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))

        covered = sum(max(0.0, end - start) for start, end in merged)
        area += covered * dx

    return area


def projection_boundary_area(graph: dict[str, Any]) -> float:
    points: list[tuple[float, float]] = []
    for node in graph["nodes"]:
        x, _, z = node["position"]
        points.append((float(x), float(z)))

    rectangles: list[tuple[float, float, float, float]] = []
    for panel in graph["panels"]:
        cx, _, cz = panel["center"]
        sx, _, sz = panel["size"]
        hx = float(sx) * 0.5
        hz = float(sz) * 0.5
        points.extend(
            [
                (float(cx) - hx, float(cz) - hz),
                (float(cx) - hx, float(cz) + hz),
                (float(cx) + hx, float(cz) - hz),
                (float(cx) + hx, float(cz) + hz),
            ]
        )
        rectangles.append(
            (
                float(cx) - hx,
                float(cx) + hx,
                float(cz) - hz,
                float(cz) + hz,
            )
        )

    hull_area = 0.0
    if points:
        hull = convex_hull(points)
        hull_area = polygon_area(hull)

    panel_union_area = rectangle_union_area(rectangles)
    return max(hull_area, panel_union_area, 1e-6)


def compute_metrics(graph: dict[str, Any], baseline_efficiency: float) -> dict[str, float]:
    nodes = graph["nodes"]
    panels = graph["panels"]

    xs = [item["position"][0] for item in nodes]
    ys = [item["position"][1] for item in nodes]
    zs = [item["position"][2] for item in nodes]
    span_x = max(xs) - min(xs) if xs else 0.0
    span_y = max(ys) - min(ys) if ys else 0.0
    span_z = max(zs) - min(zs) if zs else 0.0

    footprint_projection_boundary_area = projection_boundary_area(graph)
    panel_projection_area_sum = sum(float(panel["size"][0]) * float(panel["size"][2]) for panel in panels)
    target_efficiency = panel_projection_area_sum / footprint_projection_boundary_area

    return {
        "span_x": round3(span_x),
        "span_y": round3(span_y),
        "span_z": round3(span_z),
        "footprint_area": round3(footprint_projection_boundary_area),
        "footprint_projection_boundary_area": round3(footprint_projection_boundary_area),
        "storage_surface": round3(panel_projection_area_sum),
        "panel_projection_area_sum": round3(panel_projection_area_sum),
        "storage_efficiency": round3(target_efficiency),
        "target_efficiency": round3(target_efficiency),
        "goal_score": round3(target_efficiency),
        "baseline_score": round3(baseline_efficiency),
        "baseline_efficiency": round3(baseline_efficiency),
        "improvement_ratio": round3(target_efficiency / baseline_efficiency if baseline_efficiency > 0 else 0.0),
    }


def module_set_of(graph: dict[str, Any]) -> set[Module]:
    modules: set[Module] = set()
    if graph["nodes"]:
        modules.add(Module.CONNECTOR)
    if graph["rods"]:
        modules.add(Module.ROD)
    if graph["panels"]:
        modules.add(Module.PANEL)
    return modules


def validate_r1_connectivity(graph: dict[str, Any]) -> bool:
    connector_ids = [node["id"] for node in graph["nodes"]]
    rods = graph["rods"]
    panels = graph["panels"]

    module_nodes: list[str] = []
    for connector_id in connector_ids:
        module_nodes.append(f"C:{connector_id}")
    for idx in range(len(rods)):
        module_nodes.append(f"R:{idx}")
    for idx in range(len(panels)):
        module_nodes.append(f"P:{idx}")

    if not module_nodes:
        return False

    adj: dict[str, set[str]] = {node_id: set() for node_id in module_nodes}

    for idx, rod in enumerate(rods):
        rid = f"R:{idx}"
        for endpoint in [rod["from"], rod["to"]]:
            cid = f"C:{endpoint}"
            if cid not in adj:
                continue
            adj[rid].add(cid)
            adj[cid].add(rid)

    for idx, panel in enumerate(panels):
        pid = f"P:{idx}"
        for support in panel.get("supports", []):
            cid = f"C:{support}"
            if cid not in adj:
                continue
            adj[pid].add(cid)
            adj[cid].add(pid)

    visited: set[str] = set()
    stack = [module_nodes[0]]
    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        for nxt in adj[current]:
            if nxt not in visited:
                stack.append(nxt)

    return len(visited) == len(module_nodes)


def validate_combination_principles(graph: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    node_map = {node["id"]: node["position"] for node in graph["nodes"]}

    # R2: must include connector module.
    if not graph["nodes"]:
        reasons.append("module combination violates R2: connector module is required")

    # R3: all rods/panels must connect via connector nodes.
    for rod in graph["rods"]:
        if rod["from"] not in node_map or rod["to"] not in node_map:
            reasons.append(
                "module combination violates R3: rod must connect through connector nodes"
            )
            break

    for panel in graph["panels"]:
        supports = panel.get("supports", [])
        if not supports or any(node_id not in node_map for node_id in supports):
            reasons.append(
                "module combination violates R3: panel must connect through connector nodes"
            )
            break

    # R4: each connector must connect at least two modules.
    incident_count: dict[str, int] = {node_id: 0 for node_id in node_map}
    for rod in graph["rods"]:
        if rod["from"] in incident_count:
            incident_count[rod["from"]] += 1
        if rod["to"] in incident_count:
            incident_count[rod["to"]] += 1
    for panel in graph["panels"]:
        for support in panel.get("supports", []):
            if support in incident_count:
                incident_count[support] += 1

    isolated_connectors = [
        node_id for node_id, count in incident_count.items() if count < 2
    ]
    if isolated_connectors:
        reasons.append(
            "module combination violates R4: connector must connect at least two modules"
        )

    # R5: panel must be horizontal (all support connectors share same y).
    for panel in graph["panels"]:
        supports = panel.get("supports", [])
        if not supports:
            reasons.append("module combination violates R5: panel must be horizontal")
            break
        y_values = {round3(float(node_map[support][1])) for support in supports if support in node_map}
        if len(y_values) != 1:
            reasons.append("module combination violates R5: panel must be horizontal")
            break

    # R6: rod must be vertical (x,z equal on both endpoints and y differs).
    for rod in graph["rods"]:
        a = node_map.get(rod["from"])
        b = node_map.get(rod["to"])
        if a is None or b is None:
            continue
        same_x = abs(float(a[0]) - float(b[0])) <= EPS
        same_z = abs(float(a[2]) - float(b[2])) <= EPS
        diff_y = abs(float(a[1]) - float(b[1])) > EPS
        if not (same_x and same_z and diff_y):
            reasons.append("module combination violates R6: rod must be vertical")
            break

    # R1: all modules must be mutually reachable.
    if not validate_r1_connectivity(graph):
        reasons.append("module combination violates R1: module graph is disconnected")

    return (len(reasons) == 0, reasons)


def validate_boundary(metrics: dict[str, float], boundary_limit_a: float | None) -> tuple[bool, list[str], list[str]]:
    reasons: list[str] = []
    warnings: list[str] = []

    if boundary_limit_a is None:
        warnings.append("boundary A is not concretely specified in standard; boundary stage is pass-through")
        return True, reasons, warnings

    if metrics["footprint_projection_boundary_area"] > boundary_limit_a + EPS:
        reasons.append("footprint area exceeds boundary A")
        return False, reasons, warnings

    return True, reasons, warnings


def validate_open_style(_graph: dict[str, Any]) -> bool:
    # With current module set (vertical rods + horizontal panels + point connectors),
    # there is no wall module that can form fully enclosed access faces.
    return True


def validate_goal(
    graph: dict[str, Any],
    metrics: dict[str, float],
    baseline_efficiency: float,
) -> tuple[bool, bool, bool, list[str]]:
    reasons: list[str] = []

    open_style_valid = validate_open_style(graph)
    if not open_style_valid:
        reasons.append("open-style goal not satisfied")

    efficiency_valid = metrics["target_efficiency"] > baseline_efficiency
    if not efficiency_valid:
        reasons.append("target efficiency does not exceed baseline efficiency")

    return (open_style_valid and efficiency_valid, open_style_valid, efficiency_valid, reasons)


def evaluate_design(
    graph: dict[str, Any],
    profile: StandardProfile,
) -> tuple[dict[str, Any], dict[str, float]]:
    metrics = compute_metrics(graph, baseline_efficiency=profile.baseline_efficiency)
    validation: dict[str, Any] = {
        "combination_valid": None,
        "boundary_valid": None,
        "goal_passed": None,
        "open_style_valid": None,
        "efficiency_valid": None,
        "passed": False,
        "failed_stage": None,
        "reasons": [],
        "warnings": [],
    }

    combination_valid, combo_reasons = validate_combination_principles(graph)
    validation["combination_valid"] = combination_valid
    if not combination_valid:
        validation["failed_stage"] = "combination"
        validation["reasons"] = combo_reasons
        return validation, metrics

    boundary_valid, boundary_reasons, boundary_warnings = validate_boundary(
        metrics=metrics,
        boundary_limit_a=profile.boundary_limit_a,
    )
    validation["boundary_valid"] = boundary_valid
    validation["warnings"].extend(boundary_warnings)
    if not boundary_valid:
        validation["failed_stage"] = "boundary"
        validation["reasons"] = boundary_reasons
        return validation, metrics

    goal_passed, open_style_valid, efficiency_valid, goal_reasons = validate_goal(
        graph=graph,
        metrics=metrics,
        baseline_efficiency=profile.baseline_efficiency,
    )
    validation["goal_passed"] = goal_passed
    validation["open_style_valid"] = open_style_valid
    validation["efficiency_valid"] = efficiency_valid
    if not goal_passed:
        validation["failed_stage"] = "goal"
        validation["reasons"] = goal_reasons
        return validation, metrics

    validation["passed"] = True
    return validation, metrics


def compute_isomorphism_signature(graph: dict[str, Any]) -> str:
    connector_ids = [node["id"] for node in graph["nodes"]]

    label: dict[str, str] = {}
    adj: dict[str, list[str]] = {}

    for connector_id in connector_ids:
        node_id = f"C:{connector_id}"
        label[node_id] = "C"
        adj[node_id] = []

    for idx, rod in enumerate(graph["rods"]):
        rid = f"R:{idx}"
        a = f"C:{rod['from']}"
        b = f"C:{rod['to']}"
        label[rid] = "R"
        adj[rid] = []
        if a in adj:
            adj[rid].append(a)
            adj[a].append(rid)
        if b in adj:
            adj[rid].append(b)
            adj[b].append(rid)

    for idx, panel in enumerate(graph["panels"]):
        pid = f"P:{idx}"
        supports = sorted(set(panel.get("supports", [])))
        label[pid] = f"P{len(supports)}"
        adj[pid] = []
        for support in supports:
            cid = f"C:{support}"
            if cid in adj:
                adj[pid].append(cid)
                adj[cid].append(pid)

    colors = dict(label)
    for _ in range(4):
        next_colors: dict[str, str] = {}
        for node_id in sorted(colors):
            neigh = sorted(colors[nbr] for nbr in adj.get(node_id, []))
            payload = f"{colors[node_id]}|{'/'.join(neigh)}"
            next_colors[node_id] = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]
        colors = next_colors

    connector_profile: list[tuple[int, int]] = []
    for connector_id in connector_ids:
        rod_incident = 0
        panel_incident = 0
        for rod in graph["rods"]:
            if rod["from"] == connector_id or rod["to"] == connector_id:
                rod_incident += 1
        for panel in graph["panels"]:
            if connector_id in panel.get("supports", []):
                panel_incident += 1
        connector_profile.append((rod_incident, panel_incident))

    color_counts = Counter(colors.values())
    color_part = ",".join(f"{key}:{color_counts[key]}" for key in sorted(color_counts))
    profile_part = ",".join(f"{a}-{b}" for a, b in sorted(connector_profile))

    return (
        f"C{len(graph['nodes'])}-R{len(graph['rods'])}-P{len(graph['panels'])}"
        f"-CP[{profile_part}]-WL[{color_part}]"
    )


def module_universe(module_symbols: list[str]) -> list[Module]:
    symbols = sorted(set(module_symbols))
    modules: list[Module] = []
    for symbol in symbols:
        enum_name = symbol.split(".", 1)[1]
        if enum_name not in Module.__members__:
            raise ValueError(f"unknown module symbol in standard: {symbol}")
        modules.append(Module[enum_name])
    return modules


def modules_key(modules: set[Module]) -> str:
    return "+".join(sorted(item.value for item in modules))


def compute_family_id(graph: dict[str, Any]) -> tuple[str, str]:
    panel_count = len(graph["panels"])
    rod_count = len(graph["rods"])
    connector_count = len(graph["nodes"])
    family = f"p{panel_count}_r{rod_count}_c{connector_count}"
    label = f"隔板{panel_count}-杆{rod_count}-连接接口{connector_count}"
    return family, label


def build_dataset(limit: int | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    profile = load_standard_profile()
    _ = module_universe(profile.module_symbols)
    domain = build_enumeration_domain()

    representatives: dict[str, dict[str, Any]] = {}
    raw_candidate_count = 0

    for candidate in iter_candidates(domain):
        raw_candidate_count += 1
        graph = materialize_graph(candidate, domain)
        signature = compute_isomorphism_signature(graph)
        if signature in representatives:
            continue
        representatives[signature] = graph
        if limit is not None and len(representatives) >= limit:
            break

    combinations_out: list[dict[str, Any]] = []
    family_seen: dict[str, int] = {}
    family_stats: dict[str, dict[str, Any]] = {}

    for idx, signature in enumerate(sorted(representatives), start=1):
        graph = representatives[signature]
        validation, metrics = evaluate_design(graph=graph, profile=profile)
        modules = module_set_of(graph)

        family, family_label = compute_family_id(graph)
        family_seen[family] = family_seen.get(family, 0) + 1
        variant = family_seen[family]

        combo = {
            "id": f"SHELF-{idx:04d}",
            "family": family,
            "family_label": family_label,
            "description": f"拓扑代表结构：{family_label}",
            "variant": variant,
            "topology_signature": signature,
            "modules": sorted(module.value for module in modules),
            "graph": graph,
            "metrics": metrics,
            "validation": validation,
        }
        combinations_out.append(combo)

        if family not in family_stats:
            family_stats[family] = {
                "family": family,
                "label": family_label,
                "count": 0,
                "passed": 0,
                "failed": 0,
                "scores": [],
            }

        stat = family_stats[family]
        stat["count"] += 1
        stat["scores"].append(metrics["goal_score"])
        if validation["passed"]:
            stat["passed"] += 1
        else:
            stat["failed"] += 1

    total = len(combinations_out)
    passed = sum(1 for item in combinations_out if item["validation"]["passed"])
    failed = total - passed

    scores = [item["metrics"]["goal_score"] for item in combinations_out]
    score_min = min(scores) if scores else 0.0
    score_max = max(scores) if scores else 0.0

    bins = min(10, max(1, total if total < 10 else 10))
    width = (score_max - score_min) / bins if score_max > score_min else 1.0
    score_distribution: list[dict[str, Any]] = []
    for idx in range(bins):
        lower = score_min + idx * width
        upper = lower + width
        if score_max <= score_min:
            lower = score_min + idx
            upper = score_min + idx + 1
        count_in_bin = sum(
            1
            for score in scores
            if score >= lower and (score < upper or (idx == bins - 1 and score <= upper))
        )
        score_distribution.append(
            {
                "bin": idx + 1,
                "range": [round3(lower), round3(upper)],
                "count": count_in_bin,
            }
        )

    families: list[dict[str, Any]] = []
    for family in sorted(family_stats):
        stat = family_stats[family]
        avg_score = sum(stat["scores"]) / len(stat["scores"]) if stat["scores"] else 0.0
        families.append(
            {
                "family": stat["family"],
                "label": stat["label"],
                "count": stat["count"],
                "passed": stat["passed"],
                "failed": stat["failed"],
                "pass_rate": round3(stat["passed"] / max(1, stat["count"])),
                "avg_score": round3(avg_score),
            }
        )

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "standard_profile": profile.to_dict(),
        "enumeration_domain": domain.to_dict(),
        "raw_candidates": raw_candidate_count,
        "total_combinations": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": round3(passed / max(1, total)),
        "baseline_score": round3(profile.baseline_efficiency),
        "score_min": round3(score_min),
        "score_max": round3(score_max),
        "score_avg": round3(sum(scores) / max(1, len(scores))),
        "score_distribution": score_distribution,
        "families": families,
    }
    return combinations_out, summary


def write_outputs(combinations_out: list[dict[str, Any]], summary: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "combinations.json").write_text(
        json.dumps({"combinations": combinations_out}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate deduplicated shelf combinations and run 3-stage validation from L2 standard"
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="output directory")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="optional cap for deduplicated combinations (default: exhaustive)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="legacy alias of --limit; default is exhaustive",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.limit is not None and args.limit <= 0:
        raise ValueError("--limit must be > 0")
    if args.count is not None and args.count <= 0:
        raise ValueError("--count must be > 0")

    resolved_limit = args.limit if args.limit is not None else args.count

    combinations_out, summary = build_dataset(limit=resolved_limit)
    write_outputs(combinations_out, summary, args.output_dir)

    print(
        json.dumps(
            {
                "standard_source": summary["standard_profile"]["source_file"],
                "raw_candidates": summary["raw_candidates"],
                "total_combinations": summary["total_combinations"],
                "passed": summary["passed"],
                "failed": summary["failed"],
                "baseline_score": summary["baseline_score"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
