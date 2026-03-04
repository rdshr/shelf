from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from domain import BoundaryDefinition, DiscreteGrid, EnumerationConfig, Footprint2D, Opening2D, Space3D
from enumeration import enumerate_structure_types
from rules.combination_rules import geometric_type_combinations
from visualization.type_grouping import TypeGroup, build_type_groups


@dataclass(frozen=True)
class MappingCheckResult:
    passed: bool
    checked_changes: bool
    error_count: int
    first_error: str


@dataclass(frozen=True)
class ProjectionMetric:
    weighted_cells: int
    union_cells: int
    effective_area: float
    footprint_area: float
    ratio: float


@dataclass(frozen=True)
class ProjectionValidationSummary:
    generated_at_utc: str
    strict_mapping_passed: bool
    strict_mapping_change_passed: bool
    ratio_threshold: float
    total_types: int
    boundary_valid: bool
    structural_valid_types: int
    structural_invalid_types: int
    projection_improved_types: int
    projection_not_improved_types: int
    passed_types: int
    failed_types: int
    avg_ratio: float
    min_ratio: float
    max_ratio: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at_utc": self.generated_at_utc,
            "strict_mapping_passed": self.strict_mapping_passed,
            "strict_mapping_change_passed": self.strict_mapping_change_passed,
            "ratio_threshold": self.ratio_threshold,
            "total_types": self.total_types,
            "boundary_valid": self.boundary_valid,
            "structural_valid_types": self.structural_valid_types,
            "structural_invalid_types": self.structural_invalid_types,
            "projection_improved_types": self.projection_improved_types,
            "projection_not_improved_types": self.projection_not_improved_types,
            "passed_types": self.passed_types,
            "failed_types": self.failed_types,
            "avg_ratio": self.avg_ratio,
            "min_ratio": self.min_ratio,
            "max_ratio": self.max_ratio,
        }


def _parse_int_options(raw: str, *, name: str) -> list[int]:
    items = [item.strip() for item in raw.split(",")]
    values: list[int] = []
    for item in items:
        if not item:
            continue
        try:
            values.append(int(item))
        except ValueError as exc:
            raise ValueError(f"{name} contains non-integer value: {item!r}") from exc
    if not values:
        raise ValueError(f"{name} must contain at least one integer")
    ordered_unique: list[int] = []
    for value in values:
        if value not in ordered_unique:
            ordered_unique.append(value)
    return ordered_unique


def _parse_bool_options(raw: str, *, name: str) -> list[bool]:
    tokens = [token.strip().lower() for token in raw.split(",") if token.strip()]
    if not tokens:
        raise ValueError(f"{name} must contain at least one boolean value")
    mapping = {
        "true": True,
        "1": True,
        "yes": True,
        "y": True,
        "false": False,
        "0": False,
        "no": False,
        "n": False,
    }
    values: list[bool] = []
    for token in tokens:
        if token not in mapping:
            raise ValueError(f"{name} contains invalid boolean value: {token!r}")
        values.append(mapping[token])
    ordered_unique: list[bool] = []
    for value in values:
        if value not in ordered_unique:
            ordered_unique.append(value)
    return ordered_unique


def _scenario_id(x_cells: int, y_cells: int, layers: int, allow_empty_layer: bool) -> str:
    return f"x{x_cells}_y{y_cells}_l{layers}_e{1 if allow_empty_layer else 0}"


def _run_mapping_check(check_changes: bool) -> MappingCheckResult:
    cmd = [sys.executable, str(REPO_ROOT / "scripts/validate_strict_mapping.py")]
    if check_changes:
        cmd.append("--check-changes")
    cmd.append("--json")

    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    payload: dict[str, Any]
    if result.stdout.strip():
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            payload = {"passed": False, "errors": [{"message": result.stdout.strip()}]}
    else:
        payload = {
            "passed": False,
            "errors": [
                {
                    "message": result.stderr.strip() or "mapping validation produced no output",
                }
            ],
        }

    errors = payload.get("errors", [])
    first_error = ""
    if errors and isinstance(errors, list) and isinstance(errors[0], dict):
        first_error = str(errors[0].get("message", ""))

    return MappingCheckResult(
        passed=bool(payload.get("passed", False)) and result.returncode == 0,
        checked_changes=check_changes,
        error_count=len(errors) if isinstance(errors, list) else 1,
        first_error=first_error,
    )


def _default_boundary() -> BoundaryDefinition:
    return BoundaryDefinition(
        layers_n=2,
        payload_p_per_layer=30.0,
        space_s_per_layer=Space3D(width=80.0, depth=35.0, height=30.0),
        opening_o=Opening2D(width=65.0, height=28.0),
        footprint_a=Footprint2D(width=90.0, depth=40.0),
    )


def _build_grid(boundary: BoundaryDefinition, x_cells: int, y_cells: int) -> DiscreteGrid:
    return DiscreteGrid(
        x_cells=x_cells,
        y_cells=y_cells,
        layers_n=boundary.layers_n,
        cell_width=boundary.footprint_a.width / float(x_cells),
        cell_depth=boundary.footprint_a.depth / float(y_cells),
        layer_height=boundary.space_s_per_layer.height,
    )


def _group_lookup(candidates: list[Any], grid: DiscreteGrid) -> tuple[dict[str, str], dict[str, TypeGroup]]:
    groups = build_type_groups(candidates, grid)
    key_to_group: dict[str, str] = {}
    group_meta: dict[str, TypeGroup] = {}

    for idx, group in enumerate(groups):
        gid = f"G{idx:02d}"
        group_meta[gid] = group
        for _, candidate in group.items:
            key_to_group[candidate.canonical_key] = gid

    return key_to_group, group_meta


def _projection_metric(topology: Any, grid: DiscreteGrid, boundary: BoundaryDefinition) -> ProjectionMetric:
    coverage: dict[tuple[int, int], int] = defaultdict(int)
    for cells in topology.occupied_cells_by_layer().values():
        for cell in cells:
            coverage[cell] += 1

    weighted_cells = sum(coverage.values())
    union_cells = len(coverage)
    effective_area = float(weighted_cells) * grid.cell_area
    footprint_area = boundary.footprint_a.width * boundary.footprint_a.depth
    ratio = (effective_area / footprint_area) if footprint_area > 0 else 0.0

    return ProjectionMetric(
        weighted_cells=weighted_cells,
        union_cells=union_cells,
        effective_area=effective_area,
        footprint_area=footprint_area,
        ratio=ratio,
    )


def _collect_rows(
    grid: DiscreteGrid,
    boundary: BoundaryDefinition,
    ratio_threshold: float,
    allow_empty_layer: bool,
    max_type_count: int,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    enum_result = enumerate_structure_types(
        EnumerationConfig(
            grid=grid,
            allow_empty_layer=allow_empty_layer,
            mirror_equivalent=True,
            axis_permutation_equivalent=True,
            include_shelf_family=True,
            include_frame_family=False,
            max_type_count=max_type_count,
        )
    )

    key_to_group, group_meta = _group_lookup(enum_result.unique_candidates, grid)
    valid_combo_keys = {frozenset(combo) for combo in geometric_type_combinations()}
    boundary_valid, boundary_errors = boundary.validate()

    rows: list[dict[str, Any]] = []
    reason_counter: Counter[str] = Counter()
    for idx, candidate in enumerate(enum_result.unique_candidates, start=1):
        projection = _projection_metric(candidate.topology, grid, boundary)
        group_id = key_to_group.get(candidate.canonical_key, "UNKNOWN")
        group = group_meta.get(group_id)
        combo_valid = frozenset(candidate.topology.module_combo()) in valid_combo_keys
        structural_valid = bool(candidate.structural_valid)
        projection_improved = projection.ratio > ratio_threshold

        reasons: list[str] = []
        if not boundary_valid:
            reasons.extend(boundary_errors)
        if not combo_valid:
            reasons.append("combo is not in valid combinations")
        if not structural_valid:
            reasons.extend(candidate.reasons or ["structural rules failed"])
        if not projection_improved:
            reasons.append(
                f"projection_ratio({projection.ratio:.6f}) <= threshold({ratio_threshold:.6f})"
            )
        if not reasons:
            reasons.append("passed")

        for reason in reasons:
            reason_counter[reason] += 1

        rows.append(
            {
                "index": idx,
                "group_id": group_id,
                "group_counts_per_layer": ",".join(str(x) for x in (group.counts_per_layer if group else ())),
                "canonical_key": candidate.canonical_key,
                "panel_count": candidate.topology.panel_count(),
                "boundary_valid": boundary_valid,
                "combination_valid": combo_valid,
                "structural_valid": structural_valid,
                "projection_improved": projection_improved,
                "passed": boundary_valid and combo_valid and structural_valid and projection_improved,
                "weighted_projected_cells": projection.weighted_cells,
                "union_projected_cells": projection.union_cells,
                "effective_area": round(projection.effective_area, 6),
                "footprint_area": round(projection.footprint_area, 6),
                "projection_ratio": round(projection.ratio, 6),
                "threshold": round(ratio_threshold, 6),
                "reasons": " | ".join(reasons),
            }
        )

    return rows, dict(reason_counter)


def _collect_scenarios(
    boundary_template: BoundaryDefinition,
    *,
    x_cells_options: list[int],
    y_cells_options: list[int],
    layers_options: list[int],
    allow_empty_options: list[bool],
    ratio_threshold: float,
    max_type_count: int,
) -> list[dict[str, Any]]:
    scenarios: list[dict[str, Any]] = []
    for layers in layers_options:
        boundary = BoundaryDefinition(
            layers_n=layers,
            payload_p_per_layer=boundary_template.payload_p_per_layer,
            space_s_per_layer=boundary_template.space_s_per_layer,
            opening_o=boundary_template.opening_o,
            footprint_a=boundary_template.footprint_a,
        )
        for x_cells in x_cells_options:
            for y_cells in y_cells_options:
                grid = _build_grid(boundary, x_cells=x_cells, y_cells=y_cells)
                for allow_empty_layer in allow_empty_options:
                    rows, reason_counter = _collect_rows(
                        grid=grid,
                        boundary=boundary,
                        ratio_threshold=ratio_threshold,
                        allow_empty_layer=allow_empty_layer,
                        max_type_count=max_type_count,
                    )
                    scenarios.append(
                        {
                            "id": _scenario_id(x_cells, y_cells, layers, allow_empty_layer),
                            "x_cells": x_cells,
                            "y_cells": y_cells,
                            "layers": layers,
                            "allow_empty_layer": allow_empty_layer,
                            "footprint_cells": x_cells * y_cells,
                            "rows": rows,
                            "reason_counter": reason_counter,
                        }
                    )
    scenarios.sort(
        key=lambda item: (
            int(item["layers"]),
            int(item["x_cells"]),
            int(item["y_cells"]),
            0 if bool(item["allow_empty_layer"]) else 1,
        )
    )
    return scenarios


def _build_summary(
    rows: list[dict[str, Any]],
    mapping_default: MappingCheckResult,
    mapping_changes: MappingCheckResult,
    ratio_threshold: float,
) -> ProjectionValidationSummary:
    ratios = [float(row["projection_ratio"]) for row in rows]
    passed_rows = [row for row in rows if row["passed"]]
    structural_valid_rows = [row for row in rows if row["structural_valid"]]
    improved_rows = [row for row in rows if row["projection_improved"]]
    boundary_valid = bool(rows[0]["boundary_valid"]) if rows else False

    return ProjectionValidationSummary(
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        strict_mapping_passed=mapping_default.passed,
        strict_mapping_change_passed=mapping_changes.passed,
        ratio_threshold=ratio_threshold,
        total_types=len(rows),
        boundary_valid=boundary_valid,
        structural_valid_types=len(structural_valid_rows),
        structural_invalid_types=len(rows) - len(structural_valid_rows),
        projection_improved_types=len(improved_rows),
        projection_not_improved_types=len(rows) - len(improved_rows),
        passed_types=len(passed_rows),
        failed_types=len(rows) - len(passed_rows),
        avg_ratio=(sum(ratios) / len(ratios)) if ratios else 0.0,
        min_ratio=min(ratios) if ratios else 0.0,
        max_ratio=max(ratios) if ratios else 0.0,
    )


def _write_rows_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "index",
        "group_id",
        "group_counts_per_layer",
        "canonical_key",
        "panel_count",
        "boundary_valid",
        "combination_valid",
        "structural_valid",
        "projection_improved",
        "passed",
        "weighted_projected_cells",
        "union_projected_cells",
        "effective_area",
        "footprint_area",
        "projection_ratio",
        "threshold",
        "reasons",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_group_summary_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    group_buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        group_buckets[str(row["group_id"])].append(row)

    fieldnames = [
        "group_id",
        "counts_per_layer",
        "total_types",
        "passed_types",
        "failed_types",
        "avg_ratio",
        "min_ratio",
        "max_ratio",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for gid in sorted(group_buckets.keys()):
            bucket = group_buckets[gid]
            ratios = [float(row["projection_ratio"]) for row in bucket]
            passed_types = sum(1 for row in bucket if row["passed"])
            writer.writerow(
                {
                    "group_id": gid,
                    "counts_per_layer": bucket[0]["group_counts_per_layer"],
                    "total_types": len(bucket),
                    "passed_types": passed_types,
                    "failed_types": len(bucket) - passed_types,
                    "avg_ratio": round(sum(ratios) / len(ratios), 6) if ratios else 0.0,
                    "min_ratio": min(ratios) if ratios else 0.0,
                    "max_ratio": max(ratios) if ratios else 0.0,
                }
            )


def _write_markdown_summary(
    summary: ProjectionValidationSummary,
    mapping_default: MappingCheckResult,
    mapping_changes: MappingCheckResult,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Shelf Projection Validation Summary",
        "",
        "Metric rule:",
        f"- pass if `projection_ratio > {summary.ratio_threshold:.6f}` and boundary/combination/structural checks all pass.",
        "",
        "## Validation Checks",
        "",
        "| Check | Passed | Error Count | First Error |",
        "|---|---:|---:|---|",
        (
            f"| strict_mapping | {mapping_default.passed} | {mapping_default.error_count} | "
            f"{mapping_default.first_error or '-'} |"
        ),
        (
            f"| strict_mapping_change_propagation | {mapping_changes.passed} | {mapping_changes.error_count} | "
            f"{mapping_changes.first_error or '-'} |"
        ),
        "",
        "## Stats",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| generated_at_utc | {summary.generated_at_utc} |",
        f"| total_types | {summary.total_types} |",
        f"| structural_valid_types | {summary.structural_valid_types} |",
        f"| projection_improved_types | {summary.projection_improved_types} |",
        f"| passed_types | {summary.passed_types} |",
        f"| failed_types | {summary.failed_types} |",
        f"| avg_ratio | {summary.avg_ratio:.6f} |",
        f"| min_ratio | {summary.min_ratio:.6f} |",
        f"| max_ratio | {summary.max_ratio:.6f} |",
        "",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")


def _write_json_summary(summary: ProjectionValidationSummary, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(summary.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _write_dashboard(
    scenarios: list[dict[str, Any]],
    default_state: dict[str, Any],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "scenarios": scenarios,
        "default": default_state,
    }
    payload_json = json.dumps(payload, ensure_ascii=False)
    html = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Shelf Top-Projection Validation Dashboard</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    :root {
      --bg: #f4f6fb;
      --panel: #ffffff;
      --text: #1f2937;
      --muted: #6b7280;
      --line: #d9e2f1;
      --pass: #1f9d55;
      --fail: #d64545;
      --chip-on: #e7f1ff;
      --chip-off: #f4f4f6;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    .page {
      max-width: 1760px;
      margin: 0 auto;
      padding: 16px;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 14px;
      margin-bottom: 12px;
    }
    .title {
      margin: 0 0 8px 0;
      font-size: 20px;
      font-weight: 700;
    }
    .subtitle {
      margin: 0;
      color: var(--muted);
      font-size: 13px;
    }
    .controls {
      display: grid;
      grid-template-columns: repeat(6, minmax(170px, 1fr));
      gap: 10px 12px;
      align-items: end;
    }
    .control label {
      display: block;
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 4px;
    }
    .control select,
    .control input[type="number"] {
      width: 100%;
      padding: 7px 9px;
      border: 1px solid #c6d3e8;
      border-radius: 7px;
      font-size: 14px;
      background: #fff;
    }
    .check-group {
      display: grid;
      grid-template-columns: repeat(5, minmax(200px, 1fr));
      gap: 6px 12px;
      margin-top: 10px;
      margin-bottom: 8px;
    }
    .check-item {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;
      color: var(--text);
    }
    .hint {
      color: var(--muted);
      font-size: 12px;
      margin-top: 6px;
    }
    .btn {
      padding: 8px 10px;
      border: 1px solid #bfd0ea;
      border-radius: 8px;
      background: #f7fbff;
      color: #26456d;
      cursor: pointer;
      font-size: 13px;
    }
    .stats {
      display: grid;
      grid-template-columns: repeat(5, minmax(170px, 1fr));
      gap: 10px;
    }
    .stat {
      background: #f8fbff;
      border: 1px solid #d9e2f1;
      border-radius: 9px;
      padding: 10px;
    }
    .stat .k {
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 6px;
    }
    .stat .v {
      font-size: 22px;
      font-weight: 700;
    }
    .rule-grid {
      display: grid;
      grid-template-columns: repeat(5, minmax(180px, 1fr));
      gap: 10px;
      margin-top: 10px;
    }
    .rule-card {
      border-radius: 9px;
      border: 1px solid #d9e2f1;
      padding: 9px;
      background: var(--chip-off);
    }
    .rule-card.on {
      background: var(--chip-on);
      border-color: #b6cbee;
    }
    .rule-card .rk {
      font-size: 12px;
      color: #4b5563;
      margin-bottom: 6px;
    }
    .rule-card .rv {
      font-size: 20px;
      font-weight: 700;
    }
    .layout-grid {
      display: grid;
      grid-template-columns: 1.2fr 1fr;
      gap: 10px;
    }
    .charts {
      display: grid;
      grid-template-columns: repeat(2, minmax(300px, 1fr));
      gap: 10px;
    }
    .chart-box {
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 9px;
      padding: 8px;
      min-height: 320px;
    }
    .table-wrap {
      overflow: auto;
      max-height: 360px;
      border: 1px solid #d9e2f1;
      border-radius: 8px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
    }
    thead th {
      position: sticky;
      top: 0;
      background: #edf3ff;
      text-align: left;
      padding: 6px;
      border-bottom: 1px solid #d9e2f1;
      z-index: 1;
    }
    tbody td {
      padding: 6px;
      border-bottom: 1px solid #eef3fb;
      vertical-align: top;
      word-break: break-all;
    }
    .status-pass { color: var(--pass); font-weight: 700; }
    .status-fail { color: var(--fail); font-weight: 700; }
    .cell-btn {
      border: 0;
      background: transparent;
      color: #1f4f9a;
      cursor: pointer;
      text-align: left;
      padding: 0;
      font-size: 12px;
      text-decoration: underline;
    }
    .detail {
      font-size: 13px;
      line-height: 1.5;
      background: #fcfdff;
      border: 1px solid #d9e2f1;
      border-radius: 8px;
      padding: 10px;
      min-height: 240px;
    }
    .detail .line {
      margin: 4px 0;
    }
    .chips {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
      margin-top: 4px;
    }
    .chip {
      border-radius: 999px;
      font-size: 11px;
      padding: 3px 8px;
      border: 1px solid #c9d7ee;
      background: #f5f9ff;
    }
    .chip.fail {
      border-color: #f2b9b9;
      background: #fff1f1;
      color: #a11a1a;
    }
    .chip.pass {
      border-color: #b8e3c8;
      background: #eefcf2;
      color: #0f6a34;
    }
    @media (max-width: 1380px) {
      .controls { grid-template-columns: repeat(3, minmax(180px, 1fr)); }
      .check-group { grid-template-columns: repeat(2, minmax(220px, 1fr)); }
      .rule-grid { grid-template-columns: repeat(2, minmax(180px, 1fr)); }
      .stats { grid-template-columns: repeat(2, minmax(180px, 1fr)); }
      .layout-grid { grid-template-columns: 1fr; }
      .charts { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="page">
    <div class="panel">
      <h1 class="title">Shelf Top-Projection Validation Dashboard</h1>
      <p class="subtitle">边界与组合原则可调；支持分组筛选、点击分型看详情、显示各原则对通过/失败的影响。</p>
    </div>

    <div class="panel">
      <div class="controls">
        <div class="control">
          <label for="xCells">x_cells</label>
          <select id="xCells"></select>
        </div>
        <div class="control">
          <label for="yCells">y_cells</label>
          <select id="yCells"></select>
        </div>
        <div class="control">
          <label for="layers">layers</label>
          <select id="layers"></select>
        </div>
        <div class="control">
          <label for="allowEmptyLayer">allow_empty_layer</label>
          <select id="allowEmptyLayer">
            <option value="true">true</option>
            <option value="false">false</option>
          </select>
        </div>
        <div class="control">
          <label for="ratioThreshold">ratio_threshold</label>
          <input id="ratioThreshold" type="number" step="0.01" min="0" />
        </div>
        <div class="control">
          <label for="groupFilter">group filter</label>
          <select id="groupFilter"></select>
        </div>
      </div>

      <div class="check-group">
        <label class="check-item"><input id="requireBoundary" type="checkbox" /> B1: boundary_valid</label>
        <label class="check-item"><input id="requireCombination" type="checkbox" /> C1: combination_valid</label>
        <label class="check-item"><input id="requireStructural" type="checkbox" /> S1: structural_valid</label>
        <label class="check-item"><input id="requireR6" type="checkbox" /> S2: weighted_cells &gt; footprint_cells</label>
        <label class="check-item"><input id="requireRatioThreshold" type="checkbox" /> E1: projection_ratio &gt; threshold</label>
      </div>

      <button id="btnResetConstraints" class="btn" type="button">重置为默认约束</button>
      <div class="hint" id="scenarioHint"></div>
      <div class="hint" id="constraintImpact"></div>
    </div>

    <div class="panel">
      <div class="stats">
        <div class="stat"><div class="k">types (filtered)</div><div class="v" id="statTotal">0</div></div>
        <div class="stat"><div class="k">passed</div><div class="v" id="statPassed">0</div></div>
        <div class="stat"><div class="k">failed</div><div class="v" id="statFailed">0</div></div>
        <div class="stat"><div class="k">pass_rate</div><div class="v" id="statPassRate">0%</div></div>
        <div class="stat"><div class="k">avg_ratio</div><div class="v" id="statAvgRatio">0.000</div></div>
      </div>
      <div class="rule-grid" id="ruleGrid"></div>
    </div>

    <div class="layout-grid">
      <div class="panel">
        <div class="charts">
          <div class="chart-box"><div id="chartOverall"></div></div>
          <div class="chart-box"><div id="chartGroup"></div></div>
          <div class="chart-box"><div id="chartPrinciple"></div></div>
          <div class="chart-box"><div id="chartScatter"></div></div>
        </div>
      </div>

      <div class="panel">
        <h3>分型详情（点击右侧表格行或散点）</h3>
        <div class="detail" id="detailPanel">请选择一个结构分型。</div>
      </div>
    </div>

    <div class="layout-grid">
      <div class="panel">
        <h3>分组汇总</h3>
        <div class="table-wrap" id="groupTable"></div>
      </div>
      <div class="panel">
        <h3>结构分型列表</h3>
        <div class="table-wrap" id="typeTable"></div>
      </div>
    </div>
  </div>

  <script>
    const PAYLOAD = __PAYLOAD_JSON__;
    const scenarios = PAYLOAD.scenarios;
    const defaultState = PAYLOAD.default;

    const PRINCIPLE_META = [
      { id: "BOUNDARY", label: "B1 boundary_valid", checkKey: "requireBoundary" },
      { id: "COMBO", label: "C1 combination_valid", checkKey: "requireCombination" },
      { id: "STRUCTURAL", label: "S1 structural_valid", checkKey: "requireStructural" },
      { id: "R6", label: "S2 weighted_cells > footprint_cells", checkKey: "requireR6" },
      { id: "RATIO", label: "E1 projection_ratio > threshold", checkKey: "requireRatioThreshold" },
    ];

    let latestRows = [];
    let selectedKey = null;

    const dom = {
      xCells: document.getElementById("xCells"),
      yCells: document.getElementById("yCells"),
      layers: document.getElementById("layers"),
      allowEmptyLayer: document.getElementById("allowEmptyLayer"),
      ratioThreshold: document.getElementById("ratioThreshold"),
      groupFilter: document.getElementById("groupFilter"),
      requireBoundary: document.getElementById("requireBoundary"),
      requireCombination: document.getElementById("requireCombination"),
      requireStructural: document.getElementById("requireStructural"),
      requireR6: document.getElementById("requireR6"),
      requireRatioThreshold: document.getElementById("requireRatioThreshold"),
      btnResetConstraints: document.getElementById("btnResetConstraints"),
      scenarioHint: document.getElementById("scenarioHint"),
      constraintImpact: document.getElementById("constraintImpact"),
      statTotal: document.getElementById("statTotal"),
      statPassed: document.getElementById("statPassed"),
      statFailed: document.getElementById("statFailed"),
      statPassRate: document.getElementById("statPassRate"),
      statAvgRatio: document.getElementById("statAvgRatio"),
      ruleGrid: document.getElementById("ruleGrid"),
      groupTable: document.getElementById("groupTable"),
      typeTable: document.getElementById("typeTable"),
      detailPanel: document.getElementById("detailPanel"),
    };

    function uniqueValues(field) {
      return [...new Set(scenarios.map((item) => item[field]))].sort((a, b) => Number(a) - Number(b));
    }

    function fillSelect(selectEl, values) {
      selectEl.innerHTML = "";
      for (const value of values) {
        const option = document.createElement("option");
        option.value = String(value);
        option.textContent = String(value);
        selectEl.appendChild(option);
      }
    }

    function escapeHtml(value) {
      return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
    }

    function rowKey(row) {
      return String(row.canonical_key);
    }

    function scenarioBySelection() {
      const x = Number(dom.xCells.value);
      const y = Number(dom.yCells.value);
      const layers = Number(dom.layers.value);
      const allowEmptyLayer = dom.allowEmptyLayer.value === "true";
      return scenarios.find((item) =>
        item.x_cells === x &&
        item.y_cells === y &&
        item.layers === layers &&
        Boolean(item.allow_empty_layer) === allowEmptyLayer
      ) || null;
    }

    function currentConfig() {
      return {
        ratioThreshold: Number(dom.ratioThreshold.value),
        requireBoundary: dom.requireBoundary.checked,
        requireCombination: dom.requireCombination.checked,
        requireStructural: dom.requireStructural.checked,
        requireR6: dom.requireR6.checked,
        requireRatioThreshold: dom.requireRatioThreshold.checked,
      };
    }

    function baselineConfigFromCurrent() {
      const cfg = currentConfig();
      return {
        ...cfg,
        requireBoundary: true,
        requireCombination: true,
        requireStructural: true,
        requireR6: true,
        requireRatioThreshold: true,
      };
    }

    function evaluateRows(scenario, config) {
      const out = [];
      for (const row of scenario.rows) {
        const flags = {
          BOUNDARY: !row.boundary_valid,
          COMBO: !row.combination_valid,
          STRUCTURAL: !row.structural_valid,
          R6: !(row.weighted_projected_cells > scenario.footprint_cells),
          RATIO: !(Number(row.projection_ratio) > config.ratioThreshold),
        };

        const failedPrinciples = [];
        if (config.requireBoundary && flags.BOUNDARY) failedPrinciples.push("BOUNDARY");
        if (config.requireCombination && flags.COMBO) failedPrinciples.push("COMBO");
        if (config.requireStructural && flags.STRUCTURAL) failedPrinciples.push("STRUCTURAL");
        if (config.requireR6 && flags.R6) failedPrinciples.push("R6");
        if (config.requireRatioThreshold && flags.RATIO) failedPrinciples.push("RATIO");

        const passed = failedPrinciples.length === 0;
        const principleText = passed
          ? "满足启用原则"
          : `违反: ${failedPrinciples.map((id) => PRINCIPLE_META.find((it) => it.id === id).label).join(" | ")}`;

        out.push({
          ...row,
          key: rowKey(row),
          footprint_cells: scenario.footprint_cells,
          rule_flags: flags,
          failed_principles: failedPrinciples,
          principle_text: principleText,
          dynamic_reasons: passed ? "passed" : principleText,
          passed,
        });
      }
      return out;
    }

    function filteredByGroup(rows) {
      const gid = dom.groupFilter.value || "ALL";
      if (gid === "ALL") return rows;
      return rows.filter((row) => row.group_id === gid);
    }

    function getGroupIds(rows) {
      return [...new Set(rows.map((row) => row.group_id))].sort();
    }

    function refreshGroupFilterOptions(scenarioRows) {
      const current = dom.groupFilter.value || "ALL";
      const groups = getGroupIds(scenarioRows);
      dom.groupFilter.innerHTML = `<option value="ALL">ALL</option>${groups
        .map((gid) => `<option value="${escapeHtml(gid)}">${escapeHtml(gid)}</option>`)
        .join("")}`;
      if (groups.includes(current)) {
        dom.groupFilter.value = current;
      } else {
        dom.groupFilter.value = "ALL";
      }
    }

    function renderStats(rows) {
      const total = rows.length;
      const passed = rows.filter((row) => row.passed).length;
      const failed = total - passed;
      const avgRatio = total === 0
        ? 0
        : rows.reduce((acc, row) => acc + Number(row.projection_ratio), 0) / total;

      dom.statTotal.textContent = String(total);
      dom.statPassed.textContent = String(passed);
      dom.statFailed.textContent = String(failed);
      dom.statPassRate.textContent = total === 0 ? "0%" : `${((passed / total) * 100).toFixed(1)}%`;
      dom.statAvgRatio.textContent = avgRatio.toFixed(3);
    }

    function renderRuleCards(rows, config) {
      const cards = PRINCIPLE_META.map((meta) => {
        const failCount = rows.filter((row) => row.rule_flags[meta.id]).length;
        const on = Boolean(config[meta.checkKey]);
        const rowClass = on ? "rule-card on" : "rule-card";
        return `
          <div class="${rowClass}">
            <div class="rk">${escapeHtml(meta.label)} (${on ? "启用" : "未启用"})</div>
            <div class="rv">${failCount}</div>
          </div>
        `;
      }).join("");
      dom.ruleGrid.innerHTML = cards;
    }

    function renderCharts(rows, config) {
      const passedRows = rows.filter((row) => row.passed);
      const failedRows = rows.filter((row) => !row.passed);

      Plotly.react(
        "chartOverall",
        [{
          type: "bar",
          x: ["passed", "failed"],
          y: [passedRows.length, failedRows.length],
          marker: { color: ["#1f9d55", "#d64545"] },
          showlegend: false,
        }],
        {
          title: "通过 / 失败",
          margin: { l: 40, r: 20, t: 36, b: 40 },
          template: "plotly_white",
        },
        { responsive: true }
      );

      const groupMap = new Map();
      for (const row of rows) {
        if (!groupMap.has(row.group_id)) {
          groupMap.set(row.group_id, { pass: 0, fail: 0 });
        }
        if (row.passed) groupMap.get(row.group_id).pass += 1;
        else groupMap.get(row.group_id).fail += 1;
      }
      const groups = [...groupMap.keys()].sort();
      Plotly.react(
        "chartGroup",
        [
          {
            type: "bar",
            name: "passed",
            x: groups,
            y: groups.map((g) => groupMap.get(g).pass),
            marker: { color: "#1f9d55" },
          },
          {
            type: "bar",
            name: "failed",
            x: groups,
            y: groups.map((g) => groupMap.get(g).fail),
            marker: { color: "#d64545" },
          },
        ],
        {
          title: "分组通过/失败",
          barmode: "stack",
          margin: { l: 40, r: 20, t: 36, b: 40 },
          template: "plotly_white",
        },
        { responsive: true }
      );

      const failByPrinciple = PRINCIPLE_META.map((meta) => {
        const count = rows.filter((row) => row.rule_flags[meta.id]).length;
        return { label: meta.label, count };
      });

      Plotly.react(
        "chartPrinciple",
        [{
          type: "bar",
          x: failByPrinciple.map((item) => item.count),
          y: failByPrinciple.map((item) => item.label),
          orientation: "h",
          marker: { color: "#2b6cb0" },
          showlegend: false,
        }],
        {
          title: "各原则违反计数（当前过滤后）",
          margin: { l: 170, r: 20, t: 36, b: 40 },
          template: "plotly_white",
        },
        { responsive: true }
      );

      Plotly.react(
        "chartScatter",
        [{
          type: "scatter",
          mode: "markers",
          x: rows.map((row) => Number(row.index)),
          y: rows.map((row) => Number(row.projection_ratio)),
          customdata: rows.map((row) => [row.key, row.group_id, row.canonical_key]),
          text: rows.map((row) => `${row.group_id}<br>${row.canonical_key}<br>${row.principle_text}`),
          hovertemplate: "%{text}<extra></extra>",
          marker: {
            size: 8,
            opacity: 0.9,
            color: rows.map((row) => row.passed ? "#1f9d55" : "#d64545"),
          },
          showlegend: false,
        }],
        {
          title: "分型散点（点击查看详情）",
          margin: { l: 40, r: 20, t: 36, b: 40 },
          template: "plotly_white",
          shapes: config.requireRatioThreshold ? [{
            type: "line",
            x0: 0,
            x1: Math.max(...rows.map((row) => Number(row.index)), 1),
            y0: Number(config.ratioThreshold),
            y1: Number(config.ratioThreshold),
            line: { color: "#1f6feb", width: 2, dash: "dash" },
          }] : [],
        },
        { responsive: true }
      );
    }

    function renderGroupTable(rows) {
      const map = new Map();
      for (const row of rows) {
        if (!map.has(row.group_id)) {
          map.set(row.group_id, {
            group_id: row.group_id,
            counts_per_layer: row.group_counts_per_layer,
            total: 0,
            pass: 0,
            fail: 0,
          });
        }
        const item = map.get(row.group_id);
        item.total += 1;
        if (row.passed) item.pass += 1;
        else item.fail += 1;
      }
      const list = [...map.values()].sort((a, b) => a.group_id.localeCompare(b.group_id));
      const body = list.map((item) => {
        const rate = item.total === 0 ? 0 : (item.pass / item.total) * 100;
        return `
          <tr>
            <td><button class="cell-btn" data-group="${escapeHtml(item.group_id)}">${escapeHtml(item.group_id)}</button></td>
            <td>${escapeHtml(item.counts_per_layer)}</td>
            <td>${item.total}</td>
            <td class="status-pass">${item.pass}</td>
            <td class="status-fail">${item.fail}</td>
            <td>${rate.toFixed(1)}%</td>
          </tr>
        `;
      }).join("");

      dom.groupTable.innerHTML = `
        <table>
          <thead>
            <tr><th>group</th><th>counts_per_layer</th><th>total</th><th>pass</th><th>fail</th><th>pass_rate</th></tr>
          </thead>
          <tbody>${body}</tbody>
        </table>
      `;
    }

    function renderTypeTable(rows) {
      const sorted = [...rows].sort((a, b) => {
        if (a.passed !== b.passed) return a.passed ? 1 : -1;
        return Number(a.projection_ratio) - Number(b.projection_ratio);
      });

      const body = sorted.map((row) => {
        const status = row.passed
          ? `<span class="status-pass">PASS</span>`
          : `<span class="status-fail">FAIL</span>`;
        return `
          <tr>
            <td>${status}</td>
            <td>${escapeHtml(row.group_id)}</td>
            <td>${escapeHtml(row.group_counts_per_layer)}</td>
            <td>${row.index}</td>
            <td>${Number(row.projection_ratio).toFixed(3)}</td>
            <td>${row.panel_count}</td>
            <td>${escapeHtml(row.principle_text)}</td>
            <td><button class="cell-btn" data-key="${escapeHtml(row.key)}">${escapeHtml(row.canonical_key)}</button></td>
          </tr>
        `;
      }).join("");

      dom.typeTable.innerHTML = `
        <table>
          <thead>
            <tr>
              <th>status</th><th>group</th><th>group_counts</th><th>index</th><th>ratio</th><th>panel</th><th>原则匹配</th><th>canonical_key</th>
            </tr>
          </thead>
          <tbody>${body}</tbody>
        </table>
      `;
    }

    function renderDetail(row) {
      if (!row) {
        dom.detailPanel.innerHTML = "请选择一个结构分型。";
        return;
      }

      const principleChips = PRINCIPLE_META.map((meta) => {
        const failed = Boolean(row.rule_flags[meta.id]);
        const cls = failed ? "chip fail" : "chip pass";
        return `<span class="${cls}">${escapeHtml(meta.label)}: ${failed ? "不满足" : "满足"}</span>`;
      }).join("");

      const failedPrinciples = row.failed_principles.length === 0
        ? "<span class='chip pass'>全部满足</span>"
        : row.failed_principles
            .map((id) => {
              const found = PRINCIPLE_META.find((item) => item.id === id);
              return found ? found.label : id;
            })
            .map((label) => `<span class="chip fail">${escapeHtml(label)}</span>`)
            .join("");

      dom.detailPanel.innerHTML = `
        <div class="line"><strong>status:</strong> ${row.passed ? "<span class='status-pass'>PASS</span>" : "<span class='status-fail'>FAIL</span>"}</div>
        <div class="line"><strong>group:</strong> ${escapeHtml(row.group_id)} | <strong>group_counts:</strong> ${escapeHtml(row.group_counts_per_layer)}</div>
        <div class="line"><strong>index:</strong> ${row.index} | <strong>panel_count:</strong> ${row.panel_count}</div>
        <div class="line"><strong>projection_ratio:</strong> ${Number(row.projection_ratio).toFixed(6)} | <strong>weighted/footprint_cells:</strong> ${row.weighted_projected_cells}/${row.footprint_cells}</div>
        <div class="line"><strong>canonical_key:</strong> ${escapeHtml(row.canonical_key)}</div>
        <div class="line"><strong>当前失败原则:</strong><div class="chips">${failedPrinciples}</div></div>
        <div class="line"><strong>各原则状态:</strong><div class="chips">${principleChips}</div></div>
        <div class="line"><strong>动态判定:</strong> ${escapeHtml(row.dynamic_reasons)}</div>
        <div class="line"><strong>原始规则说明:</strong> ${escapeHtml(row.reasons || "")}</div>
      `;
    }

    function updateConstraintImpact(filteredRows, baselineFilteredRows) {
      const currPass = filteredRows.filter((row) => row.passed).length;
      const basePass = baselineFilteredRows.filter((row) => row.passed).length;
      const delta = currPass - basePass;
      const deltaText = delta === 0 ? "无变化" : (delta > 0 ? `+${delta}` : `${delta}`);
      dom.constraintImpact.textContent =
        `与“全部原则启用”相比：passed 变化 ${deltaText}（current=${currPass}, baseline=${basePass}）。`;
    }

    function bindInteractionHandlers() {
      dom.groupTable.addEventListener("click", (event) => {
        const target = event.target;
        if (!(target instanceof HTMLElement)) return;
        const gid = target.getAttribute("data-group");
        if (!gid) return;
        dom.groupFilter.value = gid;
        render();
      });

      dom.typeTable.addEventListener("click", (event) => {
        const target = event.target;
        if (!(target instanceof HTMLElement)) return;
        const key = target.getAttribute("data-key");
        if (!key) return;
        selectedKey = key;
        const row = latestRows.find((item) => item.key === key) || null;
        renderDetail(row);
      });

      const scatter = document.getElementById("chartScatter");
      if (scatter && typeof scatter.on === "function") {
        scatter.on("plotly_click", (eventData) => {
          const points = eventData && eventData.points ? eventData.points : [];
          const point = points.length > 0 ? points[0] : null;
          const customData = point && point.customdata ? point.customdata : [];
          const key = customData.length > 0 ? customData[0] : null;
          if (!key) return;
          selectedKey = key;
          const row = latestRows.find((item) => item.key === key) || null;
          renderDetail(row);
        });
      }
    }

    function render() {
      const scenario = scenarioBySelection();
      if (!scenario) {
        dom.scenarioHint.textContent = "当前边界组合没有预计算数据。";
        renderStats([]);
        dom.ruleGrid.innerHTML = "";
        dom.groupTable.innerHTML = "";
        dom.typeTable.innerHTML = "";
        renderDetail(null);
        return;
      }

      refreshGroupFilterOptions(scenario.rows);
      const config = currentConfig();
      const baselineConfig = baselineConfigFromCurrent();
      const allRows = evaluateRows(scenario, config);
      const baselineRows = evaluateRows(scenario, baselineConfig);
      const filteredRows = filteredByGroup(allRows);
      const baselineFilteredRows = filteredByGroup(baselineRows);
      latestRows = filteredRows;

      dom.scenarioHint.textContent =
        `scenario=${scenario.id} | footprint_cells=${scenario.footprint_cells} | group=${dom.groupFilter.value || "ALL"} | threshold=${Number(config.ratioThreshold).toFixed(3)}`;

      renderStats(filteredRows);
      renderRuleCards(filteredRows, config);
      updateConstraintImpact(filteredRows, baselineFilteredRows);
      renderCharts(filteredRows, config);
      renderGroupTable(filteredRows);
      renderTypeTable(filteredRows);

      const selected = selectedKey
        ? filteredRows.find((row) => row.key === selectedKey)
        : null;
      renderDetail(selected || filteredRows[0] || null);
    }

    function init() {
      fillSelect(dom.xCells, uniqueValues("x_cells"));
      fillSelect(dom.yCells, uniqueValues("y_cells"));
      fillSelect(dom.layers, uniqueValues("layers"));

      dom.xCells.value = String(defaultState.x_cells);
      dom.yCells.value = String(defaultState.y_cells);
      dom.layers.value = String(defaultState.layers);
      dom.allowEmptyLayer.value = defaultState.allow_empty_layer ? "true" : "false";
      dom.ratioThreshold.value = String(defaultState.ratio_threshold);

      dom.requireBoundary.checked = Boolean(defaultState.require_boundary);
      dom.requireCombination.checked = Boolean(defaultState.require_combination);
      dom.requireStructural.checked = Boolean(defaultState.require_structural);
      dom.requireR6.checked = Boolean(defaultState.require_r6_weighted_gt_footprint);
      dom.requireRatioThreshold.checked = Boolean(defaultState.require_ratio_threshold);

      dom.btnResetConstraints.addEventListener("click", () => {
        dom.ratioThreshold.value = String(defaultState.ratio_threshold);
        dom.requireBoundary.checked = Boolean(defaultState.require_boundary);
        dom.requireCombination.checked = Boolean(defaultState.require_combination);
        dom.requireStructural.checked = Boolean(defaultState.require_structural);
        dom.requireR6.checked = Boolean(defaultState.require_r6_weighted_gt_footprint);
        dom.requireRatioThreshold.checked = Boolean(defaultState.require_ratio_threshold);
        render();
      });

      const listeners = [
        dom.xCells,
        dom.yCells,
        dom.layers,
        dom.allowEmptyLayer,
        dom.groupFilter,
        dom.ratioThreshold,
        dom.requireBoundary,
        dom.requireCombination,
        dom.requireStructural,
        dom.requireR6,
        dom.requireRatioThreshold,
      ];
      for (const item of listeners) {
        item.addEventListener("change", render);
      }

      bindInteractionHandlers();
      render();
    }

    init();
  </script>
</body>
</html>
"""
    output_path.write_text(html.replace("__PAYLOAD_JSON__", payload_json), encoding="utf-8")


def _write_scenarios_json(scenarios: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps({"scenarios": scenarios}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate shelf top-projection validation table and dashboard."
    )
    parser.add_argument("--x-cells", type=int, default=2)
    parser.add_argument("--y-cells", type=int, default=2)
    parser.add_argument("--layers", type=int, default=2)
    parser.add_argument("--x-cells-options", default="1,2")
    parser.add_argument("--y-cells-options", default="1,2")
    parser.add_argument("--layers-options", default="1,2")
    parser.add_argument("--allow-empty-options", default="true,false")
    parser.add_argument("--ratio-threshold", type=float, default=1.0)
    parser.add_argument("--allow-empty-layer", dest="allow_empty_layer", action="store_true")
    parser.add_argument("--no-allow-empty-layer", dest="allow_empty_layer", action="store_false")
    parser.set_defaults(allow_empty_layer=True)
    parser.add_argument("--max-type-count", type=int, default=5000)
    parser.add_argument("--output-dir", default="docs/validation")
    args = parser.parse_args()

    x_cells_options = _parse_int_options(args.x_cells_options, name="x-cells-options")
    y_cells_options = _parse_int_options(args.y_cells_options, name="y-cells-options")
    layers_options = _parse_int_options(args.layers_options, name="layers-options")
    allow_empty_options = _parse_bool_options(args.allow_empty_options, name="allow-empty-options")

    if args.x_cells not in x_cells_options:
        x_cells_options.append(args.x_cells)
    if args.y_cells not in y_cells_options:
        y_cells_options.append(args.y_cells)
    if args.layers not in layers_options:
        layers_options.append(args.layers)
    if args.allow_empty_layer not in allow_empty_options:
        allow_empty_options.append(args.allow_empty_layer)

    boundary_template = _default_boundary()

    mapping_default = _run_mapping_check(check_changes=False)
    mapping_changes = _run_mapping_check(check_changes=True)

    scenarios = _collect_scenarios(
        boundary_template=boundary_template,
        x_cells_options=x_cells_options,
        y_cells_options=y_cells_options,
        layers_options=layers_options,
        allow_empty_options=allow_empty_options,
        ratio_threshold=args.ratio_threshold,
        max_type_count=args.max_type_count,
    )
    scenario_lookup = {str(item["id"]): item for item in scenarios}
    selected_scenario_id = _scenario_id(
        args.x_cells,
        args.y_cells,
        args.layers,
        args.allow_empty_layer,
    )
    selected_scenario = scenario_lookup.get(selected_scenario_id)
    if selected_scenario is None:
        raise ValueError(f"default scenario missing: {selected_scenario_id}")

    rows = list(selected_scenario["rows"])
    reason_counter = dict(selected_scenario["reason_counter"])
    summary = _build_summary(
        rows=rows,
        mapping_default=mapping_default,
        mapping_changes=mapping_changes,
        ratio_threshold=args.ratio_threshold,
    )

    output_dir = Path(args.output_dir)
    row_csv_path = output_dir / "shelf_projection_validation_table.csv"
    group_csv_path = output_dir / "shelf_projection_group_summary.csv"
    md_path = output_dir / "shelf_projection_validation_summary.md"
    html_path = output_dir / "shelf_projection_validation_dashboard.html"
    json_path = output_dir / "shelf_projection_validation_summary.json"
    scenarios_json_path = output_dir / "shelf_projection_validation_scenarios.json"

    _write_rows_csv(rows, row_csv_path)
    _write_group_summary_csv(rows, group_csv_path)
    _write_markdown_summary(summary, mapping_default, mapping_changes, md_path)
    _write_dashboard(
        scenarios=scenarios,
        default_state={
            "x_cells": args.x_cells,
            "y_cells": args.y_cells,
            "layers": args.layers,
            "allow_empty_layer": args.allow_empty_layer,
            "ratio_threshold": args.ratio_threshold,
            "require_boundary": True,
            "require_combination": True,
            "require_structural": True,
            "require_ratio_threshold": True,
            "require_r6_weighted_gt_footprint": True,
        },
        output_path=html_path,
    )
    _write_json_summary(summary, json_path)
    _write_scenarios_json(scenarios, scenarios_json_path)

    print(
        json.dumps(
            {
                "summary": summary.to_dict(),
                "scenario_count": len(scenarios),
                "default_scenario_id": selected_scenario_id,
                "default_failure_reason_count": len(reason_counter),
                "artifacts": {
                    "row_csv": str(row_csv_path),
                    "group_csv": str(group_csv_path),
                    "summary_markdown": str(md_path),
                    "dashboard_html": str(html_path),
                    "summary_json": str(json_path),
                    "scenarios_json": str(scenarios_json_path),
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
