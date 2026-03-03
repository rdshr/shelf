from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, cast

from domain.models import CandidateEvaluation, DiscreteGrid, StructureTopology
from geometry.builders import build_geometry
from visualization.viewer_backend import FilterMode, ViewerBackendResult, enumerate_candidates_for_view


def _draw_topology(
    ax,
    topology: StructureTopology,
    grid: DiscreteGrid,
    structural_valid: bool,
) -> None:
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    geometry = build_geometry(topology, grid)
    rod_color = "#1f77b4" if structural_valid else "#d62728"
    panel_color = "#ff7f0e" if structural_valid else "#ff9896"

    for rod in geometry.rods:
        ax.plot(
            [rod.start[0], rod.end[0]],
            [rod.start[1], rod.end[1]],
            [rod.start[2], rod.end[2]],
            color=rod_color,
            linewidth=2.0,
        )

    if geometry.connectors:
        ax.scatter(
            [node.point[0] for node in geometry.connectors],
            [node.point[1] for node in geometry.connectors],
            [node.point[2] for node in geometry.connectors],
            color="#2ca02c",
            s=20,
        )

    for panel in geometry.panels:
        poly = Poly3DCollection([list(panel.corners)], alpha=0.5, facecolor=panel_color)
        poly.set_edgecolor("#444444")
        ax.add_collection3d(poly)

    max_x = grid.footprint_width
    max_y = grid.footprint_depth
    max_z = grid.layers_n * grid.layer_height

    ax.set_xlim(0.0, max_x if max_x > 0 else 1.0)
    ax.set_ylim(0.0, max_y if max_y > 0 else 1.0)
    ax.set_zlim(0.0, max_z if max_z > 0 else 1.0)
    ax.set_box_aspect((max_x if max_x > 0 else 1.0, max_y if max_y > 0 else 1.0, max_z if max_z > 0 else 1.0))
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")


@dataclass
class _ViewerState:
    backend: ViewerBackendResult
    selected_index: int = 0


class InteractiveShelfViewer:
    """Native interactive 3D window for shelf topology exploration."""

    def __init__(self) -> None:
        import matplotlib.pyplot as plt
        from matplotlib.widgets import Button, CheckButtons, RadioButtons, Slider

        self._plt = plt

        self._x_cells = 2
        self._y_cells = 2
        self._layers_n = 2
        self._cell_width = 45.0
        self._cell_depth = 20.0
        self._layer_height = 30.0
        self._allow_empty_layer = True
        self._filter_mode: FilterMode = "valid"

        backend = enumerate_candidates_for_view(
            x_cells=self._x_cells,
            y_cells=self._y_cells,
            layers_n=self._layers_n,
            cell_width=self._cell_width,
            cell_depth=self._cell_depth,
            layer_height=self._layer_height,
            allow_empty_layer=self._allow_empty_layer,
            filter_mode=self._filter_mode,
        )
        self._state = _ViewerState(backend=backend)

        self.fig = plt.figure(figsize=(14, 9))
        self.ax3d = cast(Any, self.fig.add_axes((0.05, 0.25, 0.62, 0.7), projection="3d"))
        self.ax_info = self.fig.add_axes((0.70, 0.25, 0.28, 0.7))
        self.ax_info.axis("off")

        self.slider_x = Slider(self.fig.add_axes((0.10, 0.18, 0.22, 0.03)), "x_cells", 1, 2, valinit=2, valstep=1)
        self.slider_y = Slider(self.fig.add_axes((0.35, 0.18, 0.22, 0.03)), "y_cells", 1, 2, valinit=2, valstep=1)
        self.slider_layers = Slider(
            self.fig.add_axes((0.60, 0.18, 0.22, 0.03)),
            "layers",
            1,
            4,
            valinit=2,
            valstep=1,
        )

        self.slider_w = Slider(self.fig.add_axes((0.10, 0.13, 0.22, 0.03)), "cell_w", 10, 120, valinit=45)
        self.slider_d = Slider(self.fig.add_axes((0.35, 0.13, 0.22, 0.03)), "cell_d", 10, 120, valinit=20)
        self.slider_h = Slider(self.fig.add_axes((0.60, 0.13, 0.22, 0.03)), "layer_h", 10, 80, valinit=30)

        self.btn_prev = Button(self.fig.add_axes((0.10, 0.05, 0.10, 0.05)), "Prev")
        self.btn_next = Button(self.fig.add_axes((0.22, 0.05, 0.10, 0.05)), "Next")
        self.btn_refresh = Button(self.fig.add_axes((0.35, 0.05, 0.12, 0.05)), "Recompute")

        self.check_opts = CheckButtons(self.fig.add_axes((0.50, 0.03, 0.16, 0.09)), ["allow_empty"], [True])
        self.radio_filter = RadioButtons(
            self.fig.add_axes((0.70, 0.03, 0.16, 0.12)),
            ["valid", "invalid", "all"],
            active=0,
        )

        self.slider_x.on_changed(self._on_dimension_changed)
        self.slider_y.on_changed(self._on_dimension_changed)
        self.slider_layers.on_changed(self._on_dimension_changed)

        self.slider_w.on_changed(self._on_scale_changed)
        self.slider_d.on_changed(self._on_scale_changed)
        self.slider_h.on_changed(self._on_scale_changed)

        self.btn_prev.on_clicked(self._on_prev)
        self.btn_next.on_clicked(self._on_next)
        self.btn_refresh.on_clicked(self._on_recompute)
        self.check_opts.on_clicked(self._on_check_toggle)
        self.radio_filter.on_clicked(self._on_filter_changed)

        self._render()

    def _current_candidate(self) -> CandidateEvaluation | None:
        if not self._state.backend.candidates:
            return None
        idx = max(0, min(self._state.selected_index, len(self._state.backend.candidates) - 1))
        self._state.selected_index = idx
        return self._state.backend.candidates[idx]

    def _recompute(self) -> None:
        self._x_cells = int(self.slider_x.val)
        self._y_cells = int(self.slider_y.val)
        self._layers_n = int(self.slider_layers.val)

        self._cell_width = float(self.slider_w.val)
        self._cell_depth = float(self.slider_d.val)
        self._layer_height = float(self.slider_h.val)

        self._state.backend = enumerate_candidates_for_view(
            x_cells=self._x_cells,
            y_cells=self._y_cells,
            layers_n=self._layers_n,
            cell_width=self._cell_width,
            cell_depth=self._cell_depth,
            layer_height=self._layer_height,
            allow_empty_layer=self._allow_empty_layer,
            filter_mode=self._filter_mode,
        )
        self._state.selected_index = 0

    def _render(self) -> None:
        candidate = self._current_candidate()
        grid = self._state.backend.grid

        self.ax3d.clear()
        if candidate is None:
            self.ax3d.set_title("No candidate for current filter")
            self.ax3d.set_xlim(0, 1)
            self.ax3d.set_ylim(0, 1)
            self.ax3d.set_zlim(0, 1)
        else:
            _draw_topology(self.ax3d, candidate.topology, grid, candidate.structural_valid)
            self.ax3d.set_title("Structure Topology (Window Interactive)")

        self.ax_info.clear()
        self.ax_info.axis("off")
        self.ax_info.text(
            0.0,
            1.0,
            self._info_text(candidate),
            va="top",
            ha="left",
            fontsize=10,
            family="monospace",
        )
        self.fig.canvas.draw_idle()

    def _info_text(self, candidate: CandidateEvaluation | None) -> str:
        base = self._state.backend.enumeration
        lines = [
            f"filter_mode: {self._filter_mode}",
            f"allow_empty_layer: {self._allow_empty_layer}",
            f"grid: {self._x_cells}x{self._y_cells}x{self._layers_n}",
            f"cell size: ({self._cell_width:.1f}, {self._cell_depth:.1f}, {self._layer_height:.1f})",
            "",
            f"raw candidates: {base.raw_candidate_count}",
            f"unique types: {base.stats.unique_types}",
            f"valid types: {len(base.valid_candidates())}",
            f"invalid types: {len(base.invalid_candidates())}",
            "",
            f"shown list count: {len(self._state.backend.candidates)}",
            f"selected index: {self._state.selected_index}",
        ]

        if candidate is not None:
            lines.extend(
                [
                    "",
                    f"family: {candidate.topology.family.value}",
                    f"structural_valid: {candidate.structural_valid}",
                    f"panel_count: {candidate.topology.panel_count()}",
                    f"canonical_key:",
                    candidate.canonical_key,
                ]
            )
            if candidate.reasons:
                lines.append("reasons:")
                lines.extend(f"- {item}" for item in candidate.reasons[:4])

        return "\n".join(lines)

    def _on_dimension_changed(self, _value: float) -> None:
        # Dimensions change topology search space; force explicit recompute to avoid accidental heavy runs.
        pass

    def _on_scale_changed(self, _value: float) -> None:
        # Scale only affects geometry rendering for current topology.
        self._x_cells = int(self.slider_x.val)
        self._y_cells = int(self.slider_y.val)
        self._layers_n = int(self.slider_layers.val)
        self._cell_width = float(self.slider_w.val)
        self._cell_depth = float(self.slider_d.val)
        self._layer_height = float(self.slider_h.val)

        candidate = self._current_candidate()
        if candidate is None:
            self._render()
            return

        # Rebuild only grid to redraw current topology at new scale.
        self._state.backend = ViewerBackendResult(
            grid=DiscreteGrid(
                x_cells=self._x_cells,
                y_cells=self._y_cells,
                layers_n=self._layers_n,
                cell_width=self._cell_width,
                cell_depth=self._cell_depth,
                layer_height=self._layer_height,
            ),
            enumeration=self._state.backend.enumeration,
            candidates=self._state.backend.candidates,
        )
        self._render()

    def _on_prev(self, _event: object) -> None:
        if not self._state.backend.candidates:
            return
        self._state.selected_index = (self._state.selected_index - 1) % len(self._state.backend.candidates)
        self._render()

    def _on_next(self, _event: object) -> None:
        if not self._state.backend.candidates:
            return
        self._state.selected_index = (self._state.selected_index + 1) % len(self._state.backend.candidates)
        self._render()

    def _on_recompute(self, _event: object) -> None:
        self._recompute()
        self._render()

    def _on_check_toggle(self, _label: str | None) -> None:
        self._allow_empty_layer = bool(self.check_opts.get_status()[0])

    def _on_filter_changed(self, label: str | None) -> None:
        if label is None:
            return
        self._filter_mode = "all" if label == "all" else ("invalid" if label == "invalid" else "valid")
        self._recompute()
        self._render()

    def show(self) -> None:
        self._plt.show()


def launch_interactive_viewer() -> None:
    viewer = InteractiveShelfViewer()
    viewer.show()
