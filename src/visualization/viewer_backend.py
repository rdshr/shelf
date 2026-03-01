from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from domain.models import CandidateEvaluation, DiscreteGrid, EnumerationConfig
from enumeration import EnumerationResult, enumerate_structure_types

FilterMode = Literal["all", "valid", "invalid"]


@dataclass(frozen=True)
class ViewerBackendResult:
    grid: DiscreteGrid
    enumeration: EnumerationResult
    candidates: list[CandidateEvaluation]


def _filter_candidates(
    result: EnumerationResult,
    mode: FilterMode,
) -> list[CandidateEvaluation]:
    if mode == "valid":
        return result.valid_candidates()
    if mode == "invalid":
        return result.invalid_candidates()
    return result.unique_candidates


def enumerate_candidates_for_view(
    x_cells: int,
    y_cells: int,
    layers_n: int,
    cell_width: float,
    cell_depth: float,
    layer_height: float,
    allow_empty_layer: bool,
    filter_mode: FilterMode,
    max_type_count: int = 10000,
) -> ViewerBackendResult:
    grid = DiscreteGrid(
        x_cells=max(1, x_cells),
        y_cells=max(1, y_cells),
        layers_n=max(1, layers_n),
        cell_width=max(1e-6, cell_width),
        cell_depth=max(1e-6, cell_depth),
        layer_height=max(1e-6, layer_height),
    )
    result = enumerate_structure_types(
        EnumerationConfig(
            grid=grid,
            allow_empty_layer=allow_empty_layer,
            mirror_equivalent=True,
            axis_permutation_equivalent=True,
            max_type_count=max_type_count,
        )
    )
    return ViewerBackendResult(
        grid=grid,
        enumeration=result,
        candidates=_filter_candidates(result, filter_mode),
    )
