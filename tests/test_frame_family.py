from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from domain.models import DiscreteGrid, EnumerationConfig, StructureFamily, StructureTopology
from enumeration import canonical_key, counting_framework_summary, enumerate_structure_types
from geometry.frame import derive_boundary_skeleton_edges
from visualization import render_structure


class FrameFamilyTest(unittest.TestCase):
    def test_frame_can_be_enumerated_independently(self) -> None:
        grid = DiscreteGrid(x_cells=2, y_cells=1, layers_n=1)
        result = enumerate_structure_types(
            EnumerationConfig(
                grid=grid,
                include_shelf_family=False,
                include_frame_family=True,
                allow_empty_layer=True,
                max_type_count=1000,
            )
        )
        self.assertEqual(result.shelf_raw_candidate_count, 0)
        self.assertGreater(result.frame_raw_candidate_count, 0)
        self.assertTrue(all(item.topology.family == StructureFamily.FRAME for item in result.unique_candidates))

    def test_frame_canonical_dedup_by_translation(self) -> None:
        cells_a = frozenset({(0, 0, 0)})
        cells_b = frozenset({(1, 0, 0)})
        top_a = StructureTopology(
            family=StructureFamily.FRAME,
            frame_cells=cells_a,
            frame_edges=derive_boundary_skeleton_edges(cells_a),
        )
        top_b = StructureTopology(
            family=StructureFamily.FRAME,
            frame_cells=cells_b,
            frame_edges=derive_boundary_skeleton_edges(cells_b),
        )
        key_a = canonical_key(top_a, mirror_equivalent=True, axis_permutation_equivalent=True)
        key_b = canonical_key(top_b, mirror_equivalent=True, axis_permutation_equivalent=True)
        self.assertEqual(key_a, key_b)

    def test_frame_can_render_3d(self) -> None:
        cells = frozenset({(0, 0, 0)})
        topology = StructureTopology(
            family=StructureFamily.FRAME,
            frame_cells=cells,
            frame_edges=derive_boundary_skeleton_edges(cells),
        )
        grid = DiscreteGrid(x_cells=1, y_cells=1, layers_n=1)
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts = render_structure(topology, grid, tmp_dir, "frame_smoke")
            obj_path = Path(artifacts["obj_fallback"])
            self.assertTrue(obj_path.exists())
            self.assertGreater(obj_path.stat().st_size, 0)

    def test_frame_and_shelf_summary_counts(self) -> None:
        grid = DiscreteGrid(x_cells=1, y_cells=1, layers_n=1)
        result = enumerate_structure_types(
            EnumerationConfig(
                grid=grid,
                include_shelf_family=True,
                include_frame_family=True,
                allow_empty_layer=True,
                max_type_count=1000,
            )
        )
        summary = counting_framework_summary(result, grid)
        self.assertEqual(result.shelf_raw_candidate_count, 2)
        self.assertEqual(result.frame_raw_candidate_count, 1)
        self.assertEqual(result.raw_candidate_count, 3)
        self.assertEqual(summary["formula_instantiated"], result.raw_candidate_count)
        self.assertEqual(summary["all"]["formula_instantiated"], 3)
        self.assertEqual(summary["shelf"]["formula_instantiated"], 2)
        self.assertEqual(summary["frame"]["formula_instantiated"], 1)


if __name__ == "__main__":
    unittest.main()
