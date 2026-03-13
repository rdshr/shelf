from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class FrameworkUpstreamRef:
    framework: str
    level: int
    module: int
    rules: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FrameworkCapabilityIR:
    capability_id: str
    name: str
    statement: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FrameworkNonResponsibilityIR:
    responsibility_id: str
    name: str
    statement: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FrameworkBoundaryIR:
    boundary_id: str
    name: str
    statement: str
    source_tokens: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FrameworkBaseIR:
    base_id: str
    name: str
    statement: str
    inline_expr: str
    source_tokens: tuple[str, ...]
    upstream_refs: tuple[FrameworkUpstreamRef, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_id": self.base_id,
            "name": self.name,
            "statement": self.statement,
            "inline_expr": self.inline_expr,
            "source_tokens": list(self.source_tokens),
            "upstream_refs": [item.to_dict() for item in self.upstream_refs],
        }


@dataclass(frozen=True)
class FrameworkRuleIR:
    rule_id: str
    name: str
    participant_bases: tuple[str, ...]
    combination: str
    output_capabilities: tuple[str, ...]
    invalid_conclusions: tuple[str, ...]
    boundary_bindings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FrameworkVerificationIR:
    verification_id: str
    name: str
    statement: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FrameworkModuleIR:
    framework: str
    level: int
    module: int
    path: str
    title_cn: str
    title_en: str
    intro: str
    capabilities: tuple[FrameworkCapabilityIR, ...]
    non_responsibilities: tuple[FrameworkNonResponsibilityIR, ...]
    boundaries: tuple[FrameworkBoundaryIR, ...]
    bases: tuple[FrameworkBaseIR, ...]
    rules: tuple[FrameworkRuleIR, ...]
    verifications: tuple[FrameworkVerificationIR, ...]

    @property
    def module_id(self) -> str:
        return f"{self.framework}.L{self.level}.M{self.module}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "framework": self.framework,
            "level": self.level,
            "module": self.module,
            "module_id": self.module_id,
            "path": self.path,
            "title_cn": self.title_cn,
            "title_en": self.title_en,
            "intro": self.intro,
            "capabilities": [item.to_dict() for item in self.capabilities],
            "non_responsibilities": [item.to_dict() for item in self.non_responsibilities],
            "boundaries": [item.to_dict() for item in self.boundaries],
            "bases": [item.to_dict() for item in self.bases],
            "rules": [item.to_dict() for item in self.rules],
            "verifications": [item.to_dict() for item in self.verifications],
        }


@dataclass(frozen=True)
class FrameworkRegistryIR:
    modules: tuple[FrameworkModuleIR, ...]

    def get_module(self, framework: str, level: int, module: int) -> FrameworkModuleIR:
        for item in self.modules:
            if item.framework == framework and item.level == level and item.module == module:
                return item
        raise KeyError(f"missing framework module: {framework}.L{level}.M{module}")

    def to_dict(self) -> dict[str, Any]:
        return {"modules": [item.to_dict() for item in self.modules]}
