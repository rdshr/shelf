from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import json
from typing import Any, Callable, Generic, Iterable, TypeVar

T = TypeVar("T")
ComboValidator = Callable[[set[T]], bool]


@dataclass(frozen=True)
class Goal:
    statement: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Capability:
    capability_id: str
    statement: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Base:
    base_id: str
    label: str
    structure: str
    depends_on: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BoundaryItem:
    boundary_id: str
    statement: str
    measurable: bool = True
    verifiable: bool = True
    depends_on: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BoundaryDefinition:
    items: tuple[BoundaryItem, ...]

    def validate(self) -> tuple[bool, list[str]]:
        errors: list[str] = []
        if not self.items:
            errors.append("boundary must contain at least one boundary item")
        for item in self.items:
            if not item.boundary_id.strip():
                errors.append("boundary item id cannot be empty")
            if not item.statement.strip():
                errors.append(f"boundary item {item.boundary_id!r} statement cannot be empty")
            if not item.measurable:
                errors.append(f"boundary item {item.boundary_id!r} must be measurable")
            if not item.verifiable:
                errors.append(f"boundary item {item.boundary_id!r} must be verifiable")
        return len(errors) == 0, errors

    def to_dict(self) -> dict[str, Any]:
        return {"items": [item.to_dict() for item in self.items]}


@dataclass(frozen=True)
class Rule(Generic[T]):
    rule_id: str
    description: str
    validator: ComboValidator[T]

    def check(self, combo: set[T]) -> bool:
        return self.validator(combo)


class CombinationRules(Generic[T]):
    def __init__(self, rules: list[Rule[T]]) -> None:
        self.rules = rules

    @staticmethod
    def all_subsets(universe: Iterable[T]) -> list[set[T]]:
        items = list(universe)
        all_sets: list[set[T]] = [set()]
        for mask in range(1, 1 << len(items)):
            subset: set[T] = set()
            for idx, item in enumerate(items):
                if mask & (1 << idx):
                    subset.add(item)
            all_sets.append(subset)
        return all_sets

    def valid_subsets(self, universe: Iterable[T]) -> list[set[T]]:
        candidates = self.all_subsets(universe)
        return [combo for combo in candidates if all(rule.check(combo) for rule in self.rules)]


@dataclass(frozen=True)
class Hypothesis:
    hypothesis_id: str
    statement: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VerificationInput:
    subject: str
    pass_criteria: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    baseline: float | None = None
    target: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VerificationResult:
    passed: bool
    reasons: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def verify(payload: VerificationInput) -> VerificationResult:
    reasons: list[str] = []
    if not payload.subject.strip():
        reasons.append("verification subject cannot be empty")
    if not payload.pass_criteria:
        reasons.append("verification input must include at least one pass criterion")
    if payload.baseline is not None and payload.target is not None and payload.target <= payload.baseline:
        reasons.append("target must be > baseline when both are provided")
    return VerificationResult(
        passed=len(reasons) == 0,
        reasons=reasons,
        evidence=payload.evidence,
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
                    errors.append(f"step {step.step_id} depends on missing or future step: {dep}")
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
