from __future__ import annotations

from pathlib import Path

from domain.models import DiscreteGrid, StructureTopology
from geometry.builders import build_geometry
from visualization.plotly_html import write_plotly_html


def _render_plotly_html(topology: StructureTopology, grid: DiscreteGrid, html_path: Path) -> Path:
    import plotly.graph_objects as go

    geometry = build_geometry(topology, grid)
    fig = go.Figure()

    for rod in geometry.rods:
        fig.add_trace(
            go.Scatter3d(
                x=[rod.start[0], rod.end[0]],
                y=[rod.start[1], rod.end[1]],
                z=[rod.start[2], rod.end[2]],
                mode="lines",
                line={"color": "#1f77b4", "width": 6},
                showlegend=False,
            )
        )

    if geometry.connectors:
        fig.add_trace(
            go.Scatter3d(
                x=[node.point[0] for node in geometry.connectors],
                y=[node.point[1] for node in geometry.connectors],
                z=[node.point[2] for node in geometry.connectors],
                mode="markers",
                marker={"size": 4, "color": "#d62728"},
                showlegend=False,
            )
        )

    for panel in geometry.panels:
        xs = [panel.corners[idx][0] for idx in (0, 1, 2, 3)]
        ys = [panel.corners[idx][1] for idx in (0, 1, 2, 3)]
        zs = [panel.corners[idx][2] for idx in (0, 1, 2, 3)]
        fig.add_trace(
            go.Mesh3d(
                x=xs,
                y=ys,
                z=zs,
                i=[0, 0],
                j=[1, 2],
                k=[2, 3],
                opacity=0.6,
                color="#ff7f0e",
                flatshading=True,
                showscale=False,
            )
        )

    fig.update_layout(
        title=f"Structure Topology 3D ({topology.family.value})",
        scene={
            "xaxis_title": "X",
            "yaxis_title": "Y",
            "zaxis_title": "Z",
            "aspectmode": "data",
        },
        margin={"l": 0, "r": 0, "b": 0, "t": 30},
    )

    html_path.parent.mkdir(parents=True, exist_ok=True)
    return write_plotly_html(fig, html_path)


def _render_obj(topology: StructureTopology, grid: DiscreteGrid, obj_path: Path) -> Path:
    geometry = build_geometry(topology, grid)
    lines: list[str] = ["# Shelf topology fallback OBJ"]
    vertices: list[tuple[float, float, float]] = []

    def add_vertex(vertex: tuple[float, float, float]) -> int:
        vertices.append(vertex)
        lines.append(f"v {vertex[0]} {vertex[1]} {vertex[2]}")
        return len(vertices)

    for panel in geometry.panels:
        idx = [add_vertex(corner) for corner in panel.corners]
        lines.append(f"f {idx[0]} {idx[1]} {idx[2]}")
        lines.append(f"f {idx[0]} {idx[2]} {idx[3]}")

    for rod in geometry.rods:
        s = add_vertex(rod.start)
        e = add_vertex(rod.end)
        lines.append(f"l {s} {e}")

    obj_path.parent.mkdir(parents=True, exist_ok=True)
    obj_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return obj_path


def render_structure(
    topology: StructureTopology,
    grid: DiscreteGrid,
    output_dir: str | Path,
    file_stem: str,
) -> dict[str, str]:
    out_dir = Path(output_dir)
    html_path = out_dir / f"{file_stem}.html"
    obj_path = out_dir / f"{file_stem}.obj"

    result: dict[str, str] = {}
    try:
        created = _render_plotly_html(topology, grid, html_path)
        result["interactive_html"] = str(created)
    except Exception as exc:  # pragma: no cover - fallback path
        result["interactive_html_error"] = str(exc)

    created_obj = _render_obj(topology, grid, obj_path)
    result["obj_fallback"] = str(created_obj)
    return result
