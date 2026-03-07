from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import math
from typing import Any

Vector3 = tuple[float, float, float]
Point3 = tuple[float, float, float]


@dataclass(frozen=True)
class Space3D:
    width: float
    depth: float
    height: float

    def is_valid(self) -> bool:
        return self.width > 0 and self.depth > 0 and self.height > 0


@dataclass(frozen=True)
class Opening2D:
    width: float
    height: float

    def is_valid(self) -> bool:
        return self.width > 0 and self.height > 0


@dataclass(frozen=True)
class Footprint2D:
    width: float
    depth: float

    def is_valid(self) -> bool:
        return self.width > 0 and self.depth > 0


@dataclass(frozen=True)
class BoundaryDefinition:
    layers_n: int
    payload_p_per_layer: float
    space_s_per_layer: Space3D
    opening_o: Opening2D
    footprint_a: Footprint2D

    def validate(self) -> tuple[bool, list[str]]:
        errors: list[str] = []

        if self.layers_n <= 0:
            errors.append("layers_n must be > 0")
        if self.payload_p_per_layer <= 0:
            errors.append("payload_p_per_layer must be > 0")
        if not self.space_s_per_layer.is_valid():
            errors.append("space_s_per_layer must be positive on all dimensions")
        if not self.opening_o.is_valid():
            errors.append("opening_o must be positive on all dimensions")
        if not self.footprint_a.is_valid():
            errors.append("footprint_a must be positive on all dimensions")

        return len(errors) == 0, errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "layers_n": self.layers_n,
            "payload_p_per_layer": self.payload_p_per_layer,
            "space_s_per_layer": asdict(self.space_s_per_layer),
            "opening_o": asdict(self.opening_o),
            "footprint_a": asdict(self.footprint_a),
        }


class Module(str, Enum):
    ROD = "rod"
    CONNECTOR = "connector"
    PANEL = "panel"


MODULE_ROLE: dict[Module, str] = {
    Module.ROD: "load-bearing support",
    Module.CONNECTOR: "joint between structural members",
    Module.PANEL: "placement surface",
}


def _dot(lhs: Vector3, rhs: Vector3) -> float:
    return lhs[0] * rhs[0] + lhs[1] * rhs[1] + lhs[2] * rhs[2]


def _cross(lhs: Vector3, rhs: Vector3) -> Vector3:
    return (
        lhs[1] * rhs[2] - lhs[2] * rhs[1],
        lhs[2] * rhs[0] - lhs[0] * rhs[2],
        lhs[0] * rhs[1] - lhs[1] * rhs[0],
    )


def _norm(vec: Vector3) -> float:
    return math.sqrt(_dot(vec, vec))


def _normalize(vec: Vector3, tolerance: float) -> Vector3 | None:
    length = _norm(vec)
    if length <= tolerance:
        return None
    return (vec[0] / length, vec[1] / length, vec[2] / length)


def _subtract(lhs: Point3, rhs: Point3) -> Vector3:
    return (lhs[0] - rhs[0], lhs[1] - rhs[1], lhs[2] - rhs[2])


def _is_close(lhs: float, rhs: float, tolerance: float) -> bool:
    return abs(lhs - rhs) <= tolerance


def _is_axis_aligned(vec: Vector3, tolerance: float) -> bool:
    normalized = _normalize(vec, tolerance)
    if normalized is None:
        return False
    non_zero_axes = sum(1 for item in normalized if abs(item) > tolerance)
    return non_zero_axes == 1


def _is_parallel_or_perpendicular_angle(angle_deg: float, tolerance: float) -> bool:
    normalized = abs(angle_deg) % 180.0
    return (
        _is_close(normalized, 0.0, tolerance)
        or _is_close(normalized, 90.0, tolerance)
        or _is_close(normalized, 180.0, tolerance)
    )


def _points_form_rectangle(points: list[Point3], tolerance: float) -> bool:
    if len(points) != 4:
        return False

    distances_sq: list[float] = []
    for i in range(4):
        for j in range(i + 1, 4):
            delta = _subtract(points[i], points[j])
            distances_sq.append(_dot(delta, delta))

    distances_sq.sort()
    d0, d1, d2, d3, d4, d5 = distances_sq
    tol_sq = tolerance * tolerance
    if d0 <= tol_sq:
        return False

    return (
        _is_close(d0, d1, tol_sq)
        and _is_close(d2, d3, tol_sq)
        and _is_close(d4, d5, tol_sq)
        and _is_close(d0 + d2, d4, tol_sq)
    )


def _corners_match_with_tolerance(
    lhs: list[Point3], rhs: list[Point3], tolerance: float
) -> bool:
    if len(lhs) != len(rhs):
        return False

    unmatched = rhs[:]
    for corner in lhs:
        matched_index = None
        for idx, candidate in enumerate(unmatched):
            if _norm(_subtract(corner, candidate)) <= tolerance:
                matched_index = idx
                break
        if matched_index is None:
            return False
        unmatched.pop(matched_index)
    return True


def _board_normal(corners: list[Point3], tolerance: float) -> Vector3 | None:
    if len(corners) < 3:
        return None

    for i in range(len(corners)):
        for j in range(i + 1, len(corners)):
            for k in range(j + 1, len(corners)):
                edge_1 = _subtract(corners[j], corners[i])
                edge_2 = _subtract(corners[k], corners[i])
                normal = _cross(edge_1, edge_2)
                normalized = _normalize(normal, tolerance)
                if normalized is not None:
                    return normalized
    return None


@dataclass(frozen=True)
class ExactFitSpec:
    board_corners: list[Point3]
    support_points: list[Point3]
    corner_rod_directions: list[Vector3]
    epsilon: float = 1e-6


class StructuralPrinciples:
    @staticmethod
    def rods_orthogonal_layout(
        rod_directions: list[Vector3],
        rod_connection_angles_deg: list[float],
        angle_tolerance_deg: float = 1e-6,
    ) -> bool:
        if not rod_directions:
            return False
        if any(not _is_axis_aligned(item, angle_tolerance_deg) for item in rod_directions):
            return False
        return all(
            _is_parallel_or_perpendicular_angle(angle, angle_tolerance_deg)
            for angle in rod_connection_angles_deg
        )

    @staticmethod
    def boards_parallel_with_rod_constraints(
        board_normals: list[Vector3],
        rod_to_board_plane_angles_deg: list[float],
        angle_tolerance_deg: float = 1e-6,
    ) -> bool:
        if not board_normals:
            return False

        normalized_normals: list[Vector3] = []
        for normal in board_normals:
            normalized = _normalize(normal, angle_tolerance_deg)
            if normalized is None:
                return False
            normalized_normals.append(normalized)

        base = normalized_normals[0]
        for normal in normalized_normals[1:]:
            if _norm(_cross(base, normal)) > angle_tolerance_deg:
                return False

        return all(
            _is_parallel_or_perpendicular_angle(angle, angle_tolerance_deg)
            for angle in rod_to_board_plane_angles_deg
        )

    @staticmethod
    def exact_fit(spec: ExactFitSpec) -> tuple[bool, list[str]]:
        errors: list[str] = []

        if spec.epsilon <= 0:
            errors.append("epsilon must be > 0")
        if len(spec.board_corners) != 4:
            errors.append("board_corners must contain exactly 4 points")
        if len(spec.support_points) != 4:
            errors.append("support_points must contain exactly 4 points")
        if len(spec.corner_rod_directions) != 4:
            errors.append("corner_rod_directions must contain exactly 4 vectors")

        if errors:
            return False, errors

        if not _points_form_rectangle(spec.board_corners, spec.epsilon):
            errors.append("board corners must form a rectangle in board plane")
        if not _points_form_rectangle(spec.support_points, spec.epsilon):
            errors.append("support points must form a rectangle")
        if not _corners_match_with_tolerance(
            spec.board_corners, spec.support_points, spec.epsilon
        ):
            errors.append("board corners must coincide with support points within epsilon")

        normalized_rods: list[Vector3] = []
        for direction in spec.corner_rod_directions:
            normalized = _normalize(direction, spec.epsilon)
            if normalized is None:
                errors.append("corner rod direction must be non-zero")
                continue
            normalized_rods.append(normalized)

        if normalized_rods:
            base = normalized_rods[0]
            for direction in normalized_rods[1:]:
                if _norm(_cross(base, direction)) > spec.epsilon:
                    errors.append("corner rods must be parallel to each other")
                    break

        board_normal = _board_normal(spec.board_corners, spec.epsilon)
        if board_normal is None:
            errors.append("board corners must define a valid plane")
        elif normalized_rods:
            for direction in normalized_rods:
                if _norm(_cross(direction, board_normal)) > spec.epsilon:
                    errors.append("corner rods must be perpendicular to board plane")
                    break

        return len(errors) == 0, errors


@dataclass(frozen=True)
class VerificationInput:
    boundary: BoundaryDefinition
    combo: set[Module]
    valid_combinations: list[set[Module]]
    baseline_efficiency: float
    target_efficiency: float


@dataclass(frozen=True)
class VerificationResult:
    boundary_valid: bool
    combination_valid: bool
    efficiency_improved: bool
    passed: bool
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def verify(payload: VerificationInput) -> VerificationResult:
    boundary_valid, boundary_errors = payload.boundary.validate()
    combo_key = frozenset(payload.combo)
    valid_set = {frozenset(item) for item in payload.valid_combinations}
    combination_valid = combo_key in valid_set
    efficiency_improved = payload.target_efficiency > payload.baseline_efficiency

    reasons: list[str] = []
    reasons.extend(boundary_errors)
    if not combination_valid:
        reasons.append("combo is not in valid combinations")
    if not efficiency_improved:
        reasons.append("target_efficiency must be > baseline_efficiency")

    return VerificationResult(
        boundary_valid=boundary_valid,
        combination_valid=combination_valid,
        efficiency_improved=efficiency_improved,
        passed=boundary_valid and combination_valid and efficiency_improved,
        reasons=reasons,
    )


def modules_to_list(combo: set[Module]) -> list[str]:
    return sorted(item.value for item in combo)
