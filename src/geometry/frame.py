from __future__ import annotations

from collections import deque

from domain.models import Cell3D, DiscreteGrid, GridEdge3D, GridPoint3D


def all_cells_3d(grid: DiscreteGrid) -> tuple[Cell3D, ...]:
    return tuple(
        (x, y, z)
        for x in range(grid.x_cells)
        for y in range(grid.y_cells)
        for z in range(grid.layers_n)
    )


def six_neighbors(cell: Cell3D) -> tuple[Cell3D, ...]:
    x, y, z = cell
    return (
        (x - 1, y, z),
        (x + 1, y, z),
        (x, y - 1, z),
        (x, y + 1, z),
        (x, y, z - 1),
        (x, y, z + 1),
    )


def is_connected_6(cells: frozenset[Cell3D]) -> bool:
    if not cells:
        return False
    visited: set[Cell3D] = set()
    queue: deque[Cell3D] = deque([next(iter(cells))])
    while queue:
        current = queue.popleft()
        if current in visited:
            continue
        visited.add(current)
        for neighbor in six_neighbors(current):
            if neighbor in cells and neighbor not in visited:
                queue.append(neighbor)
    return len(visited) == len(cells)


def enumerate_connected_non_empty_cell_subsets(
    grid: DiscreteGrid,
    max_cells: int | None = None,
) -> list[frozenset[Cell3D]]:
    """Brute-force connected subsets on bounded voxel grid (V1 baseline)."""
    cells = all_cells_3d(grid)
    out: list[frozenset[Cell3D]] = []
    for bitmask in range(1, 1 << len(cells)):
        picked: set[Cell3D] = set()
        for idx, cell in enumerate(cells):
            if bitmask & (1 << idx):
                picked.add(cell)
                if max_cells is not None and len(picked) > max_cells:
                    break
        if max_cells is not None and len(picked) > max_cells:
            continue
        frozen = frozenset(picked)
        if is_connected_6(frozen):
            out.append(frozen)
    return out


def _normalize_edge(start: GridPoint3D, end: GridPoint3D) -> GridEdge3D:
    if start <= end:
        return (start, end)
    return (end, start)


def _boundary_face_edges(cell: Cell3D, direction: Cell3D) -> tuple[GridEdge3D, ...]:
    x, y, z = cell
    dx, dy, dz = direction

    if dx == -1:
        p = [(x, y, z), (x, y + 1, z), (x, y + 1, z + 1), (x, y, z + 1)]
    elif dx == 1:
        p = [(x + 1, y, z), (x + 1, y + 1, z), (x + 1, y + 1, z + 1), (x + 1, y, z + 1)]
    elif dy == -1:
        p = [(x, y, z), (x + 1, y, z), (x + 1, y, z + 1), (x, y, z + 1)]
    elif dy == 1:
        p = [(x, y + 1, z), (x + 1, y + 1, z), (x + 1, y + 1, z + 1), (x, y + 1, z + 1)]
    elif dz == -1:
        p = [(x, y, z), (x + 1, y, z), (x + 1, y + 1, z), (x, y + 1, z)]
    elif dz == 1:
        p = [(x, y, z + 1), (x + 1, y, z + 1), (x + 1, y + 1, z + 1), (x, y + 1, z + 1)]
    else:
        raise ValueError(f"unsupported boundary direction: {direction}")

    return (
        _normalize_edge(p[0], p[1]),
        _normalize_edge(p[1], p[2]),
        _normalize_edge(p[2], p[3]),
        _normalize_edge(p[3], p[0]),
    )


def derive_boundary_skeleton_edges(cells: frozenset[Cell3D]) -> tuple[GridEdge3D, ...]:
    if not cells:
        return tuple()
    directions: tuple[Cell3D, ...] = (
        (-1, 0, 0),
        (1, 0, 0),
        (0, -1, 0),
        (0, 1, 0),
        (0, 0, -1),
        (0, 0, 1),
    )
    edges: set[GridEdge3D] = set()
    for cell in cells:
        for direction in directions:
            neighbor = (cell[0] + direction[0], cell[1] + direction[1], cell[2] + direction[2])
            if neighbor in cells:
                continue
            edges.update(_boundary_face_edges(cell, direction))
    return tuple(sorted(edges))


def derive_boundary_connectors(edges: tuple[GridEdge3D, ...]) -> tuple[GridPoint3D, ...]:
    points: set[GridPoint3D] = set()
    for start, end in edges:
        points.add(start)
        points.add(end)
    return tuple(sorted(points))


__all__ = [
    "all_cells_3d",
    "derive_boundary_connectors",
    "derive_boundary_skeleton_edges",
    "enumerate_connected_non_empty_cell_subsets",
    "is_connected_6",
    "six_neighbors",
]
