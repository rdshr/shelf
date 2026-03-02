from __future__ import annotations

import unittest

from domain import (
    BoundaryDefinition,
    DiscreteGrid,
    Footprint2D,
    Module,
    Opening2D,
    PanelPlacement,
    Rect2D,
    Space3D,
    StructureFamily,
    StructureTopology,
    VerificationInput,
)
from geometry.frame import derive_boundary_skeleton_edges
from rules.combination_rules import geometric_type_combinations
from shelf_framework import verify
from verification import verify_structure


class VerificationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.boundary = BoundaryDefinition(
            layers_n=2,
            payload_p_per_layer=10.0,
            space_s_per_layer=Space3D(width=10.0, depth=10.0, height=10.0),
            opening_o=Opening2D(width=10.0, height=10.0),
            footprint_a=Footprint2D(width=10.0, depth=10.0),
        )
        self.grid = DiscreteGrid(x_cells=1, y_cells=1, layers_n=2, cell_width=10.0, cell_depth=10.0)
        self.topology = StructureTopology(
            panels=(
                PanelPlacement(rect=Rect2D(0, 1, 0, 1), layer_index=0),
                PanelPlacement(rect=Rect2D(0, 1, 0, 1), layer_index=1),
            )
        )
        self.frame_topology = StructureTopology(
            family=StructureFamily.FRAME,
            frame_cells=frozenset({(0, 0, 0)}),
            frame_edges=derive_boundary_skeleton_edges(frozenset({(0, 0, 0)})),
        )

    def test_boundary_invalid_fails(self) -> None:
        bad_boundary = BoundaryDefinition(
            layers_n=0,
            payload_p_per_layer=0.0,
            space_s_per_layer=Space3D(width=10.0, depth=10.0, height=10.0),
            opening_o=Opening2D(width=10.0, height=10.0),
            footprint_a=Footprint2D(width=10.0, depth=10.0),
        )
        report = verify_structure(self.topology, bad_boundary, self.grid, baseline_efficiency=0.1)
        self.assertFalse(report.passed)
        self.assertFalse(report.boundary_valid)

    def test_valid_combo_and_efficiency_pass(self) -> None:
        report = verify_structure(self.topology, self.boundary, self.grid, baseline_efficiency=0.1)
        self.assertTrue(report.passed)

    def test_not_improved_efficiency_fails(self) -> None:
        report = verify_structure(self.topology, self.boundary, self.grid, baseline_efficiency=999.0)
        self.assertFalse(report.passed)
        self.assertFalse(report.efficiency_improved)

    def test_cp_combo_invalid(self) -> None:
        result = verify(
            VerificationInput(
                boundary=self.boundary,
                combo={Module.CONNECTOR, Module.PANEL},
                valid_combinations=geometric_type_combinations(),
                baseline_efficiency=0.1,
                target_efficiency=0.2,
            )
        )
        self.assertFalse(result.passed)

    def test_projection_gain_rule_r6_fails_when_weighted_cells_not_greater_than_footprint(self) -> None:
        single_layer = StructureTopology(
            panels=(PanelPlacement(rect=Rect2D(0, 1, 0, 1), layer_index=0),)
        )
        report = verify_structure(single_layer, self.boundary, self.grid, baseline_efficiency=0.0)
        self.assertFalse(report.passed)
        r6 = next(item for item in report.structural_checks if item.name == "R6")
        self.assertFalse(r6.passed)
        self.assertTrue(any("weighted projected panel cells must be > footprint cells" in msg for msg in r6.reasons))

    def test_frame_without_panel_not_failed_by_r4_r5(self) -> None:
        report = verify_structure(self.frame_topology, self.boundary, self.grid, baseline_efficiency=0.0)
        self.assertTrue(report.passed)
        r4 = next(item for item in report.structural_checks if item.name == "R4")
        r5 = next(item for item in report.structural_checks if item.name == "R5")
        r6 = next(item for item in report.structural_checks if item.name == "R6")
        self.assertTrue(r4.passed)
        self.assertTrue(r5.passed)
        self.assertTrue(r6.passed)
        self.assertTrue(any("not applicable" in msg for msg in r4.reasons))
        self.assertTrue(any("not applicable" in msg for msg in r5.reasons))
        self.assertTrue(any("not applicable" in msg for msg in r6.reasons))


if __name__ == "__main__":
    unittest.main()
