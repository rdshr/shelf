from __future__ import annotations

import unittest

from shelf_framework import ExactFitSpec, StructuralPrinciples


class ExactFitTest(unittest.TestCase):
    def test_exact_fit_valid(self) -> None:
        spec = ExactFitSpec(
            board_corners=[
                (0.0, 0.0, 1.0),
                (1.0, 0.0, 1.0),
                (1.0, 1.0, 1.0),
                (0.0, 1.0, 1.0),
            ],
            support_points=[
                (0.0, 0.0, 1.0),
                (1.0, 0.0, 1.0),
                (1.0, 1.0, 1.0),
                (0.0, 1.0, 1.0),
            ],
            corner_rod_directions=[(0.0, 0.0, 1.0)] * 4,
            epsilon=1e-6,
        )
        passed, errors = StructuralPrinciples.exact_fit(spec)
        self.assertTrue(passed)
        self.assertEqual(errors, [])

    def test_exact_fit_missing_corner_support_invalid(self) -> None:
        spec = ExactFitSpec(
            board_corners=[
                (0.0, 0.0, 1.0),
                (1.0, 0.0, 1.0),
                (1.0, 1.0, 1.0),
                (0.0, 1.0, 1.0),
            ],
            support_points=[
                (0.0, 0.0, 1.0),
                (1.0, 0.0, 1.0),
                (1.0, 1.0, 1.0),
            ],
            corner_rod_directions=[(0.0, 0.0, 1.0)] * 4,
            epsilon=1e-6,
        )
        passed, _ = StructuralPrinciples.exact_fit(spec)
        self.assertFalse(passed)

    def test_exact_fit_non_rectangle_invalid(self) -> None:
        spec = ExactFitSpec(
            board_corners=[
                (0.0, 0.0, 1.0),
                (1.0, 0.0, 1.0),
                (1.2, 1.0, 1.0),
                (0.0, 1.0, 1.0),
            ],
            support_points=[
                (0.0, 0.0, 1.0),
                (1.0, 0.0, 1.0),
                (1.2, 1.0, 1.0),
                (0.0, 1.0, 1.0),
            ],
            corner_rod_directions=[(0.0, 0.0, 1.0)] * 4,
            epsilon=1e-6,
        )
        passed, _ = StructuralPrinciples.exact_fit(spec)
        self.assertFalse(passed)


if __name__ == "__main__":
    unittest.main()
