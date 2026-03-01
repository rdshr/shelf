from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from visualization.type_subpages import generate_type_subpages
from visualization.viewer_backend import enumerate_candidates_for_view


class TypeSubpagesTest(unittest.TestCase):
    def test_generate_index_and_group_pages(self) -> None:
        backend = enumerate_candidates_for_view(
            x_cells=1,
            y_cells=2,
            layers_n=2,
            cell_width=10.0,
            cell_depth=10.0,
            layer_height=10.0,
            allow_empty_layer=True,
            filter_mode="valid",
            max_type_count=2000,
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts = generate_type_subpages(
                candidates=backend.candidates,
                grid=backend.grid,
                output_dir=tmp_dir,
                title="test-type-subpages",
                include_group_3d=False,
            )

            index_path = Path(artifacts.index_html)
            self.assertTrue(index_path.exists())
            self.assertGreater(index_path.stat().st_size, 0)
            self.assertGreater(artifacts.group_count, 0)
            self.assertEqual(len(artifacts.group_pages), artifacts.group_count)
            for item in artifacts.group_pages:
                page = Path(item)
                self.assertTrue(page.exists())
                self.assertGreater(page.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
