from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from domain.models import CandidateEvaluation, DiscreteGrid


@dataclass(frozen=True)
class TypeGroup:
    family: str
    counts_per_layer: tuple[int, ...]
    items: list[tuple[int, CandidateEvaluation]]

    @property
    def active_layers(self) -> int:
        return sum(1 for item in self.counts_per_layer if item > 0)

    @property
    def total_cells(self) -> int:
        return sum(self.counts_per_layer)

    def title(self, idx: int) -> str:
        counts_str = ",".join(str(x) for x in self.counts_per_layer)
        return (
            f"G{idx:02d} family={self.family} cells/layer=({counts_str}) "
            f"active={self.active_layers} count={len(self.items)}"
        )


def layer_cell_counts(candidate: CandidateEvaluation, layers_n: int) -> tuple[int, ...]:
    occupied = candidate.topology.occupied_cells_by_layer()
    return tuple(len(occupied.get(layer, frozenset())) for layer in range(layers_n))


def build_type_groups(candidates: list[CandidateEvaluation], grid: DiscreteGrid) -> list[TypeGroup]:
    buckets: dict[tuple[str, tuple[int, ...]], list[tuple[int, CandidateEvaluation]]] = defaultdict(list)
    for idx, candidate in enumerate(candidates):
        key = (candidate.topology.family.value, layer_cell_counts(candidate, grid.layers_n))
        buckets[key].append((idx, candidate))

    groups = [
        TypeGroup(
            family=family,
            counts_per_layer=counts,
            items=items,
        )
        for (family, counts), items in buckets.items()
    ]
    groups.sort(
        key=lambda group: (
            group.family != "shelf",
            -group.active_layers,
            -group.total_cells,
            group.counts_per_layer,
        )
    )
    return groups
