from __future__ import annotations

import argparse
import json

from visualization.type_gallery import generate_type_gallery
from visualization.viewer_backend import enumerate_candidates_for_view


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate contact-sheet image and HTML gallery for shelf types.")
    parser.add_argument("--x-cells", type=int, default=2)
    parser.add_argument("--y-cells", type=int, default=2)
    parser.add_argument("--layers", type=int, default=2)
    parser.add_argument("--allow-empty", action="store_true", default=True)
    parser.add_argument("--filter", choices=["valid", "invalid", "all"], default="valid")
    parser.add_argument("--output-image", default="docs/examples/type_gallery_2x2x2.png")
    parser.add_argument("--output-html", default="docs/examples/type_gallery_2x2x2.html")
    parser.add_argument("--columns", type=int, default=12)
    args = parser.parse_args()

    backend = enumerate_candidates_for_view(
        x_cells=args.x_cells,
        y_cells=args.y_cells,
        layers_n=args.layers,
        cell_width=45.0,
        cell_depth=20.0,
        layer_height=30.0,
        allow_empty_layer=args.allow_empty,
        filter_mode=args.filter,
        max_type_count=200000,
    )

    artifacts = generate_type_gallery(
        candidates=backend.candidates,
        grid=backend.grid,
        output_image=args.output_image,
        output_html=args.output_html,
        columns=args.columns,
        title=f"Type Gallery ({args.filter})",
    )

    payload = {
        "image": artifacts.image_path,
        "html": artifacts.html_path,
        "type_count": artifacts.type_count,
        "raw_candidates": backend.enumeration.raw_candidate_count,
        "unique_types": backend.enumeration.stats.unique_types,
        "valid_types": len(backend.enumeration.valid_candidates()),
        "invalid_types": len(backend.enumeration.invalid_candidates()),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
