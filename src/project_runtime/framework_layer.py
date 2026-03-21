from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from framework_ir import FrameworkModule as ParsedFrameworkModule
from framework_ir import load_framework_catalog

from project_runtime.correspondence_contracts import (
    boundary_field_name,
    module_class_name_fragment,
    module_key_from_id,
)
from project_runtime.models import SelectedFrameworkModule


class FrameworkBaseClass:
    class_id: str
    canonical_id: str
    module_id: str
    base_id: str
    name: str
    statement: str
    inline_expr: str
    source_tokens: tuple[str, ...]
    upstream_links: tuple[Any, ...]
    source_ref: dict[str, Any]
    related_rule_ids: tuple[str, ...]
    boundary_bindings: tuple[str, ...]

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        return {
            "class_id": cls.class_id,
            "canonical_id": cls.canonical_id,
            "module_id": cls.module_id,
            "base_id": cls.base_id,
            "name": cls.name,
            "statement": cls.statement,
            "inline_expr": cls.inline_expr,
            "source_tokens": list(cls.source_tokens),
            "upstream_links": [item.to_dict() for item in cls.upstream_links],
            "source_ref": dict(cls.source_ref),
            "related_rule_ids": list(cls.related_rule_ids),
            "boundary_bindings": list(cls.boundary_bindings),
            "class_name": cls.__name__,
        }


class FrameworkRuleClass:
    class_id: str
    canonical_id: str
    module_id: str
    rule_id: str
    name: str
    participant_bases: tuple[str, ...]
    combination: str
    output_capabilities: tuple[str, ...]
    invalid_conclusions: tuple[str, ...]
    boundary_bindings: tuple[str, ...]
    source_ref: dict[str, Any]

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        return {
            "class_id": cls.class_id,
            "canonical_id": cls.canonical_id,
            "module_id": cls.module_id,
            "rule_id": cls.rule_id,
            "name": cls.name,
            "participant_bases": list(cls.participant_bases),
            "combination": cls.combination,
            "output_capabilities": list(cls.output_capabilities),
            "invalid_conclusions": list(cls.invalid_conclusions),
            "boundary_bindings": list(cls.boundary_bindings),
            "source_ref": dict(cls.source_ref),
            "class_name": cls.__name__,
        }


class FrameworkBoundarySpecClass:
    class_id: str
    canonical_id: str
    module_id: str
    boundary_id: str
    name: str
    statement: str
    source_tokens: tuple[str, ...]
    source_ref: dict[str, Any]
    projection: dict[str, Any]

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        return {
            "class_id": cls.class_id,
            "canonical_id": cls.canonical_id,
            "module_id": cls.module_id,
            "boundary_id": cls.boundary_id,
            "name": cls.name,
            "statement": cls.statement,
            "source_tokens": list(cls.source_tokens),
            "source_ref": dict(cls.source_ref),
            "projection": dict(cls.projection),
            "class_name": cls.__name__,
        }


class FrameworkBoundaryRuntimeClass:
    class_id: str
    canonical_id: str
    module_id: str
    boundary_id: str
    primary_exact_path: str
    primary_communication_path: str
    mapping_mode: str
    note: str
    source_ref: dict[str, Any]

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        return {
            "class_id": cls.class_id,
            "canonical_id": cls.canonical_id,
            "module_id": cls.module_id,
            "boundary_id": cls.boundary_id,
            "primary_exact_path": cls.primary_exact_path,
            "primary_communication_path": cls.primary_communication_path,
            "mapping_mode": cls.mapping_mode,
            "note": cls.note,
            "source_ref": dict(cls.source_ref),
            "class_name": cls.__name__,
        }


class FrameworkModuleClass:
    class_id: str
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
    boundary_spec_classes: tuple[type[FrameworkBoundarySpecClass], ...]
    boundary_runtime_classes: tuple[type[FrameworkBoundaryRuntimeClass], ...]
    base_classes: tuple[type[FrameworkBaseClass], ...]
    rule_classes: tuple[type[FrameworkRuleClass], ...]
    upstream_module_ids: tuple[str, ...]
    source_ref: dict[str, Any]
    boundary_projection_map: dict[str, dict[str, Any]]
    exact_overlay_paths: tuple[str, ...]

    @classmethod
    def export_surface(cls) -> dict[str, Any]:
        return {
            "class_id": cls.class_id,
            "module_id": cls.module_id,
            "framework_file": cls.framework_file,
            "title_cn": cls.title_cn,
            "title_en": cls.title_en,
            "intro": cls.intro,
            "source_ref": dict(cls.source_ref),
            "boundary_ids": [item.boundary_id for item in cls.boundaries],
            "boundary_spec_ids": [item.boundary_id for item in cls.boundary_spec_classes],
            "boundary_runtime_ids": [item.boundary_id for item in cls.boundary_runtime_classes],
            "base_ids": [item.base_id for item in cls.base_classes],
            "rule_ids": [item.rule_id for item in cls.rule_classes],
            "capability_ids": [item.capability_id for item in cls.capabilities],
            "verification_ids": [item.verification_id for item in cls.verifications],
            "upstream_module_ids": list(cls.upstream_module_ids),
            "boundary_projections": [
                dict(cls.boundary_projection_map[item.boundary_id])
                for item in cls.boundaries
                if item.boundary_id in cls.boundary_projection_map
            ],
            "exact_overlay_paths": list(cls.exact_overlay_paths),
            "class_name": cls.__name__,
        }

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        return {
            "class_id": cls.class_id,
            "module_id": cls.module_id,
            "framework_file": cls.framework_file,
            "title_cn": cls.title_cn,
            "title_en": cls.title_en,
            "intro": cls.intro,
            "source_ref": dict(cls.source_ref),
            "capabilities": [item.to_dict() for item in cls.capabilities],
            "boundaries": [_serialize_boundary(item, cls.boundary_projection_map) for item in cls.boundaries],
            "boundary_specs": [item.to_dict() for item in cls.boundary_spec_classes],
            "boundary_runtimes": [item.to_dict() for item in cls.boundary_runtime_classes],
            "bases": [item.to_dict() for item in cls.base_classes],
            "rules": [item.to_dict() for item in cls.rule_classes],
            "verifications": [item.to_dict() for item in cls.verifications],
            "export_surface": cls.export_surface(),
        }


def _module_name_fragment(module: ParsedFrameworkModule) -> str:
    module_id = f"{module.framework}.L{module.level}.M{module.module}"
    return module_class_name_fragment(module_id)


def _class_id(kind: str, *parts: str) -> str:
    normalized = [kind, *parts]
    return "::".join(normalized)


def _exact_to_communication_path(path: str) -> str:
    parts = path.split(".")
    if len(parts) != 3 or parts[0] != "exact":
        return ""
    return ".".join(("communication", parts[1], parts[2]))


def _boundary_projection(
    module: ParsedFrameworkModule,
    boundary_id: str,
    *,
    primary_exact_path: str,
    mapping_mode: str = "direct",
    note: str = "",
) -> dict[str, Any]:
    # Framework projection is one-to-one by contract: each boundary maps to one exact path.
    # Keep related fields for trace compatibility, but force them to mirror primary only.
    related_exact = (primary_exact_path,)
    primary_communication = _exact_to_communication_path(primary_exact_path)
    related_communication = (primary_communication,) if primary_communication else tuple()
    return {
        "projection_id": _class_id("framework_boundary_projection", module.module_id, boundary_id),
        "projection_source": "framework_export",
        "module_id": module.module_id,
        "boundary_id": boundary_id,
        "mapping_mode": mapping_mode,
        "primary_communication_path": primary_communication,
        "related_communication_paths": list(related_communication),
        "primary_exact_path": primary_exact_path,
        "related_exact_paths": list(related_exact),
        "note": note,
    }


def _boundary_name_to_section(boundary_id: str) -> str:
    return str(boundary_id).strip().lower()


def _module_boundary_projection(module: ParsedFrameworkModule, boundary_id: str) -> dict[str, Any]:
    section = _boundary_name_to_section(boundary_id)
    module_id = module.module_id
    module_key = module_key_from_id(module_id)
    field_name = boundary_field_name(boundary_id)
    return _boundary_projection(
        module,
        boundary_id,
        primary_exact_path=f"exact.{module.framework}.{section}",
        mapping_mode="direct",
        note="边界一对一映射：boundary_id 与 config/code 锚点同名。",
    ) | {
        "module_key": module_key,
        "static_field_name": field_name,
        "runtime_field_name": field_name,
        "exact_export_static_path": f"exact_export.modules.{module_key}.static_params.{field_name}",
        "communication_export_static_path": f"communication_export.modules.{module_key}.static_params.{field_name}",
        "merge_policy": "runtime_override_else_static",
    }


def _boundary_projection_map(module: ParsedFrameworkModule) -> dict[str, dict[str, Any]]:
    return {
        boundary.boundary_id: _module_boundary_projection(module, boundary.boundary_id)
        for boundary in module.boundaries
    }


def _module_exact_overlay_paths(module: ParsedFrameworkModule) -> tuple[str, ...]:
    framework_name = str(module.framework).strip()
    if not framework_name:
        return tuple()
    return (
        f"exact.code.{framework_name}",
        f"exact.{framework_name}.documents",
    )


def _serialize_boundary(boundary: Any, boundary_projection_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
    payload = boundary.to_dict()
    projection = boundary_projection_map.get(boundary.boundary_id)
    if projection is not None:
        payload["config_projection"] = dict(projection)
    return payload


def _build_base_class(module: ParsedFrameworkModule, index: int) -> type[FrameworkBaseClass]:
    base = module.bases[index]
    class_name = f"{_module_name_fragment(module)}{base.base_id}Base"
    related_rules = tuple(
        rule.rule_id
        for rule in module.rules
        if base.base_id in rule.participant_bases
    )
    boundary_bindings = tuple(
        sorted(
            {
                boundary_id
                for rule in module.rules
                if base.base_id in rule.participant_bases
                for boundary_id in rule.boundary_bindings
            }
        )
    )
    return type(
        class_name,
        (FrameworkBaseClass,),
        {
            "class_id": _class_id("framework_base_class", module.module_id, base.base_id),
            "canonical_id": _class_id("framework_base", module.module_id, base.base_id),
            "module_id": module.module_id,
            "base_id": base.base_id,
            "name": base.name,
            "statement": base.statement,
            "inline_expr": base.inline_expr,
            "source_tokens": base.source_tokens,
            "upstream_links": base.upstream_links,
            "source_ref": base.source_ref.to_dict(),
            "related_rule_ids": related_rules,
            "boundary_bindings": boundary_bindings,
        },
    )


def _build_rule_class(module: ParsedFrameworkModule, index: int) -> type[FrameworkRuleClass]:
    rule = module.rules[index]
    class_name = f"{_module_name_fragment(module)}{rule.rule_id}Rule"
    return type(
        class_name,
        (FrameworkRuleClass,),
        {
            "class_id": _class_id("framework_rule_class", module.module_id, rule.rule_id),
            "canonical_id": _class_id("framework_rule", module.module_id, rule.rule_id),
            "module_id": module.module_id,
            "rule_id": rule.rule_id,
            "name": rule.name,
            "participant_bases": rule.participant_bases,
            "combination": rule.combination,
            "output_capabilities": rule.output_capabilities,
            "invalid_conclusions": rule.invalid_conclusions,
            "boundary_bindings": rule.boundary_bindings,
            "source_ref": rule.source_ref.to_dict(),
        },
    )


def _build_boundary_spec_class(
    module: ParsedFrameworkModule,
    index: int,
    boundary_projection_map: dict[str, dict[str, Any]],
) -> type[FrameworkBoundarySpecClass]:
    boundary = module.boundaries[index]
    class_name = f"{_module_name_fragment(module)}{boundary.boundary_id}BoundarySpec"
    projection = boundary_projection_map.get(boundary.boundary_id, {})
    return type(
        class_name,
        (FrameworkBoundarySpecClass,),
        {
            "class_id": _class_id("framework_boundary_spec_class", module.module_id, boundary.boundary_id),
            "canonical_id": _class_id("framework_boundary_spec", module.module_id, boundary.boundary_id),
            "module_id": module.module_id,
            "boundary_id": boundary.boundary_id,
            "name": boundary.name,
            "statement": boundary.statement,
            "source_tokens": boundary.source_tokens,
            "source_ref": boundary.source_ref.to_dict(),
            "projection": dict(projection),
        },
    )


def _build_boundary_runtime_class(
    module: ParsedFrameworkModule,
    index: int,
    boundary_projection_map: dict[str, dict[str, Any]],
) -> type[FrameworkBoundaryRuntimeClass]:
    boundary = module.boundaries[index]
    class_name = f"{_module_name_fragment(module)}{boundary.boundary_id}BoundaryRuntime"
    projection = boundary_projection_map.get(boundary.boundary_id, {})
    return type(
        class_name,
        (FrameworkBoundaryRuntimeClass,),
        {
            "class_id": _class_id("framework_boundary_runtime_class", module.module_id, boundary.boundary_id),
            "canonical_id": _class_id("framework_boundary_runtime", module.module_id, boundary.boundary_id),
            "module_id": module.module_id,
            "boundary_id": boundary.boundary_id,
            "primary_exact_path": str(projection.get("primary_exact_path") or ""),
            "primary_communication_path": str(projection.get("primary_communication_path") or ""),
            "mapping_mode": str(projection.get("mapping_mode") or ""),
            "note": str(projection.get("note") or ""),
            "source_ref": boundary.source_ref.to_dict(),
        },
    )


def _build_module_class(module: ParsedFrameworkModule) -> type[FrameworkModuleClass]:
    boundary_projection_map = _boundary_projection_map(module)
    boundary_spec_classes = tuple(
        _build_boundary_spec_class(module, index, boundary_projection_map)
        for index in range(len(module.boundaries))
    )
    boundary_runtime_classes = tuple(
        _build_boundary_runtime_class(module, index, boundary_projection_map)
        for index in range(len(module.boundaries))
    )
    base_classes = tuple(_build_base_class(module, index) for index in range(len(module.bases)))
    rule_classes = tuple(_build_rule_class(module, index) for index in range(len(module.rules)))
    class_name = f"{_module_name_fragment(module)}FrameworkModule"
    return type(
        class_name,
        (FrameworkModuleClass,),
        {
            "class_id": _class_id("framework_module_class", module.module_id),
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
            "boundary_spec_classes": boundary_spec_classes,
            "boundary_runtime_classes": boundary_runtime_classes,
            "base_classes": base_classes,
            "rule_classes": rule_classes,
            "upstream_module_ids": tuple(sorted({link.module_id for base in module.bases for link in base.upstream_links})),
            "source_ref": module.source_ref.to_dict(),
            "boundary_projection_map": boundary_projection_map,
            "exact_overlay_paths": _module_exact_overlay_paths(module),
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
