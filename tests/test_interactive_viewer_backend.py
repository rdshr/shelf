from __future__ import annotations

import unittest

from visualization.viewer_backend import enumerate_candidates_for_view


class InteractiveViewerBackendTest(unittest.TestCase):
    def test_backend_returns_candidates(self) -> None:
        result = enumerate_candidates_for_view(
            x_cells=2,
            y_cells=2,
            layers_n=1,
            cell_width=45.0,
            cell_depth=20.0,
            layer_height=30.0,
            allow_empty_layer=True,
            filter_mode="all",
        )
        self.assertGreater(len(result.candidates), 0)

    def test_filter_modes_partition(self) -> None:
        all_result = enumerate_candidates_for_view(
            x_cells=2,
            y_cells=2,
            layers_n=1,
            cell_width=45.0,
            cell_depth=20.0,
            layer_height=30.0,
            allow_empty_layer=True,
            filter_mode="all",
        )
        valid_result = enumerate_candidates_for_view(
            x_cells=2,
            y_cells=2,
            layers_n=1,
            cell_width=45.0,
            cell_depth=20.0,
            layer_height=30.0,
            allow_empty_layer=True,
            filter_mode="valid",
        )
        invalid_result = enumerate_candidates_for_view(
            x_cells=2,
            y_cells=2,
            layers_n=1,
            cell_width=45.0,
            cell_depth=20.0,
            layer_height=30.0,
            allow_empty_layer=True,
            filter_mode="invalid",
        )

        self.assertEqual(
            len(all_result.candidates),
            len(valid_result.candidates) + len(invalid_result.candidates),
        )


if __name__ == "__main__":
    unittest.main()
