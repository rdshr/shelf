from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from visualization.type_gallery_3d import generate_type_gallery_3d
from visualization.viewer_backend import enumerate_candidates_for_view


class TypeGallery3DTest(unittest.TestCase):
    def test_generate_3d_gallery_html(self) -> None:
        backend = enumerate_candidates_for_view(
            x_cells=1,
            y_cells=1,
            layers_n=1,
            cell_width=10.0,
            cell_depth=10.0,
            layer_height=10.0,
            allow_empty_layer=True,
            filter_mode="all",
            max_type_count=1000,
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            html = Path(tmp_dir) / "gallery3d.html"
            artifacts = generate_type_gallery_3d(
                candidates=backend.candidates,
                grid=backend.grid,
                output_html=html,
                columns=2,
                title="test-gallery-3d",
            )
            self.assertEqual(artifacts.type_count, len(backend.candidates))
            self.assertTrue(html.exists())
            self.assertGreater(html.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
