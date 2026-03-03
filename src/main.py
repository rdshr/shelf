from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any

from shelf_framework import (
    BoundaryDefinition,
    CombinationRules,
    Footprint2D,
    Goal,
    Hypothesis,
    LogicRecord,
    LogicStep,
    Module,
    Opening2D,
    Space3D,
    VerificationInput,
    evaluate_boundary_checks,
    evaluate_structural_checks,
    generate_shelf_type_specs,
    infer_grid_dimensions,
    modules_to_list,
    strict_mapping_meta,
    verify,
)

REPORT_JSON_PATH = Path("docs/shelf_visual_report.json")
REPORT_DATA_JS_PATH = Path("docs/shelf_visual_report.data.js")
GROUPS_HTML_PATH = Path("docs/groups.html")
GROUP_HTML_PATH = Path("docs/group.html")
TYPE_HTML_PATH = Path("docs/type.html")
LANDING_HTML_PATH = Path("docs/shelf_visual_report.html")

RULE_DISPLAY: dict[str, str] = {
    "B1": "B1 层数上限",
    "B2": "B2 固定占地",
    "C2": "C2 支撑连续性",
    "C3": "C3 稳定投影",
    "C4": "C4 上层参与",
    "COMBO": "组合契约",
    "EFF": "效率目标",
    "BOUNDARY": "边界定义",
    "OTHER": "其他",
}

BASE_STYLE = """
:root {
  --bg: #f5f5f7;
  --bg-soft: #ffffff;
  --panel: rgba(255, 255, 255, 0.92);
  --panel-strong: rgba(255, 255, 255, 0.98);
  --border: rgba(0, 0, 0, 0.12);
  --fg: #1d1d1f;
  --muted: #6e6e73;
  --ok: #0c7e52;
  --bad: #b4233a;
  --warn: #f5c978;
  --accent: #0071e3;
  --accent-2: #2997ff;
  --wood-light: #efbf8b;
  --wood-dark: #9a6f45;
  --metal: #77c4ff;
  --connector: #5ef0e4;
}

* {
  box-sizing: border-box;
}

html, body {
  margin: 0;
  padding: 0;
}

body {
  min-height: 100vh;
  color: var(--fg);
  font-family: "SF Pro Text", "SF Pro Display", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  background:
    radial-gradient(520px 260px at 50% -20%, rgba(0, 113, 227, 0.08), transparent 70%),
    linear-gradient(180deg, #fafafc, #f4f5f7),
    var(--bg);
  padding: 18px;
}

.shell {
  max-width: 1480px;
  margin: 0 auto;
  display: grid;
  gap: 14px;
}

.hero {
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 18px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(250, 251, 253, 0.96));
  position: relative;
  overflow: hidden;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.06);
}

.hero::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(220px 120px at 10% -10%, rgba(0, 113, 227, 0.08), transparent 66%),
    radial-gradient(220px 120px at 100% 0, rgba(41, 151, 255, 0.08), transparent 70%);
}

.hero h1 {
  position: relative;
  margin: 0;
  font-size: clamp(20px, 2.3vw, 30px);
  letter-spacing: 0.03em;
  color: #1d1d1f;
  font-family: "SF Pro Display", "PingFang SC", sans-serif;
  font-weight: 600;
}

.hero p {
  position: relative;
  margin: 8px 0 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.5;
}

.chips {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 5px 9px;
  font-size: 11px;
  color: #2d2d30;
  background: rgba(255, 255, 255, 0.9);
}

.card {
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--panel);
  padding: 12px;
  box-shadow: 0 10px 24px rgba(2, 9, 18, 0.34);
}

.card h2 {
  margin: 0;
  font-size: 16px;
  letter-spacing: 0.03em;
  color: #1d1d1f;
}

.sub {
  margin-top: 6px;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.45;
}

.toolbar {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.btn {
  border: 1px solid rgba(0, 0, 0, 0.15);
  background: rgba(255, 255, 255, 0.96);
  color: #1d1d1f;
  border-radius: 10px;
  padding: 6px 10px;
  font-size: 12px;
  cursor: pointer;
}

.btn:hover {
  border-color: rgba(0, 113, 227, 0.55);
  background: rgba(248, 251, 255, 1);
}

  .btn.accent {
  border-color: rgba(0, 113, 227, 0.65);
  background: linear-gradient(180deg, rgba(30, 141, 255, 0.95), rgba(0, 113, 227, 0.94));
  color: #fff;
}

select,
input[type="number"],
input[type="range"] {
  border: 1px solid rgba(0, 0, 0, 0.16);
  background: rgba(255, 255, 255, 0.95);
  color: #1d1d1f;
  border-radius: 10px;
  padding: 6px 8px;
  font-size: 12px;
}

.grid-2 {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.grid-3 {
  display: grid;
  grid-template-columns: minmax(300px, 360px) minmax(0, 1fr);
  gap: 12px;
  align-items: start;
}

.primary-grid {
  margin-top: 12px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 10px;
}

.primary-card {
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  padding: 10px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(249, 250, 252, 0.96));
  display: grid;
  gap: 8px;
  position: relative;
  overflow: hidden;
}

.primary-card::after {
  content: "";
  position: absolute;
  inset: auto -40% -72% -40%;
  height: 160px;
  background: radial-gradient(closest-side, rgba(0, 113, 227, 0.08), transparent 70%);
  pointer-events: none;
}

.primary-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.primary-title {
  font-size: 13px;
  font-weight: 700;
  color: #1d1d1f;
}

.meter {
  position: relative;
  width: 100%;
  height: 7px;
  border-radius: 99px;
  overflow: hidden;
  background: rgba(138, 176, 214, 0.22);
}

.meter > span {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  border-radius: inherit;
  background: linear-gradient(90deg, #55d7a2, #5ec8ff);
}

.pill {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  font-size: 11px;
  padding: 3px 8px;
  border: 1px solid transparent;
}

.pill.ok {
  background: rgba(75, 198, 147, 0.16);
  border-color: rgba(93, 218, 167, 0.42);
  color: #70f3bf;
}

.pill.bad {
  background: rgba(255, 118, 140, 0.14);
  border-color: rgba(255, 132, 153, 0.46);
  color: #ff9cae;
}

.secondary-table {
  margin-top: 2px;
  display: grid;
  gap: 6px;
}

.secondary-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  align-items: center;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 10px;
  padding: 7px;
  background: rgba(255, 255, 255, 0.9);
}

.secondary-row a {
  color: #0071e3;
  text-decoration: none;
}

.secondary-row a:hover {
  color: #005bb5;
}

.meta-line {
  font-size: 11px;
  color: var(--muted);
}

.catalog {
  margin-top: 12px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 9px;
}

.type-card {
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 12px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 249, 251, 0.96));
  padding: 8px;
  display: grid;
  gap: 8px;
  cursor: pointer;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
}

.type-card:hover {
  border-color: rgba(0, 113, 227, 0.55);
  transform: translateY(-1px);
}

.type-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  color: #6e6e73;
}

.mini-stack {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
}

.mini-layer {
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 8px;
  padding: 4px;
  background: rgba(255, 255, 255, 0.9);
}

.mini-layer .sub {
  margin: 0 0 4px;
  font-size: 10px;
}

.type-card .chips {
  margin-top: 0;
  gap: 5px;
}

.type-card .chip {
  font-size: 10px;
  padding: 3px 7px;
}

.matrix {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 4px;
}

.cell {
  aspect-ratio: 1/1;
  border-radius: 5px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  background: rgba(210, 216, 224, 0.35);
}

.cell.active {
  background: linear-gradient(152deg, rgba(247, 179, 114, 0.96), rgba(204, 125, 63, 0.94));
  border-color: rgba(255, 218, 176, 0.88);
}

.viewer-wrap {
  display: grid;
  gap: 10px;
}

.canvas-wrap {
  border: 1px solid rgba(106, 169, 230, 0.28);
  border-radius: 12px;
  padding: 8px;
  background:
    radial-gradient(150% 100% at 22% 0, rgba(101, 191, 255, 0.22), transparent 58%),
    radial-gradient(120% 110% at 100% 100%, rgba(255, 170, 103, 0.15), transparent 56%),
    rgba(7, 20, 37, 0.88);
}

.viewer-canvas {
  width: 100%;
  height: 420px;
  display: block;
  border-radius: 8px;
  background:
    radial-gradient(64% 88% at 52% 46%, rgba(82, 96, 113, 0.72), rgba(37, 45, 56, 0.9)),
    linear-gradient(180deg, rgba(84, 97, 113, 0.55), rgba(33, 41, 52, 0.9));
  cursor: grab;
}

.viewer-canvas.dragging {
  cursor: grabbing;
}

.viewer-controls {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.viewer-controls label {
  display: grid;
  gap: 4px;
  font-size: 11px;
  color: var(--muted);
}

.switches {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.switches label {
  display: inline-flex;
  gap: 6px;
  align-items: center;
  font-size: 12px;
  color: var(--muted);
}

.rules {
  margin-top: 10px;
  display: grid;
  gap: 6px;
}

.rule-row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 8px;
  padding: 6px 7px;
  background: rgba(255, 255, 255, 0.9);
  font-size: 12px;
}

.rule-row .state-ok {
  color: var(--ok);
}

.rule-row .state-bad {
  color: var(--bad);
}

.rule-row .state-pending {
  color: var(--muted);
}

.reason-box {
  margin-top: 8px;
  border: 1px dashed rgba(255, 135, 154, 0.5);
  border-radius: 10px;
  padding: 8px;
  color: #9a1c32;
  font-size: 12px;
  min-height: 60px;
  background: rgba(255, 242, 245, 0.9);
}

.meta-box {
  margin-top: 8px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 10px;
  padding: 8px;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.45;
  background: rgba(255, 255, 255, 0.92);
}

.diff-box {
  margin-top: 8px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 10px;
  padding: 8px;
  color: #6e4b2f;
  font-size: 12px;
  line-height: 1.45;
  background: rgba(255, 249, 241, 0.96);
}

.hidden {
  display: none !important;
}

.breadcrumb {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 12px;
  color: var(--muted);
}

.breadcrumb a {
  color: #0071e3;
  text-decoration: none;
}

.breadcrumb a:hover {
  color: #005bb5;
}

.viz-grid {
  margin-top: 12px;
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  gap: 8px;
}

.viz-card {
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 10px;
  padding: 8px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.97), rgba(249, 250, 252, 0.96));
  min-height: 160px;
}

.viz-card h3 {
  margin: 0;
  font-size: 13px;
  letter-spacing: 0.02em;
  color: #1d1d1f;
}

.ring-wrap {
  height: 124px;
  display: grid;
  place-items: center;
}

.ring-meter {
  --pct: 0%;
  width: 102px;
  height: 102px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background:
    radial-gradient(circle at 50% 50%, rgba(255, 255, 255, 1) 47%, transparent 48%),
    conic-gradient(from -90deg, rgba(0, 113, 227, 0.9) 0 var(--pct), rgba(136, 146, 156, 0.2) var(--pct) 100%);
  box-shadow:
    0 0 0 8px rgba(0, 113, 227, 0.08),
    inset 0 0 18px rgba(0, 113, 227, 0.15);
}

.ring-meter span {
  font-size: 15px;
  font-weight: 700;
  color: #1d1d1f;
}

.hist-bars {
  margin-top: 6px;
  height: 124px;
  display: grid;
  grid-template-columns: repeat(9, minmax(0, 1fr));
  gap: 4px;
  align-items: end;
}

.hist-col {
  display: grid;
  gap: 3px;
  justify-items: center;
}

.hist-bar {
  width: 100%;
  border-radius: 8px 8px 4px 4px;
  border: 1px solid rgba(111, 170, 228, 0.42);
  background: linear-gradient(180deg, rgba(255, 143, 156, 0.8), rgba(189, 83, 101, 0.86));
  min-height: 6px;
  position: relative;
  overflow: hidden;
}

.hist-pass {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(180deg, rgba(96, 206, 255, 0.95), rgba(51, 149, 214, 0.93));
}

.gallery-strip {
  margin-top: 8px;
  display: grid;
  grid-template-columns: repeat(8, minmax(120px, 1fr));
  gap: 8px;
}

.sample-tile {
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 8px;
  padding: 6px;
  background: rgba(255, 255, 255, 0.94);
  text-decoration: none;
  color: #1d1d1f;
  display: grid;
  gap: 4px;
  min-height: 120px;
}

.sample-tile:hover {
  border-color: rgba(0, 113, 227, 0.55);
}

.sample-head {
  display: flex;
  justify-content: space-between;
  gap: 6px;
  font-size: 10px;
  color: #6e6e73;
}

.sample-mini {
  display: grid;
  gap: 2px;
}

.sample-cell {
  aspect-ratio: 1/1;
  border-radius: 2px;
  border: 1px solid rgba(0, 0, 0, 0.11);
  background: rgba(198, 205, 214, 0.32);
}

.sample-cell.active {
  background: linear-gradient(150deg, rgba(245, 185, 122, 0.95), rgba(201, 123, 62, 0.92));
}

.rule-switches {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.rule-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid rgba(0, 0, 0, 0.14);
  border-radius: 999px;
  padding: 5px 9px;
  font-size: 12px;
  background: rgba(255, 255, 255, 0.92);
  color: #1d1d1f;
}

.stage-shell {
  margin-top: 8px;
  display: grid;
  grid-template-columns: 248px 1fr;
  gap: 12px;
}

.stage-sidebar {
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 12px;
  padding: 12px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 249, 251, 0.95));
  display: grid;
  gap: 9px;
  align-content: start;
}

.stage-title {
  margin: 0;
  font-size: 11px;
  color: #6e6e73;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.module-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  border: 1px solid rgba(0, 0, 0, 0.14);
  border-radius: 999px;
  padding: 5px 8px;
  font-size: 12px;
  color: #1d1d1f;
  background: rgba(255, 255, 255, 0.92);
}

.module-chip b {
  font-size: 11px;
  color: #6e6e73;
  margin-left: auto;
}

.material-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
}

.mat-swatch {
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 8px;
  padding: 6px;
  font-size: 10px;
  color: #4f5964;
  display: grid;
  gap: 4px;
}

.swatch-dot {
  width: 100%;
  height: 12px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.16);
}

.swatch-wood-light {
  background: linear-gradient(90deg, #edc38f, #d89d62);
}

.swatch-wood-dark {
  background: linear-gradient(90deg, #ad8156, #6e4e2f);
}

.swatch-metal {
  background: linear-gradient(90deg, #c4ccd4, #8f9aa5);
}

.swatch-connector {
  background: linear-gradient(90deg, #d6dde6, #a5afba);
}

.stage-main {
  display: grid;
  gap: 8px;
}

.boundary-mask-grid {
  display: grid;
  gap: 4px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 10px;
  padding: 6px;
  background: rgba(255, 255, 255, 0.92);
}

.boundary-mask-cell {
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 6px;
  background: rgba(205, 212, 220, 0.35);
  min-height: 24px;
  cursor: pointer;
  transition: all 120ms ease;
}

.boundary-mask-cell:hover {
  border-color: rgba(0, 113, 227, 0.55);
}

.boundary-mask-cell.active {
  background: linear-gradient(155deg, rgba(255, 184, 116, 0.95), rgba(210, 127, 60, 0.95));
  border-color: rgba(255, 230, 195, 0.9);
  box-shadow: inset 0 0 0 1px rgba(255, 245, 228, 0.22);
}

.stage-sidebar .viewer-controls {
  grid-template-columns: 1fr;
}

.stage-sidebar .switches {
  display: grid;
  gap: 6px;
  margin-top: 0;
}

.stage-sidebar .switches label {
  font-size: 11px;
}

.stage-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

@media (max-width: 1120px) {
  .grid-3 {
    grid-template-columns: 1fr;
  }

  .viz-grid {
    grid-template-columns: 1fr;
  }

  .stage-shell {
    grid-template-columns: 1fr;
  }

  .gallery-strip {
    grid-template-columns: repeat(4, minmax(120px, 1fr));
  }
}

@media (max-width: 900px) {
  body {
    padding: 10px;
  }

  .grid-2 {
    grid-template-columns: 1fr;
  }

  .viewer-controls {
    grid-template-columns: 1fr;
  }

  .hist-bars {
    grid-template-columns: repeat(6, minmax(0, 1fr));
  }

  .gallery-strip {
    grid-template-columns: repeat(2, minmax(120px, 1fr));
  }
}
"""


def build_logic_record(
    goal: Goal,
    boundary: BoundaryDefinition,
    result_ok: bool,
    summary: dict[str, Any],
    grouping: dict[str, Any],
) -> LogicRecord:
    """构建可追溯逻辑记录，用于输出 L3 证据文件。"""
    steps = [
        LogicStep("G", "goal", evidence=goal.to_dict()),
        LogicStep("B1", "layers", ["G"], {"N": boundary.layers_n}),
        LogicStep("B2", "payload", ["G"], {"P": boundary.payload_p_per_layer}),
        LogicStep("B3", "space", ["G"], {"S": boundary.space_s_per_layer.__dict__}),
        LogicStep("B4", "opening", ["G"], {"O": boundary.opening_o.__dict__}),
        LogicStep("B5", "footprint", ["G"], {"A": boundary.footprint_a.__dict__}),
        LogicStep("M1", "rod", ["B1", "B2"]),
        LogicStep("M2", "connector", ["B1", "B4"]),
        LogicStep("M3", "panel", ["B2", "B3"]),
        LogicStep("C1", "module contract (panel requires rod+connector)", ["M1", "M2", "M3"]),
        LogicStep("C2", "support continuity (rod path + connectivity)", ["C1", "B1", "B5"]),
        LogicStep("C3", "projection stability", ["C2", "B5"]),
        LogicStep("C4", "upper-layer engagement in multi-layer mode", ["C2", "B1"]),
        LogicStep("H1", "efficiency improves under valid constraints", ["C1", "C2", "C3", "C4"]),
        LogicStep("V1", "verify hypothesis", ["H1"], {"passed": result_ok}),
        LogicStep(
            "V2",
            "catalog validation",
            ["V1"],
            {
                "total_types": summary["total"],
                "passed": summary["passed"],
                "failed": summary["failed"],
                "primary_groups": grouping["primary_group_count"],
                "secondary_groups": grouping["secondary_group_count"],
            },
        ),
        LogicStep("C", "conclusion", ["V2"], {"adopt_now": result_ok}),
    ]
    return LogicRecord.build(steps)


def compute_ratio_histogram(values: list[float], bins: int = 10) -> list[dict[str, Any]]:
    if not values:
        return []

    lower = 0.0
    upper = max(2.0, max(values))
    width = (upper - lower) / bins

    hist: list[dict[str, Any]] = []
    for idx in range(bins):
        start = lower + idx * width
        end = lower + (idx + 1) * width
        hist.append({"start": round(start, 3), "end": round(end, 3), "count": 0})

    for value in values:
        if value >= upper:
            hist[-1]["count"] += 1
            continue
        slot = int((value - lower) // width)
        hist[max(0, min(bins - 1, slot))]["count"] += 1

    return hist


def support_profile(layer_masks: list[int]) -> tuple[int, int]:
    supported = 0
    unsupported = 0

    for idx in range(1, len(layer_masks)):
        upper = layer_masks[idx]
        lower = layer_masks[idx - 1]
        supported += (upper & lower).bit_count()
        unsupported += (upper & ~lower).bit_count()

    return supported, unsupported


def ratio_bin(value: float, step: float = 0.25) -> tuple[float, float]:
    start = math.floor(value / step) * step
    end = start + step
    return round(start, 2), round(end, 2)


def collect_failure_codes(type_item: dict[str, Any]) -> list[str]:
    checks = type_item["structural_checks"]
    verification = type_item["verification"]

    codes: list[str] = []
    if not checks.get("B1_layers_within_limit", True):
        codes.append("B1")
    if not checks.get("B2_fixed_footprint", True):
        codes.append("B2")
    if not checks.get("C2_support_continuity", True):
        codes.append("C2")
    if not checks.get("C3_center_projection_stable", True):
        codes.append("C3")
    if not checks.get("C4_upper_layer_engaged", True):
        codes.append("C4")

    if not verification.get("combination_valid", True):
        codes.append("COMBO")
    if not verification.get("efficiency_improved", True):
        codes.append("EFF")

    if not verification.get("boundary_valid", True) and not ({"B1", "B2"} & set(codes)):
        codes.append("BOUNDARY")

    if not verification.get("passed", False) and not codes:
        codes.append("OTHER")

    return codes


def build_secondary_signature(type_item: dict[str, Any]) -> dict[str, Any]:
    cells = type_item["active_cells_per_layer"]
    supported, unsupported = support_profile(type_item["layer_masks"])
    r_start, r_end = ratio_bin(type_item["projection_ratio"])

    sec_id = (
        "L"
        + "-".join(str(item) for item in cells)
        + f"_SUP{supported}-{unsupported}_PR{r_start:.2f}-{r_end:.2f}"
    )

    return {
        "id": sec_id,
        "label": (
            f"cells/layer={tuple(cells)} | support={supported}/{unsupported} | "
            f"ratio_bin=[{r_start:.2f},{r_end:.2f})"
        ),
        "signature": {
            "cells_per_layer": list(cells),
            "supported_cells": supported,
            "unsupported_cells": unsupported,
            "projection_ratio_bin": [r_start, r_end],
        },
    }


def build_grouping(types: list[dict[str, Any]]) -> dict[str, Any]:
    primary_map: dict[str, dict[str, Any]] = {}

    for type_item in types:
        failure_codes = collect_failure_codes(type_item)
        primary_id = "PASS" if not failure_codes else "FAIL_" + "_".join(failure_codes)

        if primary_id not in primary_map:
            if primary_id == "PASS":
                label = "PASS | 全部规则通过"
                description = "一级组依据：失败规则集合为空（所有规则通过）"
            else:
                fail_names = [RULE_DISPLAY.get(code, code) for code in failure_codes]
                label = "FAIL | " + " + ".join(fail_names)
                description = "一级组依据：失败规则集合=" + ", ".join(failure_codes)

            primary_map[primary_id] = {
                "id": primary_id,
                "label": label,
                "description": description,
                "failure_codes": failure_codes,
                "total": 0,
                "passed": 0,
                "failed": 0,
                "secondary": {},
            }

        primary = primary_map[primary_id]
        primary["total"] += 1
        primary[type_item["status"]] += 1

        secondary = build_secondary_signature(type_item)
        sec = primary["secondary"].get(secondary["id"])
        if sec is None:
            sec = {
                "id": secondary["id"],
                "label": secondary["label"],
                "signature": secondary["signature"],
                "total": 0,
                "passed": 0,
                "failed": 0,
                "type_ids": [],
            }
            primary["secondary"][secondary["id"]] = sec

        sec["total"] += 1
        sec[type_item["status"]] += 1
        sec["type_ids"].append(type_item["type_id"])

    primary_groups = list(primary_map.values())
    for primary in primary_groups:
        secondary_groups = list(primary["secondary"].values())
        for secondary in secondary_groups:
            secondary["type_ids"] = sorted(secondary["type_ids"])

        secondary_groups.sort(
            key=lambda item: (
                -item["total"],
                item["signature"]["cells_per_layer"],
                item["signature"]["supported_cells"],
                item["signature"]["unsupported_cells"],
            )
        )
        primary["secondary_groups"] = secondary_groups
        del primary["secondary"]

    primary_groups.sort(
        key=lambda item: (
            0 if item["id"] == "PASS" else 1,
            -item["total"],
            item["id"],
        )
    )

    secondary_count = sum(len(item["secondary_groups"]) for item in primary_groups)

    return {
        "basis": {
            "primary": "一级组按照失败规则集合划分；失败规则集合相同即同组。",
            "secondary": (
                "二级组在一级组内按照结构签名划分："
                "(cells_per_layer, supported_cells/unsupported_cells, projection_ratio_bin)。"
            ),
            "formula": "secondary_key = L{cells}-SUP{supported}-{unsupported}-PR{ratio_bin}",
            "rule_catalog": RULE_DISPLAY,
        },
        "primary_group_count": len(primary_groups),
        "secondary_group_count": secondary_count,
        "primary_groups": primary_groups,
    }


def build_report_payload(
    goal: Goal,
    boundary: BoundaryDefinition,
    hypothesis: Hypothesis,
    candidate_combo: set[Module],
    valid_combos: list[set[Module]],
    types: list[dict[str, Any]],
    meta: dict[str, Any],
    verification_result: dict[str, Any],
) -> dict[str, Any]:
    ratios = [item["projection_ratio"] for item in types]
    total = len(types)
    passed = sum(1 for item in types if item["status"] == "passed")
    failed = total - passed

    grouping = build_grouping(types)

    return {
        "title": "Shelf Type Grouping + 3D Explorer",
        "goal": goal.to_dict(),
        "boundary": {
            **boundary.to_dict(),
            "footprint_area_cells": meta["footprint_area_cells"],
            "grid_width": meta["grid_width"],
            "grid_depth": meta["grid_depth"],
            "max_layers": meta["max_layers"],
        },
        "hypothesis": hypothesis.to_dict(),
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "primary_group_count": grouping["primary_group_count"],
            "secondary_group_count": grouping["secondary_group_count"],
        },
        "histogram": compute_ratio_histogram(ratios, bins=9),
        "meta": {
            "footprint_area_cells": meta["footprint_area_cells"],
            "grid_width": meta["grid_width"],
            "grid_depth": meta["grid_depth"],
            "cell_count": meta["cell_count"],
            "max_layers": meta["max_layers"],
            "baseline_efficiency": meta["baseline_efficiency"],
            "module_combo": meta["module_combo"],
            "valid_combinations": meta["valid_combinations"],
        },
        "grouping": grouping,
        "types": sorted(types, key=lambda item: item["type_id"]),
        "candidate": {
            "combo": modules_to_list(candidate_combo),
            "verification": verification_result,
        },
        "strict_mapping": strict_mapping_meta(),
        "logic_record_path": "docs/logic_record.json",
    }


def variant_key(area_cells: int, max_layers: int) -> str:
    return f"A{area_cells}_N{max_layers}"


def env_int(name: str, default: int, minimum: int = 1) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(minimum, value)


def render_page(title: str, body: str, script: str) -> str:
    template = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>__TITLE__</title>
  <style>
__STYLE__
  </style>
</head>
<body>
  __BODY__
  <script src="shelf_visual_report.data.js"></script>
  <script>
__SCRIPT__
  </script>
</body>
</html>
"""
    return (
        template.replace("__TITLE__", title)
        .replace("__STYLE__", BASE_STYLE)
        .replace("__BODY__", body)
        .replace("__SCRIPT__", script)
    )


def render_groups_page(report_payload: dict[str, Any]) -> str:
    body = """
<div class="shell">
  <header class="hero">
    <h1 id="title"></h1>
    <p id="desc"></p>
    <div class="chips" id="chips"></div>
    <div class="chips" id="hero-kpis"></div>
    <div class="toolbar">
      <label class="sub">占地 A:</label>
      <input id="boundary-area" type="number" step="1" />
      <label class="sub">层数上限 N:</label>
      <input id="boundary-layers" type="number" step="1" />
      <button class="btn accent" id="apply-boundary" type="button">应用边界</button>
    </div>
  </header>

  <section class="card">
    <h2>规则实验室</h2>
    <div class="sub">可临时关闭规则，观察“放宽约束”后会出现哪些风险结构。</div>
    <div class="rule-switches" id="rule-switches"></div>
    <div class="chips" id="rule-impact"></div>
    <div class="sub" id="rule-note"></div>
  </section>

  <section class="card">
    <h2>组合可视化总览</h2>
    <div class="sub">压缩显示通过率与分布，避免大面积留白。点击分型可直达 3D。</div>
    <div class="viz-grid">
      <article class="viz-card">
        <h3>通过率</h3>
        <div class="ring-wrap">
          <div class="ring-meter" id="pass-ring">
            <span id="pass-ring-text"></span>
          </div>
        </div>
      </article>
      <article class="viz-card">
        <h3>投影比率分布</h3>
        <div class="hist-bars" id="ratio-hist"></div>
      </article>
    </div>
    <div class="gallery-strip" id="sample-gallery"></div>
  </section>

  <section class="card">
    <h2>组划分依据</h2>
    <div class="sub" id="basis-primary"></div>
    <div class="sub" id="basis-secondary"></div>
    <div class="sub" id="basis-formula"></div>
  </section>

  <section class="card">
    <h2>一级组总览</h2>
    <div class="sub">点击一级组或二级组进入组合列表页，再进入 3D 详情页。</div>
    <div class="primary-grid" id="primary-grid"></div>
  </section>
</div>
"""

    script = """
const report = window.__SHELF_REPORT__ || {};
const variantMap = report.variants || {};
const variantRuleCache = {};
Object.keys(variantMap).forEach((key) => {
  variantRuleCache[key] = "11111";
});
const profiles = (report.boundary_profiles || []).slice();
const params = new URLSearchParams(location.search);
const RULE_DEFS = [
  { id: "B2", label: "B2 固定占地", check: "B2_fixed_footprint", source: "structural" },
  { id: "C2", label: "C2 支撑连续", check: "C2_support_continuity", source: "structural" },
  { id: "C3", label: "C3 稳定投影", check: "C3_center_projection_stable", source: "structural" },
  { id: "C4", label: "C4 层完整性", check: "C4_upper_layer_engaged", source: "structural" },
  { id: "EFF", label: "EFF 效率目标", check: "efficiency_improved", source: "verification" },
];
const RULE_ORDER = RULE_DEFS.map((item) => item.id);

function decodeRuleMask(raw) {
  const base = Object.fromEntries(RULE_ORDER.map((id) => [id, true]));
  if (!raw) {
    return base;
  }
  const bits = raw.split("");
  RULE_ORDER.forEach((id, idx) => {
    if (bits[idx] === "0") {
      base[id] = false;
    }
  });
  return base;
}

function encodeRuleMask(rules) {
  return RULE_ORDER.map((id) => (rules[id] ? "1" : "0")).join("");
}

function fallbackVariantKey() {
  return report.default_variant_key || (profiles[0] ? profiles[0].key : "") || Object.keys(variantMap)[0] || "";
}

function normalizeVariantKey(key) {
  if (key && variantMap[key]) {
    return key;
  }
  return fallbackVariantKey();
}

const state = {
  variant: normalizeVariantKey(params.get("variant") || localStorage.getItem("shelf_variant_key") || report.default_variant_key),
  rules: decodeRuleMask(params.get("rr") || localStorage.getItem("shelf_rule_mask") || ""),
  evaluated: [],
};

function activeVariant() {
  return variantMap[state.variant] || report;
}

function pct(part, total) {
  if (!total) return "0.0";
  return ((part / total) * 100).toFixed(1);
}

function pctNumber(part, total) {
  if (!total) return 0;
  return (part / total) * 100;
}

function uniqueNumbers(items) {
  return Array.from(new Set(items)).sort((a, b) => a - b);
}

function keyByAreaLayers(area, layers) {
  const match = profiles.find((item) => item.area === area && item.max_layers === layers);
  return match ? match.key : fallbackVariantKey();
}

function nearestVariantKey(area, layers) {
  if (!profiles.length) {
    return fallbackVariantKey();
  }
  const exact = profiles.find((item) => item.area === area && item.max_layers === layers);
  if (exact) {
    return exact.key;
  }

  let best = profiles[0];
  let bestScore = Number.POSITIVE_INFINITY;
  profiles.forEach((item) => {
    const score = Math.abs(item.area - area) * 10 + Math.abs(item.max_layers - layers);
    if (score < bestScore) {
      bestScore = score;
      best = item;
    }
  });
  return best.key;
}

function profileByKey(key) {
  return profiles.find((item) => item.key === key) || null;
}

function parseVariantKey(key) {
  const m = /^A(\\d+)_N(\\d+)$/.exec(key || "");
  if (!m) return null;
  return {
    area: Number.parseInt(m[1], 10),
    layers: Number.parseInt(m[2], 10),
  };
}

async function ensureVariantGenerated(area, layers, ruleMask) {
  const key = `A${area}_N${layers}`;
  if (variantMap[key] && variantRuleCache[key] === ruleMask) {
    return key;
  }
  const url = `/api/variant?area=${encodeURIComponent(area)}&layers=${encodeURIComponent(layers)}&rr=${encodeURIComponent(ruleMask)}`;
  const resp = await fetch(url, { method: "GET" });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || `HTTP ${resp.status}`);
  }
  const payload = await resp.json();
  if (!payload || !payload.key || !payload.variant) {
    throw new Error("invalid variant payload");
  }
  variantMap[payload.key] = payload.variant;
  variantRuleCache[payload.key] = payload.rule_mask || ruleMask;
  if (payload.profile && !profiles.some((item) => item.key === payload.profile.key)) {
    profiles.push(payload.profile);
  }
  return payload.key;
}

function efficiencyImprovedRuntime(typeItem) {
  const v = activeVariant();
  const baseCells = (typeItem.active_cells_per_layer && typeItem.active_cells_per_layer[0]) || 0;
  const denominator = state.rules.B2 ? v.meta.footprint_area_cells : Math.max(1, baseCells);
  const runtimeEfficiency = typeItem.total_active_cells / denominator;
  return runtimeEfficiency > v.meta.baseline_efficiency;
}

function ruleResult(typeItem, ruleId) {
  const rule = RULE_DEFS.find((item) => item.id === ruleId);
  if (!rule) {
    return true;
  }
  if (rule.id === "EFF") {
    return efficiencyImprovedRuntime(typeItem);
  }
  if (rule.source === "structural") {
    return Boolean(typeItem.structural_checks[rule.check]);
  }
  return Boolean(typeItem.verification[rule.check]);
}

function passWithRules(typeItem) {
  if (!typeItem.verification.boundary_valid || !typeItem.verification.combination_valid) {
    return false;
  }
  for (const rule of RULE_DEFS) {
    if (!state.rules[rule.id]) {
      continue;
    }
    if (!ruleResult(typeItem, rule.id)) {
      return false;
    }
  }
  return true;
}

function evaluateCurrentVariant() {
  const v = activeVariant();
  state.evaluated = v.types.map((item) => {
    const failedRules = RULE_DEFS.filter((rule) => !ruleResult(item, rule.id)).map((rule) => rule.id);
    return {
      ...item,
      runtime_status: passWithRules(item) ? "passed" : "failed",
      runtime_failed_rules: failedRules,
    };
  });
}

function generatedCurrent() {
  return state.evaluated.filter((item) => item.runtime_status === "passed");
}

function summaryCurrent() {
  const generated = generatedCurrent();
  return {
    total: generated.length,
    passed: generated.length,
    failed: 0,
    raw_pool: state.evaluated.length,
  };
}

function syncVariantURL() {
  const p = new URLSearchParams(location.search);
  p.set("variant", state.variant);
  const mask = encodeRuleMask(state.rules);
  if (mask !== "11111") {
    p.set("rr", mask);
  } else {
    p.delete("rr");
  }
  history.replaceState({}, "", `groups.html?${p.toString()}`);
  localStorage.setItem("shelf_variant_key", state.variant);
  localStorage.setItem("shelf_rule_mask", mask);
}

function renderBoundaryControls() {
  const areaSel = document.getElementById("boundary-area");
  const layerSel = document.getElementById("boundary-layers");
  const profile = profileByKey(state.variant);
  const parsed = parseVariantKey(state.variant);
  areaSel.value = String(profile ? profile.area : (parsed ? parsed.area : 1));
  layerSel.value = String(profile ? profile.max_layers : (parsed ? parsed.layers : 1));
}

function renderHeader() {
  const v = activeVariant();
  const s = summaryCurrent();
  const valid = generatedCurrent();
  const secKeys = new Set(
    valid.map((item) => {
      const support = supportProfileRuntime(item.layer_masks);
      const bin = ratioBinRuntime(item.projection_ratio);
      return `L${item.active_cells_per_layer.join("-")}_SUP${support.supported}-${support.unsupported}_PR${bin[0].toFixed(2)}-${bin[1].toFixed(2)}`;
    })
  );
  document.getElementById("title").textContent = `${report.title} | 分组总览`;
  document.getElementById("desc").textContent = `A=${v.meta.footprint_area_cells}, N<=${v.meta.max_layers}。综合总数(当前规则)=${s.total}，候选池(预计算)=${s.raw_pool}`;
  document.getElementById("chips").innerHTML = [
    `primary_groups=1`,
    `secondary_groups=${secKeys.size}`,
    `active_types=${s.total}`,
    `candidate_pool=${s.raw_pool}`,
    `baseline=${v.meta.baseline_efficiency.toFixed(2)}`,
    `combo=${v.meta.module_combo.join("+")}`,
  ].map((item) => `<span class=\"chip\">${item}</span>`).join("");

  document.getElementById("hero-kpis").innerHTML = [
    `综合总数 ${s.total}`,
    `通过率 100.0%`,
    `覆盖组数 1/${secKeys.size}`,
    `层数上限 ${v.meta.max_layers}`,
    `占地目标 ${v.meta.footprint_area_cells}`,
  ].map((item) => `<span class=\"chip\">${item}</span>`).join("");
}

function renderBasis() {
  document.getElementById("basis-primary").textContent = "一级依据: 当前启用规则下的有效组合集合。";
  document.getElementById("basis-secondary").textContent = "二级依据: (cells_per_layer, supported/unsupported, projection_ratio_bin)。";
  document.getElementById("basis-formula").textContent = "公式: secondary_key = L{cells}-SUP{supported}-{unsupported}-PR{ratio_bin}";
}

function matrixMini(mask) {
  const v = activeVariant();
  const cells = [];
  for (let bit = 0; bit < v.meta.cell_count; bit += 1) {
    const active = ((mask >> bit) & 1) === 1;
    cells.push(`<span class=\"sample-cell ${active ? "active" : ""}\"></span>`);
  }
  return `<div class=\"sample-mini\" style=\"grid-template-columns:repeat(${v.meta.grid_width},minmax(0,1fr));\">${cells.join("")}</div>`;
}

function supportProfileRuntime(layerMasks) {
  const v = activeVariant();
  const baseMask = layerMasks[0] || 0;
  let supported = 0;
  let unsupported = 0;
  for (let layer = 1; layer < layerMasks.length; layer += 1) {
    const mask = layerMasks[layer] || 0;
    for (let bit = 0; bit < v.meta.cell_count; bit += 1) {
      if (((mask >> bit) & 1) === 0) continue;
      if (((baseMask >> bit) & 1) === 1) supported += 1;
      else unsupported += 1;
    }
  }
  return { supported, unsupported };
}

function ratioBinRuntime(value, step = 0.25) {
  const start = Math.floor(value / step) * step;
  return [Number(start.toFixed(2)), Number((start + step).toFixed(2))];
}

function renderRuleLab() {
  const host = document.getElementById("rule-switches");
  host.innerHTML = RULE_DEFS.map((rule) => {
    const checked = state.rules[rule.id] ? "checked" : "";
    return `<label class=\"rule-toggle\"><input type=\"checkbox\" data-rule=\"${rule.id}\" ${checked} />${rule.label}</label>`;
  }).join("");

  host.querySelectorAll("input[data-rule]").forEach((node) => {
    node.addEventListener("change", async () => {
      const id = node.getAttribute("data-rule");
      state.rules[id] = node.checked;
      const parsed = parseVariantKey(state.variant);
      if (parsed) {
        try {
          await ensureVariantGenerated(parsed.area, parsed.layers, encodeRuleMask(state.rules));
        } catch (err) {
          window.alert(`规则重算失败: ${String(err && err.message ? err.message : err)}`);
          state.rules[id] = !node.checked;
          node.checked = state.rules[id];
          return;
        }
      }
      renderAll();
    });
  });

  const current = summaryCurrent();
  const disabled = RULE_DEFS.filter((rule) => !state.rules[rule.id]);
  const mask = encodeRuleMask(state.rules);

  document.getElementById("rule-impact").innerHTML = [
    `规则掩码=${mask}`,
    `当前规则组合=${current.total}`,
    `候选池=${current.raw_pool}`,
  ].map((text) => `<span class=\"chip\">${text}</span>`).join("");

  document.getElementById("rule-note").textContent = disabled.length
    ? `当前已关闭规则: ${disabled.map((item) => item.id).join(", ")}。当前页面的“组合总数/分组/列表入口”均按当前启用规则重新生成。`
    : "当前为全规则基线（B2/C2/C3/C4/EFF 全启用）。";
}

function renderVisualOverview() {
  const v = activeVariant();
  const generated = generatedCurrent();
  const s = summaryCurrent();
  const passPct = pctNumber(s.passed, s.total || 1);
  const ring = document.getElementById("pass-ring");
  ring.style.setProperty("--pct", `${passPct}%`);
  document.getElementById("pass-ring-text").textContent = `${passPct.toFixed(1)}%`;

  const bins = v.histogram.map((item) => ({ start: item.start, end: item.end, passed: 0, failed: 0 }));
  generated.forEach((item) => {
    const idx = bins.findIndex((bin, i) => {
      const isLast = i === bins.length - 1;
      return isLast
        ? (item.projection_ratio >= bin.start && item.projection_ratio <= bin.end)
        : (item.projection_ratio >= bin.start && item.projection_ratio < bin.end);
    });
    if (idx < 0) return;
    bins[idx].passed += 1;
  });

  const maxCount = Math.max(1, ...bins.map((item) => item.passed + item.failed));
  document.getElementById("ratio-hist").innerHTML = bins.map((item) => {
    const total = item.passed + item.failed;
    const h = Math.max(8, Math.round((total / maxCount) * 128));
    const passPart = total ? Math.round((item.passed / total) * 100) : 0;
    return `
      <div class=\"hist-col\" title=\"[${item.start},${item.end}) pass=${item.passed}, fail=${item.failed}\">
        <div class=\"hist-bar\" style=\"height:${h}px\">
          <span class=\"hist-pass\" style=\"height:${passPart}%\"></span>
        </div>
        <div class=\"meta-line\">${total}</div>
      </div>
    `;
  }).join("");

  const samples = generated
    .slice()
    .sort((a, b) => {
      return b.projection_ratio - a.projection_ratio || a.type_id - b.type_id;
    })
    .slice(0, 8);

  document.getElementById("sample-gallery").innerHTML = samples.map((item) => {
    const mask = encodeRuleMask(state.rules);
    const rr = mask !== "11111" ? `&rr=${encodeURIComponent(mask)}` : "";
    const href = `type.html?variant=${encodeURIComponent(state.variant)}&type=${item.type_id}&primary=ALL${rr}`;
    const maskPreview = matrixMini(item.layer_masks[item.layer_masks.length - 1] || 0);
    const riskTag = "可用";
    return `
      <a class=\"sample-tile\" href=\"${href}\">
        <div class=\"sample-head\">
          <span>#${item.type_id}</span>
          <span class=\"pill ok\">passed</span>
        </div>
        ${maskPreview}
        <div class=\"meta-line\">ratio=${item.projection_ratio.toFixed(2)} | ${riskTag}</div>
      </a>
    `;
  }).join("");
}

function renderPrimaryGrid() {
  const host = document.getElementById("primary-grid");
  const valid = state.evaluated.filter((item) => item.runtime_status === "passed");
  if (!valid.length) {
    host.innerHTML = `<article class=\"primary-card\"><div class=\"primary-title\">当前规则下无可用组合</div><div class=\"sub\">请恢复部分规则或调整边界。</div></article>`;
    return;
  }

  const secondaryMap = new Map();
  valid.forEach((item) => {
    const support = supportProfileRuntime(item.layer_masks);
    const bin = ratioBinRuntime(item.projection_ratio);
    const secId = `L${item.active_cells_per_layer.join("-")}_SUP${support.supported}-${support.unsupported}_PR${bin[0].toFixed(2)}-${bin[1].toFixed(2)}`;
    if (!secondaryMap.has(secId)) {
      secondaryMap.set(secId, {
        id: secId,
        label: `L${item.active_cells_per_layer.join("/")} | support ${support.supported}/${support.unsupported} | R[${bin[0].toFixed(2)},${bin[1].toFixed(2)})`,
        type_ids: [],
      });
    }
    secondaryMap.get(secId).type_ids.push(item.type_id);
  });
  const secondaryGroups = Array.from(secondaryMap.values()).sort((a, b) => b.type_ids.length - a.type_ids.length);
  const mask = encodeRuleMask(state.rules);
  const rr = mask !== "11111" ? `&rr=${encodeURIComponent(mask)}` : "";
  const primaryHref = `group.html?variant=${encodeURIComponent(state.variant)}&primary=ACTIVE${rr}`;
  const secRows = secondaryGroups.slice(0, 8).map((sec) => {
    const secHref = `group.html?variant=${encodeURIComponent(state.variant)}&primary=ACTIVE&secondary=${encodeURIComponent(sec.id)}${rr}`;
    return `
      <div class=\"secondary-row\">
        <div>
          <a href=\"${secHref}\">${sec.label}</a>
          <div class=\"meta-line\">types=${sec.type_ids.length}, passed=${sec.type_ids.length}, failed=0</div>
        </div>
        <a class=\"btn\" href=\"${secHref}\">进入组合</a>
      </div>
    `;
  }).join("");
  const moreHint = secondaryGroups.length > 8
    ? `<div class=\"meta-line\">还有 ${secondaryGroups.length - 8} 个二级组，请进入组合列表查看。</div>`
    : "";

  host.innerHTML = `
    <article class=\"primary-card\">
      <div class=\"primary-head\">
        <div class=\"primary-title\">ACTIVE | 当前启用规则生成集合</div>
        <span class=\"pill ok\">pass=100.0%</span>
      </div>
      <div class=\"meter\"><span style=\"width:100%\"></span></div>
      <div class=\"sub\">组划分基于当前启用规则生成的有效组合集合（非全规则基线）。</div>
      <div class=\"meta-line\">types=${valid.length}, secondary_groups=${secondaryGroups.length}</div>
      <div class=\"toolbar\"><a class=\"btn\" href=\"${primaryHref}\">查看该组全部组合</a></div>
      <div class=\"secondary-table\">${secRows}</div>
      ${moreHint}
    </article>
  `;
}

function renderAll() {
  syncVariantURL();
  evaluateCurrentVariant();
  renderBoundaryControls();
  renderHeader();
  renderRuleLab();
  renderVisualOverview();
  renderBasis();
  renderPrimaryGrid();
}

document.getElementById("apply-boundary").addEventListener("click", async () => {
  const area = Number.parseInt(document.getElementById("boundary-area").value || "0", 10);
  const layers = Number.parseInt(document.getElementById("boundary-layers").value || "0", 10);
  if (!Number.isFinite(area) || !Number.isFinite(layers) || area <= 0 || layers <= 0) {
    window.alert("A 和 N 必须是正整数。");
    return;
  }
  try {
    state.variant = await ensureVariantGenerated(area, layers, encodeRuleMask(state.rules));
  } catch (err) {
    window.alert(`生成失败: ${String(err && err.message ? err.message : err)}`);
    return;
  }
  renderAll();
});

async function bootstrap() {
  const parsed = parseVariantKey(state.variant) || parseVariantKey(fallbackVariantKey());
  if (parsed) {
    try {
      state.variant = await ensureVariantGenerated(parsed.area, parsed.layers, encodeRuleMask(state.rules));
    } catch (_err) {
      state.variant = fallbackVariantKey();
    }
  }
  renderAll();
}

bootstrap();
"""

    return render_page("Shelf Groups", body, script)


def render_group_page(report_payload: dict[str, Any]) -> str:
    body = """
<div class="shell">
  <header class="hero">
    <h1 id="title"></h1>
    <div class="breadcrumb" id="breadcrumb"></div>
    <p id="group-desc"></p>
    <div class="chips" id="chips"></div>
    <div class="toolbar">
      <label class="sub">占地 A:</label>
      <input id="boundary-area" type="number" step="1" />
      <label class="sub">层数上限 N:</label>
      <input id="boundary-layers" type="number" step="1" />
      <button class="btn accent" id="apply-boundary" type="button">应用边界</button>
    </div>
  </header>

  <section class="card">
    <h2>组合列表</h2>
    <div class="sub">点击组合卡片进入 3D 详情页。支持过滤通过/失败。</div>
    <div class="toolbar">
      <label class="sub">状态过滤:</label>
      <select id="status-filter">
        <option value="all">全部</option>
        <option value="passed">仅通过</option>
        <option value="failed">仅失败</option>
      </select>
      <label class="sub">排序:</label>
      <select id="sort-mode">
        <option value="id">按 type_id</option>
        <option value="ratio">按 projection_ratio</option>
      </select>
      <span class="chip" id="counter"></span>
    </div>
    <div class="catalog" id="catalog"></div>
  </section>
</div>
"""

    script = """
const report = window.__SHELF_REPORT__ || {};
const variantMap = report.variants || {};
const variantRuleCache = {};
Object.keys(variantMap).forEach((key) => {
  variantRuleCache[key] = "11111";
});
const profiles = (report.boundary_profiles || []).slice();
const params = new URLSearchParams(location.search);
const RULE_DEFS = [
  { id: "B2", check: "B2_fixed_footprint", source: "structural" },
  { id: "C2", check: "C2_support_continuity", source: "structural" },
  { id: "C3", check: "C3_center_projection_stable", source: "structural" },
  { id: "C4", check: "C4_upper_layer_engaged", source: "structural" },
  { id: "EFF", check: "efficiency_improved", source: "verification" },
];
const RULE_ORDER = RULE_DEFS.map((item) => item.id);

function decodeRuleMask(raw) {
  const base = Object.fromEntries(RULE_ORDER.map((id) => [id, true]));
  if (!raw) return base;
  const bits = raw.split("");
  RULE_ORDER.forEach((id, idx) => {
    if (bits[idx] === "0") base[id] = false;
  });
  return base;
}

function encodeRuleMask(rules) {
  return RULE_ORDER.map((id) => (rules[id] ? "1" : "0")).join("");
}

function fallbackVariantKey() {
  return report.default_variant_key || (profiles[0] ? profiles[0].key : "") || Object.keys(variantMap)[0] || "";
}

function normalizeVariantKey(key) {
  if (key && variantMap[key]) {
    return key;
  }
  return fallbackVariantKey();
}

const state = {
  variant: normalizeVariantKey(params.get("variant") || localStorage.getItem("shelf_variant_key") || report.default_variant_key),
  status: "all",
  sort: "id",
  requestedPrimary: params.get("primary") || "ACTIVE",
  requestedSecondary: params.get("secondary") || "",
  rules: decodeRuleMask(params.get("rr") || localStorage.getItem("shelf_rule_mask") || ""),
};

function activeVariant() {
  return variantMap[state.variant] || report;
}

function uniqueNumbers(items) {
  return Array.from(new Set(items)).sort((a, b) => a - b);
}

function keyByAreaLayers(area, layers) {
  const match = profiles.find((item) => item.area === area && item.max_layers === layers);
  return match ? match.key : fallbackVariantKey();
}

function nearestVariantKey(area, layers) {
  if (!profiles.length) {
    return fallbackVariantKey();
  }
  const exact = profiles.find((item) => item.area === area && item.max_layers === layers);
  if (exact) {
    return exact.key;
  }

  let best = profiles[0];
  let bestScore = Number.POSITIVE_INFINITY;
  profiles.forEach((item) => {
    const score = Math.abs(item.area - area) * 10 + Math.abs(item.max_layers - layers);
    if (score < bestScore) {
      bestScore = score;
      best = item;
    }
  });
  return best.key;
}

function profileByKey(key) {
  return profiles.find((item) => item.key === key) || null;
}

function parseVariantKey(key) {
  const m = /^A(\\d+)_N(\\d+)$/.exec(key || "");
  if (!m) return null;
  return {
    area: Number.parseInt(m[1], 10),
    layers: Number.parseInt(m[2], 10),
  };
}

async function ensureVariantGenerated(area, layers, ruleMask) {
  const key = `A${area}_N${layers}`;
  if (variantMap[key] && variantRuleCache[key] === ruleMask) {
    return key;
  }
  const url = `/api/variant?area=${encodeURIComponent(area)}&layers=${encodeURIComponent(layers)}&rr=${encodeURIComponent(ruleMask)}`;
  const resp = await fetch(url, { method: "GET" });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || `HTTP ${resp.status}`);
  }
  const payload = await resp.json();
  if (!payload || !payload.key || !payload.variant) {
    throw new Error("invalid variant payload");
  }
  variantMap[payload.key] = payload.variant;
  variantRuleCache[payload.key] = payload.rule_mask || ruleMask;
  if (payload.profile && !profiles.some((item) => item.key === payload.profile.key)) {
    profiles.push(payload.profile);
  }
  return payload.key;
}

function efficiencyImprovedRuntime(typeItem) {
  const v = activeVariant();
  const baseCells = (typeItem.active_cells_per_layer && typeItem.active_cells_per_layer[0]) || 0;
  const denominator = state.rules.B2 ? v.meta.footprint_area_cells : Math.max(1, baseCells);
  const runtimeEfficiency = typeItem.total_active_cells / denominator;
  return runtimeEfficiency > v.meta.baseline_efficiency;
}

function ruleResult(typeItem, ruleId) {
  const rule = RULE_DEFS.find((item) => item.id === ruleId);
  if (!rule) return true;
  if (rule.id === "EFF") {
    return efficiencyImprovedRuntime(typeItem);
  }
  if (rule.source === "structural") {
    return Boolean(typeItem.structural_checks[rule.check]);
  }
  return Boolean(typeItem.verification[rule.check]);
}

function passWithRules(typeItem) {
  if (!typeItem.verification.boundary_valid || !typeItem.verification.combination_valid) {
    return false;
  }
  for (const rule of RULE_DEFS) {
    if (!state.rules[rule.id]) continue;
    if (!ruleResult(typeItem, rule.id)) return false;
  }
  return true;
}

function evaluateTypesWithRules(items) {
  return items.map((item) => {
    const failedRules = RULE_DEFS.filter((rule) => !ruleResult(item, rule.id)).map((rule) => rule.id);
    return {
      ...item,
      runtime_status: passWithRules(item) ? "passed" : "failed",
      runtime_failed_rules: failedRules,
    };
  });
}

function supportProfileRuntime(layerMasks, cellCount) {
  const baseMask = layerMasks[0] || 0;
  let supported = 0;
  let unsupported = 0;
  for (let layer = 1; layer < layerMasks.length; layer += 1) {
    const mask = layerMasks[layer] || 0;
    for (let bit = 0; bit < cellCount; bit += 1) {
      if (((mask >> bit) & 1) === 0) continue;
      if (((baseMask >> bit) & 1) === 1) supported += 1;
      else unsupported += 1;
    }
  }
  return { supported, unsupported };
}

function ratioBinRuntime(value, step = 0.25) {
  const start = Math.floor(value / step) * step;
  return [Number(start.toFixed(2)), Number((start + step).toFixed(2))];
}

function buildSecondaryGroups(filtered, cellCount) {
  const map = new Map();
  filtered.forEach((item) => {
    const support = supportProfileRuntime(item.layer_masks, cellCount);
    const bin = ratioBinRuntime(item.projection_ratio);
    const id = `L${item.active_cells_per_layer.join("-")}_SUP${support.supported}-${support.unsupported}_PR${bin[0].toFixed(2)}-${bin[1].toFixed(2)}`;
    if (!map.has(id)) {
      map.set(id, {
        id,
        label: `L${item.active_cells_per_layer.join("/")} | support ${support.supported}/${support.unsupported} | R[${bin[0].toFixed(2)},${bin[1].toFixed(2)})`,
        type_ids: [],
      });
    }
    map.get(id).type_ids.push(item.type_id);
  });
  return Array.from(map.values()).sort((a, b) => b.type_ids.length - a.type_ids.length);
}

function updateURL(primaryId, secondaryId) {
  const p = new URLSearchParams();
  p.set("variant", state.variant);
  if (primaryId) p.set("primary", primaryId);
  if (secondaryId) p.set("secondary", secondaryId);
  const mask = encodeRuleMask(state.rules);
  if (mask !== "11111") p.set("rr", mask);
  history.replaceState({}, "", `group.html?${p.toString()}`);
  localStorage.setItem("shelf_variant_key", state.variant);
  localStorage.setItem("shelf_rule_mask", mask);
}

function renderBoundaryControls() {
  const areaSel = document.getElementById("boundary-area");
  const layerSel = document.getElementById("boundary-layers");
  const profile = profileByKey(state.variant);
  const parsed = parseVariantKey(state.variant);
  areaSel.value = String(profile ? profile.area : (parsed ? parsed.area : 1));
  layerSel.value = String(profile ? profile.max_layers : (parsed ? parsed.layers : 1));
}

function renderHeader(primaryLabel, secondary, totalCount) {
  const breadcrumb = document.getElementById("breadcrumb");
  const v = activeVariant();
  const secText = secondary ? ` / 二级组: ${secondary.id}` : "";

  document.getElementById("title").textContent = `组合列表 | ${primaryLabel}${secText}`;
  if (secondary) {
    document.getElementById("group-desc").textContent =
      `一级依据: 当前启用规则生成集合。二级结构: ${secondary.label}`;
  } else {
    document.getElementById("group-desc").textContent = "一级依据: 当前启用规则生成集合。";
  }

  const mask = encodeRuleMask(state.rules);
  const rr = mask !== "11111" ? `&rr=${encodeURIComponent(mask)}` : "";
  const primaryLink = `group.html?variant=${encodeURIComponent(state.variant)}&primary=ACTIVE${rr}`;
  breadcrumb.innerHTML = [
    `<a href=\"groups.html?variant=${encodeURIComponent(state.variant)}\">分组总览</a>`,
    `<span>/</span>`,
    `<a href=\"${primaryLink}\">${primaryLabel}</a>`,
    secondary ? `<span>/</span><span>${secondary.id}</span>` : "",
  ].join("");

  document.getElementById("chips").innerHTML = [
    `types=${secondary ? secondary.type_ids.length : totalCount}`,
    `passed=${secondary ? secondary.type_ids.length : totalCount}`,
    "failed=0",
    `A=${v.meta.footprint_area_cells}`,
    `N<=${v.meta.max_layers}`,
    `rr=${mask}`,
  ].map((item) => `<span class=\"chip\">${item}</span>`).join("");
}

function collectFailureCodes(item) {
  const checks = item.structural_checks || {};
  const codes = [];
  if (!checks.B2_fixed_footprint) codes.push("B2");
  if (!checks.C2_support_continuity) codes.push("C2");
  if (!checks.C3_center_projection_stable) codes.push("C3");
  if (!checks.C4_upper_layer_engaged) codes.push("C4");
  if (!efficiencyImprovedRuntime(item)) codes.push("EFF");
  return codes;
}

function matrixHtml(mask) {
  const v = activeVariant();
  const cells = [];
  for (let bit = 0; bit < v.meta.cell_count; bit += 1) {
    const active = ((mask >> bit) & 1) === 1;
    cells.push(`<span class=\"cell ${active ? "active" : ""}\"></span>`);
  }
  return `<div class=\"matrix\" style=\"grid-template-columns:repeat(${v.meta.grid_width},minmax(0,1fr));\">${cells.join("")}</div>`;
}

function renderCatalog(baseList, secondaryId) {
  const v = activeVariant();
  let list = baseList.slice();

  if (state.status !== "all") {
    list = list.filter((item) => item.runtime_status === state.status);
  }

  if (state.sort === "ratio") {
    list.sort((a, b) => b.projection_ratio - a.projection_ratio || a.type_id - b.type_id);
  } else {
    list.sort((a, b) => a.type_id - b.type_id);
  }

  document.getElementById("counter").textContent = `当前 ${list.length} 条`;

  const host = document.getElementById("catalog");
  const mask = encodeRuleMask(state.rules);
  const rr = mask !== "11111" ? `&rr=${encodeURIComponent(mask)}` : "";
  host.innerHTML = list.map((item) => {
    const detailHref = `type.html?variant=${encodeURIComponent(state.variant)}&type=${item.type_id}&primary=ACTIVE${secondaryId ? `&secondary=${encodeURIComponent(secondaryId)}` : ""}${rr}`;
    const layers = item.layer_masks.map((mask, idx) => {
      return `<div class=\"mini-layer\"><div class=\"sub\">L${idx + 1}</div>${matrixHtml(mask)}</div>`;
    }).join("");
    const failCodes = (item.runtime_failed_rules || []).slice(0, 3);
    const failChips = failCodes.map((code) => `<span class=\"chip\">${code}</span>`).join("");

    return `
      <article class=\"type-card\" data-href=\"${detailHref}\">
        <div class=\"type-head\">
          <span>#${item.type_id} / ${item.group_id}</span>
          <span class=\"pill ${item.runtime_status === "passed" ? "ok" : "bad"}\">${item.runtime_status}</span>
        </div>
        <div class=\"mini-stack\">${layers}</div>
        <div class=\"chips\">
          <span class=\"chip\">active ${item.active_cells_per_layer.join("/")}</span>
          <span class=\"chip\">L ${item.effective_layers || 1}/${item.declared_layers || v.meta.max_layers}</span>
          <span class=\"chip\">ratio ${item.projection_ratio.toFixed(2)}</span>
          ${item.is_degenerate_single_layer ? '<span class=\"chip\">退化单层</span>' : ""}
          ${failChips}
        </div>
      </article>
    `;
  }).join("");

  document.querySelectorAll(".type-card").forEach((node) => {
    node.addEventListener("click", () => {
      const href = node.getAttribute("data-href");
      if (href) {
        window.location.href = href;
      }
    });
  });
}

function bootstrap() {
  const v = activeVariant();
  const evaluated = evaluateTypesWithRules(v.types);
  const filtered = evaluated.filter((item) => item.runtime_status === "passed");
  const secondaryGroups = buildSecondaryGroups(filtered, v.meta.cell_count);
  const secondary = state.requestedSecondary
    ? secondaryGroups.find((item) => item.id === state.requestedSecondary) || null
    : null;
  const typeIdSet = new Set(secondary ? secondary.type_ids : filtered.map((item) => item.type_id));
  const listItems = filtered.filter((item) => typeIdSet.has(item.type_id));

  renderHeader("ACTIVE | 当前启用规则", secondary, filtered.length);
  renderCatalog(listItems, secondary ? secondary.id : "");
  updateURL("ACTIVE", secondary ? secondary.id : "");

  document.getElementById("status-filter").addEventListener("change", (event) => {
    state.status = event.target.value;
    renderCatalog(listItems, secondary ? secondary.id : "");
  });

  document.getElementById("sort-mode").addEventListener("change", (event) => {
    state.sort = event.target.value;
    renderCatalog(listItems, secondary ? secondary.id : "");
  });
}

document.getElementById("apply-boundary").addEventListener("click", async () => {
  const area = Number.parseInt(document.getElementById("boundary-area").value || "0", 10);
  const layers = Number.parseInt(document.getElementById("boundary-layers").value || "0", 10);
  if (!Number.isFinite(area) || !Number.isFinite(layers) || area <= 0 || layers <= 0) {
    window.alert("A 和 N 必须是正整数。");
    return;
  }
  let nextVariant = state.variant;
  try {
    nextVariant = await ensureVariantGenerated(area, layers, encodeRuleMask(state.rules));
  } catch (err) {
    window.alert(`生成失败: ${String(err && err.message ? err.message : err)}`);
    return;
  }
  localStorage.setItem("shelf_variant_key", nextVariant);
  const mask = encodeRuleMask(state.rules);
  localStorage.setItem("shelf_rule_mask", mask);
  const rr = mask !== "11111" ? `&rr=${encodeURIComponent(mask)}` : "";
  window.location.href = `group.html?variant=${encodeURIComponent(nextVariant)}&primary=ACTIVE${rr}`;
});

async function pageInit() {
  const parsed = parseVariantKey(state.variant) || parseVariantKey(fallbackVariantKey());
  if (parsed) {
    try {
      state.variant = await ensureVariantGenerated(parsed.area, parsed.layers, encodeRuleMask(state.rules));
    } catch (_err) {
      state.variant = fallbackVariantKey();
    }
  }
  renderBoundaryControls();
  bootstrap();
}

pageInit();
"""

    return render_page("Shelf Group", body, script)


def render_type_page(report_payload: dict[str, Any]) -> str:
    body = """
<div class="shell">
  <header class="hero">
    <h1 id="title"></h1>
    <div class="breadcrumb" id="breadcrumb"></div>
    <p id="type-desc"></p>
    <div class="chips" id="chips"></div>
    <div class="toolbar">
      <label class="sub">占地 A:</label>
      <input id="boundary-area" type="number" step="1" />
      <label class="sub">层数上限 N:</label>
      <input id="boundary-layers" type="number" step="1" />
      <button class="btn accent" id="apply-boundary" type="button">应用边界</button>
    </div>
  </header>

  <div class="grid-3">
    <section class="card">
      <h2>规则与状态</h2>
      <div class="toolbar">
        <button class="btn" id="prev-type" type="button">上一组合</button>
        <button class="btn" id="next-type" type="button">下一组合</button>
      </div>
      <div class="toolbar">
        <label class="sub">当前组合:</label>
        <select id="type-select"></select>
      </div>

      <div class="toolbar">
        <label class="sub">规则回放:</label>
        <button class="btn" id="step-prev" type="button">上一步</button>
        <button class="btn" id="step-next" type="button">下一步</button>
        <button class="btn" id="step-reset" type="button">完整</button>
      </div>
      <div class="sub" id="step-label"></div>

      <div class="rules" id="rules"></div>
      <div class="reason-box" id="reasons"></div>
      <div class="meta-box" id="meta"></div>
      <div class="diff-box hidden" id="diff-box"></div>
    </section>

    <section class="card">
      <h2>主结构 3D</h2>
      <div class="sub">拖拽旋转、滚轮缩放。浅木色为隔板（panel），银灰为支柱（rod），金属灰为连接件（connector），红色叉号表示 C2 违规。</div>
      <div class="stage-shell">
        <aside class="stage-sidebar">
          <p class="stage-title">Components</p>
          <label class="module-chip"><input type="checkbox" id="show-rods" checked />杆件 Rods<b>M1</b></label>
          <label class="module-chip"><input type="checkbox" id="show-connectors" checked />连接件 Connectors<b>M3</b></label>
          <label class="module-chip"><input type="checkbox" id="show-panels" checked />隔板 Panels<b>M2</b></label>
          <label class="module-chip"><input type="checkbox" id="show-support" checked />支撑链 Support<b>C2</b></label>
          <label class="module-chip"><input type="checkbox" id="show-com" checked />重心投影 COM<b>C3</b></label>
          <label class="module-chip"><input type="checkbox" id="show-interface" checked />接口节点 Interface<b>I/O</b></label>

          <p class="stage-title">Material</p>
          <div class="material-grid">
            <div class="mat-swatch"><span class="swatch-dot swatch-wood-light"></span><span>Wood Light</span></div>
            <div class="mat-swatch"><span class="swatch-dot swatch-wood-dark"></span><span>Wood Dark</span></div>
            <div class="mat-swatch"><span class="swatch-dot swatch-metal"></span><span>Metal Rod</span></div>
            <div class="mat-swatch"><span class="swatch-dot swatch-connector"></span><span>Connector</span></div>
          </div>

          <p class="stage-title">Camera</p>
          <div class="viewer-controls">
            <label>Yaw<input id="yaw" type="range" min="10" max="80" value="34" /></label>
            <label>Pitch<input id="pitch" type="range" min="10" max="70" value="30" /></label>
            <label>Zoom<input id="zoom" type="range" min="65" max="190" value="110" /></label>
          </div>
          <div class="switches" id="layer-switches"></div>
          <p class="stage-title">Boundary Mask</p>
          <div class="sub">点击网格单元可启用/取消边界；会实时过滤可选组合。</div>
          <div class="boundary-mask-grid" id="boundary-mask-grid"></div>
          <div class="toolbar">
            <button class="btn" id="boundary-mask-all" type="button">全选边界</button>
            <button class="btn" id="boundary-mask-clear" type="button">清空边界</button>
          </div>
          <div class="meta-line" id="boundary-mask-meta"></div>
          <label class="module-chip"><input type="checkbox" id="compare-enabled" />开启双组合对比<b>2x</b></label>
        </aside>
        <div class="stage-main">
          <div class="canvas-wrap">
            <canvas id="main-canvas" class="viewer-canvas" width="1200" height="420"></canvas>
          </div>
          <div class="stage-actions">
            <button class="btn" id="reset-camera" type="button">重置视角</button>
            <button class="btn accent" id="copy-link" type="button">复制直链</button>
          </div>
          <div class="meta-box" id="main-meta"></div>
        </div>
      </div>
    </section>

  </div>

  <section class="card hidden" id="compare-card">
    <h2>对比结构 3D</h2>
    <div class="toolbar">
      <label class="sub">对比组合:</label>
      <select id="compare-select"></select>
    </div>
    <div class="canvas-wrap">
      <canvas id="compare-canvas" class="viewer-canvas" width="1200" height="420"></canvas>
    </div>
    <div class="meta-box" id="compare-meta"></div>
  </section>
</div>
"""

    script = """
const report = window.__SHELF_REPORT__ || {};
const variantMap = report.variants || {};
const variantRuleCache = {};
Object.keys(variantMap).forEach((key) => {
  variantRuleCache[key] = "11111";
});
const profiles = (report.boundary_profiles || []).slice();
const params = new URLSearchParams(location.search);
const RULE_DEFS = [
  { id: "B2", check: "B2_fixed_footprint", source: "structural" },
  { id: "C2", check: "C2_support_continuity", source: "structural" },
  { id: "C3", check: "C3_center_projection_stable", source: "structural" },
  { id: "C4", check: "C4_upper_layer_engaged", source: "structural" },
  { id: "EFF", check: "efficiency_improved", source: "verification" },
];
const RULE_ORDER = RULE_DEFS.map((item) => item.id);
let types = [];
let typeMap = new Map();

function decodeRuleMask(raw) {
  const base = Object.fromEntries(RULE_ORDER.map((id) => [id, true]));
  if (!raw) {
    return base;
  }
  const bits = raw.split("");
  RULE_ORDER.forEach((id, idx) => {
    if (bits[idx] === "0") {
      base[id] = false;
    }
  });
  return base;
}

function encodeRuleMask(rules) {
  return RULE_ORDER.map((id) => (rules[id] ? "1" : "0")).join("");
}

function fallbackVariantKey() {
  return report.default_variant_key || (profiles[0] ? profiles[0].key : "") || Object.keys(variantMap)[0] || "";
}

function normalizeVariantKey(key) {
  if (key && variantMap[key]) {
    return key;
  }
  return fallbackVariantKey();
}

let currentVariantKey = normalizeVariantKey(
  params.get("variant") || localStorage.getItem("shelf_variant_key") || report.default_variant_key
);

function activeVariant() {
  return variantMap[currentVariantKey] || report;
}

function applyVariantToReport() {
  const v = activeVariant();
  report.boundary = v.boundary;
  report.summary = v.summary;
  report.histogram = v.histogram;
  report.meta = v.meta;
  report.grouping = v.grouping;
  report.types = v.types;
  report.candidate = v.candidate;
}

function rebuildTypeIndex() {
  applyVariantToReport();
  types = report.types.slice().sort((a, b) => a.type_id - b.type_id);
  typeMap = new Map(types.map((item) => [item.type_id, item]));
}

function uniqueNumbers(items) {
  return Array.from(new Set(items)).sort((a, b) => a - b);
}

function keyByAreaLayers(area, layers) {
  const match = profiles.find((item) => item.area === area && item.max_layers === layers);
  return match ? match.key : fallbackVariantKey();
}

function nearestVariantKey(area, layers) {
  if (!profiles.length) {
    return fallbackVariantKey();
  }
  const exact = profiles.find((item) => item.area === area && item.max_layers === layers);
  if (exact) {
    return exact.key;
  }

  let best = profiles[0];
  let bestScore = Number.POSITIVE_INFINITY;
  profiles.forEach((item) => {
    const score = Math.abs(item.area - area) * 10 + Math.abs(item.max_layers - layers);
    if (score < bestScore) {
      bestScore = score;
      best = item;
    }
  });
  return best.key;
}

function profileByKey(key) {
  return profiles.find((item) => item.key === key) || null;
}

function parseVariantKey(key) {
  const m = /^A(\\d+)_N(\\d+)$/.exec(key || "");
  if (!m) return null;
  return {
    area: Number.parseInt(m[1], 10),
    layers: Number.parseInt(m[2], 10),
  };
}

async function ensureVariantGenerated(area, layers, ruleMask) {
  const key = `A${area}_N${layers}`;
  if (variantMap[key] && variantRuleCache[key] === ruleMask) {
    return key;
  }
  const url = `/api/variant?area=${encodeURIComponent(area)}&layers=${encodeURIComponent(layers)}&rr=${encodeURIComponent(ruleMask)}`;
  const resp = await fetch(url, { method: "GET" });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || `HTTP ${resp.status}`);
  }
  const payload = await resp.json();
  if (!payload || !payload.key || !payload.variant) {
    throw new Error("invalid variant payload");
  }
  variantMap[payload.key] = payload.variant;
  variantRuleCache[payload.key] = payload.rule_mask || ruleMask;
  if (payload.profile && !profiles.some((item) => item.key === payload.profile.key)) {
    profiles.push(payload.profile);
  }
  return payload.key;
}

const replaySteps = [
  { code: "C1", label: "C1: 模块契约（面板需 rod+connector）" },
  { code: "C2", label: "C2: 支撑连续性（支撑链+连通）" },
  { code: "C3", label: "C3: 稳定投影（重心投影在占地内）" },
  { code: "C4", label: "C4: 层完整性（多层模式每层至少一格）" },
  { code: "VERIFY", label: "Verify: 边界+组合+目标" },
];

function bitCount(mask) {
  return mask.toString(2).split("0").join("").length;
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function degToRad(value) {
  return (value * Math.PI) / 180;
}

function efficiencyImprovedRuntime(typeItem) {
  const baseCells = (typeItem.active_cells_per_layer && typeItem.active_cells_per_layer[0]) || 0;
  const denominator = state.rules.B2 ? report.meta.footprint_area_cells : Math.max(1, baseCells);
  const runtimeEfficiency = typeItem.total_active_cells / denominator;
  return runtimeEfficiency > report.meta.baseline_efficiency;
}

function ruleResult(typeItem, ruleId) {
  const rule = RULE_DEFS.find((item) => item.id === ruleId);
  if (!rule) {
    return true;
  }
  if (rule.id === "EFF") {
    return efficiencyImprovedRuntime(typeItem);
  }
  if (rule.source === "structural") {
    return Boolean(typeItem.structural_checks[rule.check]);
  }
  return Boolean(typeItem.verification[rule.check]);
}

function passWithRules(typeItem) {
  if (!typeItem.verification.boundary_valid || !typeItem.verification.combination_valid) {
    return false;
  }
  for (const rule of RULE_DEFS) {
    if (!state.rules[rule.id]) {
      continue;
    }
    if (!ruleResult(typeItem, rule.id)) {
      return false;
    }
  }
  return true;
}

function supportProfileRuntime(layerMasks, cellCount) {
  const baseMask = layerMasks[0] || 0;
  let supported = 0;
  let unsupported = 0;
  for (let layer = 1; layer < layerMasks.length; layer += 1) {
    const mask = layerMasks[layer] || 0;
    for (let bit = 0; bit < cellCount; bit += 1) {
      if (((mask >> bit) & 1) === 0) continue;
      if (((baseMask >> bit) & 1) === 1) supported += 1;
      else unsupported += 1;
    }
  }
  return { supported, unsupported };
}

function ratioBinRuntime(value, step = 0.25) {
  const start = Math.floor(value / step) * step;
  return [Number(start.toFixed(2)), Number((start + step).toFixed(2))];
}

function buildRuntimeSecondaryGroups(filtered, cellCount) {
  const map = new Map();
  filtered.forEach((item) => {
    const support = supportProfileRuntime(item.layer_masks, cellCount);
    const bin = ratioBinRuntime(item.projection_ratio);
    const id = `L${item.active_cells_per_layer.join("-")}_SUP${support.supported}-${support.unsupported}_PR${bin[0].toFixed(2)}-${bin[1].toFixed(2)}`;
    if (!map.has(id)) {
      map.set(id, {
        id,
        type_ids: [],
      });
    }
    map.get(id).type_ids.push(item.type_id);
  });
  return Array.from(map.values()).sort((a, b) => b.type_ids.length - a.type_ids.length);
}

function contextTypeIds(_primaryId, secondaryId) {
  if (_primaryId === "ALL") {
    return types.map((item) => item.type_id).sort((a, b) => a - b);
  }
  const filtered = types.filter((item) => passWithRules(item));
  if (!filtered.length) {
    return [];
  }
  if (!secondaryId) {
    return filtered.map((item) => item.type_id).sort((a, b) => a - b);
  }
  const secondaryGroups = buildRuntimeSecondaryGroups(filtered, report.meta.cell_count);
  const sec = secondaryGroups.find((item) => item.id === secondaryId);
  if (!sec) {
    return filtered.map((item) => item.type_id).sort((a, b) => a - b);
  }
  return [...sec.type_ids].sort((a, b) => a - b);
}

rebuildTypeIndex();

function fullBoundaryMask() {
  return (1 << report.meta.cell_count) - 1;
}

function parseBoundaryMaskParam(raw) {
  if (!raw) {
    return NaN;
  }
  const value = Number.parseInt(raw, 36);
  return Number.isFinite(value) ? value : NaN;
}

function normalizeBoundaryMask(mask) {
  const full = fullBoundaryMask();
  if (!Number.isFinite(mask)) {
    return full;
  }
  return mask & full;
}

function typeFitsBoundary(typeItem, boundaryMask) {
  return typeItem.layer_masks.every((mask) => ((mask & ~boundaryMask) === 0));
}

const state = {
  primary: params.get("primary") || "ACTIVE",
  secondary: params.get("secondary") || "",
  ids: [],
  pinnedTypeId: Number(params.get("type")) || 0,
  currentId: Number(params.get("type")) || (types[0] ? types[0].type_id : 0),
  compareEnabled: false,
  compareId: null,
  showLayers: Array.from({ length: report.meta.max_layers }, () => true),
  showRods: true,
  showPanels: true,
  showConnectors: true,
  showSupport: true,
  showCom: true,
  showInterface: true,
  stepIdx: replaySteps.length - 1,
  camera: {
    yaw: 34,
    pitch: 30,
    zoom: 1.1,
  },
  dragging: false,
  dragX: 0,
  dragY: 0,
  boundaryMask: parseBoundaryMaskParam(params.get("bm")),
  rules: decodeRuleMask(params.get("rr") || localStorage.getItem("shelf_rule_mask") || ""),
};

function recomputeVisibleTypeIds() {
  let ids = contextTypeIds(state.primary, state.secondary);
  ids = ids.filter((id) => {
    const item = typeMap.get(id);
    return Boolean(item) && typeFitsBoundary(item, state.boundaryMask);
  });

  if (state.pinnedTypeId && typeMap.has(state.pinnedTypeId)) {
    const pinned = typeMap.get(state.pinnedTypeId);
    if (pinned && typeFitsBoundary(pinned, state.boundaryMask) && !ids.includes(state.pinnedTypeId)) {
      ids = [state.pinnedTypeId, ...ids];
    }
  }
  state.ids = ids;

  if (!state.ids.length) {
    state.currentId = 0;
    state.compareId = 0;
    return;
  }

  if (!typeMap.has(state.currentId) || !state.ids.includes(state.currentId)) {
    state.currentId = state.ids[0];
  }
  state.compareId = state.ids.find((id) => id !== state.currentId) || state.currentId;
}

function refreshVariantContext(resetBoundary = false) {
  rebuildTypeIndex();
  if (resetBoundary) {
    state.boundaryMask = fullBoundaryMask();
  }
  state.boundaryMask = normalizeBoundaryMask(state.boundaryMask);
  state.showLayers = Array.from({ length: report.meta.max_layers }, (_, idx) => {
    const prev = state.showLayers[idx];
    return typeof prev === "boolean" ? prev : true;
  });
  recomputeVisibleTypeIds();
}

refreshVariantContext(false);

function getCurrentType() {
  return typeMap.get(state.currentId) || null;
}

function getCompareType() {
  return typeMap.get(state.compareId) || getCurrentType();
}

function checksFromType(typeItem) {
  return {
    C1: Boolean(typeItem.verification.combination_valid),
    C2: Boolean(typeItem.structural_checks.C2_support_continuity),
    C3: Boolean(typeItem.structural_checks.C3_center_projection_stable),
    C4: Boolean(typeItem.structural_checks.C4_upper_layer_engaged),
    B1: Boolean(typeItem.structural_checks.B1_layers_within_limit),
    B2: Boolean(typeItem.structural_checks.B2_fixed_footprint),
    VERIFY: passWithRules(typeItem),
  };
}

function isStepActive(code) {
  const index = replaySteps.findIndex((item) => item.code === code);
  return index >= 0 && index <= state.stepIdx;
}

function buildCells(typeItem) {
  const cells = [];
  for (let layer = 0; layer < typeItem.layer_masks.length; layer += 1) {
    if (!state.showLayers[layer]) {
      continue;
    }
    const mask = typeItem.layer_masks[layer];
    for (let bit = 0; bit < report.meta.cell_count; bit += 1) {
      if (((mask >> bit) & 1) === 0) {
        continue;
      }
      const x = bit % report.meta.grid_width;
      const y = Math.floor(bit / report.meta.grid_width);
      const baseMask = typeItem.layer_masks[0] || 0;
      const unsupported = layer > 0 && (((baseMask >> bit) & 1) === 0);
      cells.push({ x, y, bit, layer, unsupported });
    }
  }
  return cells;
}

function centerOfMass(cells) {
  if (!cells.length) {
    return null;
  }

  let sx = 0;
  let sy = 0;
  let sz = 0;

  cells.forEach((cell) => {
    sx += cell.x + 0.5;
    sy += cell.y + 0.5;
    sz += cell.layer + 0.55;
  });

  return {
    x: sx / cells.length,
    y: sy / cells.length,
    z: sz / cells.length,
  };
}

function projectPoint(point, camera, viewport) {
  const c = {
    x: point.x - viewport.center.x,
    y: point.y - viewport.center.y,
    z: point.z - viewport.center.z,
  };

  const yaw = degToRad(camera.yaw);
  const pitch = degToRad(camera.pitch);

  const x1 = c.x * Math.cos(yaw) - c.y * Math.sin(yaw);
  const y1 = c.x * Math.sin(yaw) + c.y * Math.cos(yaw);
  const z1 = c.z;

  const y2 = y1 * Math.cos(pitch) - z1 * Math.sin(pitch);
  const z2 = y1 * Math.sin(pitch) + z1 * Math.cos(pitch);

  const scale = camera.zoom * (8 / (8 + z2 + 8));
  return {
    x: viewport.cx + x1 * viewport.unit * scale,
    y: viewport.cy - y2 * viewport.unit * scale,
    depth: z2,
  };
}

function drawLine(ctx, from, to, color, width = 1.0, dash = []) {
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(from.x, from.y);
  ctx.lineTo(to.x, to.y);
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.setLineDash(dash);
  ctx.stroke();
  ctx.restore();
}

function drawPolygon(ctx, points, fill, stroke = null, lineWidth = 1.1) {
  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  for (let i = 1; i < points.length; i += 1) {
    ctx.lineTo(points[i].x, points[i].y);
  }
  ctx.closePath();
  ctx.fillStyle = fill;
  ctx.fill();
  if (stroke) {
    ctx.strokeStyle = stroke;
    ctx.lineWidth = lineWidth;
    ctx.stroke();
  }
}

function drawTextTag(ctx, point, text, color = "rgba(216, 224, 232, 0.95)") {
  ctx.save();
  ctx.font = "12px SF Pro Text, PingFang SC, sans-serif";
  ctx.fillStyle = color;
  ctx.strokeStyle = "rgba(28, 34, 42, 0.72)";
  ctx.lineWidth = 3.2;
  ctx.strokeText(text, point.x + 6, point.y - 8);
  ctx.fillText(text, point.x + 6, point.y - 8);
  ctx.restore();
}

function drawNode(ctx, point, radius, fill, stroke) {
  ctx.save();
  ctx.shadowBlur = 12;
  ctx.shadowColor = fill;
  ctx.beginPath();
  ctx.arc(point.x, point.y, radius, 0, Math.PI * 2);
  ctx.fillStyle = fill;
  ctx.strokeStyle = stroke;
  ctx.lineWidth = 1.0;
  ctx.fill();
  ctx.stroke();
  ctx.restore();
}

function drawRod(ctx, from, to) {
  drawLine(ctx, from, to, "rgba(82, 94, 108, 0.22)", 7.0);
  drawLine(ctx, from, to, "rgba(146, 160, 176, 0.92)", 2.8);
  drawLine(ctx, from, to, "rgba(236, 242, 249, 0.88)", 1.0);
}

function drawConnectorGlyph(ctx, point) {
  ctx.save();
  ctx.strokeStyle = "rgba(188, 200, 214, 0.96)";
  ctx.lineWidth = 1.3;
  ctx.beginPath();
  ctx.moveTo(point.x - 3, point.y - 3);
  ctx.lineTo(point.x + 3, point.y - 3);
  ctx.lineTo(point.x + 3, point.y + 3);
  ctx.lineTo(point.x - 3, point.y + 3);
  ctx.closePath();
  ctx.fillStyle = "rgba(145, 155, 166, 0.45)";
  ctx.fill();
  ctx.stroke();
  ctx.restore();
}

function lerpPoint(a, b, t) {
  return {
    x: a.x + (b.x - a.x) * t,
    y: a.y + (b.y - a.y) * t,
  };
}

function drawPanelGrain(ctx, quad) {
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(quad[0].x, quad[0].y);
  for (let i = 1; i < quad.length; i += 1) {
    ctx.lineTo(quad[i].x, quad[i].y);
  }
  ctx.closePath();
  ctx.clip();

  for (let i = 1; i <= 5; i += 1) {
    const t = i / 6;
    const from = lerpPoint(quad[0], quad[3], t);
    const to = lerpPoint(quad[1], quad[2], t);
    drawLine(ctx, from, to, "rgba(145, 108, 72, 0.28)", 0.7);
  }
  ctx.restore();
}

function maskHasCell(mask, x, y) {
  if (x < 0 || y < 0 || x >= report.meta.grid_width || y >= report.meta.grid_depth) {
    return false;
  }
  const bit = y * report.meta.grid_width + x;
  return ((mask >> bit) & 1) === 1;
}

function drawPanel(ctx, cell, camera, viewport, showCross, layerMask) {
  const zTop = cell.layer * 1.05 + 0.06;
  const v00 = projectPoint({ x: cell.x, y: cell.y, z: zTop }, camera, viewport);
  const v10 = projectPoint({ x: cell.x + 1, y: cell.y, z: zTop }, camera, viewport);
  const v11 = projectPoint({ x: cell.x + 1, y: cell.y + 1, z: zTop }, camera, viewport);
  const v01 = projectPoint({ x: cell.x, y: cell.y + 1, z: zTop }, camera, viewport);

  const normal = cell.layer === 0
    ? {
        top: "rgba(229, 193, 151, 0.97)",
        edge: "rgba(244, 223, 194, 0.95)",
      }
    : {
        top: "rgba(235, 205, 170, 0.96)",
        edge: "rgba(248, 232, 210, 0.95)",
      };
  const warn = {
    top: "rgba(255, 131, 131, 0.95)",
    edge: "rgba(255, 217, 217, 0.95)",
  };
  const palette = cell.unsupported ? warn : normal;
  const hasRight = maskHasCell(layerMask, cell.x + 1, cell.y);
  const hasLeft = maskHasCell(layerMask, cell.x - 1, cell.y);
  const hasUp = maskHasCell(layerMask, cell.x, cell.y - 1);
  const hasDown = maskHasCell(layerMask, cell.x, cell.y + 1);

  const quad = [v00, v10, v11, v01];
  drawPolygon(ctx, quad, palette.top, null);
  drawPanelGrain(ctx, quad);

  if (!hasUp) drawLine(ctx, v00, v10, palette.edge, 1.0);
  if (!hasRight) drawLine(ctx, v10, v11, palette.edge, 1.0);
  if (!hasDown) drawLine(ctx, v01, v11, palette.edge, 1.0);
  if (!hasLeft) drawLine(ctx, v00, v01, palette.edge, 1.0);

  if (showCross && cell.unsupported) {
    drawLine(ctx, v00, v11, "rgba(255, 236, 236, 0.96)", 2.0);
    drawLine(ctx, v10, v01, "rgba(255, 236, 236, 0.96)", 2.0);
  }
}

function drawStructure(canvasId, metaId, typeItem) {
  const canvas = document.getElementById(canvasId);
  const metaBox = document.getElementById(metaId);
  if (!canvas || !metaBox || !typeItem) {
    return;
  }

  const rect = canvas.getBoundingClientRect();
  if (rect.width <= 0 || rect.height <= 0) {
    return;
  }

  const dpr = window.devicePixelRatio || 1;
  const width = Math.max(1, Math.floor(rect.width * dpr));
  const height = Math.max(1, Math.floor(rect.height * dpr));
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }

  const ctx = canvas.getContext("2d");
  if (!ctx) {
    return;
  }

  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, rect.width, rect.height);

  const viewport = {
    cx: rect.width * 0.5,
    cy: rect.height * 0.72,
    unit: Math.min(rect.width, rect.height) * 0.24,
    center: {
      x: report.meta.grid_width * 0.5,
      y: report.meta.grid_depth * 0.5,
      z: report.meta.max_layers * 0.62,
    },
  };

  const checks = checksFromType(typeItem);
  const showRods = state.showRods && isStepActive("C1");
  const showPanels = state.showPanels;
  const showConnectors = state.showConnectors && isStepActive("C1");
  const showSupport = state.showSupport && isStepActive("C2");
  const showCom = state.showCom && isStepActive("C3");
  const showCross = isStepActive("C2");
  const showInterfaces = state.showInterface && isStepActive("C1");

  for (let x = 0; x <= report.meta.grid_width; x += 1) {
    const from = projectPoint({ x, y: 0, z: 0 }, state.camera, viewport);
    const to = projectPoint({ x, y: report.meta.grid_depth, z: 0 }, state.camera, viewport);
    drawLine(ctx, from, to, x === 0 || x === report.meta.grid_width ? "rgba(188, 202, 218, 0.78)" : "rgba(167, 181, 198, 0.42)", 1.0, x === 0 || x === report.meta.grid_width ? [] : [4, 5]);
  }

  for (let y = 0; y <= report.meta.grid_depth; y += 1) {
    const from = projectPoint({ x: 0, y, z: 0 }, state.camera, viewport);
    const to = projectPoint({ x: report.meta.grid_width, y, z: 0 }, state.camera, viewport);
    drawLine(ctx, from, to, y === 0 || y === report.meta.grid_depth ? "rgba(188, 202, 218, 0.78)" : "rgba(167, 181, 198, 0.42)", 1.0, y === 0 || y === report.meta.grid_depth ? [] : [4, 5]);
  }

  // Empty upper layers are still part of declared boundary, draw guide planes to avoid
  // visually misreading them as single-layer declarations.
  for (let layer = 1; layer < typeItem.layer_masks.length; layer += 1) {
    if (!state.showLayers[layer]) {
      continue;
    }
    const mask = typeItem.layer_masks[layer];
    if (mask !== 0) {
      continue;
    }
    const z = layer * 1.05 + 0.06;
    const p00 = projectPoint({ x: 0, y: 0, z }, state.camera, viewport);
    const p10 = projectPoint({ x: report.meta.grid_width, y: 0, z }, state.camera, viewport);
    const p11 = projectPoint({ x: report.meta.grid_width, y: report.meta.grid_depth, z }, state.camera, viewport);
    const p01 = projectPoint({ x: 0, y: report.meta.grid_depth, z }, state.camera, viewport);
    drawPolygon(ctx, [p00, p10, p11, p01], "rgba(182, 191, 203, 0.08)", "rgba(198, 207, 218, 0.48)", 1.0);
    drawLine(ctx, p00, p10, "rgba(198, 207, 218, 0.62)", 1.0, [6, 5]);
    drawLine(ctx, p10, p11, "rgba(198, 207, 218, 0.62)", 1.0, [6, 5]);
    drawLine(ctx, p11, p01, "rgba(198, 207, 218, 0.62)", 1.0, [6, 5]);
    drawLine(ctx, p01, p00, "rgba(198, 207, 218, 0.62)", 1.0, [6, 5]);
    drawTextTag(ctx, p00, `L${layer + 1} empty`, "rgba(214, 223, 234, 0.95)");
  }

  let rodCount = 0;
  if (state.showLayers[0] && showRods) {
    const baseMask = typeItem.layer_masks[0] || 0;
    const cornerSet = new Set();
    const rodTop = (report.meta.max_layers + 0.2) * 1.05;

    for (let bit = 0; bit < report.meta.cell_count; bit += 1) {
      if (((baseMask >> bit) & 1) === 0) {
        continue;
      }
      const x = bit % report.meta.grid_width;
      const y = Math.floor(bit / report.meta.grid_width);
      [`${x},${y}`, `${x + 1},${y}`, `${x},${y + 1}`, `${x + 1},${y + 1}`].forEach((item) => cornerSet.add(item));
    }
    rodCount = cornerSet.size;

    cornerSet.forEach((token) => {
      const [tx, ty] = token.split(",");
      const x = Number(tx);
      const y = Number(ty);
      const from = projectPoint({ x, y, z: 0 }, state.camera, viewport);
      const to = projectPoint({ x, y, z: rodTop }, state.camera, viewport);
      drawRod(ctx, from, to);
    });
  }

  const interfaceTokenSet = new Set();
  if (showInterfaces || showConnectors) {
    for (let layer = 0; layer < typeItem.layer_masks.length; layer += 1) {
      if (!state.showLayers[layer]) {
        continue;
      }
      const mask = typeItem.layer_masks[layer];
      for (let bit = 0; bit < report.meta.cell_count; bit += 1) {
        if (((mask >> bit) & 1) === 0) {
          continue;
        }
        const x = bit % report.meta.grid_width;
        const y = Math.floor(bit / report.meta.grid_width);
        const z = layer * 1.05 + 0.04;
        [`${x},${y},${z}`, `${x + 1},${y},${z}`, `${x},${y + 1},${z}`, `${x + 1},${y + 1},${z}`]
          .forEach((item) => interfaceTokenSet.add(item));
      }
    }

    interfaceTokenSet.forEach((token) => {
      const [tx, ty, tz] = token.split(",");
      const node = projectPoint(
        { x: Number(tx), y: Number(ty), z: Number(tz) },
        state.camera,
        viewport,
      );
      if (showInterfaces) {
        drawNode(
          ctx,
          node,
          2.4,
          "rgba(191, 203, 216, 0.9)",
          "rgba(244, 249, 255, 0.95)",
        );
      }
      if (showConnectors) {
        drawConnectorGlyph(ctx, node);
      }
    });
  }

  if (showSupport) {
    const baseMask = typeItem.layer_masks[0] || 0;
    for (let layer = 1; layer < typeItem.layer_masks.length; layer += 1) {
      if (!state.showLayers[layer]) {
        continue;
      }

      for (let bit = 0; bit < report.meta.cell_count; bit += 1) {
        if (((typeItem.layer_masks[layer] >> bit) & 1) === 0) {
          continue;
        }

        const baseActive = ((baseMask >> bit) & 1) === 1;
        const x = (bit % report.meta.grid_width) + 0.5;
        const y = Math.floor(bit / report.meta.grid_width) + 0.5;

        const from = projectPoint({ x, y, z: 0.04 }, state.camera, viewport);
        const to = projectPoint({ x, y, z: layer * 1.05 + 0.04 }, state.camera, viewport);

        if (baseActive) {
          drawLine(ctx, from, to, "rgba(120, 162, 198, 0.72)", 1.1, [4, 4]);
        } else {
          drawLine(ctx, from, to, "rgba(214, 95, 111, 0.85)", 1.4, [3, 3]);
        }
      }
    }
  }

  const cells = buildCells(typeItem);
  const queue = cells
    .map((cell) => {
      const p = projectPoint({ x: cell.x + 0.5, y: cell.y + 0.5, z: cell.layer + 0.05 }, state.camera, viewport);
      return { cell, depth: p.depth + p.y * 0.0005 };
    })
    .sort((a, b) => a.depth - b.depth);

  if (showPanels) {
    queue.forEach((item) => {
      drawPanel(
        ctx,
        item.cell,
        state.camera,
        viewport,
        showCross,
        typeItem.layer_masks[item.cell.layer] || 0,
      );
    });
  }

  if (showCom) {
    const com = centerOfMass(cells);
    if (com) {
      const onFloor = projectPoint({ x: com.x, y: com.y, z: 0 }, state.camera, viewport);
      const inAir = projectPoint(com, state.camera, viewport);
      const inside = com.x >= 0 && com.x <= report.meta.grid_width && com.y >= 0 && com.y <= report.meta.grid_depth;
      const color = inside ? "rgba(73, 232, 162, 0.95)" : "rgba(255, 106, 106, 0.95)";

      drawLine(ctx, onFloor, inAir, color, 1.7, [5, 4]);
      ctx.beginPath();
      ctx.arc(onFloor.x, onFloor.y, 4.5, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.beginPath();
      ctx.arc(inAir.x, inAir.y, 4.5, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(255, 242, 176, 0.96)";
      ctx.fill();
    }
  }

  const unsupported = cells.filter((cell) => cell.unsupported).length;
  metaBox.textContent = [
    `active_cells=${cells.length}`,
    `panels=${showPanels ? cells.length : 0}`,
    `rods=${rodCount}`,
    `connectors=${showConnectors ? interfaceTokenSet.size : 0}`,
    `interface_nodes=${interfaceTokenSet.size}`,
    `unsupported_cells=${unsupported}`,
    `C2=${checks.C2 ? "OK" : "X"}`,
    `C3=${checks.C3 ? "OK" : "X"}`,
    `C4=${checks.C4 ? "OK" : "X"}`,
    `status=${passWithRules(typeItem) ? "PASSED" : "FAILED"}`,
  ].join(" | ");
}

function updateURL() {
  const p = new URLSearchParams();
  p.set("variant", currentVariantKey);
  if (state.currentId) {
    p.set("type", String(state.currentId));
  }
  if (state.primary) p.set("primary", state.primary === "ALL" ? "ALL" : "ACTIVE");
  if (state.secondary) p.set("secondary", state.secondary);
  const fullMask = fullBoundaryMask();
  if (state.boundaryMask !== fullMask) {
    p.set("bm", state.boundaryMask.toString(36));
  }
  const ruleMask = encodeRuleMask(state.rules);
  if (ruleMask !== "11111") {
    p.set("rr", ruleMask);
  }
  history.replaceState({}, "", `type.html?${p.toString()}`);
  localStorage.setItem("shelf_variant_key", currentVariantKey);
  localStorage.setItem("shelf_rule_mask", ruleMask);
}

function renderBoundaryControls() {
  const areaSel = document.getElementById("boundary-area");
  const layerSel = document.getElementById("boundary-layers");
  const profile = profileByKey(currentVariantKey);
  const parsed = parseVariantKey(currentVariantKey);
  areaSel.value = String(profile ? profile.area : (parsed ? parsed.area : 1));
  layerSel.value = String(profile ? profile.max_layers : (parsed ? parsed.layers : 1));
}

function renderHeader() {
  const typeItem = getCurrentType();
  const ruleMask = encodeRuleMask(state.rules);
  const runtimeStatus = typeItem ? (passWithRules(typeItem) ? "passed" : "failed") : "";
  const rr = ruleMask !== "11111" ? `&rr=${encodeURIComponent(ruleMask)}` : "";
  const scopePrimary = state.primary === "ALL" ? "ALL" : "ACTIVE";
  const chips = [
    `A=${report.meta.footprint_area_cells}`,
    `N<=${report.meta.max_layers}`,
    `primary=${scopePrimary}`,
    `secondary=${state.secondary || "ALL"}`,
    `boundary=${bitCount(state.boundaryMask)}/${report.meta.cell_count}`,
    `scope_types=${state.ids.length}`,
    `rr=${ruleMask}`,
  ];
  if (typeItem) {
    document.getElementById("title").textContent = `3D 详情 | #${typeItem.type_id} / ${typeItem.group_id}`;
    document.getElementById("type-desc").textContent = `key=${typeItem.canonical_key} | active=${typeItem.active_cells_per_layer.join("/")} | effective_layers=${typeItem.effective_layers}/${typeItem.declared_layers} | ratio=${typeItem.projection_ratio.toFixed(2)}`;
    chips.unshift(`status=${runtimeStatus}`);
    if (typeItem.is_degenerate_single_layer) {
      chips.unshift("退化单层(上层为空)");
    }
  } else {
    document.getElementById("title").textContent = "3D 详情 | 当前边界无可用组合";
    document.getElementById("type-desc").textContent = "请恢复部分边界单元，或调整 A / N。";
  }
  document.getElementById("chips").innerHTML = chips.map((item) => `<span class=\"chip\">${item}</span>`).join("");

  const groupHref = scopePrimary === "ALL"
    ? `groups.html?variant=${encodeURIComponent(currentVariantKey)}${rr}`
    : `group.html?variant=${encodeURIComponent(currentVariantKey)}&primary=ACTIVE${state.secondary ? `&secondary=${encodeURIComponent(state.secondary)}` : ""}${rr}`;

  document.getElementById("breadcrumb").innerHTML = [
    `<a href=\"groups.html?variant=${encodeURIComponent(currentVariantKey)}${rr}\">分组总览</a>`,
    `<span>/</span>`,
    `<a href=\"${groupHref}\">组合列表</a>`,
    `<span>/</span>`,
    `<span>${typeItem ? `#${typeItem.type_id}` : "无组合"}</span>`,
  ].join("");
}

function renderTypeSelects() {
  const select = document.getElementById("type-select");
  const compare = document.getElementById("compare-select");
  if (!select || !compare) {
    return;
  }

  select.innerHTML = state.ids
    .map((id) => {
      const item = typeMap.get(id);
      if (!item) return "";
      return `<option value=\"${id}\">#${id} | ${item.group_id} | ${passWithRules(item) ? "passed" : "failed"}</option>`;
    })
    .join("");

  compare.innerHTML = state.ids
    .map((id) => {
      const item = typeMap.get(id);
      if (!item) return "";
      return `<option value=\"${id}\">#${id} | ${item.group_id}</option>`;
    })
    .join("");

  if (!state.ids.length) {
    select.innerHTML = '<option value="">无可用组合</option>';
    compare.innerHTML = '<option value="">无可用组合</option>';
    return;
  }

  select.value = String(state.currentId);
  compare.value = String(state.compareId);
}

function renderLayerSwitches() {
  const host = document.getElementById("layer-switches");
  host.innerHTML = state.showLayers.map((enabled, idx) => {
    return `<label><input type=\"checkbox\" data-layer=\"${idx}\" ${enabled ? "checked" : ""} />显示 L${idx + 1}</label>`;
  }).join("");

  host.querySelectorAll("input[data-layer]").forEach((node) => {
    node.addEventListener("change", () => {
      const idx = Number(node.getAttribute("data-layer"));
      state.showLayers[idx] = node.checked;
      renderCanvases();
    });
  });
}

function setBoundaryMask(mask) {
  state.boundaryMask = normalizeBoundaryMask(mask);
  recomputeVisibleTypeIds();
  updateURL();
  renderAll();
}

function renderBoundaryMaskEditor() {
  const host = document.getElementById("boundary-mask-grid");
  const meta = document.getElementById("boundary-mask-meta");
  if (!host || !meta) {
    return;
  }

  host.style.gridTemplateColumns = `repeat(${report.meta.grid_width}, minmax(0, 1fr))`;
  const cells = [];
  for (let bit = 0; bit < report.meta.cell_count; bit += 1) {
    const active = ((state.boundaryMask >> bit) & 1) === 1;
    cells.push(`<button type=\"button\" class=\"boundary-mask-cell ${active ? "active" : ""}\" data-bit=\"${bit}\" title=\"cell-${bit}\"></button>`);
  }
  host.innerHTML = cells.join("");

  const activeCount = bitCount(state.boundaryMask);
  meta.textContent = `boundary_active=${activeCount}/${report.meta.cell_count} | visible_types=${state.ids.length}`;

  host.querySelectorAll("button[data-bit]").forEach((node) => {
    node.addEventListener("click", () => {
      const bit = Number(node.getAttribute("data-bit"));
      setBoundaryMask(state.boundaryMask ^ (1 << bit));
    });
  });
}

function renderRulesPanel() {
  const typeItem = getCurrentType();
  if (!typeItem) {
    document.getElementById("rules").innerHTML = "";
    document.getElementById("step-label").textContent = "当前回放步骤: 无";
    document.getElementById("reasons").textContent = "当前规则 + 边界掩码下无可用组合。";
    document.getElementById("meta").textContent = `boundary_mask=${state.boundaryMask.toString(2)} | rr=${encodeRuleMask(state.rules)} | visible_types=0`;
    return;
  }
  const checks = checksFromType(typeItem);
  const disabledRuleCodes = new Set(
    RULE_DEFS.filter((item) => !state.rules[item.id]).map((item) => item.id)
  );
  const replayToRule = {
    C2: "C2",
    C3: "C3",
    C4: "C4",
  };

  const rows = replaySteps.map((step, idx) => {
    const active = idx <= state.stepIdx;
    const mappedRule = replayToRule[step.code] || "";
    const isDisabled = mappedRule && disabledRuleCodes.has(mappedRule);
    const pass = checks[step.code];
    const stateClass = !active || isDisabled ? "state-pending" : (pass ? "state-ok" : "state-bad");
    const stateText = !active ? "pending" : (isDisabled ? "OFF" : (pass ? "OK" : "X"));
    return `<div class=\"rule-row\"><span>${step.label}</span><span class=\"${stateClass}\">${stateText}</span></div>`;
  });

  const extraRows = [
    ["B1 边界层数", checks.B1, false],
    ["B2 固定占地", checks.B2, disabledRuleCodes.has("B2")],
  ].map((item) => {
    const stateClass = item[2] ? "state-pending" : (item[1] ? "state-ok" : "state-bad");
    const stateText = item[2] ? "OFF" : (item[1] ? "OK" : "X");
    return `<div class=\"rule-row\"><span>${item[0]}</span><span class=\"${stateClass}\">${stateText}</span></div>`;
  });

  document.getElementById("rules").innerHTML = rows.join("") + extraRows.join("");
  document.getElementById("step-label").textContent = `当前回放步骤: ${replaySteps[state.stepIdx].label}`;

  const reasons = typeItem.verification.reasons || [];
  const reasonMap = {
    B1: "B1: 激活层数超过边界上限",
    B2: "B2: 底层占地未满足固定占地",
    C2: "C2: 支撑链/连通性不足",
    C3: "C3: 重心投影越出占地",
    C4: "C4: 多层模式下存在空层（每层必须放置隔板）",
    "target_efficiency must be > baseline_efficiency": "EFF: 当前效率未高于基线",
  };
  const reasonText = reasons.map((item) => reasonMap[item] || item);
  const activeFailedRules = RULE_DEFS
    .filter((rule) => state.rules[rule.id] && !ruleResult(typeItem, rule.id))
    .map((rule) => rule.id);
  const relaxedFailedRules = RULE_DEFS
    .filter((rule) => !state.rules[rule.id] && !ruleResult(typeItem, rule.id))
    .map((rule) => rule.id);
  const activePass = passWithRules(typeItem);
  if (!activePass) {
    document.getElementById("reasons").textContent = reasons.length
      ? `失败原因: ${reasonText.join("; ")}`
      : `失败原因: ${activeFailedRules.join(", ") || "边界或组合契约"}`;
  } else if (relaxedFailedRules.length) {
    document.getElementById("reasons").textContent =
      `当前通过（放宽规则后）；若恢复规则将触发: ${relaxedFailedRules.join(", ")}`;
  } else {
    document.getElementById("reasons").textContent = "该组合在当前启用规则下通过验证。";
  }

  const supported = (() => {
    const baseMask = typeItem.layer_masks[0] || 0;
    let sum = 0;
    for (let i = 1; i < typeItem.layer_masks.length; i += 1) {
      sum += (typeItem.layer_masks[i] & baseMask).toString(2).split("0").join("").length;
    }
    return sum;
  })();

  document.getElementById("meta").textContent = [
    `legacy_group=${typeItem.group_id}`,
    `active_cells_per_layer=${typeItem.active_cells_per_layer.join("/")}`,
    `supported_cells=${supported}`,
    `projection_ratio=${typeItem.projection_ratio.toFixed(3)}`,
    `candidate_combo=${report.meta.module_combo.join("+")}`,
  ].join(" | ");
}

function renderDiffPanel() {
  const box = document.getElementById("diff-box");
  if (!state.compareEnabled) {
    box.classList.add("hidden");
    box.textContent = "";
    return;
  }

  const a = getCurrentType();
  const b = getCompareType();
  if (!a || !b) {
    box.classList.add("hidden");
    box.textContent = "";
    return;
  }
  const lines = [];
  let totalDiff = 0;

  for (let i = 0; i < report.meta.max_layers; i += 1) {
    const am = a.layer_masks[i] || 0;
    const bm = b.layer_masks[i] || 0;
    const xor = (am ^ bm).toString(2).split("0").join("").length;
    const overlap = (am & bm).toString(2).split("0").join("").length;
    totalDiff += xor;
    lines.push(`L${i + 1}: diff=${xor}, overlap=${overlap}`);
  }

  lines.push(`total_diff=${totalDiff}`);
  lines.push(`ratio_delta=${(a.projection_ratio - b.projection_ratio).toFixed(3)}`);

  box.classList.remove("hidden");
  box.textContent = `对比 #${a.type_id} vs #${b.type_id} | ${lines.join(" | ")}`;
}

function renderCanvases() {
  const main = getCurrentType();
  drawStructure("main-canvas", "main-meta", main);
  if (!main) {
    document.getElementById("main-meta").textContent = "无可用组合（当前边界掩码过滤后结果为空）";
  }

  const compareCard = document.getElementById("compare-card");
  if (state.compareEnabled && main) {
    compareCard.classList.remove("hidden");
    drawStructure("compare-canvas", "compare-meta", getCompareType());
  } else {
    compareCard.classList.add("hidden");
  }

  renderDiffPanel();
}

function syncCameraControls() {
  document.getElementById("yaw").value = String(Math.round(state.camera.yaw));
  document.getElementById("pitch").value = String(Math.round(state.camera.pitch));
  document.getElementById("zoom").value = String(Math.round(state.camera.zoom * 100));
}

function syncToggleControls() {
  document.getElementById("show-rods").checked = state.showRods;
  document.getElementById("show-panels").checked = state.showPanels;
  document.getElementById("show-connectors").checked = state.showConnectors;
  document.getElementById("show-support").checked = state.showSupport;
  document.getElementById("show-com").checked = state.showCom;
  document.getElementById("show-interface").checked = state.showInterface;
  document.getElementById("compare-enabled").checked = state.compareEnabled;
}

function attachCanvasInteractions(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) {
    return;
  }

  canvas.addEventListener("mousedown", (event) => {
    state.dragging = true;
    state.dragX = event.clientX;
    state.dragY = event.clientY;
    canvas.classList.add("dragging");
  });

  canvas.addEventListener("wheel", (event) => {
    event.preventDefault();
    const delta = event.deltaY < 0 ? 0.06 : -0.06;
    state.camera.zoom = clamp(state.camera.zoom + delta, 0.65, 1.9);
    syncCameraControls();
    renderCanvases();
  }, { passive: false });
}

function moveCurrent(offset) {
  const index = state.ids.indexOf(state.currentId);
  if (index < 0) {
    return;
  }
  const nextIndex = clamp(index + offset, 0, state.ids.length - 1);
  state.currentId = state.ids[nextIndex];
  state.pinnedTypeId = state.currentId;
  if (state.compareId === state.currentId && state.ids.length > 1) {
    state.compareId = state.ids[(nextIndex + 1) % state.ids.length];
  }
  updateURL();
  renderAll();
}

function renderAll() {
  renderBoundaryControls();
  syncCameraControls();
  syncToggleControls();
  renderHeader();
  renderTypeSelects();
  renderLayerSwitches();
  renderBoundaryMaskEditor();
  renderRulesPanel();
  renderCanvases();
}

function wireEvents() {
  document.getElementById("apply-boundary").addEventListener("click", async () => {
    const area = Number.parseInt(document.getElementById("boundary-area").value || "0", 10);
    const layers = Number.parseInt(document.getElementById("boundary-layers").value || "0", 10);
    if (!Number.isFinite(area) || !Number.isFinite(layers) || area <= 0 || layers <= 0) {
      window.alert("A 和 N 必须是正整数。");
      return;
    }
    try {
      currentVariantKey = await ensureVariantGenerated(area, layers, encodeRuleMask(state.rules));
    } catch (err) {
      window.alert(`生成失败: ${String(err && err.message ? err.message : err)}`);
      return;
    }
    state.primary = "ACTIVE";
    state.secondary = "";
    state.currentId = 0;
    state.pinnedTypeId = 0;
    refreshVariantContext(true);
    updateURL();
    renderAll();
  });

  document.getElementById("prev-type").addEventListener("click", () => moveCurrent(-1));
  document.getElementById("next-type").addEventListener("click", () => moveCurrent(1));

  document.getElementById("type-select").addEventListener("change", (event) => {
    state.currentId = Number(event.target.value);
    if (!Number.isFinite(state.currentId) || !state.currentId) {
      return;
    }
    state.pinnedTypeId = state.currentId;
    if (state.compareId === state.currentId && state.ids.length > 1) {
      state.compareId = state.ids.find((id) => id !== state.currentId) || state.currentId;
    }
    updateURL();
    renderAll();
  });

  document.getElementById("compare-select").addEventListener("change", (event) => {
    state.compareId = Number(event.target.value);
    if (!Number.isFinite(state.compareId) || !state.compareId) {
      return;
    }
    renderCanvases();
  });

  document.getElementById("boundary-mask-all").addEventListener("click", () => {
    setBoundaryMask(fullBoundaryMask());
  });

  document.getElementById("boundary-mask-clear").addEventListener("click", () => {
    setBoundaryMask(0);
  });

  document.getElementById("compare-enabled").addEventListener("change", (event) => {
    state.compareEnabled = event.target.checked;
    renderCanvases();
  });

  document.getElementById("show-rods").addEventListener("change", (event) => {
    state.showRods = event.target.checked;
    renderCanvases();
  });

  document.getElementById("show-panels").addEventListener("change", (event) => {
    state.showPanels = event.target.checked;
    renderCanvases();
  });

  document.getElementById("show-connectors").addEventListener("change", (event) => {
    state.showConnectors = event.target.checked;
    renderCanvases();
  });

  document.getElementById("show-support").addEventListener("change", (event) => {
    state.showSupport = event.target.checked;
    renderCanvases();
  });

  document.getElementById("show-com").addEventListener("change", (event) => {
    state.showCom = event.target.checked;
    renderCanvases();
  });

  document.getElementById("show-interface").addEventListener("change", (event) => {
    state.showInterface = event.target.checked;
    renderCanvases();
  });

  document.getElementById("step-prev").addEventListener("click", () => {
    state.stepIdx = clamp(state.stepIdx - 1, 0, replaySteps.length - 1);
    renderRulesPanel();
    renderCanvases();
  });

  document.getElementById("step-next").addEventListener("click", () => {
    state.stepIdx = clamp(state.stepIdx + 1, 0, replaySteps.length - 1);
    renderRulesPanel();
    renderCanvases();
  });

  document.getElementById("step-reset").addEventListener("click", () => {
    state.stepIdx = replaySteps.length - 1;
    renderRulesPanel();
    renderCanvases();
  });

  document.getElementById("yaw").addEventListener("input", (event) => {
    state.camera.yaw = Number(event.target.value);
    renderCanvases();
  });
  document.getElementById("pitch").addEventListener("input", (event) => {
    state.camera.pitch = Number(event.target.value);
    renderCanvases();
  });
  document.getElementById("zoom").addEventListener("input", (event) => {
    state.camera.zoom = Number(event.target.value) / 100;
    renderCanvases();
  });

  document.getElementById("reset-camera").addEventListener("click", () => {
    state.camera.yaw = 34;
    state.camera.pitch = 30;
    state.camera.zoom = 1.1;
    syncCameraControls();
    renderCanvases();
  });

  document.getElementById("copy-link").addEventListener("click", async () => {
    const url = new URL(window.location.href);
    url.searchParams.set("variant", currentVariantKey);
    if (state.currentId) {
      url.searchParams.set("type", String(state.currentId));
    }
    if (state.primary) {
      url.searchParams.set("primary", state.primary);
    }
    if (state.secondary) {
      url.searchParams.set("secondary", state.secondary);
    }
    const ruleMask = encodeRuleMask(state.rules);
    if (ruleMask !== "11111") {
      url.searchParams.set("rr", ruleMask);
    } else {
      url.searchParams.delete("rr");
    }
    const fullMask = fullBoundaryMask();
    if (state.boundaryMask !== fullMask) {
      url.searchParams.set("bm", state.boundaryMask.toString(36));
    } else {
      url.searchParams.delete("bm");
    }
    try {
      await navigator.clipboard.writeText(url.toString());
      document.getElementById("copy-link").textContent = "已复制";
      setTimeout(() => {
        document.getElementById("copy-link").textContent = "复制直链";
      }, 900);
    } catch (_err) {
      document.getElementById("copy-link").textContent = "复制失败";
      setTimeout(() => {
        document.getElementById("copy-link").textContent = "复制直链";
      }, 900);
    }
  });

  window.addEventListener("mousemove", (event) => {
    if (!state.dragging) {
      return;
    }
    const dx = event.clientX - state.dragX;
    const dy = event.clientY - state.dragY;
    state.dragX = event.clientX;
    state.dragY = event.clientY;

    state.camera.yaw = clamp(state.camera.yaw + dx * 0.28, 10, 80);
    state.camera.pitch = clamp(state.camera.pitch + dy * 0.22, 10, 70);
    syncCameraControls();
    renderCanvases();
  });

  window.addEventListener("mouseup", () => {
    if (!state.dragging) {
      return;
    }
    state.dragging = false;
    document.querySelectorAll(".viewer-canvas").forEach((item) => item.classList.remove("dragging"));
  });

  window.addEventListener("resize", () => {
    renderCanvases();
  });

  window.addEventListener("keydown", (event) => {
    if (event.target && ["INPUT", "SELECT", "TEXTAREA"].includes(event.target.tagName)) {
      return;
    }
    if (event.key === "ArrowLeft") {
      moveCurrent(-1);
    }
    if (event.key === "ArrowRight") {
      moveCurrent(1);
    }
  });

  attachCanvasInteractions("main-canvas");
  attachCanvasInteractions("compare-canvas");
}

async function initPage() {
  const parsed = parseVariantKey(currentVariantKey) || parseVariantKey(fallbackVariantKey());
  if (parsed) {
    try {
      currentVariantKey = await ensureVariantGenerated(
        parsed.area,
        parsed.layers,
        encodeRuleMask(state.rules),
      );
    } catch (_err) {
      currentVariantKey = fallbackVariantKey();
    }
  }
  refreshVariantContext(false);
  syncCameraControls();
  wireEvents();
  renderAll();
}

initPage();
"""

    return render_page("Shelf Type 3D", body, script)


def main() -> None:
    """运行置物架框架示例并输出多页面交互式可视化报告。"""
    goal = Goal("Increase storage access efficiency per footprint area")
    rules = CombinationRules.default()
    valid_combos = rules.valid_subsets()
    candidate_combo = {Module.ROD, Module.CONNECTOR, Module.PANEL}
    hypothesis = Hypothesis(
        hypothesis_id="H1",
        statement="With valid boundary and combination, access efficiency should improve",
    )

    boundary_profiles: list[dict[str, Any]] = []
    variants: dict[str, dict[str, Any]] = {}
    boundary_map: dict[str, BoundaryDefinition] = {}

    check_messages = {
        "B1_layers_within_limit": "active layers exceed Boundary.max_layers",
        "B2_fixed_footprint": "base footprint must exactly match configured area",
        "C2_support_continuity": (
            "C2 violated: support/continuity contract failed "
            "(rod/interface readiness, footprint path, or bridge connectivity)"
        ),
        "C3_center_projection_stable": "C3 violated: center of mass projection is outside footprint",
        "C4_upper_layer_engaged": (
            "C4 violated: multi-layer mode requires every declared upper layer to be non-empty"
        ),
    }

    # Keep the prebuilt payload intentionally small. Arbitrary A/N requests are served
    # at runtime by /api/variant, so docs bootstrap should only include a light baseline.
    area_min = env_int("SHELF_AREA_MIN", 4, minimum=1)
    area_max = env_int("SHELF_AREA_MAX", 4, minimum=1)
    layer_min = env_int("SHELF_LAYER_MIN", 2, minimum=1)
    layer_max = env_int("SHELF_LAYER_MAX", 2, minimum=1)

    if area_min > area_max:
        area_min, area_max = area_max, area_min
    if layer_min > layer_max:
        layer_min, layer_max = layer_max, layer_min

    for area_cells in range(area_min, area_max + 1):
        grid_width, grid_depth = infer_grid_dimensions(area_cells)
        for max_layers in range(layer_min, layer_max + 1):
            key = variant_key(area_cells, max_layers)
            boundary = BoundaryDefinition(
                layers_n=max_layers,
                payload_p_per_layer=30.0,
                space_s_per_layer=Space3D(width=2.0, depth=2.0, height=30.0),
                opening_o=Opening2D(width=1.8, height=1.6),
                footprint_a=Footprint2D(width=float(grid_width), depth=float(grid_depth)),
            )

            specs, meta = generate_shelf_type_specs(
                boundary=boundary,
                footprint_area_cells=area_cells,
                max_layers=max_layers,
                baseline_efficiency=1.0,
                rules=rules,
                combo=candidate_combo,
            )
            specs_payload = [item.to_dict() for item in specs]

            if specs:
                sample_checks = specs[0].structural_checks
            else:
                sample_masks = ((1 << meta["cell_count"]) - 1,) + (0,) * (max_layers - 1)
                sample_checks = {
                    **evaluate_boundary_checks(
                        sample_masks,
                        boundary=boundary,
                        footprint_area_cells=area_cells,
                    ),
                    **evaluate_structural_checks(
                        sample_masks,
                        grid_width=meta["grid_width"],
                        grid_depth=meta["grid_depth"],
                        combo=candidate_combo,
                    ),
                }

            verification_result = verify(
                VerificationInput(
                    boundary=boundary,
                    combo=candidate_combo,
                    valid_combinations=valid_combos,
                    baseline_efficiency=1.0,
                    target_efficiency=1.01,
                    extra_checks=sample_checks,
                    extra_check_messages=check_messages,
                )
            )

            variant_report = build_report_payload(
                goal=goal,
                boundary=boundary,
                hypothesis=hypothesis,
                candidate_combo=candidate_combo,
                valid_combos=valid_combos,
                types=specs_payload,
                meta=meta,
                verification_result=verification_result.to_dict(),
            )

            variants[key] = {
                "boundary": variant_report["boundary"],
                "summary": variant_report["summary"],
                "histogram": variant_report["histogram"],
                "meta": variant_report["meta"],
                "grouping": variant_report["grouping"],
                "types": variant_report["types"],
                "candidate": variant_report["candidate"],
            }
            boundary_profiles.append(
                {
                    "key": key,
                    "area": area_cells,
                    "max_layers": max_layers,
                    "grid": [grid_width, grid_depth],
                    "label": f"A={area_cells}, N<={max_layers}, grid={grid_width}x{grid_depth}",
                }
            )
            boundary_map[key] = boundary

    default_key = variant_key(4, 2)
    if default_key not in variants:
        default_key = boundary_profiles[0]["key"]
    default_variant = variants[default_key]
    default_boundary = boundary_map[default_key]

    report_payload = {
        "title": "Shelf Type Grouping + 3D Explorer",
        "goal": goal.to_dict(),
        "hypothesis": hypothesis.to_dict(),
        "strict_mapping": strict_mapping_meta(),
        "logic_record_path": "docs/logic_record.json",
        "default_variant_key": default_key,
        "boundary_limits": {
            "area": {"min": area_min, "max": area_max},
            "layers": {"min": layer_min, "max": layer_max},
        },
        "boundary_profiles": boundary_profiles,
        "variants": variants,
        **default_variant,
    }

    logic_record = build_logic_record(
        goal=goal,
        boundary=default_boundary,
        result_ok=bool(default_variant["candidate"]["verification"].get("passed", False)),
        summary=default_variant["summary"],
        grouping=default_variant["grouping"],
    )
    logic_record.export_json("docs/logic_record.json")

    REPORT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(
        json.dumps(report_payload, ensure_ascii=False),
        encoding="utf-8",
    )
    REPORT_DATA_JS_PATH.write_text(
        "window.__SHELF_REPORT__ = "
        + json.dumps(report_payload, ensure_ascii=False).replace("</", "<\\/")
        + ";",
        encoding="utf-8",
    )

    groups_html = render_groups_page(report_payload)
    GROUPS_HTML_PATH.write_text(groups_html, encoding="utf-8")
    GROUP_HTML_PATH.write_text(render_group_page(report_payload), encoding="utf-8")
    TYPE_HTML_PATH.write_text(render_type_page(report_payload), encoding="utf-8")
    LANDING_HTML_PATH.write_text(groups_html, encoding="utf-8")

    snapshot = {
        "goal": goal.to_dict(),
        "boundary": default_boundary.to_dict(),
        "hypothesis": hypothesis.to_dict(),
        "strict_mapping": strict_mapping_meta(),
        "default_variant_key": default_key,
        "boundary_profile_count": len(boundary_profiles),
        "candidate_combo": modules_to_list(candidate_combo),
        "valid_combinations": [modules_to_list(item) for item in valid_combos],
        "verification": default_variant["candidate"]["verification"],
        "summary": report_payload["summary"],
        "logic_record_path": "docs/logic_record.json",
        "visual_report_json": REPORT_JSON_PATH.as_posix(),
        "visual_pages": {
            "landing": LANDING_HTML_PATH.as_posix(),
            "groups": GROUPS_HTML_PATH.as_posix(),
            "group": GROUP_HTML_PATH.as_posix(),
            "type": TYPE_HTML_PATH.as_posix(),
            "data_js": REPORT_DATA_JS_PATH.as_posix(),
        },
    }

    print(json.dumps(snapshot, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
