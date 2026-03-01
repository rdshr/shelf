from __future__ import annotations

from domain.enums import StructureFamily
from domain.models import Cell3D, PanelPlacement, Rect2D, StructureTopology


def _transform_point(x: int, y: int, transform: str) -> tuple[int, int]:
    if transform == "id":
        return (x, y)
    if transform == "rot90":
        return (-y, x)
    if transform == "rot180":
        return (-x, -y)
    if transform == "rot270":
        return (y, -x)
    if transform == "mirror_x":
        return (-x, y)
    if transform == "mirror_y":
        return (x, -y)
    if transform == "mirror_diag":
        return (y, x)
    if transform == "mirror_anti":
        return (-y, -x)
    raise ValueError(f"unsupported transform: {transform}")


def _transform_rect(rect: Rect2D, transform: str) -> Rect2D:
    corners = [(rect.x0, rect.y0), (rect.x0, rect.y1), (rect.x1, rect.y0), (rect.x1, rect.y1)]
    transformed = [_transform_point(x, y, transform) for x, y in corners]
    xs = [item[0] for item in transformed]
    ys = [item[1] for item in transformed]
    return Rect2D(x0=min(xs), x1=max(xs), y0=min(ys), y1=max(ys))


def _transform_cell(cell: Cell3D, transform: str) -> Cell3D:
    x, y, z = cell
    tx, ty = _transform_point(x, y, transform)
    return (tx, ty, z)


def _canonicalize_panels(panels: list[PanelPlacement]) -> tuple[tuple[int, int, int, int, int], ...]:
    if not panels:
        return tuple()

    min_x = min(panel.rect.x0 for panel in panels)
    min_y = min(panel.rect.y0 for panel in panels)
    min_layer = min(panel.layer_index for panel in panels)

    normalized = []
    for panel in panels:
        rect = Rect2D(
            x0=panel.rect.x0 - min_x,
            x1=panel.rect.x1 - min_x,
            y0=panel.rect.y0 - min_y,
            y1=panel.rect.y1 - min_y,
        )
        normalized.append((panel.layer_index - min_layer, rect.x0, rect.x1, rect.y0, rect.y1))

    return tuple(sorted(normalized))


def _canonicalize_cells(cells: frozenset[Cell3D]) -> tuple[Cell3D, ...]:
    if not cells:
        return tuple()
    min_x = min(cell[0] for cell in cells)
    min_y = min(cell[1] for cell in cells)
    min_z = min(cell[2] for cell in cells)
    normalized = sorted((x - min_x, y - min_y, z - min_z) for x, y, z in cells)
    return tuple(normalized)


def canonical_key(
    topology: StructureTopology,
    mirror_equivalent: bool = True,
    axis_permutation_equivalent: bool = True,
) -> str:
    if axis_permutation_equivalent and mirror_equivalent:
        transforms = [
            "id",
            "rot90",
            "rot180",
            "rot270",
            "mirror_x",
            "mirror_y",
            "mirror_diag",
            "mirror_anti",
        ]
    elif axis_permutation_equivalent:
        transforms = ["id", "rot90", "rot180", "rot270"]
    elif mirror_equivalent:
        transforms = ["id", "rot180", "mirror_x", "mirror_y"]
    else:
        transforms = ["id"]

    if topology.family == StructureFamily.FRAME:
        keys_cells: list[tuple[Cell3D, ...]] = []
        for transform in transforms:
            transformed_cells = frozenset(_transform_cell(cell, transform) for cell in topology.frame_cells)
            keys_cells.append(_canonicalize_cells(transformed_cells))
        best_cells = min(keys_cells) if keys_cells else tuple()
        body = ";".join(f"C({x},{y},{z})" for x, y, z in best_cells) or "empty"
        return f"{StructureFamily.FRAME.value.upper()}|{body}"

    keys_panels: list[tuple[tuple[int, int, int, int, int], ...]] = []
    for transform in transforms:
        transformed_panels = [
            PanelPlacement(rect=_transform_rect(panel.rect, transform), layer_index=panel.layer_index)
            for panel in topology.panels
        ]
        keys_panels.append(_canonicalize_panels(transformed_panels))

    best_panels = min(keys_panels) if keys_panels else tuple()
    body = "|".join(f"L{layer}:({x0},{x1},{y0},{y1})" for layer, x0, x1, y0, y1 in best_panels) or "empty"
    return f"{StructureFamily.SHELF.value.upper()}|{body}"
