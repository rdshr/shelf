from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from itertools import combinations, product
import json
import math
from pathlib import Path
from typing import Any, Callable, Iterable

STRICT_MAPPING_LEVEL = "L3"
STRICT_MAPPING_REGISTRY = "standards/L3/mapping_registry.json"
STRICT_MAPPING_VALIDATION_COMMAND = (
    "uv run python scripts/validate_strict_mapping.py --check-changes"
)


@dataclass(frozen=True)
class Goal:
    statement: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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

        return (len(errors) == 0, errors)

    def footprint_area(self) -> float:
        return self.footprint_a.width * self.footprint_a.depth

    def to_dict(self) -> dict[str, Any]:
        return {
            "layers_n": self.layers_n,
            "payload_p_per_layer": self.payload_p_per_layer,
            "space_s_per_layer": asdict(self.space_s_per_layer),
            "opening_o": asdict(self.opening_o),
            "footprint_a": asdict(self.footprint_a),
            "max_footprint_area": self.footprint_area(),
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


ComboValidator = Callable[[set[Module]], bool]


@dataclass(frozen=True)
class Rule:
    rule_id: str
    description: str
    validator: ComboValidator

    def check(self, combo: set[Module]) -> bool:
        return self.validator(combo)


class CombinationRules:
    def __init__(self, rules: list[Rule]) -> None:
        self.rules = rules

    @staticmethod
    def all_subsets(modules: Iterable[Module] | None = None) -> list[set[Module]]:
        universe = list(modules or list(Module))
        all_sets: list[set[Module]] = [set()]
        for size in range(1, len(universe) + 1):
            for subset in combinations(universe, size):
                all_sets.append(set(subset))
        return all_sets

    def valid_subsets(self, modules: Iterable[Module] | None = None) -> list[set[Module]]:
        candidates = self.all_subsets(modules)
        valid: list[set[Module]] = []

        for combo in candidates:
            if all(rule.check(combo) for rule in self.rules):
                valid.append(combo)

        return valid

    @staticmethod
    def default() -> "CombinationRules":
        return CombinationRules(
            rules=[
                Rule(
                    rule_id="C1",
                    description="integrated module contract: non-isolated set and panel requires rod+connector",
                    validator=lambda combo: (
                        len(combo) >= 2
                        and (
                            not ({Module.PANEL} <= combo)
                            or ({Module.ROD, Module.CONNECTOR} <= combo)
                        )
                    ),
                ),
            ]
        )


@dataclass(frozen=True)
class Hypothesis:
    hypothesis_id: str
    statement: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VerificationInput:
    boundary: BoundaryDefinition
    combo: set[Module]
    valid_combinations: list[set[Module]]
    baseline_efficiency: float
    target_efficiency: float
    extra_checks: dict[str, bool] = field(default_factory=dict)
    extra_check_messages: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class VerificationResult:
    boundary_valid: bool
    combination_valid: bool
    efficiency_improved: bool
    extra_checks_valid: bool
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
    extra_checks_valid = all(payload.extra_checks.values()) if payload.extra_checks else True

    reasons: list[str] = []
    reasons.extend(boundary_errors)
    if not combination_valid:
        reasons.append("combo is not in valid combinations")
    if not efficiency_improved:
        reasons.append("target_efficiency must be > baseline_efficiency")

    for check_id, passed in payload.extra_checks.items():
        if passed:
            continue
        reasons.append(payload.extra_check_messages.get(check_id, f"{check_id} failed"))

    return VerificationResult(
        boundary_valid=boundary_valid,
        combination_valid=combination_valid,
        efficiency_improved=efficiency_improved,
        extra_checks_valid=extra_checks_valid,
        passed=boundary_valid and combination_valid and efficiency_improved and extra_checks_valid,
        reasons=reasons,
    )


@dataclass(frozen=True)
class ShelfTypeSpec:
    type_id: int
    canonical_key: str
    group_id: str
    layer_masks: tuple[int, ...]
    layer_matrices: tuple[tuple[tuple[int, ...], ...], ...]
    active_cells_per_layer: tuple[int, ...]
    total_active_cells: int
    projection_ratio: float
    structural_checks: dict[str, bool]
    verification: VerificationResult

    @property
    def status(self) -> str:
        return "passed" if self.verification.passed else "failed"

    def to_dict(self) -> dict[str, Any]:
        effective_layers = 0
        for idx, mask in enumerate(self.layer_masks):
            if mask != 0:
                effective_layers = idx + 1
        declared_layers = len(self.layer_masks)
        return {
            "type_id": self.type_id,
            "canonical_key": self.canonical_key,
            "group_id": self.group_id,
            "layer_masks": list(self.layer_masks),
            "declared_layers": declared_layers,
            "effective_layers": effective_layers,
            "is_degenerate_single_layer": declared_layers > 1 and effective_layers <= 1,
            "active_cells_per_layer": list(self.active_cells_per_layer),
            "total_active_cells": self.total_active_cells,
            "projection_ratio": round(self.projection_ratio, 6),
            "status": self.status,
            "structural_checks": self.structural_checks,
            "verification": self.verification.to_dict(),
        }


def infer_grid_dimensions(footprint_area_cells: int) -> tuple[int, int]:
    if footprint_area_cells <= 0:
        raise ValueError("footprint_area_cells must be > 0")

    width = int(math.ceil(math.sqrt(footprint_area_cells)))
    depth = int(math.ceil(footprint_area_cells / width))
    if width < depth:
        width, depth = depth, width
    return width, depth


def mask_to_matrix(mask: int, grid_width: int, grid_depth: int) -> tuple[tuple[int, ...], ...]:
    rows: list[tuple[int, ...]] = []
    for row_idx in range(grid_depth):
        row: list[int] = []
        for col_idx in range(grid_width):
            bit_idx = row_idx * grid_width + col_idx
            row.append(1 if (mask >> bit_idx) & 1 else 0)
        rows.append(tuple(row))
    return tuple(rows)


def canonical_key(layer_masks: tuple[int, ...], cell_count: int) -> str:
    return "-".join(format(mask, f"0{cell_count}b") for mask in layer_masks)


def _mask_points(mask: int, grid_width: int) -> list[tuple[int, int]]:
    points: list[tuple[int, int]] = []
    bit_idx = 0
    temp = mask
    while temp:
        if temp & 1:
            points.append((bit_idx % grid_width, bit_idx // grid_width))
        temp >>= 1
        bit_idx += 1
    return points


def _canonical_shape(points: list[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    if not points:
        return tuple()

    transforms = (
        lambda x, y: (x, y),
        lambda x, y: (x, -y),
        lambda x, y: (-x, y),
        lambda x, y: (-x, -y),
        lambda x, y: (y, x),
        lambda x, y: (y, -x),
        lambda x, y: (-y, x),
        lambda x, y: (-y, -x),
    )

    normalized: list[tuple[tuple[int, int], ...]] = []
    for tf in transforms:
        transformed = [tf(x, y) for x, y in points]
        min_x = min(item[0] for item in transformed)
        min_y = min(item[1] for item in transformed)
        normalized.append(
            tuple(sorted((x - min_x, y - min_y) for x, y in transformed))
        )

    return min(normalized)


def _iter_submasks(mask: int) -> Iterable[int]:
    submask = mask
    while True:
        yield submask
        if submask == 0:
            break
        submask = (submask - 1) & mask


def _iter_nonempty_submasks(mask: int) -> Iterable[int]:
    for submask in _iter_submasks(mask):
        if submask != 0:
            yield submask


def enumerate_base_masks(
    footprint_area_cells: int,
    grid_width: int,
    grid_depth: int,
) -> list[int]:
    cell_count = grid_width * grid_depth
    signatures: set[tuple[tuple[int, int], ...]] = set()
    masks: list[int] = []

    for bits in combinations(range(cell_count), footprint_area_cells):
        mask = 0
        for bit in bits:
            mask |= 1 << bit

        if not is_layer_connector_bridge_connected(mask, grid_width, grid_depth):
            continue

        shape_key = _canonical_shape(_mask_points(mask, grid_width))
        if shape_key in signatures:
            continue
        signatures.add(shape_key)
        masks.append(mask)

    return masks


def projection_center(layer_masks: tuple[int, ...], grid_width: int) -> tuple[float, float] | None:
    x_sum = 0.0
    y_sum = 0.0
    weight = 0

    for mask in layer_masks:
        for bit_idx in range(mask.bit_length() or 1):
            if not ((mask >> bit_idx) & 1):
                continue
            x_sum += (bit_idx % grid_width) + 0.5
            y_sum += (bit_idx // grid_width) + 0.5
            weight += 1

    if weight == 0:
        return None

    return x_sum / weight, y_sum / weight


def is_layer_connected(mask: int, grid_width: int, grid_depth: int) -> bool:
    if mask == 0:
        return True

    active_bits = [bit for bit in range(grid_width * grid_depth) if (mask >> bit) & 1]
    if not active_bits:
        return True

    seen: set[int] = set()
    stack = [active_bits[0]]

    while stack:
        bit = stack.pop()
        if bit in seen:
            continue
        seen.add(bit)

        x = bit % grid_width
        y = bit // grid_width
        neighbors = (
            (x - 1, y),
            (x + 1, y),
            (x, y - 1),
            (x, y + 1),
        )

        for nx, ny in neighbors:
            if nx < 0 or ny < 0 or nx >= grid_width or ny >= grid_depth:
                continue
            nb = ny * grid_width + nx
            if ((mask >> nb) & 1) and nb not in seen:
                stack.append(nb)

    return len(seen) == len(active_bits)


def is_layer_connector_bridge_connected(mask: int, grid_width: int, grid_depth: int) -> bool:
    """8-neighborhood connectivity to model connector-assisted corner bridging."""
    if mask == 0:
        return True

    active_bits = [bit for bit in range(grid_width * grid_depth) if (mask >> bit) & 1]
    if not active_bits:
        return True

    seen: set[int] = set()
    stack = [active_bits[0]]

    while stack:
        bit = stack.pop()
        if bit in seen:
            continue
        seen.add(bit)

        x = bit % grid_width
        y = bit // grid_width
        for ny in range(y - 1, y + 2):
            for nx in range(x - 1, x + 2):
                if nx == x and ny == y:
                    continue
                if nx < 0 or ny < 0 or nx >= grid_width or ny >= grid_depth:
                    continue
                nb = ny * grid_width + nx
                if ((mask >> nb) & 1) and nb not in seen:
                    stack.append(nb)

    return len(seen) == len(active_bits)


def evaluate_structural_checks(
    layer_masks: tuple[int, ...],
    grid_width: int,
    grid_depth: int,
    combo: set[Module],
) -> dict[str, bool]:
    base_mask = layer_masks[0] if layer_masks else 0
    has_base = base_mask != 0

    # Rod-through support model:
    # Upper shelves are supported by vertical rods/interfaces, not by requiring
    # same-cell panel overlap with the immediate lower layer.
    # We only constrain active cells to remain inside base footprint.
    support_chain = all((mask & ~base_mask) == 0 for mask in layer_masks[1:])

    connected_layers = all(
        is_layer_connector_bridge_connected(
            mask,
            grid_width=grid_width,
            grid_depth=grid_depth,
        )
        for mask in layer_masks
        if mask != 0
    )

    upper_layer_engagement = (
        len(layer_masks) <= 1 or all(mask != 0 for mask in layer_masks[1:])
    )

    center = projection_center(layer_masks, grid_width)
    center_inside = False
    if center is not None:
        x, y = center
        center_inside = 0.0 <= x <= float(grid_width) and 0.0 <= y <= float(grid_depth)

    support_modules_ready = Module.ROD in combo and Module.CONNECTOR in combo
    panel_horizontal_only = Module.PANEL not in combo or support_modules_ready
    continuity = support_chain and connected_layers and panel_horizontal_only and support_modules_ready

    return {
        "C2_support_continuity": continuity,
        "C3_center_projection_stable": has_base and center_inside,
        "C4_upper_layer_engaged": upper_layer_engagement,
    }


def evaluate_boundary_checks(
    layer_masks: tuple[int, ...],
    boundary: BoundaryDefinition,
    footprint_area_cells: int,
) -> dict[str, bool]:
    max_layers_allowed = boundary.layers_n
    max_cells_allowed = int(boundary.footprint_area())

    active_layers = sum(1 for mask in layer_masks if mask != 0)
    base_cells = layer_masks[0].bit_count() if layer_masks else 0

    return {
        "B1_layers_within_limit": 0 < active_layers <= max_layers_allowed,
        "B2_fixed_footprint": (
            footprint_area_cells <= max_cells_allowed
            and base_cells == footprint_area_cells
            and all(mask.bit_count() <= base_cells for mask in layer_masks)
        ),
    }


def generate_shelf_type_specs(
    boundary: BoundaryDefinition,
    footprint_area_cells: int,
    max_layers: int,
    baseline_efficiency: float,
    rules: CombinationRules | None = None,
    combo: set[Module] | None = None,
) -> tuple[list[ShelfTypeSpec], dict[str, Any]]:
    if max_layers <= 0:
        raise ValueError("max_layers must be > 0")

    grid_width, grid_depth = infer_grid_dimensions(footprint_area_cells)
    cell_count = grid_width * grid_depth

    module_combo = combo or {Module.ROD, Module.CONNECTOR, Module.PANEL}
    combination_rules = rules or CombinationRules.default()
    valid_combinations = combination_rules.valid_subsets()

    check_messages = {
        "B1_layers_within_limit": "B1",
        "B2_fixed_footprint": "B2",
        "C2_support_continuity": "C2",
        "C3_center_projection_stable": "C3",
        "C4_upper_layer_engaged": "C4",
    }

    specs: list[ShelfTypeSpec] = []

    type_counter = 1
    base_masks_by_size: dict[int, list[int]] = {
        size: enumerate_base_masks(
            footprint_area_cells=size,
            grid_width=grid_width,
            grid_depth=grid_depth,
        )
        for size in range(1, cell_count + 1)
    }

    for base_size in range(1, cell_count + 1):
        for base_mask in base_masks_by_size[base_size]:
            for declared_layers in range(1, max_layers + 1):
                if declared_layers == 1:
                    upper_iter = (tuple(),)
                else:
                    upper_masks_pool = tuple(_iter_nonempty_submasks(base_mask))
                    upper_iter = product(upper_masks_pool, repeat=declared_layers - 1)
                for upper_masks in upper_iter:
                    layer_masks = (base_mask, *upper_masks)

                    structural_checks = evaluate_structural_checks(
                        layer_masks=layer_masks,
                        grid_width=grid_width,
                        grid_depth=grid_depth,
                        combo=module_combo,
                    )

                    boundary_checks = evaluate_boundary_checks(
                        layer_masks=layer_masks,
                        boundary=boundary,
                        footprint_area_cells=footprint_area_cells,
                    )
                    all_checks = {**boundary_checks, **structural_checks}

                    active_cells_per_layer = tuple(mask.bit_count() for mask in layer_masks)
                    total_active_cells = sum(active_cells_per_layer)
                    projection_ratio = total_active_cells / float(footprint_area_cells)

                    verification = verify(
                        VerificationInput(
                            boundary=boundary,
                            combo=module_combo,
                            valid_combinations=valid_combinations,
                            baseline_efficiency=baseline_efficiency,
                            target_efficiency=projection_ratio,
                            extra_checks=all_checks,
                            extra_check_messages=check_messages,
                        )
                    )

                    group_id = "G" + "-".join(str(count) for count in active_cells_per_layer)
                    specs.append(
                        ShelfTypeSpec(
                            type_id=type_counter,
                            canonical_key=canonical_key(layer_masks, cell_count),
                            group_id=group_id,
                            layer_masks=layer_masks,
                            layer_matrices=tuple(
                                mask_to_matrix(mask, grid_width=grid_width, grid_depth=grid_depth)
                                for mask in layer_masks
                            ),
                            active_cells_per_layer=active_cells_per_layer,
                            total_active_cells=total_active_cells,
                            projection_ratio=projection_ratio,
                            structural_checks=all_checks,
                            verification=verification,
                        )
                    )
                    type_counter += 1

    summary = summarize_shelf_type_specs(specs)
    meta = {
        "footprint_area_cells": footprint_area_cells,
        "grid_width": grid_width,
        "grid_depth": grid_depth,
        "cell_count": cell_count,
        "max_layers": max_layers,
        "baseline_efficiency": baseline_efficiency,
        "module_combo": modules_to_list(module_combo),
        "valid_combinations": [modules_to_list(item) for item in valid_combinations],
        "summary": summary,
    }

    return specs, meta


def summarize_shelf_type_specs(specs: list[ShelfTypeSpec]) -> dict[str, Any]:
    total = len(specs)
    passed = sum(1 for item in specs if item.status == "passed")
    failed = total - passed

    groups: dict[str, dict[str, Any]] = {}
    for item in specs:
        group = groups.setdefault(
            item.group_id,
            {
                "group_id": item.group_id,
                "active_cells_per_layer": list(item.active_cells_per_layer),
                "total": 0,
                "passed": 0,
                "failed": 0,
                "sample_type_ids": [],
            },
        )
        group["total"] += 1
        group[item.status] += 1
        if len(group["sample_type_ids"]) < 3:
            group["sample_type_ids"].append(item.type_id)

    ordered_groups = sorted(
        groups.values(),
        key=lambda g: (
            -g["total"],
            g["active_cells_per_layer"],
        ),
    )

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "groups": ordered_groups,
    }


@dataclass(frozen=True)
class LogicStep:
    step_id: str
    label: str
    depends_on: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LogicRecord:
    steps: list[LogicStep]

    @classmethod
    def build(cls, steps: list[LogicStep]) -> "LogicRecord":
        record = cls(steps=steps)
        result = record.validate_self_consistency()
        if not result["ok"]:
            errors = "; ".join(result["errors"])
            raise ValueError(f"logic record is inconsistent: {errors}")
        return record

    def validate_self_consistency(self) -> dict[str, Any]:
        seen: set[str] = set()
        errors: list[str] = []

        for step in self.steps:
            if step.step_id in seen:
                errors.append(f"duplicate step id: {step.step_id}")
            for dep in step.depends_on:
                if dep not in seen:
                    errors.append(
                        f"step {step.step_id} depends on missing or future step: {dep}"
                    )
            seen.add(step.step_id)

        return {"ok": len(errors) == 0, "errors": errors}

    def to_dict(self) -> dict[str, Any]:
        return {
            "steps": [step.to_dict() for step in self.steps],
            "self_consistency": self.validate_self_consistency(),
        }

    def export_json(self, path: str | Path) -> None:
        out_path = Path(path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def modules_to_list(combo: set[Module]) -> list[str]:
    return sorted(item.value for item in combo)


def strict_mapping_meta() -> dict[str, str]:
    return {
        "level": STRICT_MAPPING_LEVEL,
        "registry": STRICT_MAPPING_REGISTRY,
        "validation_command": STRICT_MAPPING_VALIDATION_COMMAND,
    }
