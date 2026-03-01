from __future__ import annotations

import unittest

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


if __name__ == "__main__":
    unittest.main()
