from __future__ import annotations

import unittest

from domain import DiscreteGrid, PanelPlacement, Rect2D, StructureTopology
from rules.structural_rules import check_r3_rods_orthogonal, check_r4_board_parallel, check_r5_exact_fit
from shelf_framework import StructuralPrinciples


class StructuralRulesTest(unittest.TestCase):
    def test_r3_rejects_slanted_rod(self) -> None:
        passed = StructuralPrinciples.rods_orthogonal_layout(
            rod_directions=[(1.0, 1.0, 0.0)],
            rod_connection_angles_deg=[0.0],
        )
        self.assertFalse(passed)

    def test_r3_rejects_slanted_connection_angle(self) -> None:
        passed = StructuralPrinciples.rods_orthogonal_layout(
            rod_directions=[(0.0, 0.0, 1.0), (0.0, 1.0, 0.0)],
            rod_connection_angles_deg=[45.0],
        )
        self.assertFalse(passed)

    def test_r4_rejects_non_parallel_boards(self) -> None:
        passed = StructuralPrinciples.boards_parallel_with_rod_constraints(
            board_normals=[(0.0, 0.0, 1.0), (0.0, 1.0, 0.0)],
            rod_to_board_plane_angles_deg=[90.0],
        )
        self.assertFalse(passed)

    def test_r4_rejects_slanted_rod_to_board_angle(self) -> None:
        passed = StructuralPrinciples.boards_parallel_with_rod_constraints(
            board_normals=[(0.0, 0.0, 1.0), (0.0, 0.0, 1.0)],
            rod_to_board_plane_angles_deg=[30.0],
        )
        self.assertFalse(passed)

    def test_geometry_backed_r3_r4_r5_pass_for_two_level_shelf(self) -> None:
        grid = DiscreteGrid(x_cells=1, y_cells=1, layers_n=2, cell_width=10.0, cell_depth=10.0)
        topology = StructureTopology(
            panels=(
                PanelPlacement(rect=Rect2D(0, 1, 0, 1), layer_index=0),
                PanelPlacement(rect=Rect2D(0, 1, 0, 1), layer_index=1),
            )
        )

        self.assertTrue(check_r3_rods_orthogonal(topology, grid).passed)
        self.assertTrue(check_r4_board_parallel(topology, grid).passed)
        self.assertTrue(check_r5_exact_fit(topology, grid).passed)


if __name__ == "__main__":
    unittest.main()
