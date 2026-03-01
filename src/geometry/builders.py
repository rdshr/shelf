from __future__ import annotations

from dataclasses import dataclass

from domain.enums import StructureFamily
from domain.models import DiscreteGrid, GridEdge3D, PanelPlacement, Point3, StructureTopology
from geometry.frame import derive_boundary_connectors, derive_boundary_skeleton_edges


@dataclass(frozen=True)
class ConnectorNode:
    point: Point3


@dataclass(frozen=True)
class RodSegment:
    start: Point3
    end: Point3

    def direction(self) -> tuple[float, float, float]:
        return (
            self.end[0] - self.start[0],
            self.end[1] - self.start[1],
            self.end[2] - self.start[2],
        )


@dataclass(frozen=True)
class PanelSurface:
    corners: tuple[Point3, Point3, Point3, Point3]


@dataclass(frozen=True)
class StructureGeometry:
    connectors: tuple[ConnectorNode, ...]
    rods: tuple[RodSegment, ...]
    panels: tuple[PanelSurface, ...]


def _panel_surface(panel: PanelPlacement, grid: DiscreteGrid) -> PanelSurface:
    corners = panel.corners_world(grid)
    return PanelSurface(corners=(corners[0], corners[1], corners[2], corners[3]))


def _build_shelf_geometry(topology: StructureTopology, grid: DiscreteGrid) -> StructureGeometry:
    panel_surfaces = tuple(_panel_surface(panel, grid) for panel in topology.panels)

    connector_points: set[Point3] = set()
    z_by_xy: dict[tuple[float, float], float] = {}

    for panel in topology.panels:
        corners = panel.corners_world(grid)
        for point in corners:
            connector_points.add(point)
            key = (point[0], point[1])
            z_by_xy[key] = max(z_by_xy.get(key, 0.0), point[2])

    connectors = tuple(ConnectorNode(point=item) for item in sorted(connector_points))
    rods = tuple(
        RodSegment(start=(xy[0], xy[1], 0.0), end=(xy[0], xy[1], top_z))
        for xy, top_z in sorted(z_by_xy.items())
    )

    return StructureGeometry(connectors=connectors, rods=rods, panels=panel_surfaces)


def _point3d_to_world(point: tuple[int, int, int], grid: DiscreteGrid) -> Point3:
    return (
        float(point[0]) * grid.cell_width,
        float(point[1]) * grid.cell_depth,
        float(point[2]) * grid.layer_height,
    )


def _edge_to_rod(edge: GridEdge3D, grid: DiscreteGrid) -> RodSegment:
    return RodSegment(
        start=_point3d_to_world(edge[0], grid),
        end=_point3d_to_world(edge[1], grid),
    )


def _build_frame_geometry(topology: StructureTopology, grid: DiscreteGrid) -> StructureGeometry:
    edges = topology.frame_edges or derive_boundary_skeleton_edges(topology.frame_cells)
    connectors = tuple(
        ConnectorNode(point=_point3d_to_world(point, grid))
        for point in derive_boundary_connectors(edges)
    )
    rods = tuple(_edge_to_rod(edge, grid) for edge in edges)
    return StructureGeometry(connectors=connectors, rods=rods, panels=tuple())


def build_geometry(topology: StructureTopology, grid: DiscreteGrid) -> StructureGeometry:
    if topology.family == StructureFamily.FRAME:
        return _build_frame_geometry(topology, grid)
    return _build_shelf_geometry(topology, grid)
