from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

from framework_core import Base, Capability, Goal, Hypothesis, LogicRecord, LogicStep
from shelf_domain import (
    BoundaryDefinition,
    ExactFitSpec,
    Footprint2D,
    Opening2D,
    Space3D,
    VerificationInput,
    VerificationResult,
)

from domain.enums import Module, StructureFamily

Cell = tuple[int, int]
Cell3D = tuple[int, int, int]
GridPoint3D = tuple[int, int, int]
GridEdge3D = tuple[GridPoint3D, GridPoint3D]
Point3 = tuple[float, float, float]
Vector3 = tuple[float, float, float]


@dataclass(frozen=True)
class Rect2D:
    """Axis-aligned rectangle on the discrete XY grid."""

    x0: int
    x1: int
    y0: int
    y1: int

    def validate(self) -> tuple[bool, list[str]]:
        errors: list[str] = []
        if self.x0 < 0 or self.y0 < 0:
            errors.append("rect start must be non-negative")
        if self.x1 <= self.x0:
            errors.append("x1 must be > x0")
        if self.y1 <= self.y0:
            errors.append("y1 must be > y0")
        return len(errors) == 0, errors

    def area_cells(self) -> int:
        return (self.x1 - self.x0) * (self.y1 - self.y0)

    def iter_cells(self) -> Iterable[Cell]:
        for x in range(self.x0, self.x1):
            for y in range(self.y0, self.y1):
                yield (x, y)

    def to_tuple(self) -> tuple[int, int, int, int]:
        return (self.x0, self.x1, self.y0, self.y1)


@dataclass(frozen=True)
class DiscreteGrid:
    """Finite discrete modeling space used for bounded exhaustive enumeration."""

    x_cells: int
    y_cells: int
    layers_n: int
    cell_width: float = 1.0
    cell_depth: float = 1.0
    layer_height: float = 1.0

    def validate(self) -> tuple[bool, list[str]]:
        errors: list[str] = []
        if self.x_cells <= 0:
            errors.append("x_cells must be > 0")
        if self.y_cells <= 0:
            errors.append("y_cells must be > 0")
        if self.layers_n <= 0:
            errors.append("layers_n must be > 0")
        if self.cell_width <= 0:
            errors.append("cell_width must be > 0")
        if self.cell_depth <= 0:
            errors.append("cell_depth must be > 0")
        if self.layer_height <= 0:
            errors.append("layer_height must be > 0")
        return len(errors) == 0, errors

    @property
    def footprint_width(self) -> float:
        return self.x_cells * self.cell_width

    @property
    def footprint_depth(self) -> float:
        return self.y_cells * self.cell_depth

    @property
    def footprint_area(self) -> float:
        return self.footprint_width * self.footprint_depth

    @property
    def cell_area(self) -> float:
        return self.cell_width * self.cell_depth


@dataclass(frozen=True)
class PanelPlacement:
    """One rectangular panel placed on a specific layer index."""

    rect: Rect2D
    layer_index: int

    def validate(self, grid: DiscreteGrid) -> tuple[bool, list[str]]:
        ok, errors = self.rect.validate()
        if self.layer_index < 0:
            errors.append("layer_index must be >= 0")
        if self.layer_index >= grid.layers_n:
            errors.append("layer_index must be < grid.layers_n")
        if self.rect.x1 > grid.x_cells:
            errors.append("rect.x1 must be <= grid.x_cells")
        if self.rect.y1 > grid.y_cells:
            errors.append("rect.y1 must be <= grid.y_cells")
        return ok and len(errors) == 0, errors

    def corners_world(self, grid: DiscreteGrid) -> list[Point3]:
        z = float(self.layer_index + 1) * grid.layer_height
        x0 = float(self.rect.x0) * grid.cell_width
        x1 = float(self.rect.x1) * grid.cell_width
        y0 = float(self.rect.y0) * grid.cell_depth
        y1 = float(self.rect.y1) * grid.cell_depth
        return [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]

    def to_exact_fit_spec(
        self,
        grid: DiscreteGrid,
        epsilon: float = 1e-6,
        support_points: list[Point3] | None = None,
        corner_rod_directions: list[Vector3] | None = None,
    ) -> ExactFitSpec:
        corners = self.corners_world(grid)
        return ExactFitSpec(
            board_corners=corners,
            support_points=support_points or corners,
            corner_rod_directions=corner_rod_directions or [(0.0, 0.0, 1.0)] * 4,
            epsilon=epsilon,
        )

    def occupied_cells(self) -> frozenset[Cell]:
        return frozenset(self.rect.iter_cells())


@dataclass(frozen=True)
class StructureTopology:
    """Topology type: panel partitions across all layers in discrete space."""

    panels: tuple[PanelPlacement, ...] = tuple()
    family: StructureFamily = StructureFamily.SHELF
    frame_cells: frozenset[Cell3D] = frozenset()
    frame_edges: tuple[GridEdge3D, ...] = tuple()
    metadata: dict[str, Any] = field(default_factory=dict)

    def module_combo(self) -> set[Module]:
        if self.family == StructureFamily.FRAME:
            return {Module.ROD, Module.CONNECTOR}
        if not self.panels:
            return {Module.CONNECTOR}
        return {Module.ROD, Module.CONNECTOR, Module.PANEL}

    def panel_count(self) -> int:
        return len(self.panels)

    def layer_indices(self) -> list[int]:
        if self.family == StructureFamily.FRAME:
            return sorted({cell[2] for cell in self.frame_cells})
        return sorted({panel.layer_index for panel in self.panels})

    def occupied_cells_by_layer(self) -> dict[int, frozenset[Cell]]:
        if self.family == StructureFamily.FRAME:
            frame_buckets: dict[int, set[Cell]] = {}
            for x, y, z in self.frame_cells:
                frame_buckets.setdefault(z, set()).add((x, y))
            return {layer: frozenset(cells) for layer, cells in frame_buckets.items()}

        panel_buckets: dict[int, set[Cell]] = {}
        for panel in self.panels:
            panel_buckets.setdefault(panel.layer_index, set()).update(panel.rect.iter_cells())
        return {layer: frozenset(cells) for layer, cells in panel_buckets.items()}

    def to_dict(self) -> dict[str, Any]:
        return {
            "family": self.family.value,
            "panels": [
                {
                    "layer_index": panel.layer_index,
                    "rect": panel.rect.to_tuple(),
                }
                for panel in self.panels
            ],
            "frame_cells": sorted(self.frame_cells),
            "frame_edges": [
                {
                    "start": edge[0],
                    "end": edge[1],
                }
                for edge in self.frame_edges
            ],
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class EnumerationConfig:
    """Configurable assumptions for discrete exhaustive enumeration."""

    grid: DiscreteGrid
    allow_empty_layer: bool = False
    mirror_equivalent: bool = True
    axis_permutation_equivalent: bool = True
    include_shelf_family: bool = True
    include_frame_family: bool = True
    frame_max_cells: int | None = None
    frame_forbid_dangling_rods: bool = False
    max_type_count: int | None = 20000


@dataclass(frozen=True)
class EnumerationStats:
    total_candidates: int
    structural_valid_candidates: int
    unique_types: int
    truncated: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CandidateEvaluation:
    canonical_key: str
    topology: StructureTopology
    structural_valid: bool
    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_key": self.canonical_key,
            "topology": self.topology.to_dict(),
            "structural_valid": self.structural_valid,
            "reasons": self.reasons,
        }


__all__ = [
    "Base",
    "BoundaryDefinition",
    "CandidateEvaluation",
    "Capability",
    "Cell",
    "Cell3D",
    "DiscreteGrid",
    "EnumerationConfig",
    "EnumerationStats",
    "ExactFitSpec",
    "Footprint2D",
    "Goal",
    "GridEdge3D",
    "GridPoint3D",
    "Hypothesis",
    "LogicRecord",
    "LogicStep",
    "Module",
    "Opening2D",
    "PanelPlacement",
    "Point3",
    "Rect2D",
    "Space3D",
    "StructureTopology",
    "StructureFamily",
    "Vector3",
    "VerificationInput",
    "VerificationResult",
]
