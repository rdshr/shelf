from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from framework_ir import FrameworkModule as ParsedFrameworkModule
from framework_ir import load_framework_catalog

from project_runtime.models import SelectedFrameworkModule


class FrameworkBaseClass:
    module_id: str
    base_id: str
    name: str
    statement: str
    inline_expr: str
    source_tokens: tuple[str, ...]
    upstream_links: tuple[Any, ...]

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        return {
            "module_id": cls.module_id,
            "base_id": cls.base_id,
            "name": cls.name,
            "statement": cls.statement,
            "inline_expr": cls.inline_expr,
            "source_tokens": list(cls.source_tokens),
            "upstream_links": [item.to_dict() for item in cls.upstream_links],
            "class_name": cls.__name__,
        }


class FrameworkRuleClass:
    module_id: str
    rule_id: str
    name: str
    participant_bases: tuple[str, ...]
    combination: str
    output_capabilities: tuple[str, ...]
    invalid_conclusions: tuple[str, ...]
    boundary_bindings: tuple[str, ...]

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        return {
            "module_id": cls.module_id,
            "rule_id": cls.rule_id,
            "name": cls.name,
            "participant_bases": list(cls.participant_bases),
            "combination": cls.combination,
            "output_capabilities": list(cls.output_capabilities),
            "invalid_conclusions": list(cls.invalid_conclusions),
            "boundary_bindings": list(cls.boundary_bindings),
            "class_name": cls.__name__,
        }


class FrameworkModuleClass:
    framework: str
    level: int
    module: int
    module_id: str
    framework_file: str
    title_cn: str
    title_en: str
    intro: str
    capabilities: tuple[Any, ...]
    boundaries: tuple[Any, ...]
    verifications: tuple[Any, ...]
    base_classes: tuple[type[FrameworkBaseClass], ...]
    rule_classes: tuple[type[FrameworkRuleClass], ...]
    upstream_module_ids: tuple[str, ...]

    @classmethod
    def export_surface(cls) -> dict[str, Any]:
        return {
            "module_id": cls.module_id,
            "framework_file": cls.framework_file,
            "title_cn": cls.title_cn,
            "title_en": cls.title_en,
            "intro": cls.intro,
            "boundary_ids": [item.boundary_id for item in cls.boundaries],
            "base_ids": [item.base_id for item in cls.base_classes],
            "rule_ids": [item.rule_id for item in cls.rule_classes],
            "capability_ids": [item.capability_id for item in cls.capabilities],
            "verification_ids": [item.verification_id for item in cls.verifications],
            "upstream_module_ids": list(cls.upstream_module_ids),
            "class_name": cls.__name__,
        }

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        return {
            "module_id": cls.module_id,
            "framework_file": cls.framework_file,
            "title_cn": cls.title_cn,
            "title_en": cls.title_en,
            "intro": cls.intro,
            "capabilities": [item.to_dict() for item in cls.capabilities],
            "boundaries": [item.to_dict() for item in cls.boundaries],
            "bases": [item.to_dict() for item in cls.base_classes],
            "rules": [item.to_dict() for item in cls.rule_classes],
            "verifications": [item.to_dict() for item in cls.verifications],
            "export_surface": cls.export_surface(),
        }


def _module_name_fragment(module: ParsedFrameworkModule) -> str:
    return f"{module.framework.capitalize()}L{module.level}M{module.module}"


def _build_base_class(module: ParsedFrameworkModule, index: int) -> type[FrameworkBaseClass]:
    base = module.bases[index]
    class_name = f"{_module_name_fragment(module)}{base.base_id}Base"
    return type(
        class_name,
        (FrameworkBaseClass,),
        {
            "module_id": module.module_id,
            "base_id": base.base_id,
            "name": base.name,
            "statement": base.statement,
            "inline_expr": base.inline_expr,
            "source_tokens": base.source_tokens,
            "upstream_links": base.upstream_links,
        },
    )


def _build_rule_class(module: ParsedFrameworkModule, index: int) -> type[FrameworkRuleClass]:
    rule = module.rules[index]
    class_name = f"{_module_name_fragment(module)}{rule.rule_id}Rule"
    return type(
        class_name,
        (FrameworkRuleClass,),
        {
            "module_id": module.module_id,
            "rule_id": rule.rule_id,
            "name": rule.name,
            "participant_bases": rule.participant_bases,
            "combination": rule.combination,
            "output_capabilities": rule.output_capabilities,
            "invalid_conclusions": rule.invalid_conclusions,
            "boundary_bindings": rule.boundary_bindings,
        },
    )


def _build_module_class(module: ParsedFrameworkModule) -> type[FrameworkModuleClass]:
    base_classes = tuple(_build_base_class(module, index) for index in range(len(module.bases)))
    rule_classes = tuple(_build_rule_class(module, index) for index in range(len(module.rules)))
    class_name = f"{_module_name_fragment(module)}FrameworkModule"
    return type(
        class_name,
        (FrameworkModuleClass,),
        {
            "framework": module.framework,
            "level": module.level,
            "module": module.module,
            "module_id": module.module_id,
            "framework_file": module.path,
            "title_cn": module.title_cn,
            "title_en": module.title_en,
            "intro": module.intro,
            "capabilities": module.capabilities,
            "boundaries": module.boundaries,
            "verifications": module.verifications,
            "base_classes": base_classes,
            "rule_classes": rule_classes,
            "upstream_module_ids": tuple(sorted({link.module_id for base in module.bases for link in base.upstream_links})),
        },
    )


@lru_cache(maxsize=1)
def load_framework_module_classes() -> dict[str, type[FrameworkModuleClass]]:
    catalog = load_framework_catalog()
    return {module.module_id: _build_module_class(module) for module in catalog.modules}


@lru_cache(maxsize=1)
def load_framework_file_index() -> dict[str, type[FrameworkModuleClass]]:
    classes = load_framework_module_classes()
    return {module.framework_file: module for module in classes.values()}


def resolve_selected_framework_modules(
    selection: tuple[SelectedFrameworkModule, ...],
) -> tuple[tuple[type[FrameworkModuleClass], ...], dict[str, str]]:
    file_index = load_framework_file_index()
    roots: list[type[FrameworkModuleClass]] = []
    root_module_ids: dict[str, str] = {}
    for item in selection:
        module_class = file_index.get(item.framework_file)
        if module_class is None:
            raise KeyError(f"unknown framework file: {item.framework_file}")
        roots.append(module_class)
        root_module_ids[item.role] = module_class.module_id

    resolved: dict[str, type[FrameworkModuleClass]] = {}

    def visit(module_class: type[FrameworkModuleClass]) -> None:
        if module_class.module_id in resolved:
            return
        resolved[module_class.module_id] = module_class
        classes = load_framework_module_classes()
        for upstream_module_id in module_class.upstream_module_ids:
            upstream_class = classes.get(upstream_module_id)
            if upstream_class is None:
                raise KeyError(f"missing upstream framework module: {upstream_module_id}")
            visit(upstream_class)

    for root in roots:
        visit(root)
    return tuple(sorted(resolved.values(), key=lambda item: item.module_id)), root_module_ids


def framework_class_path(module_class: type[FrameworkModuleClass]) -> str:
    return f"{Path(__file__).stem}:{module_class.__name__}"
