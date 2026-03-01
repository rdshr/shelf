from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "Gallery3DArtifacts",
    "GalleryArtifacts",
    "TypeGroup",
    "TypeSubpagesArtifacts",
    "build_type_groups",
    "generate_type_gallery",
    "generate_type_gallery_3d",
    "generate_type_subpages",
    "layer_cell_counts",
    "launch_interactive_viewer",
    "render_structure",
]

_EXPORTS: dict[str, tuple[str, str]] = {
    "launch_interactive_viewer": ("visualization.interactive_viewer", "launch_interactive_viewer"),
    "render_structure": ("visualization.render_3d", "render_structure"),
    "TypeGroup": ("visualization.type_grouping", "TypeGroup"),
    "build_type_groups": ("visualization.type_grouping", "build_type_groups"),
    "layer_cell_counts": ("visualization.type_grouping", "layer_cell_counts"),
    "Gallery3DArtifacts": ("visualization.type_gallery_3d", "Gallery3DArtifacts"),
    "generate_type_gallery_3d": ("visualization.type_gallery_3d", "generate_type_gallery_3d"),
    "GalleryArtifacts": ("visualization.type_gallery", "GalleryArtifacts"),
    "generate_type_gallery": ("visualization.type_gallery", "generate_type_gallery"),
    "TypeSubpagesArtifacts": ("visualization.type_subpages", "TypeSubpagesArtifacts"),
    "generate_type_subpages": ("visualization.type_subpages", "generate_type_subpages"),
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = _EXPORTS[name]
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
