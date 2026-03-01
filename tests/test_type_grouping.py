from __future__ import annotations

import unittest

from visualization.type_grouping import build_type_groups
from visualization.viewer_backend import enumerate_candidates_for_view


class TypeGroupingTest(unittest.TestCase):
    def test_groups_cover_all_candidates(self) -> None:
        backend = enumerate_candidates_for_view(
            x_cells=2,
            y_cells=2,
            layers_n=2,
            cell_width=45.0,
            cell_depth=20.0,
            layer_height=30.0,
            allow_empty_layer=True,
            filter_mode="valid",
            max_type_count=5000,
        )
        groups = build_type_groups(backend.candidates, backend.grid)
        self.assertGreater(len(groups), 0)
        self.assertEqual(sum(len(group.items) for group in groups), len(backend.candidates))

    def test_groups_sorted_by_active_then_total_cells(self) -> None:
        backend = enumerate_candidates_for_view(
            x_cells=2,
            y_cells=2,
            layers_n=2,
            cell_width=45.0,
            cell_depth=20.0,
            layer_height=30.0,
            allow_empty_layer=True,
            filter_mode="valid",
            max_type_count=5000,
        )
        groups = build_type_groups(backend.candidates, backend.grid)

        keys = [
            (g.family != "shelf", -g.active_layers, -g.total_cells, g.counts_per_layer)
            for g in groups
        ]
        self.assertEqual(keys, sorted(keys))


if __name__ == "__main__":
    unittest.main()
