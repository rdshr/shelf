from __future__ import annotations

import argparse
import itertools
import json
import math
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from shelf_framework import (
    BoundaryDefinition,
    CombinationRules,
    ConnectorPlacement,
    ConnectorUnit,
    Footprint2D,
    Module,
    Opening2D,
    OpeningPreference,
    PanelLayer,
    RodPanelConnection,
    ShelfStructure,
    Space3D,
    SupportKind,
    SupportOrientation,
    SupportUnit,
    UnitCell,
    VerificationInput,
    verify,
)

DEFAULT_OUTPUT_DIR = REPO_ROOT / "docs" / "diagrams"

CANVAS_W = 1500
CANVAS_H = 880
DRAW_X0 = 80
DRAW_X1 = 980
DRAW_Y0 = 120
DRAW_Y1 = 760
INFO_X0 = 1020
INFO_W = 440
PANEL_W = 700
PANEL_H = 18

BG = "#FFFFFF"
TEXT_MAIN = "#0F172A"
TEXT_SUB = "#475569"
PANEL_FILL = "#E2E8F0"
PANEL_STROKE = "#475569"
ROD_COLOR = "#1E293B"
CONNECTOR_COLORS = {
    ConnectorPlacement.CORNER: "#16A34A",
    ConnectorPlacement.PREDEFINED_SLOT: "#2563EB",
    ConnectorPlacement.CUSTOM: "#64748B",
}
PASS_COLOR = "#16A34A"
FAIL_COLOR = "#DC2626"

MANDATORY_RULE_IDS = ["R1", "R2", "R3", "R4", "R5", "R6", "R7"]

ORIENTATION_MAP = {
    "vertical": SupportOrientation.VERTICAL,
    "angled": SupportOrientation.ANGLED,
}
SUPPORT_KIND_MAP = {
    "rod": SupportKind.ROD,
    "panel": SupportKind.PANEL,
}
PLACEMENT_MAP = {
    "corner": ConnectorPlacement.CORNER,
    "predefined_slot": ConnectorPlacement.PREDEFINED_SLOT,
    "custom": ConnectorPlacement.CUSTOM,
}
CONTOUR_SHIFT_STEP_MAP = {
    "aligned": 0.0,
    "staggered": 2.0,
}


@dataclass(frozen=True)
class ArrangementOption:
    support_count: int
    support_kind: SupportKind
    support_orientation: SupportOrientation
    connector_placement: ConnectorPlacement
    contour_mode: str
    opening_direction: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "support_count": self.support_count,
            "support_kind": self.support_kind.value,
            "support_orientation": self.support_orientation.value,
            "connector_placement": self.connector_placement.value,
            "contour_mode": self.contour_mode,
            "opening_direction": self.opening_direction,
        }


@dataclass(frozen=True)
class RodGeometry:
    x_top: float
    x_bottom: float
    y_top: float
    y_bottom: float

    def x_at(self, y: float) -> float:
        if self.y_bottom == self.y_top:
            return self.x_top
        t = (y - self.y_top) / (self.y_bottom - self.y_top)
        return self.x_top + t * (self.x_bottom - self.x_top)


def parse_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_support_counts(value: str) -> list[int]:
    out: list[int] = []
    for item in parse_csv(value):
        count = int(item)
        if count <= 0:
            raise ValueError(f"support count must be > 0: {count}")
        out.append(count)
    if not out:
        raise ValueError("support counts must be non-empty")
    return out


def parse_orientations(value: str) -> list[SupportOrientation]:
    out: list[SupportOrientation] = []
    for item in parse_csv(value):
        if item not in ORIENTATION_MAP:
            raise ValueError(
                f"unsupported orientation: {item}; allowed={sorted(ORIENTATION_MAP)}"
            )
        out.append(ORIENTATION_MAP[item])
    if not out:
        raise ValueError("orientations must be non-empty")
    return out


def parse_support_kinds(value: str) -> list[SupportKind]:
    out: list[SupportKind] = []
    for item in parse_csv(value):
        if item not in SUPPORT_KIND_MAP:
            raise ValueError(
                f"unsupported support kind: {item}; allowed={sorted(SUPPORT_KIND_MAP)}"
            )
        out.append(SUPPORT_KIND_MAP[item])
    if not out:
        raise ValueError("support kinds must be non-empty")
    return out


def parse_placements(value: str) -> list[ConnectorPlacement]:
    out: list[ConnectorPlacement] = []
    for item in parse_csv(value):
        if item not in PLACEMENT_MAP:
            raise ValueError(
                f"unsupported connector placement: {item}; allowed={sorted(PLACEMENT_MAP)}"
            )
        out.append(PLACEMENT_MAP[item])
    if not out:
        raise ValueError("connector placements must be non-empty")
    return out


def parse_contour_modes(value: str) -> list[str]:
    out: list[str] = []
    for item in parse_csv(value):
        if item not in CONTOUR_SHIFT_STEP_MAP:
            raise ValueError(
                f"unsupported contour mode: {item}; allowed={sorted(CONTOUR_SHIFT_STEP_MAP)}"
            )
        out.append(item)
    if not out:
        raise ValueError("contour modes must be non-empty")
    return out


def build_boundary(args: argparse.Namespace) -> BoundaryDefinition:
    return BoundaryDefinition(
        layers_n=args.layers,
        payload_p_per_layer=args.payload,
        space_s_per_layer=Space3D(
            width=args.space_width,
            depth=args.space_depth,
            height=args.space_height,
        ),
        opening_o=Opening2D(
            width=args.opening_width,
            height=args.opening_height,
        ),
        footprint_a=Footprint2D(
            width=args.footprint_width,
            depth=args.footprint_depth,
        ),
    )


def build_structure(boundary: BoundaryDefinition, option: ArrangementOption) -> ShelfStructure:
    support_prefix = "rod" if option.support_kind == SupportKind.ROD else "panel-support"
    supports = tuple(
        SupportUnit(
            support_id=f"{support_prefix}-{idx}",
            kind=option.support_kind,
            orientation=option.support_orientation,
        )
        for idx in range(1, option.support_count + 1)
    )
    support_ids = tuple(item.support_id for item in supports)

    contour_step = CONTOUR_SHIFT_STEP_MAP[option.contour_mode]

    layers: list[PanelLayer] = []
    connectors: list[ConnectorUnit] = []
    connections: list[RodPanelConnection] = []
    connector_ids: list[str] = []

    for level in range(1, boundary.layers_n + 1):
        panel_id = f"panel-{level}"
        layers.append(
            PanelLayer(
                panel_id=panel_id,
                level_index=level,
                width=boundary.space_s_per_layer.width,
                depth=boundary.space_s_per_layer.depth,
                layer_height=boundary.space_s_per_layer.height,
                opening=Opening2D(
                    width=boundary.opening_o.width,
                    height=boundary.opening_o.height,
                ),
                support_unit_ids=support_ids,
                normal_axis="z",
                contour_offset=(level - 1) * contour_step,
            )
        )

        for support in supports:
            connector_id = f"conn-{panel_id}-{support.support_id}"
            connector_ids.append(connector_id)
            connectors.append(
                ConnectorUnit(
                    connector_id=connector_id,
                    placement=option.connector_placement,
                )
            )
            connections.append(
                RodPanelConnection(
                    support_unit_id=support.support_id,
                    panel_id=panel_id,
                    connector_id=connector_id,
                    uses_defined_interface=True,
                    illegal_intersection=False,
                    floating=False,
                )
            )

    unit_cells = (
        UnitCell(
            cell_id="cell-1",
            layer_ids=tuple(layer.panel_id for layer in layers),
            support_unit_ids=support_ids,
            connector_ids=tuple(connector_ids),
            span_x=boundary.space_s_per_layer.width,
            span_y=boundary.space_s_per_layer.depth,
            span_z=boundary.space_s_per_layer.height * boundary.layers_n,
        ),
    )

    return ShelfStructure(
        layers=tuple(layers),
        support_units=supports,
        connectors=tuple(connectors),
        connections=tuple(connections),
        unit_cells=unit_cells,
        opening_direction=option.opening_direction,
    )


def rule_compact_status(rule_results: dict[str, bool], ids: list[str]) -> str:
    parts = []
    for item in ids:
        ok = rule_results.get(item, False)
        parts.append(f"{item}{'✓' if ok else '✗'}")
    return " ".join(parts)


def evaluate_option(
    boundary: BoundaryDefinition,
    option: ArrangementOption,
    rules: CombinationRules,
    valid_combinations: list[set[Module]],
    opening_preference: OpeningPreference,
) -> dict[str, Any]:
    structure = build_structure(boundary, option)
    combo = {Module.CONNECTOR, Module.PANEL}
    if option.support_kind == SupportKind.ROD:
        combo.add(Module.ROD)
    result = verify(
        VerificationInput(
            boundary=boundary,
            combo=combo,
            valid_combinations=valid_combinations,
            baseline_efficiency=1.0,
            target_efficiency=1.1,
            structure=structure,
            rules=rules,
            opening_preference=opening_preference,
            include_recommended_rules=False,
        )
    )

    mandatory_passed = all(
        result.rule_results.get(rule_id, False) for rule_id in MANDATORY_RULE_IDS
    )
    combination_principles_passed = (
        result.boundary_valid
        and result.combination_valid
        and mandatory_passed
    )

    return {
        "option": option,
        "structure": structure,
        "verification": result,
        "mandatory_passed": mandatory_passed,
        "combination_principles_passed": combination_principles_passed,
    }


def build_rod_geometries(option: ArrangementOption, support_count: int) -> list[RodGeometry]:
    if support_count == 1:
        xs = [(DRAW_X0 + DRAW_X1) / 2]
    else:
        left = DRAW_X0 + 120
        right = DRAW_X1 - 120
        xs = [
            left + i * (right - left) / (support_count - 1)
            for i in range(support_count)
        ]

    geos: list[RodGeometry] = []
    for x in xs:
        if option.support_orientation == SupportOrientation.ANGLED:
            geos.append(
                RodGeometry(
                    x_top=x - 18,
                    x_bottom=x + 18,
                    y_top=DRAW_Y0,
                    y_bottom=DRAW_Y1,
                )
            )
        else:
            geos.append(
                RodGeometry(
                    x_top=x,
                    x_bottom=x,
                    y_top=DRAW_Y0,
                    y_bottom=DRAW_Y1,
                )
            )
    return geos


def build_panel_rects(structure: ShelfStructure) -> list[tuple[int, float, float, float, float]]:
    layer_count = len(structure.layers)
    if layer_count == 1:
        ys = [(DRAW_Y0 + DRAW_Y1) / 2]
    else:
        step = (DRAW_Y1 - DRAW_Y0 - 60) / (layer_count - 1)
        ys = [DRAW_Y1 - 40 - i * step for i in range(layer_count)]

    rects: list[tuple[int, float, float, float, float]] = []
    for idx, layer in enumerate(structure.layers):
        shift_px = layer.contour_offset * 9.0
        x = DRAW_X0 + 100 + shift_px
        y = ys[idx]
        rects.append((layer.level_index, x, y, PANEL_W, PANEL_H))
    return rects


def draw_arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[float, float],
    end: tuple[float, float],
    color: str,
    width: int = 3,
) -> None:
    draw.line((start[0], start[1], end[0], end[1]), fill=color, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    size = 12
    left = (
        end[0] - size * math.cos(angle - math.pi / 6),
        end[1] - size * math.sin(angle - math.pi / 6),
    )
    right = (
        end[0] - size * math.cos(angle + math.pi / 6),
        end[1] - size * math.sin(angle + math.pi / 6),
    )
    draw.polygon([end, left, right], fill=color)


def render_png(
    out_path: Path,
    combo_id: str,
    data: dict[str, Any],
    boundary: BoundaryDefinition,
    opening_preference: OpeningPreference,
) -> None:
    option: ArrangementOption = data["option"]
    structure: ShelfStructure = data["structure"]
    result = data["verification"]
    rule_results = result.rule_results

    image = Image.new("RGB", (CANVAS_W, CANVAS_H), BG)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    draw.text((60, 30), f"{combo_id} | 4-layer shelf arrangement", fill=TEXT_MAIN, font=font)
    draw.text(
        (60, 55),
        f"Boundary N={boundary.layers_n}, P={boundary.payload_p_per_layer}, "
        f"S=({boundary.space_s_per_layer.width},{boundary.space_s_per_layer.depth},{boundary.space_s_per_layer.height}), "
        f"O=({boundary.opening_o.width},{boundary.opening_o.height}), "
        f"A=({boundary.footprint_a.width},{boundary.footprint_a.depth})",
        fill=TEXT_SUB,
        font=font,
    )

    draw.rectangle((DRAW_X0, DRAW_Y0, DRAW_X1, DRAW_Y1), outline="#CBD5E1", width=2)
    draw.text((DRAW_X0, DRAW_Y0 - 24), "Shelf Structural View", fill=TEXT_SUB, font=font)

    rod_geos = build_rod_geometries(option, option.support_count)
    panel_rects = build_panel_rects(structure)
    support_stroke_w = 10 if option.support_kind == SupportKind.PANEL else 4
    support_color = "#64748B" if option.support_kind == SupportKind.PANEL else ROD_COLOR

    for geo in rod_geos:
        draw.line(
            (geo.x_top, geo.y_top, geo.x_bottom, geo.y_bottom),
            fill=support_color,
            width=support_stroke_w,
        )

    for level_index, x, y, w, h in panel_rects:
        draw.rectangle((x, y, x + w, y + h), fill=PANEL_FILL, outline=PANEL_STROKE, width=2)
        draw.text((x - 42, y - 4), f"L{level_index}", fill=TEXT_SUB, font=font)

        cy = y + h / 2
        for geo in rod_geos:
            cx = geo.x_at(cy)
            cx = min(max(cx, x + 8), x + w - 8)
            color = CONNECTOR_COLORS[option.connector_placement]
            draw.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=color, outline="#0F172A", width=1)

    opening_text = f"opening dir={option.opening_direction}"
    draw_arrow(draw, (DRAW_X1 - 110, DRAW_Y0 + 60), (DRAW_X1 - 35, DRAW_Y0 + 60), "#334155")
    draw.text((DRAW_X1 - 180, DRAW_Y0 + 72), opening_text, fill=TEXT_SUB, font=font)

    info_y = 140
    draw.rectangle((INFO_X0, info_y, INFO_X0 + INFO_W, 780), outline="#CBD5E1", width=2)
    draw.text((INFO_X0 + 16, info_y + 16), "Combination Params", fill=TEXT_MAIN, font=font)
    lines = [
        f"support_count: {option.support_count}",
        f"support_kind: {option.support_kind.value}",
        f"orientation: {option.support_orientation.value}",
        f"connector_placement: {option.connector_placement.value}",
        f"contour_mode: {option.contour_mode}",
        f"opening_direction: {option.opening_direction}",
        "",
        f"combination_principles_passed: {data['combination_principles_passed']}",
        f"mandatory_rules: {rule_compact_status(rule_results, MANDATORY_RULE_IDS)}",
        "",
        f"opening_preference: dir={opening_preference.preferred_direction}, "
        f"ratio=[{opening_preference.min_ratio}, {opening_preference.max_ratio}]",
    ]
    ly = info_y + 42
    for line in lines:
        color = TEXT_SUB
        if line.startswith("combination_principles_passed"):
            color = PASS_COLOR if data["combination_principles_passed"] else FAIL_COLOR
        draw.text((INFO_X0 + 16, ly), line, fill=color, font=font)
        ly += 20

    image.save(out_path, format="PNG")


def render_svg(
    out_path: Path,
    combo_id: str,
    data: dict[str, Any],
    boundary: BoundaryDefinition,
    opening_preference: OpeningPreference,
) -> None:
    option: ArrangementOption = data["option"]
    structure: ShelfStructure = data["structure"]
    result = data["verification"]
    rule_results = result.rule_results

    rod_geos = build_rod_geometries(option, option.support_count)
    panel_rects = build_panel_rects(structure)
    support_stroke_w = 10 if option.support_kind == SupportKind.PANEL else 4
    support_color = "#64748B" if option.support_kind == SupportKind.PANEL else ROD_COLOR

    lines = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{CANVAS_W}' height='{CANVAS_H}' "
        f"viewBox='0 0 {CANVAS_W} {CANVAS_H}'>",
        "<rect x='0' y='0' width='100%' height='100%' fill='#FFFFFF' />",
        "<defs>"
        "<marker id='arrow' markerWidth='12' markerHeight='12' refX='10' refY='6' orient='auto'>"
        "<path d='M0,0 L12,6 L0,12 z' fill='#334155' />"
        "</marker>"
        "</defs>",
        (
            f"<text x='60' y='35' font-family='Arial, Helvetica, sans-serif' "
            f"font-size='21' fill='{TEXT_MAIN}'>{escape(combo_id)} | 4-layer shelf arrangement</text>"
        ),
        (
            f"<text x='60' y='60' font-family='Arial, Helvetica, sans-serif' font-size='14' fill='{TEXT_SUB}'>"
            f"Boundary N={boundary.layers_n}, P={boundary.payload_p_per_layer}, "
            f"S=({boundary.space_s_per_layer.width},{boundary.space_s_per_layer.depth},{boundary.space_s_per_layer.height}), "
            f"O=({boundary.opening_o.width},{boundary.opening_o.height}), "
            f"A=({boundary.footprint_a.width},{boundary.footprint_a.depth})"
            "</text>"
        ),
        (
            f"<rect x='{DRAW_X0}' y='{DRAW_Y0}' width='{DRAW_X1 - DRAW_X0}' "
            f"height='{DRAW_Y1 - DRAW_Y0}' fill='none' stroke='#CBD5E1' stroke-width='2' />"
        ),
        (
            f"<text x='{DRAW_X0}' y='{DRAW_Y0 - 10}' font-family='Arial, Helvetica, sans-serif' "
            f"font-size='14' fill='{TEXT_SUB}'>Shelf Structural View</text>"
        ),
    ]

    for geo in rod_geos:
        lines.append(
            f"<line x1='{geo.x_top}' y1='{geo.y_top}' x2='{geo.x_bottom}' y2='{geo.y_bottom}' "
            f"stroke='{support_color}' stroke-width='{support_stroke_w}' />"
        )

    for level_index, x, y, w, h in panel_rects:
        lines.append(
            f"<rect x='{x}' y='{y}' width='{w}' height='{h}' fill='{PANEL_FILL}' "
            f"stroke='{PANEL_STROKE}' stroke-width='2' />"
        )
        lines.append(
            f"<text x='{x - 42}' y='{y + 11}' font-family='Arial, Helvetica, sans-serif' "
            f"font-size='14' fill='{TEXT_SUB}'>L{level_index}</text>"
        )

        cy = y + h / 2
        for geo in rod_geos:
            cx = geo.x_at(cy)
            cx = min(max(cx, x + 8), x + w - 8)
            color = CONNECTOR_COLORS[option.connector_placement]
            lines.append(
                f"<circle cx='{cx}' cy='{cy}' r='5' fill='{color}' stroke='#0F172A' stroke-width='1' />"
            )

    lines.extend(
        [
            (
                f"<line x1='{DRAW_X1 - 110}' y1='{DRAW_Y0 + 60}' x2='{DRAW_X1 - 35}' y2='{DRAW_Y0 + 60}' "
                "stroke='#334155' stroke-width='3' marker-end='url(#arrow)' />"
            ),
            (
                f"<text x='{DRAW_X1 - 190}' y='{DRAW_Y0 + 84}' font-family='Arial, Helvetica, sans-serif' "
                f"font-size='14' fill='{TEXT_SUB}'>opening dir={escape(option.opening_direction)}</text>"
            ),
        ]
    )

    info_y = 140
    lines.append(
        f"<rect x='{INFO_X0}' y='{info_y}' width='{INFO_W}' height='640' fill='none' "
        "stroke='#CBD5E1' stroke-width='2' />"
    )
    lines.append(
        f"<text x='{INFO_X0 + 16}' y='{info_y + 24}' font-family='Arial, Helvetica, sans-serif' "
        f"font-size='16' fill='{TEXT_MAIN}'>Combination Params</text>"
    )

    info_lines = [
        (f"support_count: {option.support_count}", TEXT_SUB),
        (f"support_kind: {option.support_kind.value}", TEXT_SUB),
        (f"orientation: {option.support_orientation.value}", TEXT_SUB),
        (f"connector_placement: {option.connector_placement.value}", TEXT_SUB),
        (f"contour_mode: {option.contour_mode}", TEXT_SUB),
        (f"opening_direction: {option.opening_direction}", TEXT_SUB),
        ("", TEXT_SUB),
        (
            f"combination_principles_passed: {data['combination_principles_passed']}",
            PASS_COLOR if data["combination_principles_passed"] else FAIL_COLOR,
        ),
        (f"mandatory_rules: {rule_compact_status(rule_results, MANDATORY_RULE_IDS)}", TEXT_SUB),
        ("", TEXT_SUB),
        (
            f"opening_preference: dir={opening_preference.preferred_direction}, "
            f"ratio=[{opening_preference.min_ratio}, {opening_preference.max_ratio}]",
            TEXT_SUB,
        ),
    ]

    ly = info_y + 48
    for text, color in info_lines:
        lines.append(
            f"<text x='{INFO_X0 + 16}' y='{ly}' font-family='Arial, Helvetica, sans-serif' "
            f"font-size='14' fill='{color}'>{escape(text)}</text>"
        )
        ly += 22

    lines.append("</svg>")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_mermaid(combo_id: str, structure: ShelfStructure, option: ArrangementOption) -> str:
    lines = [
        "---",
        f"title: {combo_id} | 4-layer shelf arrangement",
        "---",
        "flowchart TB",
    ]

    support_ids = [item.support_id for item in structure.support_units]
    for support in structure.support_units:
        lines.append(
            f'  {support.support_id.replace("-", "_")}["{support.support_id} ({support.kind.value}, {support.orientation.value})"]'
        )

    prev_panel_node: str | None = None
    for layer in structure.layers:
        panel_node = layer.panel_id.replace("-", "_")
        lines.append(
            f'  {panel_node}["{layer.panel_id} | offset={layer.contour_offset}"]'
        )
        if prev_panel_node:
            lines.append(f"  {prev_panel_node} --> {panel_node}")
        prev_panel_node = panel_node

        for support_id in support_ids:
            support_node = support_id.replace("-", "_")
            connector_node = f"conn_{layer.panel_id.replace('-', '_')}_{support_id.replace('-', '_')}"
            lines.append(f'  {connector_node}["{option.connector_placement.value}"]')
            lines.append(f"  {support_node} --> {connector_node}")
            lines.append(f"  {connector_node} --> {panel_node}")

    return "\n".join(lines) + "\n"


def clean_output_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for pattern in ("COMBO-*.mmd", "COMBO-*.svg", "COMBO-*.png"):
        for path in output_dir.glob(pattern):
            path.unlink()
    for file_name in ("README.md", "combination_matrix.json"):
        p = output_dir / file_name
        if p.exists():
            p.unlink()


def build_overview(
    boundary: BoundaryDefinition,
    opening_preference: OpeningPreference,
    matrix: list[dict[str, Any]],
) -> str:
    all_count = len(matrix)
    valid_count = sum(1 for row in matrix if row["combination_principles_passed"])
    lines = [
        "# 4层置物架组合可视化总览",
        "",
        "本目录由 `scripts/generate_shelf_combination_diagrams.py` 自动生成。",
        "“组合原则通过”按 `R1-R7` 统一规则判定。",
        "",
        "## 边界参数",
        "",
        f"- `N`(layers): {boundary.layers_n}",
        f"- `P`(payload per layer): {boundary.payload_p_per_layer}",
        (
            "- `S`(space per layer): "
            f"({boundary.space_s_per_layer.width}, {boundary.space_s_per_layer.depth}, {boundary.space_s_per_layer.height})"
        ),
        (
            "- `O`(opening): "
            f"({boundary.opening_o.width}, {boundary.opening_o.height})"
        ),
        (
            "- `A`(footprint): "
            f"({boundary.footprint_a.width}, {boundary.footprint_a.depth})"
        ),
        (
            "- opening preference: "
            f"direction={opening_preference.preferred_direction}, "
            f"ratio=[{opening_preference.min_ratio}, {opening_preference.max_ratio}]"
        ),
        "",
        "## 统计",
        "",
        f"- 枚举组合总数: {all_count}",
        f"- 组合原则通过数: {valid_count}",
        "",
        "## 组合矩阵",
        "",
        "| 组合ID | support_count | support_kind | orientation | connector | contour | opening_dir | 组合原则 | Mermaid | SVG | PNG |",
        "|---|---:|---|---|---|---|---|---|---|---|---|",
    ]

    for row in matrix:
        option = row["option"]
        cp = "YES" if row["combination_principles_passed"] else "NO"
        files = row["diagram_files"]
        mmd = f"[{files['mmd']}](./{files['mmd']})" if "mmd" in files else "-"
        svg = f"[{files['svg']}](./{files['svg']})" if "svg" in files else "-"
        png = f"[{files['png']}](./{files['png']})" if "png" in files else "-"
        lines.append(
            f"| {row['combo_id']} | {option['support_count']} | {option['support_kind']} | {option['support_orientation']} | "
            f"{option['connector_placement']} | {option['contour_mode']} | {option['opening_direction']} | "
            f"`{cp}` | {mmd} | {svg} | {png} |"
        )

    lines.extend(
        [
            "",
            "## 使用命令",
            "",
            "```bash",
            "uv run python scripts/generate_shelf_combination_diagrams.py",
            "```",
            "",
            "可通过命令行参数修改边界和组合枚举范围。",
            "",
        ]
    )
    return "\n".join(lines)


def export_artifacts(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir).resolve()
    clean_output_dir(output_dir)

    boundary = build_boundary(args)
    opening_preference = OpeningPreference(
        preferred_direction=args.preferred_opening_direction,
        min_ratio=args.opening_ratio_min,
        max_ratio=args.opening_ratio_max,
    )

    rules = CombinationRules.default()
    valid_combos = rules.valid_subsets()

    options = list(
        itertools.product(
            parse_support_counts(args.support_counts),
            parse_support_kinds(args.support_kinds),
            parse_orientations(args.support_orientations),
            parse_placements(args.connector_placements),
            parse_contour_modes(args.contour_modes),
            parse_csv(args.opening_directions),
        )
    )

    matrix: list[dict[str, Any]] = []
    valid_export_count = 0

    for idx, (
        support_count,
        support_kind,
        orientation,
        placement,
        contour_mode,
        opening_direction,
    ) in enumerate(options, start=1):
        combo_id = f"COMBO-{idx:03d}"
        option = ArrangementOption(
            support_count=support_count,
            support_kind=support_kind,
            support_orientation=orientation,
            connector_placement=placement,
            contour_mode=contour_mode,
            opening_direction=opening_direction,
        )

        evaluated = evaluate_option(
            boundary=boundary,
            option=option,
            rules=rules,
            valid_combinations=valid_combos,
            opening_preference=opening_preference,
        )

        should_export = evaluated["combination_principles_passed"] or args.export_invalid
        files: dict[str, str] = {}
        if should_export:
            structure: ShelfStructure = evaluated["structure"]
            mmd_name = f"{combo_id}.mmd"
            svg_name = f"{combo_id}.svg"
            png_name = f"{combo_id}.png"

            (output_dir / mmd_name).write_text(
                render_mermaid(combo_id, structure, option),
                encoding="utf-8",
            )
            render_svg(
                output_dir / svg_name,
                combo_id,
                evaluated,
                boundary,
                opening_preference,
            )
            render_png(
                output_dir / png_name,
                combo_id,
                evaluated,
                boundary,
                opening_preference,
            )
            files = {"mmd": mmd_name, "svg": svg_name, "png": png_name}
            if evaluated["combination_principles_passed"]:
                valid_export_count += 1

        row = {
            "combo_id": combo_id,
            "option": option.to_dict(),
            "combination_principles_passed": evaluated["combination_principles_passed"],
            "rule_results": evaluated["verification"].rule_results,
            "diagram_files": files,
        }
        matrix.append(row)

    (output_dir / "combination_matrix.json").write_text(
        json.dumps(matrix, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "README.md").write_text(
        build_overview(boundary, opening_preference, matrix),
        encoding="utf-8",
    )

    return {
        "output_dir": str(output_dir.relative_to(REPO_ROOT)),
        "total_candidates": len(matrix),
        "combination_principles_passed": sum(1 for row in matrix if row["combination_principles_passed"]),
        "exported_diagrams": sum(1 for row in matrix if row["diagram_files"]),
        "exported_passed_diagrams": valid_export_count,
        "matrix_file": "combination_matrix.json",
        "overview_file": "README.md",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate all 4-layer shelf arrangement combinations under user-defined boundary "
            "and export visualization (Mermaid/SVG/PNG)."
        )
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))

    parser.add_argument("--layers", type=int, default=4, help="Boundary N")
    parser.add_argument("--payload", type=float, default=30.0, help="Boundary P")
    parser.add_argument("--space-width", type=float, default=80.0, help="Boundary S.width")
    parser.add_argument("--space-depth", type=float, default=35.0, help="Boundary S.depth")
    parser.add_argument("--space-height", type=float, default=30.0, help="Boundary S.height")
    parser.add_argument("--opening-width", type=float, default=65.0, help="Boundary O.width")
    parser.add_argument("--opening-height", type=float, default=28.0, help="Boundary O.height")
    parser.add_argument("--footprint-width", type=float, default=90.0, help="Boundary A.width")
    parser.add_argument("--footprint-depth", type=float, default=40.0, help="Boundary A.depth")

    parser.add_argument("--support-counts", default="1,2,3,4")
    parser.add_argument("--support-kinds", default="rod,panel")
    parser.add_argument("--support-orientations", default="vertical,angled")
    parser.add_argument("--connector-placements", default="corner,predefined_slot,custom")
    parser.add_argument("--contour-modes", default="aligned,staggered")
    parser.add_argument("--opening-directions", default="front,left")
    parser.add_argument(
        "--preferred-opening-direction",
        default="front",
        help="Used by opening direction preference check",
    )
    parser.add_argument("--opening-ratio-min", type=float, default=0.6)
    parser.add_argument("--opening-ratio-max", type=float, default=0.95)
    parser.add_argument(
        "--export-invalid",
        action="store_true",
        help="Also export diagrams for combinations that fail mandatory principles.",
    )
    args = parser.parse_args()

    summary = export_artifacts(args)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
