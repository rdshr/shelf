from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path

from domain.models import CandidateEvaluation, DiscreteGrid
from visualization.type_gallery_3d import generate_type_gallery_3d
from visualization.type_grouping import build_type_groups


@dataclass(frozen=True)
class TypeSubpagesArtifacts:
    index_html: str
    group_pages: list[str]
    group_count: int
    type_count: int


def _occupied_cells_by_layer(candidate: CandidateEvaluation) -> dict[int, set[tuple[int, int]]]:
    occupied = candidate.topology.occupied_cells_by_layer()
    return {layer: set(cells) for layer, cells in occupied.items()}


def _candidate_svg(candidate: CandidateEvaluation, grid: DiscreteGrid, card_w: int = 180, card_h: int = 180) -> str:
    layers = max(1, grid.layers_n)
    margin = 12
    gap = 6
    panel_h = (card_h - margin * 2 - gap * (layers - 1)) / layers
    panel_w = card_w - margin * 2

    layer_cells = _occupied_cells_by_layer(candidate)
    parts: list[str] = [
        f'<svg width="{card_w}" height="{card_h}" viewBox="0 0 {card_w} {card_h}" xmlns="http://www.w3.org/2000/svg">',
        '<rect x="0" y="0" width="100%" height="100%" fill="#ffffff"/>',
    ]

    palette = ["#fdd0a2", "#fdae6b", "#fd8d3c", "#e6550d", "#a63603"]

    for layer in range(layers):
        y0 = margin + layer * (panel_h + gap)
        parts.append(
            f'<rect x="{margin}" y="{y0}" width="{panel_w}" height="{panel_h}" fill="#f8f8f8" stroke="#cccccc" stroke-width="1"/>'
        )

        cell_w = panel_w / grid.x_cells
        cell_h = panel_h / grid.y_cells

        for x in range(grid.x_cells + 1):
            xx = margin + x * cell_w
            parts.append(
                f'<line x1="{xx}" y1="{y0}" x2="{xx}" y2="{y0 + panel_h}" stroke="#d4d4d4" stroke-width="0.6"/>'
            )
        for y in range(grid.y_cells + 1):
            yy = y0 + y * cell_h
            parts.append(
                f'<line x1="{margin}" y1="{yy}" x2="{margin + panel_w}" y2="{yy}" stroke="#d4d4d4" stroke-width="0.6"/>'
            )

        color = palette[layer % len(palette)]
        for cx, cy in layer_cells.get(layer, set()):
            rx = margin + cx * cell_w
            ry = y0 + cy * cell_h
            parts.append(
                f'<rect x="{rx}" y="{ry}" width="{cell_w}" height="{cell_h}" fill="{color}" stroke="#666" stroke-width="0.7"/>'
            )

        parts.append(
            f'<text x="{margin + panel_w + 4}" y="{y0 + panel_h * 0.55}" font-size="9" fill="#666">L{layer}</text>'
        )

    parts.append("</svg>")
    return "".join(parts)


def _build_group_page(
    output_path: Path,
    title: str,
    group_title: str,
    group_desc: str,
    cards_html: str,
    relative_3d_html: str | None,
) -> None:
    iframe = ""
    if relative_3d_html is not None:
        iframe = (
            "<h3>该类型组 3D 总览</h3>"
            f"<iframe src='{escape(relative_3d_html)}' title='group-3d' "
            "style='width:100%;height:520px;border:1px solid #dcdcdc;border-radius:8px;background:#fff;'></iframe>"
        )

    html = "".join(
        [
            "<!doctype html><html><head><meta charset='utf-8'/>",
            f"<title>{escape(title)} - {escape(group_title)}</title>",
            "<style>",
            "body{font-family:ui-monospace,Consolas,monaco;margin:16px;background:#f5f5f5;color:#222;}",
            "a{color:#0b57d0;text-decoration:none;} a:hover{text-decoration:underline;}",
            ".meta{background:#fff;border:1px solid #ddd;border-radius:8px;padding:12px;margin:10px 0 14px 0;line-height:1.5;}",
            ".board{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px;}",
            ".card{background:#fff;border:1px solid #ddd;border-radius:8px;padding:8px;box-shadow:0 1px 3px rgba(0,0,0,.05);}",
            ".head{display:flex;justify-content:space-between;align-items:center;font-size:12px;margin-bottom:6px;}",
            ".badge{padding:2px 6px;border-radius:999px;font-size:11px;}",
            ".badge.valid{background:#e6f4ea;color:#1e7f3b;}",
            ".badge.invalid{background:#fde8e8;color:#a61b1b;}",
            ".key{font-size:10px;line-height:1.25;word-break:break-all;color:#333;margin-top:4px;}",
            "svg{width:100%;height:auto;border:1px solid #eee;border-radius:4px;background:#fafafa;}",
            "</style></head><body>",
            "<div><a href='index.html'>← 返回类型索引</a></div>",
            f"<h2>{escape(group_title)}</h2>",
            f"<div class='meta'>{group_desc}</div>",
            iframe,
            "<h3>该类型组下的全部分型图</h3>",
            f"<div class='board'>{cards_html}</div>",
            "</body></html>",
        ]
    )
    output_path.write_text(html, encoding="utf-8")


def generate_type_subpages(
    candidates: list[CandidateEvaluation],
    grid: DiscreteGrid,
    output_dir: str | Path,
    title: str = "Shelf Type Subpages",
    include_group_3d: bool = True,
    group_3d_columns: int = 8,
) -> TypeSubpagesArtifacts:
    if not candidates:
        raise ValueError("candidates is empty")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    groups = build_type_groups(candidates, grid)
    group_pages: list[str] = []
    index_rows: list[str] = []

    for group_idx, group in enumerate(groups):
        gid = f"G{group_idx:02d}"
        page_name = f"{gid}.html"
        page_path = out_dir / page_name

        counts_str = ",".join(str(x) for x in group.counts_per_layer)
        group_title = f"{gid} 类型组"
        group_desc = (
            f"结构族 family = {group.family}；"
            f"分类规则：每层占用单元数向量 = ({counts_str})；"
            f"非空层数 = {group.active_layers}；"
            f"总占用单元 = {group.total_cells}；"
            f"本组分型数 = {len(group.items)}。"
            "<br/>"
            "说明：这个子页面汇总该类型组下的全部分型图，便于同类内部比较。"
        )

        cards: list[str] = []
        for local_idx, (global_idx, candidate) in enumerate(group.items):
            svg = _candidate_svg(candidate, grid)
            badge = "valid" if candidate.structural_valid else "invalid"
            cards.append(
                "".join(
                    [
                        '<div class="card">',
                        f'<div class="head"><span>#{global_idx} / local {local_idx}</span><span class="badge {badge}">{badge}</span></div>',
                        svg,
                        f'<div class="key">{escape(candidate.canonical_key)}</div>',
                        "</div>",
                    ]
                )
            )

        rel_3d: str | None = None
        if include_group_3d:
            group_3d_name = f"{gid}_3d.html"
            group_3d_path = out_dir / group_3d_name
            generate_type_gallery_3d(
                candidates=[candidate for _, candidate in group.items],
                grid=grid,
                output_html=group_3d_path,
                columns=group_3d_columns,
                title=f"{title} - {gid}",
            )
            rel_3d = group_3d_name

        _build_group_page(
            output_path=page_path,
            title=title,
            group_title=group_title,
            group_desc=group_desc,
            cards_html="".join(cards),
            relative_3d_html=rel_3d,
        )

        group_pages.append(str(page_path))

        preview_cards = "".join(
            _candidate_svg(candidate, grid, card_w=100, card_h=100)
            for _, candidate in group.items[:3]
        )
        index_rows.append(
            "".join(
                [
                    '<div class="row">',
                    f"<div><a href='{page_name}'><strong>{gid}</strong></a></div>",
                    f"<div>family={group.family}</div>",
                    f"<div>cells/layer=({counts_str})</div>",
                    f"<div>active={group.active_layers}</div>",
                    f"<div>count={len(group.items)}</div>",
                    f"<div class='previews'>{preview_cards}</div>",
                    "</div>",
                ]
            )
        )

    index_html = "".join(
        [
            "<!doctype html><html><head><meta charset='utf-8'/>",
            f"<title>{escape(title)}</title>",
            "<style>",
            "body{font-family:ui-monospace,Consolas,monaco;margin:16px;background:#f2f2f2;color:#222;}",
            ".meta{background:#fff;border:1px solid #ddd;border-radius:8px;padding:12px;margin-bottom:12px;line-height:1.5;}",
            ".row{display:grid;grid-template-columns:120px 140px 220px 90px 90px 1fr;gap:10px;align-items:center;",
            "background:#fff;border:1px solid #ddd;border-radius:8px;padding:8px;margin-bottom:8px;}",
            ".previews{display:flex;gap:6px;overflow:auto;}",
            "svg{border:1px solid #eee;border-radius:4px;background:#fafafa;}",
            "</style></head><body>",
            f"<h2>{escape(title)}</h2>",
            f"<div class='meta'>总分型数 = {len(candidates)}，类型组数 = {len(groups)}。点击每组进入子页面，查看该组全部分型图与组内 3D 总览。</div>",
            "".join(index_rows),
            "</body></html>",
        ]
    )

    index_path = out_dir / "index.html"
    index_path.write_text(index_html, encoding="utf-8")

    return TypeSubpagesArtifacts(
        index_html=str(index_path),
        group_pages=group_pages,
        group_count=len(groups),
        type_count=len(candidates),
    )
