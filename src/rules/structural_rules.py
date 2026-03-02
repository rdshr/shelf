from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from domain.enums import StructureFamily
from domain.models import DiscreteGrid, GridEdge3D, GridPoint3D, StructureTopology
from geometry.builders import build_geometry
from geometry.frame import derive_boundary_skeleton_edges
from shelf_framework import StructuralPrinciples


@dataclass(frozen=True)
class StructuralCheck:
    name: str
    passed: bool
    reasons: list[str]

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "passed": self.passed, "reasons": self.reasons}


def _normalize_grid_edge(edge: GridEdge3D) -> GridEdge3D:
    if edge[0] <= edge[1]:
        return edge
    return (edge[1], edge[0])


def _frame_edges(topology: StructureTopology) -> tuple[GridEdge3D, ...]:
    if topology.frame_edges:
        return tuple(sorted(_normalize_grid_edge(edge) for edge in topology.frame_edges))
    return derive_boundary_skeleton_edges(topology.frame_cells)


def check_r3_rods_orthogonal(topology: StructureTopology, grid: DiscreteGrid) -> StructuralCheck:
    """R3: rods align to orthogonal axes and rod-rod angles are parallel/perpendicular."""
    geometry = build_geometry(topology, grid)
    rod_directions = [segment.direction() for segment in geometry.rods]
    angles = [0.0, 90.0] if len(rod_directions) >= 2 else [0.0]
    passed = StructuralPrinciples.rods_orthogonal_layout(rod_directions, angles)
    reasons: list[str] = [] if passed else ["R3 failed: rod directions or rod-rod angles invalid"]
    return StructuralCheck(name="R3", passed=passed, reasons=reasons)


def check_r4_board_parallel(topology: StructureTopology, grid: DiscreteGrid) -> StructuralCheck:
    """R4: all panels parallel, rod-to-board relation only parallel/perpendicular."""
    if topology.family == StructureFamily.FRAME:
        return StructuralCheck("R4", True, ["R4 not applicable for FRAME; treated as pass"])
    if not topology.panels:
        return StructuralCheck("R4", False, ["R4 failed: SHELF topology has no panel"])

    board_normals = [(0.0, 0.0, 1.0) for _ in topology.panels]
    geometry = build_geometry(topology, grid)
    rod_plane_angles = [90.0 for _ in geometry.rods]
    passed = StructuralPrinciples.boards_parallel_with_rod_constraints(
        board_normals,
        rod_plane_angles,
    )
    reasons: list[str] = [] if passed else ["R4 failed: panel parallelism or rod-panel angle invalid"]
    return StructuralCheck(name="R4", passed=passed, reasons=reasons)


def check_r5_exact_fit(topology: StructureTopology, grid: DiscreteGrid) -> StructuralCheck:
    """R5: each panel has four-corner exact-fit support."""
    if topology.family == StructureFamily.FRAME:
        return StructuralCheck("R5", True, ["R5 not applicable for FRAME; treated as pass"])

    reasons: list[str] = []
    all_passed = True
    for idx, panel in enumerate(topology.panels):
        panel_ok, panel_errors = panel.validate(grid)
        if not panel_ok:
            all_passed = False
            reasons.append(f"panel[{idx}] grid bounds failed: {panel_errors}")
            continue
        passed, errors = StructuralPrinciples.exact_fit(panel.to_exact_fit_spec(grid))
        if not passed:
            all_passed = False
            reasons.append(f"panel[{idx}] exact-fit failed: {errors}")
    if not topology.panels:
        all_passed = False
        reasons.append("R5 failed: SHELF topology has no panel")
    return StructuralCheck(name="R5", passed=all_passed, reasons=reasons)


def check_r6_projected_panel_gain(topology: StructureTopology, grid: DiscreteGrid) -> StructuralCheck:
    """R6: weighted projected panel coverage must be strictly greater than footprint cell count."""
    if topology.family == StructureFamily.FRAME:
        return StructuralCheck("R6", True, ["R6 not applicable for FRAME; treated as pass"])

    occupied_by_layer = topology.occupied_cells_by_layer()
    weighted_cells = sum(len(cells) for cells in occupied_by_layer.values())
    footprint_cells = grid.x_cells * grid.y_cells
    passed = weighted_cells > footprint_cells
    if passed:
        reasons: list[str] = []
    else:
        reasons = [
            (
                "R6 failed: weighted projected panel cells must be > footprint cells "
                f"(weighted={weighted_cells}, footprint={footprint_cells})"
            )
        ]
    return StructuralCheck(name="R6", passed=passed, reasons=reasons)


def check_frame_connected(topology: StructureTopology, _grid: DiscreteGrid) -> StructuralCheck:
    if topology.family != StructureFamily.FRAME:
        return StructuralCheck("FRAME.connected", True, ["not a FRAME topology"])

    edges = _frame_edges(topology)
    if not edges:
        return StructuralCheck("FRAME.connected", False, ["FRAME has no rods"])

    adjacency: dict[GridPoint3D, set[GridPoint3D]] = {}
    for start, end in edges:
        adjacency.setdefault(start, set()).add(end)
        adjacency.setdefault(end, set()).add(start)

    start = next(iter(adjacency))
    visited: set[GridPoint3D] = set()
    queue: deque[GridPoint3D] = deque([start])
    while queue:
        point = queue.popleft()
        if point in visited:
            continue
        visited.add(point)
        for nxt in adjacency.get(point, set()):
            if nxt not in visited:
                queue.append(nxt)

    passed = len(visited) == len(adjacency)
    reasons = [] if passed else ["FRAME.connected failed: rod graph is disconnected"]
    return StructuralCheck("FRAME.connected", passed, reasons)


def check_frame_ground_contact(topology: StructureTopology, _grid: DiscreteGrid) -> StructuralCheck:
    if topology.family != StructureFamily.FRAME:
        return StructuralCheck("FRAME.ground_contact", True, ["not a FRAME topology"])

    edges = _frame_edges(topology)
    touches_ground = any(start[2] == 0 or end[2] == 0 for start, end in edges)
    reasons = [] if touches_ground else ["FRAME.ground_contact failed: no rod touches z=0 ground plane"]
    return StructuralCheck("FRAME.ground_contact", touches_ground, reasons)


def check_frame_minimal_under_deletability(
    topology: StructureTopology,
    _grid: DiscreteGrid,
) -> StructuralCheck:
    if topology.family != StructureFamily.FRAME:
        return StructuralCheck("FRAME.minimal_under_deletability", True, ["not a FRAME topology"])
    if not topology.frame_cells:
        return StructuralCheck(
            "FRAME.minimal_under_deletability",
            False,
            ["FRAME.minimal_under_deletability failed: frame_cells is empty"],
        )

    expected = set(derive_boundary_skeleton_edges(topology.frame_cells))
    actual = set(_frame_edges(topology))
    passed = actual == expected and len(actual) > 0
    reasons = [] if passed else ["FRAME.minimal_under_deletability failed: edges are not exact boundary skeleton"]
    return StructuralCheck("FRAME.minimal_under_deletability", passed, reasons)


def check_frame_forbid_dangling_rods(
    topology: StructureTopology,
    _grid: DiscreteGrid,
    enabled: bool,
) -> StructuralCheck:
    if topology.family != StructureFamily.FRAME:
        return StructuralCheck("FRAME.forbid_dangling_rods", True, ["not a FRAME topology"])
    if not enabled:
        return StructuralCheck("FRAME.forbid_dangling_rods", True, ["optional rule disabled"])

    edges = _frame_edges(topology)
    degree: dict[GridPoint3D, int] = {}
    for start, end in edges:
        degree[start] = degree.get(start, 0) + 1
        degree[end] = degree.get(end, 0) + 1

    dangling = [point for point, d in degree.items() if d == 1]
    passed = len(dangling) == 0
    reasons = [] if passed else [f"FRAME.forbid_dangling_rods failed: dangling endpoints={dangling[:6]}"]
    return StructuralCheck("FRAME.forbid_dangling_rods", passed, reasons)


def evaluate_structural_rules(
    topology: StructureTopology,
    grid: DiscreteGrid,
    forbid_dangling_rods: bool = False,
) -> list[StructuralCheck]:
    checks = [
        check_r3_rods_orthogonal(topology, grid),
        check_r4_board_parallel(topology, grid),
        check_r5_exact_fit(topology, grid),
        check_r6_projected_panel_gain(topology, grid),
    ]
    if topology.family == StructureFamily.FRAME:
        checks.extend(
            [
                check_frame_connected(topology, grid),
                check_frame_ground_contact(topology, grid),
                check_frame_minimal_under_deletability(topology, grid),
                check_frame_forbid_dangling_rods(topology, grid, enabled=forbid_dangling_rods),
            ]
        )
    return checks
