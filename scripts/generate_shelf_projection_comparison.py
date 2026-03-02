from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _bool(value: str) -> bool:
    return str(value).strip().lower() == "true"


def _build_key_map(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["canonical_key"]: row for row in rows}


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _build_group_counts(rows: list[dict[str, str]]) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "pass": 0, "fail": 0})
    for row in rows:
        gid = row["group_id"]
        out[gid]["total"] += 1
        if _bool(row["passed"]):
            out[gid]["pass"] += 1
        else:
            out[gid]["fail"] += 1
    return dict(out)


def _write_dashboard(
    before_rows: list[dict[str, str]],
    after_rows: list[dict[str, str]],
    pass_diff_rows: list[dict[str, Any]],
    structural_diff_rows: list[dict[str, Any]],
    output_html: Path,
) -> None:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    before_pass = sum(1 for row in before_rows if _bool(row["passed"]))
    before_fail = len(before_rows) - before_pass
    after_pass = sum(1 for row in after_rows if _bool(row["passed"]))
    after_fail = len(after_rows) - after_pass

    before_group = _build_group_counts(before_rows)
    after_group = _build_group_counts(after_rows)
    group_ids = sorted(set(before_group.keys()) | set(after_group.keys()))
    before_group_pass = [before_group.get(gid, {}).get("pass", 0) for gid in group_ids]
    after_group_pass = [after_group.get(gid, {}).get("pass", 0) for gid in group_ids]
    before_group_fail = [before_group.get(gid, {}).get("fail", 0) for gid in group_ids]
    after_group_fail = [after_group.get(gid, {}).get("fail", 0) for gid in group_ids]

    pass_to_fail = [row for row in pass_diff_rows if row["change"] == "pass_to_fail"]
    fail_to_pass = [row for row in pass_diff_rows if row["change"] == "fail_to_pass"]
    structural_to_invalid = [row for row in structural_diff_rows if row["change"] == "structural_pass_to_fail"]
    structural_to_valid = [row for row in structural_diff_rows if row["change"] == "structural_fail_to_pass"]

    before_structural_valid = sum(1 for row in before_rows if _bool(row.get("structural_valid", "False")))
    before_structural_invalid = len(before_rows) - before_structural_valid
    after_structural_valid = sum(1 for row in after_rows if _bool(row.get("structural_valid", "False")))
    after_structural_invalid = len(after_rows) - after_structural_valid

    table_rows = (structural_diff_rows + pass_diff_rows)[:40]

    fig = make_subplots(
        rows=2,
        cols=2,
        specs=[
            [{"type": "xy"}, {"type": "xy"}],
            [{"type": "xy"}, {"type": "table"}],
        ],
        subplot_titles=(
            "Overall Pass/Fail: Before vs After",
            "Group-Level Pass Count Delta",
            "Flip Counts (Pass + Structural)",
            "Type-Level Flips (Top 40, structural first)",
        ),
        vertical_spacing=0.14,
        horizontal_spacing=0.09,
    )

    fig.add_trace(
        go.Bar(
            x=[
                "before_pass",
                "before_fail",
                "after_pass",
                "after_fail",
                "before_structural_valid",
                "before_structural_invalid",
                "after_structural_valid",
                "after_structural_invalid",
            ],
            y=[
                before_pass,
                before_fail,
                after_pass,
                after_fail,
                before_structural_valid,
                before_structural_invalid,
                after_structural_valid,
                after_structural_invalid,
            ],
            marker_color=["#2f855a", "#c53030", "#276749", "#9b2c2c", "#2b6cb0", "#718096", "#2c5282", "#4a5568"],
            showlegend=False,
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(x=group_ids, y=before_group_pass, name="before_pass", marker_color="#63b3ed"),
        row=1,
        col=2,
    )
    fig.add_trace(
        go.Bar(x=group_ids, y=after_group_pass, name="after_pass", marker_color="#2b6cb0"),
        row=1,
        col=2,
    )

    fig.add_trace(
        go.Bar(
            x=[
                "pass_to_fail",
                "fail_to_pass",
                "structural_pass_to_fail",
                "structural_fail_to_pass",
            ],
            y=[
                len(pass_to_fail),
                len(fail_to_pass),
                len(structural_to_invalid),
                len(structural_to_valid),
            ],
            marker_color=["#d64545", "#38a169", "#c05621", "#2b6cb0"],
            showlegend=False,
        ),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Table(
            header={
                "values": [
                    "change",
                    "group_id",
                    "canonical_key",
                    "ratio_before",
                    "ratio_after",
                    "structural_before",
                    "structural_after",
                    "reasons_after",
                ],
                "fill_color": "#e2e8f0",
                "align": "left",
            },
            cells={
                "values": [
                    [row["change"] for row in table_rows],
                    [row["group_id"] for row in table_rows],
                    [row["canonical_key"] for row in table_rows],
                    [row["projection_ratio_before"] for row in table_rows],
                    [row["projection_ratio_after"] for row in table_rows],
                    [row.get("structural_valid_before", "") for row in table_rows],
                    [row.get("structural_valid_after", "") for row in table_rows],
                    [row["reasons_after"] for row in table_rows],
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
            "Shelf Projection Validation: Before vs After R6 Rule"
            f" | types={len(after_rows)}, pass_flips={len(pass_diff_rows)}, structural_flips={len(structural_diff_rows)}"
        ),
        barmode="group",
        template="plotly_white",
        width=1800,
        height=1100,
    )
    fig.update_xaxes(title_text="group id", row=1, col=2)
    fig.update_yaxes(title_text="pass type count", row=1, col=2)

    output_html.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(output_html), include_plotlyjs=True, full_html=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare shelf projection validation before/after.")
    parser.add_argument(
        "--before-csv",
        default="docs/validation/compare/shelf_projection_validation_table_before_r6.csv",
    )
    parser.add_argument(
        "--after-csv",
        default="docs/validation/shelf_projection_validation_table.csv",
    )
    parser.add_argument(
        "--output-dir",
        default="docs/validation/compare",
    )
    args = parser.parse_args()

    before_csv = Path(args.before_csv)
    after_csv = Path(args.after_csv)
    output_dir = Path(args.output_dir)

    before_rows = _read_csv_rows(before_csv)
    after_rows = _read_csv_rows(after_csv)
    before_map = _build_key_map(before_rows)
    after_map = _build_key_map(after_rows)

    all_keys = sorted(set(before_map.keys()) | set(after_map.keys()))
    pass_diff_rows: list[dict[str, Any]] = []
    structural_diff_rows: list[dict[str, Any]] = []
    for key in all_keys:
        b = before_map.get(key)
        a = after_map.get(key)
        if b is None or a is None:
            continue
        b_pass = _bool(b["passed"])
        a_pass = _bool(a["passed"])
        if b_pass != a_pass:
            pass_diff_rows.append(
                {
                    "canonical_key": key,
                    "group_id": a["group_id"],
                    "change": "pass_to_fail" if b_pass and not a_pass else "fail_to_pass",
                    "projection_ratio_before": b["projection_ratio"],
                    "projection_ratio_after": a["projection_ratio"],
                    "structural_valid_before": b.get("structural_valid", ""),
                    "structural_valid_after": a.get("structural_valid", ""),
                    "reasons_after": a["reasons"],
                }
            )

        b_struct = _bool(b.get("structural_valid", "False"))
        a_struct = _bool(a.get("structural_valid", "False"))
        if b_struct != a_struct:
            structural_diff_rows.append(
                {
                    "canonical_key": key,
                    "group_id": a["group_id"],
                    "change": "structural_pass_to_fail" if b_struct and not a_struct else "structural_fail_to_pass",
                    "projection_ratio_before": b["projection_ratio"],
                    "projection_ratio_after": a["projection_ratio"],
                    "structural_valid_before": b.get("structural_valid", ""),
                    "structural_valid_after": a.get("structural_valid", ""),
                    "reasons_after": a["reasons"],
                }
            )

    pass_diff_rows.sort(key=lambda item: (item["change"], item["group_id"], item["canonical_key"]))
    structural_diff_rows.sort(key=lambda item: (item["change"], item["group_id"], item["canonical_key"]))

    diff_csv = output_dir / "shelf_projection_validation_diff_types.csv"
    summary_json = output_dir / "shelf_projection_validation_compare_summary.json"
    dashboard_html = output_dir / "shelf_projection_validation_compare_dashboard.html"

    _write_csv(
        path=diff_csv,
        rows=structural_diff_rows + pass_diff_rows,
        fieldnames=[
            "change",
            "group_id",
            "canonical_key",
            "projection_ratio_before",
            "projection_ratio_after",
            "structural_valid_before",
            "structural_valid_after",
            "reasons_after",
        ],
    )
    _write_dashboard(
        before_rows=before_rows,
        after_rows=after_rows,
        pass_diff_rows=pass_diff_rows,
        structural_diff_rows=structural_diff_rows,
        output_html=dashboard_html,
    )

    payload = {
        "before_csv": str(before_csv),
        "after_csv": str(after_csv),
        "type_total_before": len(before_rows),
        "type_total_after": len(after_rows),
        "pass_flip_count": len(pass_diff_rows),
        "pass_to_fail": sum(1 for row in pass_diff_rows if row["change"] == "pass_to_fail"),
        "fail_to_pass": sum(1 for row in pass_diff_rows if row["change"] == "fail_to_pass"),
        "structural_flip_count": len(structural_diff_rows),
        "structural_pass_to_fail": sum(
            1 for row in structural_diff_rows if row["change"] == "structural_pass_to_fail"
        ),
        "structural_fail_to_pass": sum(
            1 for row in structural_diff_rows if row["change"] == "structural_fail_to_pass"
        ),
        "artifacts": {
            "diff_csv": str(diff_csv),
            "dashboard_html": str(dashboard_html),
        },
    }
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
