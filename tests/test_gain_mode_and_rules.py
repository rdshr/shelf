from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from shelf_catalog_engine import (
    BoundaryConstraint,
    SearchSpace,
    _evaluate_masks,
    _panel_cells_from_masks,
    _pattern_stats,
    build_catalog,
    default_boundary,
)


class GainModeAndRulesTest(unittest.TestCase):
    def test_l2_combination_rules_include_single_connected_system(self) -> None:
        standard_path = REPO_ROOT / "standards" / "L2" / "置物架框架标准.md"
        content = standard_path.read_text(encoding="utf-8")
        self.assertIn("有效组合必须为单一连通整体", content)
        self.assertIn("所有层板的4个角点必须全部与杆端点端接", content)

    def test_viewer_uses_baseline_gain_label(self) -> None:
        html_path = REPO_ROOT / "web" / "shelf_viewer" / "index.html"
        content = html_path.read_text(encoding="utf-8")
        self.assertIn("基线取用增益 G_baseline", content)
        self.assertNotIn("基线取用面积 S_baseline", content)

    def test_viewer_shows_rule_and_boundary_failure_counters(self) -> None:
        html_path = REPO_ROOT / "web" / "shelf_viewer" / "index.html"
        content = html_path.read_text(encoding="utf-8")
        self.assertIn('id="ruleFailed"', content)
        self.assertIn('id="boundaryFailed"', content)

    def test_catalog_boundary_meta_uses_baseline_gain_key(self) -> None:
        boundary = default_boundary()
        self.assertTrue(hasattr(boundary, "baseline_gain"))
        self.assertFalse(hasattr(boundary, "baseline_space_s_per_layer"))

        space = SearchSpace(
            slots_x=1,
            slots_y=1,
            slots_z=1,
            panel_length=1.0,
            panel_width=1.0,
            rod_length=1.0,
            dedupe_symmetry=True,
        )
        payload = build_catalog(
            space=space,
            boundary=BoundaryConstraint(max_layers_n=1, baseline_gain=1.0),
            limit=10,
        )

        meta_boundary = payload["meta"]["boundary"]
        self.assertIn("baseline_gain", meta_boundary)
        self.assertNotIn("baseline_space_s_per_layer", meta_boundary)
        self.assertEqual(payload["meta"]["goal_rule"], "gain_ratio > 1")

    def test_rule_failed_designs_are_excluded_from_generated_total(self) -> None:
        space = SearchSpace(
            slots_x=1,
            slots_y=1,
            slots_z=1,
            panel_length=1.0,
            panel_width=1.0,
            rod_length=1.0,
            dedupe_symmetry=True,
        )
        payload = build_catalog(
            space=space,
            boundary=BoundaryConstraint(max_layers_n=1, baseline_gain=1.0),
            limit=10,
        )

        self.assertEqual(payload["meta"]["enumeration_total"], 2)
        self.assertEqual(payload["summary"]["rule_failed"], 2)
        self.assertEqual(payload["summary"]["generated_total"], 0)
        self.assertEqual(len(payload["rows"]), 2)

    def test_r8_single_connected_rule_blocks_disconnected_structure(self) -> None:
        pattern_stats = _pattern_stats(width=3, height=1, dedupe_symmetry=False)
        (
            _family_key,
            _family_label,
            rule_result,
            _boundary_passed,
            _goal_passed,
            _fail_reasons,
            _metrics,
            _support_union,
            _layer_area_sums,
        ) = _evaluate_masks(
            (0b000, 0b101),
            space=SearchSpace(
                slots_x=3,
                slots_y=1,
                slots_z=2,
                panel_length=1.0,
                panel_width=1.0,
                rod_length=1.0,
                dedupe_symmetry=False,
            ),
            boundary=BoundaryConstraint(max_layers_n=2, baseline_gain=1.0),
            pattern_stats=pattern_stats,
            edge_cells_per_layer=3,
        )

        self.assertTrue(rule_result.r3_min_counts)
        self.assertFalse(rule_result.r8_single_connected)
        self.assertFalse(rule_result.passed)

    def test_r9_trims_redundant_top_rod_segments(self) -> None:
        pattern_stats = _pattern_stats(width=1, height=1, dedupe_symmetry=False)
        (
            _family_key,
            _family_label,
            rule_result,
            _boundary_passed,
            _goal_passed,
            _fail_reasons,
            metrics,
            _support_union,
            _layer_area_sums,
        ) = _evaluate_masks(
            (0b1, 0b1, 0b0),
            space=SearchSpace(
                slots_x=1,
                slots_y=1,
                slots_z=3,
                panel_length=1.0,
                panel_width=1.0,
                rod_length=1.0,
                dedupe_symmetry=False,
            ),
            boundary=BoundaryConstraint(max_layers_n=3, baseline_gain=1.0),
            pattern_stats=pattern_stats,
            edge_cells_per_layer=1,
        )

        self.assertTrue(rule_result.r3_min_counts)
        self.assertTrue(rule_result.r8_single_connected)
        self.assertTrue(rule_result.r9_top_capped)
        self.assertTrue(rule_result.passed)
        self.assertEqual(metrics.rod_segments, 4)
        self.assertEqual(metrics.connector_points, 8)

    def test_dedupe_merges_shifted_equivalent_structures(self) -> None:
        space_no_dedupe = SearchSpace(
            slots_x=3,
            slots_y=1,
            slots_z=1,
            panel_length=1.0,
            panel_width=1.0,
            rod_length=1.0,
            dedupe_symmetry=False,
        )
        payload_no_dedupe = build_catalog(
            space=space_no_dedupe,
            boundary=BoundaryConstraint(max_layers_n=1, baseline_gain=1.0),
            limit=100,
        )

        space_with_dedupe = SearchSpace(
            slots_x=3,
            slots_y=1,
            slots_z=1,
            panel_length=1.0,
            panel_width=1.0,
            rod_length=1.0,
            dedupe_symmetry=True,
        )
        payload_with_dedupe = build_catalog(
            space=space_with_dedupe,
            boundary=BoundaryConstraint(max_layers_n=1, baseline_gain=1.0),
            limit=100,
        )

        self.assertEqual(payload_no_dedupe["meta"]["enumeration_total"], 8)
        self.assertEqual(payload_with_dedupe["meta"]["enumeration_total"], 5)
        self.assertGreater(payload_with_dedupe["meta"]["duplicate_removed"], 0)

    def test_ground_panel_does_not_double_count_ground_usable_area(self) -> None:
        pattern_stats = _pattern_stats(width=1, height=1, dedupe_symmetry=False)
        (
            _family_key,
            _family_label,
            _rule_result,
            _boundary_passed,
            _goal_passed,
            _fail_reasons,
            metrics,
            _support_union,
            _layer_area_sums,
        ) = _evaluate_masks(
            (0b1,),
            space=SearchSpace(
                slots_x=1,
                slots_y=1,
                slots_z=1,
                panel_length=1.0,
                panel_width=1.0,
                rod_length=1.0,
                dedupe_symmetry=False,
            ),
            boundary=BoundaryConstraint(max_layers_n=1, baseline_gain=1.0),
            pattern_stats=pattern_stats,
            edge_cells_per_layer=1,
        )

        self.assertEqual(metrics.footprint_a, 1.0)
        self.assertEqual(metrics.panel_area_total, 1.0)
        self.assertEqual(metrics.panel_area_above, 0.0)
        self.assertEqual(metrics.usable_area_total, 1.0)
        self.assertEqual(metrics.efficiency_current, 1.0)
        self.assertEqual(metrics.gain_ratio, 1.0)

    def test_rule_fail_status_returns_failed_structures(self) -> None:
        payload = build_catalog(
            space=SearchSpace(
                slots_x=1,
                slots_y=1,
                slots_z=1,
                panel_length=1.0,
                panel_width=1.0,
                rod_length=1.0,
                dedupe_symmetry=True,
            ),
            boundary=BoundaryConstraint(max_layers_n=1, baseline_gain=1.0),
            status_filter="rule_fail",
            limit=10,
        )

        self.assertEqual(payload["summary"]["rule_failed"], 2)
        self.assertEqual(len(payload["rows"]), 2)
        self.assertTrue(all(not row["validation"]["rules_passed"] for row in payload["rows"]))

    def test_status_all_includes_pass_and_fail_rows(self) -> None:
        payload = build_catalog(
            space=SearchSpace(
                slots_x=1,
                slots_y=1,
                slots_z=2,
                panel_length=1.0,
                panel_width=1.0,
                rod_length=1.0,
                dedupe_symmetry=True,
            ),
            boundary=BoundaryConstraint(max_layers_n=2, baseline_gain=1.0),
            status_filter="all",
            limit=20,
        )

        self.assertEqual(payload["meta"]["enumeration_total"], 4)
        self.assertEqual(len(payload["rows"]), 4)
        self.assertTrue(any(row["validation"]["rules_passed"] for row in payload["rows"]))
        self.assertTrue(any(not row["validation"]["rules_passed"] for row in payload["rows"]))

    def test_mid_layer_panel_gain_ratio_can_reach_two(self) -> None:
        pattern_stats = _pattern_stats(width=1, height=1, dedupe_symmetry=False)
        (
            _family_key,
            _family_label,
            rule_result,
            _boundary_passed,
            goal_passed,
            _fail_reasons,
            metrics,
            _support_union,
            _layer_area_sums,
        ) = _evaluate_masks(
            (0b0, 0b1, 0b0),
            space=SearchSpace(
                slots_x=1,
                slots_y=1,
                slots_z=3,
                panel_length=1.0,
                panel_width=1.0,
                rod_length=1.0,
                dedupe_symmetry=False,
            ),
            boundary=BoundaryConstraint(max_layers_n=3, baseline_gain=1.0),
            pattern_stats=pattern_stats,
            edge_cells_per_layer=1,
        )

        self.assertTrue(rule_result.passed)
        self.assertTrue(goal_passed)
        self.assertEqual(metrics.footprint_a, 1.0)
        self.assertEqual(metrics.usable_area_total, 2.0)
        self.assertEqual(metrics.gain_ratio, 2.0)

    def test_top_layer_single_panel_trims_rod_segments(self) -> None:
        pattern_stats = _pattern_stats(width=3, height=3, dedupe_symmetry=False)
        (
            _family_key,
            _family_label,
            rule_result,
            _boundary_passed,
            goal_passed,
            _fail_reasons,
            metrics,
            _support_union,
            _layer_area_sums,
        ) = _evaluate_masks(
            (0b0, 0b0, 0b1),
            space=SearchSpace(
                slots_x=3,
                slots_y=3,
                slots_z=3,
                panel_length=1.0,
                panel_width=1.0,
                rod_length=1.0,
                dedupe_symmetry=False,
            ),
            boundary=BoundaryConstraint(max_layers_n=3, baseline_gain=1.0),
            pattern_stats=pattern_stats,
            edge_cells_per_layer=8,
        )

        self.assertTrue(rule_result.passed)
        self.assertTrue(goal_passed)
        self.assertEqual(metrics.rod_segments, 8)
        self.assertEqual(metrics.connector_points, 12)

    def test_r10_requires_ground_panel_corners_supported_by_upper_rod_system(self) -> None:
        pattern_stats = _pattern_stats(width=2, height=1, dedupe_symmetry=False)
        (
            _family_key,
            _family_label,
            rule_result,
            _boundary_passed,
            _goal_passed,
            _fail_reasons,
            _metrics,
            _support_union,
            _layer_area_sums,
        ) = _evaluate_masks(
            (0b01, 0b10),
            space=SearchSpace(
                slots_x=2,
                slots_y=1,
                slots_z=2,
                panel_length=1.0,
                panel_width=1.0,
                rod_length=1.0,
                dedupe_symmetry=False,
            ),
            boundary=BoundaryConstraint(max_layers_n=2, baseline_gain=1.0),
            pattern_stats=pattern_stats,
            edge_cells_per_layer=2,
        )

        self.assertTrue(rule_result.r3_min_counts)
        self.assertTrue(rule_result.r8_single_connected)
        self.assertFalse(rule_result.r10_panel_four_corner_supported)
        self.assertFalse(rule_result.passed)

    def test_panel_layout_level_index_starts_from_zero(self) -> None:
        pattern_stats = _pattern_stats(width=1, height=1, dedupe_symmetry=False)
        panel_cells = _panel_cells_from_masks((0b1, 0b0), pattern_stats=pattern_stats)
        self.assertEqual(panel_cells[0], [0, 0, 0])


if __name__ == "__main__":
    unittest.main()
