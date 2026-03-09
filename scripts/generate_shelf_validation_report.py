from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from collections import Counter
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
from verification import verify_structure


@dataclass(frozen=True)
class MappingCheckResult:
    passed: bool
    checked_changes: bool
    error_count: int
    first_error: str


@dataclass(frozen=True)
class ShelfValidationSummary:
    generated_at_utc: str
    strict_mapping_passed: bool
    strict_mapping_change_passed: bool
    total_types: int
    structural_valid_types: int
    structural_invalid_types: int
    verification_passed_types: int
    verification_failed_types: int
    avg_target_efficiency: float
    max_target_efficiency: float
    min_target_efficiency: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at_utc": self.generated_at_utc,
            "strict_mapping_passed": self.strict_mapping_passed,
            "strict_mapping_change_passed": self.strict_mapping_change_passed,
            "total_types": self.total_types,
            "structural_valid_types": self.structural_valid_types,
            "structural_invalid_types": self.structural_invalid_types,
            "verification_passed_types": self.verification_passed_types,
            "verification_failed_types": self.verification_failed_types,
            "avg_target_efficiency": self.avg_target_efficiency,
            "max_target_efficiency": self.max_target_efficiency,
            "min_target_efficiency": self.min_target_efficiency,
        }


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


def _collect_rows(
    grid: DiscreteGrid,
    boundary: BoundaryDefinition,
    baseline_efficiency: float,
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

    rows: list[dict[str, Any]] = []
    reason_counter: Counter[str] = Counter()
    for idx, candidate in enumerate(enum_result.unique_candidates, start=1):
        report = verify_structure(
            topology=candidate.topology,
            boundary=boundary,
            grid=grid,
            baseline_efficiency=baseline_efficiency,
        )
        for reason in report.reasons:
            if reason.strip():
                reason_counter[reason] += 1

        rows.append(
            {
                "index": idx,
                "canonical_key": candidate.canonical_key,
                "panel_count": candidate.topology.panel_count(),
                "structural_valid": candidate.structural_valid,
                "verification_passed": report.passed,
                "boundary_valid": report.boundary_valid,
                "combination_valid": report.combination_valid,
                "efficiency_improved": report.efficiency_improved,
                "target_efficiency": round(report.target_efficiency, 6),
                "baseline_efficiency": round(report.baseline_efficiency, 6),
                "reasons": " | ".join(report.reasons),
            }
        )

    return rows, dict(reason_counter)


def _build_summary(
    rows: list[dict[str, Any]],
    mapping_default: MappingCheckResult,
    mapping_changes: MappingCheckResult,
) -> ShelfValidationSummary:
    target_values = [float(row["target_efficiency"]) for row in rows]
    passed_rows = [row for row in rows if row["verification_passed"]]
    structural_valid_rows = [row for row in rows if row["structural_valid"]]

    return ShelfValidationSummary(
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        strict_mapping_passed=mapping_default.passed,
        strict_mapping_change_passed=mapping_changes.passed,
        total_types=len(rows),
        structural_valid_types=len(structural_valid_rows),
        structural_invalid_types=len(rows) - len(structural_valid_rows),
        verification_passed_types=len(passed_rows),
        verification_failed_types=len(rows) - len(passed_rows),
        avg_target_efficiency=(sum(target_values) / len(target_values)) if target_values else 0.0,
        max_target_efficiency=max(target_values) if target_values else 0.0,
        min_target_efficiency=min(target_values) if target_values else 0.0,
    )


def _write_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "index",
        "canonical_key",
        "panel_count",
        "structural_valid",
        "verification_passed",
        "boundary_valid",
        "combination_valid",
        "efficiency_improved",
        "target_efficiency",
        "baseline_efficiency",
        "reasons",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown_summary(
    summary: ShelfValidationSummary,
    mapping_default: MappingCheckResult,
    mapping_changes: MappingCheckResult,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Shelf Validation Summary",
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
        "## Shelf Type Verification Stats",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| generated_at_utc | {summary.generated_at_utc} |",
        f"| total_types | {summary.total_types} |",
        f"| structural_valid_types | {summary.structural_valid_types} |",
        f"| structural_invalid_types | {summary.structural_invalid_types} |",
        f"| verification_passed_types | {summary.verification_passed_types} |",
        f"| verification_failed_types | {summary.verification_failed_types} |",
        f"| avg_target_efficiency | {summary.avg_target_efficiency:.6f} |",
        f"| min_target_efficiency | {summary.min_target_efficiency:.6f} |",
        f"| max_target_efficiency | {summary.max_target_efficiency:.6f} |",
        "",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")


def _write_dashboard(
    rows: list[dict[str, Any]],
    summary: ShelfValidationSummary,
    reason_counter: dict[str, int],
    output_path: Path,
) -> None:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    output_path.parent.mkdir(parents=True, exist_ok=True)

    valid_count = summary.verification_passed_types
    invalid_count = summary.verification_failed_types
    efficiencies_passed = [float(row["target_efficiency"]) for row in rows if row["verification_passed"]]
    efficiencies_failed = [float(row["target_efficiency"]) for row in rows if not row["verification_passed"]]

    reason_items = sorted(reason_counter.items(), key=lambda item: item[1], reverse=True)
    top_reasons = reason_items[:8]
    reason_labels = [item[0] for item in top_reasons] or ["no failure reason"]
    reason_values = [item[1] for item in top_reasons] or [0]

    table_rows = sorted(
        rows,
        key=lambda item: (item["verification_passed"], -float(item["target_efficiency"])),
    )[:20]

    fig = make_subplots(
        rows=2,
        cols=2,
        specs=[
            [{"type": "xy"}, {"type": "xy"}],
            [{"type": "xy"}, {"type": "table"}],
        ],
        subplot_titles=(
            "Verification Result Counts",
            "Target Efficiency Distribution",
            "Top Failure Reasons",
            "Top 20 Type Rows",
        ),
        vertical_spacing=0.13,
        horizontal_spacing=0.08,
    )

    fig.add_trace(
        go.Bar(
            x=["passed", "failed"],
            y=[valid_count, invalid_count],
            marker_color=["#2c7a7b", "#c53030"],
            name="verification",
            showlegend=False,
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Histogram(
            x=efficiencies_passed,
            name="passed",
            marker_color="#2f855a",
            opacity=0.75,
            nbinsx=20,
        ),
        row=1,
        col=2,
    )
    fig.add_trace(
        go.Histogram(
            x=efficiencies_failed,
            name="failed",
            marker_color="#c53030",
            opacity=0.75,
            nbinsx=20,
        ),
        row=1,
        col=2,
    )

    fig.add_trace(
        go.Bar(
            x=reason_values,
            y=reason_labels,
            orientation="h",
            marker_color="#3182ce",
            name="failure reasons",
            showlegend=False,
        ),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Table(
            header={
                "values": ["index", "verification_passed", "target_efficiency", "panel_count", "canonical_key"],
                "fill_color": "#e2e8f0",
                "align": "left",
            },
            cells={
                "values": [
                    [item["index"] for item in table_rows],
                    [item["verification_passed"] for item in table_rows],
                    [item["target_efficiency"] for item in table_rows],
                    [item["panel_count"] for item in table_rows],
                    [item["canonical_key"] for item in table_rows],
                ],
                "fill_color": "#f8fafc",
                "align": "left",
            },
        ),
        row=2,
        col=2,
    )

    fig.update_layout(
        title=(
            "Shelf Validation Dashboard | "
            f"types={summary.total_types}, passed={summary.verification_passed_types}, "
            f"failed={summary.verification_failed_types}"
        ),
        barmode="overlay",
        height=980,
        width=1600,
        template="plotly_white",
    )
    fig.update_yaxes(autorange="reversed", row=2, col=1)

    fig.write_html(str(output_path), include_plotlyjs=True, full_html=True)


def _write_json_summary(summary: ShelfValidationSummary, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(summary.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate shelf validation table and visualization dashboard.")
    parser.add_argument("--x-cells", type=int, default=2)
    parser.add_argument("--y-cells", type=int, default=2)
    parser.add_argument("--layers", type=int, default=2)
    parser.add_argument("--baseline-efficiency", type=float, default=0.08)
    parser.add_argument("--allow-empty-layer", dest="allow_empty_layer", action="store_true")
    parser.add_argument("--no-allow-empty-layer", dest="allow_empty_layer", action="store_false")
    parser.set_defaults(allow_empty_layer=True)
    parser.add_argument("--max-type-count", type=int, default=5000)
    parser.add_argument("--output-dir", default="docs/validation")
    args = parser.parse_args()

    boundary = _default_boundary()
    boundary = BoundaryDefinition(
        layers_n=args.layers,
        payload_p_per_layer=boundary.payload_p_per_layer,
        space_s_per_layer=boundary.space_s_per_layer,
        opening_o=boundary.opening_o,
        footprint_a=boundary.footprint_a,
    )
    grid = _build_grid(boundary, x_cells=args.x_cells, y_cells=args.y_cells)

    mapping_default = _run_mapping_check(check_changes=False)
    mapping_changes = _run_mapping_check(check_changes=True)
    rows, reason_counter = _collect_rows(
        grid=grid,
        boundary=boundary,
        baseline_efficiency=args.baseline_efficiency,
        allow_empty_layer=args.allow_empty_layer,
        max_type_count=args.max_type_count,
    )
    summary = _build_summary(rows, mapping_default, mapping_changes)

    output_dir = Path(args.output_dir)
    csv_path = output_dir / "shelf_validation_table.csv"
    md_path = output_dir / "shelf_validation_summary.md"
    html_path = output_dir / "shelf_validation_dashboard.html"
    json_path = output_dir / "shelf_validation_summary.json"

    _write_csv(rows, csv_path)
    _write_markdown_summary(summary, mapping_default, mapping_changes, md_path)
    _write_dashboard(rows, summary, reason_counter, html_path)
    _write_json_summary(summary, json_path)

    print(
        json.dumps(
            {
                "summary": summary.to_dict(),
                "artifacts": {
                    "csv": str(csv_path),
                    "markdown": str(md_path),
                    "dashboard_html": str(html_path),
                    "summary_json": str(json_path),
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
