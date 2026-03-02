from __future__ import annotations

import unittest

from domain.models import DiscreteGrid, PanelPlacement, Rect2D, StructureFamily, StructureTopology
from rules.structural_rules import check_r6_projected_panel_gain


class ProjectionRuleTest(unittest.TestCase):
    def test_r6_passes_when_weighted_projection_cells_exceed_footprint_cells(self) -> None:
        grid = DiscreteGrid(x_cells=2, y_cells=2, layers_n=2)
        topology = StructureTopology(
            panels=(
                PanelPlacement(rect=Rect2D(0, 2, 0, 2), layer_index=0),
                PanelPlacement(rect=Rect2D(0, 2, 0, 2), layer_index=1),
            )
        )
        check = check_r6_projected_panel_gain(topology, grid)
        self.assertTrue(check.passed)

    def test_r6_fails_when_weighted_projection_cells_not_exceed_footprint_cells(self) -> None:
        grid = DiscreteGrid(x_cells=2, y_cells=2, layers_n=2)
        topology = StructureTopology(
            panels=(PanelPlacement(rect=Rect2D(0, 2, 0, 2), layer_index=0),)
        )
        check = check_r6_projected_panel_gain(topology, grid)
        self.assertFalse(check.passed)
        self.assertTrue(any("weighted projected panel cells must be > footprint cells" in msg for msg in check.reasons))

    def test_r6_not_applicable_for_frame(self) -> None:
        grid = DiscreteGrid(x_cells=2, y_cells=2, layers_n=2)
        topology = StructureTopology(
            family=StructureFamily.FRAME,
            frame_cells=frozenset({(0, 0, 0)}),
            frame_edges=tuple(),
        )
        check = check_r6_projected_panel_gain(topology, grid)
        self.assertTrue(check.passed)
        self.assertTrue(any("not applicable" in msg for msg in check.reasons))


if __name__ == "__main__":
    unittest.main()
