from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from itertools import combinations
import json
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
                    rule_id="R1",
                    description="module set must not be isolated",
                    validator=lambda combo: len(combo) >= 2,
                ),
                Rule(
                    rule_id="R2",
                    description="connector must exist in every usable combination",
                    validator=lambda combo: Module.CONNECTOR in combo,
                ),
            ]
        )


@dataclass(frozen=True)
class ShelfCombination:
    combination_id: str
    layers_n: int
    # Each layer is a set of unit panel cells represented as (x, y).
    # Upper layer cells must be a subset of lower layer cells.
    layer_cells: tuple[tuple[tuple[int, int], ...], ...]
    panel_unit_area: float = 1.0
    module_combo: frozenset[Module] = field(
        default_factory=lambda: frozenset({Module.ROD, Module.CONNECTOR, Module.PANEL})
    )

    def _layer_cell_sets(self) -> list[set[tuple[int, int]]]:
        return [set(layer) for layer in self.layer_cells]

    def footprint_cells(self) -> set[tuple[int, int]]:
        cells: set[tuple[int, int]] = set()
        for layer in self._layer_cell_sets():
            cells.update(layer)
        return cells

    def footprint_width_units(self) -> int:
        cells = self.footprint_cells()
        if not cells:
            return 0
        return max(x for x, _y in cells) + 1

    def footprint_depth_units(self) -> int:
        cells = self.footprint_cells()
        if not cells:
            return 0
        return max(y for _x, y in cells) + 1

    def footprint_area_units(self) -> int:
        return len(self.footprint_cells())

    def footprint_area(self) -> float:
        return self.footprint_area_units() * self.panel_unit_area

    def panel_count_per_layer(self) -> int:
        if not self.layer_cells:
            return 0
        return len(self.layer_cells[0])

    def total_panel_count(self) -> int:
        return sum(len(layer) for layer in self.layer_cells)

    def target_efficiency(self) -> float:
        footprint = self.footprint_area()
        if footprint <= 0:
            return 0.0
        return self.total_panel_count() / footprint

    def rod_points(self) -> set[tuple[int, int]]:
        points: set[tuple[int, int]] = set()
        for x, y in self.footprint_cells():
            points.add((x, y))
            points.add((x + 1, y))
            points.add((x + 1, y + 1))
            points.add((x, y + 1))
        return points

    def rod_connection_heights(self) -> dict[tuple[int, int], int]:
        heights: dict[tuple[int, int], int] = {}
        for x, y, z in self.panel_cells():
            for corner in ((x, y), (x + 1, y), (x + 1, y + 1), (x, y + 1)):
                heights[corner] = max(heights.get(corner, 0), z)
        return heights

    def panel_cells(self) -> list[tuple[int, int, int]]:
        cells: list[tuple[int, int, int]] = []
        for z, layer in enumerate(self.layer_cells, start=1):
            for x, y in layer:
                cells.append((x, y, z))
        return cells

    def to_dict(self) -> dict[str, Any]:
        layer_areas = [len(layer) for layer in self.layer_cells]
        return {
            "combination_id": self.combination_id,
            "layers_n": self.layers_n,
            "footprint_width_units": self.footprint_width_units(),
            "footprint_depth_units": self.footprint_depth_units(),
            "panel_unit_area": self.panel_unit_area,
            "module_combo": sorted(module.value for module in self.module_combo),
            "footprint_area_units": self.footprint_area_units(),
            "footprint_area": self.footprint_area(),
            "panel_count_per_layer": self.panel_count_per_layer(),
            "total_panel_count": self.total_panel_count(),
            "layer_areas": layer_areas,
            "layer_shapes": [
                [[x, y] for x, y in sorted(layer)]
                for layer in self.layer_cells
            ],
            "target_efficiency": self.target_efficiency(),
        }


def _normalize_shape(shape: set[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    min_x = min(x for x, _y in shape)
    min_y = min(y for _x, y in shape)
    normalized = sorted((x - min_x, y - min_y) for x, y in shape)
    return tuple(normalized)


def _is_connected(shape: set[tuple[int, int]]) -> bool:
    if not shape:
        return False
    stack = [next(iter(shape))]
    visited: set[tuple[int, int]] = set()
    while stack:
        x, y = stack.pop()
        if (x, y) in visited:
            continue
        visited.add((x, y))
        for nxt in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if nxt in shape and nxt not in visited:
                stack.append(nxt)
    return len(visited) == len(shape)


def _all_connected_shapes(max_area: int) -> list[tuple[tuple[int, int], ...]]:
    by_size: dict[int, set[tuple[tuple[int, int], ...]]] = {1: {((0, 0),)}}
    for size in range(2, max_area + 1):
        next_shapes: set[tuple[tuple[int, int], ...]] = set()
        for shape in by_size[size - 1]:
            shape_set = set(shape)
            frontier: set[tuple[int, int]] = set()
            for x, y in shape_set:
                frontier.update({(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)})
            frontier -= shape_set
            for cell in frontier:
                candidate = set(shape_set)
                candidate.add(cell)
                if _is_connected(candidate):
                    next_shapes.add(_normalize_shape(candidate))
        by_size[size] = next_shapes

    all_shapes: list[tuple[tuple[int, int], ...]] = []
    for size in range(1, max_area + 1):
        all_shapes.extend(sorted(by_size.get(size, set())))
    return all_shapes


def _shape_code(shape: tuple[tuple[int, int], ...]) -> str:
    return "_".join(f"{x}{y}" for x, y in shape)


def generate_shelf_combinations(
    max_layers_n: int,
    max_footprint_area: int,
    panel_unit_area: float = 1.0,
) -> list[ShelfCombination]:
    combinations_all: list[ShelfCombination] = []
    all_shapes = _all_connected_shapes(max_footprint_area)
    shape_sets = [set(shape) for shape in all_shapes]
    shape_items = list(zip(all_shapes, shape_sets))

    if max_layers_n <= 0:
        return []

    def emit_sequence(layer_sequence: list[tuple[tuple[int, int], ...]]) -> None:
        layer_cells = tuple(tuple(sorted(shape)) for shape in layer_sequence)
        combo_id_parts = [
            f"A{len(shape)}-{_shape_code(shape)}" for shape in layer_sequence
        ]
        combinations_all.append(
            ShelfCombination(
                combination_id=f"L{len(layer_sequence)}-" + "-".join(combo_id_parts),
                layers_n=len(layer_sequence),
                layer_cells=layer_cells,
                panel_unit_area=panel_unit_area,
            )
        )

    def walk_layers(
        current_layers: list[tuple[tuple[int, int], ...]],
        current_set: set[tuple[int, int]],
        target_layers: int,
    ) -> None:
        if len(current_layers) == target_layers:
            emit_sequence(current_layers)
            return
        for next_shape, next_set in shape_items:
            if next_set.issubset(current_set):
                walk_layers(
                    current_layers + [next_shape],
                    next_set,
                    target_layers,
                )

    for layers_n in range(1, max_layers_n + 1):
        for base_shape, base_set in shape_items:
            walk_layers([base_shape], base_set, layers_n)

    return sorted(
        combinations_all,
        key=lambda item: (
            item.layers_n,
            item.footprint_area_units(),
            item.total_panel_count(),
            item.combination_id,
        ),
    )


def validate_r3_orthogonality(structure: ShelfCombination) -> tuple[bool, str]:
    if structure.layers_n <= 0:
        return False, "R3 failed: layers_n must be > 0"
    if structure.footprint_width_units() <= 0 or structure.footprint_depth_units() <= 0:
        return False, "R3 failed: footprint dimensions must be > 0"
    if len(structure.layer_cells) != structure.layers_n:
        return False, "R3 failed: layer_cells count must equal layers_n"
    layer_sets = structure._layer_cell_sets()
    for idx in range(1, len(layer_sets)):
        if not layer_sets[idx].issubset(layer_sets[idx - 1]):
            return False, "R3 failed: upper layer footprint must be subset of lower layer"
    return True, "R3 passed"


def validate_r4_panel_parallel(structure: ShelfCombination) -> tuple[bool, str]:
    panel_cells = structure.panel_cells()
    if not panel_cells:
        return False, "R4 failed: no panel exists"
    rod_points = structure.rod_points()
    for x, y, _z in panel_cells:
        corners = ((x, y), (x + 1, y), (x + 1, y + 1), (x, y + 1))
        if len(set(corners)) != 4:
            return False, "R4 failed: panel corner points are not unique"
        if any(corner not in rod_points for corner in corners):
            return False, "R4 failed: panel corners are not fully connected to rods"
    return True, "R4 passed"


def validate_r5_panel_corner_connections(structure: ShelfCombination) -> tuple[bool, str]:
    if structure.layers_n < 2:
        return False, "R5 failed: layers_n must be >= 2"
    return True, "R5 passed"


def validate_combination_principles(
    structure: ShelfCombination, rules: CombinationRules
) -> tuple[bool, list[str]]:
    reasons: list[str] = []

    module_combo = set(structure.module_combo)
    for rule in rules.rules:
        if not rule.check(module_combo):
            reasons.append(f"{rule.rule_id} failed: {rule.description}")

    checks = (
        validate_r3_orthogonality(structure),
        validate_r4_panel_parallel(structure),
        validate_r5_panel_corner_connections(structure),
    )
    for passed, message in checks:
        if not passed:
            reasons.append(message)

    return (len(reasons) == 0, reasons)


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
    geometry_principles_valid: bool = True
    geometry_errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class VerificationResult:
    boundary_valid: bool
    combination_valid: bool
    geometry_principles_valid: bool
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
    geometry_principles_valid = payload.geometry_principles_valid
    efficiency_improved = payload.target_efficiency > payload.baseline_efficiency

    reasons: list[str] = []
    reasons.extend(boundary_errors)
    if not combination_valid:
        reasons.append("combo is not in valid combinations")
    if not geometry_principles_valid:
        reasons.append("combination principles R3/R4/R5 failed")
        reasons.extend(payload.geometry_errors)
    if not efficiency_improved:
        reasons.append("target_efficiency must be > baseline_efficiency")

    return VerificationResult(
        boundary_valid=boundary_valid,
        combination_valid=combination_valid,
        geometry_principles_valid=geometry_principles_valid,
        efficiency_improved=efficiency_improved,
        passed=boundary_valid
        and combination_valid
        and geometry_principles_valid
        and efficiency_improved,
        reasons=reasons,
    )


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

