from __future__ import annotations

from dataclasses import dataclass
from html import escape
import math
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from domain.models import CandidateEvaluation, DiscreteGrid


@dataclass(frozen=True)
class GalleryArtifacts:
    image_path: str
    html_path: str
    type_count: int


def _occupied_cells_by_layer(candidate: CandidateEvaluation) -> dict[int, set[tuple[int, int]]]:
    occupied = candidate.topology.occupied_cells_by_layer()
    return {layer: set(cells) for layer, cells in occupied.items()}


def _draw_layered_card(
    ax,
    candidate: CandidateEvaluation,
    grid: DiscreteGrid,
    index: int,
) -> None:
    ax.set_xlim(0, grid.x_cells)
    ax.set_ylim(0, grid.y_cells * grid.layers_n)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])

    layer_cells = _occupied_cells_by_layer(candidate)
    palette = ["#fdd0a2", "#fdae6b", "#fd8d3c", "#e6550d", "#a63603"]

    for layer in range(grid.layers_n):
        y_offset = layer * grid.y_cells

        # Layer background and grid lines.
        ax.add_patch(
            Rectangle((0, y_offset), grid.x_cells, grid.y_cells, facecolor="#f7f7f7", edgecolor="#dddddd", linewidth=0.8)
        )
        for x in range(grid.x_cells + 1):
            ax.plot([x, x], [y_offset, y_offset + grid.y_cells], color="#d0d0d0", linewidth=0.5)
        for y in range(grid.y_cells + 1):
            y_line = y_offset + y
            ax.plot([0, grid.x_cells], [y_line, y_line], color="#d0d0d0", linewidth=0.5)

        color = palette[layer % len(palette)]
        for cell_x, cell_y in layer_cells.get(layer, set()):
            ax.add_patch(
                Rectangle((cell_x, y_offset + cell_y), 1, 1, facecolor=color, edgecolor="#666666", linewidth=0.7)
            )

        ax.text(
            grid.x_cells + 0.05,
            y_offset + grid.y_cells * 0.5,
            f"L{layer}",
            fontsize=5,
            va="center",
            ha="left",
            color="#555555",
        )

    title_color = "#0b6623" if candidate.structural_valid else "#a50f15"
    ax.set_title(f"#{index}", fontsize=6, color=title_color, pad=1.0)


def _candidate_svg(candidate: CandidateEvaluation, grid: DiscreteGrid, card_w: int = 150, card_h: int = 180) -> str:
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


def generate_type_gallery(
    candidates: list[CandidateEvaluation],
    grid: DiscreteGrid,
    output_image: str | Path,
    output_html: str | Path,
    columns: int = 12,
    title: str = "Shelf Type Gallery",
) -> GalleryArtifacts:
    if not candidates:
        raise ValueError("candidates is empty")
    cols = max(1, columns)
    rows = math.ceil(len(candidates) / cols)

    # 1) Contact sheet image.
    fig_w = max(10.0, cols * 1.35)
    fig_h = max(8.0, rows * 1.35)
    fig, axes = plt.subplots(rows, cols, figsize=(fig_w, fig_h), squeeze=False)
    fig.suptitle(f"{title} | total={len(candidates)}", fontsize=12)

    idx = 0
    for r in range(rows):
        for c in range(cols):
            ax = axes[r][c]
            if idx < len(candidates):
                _draw_layered_card(ax, candidates[idx], grid, idx)
            else:
                ax.axis("off")
            idx += 1

    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.97))
    image_path = Path(output_image)
    image_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(image_path, dpi=220)
    plt.close(fig)

    # 2) Gallery HTML.
    cards: list[str] = []
    for i, candidate in enumerate(candidates):
        badge = "valid" if candidate.structural_valid else "invalid"
        svg = _candidate_svg(candidate, grid)
        key = escape(candidate.canonical_key)
        reason = "" if not candidate.reasons else "<br/>".join(escape(item) for item in candidate.reasons[:3])
        cards.append(
            "".join(
                [
                    '<div class="card">',
                    f'<div class="head"><span class="idx">#{i}</span><span class="badge {badge}">{badge}</span></div>',
                    svg,
                    f'<div class="key">{key}</div>',
                    f'<div class="reason">{reason}</div>' if reason else "",
                    "</div>",
                ]
            )
        )

    html = "".join(
        [
            "<!doctype html><html><head><meta charset='utf-8'/>",
            f"<title>{escape(title)}</title>",
            "<style>",
            "body{font-family:ui-monospace,Consolas,monaco; margin:16px; background:#f3f3f3;}",
            ".summary{margin-bottom:12px; color:#333;}",
            ".board{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px;}",
            ".card{background:#fff;border:1px solid #ddd;border-radius:8px;padding:8px;box-shadow:0 1px 3px rgba(0,0,0,.05);}",
            ".head{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;font-size:12px;}",
            ".badge{padding:2px 6px;border-radius:999px;font-size:11px;}",
            ".badge.valid{background:#e6f4ea;color:#1e7f3b;}",
            ".badge.invalid{background:#fde8e8;color:#a61b1b;}",
            ".key{font-size:10px;line-height:1.25;color:#333;word-break:break-all;margin-top:4px;}",
            ".reason{font-size:10px;line-height:1.25;color:#a61b1b;margin-top:4px;}",
            "svg{width:100%;height:auto;border:1px solid #eee;border-radius:4px;background:#fafafa;}",
            "</style></head><body>",
            f"<h2>{escape(title)}</h2>",
            f"<div class='summary'>grid={grid.x_cells}x{grid.y_cells}x{grid.layers_n}, types={len(candidates)}</div>",
            f"<div class='summary'>这页用于横向对比多个分型，不需要逐张打开。</div>",
            "<div class='board'>",
            "".join(cards),
            "</div></body></html>",
        ]
    )

    html_path = Path(output_html)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html, encoding="utf-8")

    return GalleryArtifacts(
        image_path=str(image_path),
        html_path=str(html_path),
        type_count=len(candidates),
    )
