from __future__ import annotations

from functools import lru_cache
from itertools import product

from domain.models import Cell, DiscreteGrid, Rect2D


def all_cells(grid: DiscreteGrid) -> tuple[Cell, ...]:
    return tuple((x, y) for x in range(grid.x_cells) for y in range(grid.y_cells))


def all_non_empty_occupancies(grid: DiscreteGrid) -> list[frozenset[Cell]]:
    """Enumerate all non-empty occupancy patterns on finite grid cells."""
    cells = all_cells(grid)
    out: list[frozenset[Cell]] = []
    for bitmask in range(1, 1 << len(cells)):
        picked: set[Cell] = set()
        for idx, cell in enumerate(cells):
            if bitmask & (1 << idx):
                picked.add(cell)
        out.append(frozenset(picked))
    return out


def _rect_cells(rect: Rect2D) -> frozenset[Cell]:
    return frozenset(rect.iter_cells())


def candidate_rectangles(occupancy: frozenset[Cell], grid: DiscreteGrid) -> list[Rect2D]:
    rects: list[Rect2D] = []
    occ = set(occupancy)
    for x0 in range(grid.x_cells):
        for x1 in range(x0 + 1, grid.x_cells + 1):
            for y0 in range(grid.y_cells):
                for y1 in range(y0 + 1, grid.y_cells + 1):
                    rect = Rect2D(x0=x0, x1=x1, y0=y0, y1=y1)
                    cells = _rect_cells(rect)
                    if cells and cells.issubset(occ):
                        rects.append(rect)
    rects.sort(key=lambda item: (item.area_cells(), item.x0, item.y0, item.x1, item.y1), reverse=True)
    return rects


def partition_into_rectangles(
    occupancy: frozenset[Cell],
    grid: DiscreteGrid,
) -> list[tuple[Rect2D, ...]]:
    """Exact-cover partitions of occupancy into axis-aligned rectangles."""
    if not occupancy:
        return [tuple()]

    all_rects = candidate_rectangles(occupancy, grid)

    @lru_cache(maxsize=None)
    def _solve(remaining: frozenset[Cell]) -> tuple[tuple[Rect2D, ...], ...]:
        if not remaining:
            return (tuple(),)

        anchor = min(remaining)
        valid_rects = []
        for rect in all_rects:
            cells = _rect_cells(rect)
            if anchor in cells and cells.issubset(remaining):
                valid_rects.append((rect, cells))

        out: list[tuple[Rect2D, ...]] = []
        for rect, cells in valid_rects:
            next_remaining = frozenset(set(remaining) - set(cells))
            for tail in _solve(next_remaining):
                out.append((rect,) + tail)

        normalized: set[tuple[tuple[int, int, int, int], ...]] = set()
        deduped: list[tuple[Rect2D, ...]] = []
        for part in out:
            sorted_part = tuple(sorted(part, key=lambda item: item.to_tuple()))
            key = tuple(item.to_tuple() for item in sorted_part)
            if key in normalized:
                continue
            normalized.add(key)
            deduped.append(sorted_part)
        return tuple(deduped)

    return list(_solve(occupancy))


def occupancy_signature(occupancy: frozenset[Cell]) -> str:
    if not occupancy:
        return "empty"
    return ";".join(f"{x},{y}" for x, y in sorted(occupancy))
