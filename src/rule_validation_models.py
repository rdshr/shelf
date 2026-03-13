from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RuleValidationOutcome:
    rule_id: str
    name: str
    passed: bool
    reasons: tuple[str, ...] = ()
    evidence: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "passed": self.passed,
            "reasons": list(self.reasons),
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class RuleValidationSummary:
    module_id: str
    rules: tuple[RuleValidationOutcome, ...]

    @property
    def passed(self) -> bool:
        return self.passed_count == self.rule_count

    @property
    def passed_count(self) -> int:
        return sum(1 for item in self.rules if item.passed)

    @property
    def rule_count(self) -> int:
        return len(self.rules)

    def to_dict(self) -> dict[str, object]:
        return {
            "module_id": self.module_id,
            "passed": self.passed,
            "passed_count": self.passed_count,
            "rule_count": self.rule_count,
            "rules": [item.to_dict() for item in self.rules],
        }


@dataclass(frozen=True)
class ValidationReports:
    frontend: RuleValidationSummary | None = None
    knowledge_base: RuleValidationSummary | None = None

    @classmethod
    def empty(cls) -> "ValidationReports":
        return cls()

    @property
    def passed(self) -> bool:
        summaries = tuple(item for item in (self.frontend, self.knowledge_base) if item is not None)
        return all(item.passed for item in summaries)

    @property
    def passed_count(self) -> int:
        return sum(item.passed_count for item in (self.frontend, self.knowledge_base) if item is not None)

    @property
    def rule_count(self) -> int:
        return sum(item.rule_count for item in (self.frontend, self.knowledge_base) if item is not None)

    def summary_by_scope(self) -> dict[str, dict[str, object]]:
        payload: dict[str, dict[str, object]] = {}
        if self.frontend is not None:
            payload["frontend"] = {
                "passed": self.frontend.passed,
                "passed_count": self.frontend.passed_count,
                "rule_count": self.frontend.rule_count,
            }
        if self.knowledge_base is not None:
            payload["knowledge_base"] = {
                "passed": self.knowledge_base.passed,
                "passed_count": self.knowledge_base.passed_count,
                "rule_count": self.knowledge_base.rule_count,
            }
        return payload

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "overall": {
                "passed": self.passed,
                "passed_count": self.passed_count,
                "rule_count": self.rule_count,
            }
        }
        if self.frontend is not None:
            payload["frontend"] = self.frontend.to_dict()
        if self.knowledge_base is not None:
            payload["knowledge_base"] = self.knowledge_base.to_dict()
        return payload
