from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from domain.models import DiscreteGrid, PanelPlacement, Rect2D, StructureTopology
from visualization import render_structure


class VisualizationSmokeTest(unittest.TestCase):
    def test_render_outputs_obj(self) -> None:
        topology = StructureTopology(panels=(PanelPlacement(rect=Rect2D(0, 1, 0, 1), layer_index=0),))
        grid = DiscreteGrid(x_cells=1, y_cells=1, layers_n=1)

        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts = render_structure(topology, grid, tmp_dir, "smoke")
            obj_path = Path(artifacts["obj_fallback"])
            self.assertTrue(obj_path.exists())
            self.assertGreater(obj_path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
