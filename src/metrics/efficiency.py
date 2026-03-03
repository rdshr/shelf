from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass

from domain.enums import StructureFamily
from domain.models import BoundaryDefinition, DiscreteGrid, StructureTopology


@dataclass(frozen=True)
class LayerEfficiencyTerm:
    layer_index: int
    usable_area: float
    clear_height: float
    access_factor: float
    contribution: float


@dataclass(frozen=True)
class FrameBayEfficiencyTerm:
    bay_index: int
    bay_cell: tuple[int, int, int]
    bay_volume: float
    access_factor: float
    contribution: float


@dataclass(frozen=True)
class EfficiencyResult:
    family: str
    target_efficiency: float
    baseline_efficiency: float
    improved: bool
    terms: Sequence[LayerEfficiencyTerm | FrameBayEfficiencyTerm]

    def to_dict(self) -> dict[str, object]:
        return {
            "family": self.family,
            "target_efficiency": self.target_efficiency,
            "baseline_efficiency": self.baseline_efficiency,
            "improved": self.improved,
            "terms": [asdict(item) for item in self.terms],
        }


def _access_factor(boundary: BoundaryDefinition) -> float:
    width_ratio = min(1.0, boundary.opening_o.width / boundary.space_s_per_layer.width)
    height_ratio = min(1.0, boundary.opening_o.height / boundary.space_s_per_layer.height)
    return max(0.0, min(1.0, 0.5 * (width_ratio + height_ratio)))


def calculate_shelf_efficiency(
    topology: StructureTopology,
    boundary: BoundaryDefinition,
    grid: DiscreteGrid,
    baseline_efficiency: float,
) -> EfficiencyResult:
    """eta_shelf(S) = 1/A * sum_k(A_usable_k * h_clear_k * alpha_access_k)."""
    footprint_area = boundary.footprint_a.width * boundary.footprint_a.depth
    if footprint_area <= 0:
        return EfficiencyResult(
            family=StructureFamily.SHELF.value,
            target_efficiency=0.0,
            baseline_efficiency=baseline_efficiency,
            improved=False,
            terms=[],
        )

    occupied_by_layer = topology.occupied_cells_by_layer()
    access_factor = _access_factor(boundary)
    clear_height = boundary.space_s_per_layer.height

    terms: list[LayerEfficiencyTerm] = []
    numerator = 0.0
    for layer in range(grid.layers_n):
        cells = occupied_by_layer.get(layer, frozenset())
        usable_area = float(len(cells)) * grid.cell_area
        contribution = usable_area * clear_height * access_factor
        numerator += contribution
        terms.append(
            LayerEfficiencyTerm(
                layer_index=layer,
                usable_area=usable_area,
                clear_height=clear_height,
                access_factor=access_factor,
                contribution=contribution,
            )
        )

    target = numerator / footprint_area
    return EfficiencyResult(
        family=StructureFamily.SHELF.value,
        target_efficiency=target,
        baseline_efficiency=baseline_efficiency,
        improved=target > baseline_efficiency,
        terms=terms,
    )


def calculate_frame_efficiency(
    topology: StructureTopology,
    boundary: BoundaryDefinition,
    grid: DiscreteGrid,
    baseline_efficiency: float,
) -> EfficiencyResult:
    """
    eta_frame = (1/A) * sum(volume(bay) * access_coeff(bay)).
    V1 uses each connected-cell bay directly as one bay term.
    """
    footprint_area = boundary.footprint_a.width * boundary.footprint_a.depth
    if footprint_area <= 0:
        return EfficiencyResult(
            family=StructureFamily.FRAME.value,
            target_efficiency=0.0,
            baseline_efficiency=baseline_efficiency,
            improved=False,
            terms=[],
        )

    if not topology.frame_cells:
        return EfficiencyResult(
            family=StructureFamily.FRAME.value,
            target_efficiency=0.0,
            baseline_efficiency=baseline_efficiency,
            improved=False,
            terms=[],
        )

    access_factor = _access_factor(boundary)
    bay_volume = grid.cell_width * grid.cell_depth * grid.layer_height
    terms: list[FrameBayEfficiencyTerm] = []
    numerator = 0.0
    for idx, cell in enumerate(sorted(topology.frame_cells)):
        contribution = bay_volume * access_factor
        numerator += contribution
        terms.append(
            FrameBayEfficiencyTerm(
                bay_index=idx,
                bay_cell=cell,
                bay_volume=bay_volume,
                access_factor=access_factor,
                contribution=contribution,
            )
        )

    target = numerator / footprint_area
    return EfficiencyResult(
        family=StructureFamily.FRAME.value,
        target_efficiency=target,
        baseline_efficiency=baseline_efficiency,
        improved=target > baseline_efficiency,
        terms=terms,
    )


def calculate_efficiency(
    topology: StructureTopology,
    boundary: BoundaryDefinition,
    grid: DiscreteGrid,
    baseline_efficiency: float,
) -> EfficiencyResult:
    if topology.family == StructureFamily.FRAME:
        return calculate_frame_efficiency(topology, boundary, grid, baseline_efficiency)
    return calculate_shelf_efficiency(topology, boundary, grid, baseline_efficiency)
