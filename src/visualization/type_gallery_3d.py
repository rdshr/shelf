from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

import plotly.graph_objects as go

from domain.models import CandidateEvaluation, DiscreteGrid
from geometry.builders import build_geometry
from visualization.type_grouping import TypeGroup, build_type_groups


@dataclass(frozen=True)
class Gallery3DArtifacts:
    html_path: str
    type_count: int


def generate_type_gallery_3d(
    candidates: list[CandidateEvaluation],
    grid: DiscreteGrid,
    output_html: str | Path,
    columns: int = 16,
    title: str = "Shelf Type Gallery 3D",
) -> Gallery3DArtifacts:
    if not candidates:
        raise ValueError("candidates is empty")

    # Keep function signature compatible: old `columns` now maps to per-group local columns.
    group_local_cols = max(2, min(columns, 16))
    group_grid_cols = 4

    spacing_x = grid.footprint_width * 1.8 + 24.0
    spacing_y = grid.footprint_depth * 1.8 + 24.0
    group_gap_x = 42.0
    group_gap_y = 64.0
    top_z = grid.layers_n * grid.layer_height

    valid_x: list[float | None] = []
    valid_y: list[float | None] = []
    valid_z: list[float | None] = []
    invalid_x: list[float | None] = []
    invalid_y: list[float | None] = []
    invalid_z: list[float | None] = []

    panel_outline_x: list[float | None] = []
    panel_outline_y: list[float | None] = []
    panel_outline_z: list[float | None] = []

    panel_mesh_x: list[float] = []
    panel_mesh_y: list[float] = []
    panel_mesh_z: list[float] = []
    panel_mesh_i: list[int] = []
    panel_mesh_j: list[int] = []
    panel_mesh_k: list[int] = []

    connector_x: list[float] = []
    connector_y: list[float] = []
    connector_z: list[float] = []

    cell_frame_x: list[float | None] = []
    cell_frame_y: list[float | None] = []
    cell_frame_z: list[float | None] = []

    type_label_x: list[float] = []
    type_label_y: list[float] = []
    type_label_z: list[float] = []
    type_labels: list[str] = []

    group_label_x: list[float] = []
    group_label_y: list[float] = []
    group_label_z: list[float] = []
    group_labels: list[str] = []

    groups = build_type_groups(candidates, grid)

    group_positions: list[tuple[float, float, int, TypeGroup, int]] = []
    cursor_y = 0.0
    for row_start in range(0, len(groups), group_grid_cols):
        row_groups = groups[row_start : row_start + group_grid_cols]
        cursor_x = 0.0
        row_max_height = 0.0

        for local_g_idx, group in enumerate(row_groups):
            rows_in_group = math.ceil(len(group.items) / group_local_cols)
            block_height = max(1, rows_in_group) * spacing_y
            group_positions.append((cursor_x, cursor_y, rows_in_group, group, row_start + local_g_idx))

            block_width = max(1, min(group_local_cols, len(group.items))) * spacing_x
            cursor_x += block_width + group_gap_x
            row_max_height = max(row_max_height, block_height)

        cursor_y += row_max_height + group_gap_y

    for group_x, group_y, rows_in_group, group, group_idx in group_positions:
        items = group.items
        rows_in_group = max(1, rows_in_group)
        width_count = max(1, min(group_local_cols, len(items)))
        block_width = (width_count - 1) * spacing_x + grid.footprint_width
        block_height = (rows_in_group - 1) * spacing_y + grid.footprint_depth

        # Group frame.
        group_frame = [
            (group_x - 8.0, group_y - 8.0, 0.0),
            (group_x + block_width + 8.0, group_y - 8.0, 0.0),
            (group_x + block_width + 8.0, group_y + block_height + 8.0, 0.0),
            (group_x - 8.0, group_y + block_height + 8.0, 0.0),
            (group_x - 8.0, group_y - 8.0, 0.0),
        ]
        for fx, fy, fz in group_frame:
            cell_frame_x.append(fx)
            cell_frame_y.append(fy)
            cell_frame_z.append(fz)
        cell_frame_x.append(None)
        cell_frame_y.append(None)
        cell_frame_z.append(None)

        group_label_x.append(group_x + block_width * 0.5)
        group_label_y.append(group_y + block_height + 10.0)
        group_label_z.append(top_z + grid.layer_height * 0.34)
        group_labels.append(group.title(group_idx))

        for local_idx, (original_idx, candidate) in enumerate(items):
            local_row = local_idx // group_local_cols
            local_col = local_idx % group_local_cols
            dx = group_x + local_col * spacing_x
            dy = group_y + local_row * spacing_y

            geometry = build_geometry(candidate.topology, grid)

            for rod in geometry.rods:
                tx = [rod.start[0] + dx, rod.end[0] + dx, None]
                ty = [rod.start[1] + dy, rod.end[1] + dy, None]
                tz = [rod.start[2], rod.end[2], None]
                if candidate.structural_valid:
                    valid_x.extend(tx)
                    valid_y.extend(ty)
                    valid_z.extend(tz)
                else:
                    invalid_x.extend(tx)
                    invalid_y.extend(ty)
                    invalid_z.extend(tz)

            for node in geometry.connectors:
                connector_x.append(node.point[0] + dx)
                connector_y.append(node.point[1] + dy)
                connector_z.append(node.point[2])

            base_frame = [
                (dx, dy, 0.0),
                (dx + grid.footprint_width, dy, 0.0),
                (dx + grid.footprint_width, dy + grid.footprint_depth, 0.0),
                (dx, dy + grid.footprint_depth, 0.0),
                (dx, dy, 0.0),
            ]
            for fx, fy, fz in base_frame:
                cell_frame_x.append(fx)
                cell_frame_y.append(fy)
                cell_frame_z.append(fz)
            cell_frame_x.append(None)
            cell_frame_y.append(None)
            cell_frame_z.append(None)

            for panel in geometry.panels:
                ordered = [panel.corners[0], panel.corners[1], panel.corners[2], panel.corners[3], panel.corners[0]]
                for point in ordered:
                    panel_outline_x.append(point[0] + dx)
                    panel_outline_y.append(point[1] + dy)
                    panel_outline_z.append(point[2])
                panel_outline_x.append(None)
                panel_outline_y.append(None)
                panel_outline_z.append(None)

                base = len(panel_mesh_x)
                p0, p1, p2, p3 = panel.corners
                vertices = [
                    (p0[0] + dx, p0[1] + dy, p0[2]),
                    (p1[0] + dx, p1[1] + dy, p1[2]),
                    (p2[0] + dx, p2[1] + dy, p2[2]),
                    (p3[0] + dx, p3[1] + dy, p3[2]),
                ]
                for vx, vy, vz in vertices:
                    panel_mesh_x.append(vx)
                    panel_mesh_y.append(vy)
                    panel_mesh_z.append(vz)
                panel_mesh_i.extend([base, base])
                panel_mesh_j.extend([base + 1, base + 2])
                panel_mesh_k.extend([base + 2, base + 3])

            type_label_x.append(dx + grid.footprint_width * 0.5)
            type_label_y.append(dy + grid.footprint_depth * 0.5)
            type_label_z.append(top_z + grid.layer_height * 0.14)
            type_labels.append(f"#{original_idx}")

    fig = go.Figure()

    if valid_x:
        fig.add_trace(
            go.Scatter3d(
                x=valid_x,
                y=valid_y,
                z=valid_z,
                mode="lines",
                line={"color": "#0b3d91", "width": 5},
                name="valid rods",
                hoverinfo="skip",
            )
        )

    if invalid_x:
        fig.add_trace(
            go.Scatter3d(
                x=invalid_x,
                y=invalid_y,
                z=invalid_z,
                mode="lines",
                line={"color": "#b2182b", "width": 5},
                name="invalid rods",
                hoverinfo="skip",
            )
        )

    if panel_mesh_x:
        fig.add_trace(
            go.Mesh3d(
                x=panel_mesh_x,
                y=panel_mesh_y,
                z=panel_mesh_z,
                i=panel_mesh_i,
                j=panel_mesh_j,
                k=panel_mesh_k,
                color="#fdb863",
                opacity=0.38,
                flatshading=True,
                name="panel surfaces",
                hoverinfo="skip",
                showscale=False,
            )
        )

    if panel_outline_x:
        fig.add_trace(
            go.Scatter3d(
                x=panel_outline_x,
                y=panel_outline_y,
                z=panel_outline_z,
                mode="lines",
                line={"color": "#d95f02", "width": 3},
                name="panel outlines",
                hoverinfo="skip",
            )
        )

    if connector_x:
        fig.add_trace(
            go.Scatter3d(
                x=connector_x,
                y=connector_y,
                z=connector_z,
                mode="markers",
                marker={"size": 2.7, "color": "#444444", "opacity": 0.7},
                name="connectors",
                hoverinfo="skip",
            )
        )

    if cell_frame_x:
        fig.add_trace(
            go.Scatter3d(
                x=cell_frame_x,
                y=cell_frame_y,
                z=cell_frame_z,
                mode="lines",
                line={"color": "#9e9e9e", "width": 2},
                name="type/group frames",
                hoverinfo="skip",
            )
        )

    fig.add_trace(
        go.Scatter3d(
            x=type_label_x,
            y=type_label_y,
            z=type_label_z,
            mode="text",
            text=type_labels,
            textfont={"size": 9, "color": "#222"},
            name="type index",
            hoverinfo="skip",
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=group_label_x,
            y=group_label_y,
            z=group_label_z,
            mode="text",
            text=group_labels,
            textfont={"size": 11, "color": "#111"},
            name="group labels",
            hoverinfo="skip",
        )
    )

    fig.update_layout(
        title=f"{title} | total={len(candidates)} | groups={len(groups)}",
        scene={
            "xaxis_title": "Gallery X",
            "yaxis_title": "Gallery Y",
            "zaxis_title": "Height",
            "aspectmode": "data",
            "xaxis": {"backgroundcolor": "#f7f7f7", "gridcolor": "#dddddd"},
            "yaxis": {"backgroundcolor": "#f7f7f7", "gridcolor": "#dddddd"},
            "zaxis": {"backgroundcolor": "#f7f7f7", "gridcolor": "#dddddd"},
            "camera": {"eye": {"x": 1.25, "y": 1.45, "z": 0.95}},
        },
        margin={"l": 0, "r": 0, "b": 0, "t": 44},
        legend={"orientation": "h", "y": -0.04},
    )

    out = Path(output_html)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out), include_plotlyjs="cdn")

    return Gallery3DArtifacts(html_path=str(out), type_count=len(candidates))
