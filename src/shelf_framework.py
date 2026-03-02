from __future__ import annotations

from collections import deque
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

CONTOUR_ALIGNMENT_TOLERANCE = 5.0


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

    def area(self) -> float:
        return self.width * self.depth


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

        if (
            self.opening_o.width > self.space_s_per_layer.width
            or self.opening_o.height > self.space_s_per_layer.height
        ):
            errors.append("opening_o must fit within space_s_per_layer")

        return (len(errors) == 0, errors)

    def max_layer_area(self) -> float:
        return min(
            self.space_s_per_layer.width * self.space_s_per_layer.depth,
            self.footprint_a.area(),
        )

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


class SupportKind(str, Enum):
    ROD = "rod"
    EQUIVALENT = "equivalent_support"


class SupportOrientation(str, Enum):
    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"
    ANGLED = "angled"


class ConnectorPlacement(str, Enum):
    CORNER = "corner"
    PREDEFINED_SLOT = "predefined_slot"
    CUSTOM = "custom"


@dataclass(frozen=True)
class OpeningPreference:
    preferred_direction: str
    min_ratio: float
    max_ratio: float

    def is_valid(self) -> bool:
        return (
            self.min_ratio > 0
            and self.max_ratio > 0
            and self.min_ratio <= self.max_ratio
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SupportUnit:
    support_id: str
    kind: SupportKind
    orientation: SupportOrientation = SupportOrientation.VERTICAL

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PanelLayer:
    panel_id: str
    level_index: int
    width: float
    depth: float
    layer_height: float
    opening: Opening2D
    support_unit_ids: tuple[str, ...]
    normal_axis: str = "z"
    contour_offset: float = 0.0

    def area(self) -> float:
        return self.width * self.depth

    def opening_ratio(self) -> float:
        if self.width <= 0:
            return 0.0
        return self.opening.width / self.width

    def is_valid(self) -> bool:
        return (
            self.level_index >= 1
            and self.width > 0
            and self.depth > 0
            and self.layer_height > 0
            and self.opening.is_valid()
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ConnectorUnit:
    connector_id: str
    placement: ConnectorPlacement = ConnectorPlacement.CUSTOM

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RodPanelConnection:
    support_unit_id: str
    panel_id: str
    connector_id: str | None
    uses_defined_interface: bool
    illegal_intersection: bool = False
    floating: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ShelfStructure:
    layers: tuple[PanelLayer, ...]
    support_units: tuple[SupportUnit, ...]
    connectors: tuple[ConnectorUnit, ...]
    connections: tuple[RodPanelConnection, ...]
    opening_direction: str = "front"

    def panel_map(self) -> dict[str, PanelLayer]:
        return {item.panel_id: item for item in self.layers}

    def support_map(self) -> dict[str, SupportUnit]:
        return {item.support_id: item for item in self.support_units}

    def connector_map(self) -> dict[str, ConnectorUnit]:
        return {item.connector_id: item for item in self.connectors}

    def node_ids(self) -> set[str]:
        return (
            {item.panel_id for item in self.layers}
            | {item.support_id for item in self.support_units}
            | {item.connector_id for item in self.connectors}
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RuleContext:
    combo: set[Module]
    boundary: BoundaryDefinition | None = None
    structure: ShelfStructure | None = None
    opening_preference: OpeningPreference | None = None


RuleValidator = Callable[[RuleContext], bool]


@dataclass(frozen=True)
class Rule:
    rule_id: str
    description: str
    validator: RuleValidator
    mandatory: bool
    scope: str
    deletable: bool = False

    def check(self, context: RuleContext) -> bool:
        return self.validator(context)


@dataclass(frozen=True)
class RuleDeletionAssessment:
    rule_id: str
    mandatory: bool
    baseline_passed: bool
    passed_after_removal: bool
    target_not_degraded: bool
    removable: bool
    mandatory_conflict: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _rule_r1(context: RuleContext) -> bool:
    return len(context.combo) >= 2


def _rule_r2(context: RuleContext) -> bool:
    return Module.CONNECTOR in context.combo


def _require_structure_context(
    context: RuleContext,
) -> tuple[ShelfStructure, BoundaryDefinition] | None:
    if context.structure is None or context.boundary is None:
        return None
    return (context.structure, context.boundary)


def _rule_e1(context: RuleContext) -> bool:
    scoped = _require_structure_context(context)
    if scoped is None:
        return False
    structure, _boundary = scoped
    if len(structure.layers) < 2:
        return False
    normals = {layer.normal_axis for layer in structure.layers}
    return len(normals) == 1


def _rule_e2(context: RuleContext) -> bool:
    scoped = _require_structure_context(context)
    if scoped is None:
        return False
    structure, _boundary = scoped
    support_map = structure.support_map()

    for layer in structure.layers:
        if len(layer.support_unit_ids) < 2:
            return False
        for support_id in layer.support_unit_ids:
            support = support_map.get(support_id)
            if support is None:
                return False
            if support.kind not in (SupportKind.ROD, SupportKind.EQUIVALENT):
                return False
    return True


def _rule_e3(context: RuleContext) -> bool:
    scoped = _require_structure_context(context)
    if scoped is None:
        return False
    structure, _boundary = scoped
    panel_map = structure.panel_map()
    support_map = structure.support_map()
    connector_map = structure.connector_map()

    for connection in structure.connections:
        panel = panel_map.get(connection.panel_id)
        support = support_map.get(connection.support_unit_id)
        if panel is None or support is None:
            return False
        if support.kind in (SupportKind.ROD, SupportKind.EQUIVALENT):
            if not connection.connector_id:
                return False
            if connection.connector_id not in connector_map:
                return False
    return True


def _rule_e4(context: RuleContext) -> bool:
    scoped = _require_structure_context(context)
    if scoped is None:
        return False
    structure, _boundary = scoped
    node_ids = structure.node_ids()
    if not node_ids:
        return False

    graph: dict[str, set[str]] = {node_id: set() for node_id in node_ids}
    for connection in structure.connections:
        connector_id = connection.connector_id
        if (
            not connector_id
            or connection.support_unit_id not in graph
            or connection.panel_id not in graph
            or connector_id not in graph
        ):
            continue
        graph[connection.support_unit_id].add(connector_id)
        graph[connector_id].add(connection.support_unit_id)
        graph[connector_id].add(connection.panel_id)
        graph[connection.panel_id].add(connector_id)

    start = next(iter(node_ids))
    visited: set[str] = set()
    queue: deque[str] = deque([start])
    while queue:
        node = queue.popleft()
        if node in visited:
            continue
        visited.add(node)
        for nxt in graph[node]:
            if nxt not in visited:
                queue.append(nxt)

    return visited == node_ids


def _rule_e5(context: RuleContext) -> bool:
    scoped = _require_structure_context(context)
    if scoped is None:
        return False
    structure, boundary = scoped
    if len(structure.layers) != boundary.layers_n:
        return False

    max_layer_height = boundary.space_s_per_layer.height
    max_layer_area = boundary.max_layer_area()

    for layer in structure.layers:
        if not layer.is_valid():
            return False
        if layer.layer_height > max_layer_height:
            return False
        if layer.area() > max_layer_area:
            return False
        if layer.opening.width > boundary.opening_o.width:
            return False
        if layer.opening.height > boundary.opening_o.height:
            return False
    return True


def _rule_e6(context: RuleContext) -> bool:
    scoped = _require_structure_context(context)
    if scoped is None:
        return False
    structure, _boundary = scoped

    for connection in structure.connections:
        if not connection.uses_defined_interface:
            return False
        if connection.illegal_intersection:
            return False
        if connection.floating:
            return False
    return True


def _rule_s1(context: RuleContext) -> bool:
    scoped = _require_structure_context(context)
    if scoped is None:
        return False
    structure, _boundary = scoped
    return all(
        support.orientation == SupportOrientation.VERTICAL
        for support in structure.support_units
    )


def _rule_s2(context: RuleContext) -> bool:
    scoped = _require_structure_context(context)
    if scoped is None:
        return False
    structure, _boundary = scoped
    return all(len(layer.support_unit_ids) == 4 for layer in structure.layers)


def _rule_s3(context: RuleContext) -> bool:
    scoped = _require_structure_context(context)
    if scoped is None:
        return False
    structure, _boundary = scoped
    return all(
        connector.placement in (ConnectorPlacement.CORNER, ConnectorPlacement.PREDEFINED_SLOT)
        for connector in structure.connectors
    )


def _rule_s4(context: RuleContext) -> bool:
    scoped = _require_structure_context(context)
    if scoped is None:
        return False
    structure, _boundary = scoped
    if not structure.layers:
        return False
    offsets = [layer.contour_offset for layer in structure.layers]
    return (max(offsets) - min(offsets)) <= CONTOUR_ALIGNMENT_TOLERANCE


def _rule_s5(context: RuleContext) -> bool:
    scoped = _require_structure_context(context)
    if scoped is None:
        return False
    structure, _boundary = scoped
    preference = context.opening_preference
    if preference is None or not preference.is_valid():
        return False
    if structure.opening_direction != preference.preferred_direction:
        return False

    for layer in structure.layers:
        ratio = layer.opening_ratio()
        if ratio < preference.min_ratio or ratio > preference.max_ratio:
            return False
    return True


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

    def _select_rules(
        self,
        scopes: set[str],
        disabled_rule_ids: set[str] | None = None,
        include_recommended: bool = True,
    ) -> list[Rule]:
        disabled = disabled_rule_ids or set()
        selected: list[Rule] = []

        for rule in self.rules:
            if rule.rule_id in disabled:
                continue
            if rule.scope not in scopes:
                continue
            if not include_recommended and not rule.mandatory:
                continue
            selected.append(rule)

        return selected

    def valid_subsets(self, modules: Iterable[Module] | None = None) -> list[set[Module]]:
        candidates = self.all_subsets(modules)
        combo_rules = self._select_rules(scopes={"combo"}, include_recommended=False)
        valid: list[set[Module]] = []

        for combo in candidates:
            context = RuleContext(combo=combo)
            if all(rule.check(context) for rule in combo_rules):
                valid.append(combo)

        return valid

    def evaluate_rules(
        self,
        context: RuleContext,
        disabled_rule_ids: set[str] | None = None,
        include_recommended: bool = True,
    ) -> dict[str, bool]:
        selected = self._select_rules(
            scopes={"combo", "structure"},
            disabled_rule_ids=disabled_rule_ids,
            include_recommended=include_recommended,
        )
        return {rule.rule_id: rule.check(context) for rule in selected}

    def overall_pass(self, rule_results: dict[str, bool]) -> bool:
        for rule in self.rules:
            if not rule.mandatory:
                continue
            if rule.rule_id not in rule_results:
                continue
            if not rule_results[rule.rule_id]:
                return False
        return True

    def rule_by_id(self, rule_id: str) -> Rule | None:
        for rule in self.rules:
            if rule.rule_id == rule_id:
                return rule
        return None

    def failed_rule_ids(
        self,
        rule_results: dict[str, bool],
        mandatory_only: bool,
    ) -> list[str]:
        failed: list[str] = []
        for rule in self.rules:
            if rule.rule_id not in rule_results:
                continue
            if mandatory_only and not rule.mandatory:
                continue
            if not mandatory_only and rule.mandatory:
                continue
            if not rule_results[rule.rule_id]:
                failed.append(rule.rule_id)
        return failed

    def assess_rule_deletions(
        self,
        context: RuleContext,
        baseline_efficiency: float,
        target_efficiency: float,
        include_recommended: bool = True,
    ) -> list[RuleDeletionAssessment]:
        baseline_results = self.evaluate_rules(context, include_recommended=include_recommended)
        target_not_degraded = target_efficiency >= baseline_efficiency
        baseline_passed = self.overall_pass(baseline_results) and target_not_degraded
        assessments: list[RuleDeletionAssessment] = []

        for rule in self._select_rules(
            scopes={"combo", "structure"},
            include_recommended=include_recommended,
        ):
            reduced_results = self.evaluate_rules(
                context,
                disabled_rule_ids={rule.rule_id},
                include_recommended=include_recommended,
            )
            passed_after_removal = self.overall_pass(reduced_results) and target_not_degraded
            removable = rule.deletable and passed_after_removal
            assessments.append(
                RuleDeletionAssessment(
                    rule_id=rule.rule_id,
                    mandatory=rule.mandatory,
                    baseline_passed=baseline_passed,
                    passed_after_removal=passed_after_removal,
                    target_not_degraded=target_not_degraded,
                    removable=removable,
                    mandatory_conflict=rule.mandatory and rule.deletable and removable,
                )
            )

        return assessments

    @staticmethod
    def default() -> "CombinationRules":
        return CombinationRules(
            rules=[
                Rule(
                    rule_id="R1",
                    description="combination must contain at least 2 modules",
                    validator=_rule_r1,
                    mandatory=True,
                    scope="combo",
                ),
                Rule(
                    rule_id="R2",
                    description="connector must exist in every usable combination",
                    validator=_rule_r2,
                    mandatory=True,
                    scope="combo",
                ),
                Rule(
                    rule_id="E1",
                    description="at least two parallel panels are required",
                    validator=_rule_e1,
                    mandatory=True,
                    scope="structure",
                ),
                Rule(
                    rule_id="E2",
                    description="each panel must connect to at least two support units",
                    validator=_rule_e2,
                    mandatory=True,
                    scope="structure",
                ),
                Rule(
                    rule_id="E3",
                    description="rod-panel connection must go through connector",
                    validator=_rule_e3,
                    mandatory=True,
                    scope="structure",
                ),
                Rule(
                    rule_id="E4",
                    description="structure graph must be single connected",
                    validator=_rule_e4,
                    mandatory=True,
                    scope="structure",
                ),
                Rule(
                    rule_id="E5",
                    description="layer count, height and area must be within boundary",
                    validator=_rule_e5,
                    mandatory=True,
                    scope="structure",
                ),
                Rule(
                    rule_id="E6",
                    description="forbid undefined penetration, illegal intersection, floating connection",
                    validator=_rule_e6,
                    mandatory=True,
                    scope="structure",
                ),
                Rule(
                    rule_id="S1",
                    description="prefer vertical relationship between rod and panel",
                    validator=_rule_s1,
                    mandatory=False,
                    scope="structure",
                    deletable=True,
                ),
                Rule(
                    rule_id="S2",
                    description="prefer four support points per layer",
                    validator=_rule_s2,
                    mandatory=False,
                    scope="structure",
                    deletable=True,
                ),
                Rule(
                    rule_id="S3",
                    description="prefer connector on corners or predefined slots",
                    validator=_rule_s3,
                    mandatory=False,
                    scope="structure",
                    deletable=True,
                ),
                Rule(
                    rule_id="S4",
                    description="prefer aligned contour across layers",
                    validator=_rule_s4,
                    mandatory=False,
                    scope="structure",
                    deletable=True,
                ),
                Rule(
                    rule_id="S5",
                    description="opening direction and ratio follow scenario preference",
                    validator=_rule_s5,
                    mandatory=False,
                    scope="structure",
                    deletable=True,
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
    structure: ShelfStructure
    rules: CombinationRules | None = None
    opening_preference: OpeningPreference | None = None
    disabled_rules: tuple[str, ...] = ()
    include_recommended_rules: bool = True


@dataclass(frozen=True)
class VerificationResult:
    boundary_valid: bool
    combination_valid: bool
    efficiency_improved: bool
    mandatory_rules_passed: bool
    passed: bool
    reasons: list[str] = field(default_factory=list)
    rule_results: dict[str, bool] = field(default_factory=dict)
    deletion_assessment: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def verify(payload: VerificationInput) -> VerificationResult:
    boundary_valid, boundary_errors = payload.boundary.validate()
    combo_key = frozenset(payload.combo)
    valid_set = {frozenset(item) for item in payload.valid_combinations}
    combination_valid = combo_key in valid_set
    efficiency_improved = payload.target_efficiency > payload.baseline_efficiency

    rules_engine = payload.rules or CombinationRules.default()
    context = RuleContext(
        combo=set(payload.combo),
        boundary=payload.boundary,
        structure=payload.structure,
        opening_preference=payload.opening_preference,
    )
    rule_results = rules_engine.evaluate_rules(
        context,
        disabled_rule_ids=set(payload.disabled_rules),
        include_recommended=payload.include_recommended_rules,
    )
    mandatory_rules_passed = rules_engine.overall_pass(rule_results)
    deletion_assessment = [
        item.to_dict()
        for item in rules_engine.assess_rule_deletions(
            context,
            baseline_efficiency=payload.baseline_efficiency,
            target_efficiency=payload.target_efficiency,
            include_recommended=payload.include_recommended_rules,
        )
    ]

    reasons: list[str] = []
    reasons.extend(boundary_errors)
    if not combination_valid:
        reasons.append("combo is not in valid combinations")
    if not efficiency_improved:
        reasons.append("target_efficiency must be > baseline_efficiency")

    for rule_id in rules_engine.failed_rule_ids(rule_results, mandatory_only=True):
        rule = rules_engine.rule_by_id(rule_id)
        if rule is not None:
            reasons.append(f"mandatory rule {rule.rule_id} failed: {rule.description}")

    for rule_id in rules_engine.failed_rule_ids(rule_results, mandatory_only=False):
        rule = rules_engine.rule_by_id(rule_id)
        if rule is not None:
            reasons.append(f"recommended rule {rule.rule_id} not met: {rule.description}")

    for item in deletion_assessment:
        if item["mandatory_conflict"]:
            reasons.append(
                "mandatory rule removal conflict: "
                f"{item['rule_id']} can be removed without target degradation"
            )

    return VerificationResult(
        boundary_valid=boundary_valid,
        combination_valid=combination_valid,
        efficiency_improved=efficiency_improved,
        mandatory_rules_passed=mandatory_rules_passed,
        passed=boundary_valid and combination_valid and efficiency_improved and mandatory_rules_passed,
        reasons=reasons,
        rule_results=rule_results,
        deletion_assessment=deletion_assessment,
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
