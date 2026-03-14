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


@dataclass(frozen=True)
class ShelfValidationRow:
    index: int
    canonical_key: str
    panel_count: int
    structural_valid: bool
    verification_passed: bool
    boundary_valid: bool
    combination_valid: bool
    efficiency_improved: bool
    target_efficiency: float
    baseline_efficiency: float
    reasons: str

    def to_csv_row(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "canonical_key": self.canonical_key,
            "panel_count": self.panel_count,
            "structural_valid": self.structural_valid,
            "verification_passed": self.verification_passed,
            "boundary_valid": self.boundary_valid,
            "combination_valid": self.combination_valid,
            "efficiency_improved": self.efficiency_improved,
            "target_efficiency": self.target_efficiency,
            "baseline_efficiency": self.baseline_efficiency,
            "reasons": self.reasons,
        }


@dataclass(frozen=True)
class ShelfValidationArtifacts:
    csv: Path
    markdown: Path
    dashboard_html: Path
    summary_json: Path

    def to_dict(self) -> dict[str, str]:
        return {
            "csv": str(self.csv),
            "markdown": str(self.markdown),
            "dashboard_html": str(self.dashboard_html),
            "summary_json": str(self.summary_json),
        }


@dataclass(frozen=True)
class ShelfValidationDashboardData:
    valid_count: int
    invalid_count: int
    efficiencies_passed: list[float]
    efficiencies_failed: list[float]
    reason_labels: list[str]
    reason_values: list[int]
    table_rows: list[ShelfValidationRow]


@dataclass(frozen=True)
class ShelfValidationReportContext:
    rows: list[ShelfValidationRow]
    reason_counter: dict[str, int]
    mapping_default: MappingCheckResult
    mapping_changes: MappingCheckResult
    summary: ShelfValidationSummary

    @classmethod
    def build(
        cls,
        *,
        rows: list[ShelfValidationRow],
        reason_counter: dict[str, int],
        mapping_default: MappingCheckResult,
        mapping_changes: MappingCheckResult,
    ) -> "ShelfValidationReportContext":
        return cls(
            rows=rows,
            reason_counter=reason_counter,
            mapping_default=mapping_default,
            mapping_changes=mapping_changes,
            summary=_build_summary(rows, mapping_default, mapping_changes),
        )


def _parse_mapping_check_payload(stdout: str, stderr: str) -> dict[str, Any]:
    if stdout.strip():
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            for line in reversed([item.strip() for item in stdout.splitlines() if item.strip()]):
                if not line.startswith("{"):
                    continue
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
            return {"passed": False, "errors": [{"message": stdout.strip()}]}
    return {
        "passed": False,
        "errors": [
            {
                "message": stderr.strip() or "mapping validation produced no output",
            }
        ],
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

    payload = _parse_mapping_check_payload(result.stdout, result.stderr)

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
) -> tuple[list[ShelfValidationRow], dict[str, int]]:
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

    rows: list[ShelfValidationRow] = []
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
            ShelfValidationRow(
                index=idx,
                canonical_key=candidate.canonical_key,
                panel_count=candidate.topology.panel_count(),
                structural_valid=candidate.structural_valid,
                verification_passed=report.passed,
                boundary_valid=report.boundary_valid,
                combination_valid=report.combination_valid,
                efficiency_improved=report.efficiency_improved,
                target_efficiency=round(report.target_efficiency, 6),
                baseline_efficiency=round(report.baseline_efficiency, 6),
                reasons=" | ".join(report.reasons),
            )
        )

    return rows, dict(reason_counter)


def _build_summary(
    rows: list[ShelfValidationRow],
    mapping_default: MappingCheckResult,
    mapping_changes: MappingCheckResult,
) -> ShelfValidationSummary:
    target_values = [row.target_efficiency for row in rows]
    passed_rows = [row for row in rows if row.verification_passed]
    structural_valid_rows = [row for row in rows if row.structural_valid]

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


def _write_csv(rows: list[ShelfValidationRow], output_path: Path) -> None:
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
        for row in rows:
            writer.writerow(row.to_csv_row())


def _write_markdown_summary(report: ShelfValidationReportContext, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Shelf Validation Summary",
        "",
        "## Validation Checks",
        "",
        "| Check | Passed | Error Count | First Error |",
        "|---|---:|---:|---|",
        (
            f"| strict_mapping | {report.mapping_default.passed} | {report.mapping_default.error_count} | "
            f"{report.mapping_default.first_error or '-'} |"
        ),
        (
            f"| strict_mapping_change_propagation | {report.mapping_changes.passed} | {report.mapping_changes.error_count} | "
            f"{report.mapping_changes.first_error or '-'} |"
        ),
        "",
        "## Shelf Type Verification Stats",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| generated_at_utc | {report.summary.generated_at_utc} |",
        f"| total_types | {report.summary.total_types} |",
        f"| structural_valid_types | {report.summary.structural_valid_types} |",
        f"| structural_invalid_types | {report.summary.structural_invalid_types} |",
        f"| verification_passed_types | {report.summary.verification_passed_types} |",
        f"| verification_failed_types | {report.summary.verification_failed_types} |",
        f"| avg_target_efficiency | {report.summary.avg_target_efficiency:.6f} |",
        f"| min_target_efficiency | {report.summary.min_target_efficiency:.6f} |",
        f"| max_target_efficiency | {report.summary.max_target_efficiency:.6f} |",
        "",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")


def _build_dashboard_data(
    rows: list[ShelfValidationRow],
    summary: ShelfValidationSummary,
    reason_counter: dict[str, int],
) -> ShelfValidationDashboardData:
    reason_items = sorted(reason_counter.items(), key=lambda item: item[1], reverse=True)
    top_reasons = reason_items[:8]
    return ShelfValidationDashboardData(
        valid_count=summary.verification_passed_types,
        invalid_count=summary.verification_failed_types,
        efficiencies_passed=[row.target_efficiency for row in rows if row.verification_passed],
        efficiencies_failed=[row.target_efficiency for row in rows if not row.verification_passed],
        reason_labels=[item[0] for item in top_reasons] or ["no failure reason"],
        reason_values=[item[1] for item in top_reasons] or [0],
        table_rows=sorted(
            rows,
            key=lambda item: (item.verification_passed, -item.target_efficiency),
        )[:20],
    )


def _add_dashboard_result_counts(fig: Any, data: ShelfValidationDashboardData) -> None:
    import plotly.graph_objects as go

    fig.add_trace(
        go.Bar(
            x=["passed", "failed"],
            y=[data.valid_count, data.invalid_count],
            marker_color=["#2c7a7b", "#c53030"],
            name="verification",
            showlegend=False,
        ),
        row=1,
        col=1,
    )


def _add_dashboard_efficiency_histograms(fig: Any, data: ShelfValidationDashboardData) -> None:
    import plotly.graph_objects as go

    fig.add_trace(
        go.Histogram(
            x=data.efficiencies_passed,
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
            x=data.efficiencies_failed,
            name="failed",
            marker_color="#c53030",
            opacity=0.75,
            nbinsx=20,
        ),
        row=1,
        col=2,
    )


def _add_dashboard_failure_reasons(fig: Any, data: ShelfValidationDashboardData) -> None:
    import plotly.graph_objects as go

    fig.add_trace(
        go.Bar(
            x=data.reason_values,
            y=data.reason_labels,
            orientation="h",
            marker_color="#3182ce",
            name="failure reasons",
            showlegend=False,
        ),
        row=2,
        col=1,
    )


def _add_dashboard_table(fig: Any, data: ShelfValidationDashboardData) -> None:
    import plotly.graph_objects as go

    fig.add_trace(
        go.Table(
            header={
                "values": ["index", "verification_passed", "target_efficiency", "panel_count", "canonical_key"],
                "fill_color": "#e2e8f0",
                "align": "left",
            },
            cells={
                "values": [
                    [item.index for item in data.table_rows],
                    [item.verification_passed for item in data.table_rows],
                    [item.target_efficiency for item in data.table_rows],
                    [item.panel_count for item in data.table_rows],
                    [item.canonical_key for item in data.table_rows],
                ],
                "fill_color": "#f8fafc",
                "align": "left",
            },
        ),
        row=2,
        col=2,
    )


def _write_dashboard(
    report: ShelfValidationReportContext,
    output_path: Path,
) -> None:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = _build_dashboard_data(report.rows, report.summary, report.reason_counter)

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

    _add_dashboard_result_counts(fig, data)
    _add_dashboard_efficiency_histograms(fig, data)
    _add_dashboard_failure_reasons(fig, data)
    _add_dashboard_table(fig, data)

    fig.update_layout(
        title=(
            "Shelf Validation Dashboard | "
            f"types={report.summary.total_types}, passed={report.summary.verification_passed_types}, "
            f"failed={report.summary.verification_failed_types}"
        ),
        barmode="overlay",
        height=980,
        width=1600,
        template="plotly_white",
    )
    fig.update_yaxes(autorange="reversed", row=2, col=1)

    fig.write_html(str(output_path), include_plotlyjs=True, full_html=True)


def _write_json_summary(report: ShelfValidationReportContext, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report.summary.to_dict(), ensure_ascii=False, indent=2),
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
    report = ShelfValidationReportContext.build(
        rows=rows,
        reason_counter=reason_counter,
        mapping_default=mapping_default,
        mapping_changes=mapping_changes,
    )

    output_dir = Path(args.output_dir)
    artifacts = ShelfValidationArtifacts(
        csv=output_dir / "shelf_validation_table.csv",
        markdown=output_dir / "shelf_validation_summary.md",
        dashboard_html=output_dir / "shelf_validation_dashboard.html",
        summary_json=output_dir / "shelf_validation_summary.json",
    )

    _write_csv(rows, artifacts.csv)
    _write_markdown_summary(report, artifacts.markdown)
    _write_dashboard(report, artifacts.dashboard_html)
    _write_json_summary(report, artifacts.summary_json)

    print(
        json.dumps(
            {
                "summary": report.summary.to_dict(),
                "artifacts": artifacts.to_dict(),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
