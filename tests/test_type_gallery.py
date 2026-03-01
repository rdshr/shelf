from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from visualization.type_gallery import generate_type_gallery
from visualization.viewer_backend import enumerate_candidates_for_view


class TypeGalleryTest(unittest.TestCase):
    def test_generate_gallery_files(self) -> None:
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
            img = Path(tmp_dir) / "gallery.png"
            html = Path(tmp_dir) / "gallery.html"
            artifacts = generate_type_gallery(
                candidates=backend.candidates,
                grid=backend.grid,
                output_image=img,
                output_html=html,
                columns=2,
                title="test-gallery",
            )
            self.assertEqual(artifacts.type_count, len(backend.candidates))
            self.assertTrue(img.exists())
            self.assertTrue(html.exists())
            self.assertGreater(img.stat().st_size, 0)
            self.assertGreater(html.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
