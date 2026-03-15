from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class FrameworkSourceRef:
    file_path: str
    line: int
    section: str
    anchor: str
    token: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FrameworkUpstreamLink:
    framework: str
    level: int
    module: int
    rules: tuple[str, ...]

    @property
    def module_id(self) -> str:
        return f"{self.framework}.L{self.level}.M{self.module}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FrameworkCapability:
    capability_id: str
    name: str
    statement: str
    source_ref: FrameworkSourceRef

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "name": self.name,
            "statement": self.statement,
            "source_ref": self.source_ref.to_dict(),
        }


@dataclass(frozen=True)
class FrameworkNonResponsibility:
    responsibility_id: str
    name: str
    statement: str
    source_ref: FrameworkSourceRef

    def to_dict(self) -> dict[str, Any]:
        return {
            "responsibility_id": self.responsibility_id,
            "name": self.name,
            "statement": self.statement,
            "source_ref": self.source_ref.to_dict(),
        }


@dataclass(frozen=True)
class FrameworkBoundary:
    boundary_id: str
    name: str
    statement: str
    source_tokens: tuple[str, ...]
    source_ref: FrameworkSourceRef

    def to_dict(self) -> dict[str, Any]:
        return {
            "boundary_id": self.boundary_id,
            "name": self.name,
            "statement": self.statement,
            "source_tokens": list(self.source_tokens),
            "source_ref": self.source_ref.to_dict(),
        }


@dataclass(frozen=True)
class FrameworkBase:
    base_id: str
    name: str
    statement: str
    inline_expr: str
    source_tokens: tuple[str, ...]
    upstream_links: tuple[FrameworkUpstreamLink, ...]
    source_ref: FrameworkSourceRef

    @property
    def upstream_refs(self) -> tuple[FrameworkUpstreamLink, ...]:
        return self.upstream_links

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_id": self.base_id,
            "name": self.name,
            "statement": self.statement,
            "inline_expr": self.inline_expr,
            "source_tokens": list(self.source_tokens),
            "upstream_links": [item.to_dict() for item in self.upstream_links],
            "source_ref": self.source_ref.to_dict(),
        }


@dataclass(frozen=True)
class FrameworkRule:
    rule_id: str
    name: str
    participant_bases: tuple[str, ...]
    combination: str
    output_capabilities: tuple[str, ...]
    invalid_conclusions: tuple[str, ...]
    boundary_bindings: tuple[str, ...]
    source_ref: FrameworkSourceRef

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "participant_bases": list(self.participant_bases),
            "combination": self.combination,
            "output_capabilities": list(self.output_capabilities),
            "invalid_conclusions": list(self.invalid_conclusions),
            "boundary_bindings": list(self.boundary_bindings),
            "source_ref": self.source_ref.to_dict(),
        }


@dataclass(frozen=True)
class FrameworkVerification:
    verification_id: str
    name: str
    statement: str
    source_ref: FrameworkSourceRef

    def to_dict(self) -> dict[str, Any]:
        return {
            "verification_id": self.verification_id,
            "name": self.name,
            "statement": self.statement,
            "source_ref": self.source_ref.to_dict(),
        }


@dataclass(frozen=True)
class FrameworkModuleExport:
    module_id: str
    path: str
    title_cn: str
    title_en: str
    intro: str
    capability_ids: tuple[str, ...]
    boundary_ids: tuple[str, ...]
    base_ids: tuple[str, ...]
    rule_ids: tuple[str, ...]
    verification_ids: tuple[str, ...]
    upstream_module_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "module_id": self.module_id,
            "path": self.path,
            "title_cn": self.title_cn,
            "title_en": self.title_en,
            "intro": self.intro,
            "capability_ids": list(self.capability_ids),
            "boundary_ids": list(self.boundary_ids),
            "base_ids": list(self.base_ids),
            "rule_ids": list(self.rule_ids),
            "verification_ids": list(self.verification_ids),
            "upstream_module_ids": list(self.upstream_module_ids),
        }


@dataclass(frozen=True)
class FrameworkModule:
    framework: str
    level: int
    module: int
    path: str
    title_cn: str
    title_en: str
    intro: str
    capabilities: tuple[FrameworkCapability, ...]
    non_responsibilities: tuple[FrameworkNonResponsibility, ...]
    boundaries: tuple[FrameworkBoundary, ...]
    bases: tuple[FrameworkBase, ...]
    rules: tuple[FrameworkRule, ...]
    verifications: tuple[FrameworkVerification, ...]
    source_ref: FrameworkSourceRef

    @property
    def module_id(self) -> str:
        return f"{self.framework}.L{self.level}.M{self.module}"

    def export_surface(self) -> FrameworkModuleExport:
        upstream_module_ids = tuple(
            sorted({link.module_id for base in self.bases for link in base.upstream_links})
        )
        return FrameworkModuleExport(
            module_id=self.module_id,
            path=self.path,
            title_cn=self.title_cn,
            title_en=self.title_en,
            intro=self.intro,
            capability_ids=tuple(item.capability_id for item in self.capabilities),
            boundary_ids=tuple(item.boundary_id for item in self.boundaries),
            base_ids=tuple(item.base_id for item in self.bases),
            rule_ids=tuple(item.rule_id for item in self.rules),
            verification_ids=tuple(item.verification_id for item in self.verifications),
            upstream_module_ids=upstream_module_ids,
        )

    def to_dict(self) -> dict[str, Any]:
        export_surface = self.export_surface()
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
            "source_ref": self.source_ref.to_dict(),
            "export_surface": export_surface.to_dict(),
        }


@dataclass(frozen=True)
class FrameworkCatalog:
    modules: tuple[FrameworkModule, ...]

    def get_module(self, framework: str, level: int, module: int) -> FrameworkModule:
        for item in self.modules:
            if item.framework == framework and item.level == level and item.module == module:
                return item
        raise KeyError(f"missing framework module: {framework}.L{level}.M{module}")

    def to_dict(self) -> dict[str, Any]:
        return {"modules": [item.to_dict() for item in self.modules]}
