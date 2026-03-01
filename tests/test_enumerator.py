from __future__ import annotations

import unittest

from domain.models import DiscreteGrid, EnumerationConfig
from enumeration import counting_framework_summary, enumerate_structure_types


class EnumeratorTest(unittest.TestCase):
    def test_small_grid_exhaustive_and_dedup(self) -> None:
        grid = DiscreteGrid(x_cells=2, y_cells=2, layers_n=1)
        result = enumerate_structure_types(
            EnumerationConfig(
                grid=grid,
                allow_empty_layer=True,
                mirror_equivalent=True,
                axis_permutation_equivalent=True,
                max_type_count=5000,
            )
        )
        self.assertGreater(result.raw_candidate_count, 0)
        self.assertGreater(result.stats.unique_types, 0)
        self.assertLess(result.stats.unique_types, result.raw_candidate_count)
        self.assertGreater(len(result.valid_candidates()), 0)
        self.assertGreater(len(result.invalid_candidates()), 0)

    def test_partition_count_recorded(self) -> None:
        grid = DiscreteGrid(x_cells=2, y_cells=2, layers_n=1)
        result = enumerate_structure_types(
            EnumerationConfig(grid=grid, allow_empty_layer=False, max_type_count=5000)
        )
        self.assertGreater(len(result.occupancy_partition_count), 0)
        self.assertTrue(all(count >= 1 for count in result.occupancy_partition_count.values()))

    def test_counting_framework_matches_raw_candidate_count_when_not_truncated(self) -> None:
        grid = DiscreteGrid(x_cells=2, y_cells=2, layers_n=2)
        result = enumerate_structure_types(
            EnumerationConfig(
                grid=grid,
                allow_empty_layer=True,
                mirror_equivalent=True,
                axis_permutation_equivalent=True,
                max_type_count=5000,
            )
        )
        summary = counting_framework_summary(result, grid)
        self.assertFalse(result.stats.truncated)
        self.assertEqual(summary["formula_instantiated"], result.raw_candidate_count)


if __name__ == "__main__":
    unittest.main()
