from __future__ import annotations

from dataclasses import dataclass
from itertools import product

from domain.enums import StructureFamily
from domain.models import (
    CandidateEvaluation,
    DiscreteGrid,
    EnumerationConfig,
    EnumerationStats,
    PanelPlacement,
    StructureTopology,
)
from enumeration.canonical import canonical_key
from geometry.frame import derive_boundary_skeleton_edges, enumerate_connected_non_empty_cell_subsets
from geometry.grid import all_non_empty_occupancies, occupancy_signature, partition_into_rectangles
from rules.structural_rules import evaluate_structural_rules


@dataclass(frozen=True)
class EnumerationResult:
    stats: EnumerationStats
    unique_candidates: list[CandidateEvaluation]
    raw_candidate_count: int
    shelf_raw_candidate_count: int
    frame_raw_candidate_count: int
    layer_pattern_count: int
    occupancy_partition_count: dict[str, int]
    allow_empty_layer: bool
    family_counts: dict[str, dict[str, int]]

    def valid_candidates(self, family: StructureFamily | None = None) -> list[CandidateEvaluation]:
        selected = [item for item in self.unique_candidates if item.structural_valid]
        if family is None:
            return selected
        return [item for item in selected if item.topology.family == family]

    def invalid_candidates(self, family: StructureFamily | None = None) -> list[CandidateEvaluation]:
        selected = [item for item in self.unique_candidates if not item.structural_valid]
        if family is None:
            return selected
        return [item for item in selected if item.topology.family == family]


def _layer_realizations(grid: DiscreteGrid, allow_empty_layer: bool) -> tuple[
    list[tuple[PanelPlacement, ...]],
    dict[str, int],
]:
    occupancy_partition_count: dict[str, int] = {}
    out: list[tuple[PanelPlacement, ...]] = []

    if allow_empty_layer:
        out.append(tuple())

    for occupancy in all_non_empty_occupancies(grid):
        partitions = partition_into_rectangles(occupancy, grid)
        key = occupancy_signature(occupancy)
        occupancy_partition_count[key] = len(partitions)
        for partition in partitions:
            out.append(tuple(PanelPlacement(rect=rect, layer_index=0) for rect in partition))

    return out, occupancy_partition_count


def _instantiate_shelf_layers(
    template_layers: tuple[tuple[PanelPlacement, ...], ...],
) -> StructureTopology:
    panels: list[PanelPlacement] = []
    for layer_idx, panels_on_layer in enumerate(template_layers):
        for panel in panels_on_layer:
            panels.append(PanelPlacement(rect=panel.rect, layer_index=layer_idx))
    panels.sort(key=lambda item: (item.layer_index, item.rect.x0, item.rect.y0, item.rect.x1, item.rect.y1))
    return StructureTopology(
        family=StructureFamily.SHELF,
        panels=tuple(panels),
        frame_cells=frozenset(),
        frame_edges=tuple(),
    )


def _evaluate_candidate(
    topology: StructureTopology,
    config: EnumerationConfig,
) -> tuple[bool, list[str]]:
    checks = evaluate_structural_rules(
        topology,
        config.grid,
        forbid_dangling_rods=config.frame_forbid_dangling_rods,
    )
    reasons = [reason for check in checks for reason in check.reasons]
    return all(check.passed for check in checks), reasons


def enumerate_structure_types(config: EnumerationConfig) -> EnumerationResult:
    grid = config.grid
    ok, errors = grid.validate()
    if not ok:
        raise ValueError(f"invalid grid: {errors}")
    if not config.include_shelf_family and not config.include_frame_family:
        raise ValueError("at least one family must be enabled")

    unique: dict[str, CandidateEvaluation] = {}
    occupancy_partition_count: dict[str, int] = {}
    layer_pattern_count = 0

    raw_candidate_count = 0
    shelf_raw_candidate_count = 0
    frame_raw_candidate_count = 0
    structural_valid_count = 0
    truncated = False

    raw_by_family: dict[StructureFamily, int] = {
        StructureFamily.FRAME: 0,
        StructureFamily.SHELF: 0,
    }
    raw_valid_by_family: dict[StructureFamily, int] = {
        StructureFamily.FRAME: 0,
        StructureFamily.SHELF: 0,
    }

    if config.include_shelf_family:
        layer_templates, occupancy_partition_count = _layer_realizations(grid, config.allow_empty_layer)
        layer_pattern_count = len(layer_templates)
        for template_layers in product(layer_templates, repeat=grid.layers_n):
            topology = _instantiate_shelf_layers(template_layers)
            is_valid, reasons = _evaluate_candidate(topology, config)

            raw_candidate_count += 1
            shelf_raw_candidate_count += 1
            raw_by_family[StructureFamily.SHELF] += 1
            if is_valid:
                structural_valid_count += 1
                raw_valid_by_family[StructureFamily.SHELF] += 1

            key = canonical_key(
                topology,
                mirror_equivalent=config.mirror_equivalent,
                axis_permutation_equivalent=config.axis_permutation_equivalent,
            )
            if key not in unique:
                unique[key] = CandidateEvaluation(
                    canonical_key=key,
                    topology=topology,
                    structural_valid=is_valid,
                    reasons=reasons,
                )

            if config.max_type_count is not None and len(unique) >= config.max_type_count:
                truncated = True
                break

    if not truncated and config.include_frame_family:
        cell_subsets = enumerate_connected_non_empty_cell_subsets(
            grid,
            max_cells=config.frame_max_cells,
        )
        for subset in cell_subsets:
            edges = derive_boundary_skeleton_edges(subset)
            topology = StructureTopology(
                family=StructureFamily.FRAME,
                panels=tuple(),
                frame_cells=subset,
                frame_edges=edges,
                metadata={"generator": "frame_boundary_induction_v1"},
            )
            is_valid, reasons = _evaluate_candidate(topology, config)

            raw_candidate_count += 1
            frame_raw_candidate_count += 1
            raw_by_family[StructureFamily.FRAME] += 1
            if is_valid:
                structural_valid_count += 1
                raw_valid_by_family[StructureFamily.FRAME] += 1

            key = canonical_key(
                topology,
                mirror_equivalent=config.mirror_equivalent,
                axis_permutation_equivalent=config.axis_permutation_equivalent,
            )
            if key not in unique:
                unique[key] = CandidateEvaluation(
                    canonical_key=key,
                    topology=topology,
                    structural_valid=is_valid,
                    reasons=reasons,
                )

            if config.max_type_count is not None and len(unique) >= config.max_type_count:
                truncated = True
                break

    unique_list = list(unique.values())
    family_counts: dict[str, dict[str, int]] = {}
    for family in (StructureFamily.FRAME, StructureFamily.SHELF):
        family_unique = [item for item in unique_list if item.topology.family == family]
        family_valid = [item for item in family_unique if item.structural_valid]
        family_counts[family.value] = {
            "raw_candidates": raw_by_family[family],
            "raw_valid_candidates": raw_valid_by_family[family],
            "unique_types": len(family_unique),
            "valid_types": len(family_valid),
            "invalid_types": len(family_unique) - len(family_valid),
        }

    stats = EnumerationStats(
        total_candidates=raw_candidate_count,
        structural_valid_candidates=structural_valid_count,
        unique_types=len(unique_list),
        truncated=truncated,
    )
    return EnumerationResult(
        stats=stats,
        unique_candidates=unique_list,
        raw_candidate_count=raw_candidate_count,
        shelf_raw_candidate_count=shelf_raw_candidate_count,
        frame_raw_candidate_count=frame_raw_candidate_count,
        layer_pattern_count=layer_pattern_count,
        occupancy_partition_count=occupancy_partition_count,
        allow_empty_layer=config.allow_empty_layer,
        family_counts=family_counts,
    )


def counting_framework_summary(
    result: EnumerationResult,
    grid: DiscreteGrid,
) -> dict[str, object]:
    """Dual-family counting summary with explicit shelf/frame decomposition."""
    per_layer_term_count = sum(result.occupancy_partition_count.values())
    empty_layer_terms = 1 if result.allow_empty_layer else 0
    per_layer_total = per_layer_term_count + empty_layer_terms

    shelf_formula_count = 0
    if result.shelf_raw_candidate_count > 0:
        shelf_formula_count = per_layer_total**grid.layers_n

    frame_formula_count = result.frame_raw_candidate_count
    all_formula_count = shelf_formula_count + frame_formula_count

    return {
        "counting_mode": "dual_family",
        "omega_formula": "Omega = Omega_frame ⊔ Omega_shelf",
        "layers_n": grid.layers_n,
        "grid_cells_2d": grid.x_cells * grid.y_cells,
        "grid_cells_3d": grid.x_cells * grid.y_cells * grid.layers_n,
        "shelf": {
            "counting_formula": "C_raw^shelf = (T_layer)^N",
            "occupancy_patterns_non_empty": len(result.occupancy_partition_count),
            "partition_terms_per_layer": per_layer_term_count,
            "empty_layer_terms": empty_layer_terms,
            "terms_per_layer_total": per_layer_total,
            "formula_instantiated": shelf_formula_count,
            "raw_candidate_count": result.shelf_raw_candidate_count,
        },
        "frame": {
            "counting_formula": (
                "C_raw^frame = |{U subseteq C | U != empty and connected_6(U)}| "
                "(V1 cavity-induced boundary skeleton)"
            ),
            "formula_instantiated": frame_formula_count,
            "raw_candidate_count": result.frame_raw_candidate_count,
        },
        "all": {
            "counting_formula": "C_raw^all = C_raw^frame + C_raw^shelf",
            "formula_instantiated": all_formula_count,
            "raw_candidate_count": result.raw_candidate_count,
        },
        # Backward-compatible key used by prior tests/docs.
        "formula_instantiated": all_formula_count,
        "family_counts": result.family_counts,
    }
