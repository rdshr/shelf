from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass

from domain.enums import StructureFamily
from domain.models import BoundaryDefinition, DiscreteGrid, StructureTopology


@dataclass(frozen=True)
class LayerUtilizationTerm:
    layer_index: int
    usable_area: float
    clear_height: float
    access_factor: float
    contribution: float


@dataclass(frozen=True)
class FrameBayUtilizationTerm:
    bay_index: int
    bay_cell: tuple[int, int, int]
    bay_volume: float
    access_factor: float
    contribution: float


@dataclass(frozen=True)
class UtilizationResult:
    family: str
    target_utilization: float
    baseline_utilization: float
    improved: bool
    terms: Sequence[LayerUtilizationTerm | FrameBayUtilizationTerm]

    @property
    def target_efficiency(self) -> float:
        return self.target_utilization

    @property
    def baseline_efficiency(self) -> float:
        return self.baseline_utilization

    def to_dict(self) -> dict[str, object]:
        return {
            "metric_name": "space_utilization",
            "family": self.family,
            "target_utilization": self.target_utilization,
            "baseline_utilization": self.baseline_utilization,
            "target_efficiency": self.target_utilization,
            "baseline_efficiency": self.baseline_utilization,
            "improved": self.improved,
            "terms": [asdict(item) for item in self.terms],
        }


def _access_factor(boundary: BoundaryDefinition) -> float:
    width_ratio = min(1.0, boundary.opening_o.width / boundary.space_s_per_layer.width)
    height_ratio = min(1.0, boundary.opening_o.height / boundary.space_s_per_layer.height)
    return max(0.0, min(1.0, 0.5 * (width_ratio + height_ratio)))


def _bounding_volume(boundary: BoundaryDefinition, grid: DiscreteGrid) -> float:
    total_height = float(grid.layers_n) * grid.layer_height
    return boundary.footprint_a.width * boundary.footprint_a.depth * total_height


def calculate_shelf_utilization(
    topology: StructureTopology,
    boundary: BoundaryDefinition,
    grid: DiscreteGrid,
    baseline_utilization: float,
) -> UtilizationResult:
    """u_shelf(S) = 1/V_total * sum_k(A_usable_k * h_clear_k * alpha_access_k)."""
    bounding_volume = _bounding_volume(boundary, grid)
    if bounding_volume <= 0:
        return UtilizationResult(
            family=StructureFamily.SHELF.value,
            target_utilization=0.0,
            baseline_utilization=baseline_utilization,
            improved=False,
            terms=[],
        )

    occupied_by_layer = topology.occupied_cells_by_layer()
    access_factor = _access_factor(boundary)
    clear_height = boundary.space_s_per_layer.height

    terms: list[LayerUtilizationTerm] = []
    numerator = 0.0
    for layer in range(grid.layers_n):
        cells = occupied_by_layer.get(layer, frozenset())
        usable_area = float(len(cells)) * grid.cell_area
        contribution = usable_area * clear_height * access_factor
        numerator += contribution
        terms.append(
            LayerUtilizationTerm(
                layer_index=layer,
                usable_area=usable_area,
                clear_height=clear_height,
                access_factor=access_factor,
                contribution=contribution,
            )
        )

    target_utilization = numerator / bounding_volume
    return UtilizationResult(
        family=StructureFamily.SHELF.value,
        target_utilization=target_utilization,
        baseline_utilization=baseline_utilization,
        improved=target_utilization > baseline_utilization,
        terms=terms,
    )


def calculate_frame_utilization(
    topology: StructureTopology,
    boundary: BoundaryDefinition,
    grid: DiscreteGrid,
    baseline_utilization: float,
) -> UtilizationResult:
    """
    u_frame = (1/V_total) * sum(volume(bay) * access_coeff(bay)).
    V1 uses each connected-cell bay directly as one bay term.
    """
    bounding_volume = _bounding_volume(boundary, grid)
    if bounding_volume <= 0:
        return UtilizationResult(
            family=StructureFamily.FRAME.value,
            target_utilization=0.0,
            baseline_utilization=baseline_utilization,
            improved=False,
            terms=[],
        )

    if not topology.frame_cells:
        return UtilizationResult(
            family=StructureFamily.FRAME.value,
            target_utilization=0.0,
            baseline_utilization=baseline_utilization,
            improved=False,
            terms=[],
        )

    access_factor = _access_factor(boundary)
    bay_volume = grid.cell_width * grid.cell_depth * grid.layer_height
    terms: list[FrameBayUtilizationTerm] = []
    numerator = 0.0
    for idx, cell in enumerate(sorted(topology.frame_cells)):
        contribution = bay_volume * access_factor
        numerator += contribution
        terms.append(
            FrameBayUtilizationTerm(
                bay_index=idx,
                bay_cell=cell,
                bay_volume=bay_volume,
                access_factor=access_factor,
                contribution=contribution,
            )
        )

    target_utilization = numerator / bounding_volume
    return UtilizationResult(
        family=StructureFamily.FRAME.value,
        target_utilization=target_utilization,
        baseline_utilization=baseline_utilization,
        improved=target_utilization > baseline_utilization,
        terms=terms,
    )


def calculate_utilization(
    topology: StructureTopology,
    boundary: BoundaryDefinition,
    grid: DiscreteGrid,
    baseline_utilization: float,
) -> UtilizationResult:
    if topology.family == StructureFamily.FRAME:
        return calculate_frame_utilization(topology, boundary, grid, baseline_utilization)
    return calculate_shelf_utilization(topology, boundary, grid, baseline_utilization)


# Backward-compatible aliases kept while callers migrate to utilization terminology.
LayerEfficiencyTerm = LayerUtilizationTerm
FrameBayEfficiencyTerm = FrameBayUtilizationTerm
EfficiencyResult = UtilizationResult


def calculate_shelf_efficiency(
    topology: StructureTopology,
    boundary: BoundaryDefinition,
    grid: DiscreteGrid,
    baseline_efficiency: float,
) -> UtilizationResult:
    return calculate_shelf_utilization(topology, boundary, grid, baseline_efficiency)


def calculate_frame_efficiency(
    topology: StructureTopology,
    boundary: BoundaryDefinition,
    grid: DiscreteGrid,
    baseline_efficiency: float,
) -> UtilizationResult:
    return calculate_frame_utilization(topology, boundary, grid, baseline_efficiency)


def calculate_efficiency(
    topology: StructureTopology,
    boundary: BoundaryDefinition,
    grid: DiscreteGrid,
    baseline_efficiency: float,
) -> UtilizationResult:
    return calculate_utilization(topology, boundary, grid, baseline_efficiency)
