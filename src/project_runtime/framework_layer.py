from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from framework_ir import FrameworkModule as ParsedFrameworkModule
from framework_ir import load_framework_catalog

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
            "bases": [item.to_dict() for item in cls.base_classes],
            "rules": [item.to_dict() for item in cls.rule_classes],
            "verifications": [item.to_dict() for item in cls.verifications],
            "export_surface": cls.export_surface(),
        }


def _module_name_fragment(module: ParsedFrameworkModule) -> str:
    return f"{module.framework.capitalize()}L{module.level}M{module.module}"


def _class_id(kind: str, *parts: str) -> str:
    normalized = [kind, *parts]
    return "::".join(normalized)


def _exact_to_communication_path(path: str) -> str:
    parts = path.split(".")
    if len(parts) != 3 or parts[0] != "exact":
        return ""
    return ".".join(("communication", parts[1], parts[2]))


def _related_communication_paths(paths: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        communication_path
        for path in paths
        for communication_path in (_exact_to_communication_path(path),)
        if communication_path
    )


def _boundary_projection(
    module: ParsedFrameworkModule,
    boundary_id: str,
    *,
    primary_exact_path: str,
    related_exact_paths: tuple[str, ...] = tuple(),
    mapping_mode: str = "direct",
    note: str = "",
) -> dict[str, Any]:
    related_exact = tuple(dict.fromkeys((primary_exact_path, *related_exact_paths)))
    primary_communication = _exact_to_communication_path(primary_exact_path)
    related_communication = _related_communication_paths(related_exact)
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


def _frontend_boundary_projection(module: ParsedFrameworkModule, boundary_id: str) -> dict[str, Any]:
    direct_paths: dict[str, tuple[str, tuple[str, ...]]] = {
        "SURFACE": ("exact.frontend.surface", ("exact.frontend.surface.copy",)),
        "VISUAL": ("exact.frontend.visual", tuple()),
        "INTERACT": ("exact.frontend.interact", ("exact.frontend.interact.aux_nav",)),
        "STATE": (
            "exact.frontend.state",
            ("exact.frontend.state.role_labels", "exact.frontend.state.relative_groups"),
        ),
        "EXTEND": ("exact.frontend.extend", tuple()),
        "ROUTE": ("exact.frontend.route", ("exact.frontend.route.showcase_page",)),
        "A11Y": ("exact.frontend.a11y", tuple()),
    }
    if boundary_id in direct_paths:
        primary_exact_path, related_exact_paths = direct_paths[boundary_id]
        return _boundary_projection(
            module,
            boundary_id,
            primary_exact_path=primary_exact_path,
            related_exact_paths=related_exact_paths,
        )
    if boundary_id in {"A11Y", "READ", "ORDER", "FOCUS"} or boundary_id.endswith("A11Y"):
        return _boundary_projection(
            module,
            boundary_id,
            primary_exact_path="exact.frontend.a11y",
            mapping_mode="derived",
            note="该边界按可访问与阅读路径归属到项目配置。",
        )
    if boundary_id in {"ROUTE", "NAV", "ENTRY", "RETURN", "PAGESET", "SCENE", "STEP", "REF"}:
        return _boundary_projection(
            module,
            boundary_id,
            primary_exact_path="exact.frontend.route",
            mapping_mode="derived",
            note="该边界按导航与返回路径归属到项目配置。",
        )
    visual_boundaries = {
        "VISUAL",
        "TOKEN",
        "THEME",
        "DENSITY",
        "ALERT",
        "TAG",
        "BUBBLE",
        "TEXTTONE",
        "TEXTTYPO",
        "BTNCHROME",
        "PANELTONE",
        "FEEDBACK",
    }
    if boundary_id in visual_boundaries or "TONE" in boundary_id or "TYPO" in boundary_id or "CHROME" in boundary_id:
        return _boundary_projection(
            module,
            boundary_id,
            primary_exact_path="exact.frontend.visual",
            mapping_mode="derived",
            note="该边界按视觉与主题语义归属到项目配置。",
        )
    return _boundary_projection(
        module,
        boundary_id,
        primary_exact_path="exact.frontend.surface",
        related_exact_paths=("exact.frontend.surface.copy",),
        mapping_mode="derived",
        note="该边界按界面承载与组件装配归属到项目配置。",
    )


def _knowledge_base_boundary_projection(module: ParsedFrameworkModule, boundary_id: str) -> dict[str, Any]:
    direct_paths: dict[str, tuple[str, tuple[str, ...]]] = {
        "SURFACE": ("exact.frontend.surface", ("exact.frontend.surface.copy",)),
        "LIBRARY": ("exact.knowledge_base.library", tuple()),
        "PREVIEW": ("exact.knowledge_base.preview", tuple()),
        "CHAT": ("exact.knowledge_base.chat", tuple()),
        "CONTEXT": ("exact.knowledge_base.context", tuple()),
        "RETURN": ("exact.knowledge_base.return", tuple()),
    }
    if boundary_id in direct_paths:
        primary_exact_path, related_exact_paths = direct_paths[boundary_id]
        return _boundary_projection(
            module,
            boundary_id,
            primary_exact_path=primary_exact_path,
            related_exact_paths=related_exact_paths,
        )
    if boundary_id == "A11Y" or boundary_id.endswith("A11Y"):
        return _boundary_projection(
            module,
            boundary_id,
            primary_exact_path="exact.frontend.a11y",
            mapping_mode="derived",
            note="该边界由工作台可访问切片承接。",
        )
    if boundary_id in {"FILESET", "INGEST", "CLASSIFY", "LIMIT"}:
        return _boundary_projection(
            module,
            boundary_id,
            primary_exact_path="exact.knowledge_base.library",
            mapping_mode="derived",
            note="该边界由知识库配置承接。",
        )
    if boundary_id == "VISIBILITY":
        return _boundary_projection(
            module,
            boundary_id,
            primary_exact_path="exact.knowledge_base.library",
            related_exact_paths=("exact.knowledge_base.preview",),
            mapping_mode="derived",
            note="该边界由知识库入口与来源预览配置共同承接。",
        )
    if boundary_id == "ENTRY":
        return _boundary_projection(
            module,
            boundary_id,
            primary_exact_path="exact.knowledge_base.library",
            related_exact_paths=("exact.frontend.route",),
            mapping_mode="derived",
            note="该边界由知识库入口配置与工作台路由共同承接。",
        )
    if boundary_id in {"DOCVIEW", "TOC", "META"}:
        return _boundary_projection(
            module,
            boundary_id,
            primary_exact_path="exact.knowledge_base.preview",
            mapping_mode="derived",
            note="该边界由来源预览配置承接。",
        )
    if boundary_id == "FOCUS":
        return _boundary_projection(
            module,
            boundary_id,
            primary_exact_path="exact.knowledge_base.preview",
            related_exact_paths=("exact.frontend.a11y",),
            mapping_mode="derived",
            note="该边界由来源预览与可访问配置共同承接。",
        )
    if boundary_id == "ANCHOR":
        return _boundary_projection(
            module,
            boundary_id,
            primary_exact_path="exact.knowledge_base.preview",
            related_exact_paths=("exact.knowledge_base.return",),
            mapping_mode="derived",
            note="该边界由来源锚点与返回路径配置共同承接。",
        )
    if boundary_id in {"TURN", "INPUT"}:
        return _boundary_projection(
            module,
            boundary_id,
            primary_exact_path="exact.knowledge_base.chat",
            mapping_mode="derived",
            note="该边界由对话项目配置承接。",
        )
    if boundary_id == "STATUS":
        return _boundary_projection(
            module,
            boundary_id,
            primary_exact_path="exact.knowledge_base.chat",
            related_exact_paths=("exact.knowledge_base.preview",),
            mapping_mode="derived",
            note="该边界由对话输出与来源状态配置共同承接。",
        )
    if boundary_id == "CITATION":
        return _boundary_projection(
            module,
            boundary_id,
            primary_exact_path="exact.knowledge_base.chat",
            related_exact_paths=(
                "exact.knowledge_base.context",
                "exact.knowledge_base.return",
                "exact.knowledge_base.preview",
            ),
            mapping_mode="derived",
            note="该边界由对话、上下文、返回与来源预览配置共同承接。",
        )
    if boundary_id == "SCOPE":
        return _boundary_projection(
            module,
            boundary_id,
            primary_exact_path="exact.knowledge_base.context",
            related_exact_paths=("exact.knowledge_base.preview",),
            mapping_mode="derived",
            note="该边界由上下文选择与来源预览配置共同承接。",
        )
    if boundary_id == "TURNLINK":
        return _boundary_projection(
            module,
            boundary_id,
            primary_exact_path="exact.knowledge_base.return",
            related_exact_paths=("exact.knowledge_base.chat", "exact.knowledge_base.context"),
            mapping_mode="derived",
            note="该边界由回合返回链路与上下文配置共同承接。",
        )
    if boundary_id == "TRACE":
        return _boundary_projection(
            module,
            boundary_id,
            primary_exact_path="exact.knowledge_base.context",
            related_exact_paths=("exact.knowledge_base.preview", "exact.knowledge_base.return"),
            mapping_mode="derived",
            note="该边界由上下文、来源追踪与返回链路配置共同承接。",
        )
    if boundary_id == "EMPTY":
        return _boundary_projection(
            module,
            boundary_id,
            primary_exact_path="exact.knowledge_base.chat",
            related_exact_paths=("exact.knowledge_base.preview", "exact.knowledge_base.library"),
            mapping_mode="derived",
            note="该边界由聊天、预览与知识库空态配置共同承接。",
        )
    if boundary_id == "REGION":
        return _boundary_projection(
            module,
            boundary_id,
            primary_exact_path="exact.frontend.surface",
            related_exact_paths=("exact.frontend.surface.copy",),
            mapping_mode="derived",
            note="该边界由工作台界面承载配置承接。",
        )
    if boundary_id == "RESPONSIVE":
        return _boundary_projection(
            module,
            boundary_id,
            primary_exact_path="exact.frontend.surface",
            related_exact_paths=("exact.frontend.visual",),
            mapping_mode="derived",
            note="该边界由界面承载与视觉配置共同承接。",
        )
    return _boundary_projection(
        module,
        boundary_id,
        primary_exact_path="exact.knowledge_base.chat",
        related_exact_paths=("exact.knowledge_base.context", "exact.knowledge_base.return"),
        mapping_mode="derived",
        note="该边界由知识库工作台主链配置承接。",
    )


def _backend_boundary_projection(module: ParsedFrameworkModule, boundary_id: str) -> dict[str, Any]:
    direct_paths: dict[str, tuple[str, tuple[str, ...]]] = {
        "RESULT": ("exact.backend.result", tuple()),
        "AUTH": ("exact.backend.auth", tuple()),
        "TRACE": ("exact.backend.trace", tuple()),
    }
    if boundary_id in direct_paths:
        primary_exact_path, related_exact_paths = direct_paths[boundary_id]
        return _boundary_projection(
            module,
            boundary_id,
            primary_exact_path=primary_exact_path,
            related_exact_paths=related_exact_paths,
        )
    if boundary_id.startswith("LIB") or boundary_id in {"FILE", "LIBRARY"}:
        return _boundary_projection(
            module,
            boundary_id,
            primary_exact_path="exact.knowledge_base.library",
            mapping_mode="derived",
            note="该边界由知识库项目配置承接。",
        )
    if boundary_id.startswith("PREVIEW") or boundary_id == "PREVIEW":
        return _boundary_projection(
            module,
            boundary_id,
            primary_exact_path="exact.knowledge_base.preview",
            mapping_mode="derived",
            note="该边界由来源预览配置承接。",
        )
    if boundary_id.startswith("CHAT") or boundary_id == "CITATION":
        return _boundary_projection(
            module,
            boundary_id,
            primary_exact_path="exact.knowledge_base.chat",
            related_exact_paths=(
                "exact.knowledge_base.context",
                "exact.knowledge_base.return",
                "exact.knowledge_base.preview",
            ),
            mapping_mode="derived",
            note="该边界由对话、返回与来源预览配置共同承接。",
        )
    if boundary_id == "TRACE":
        return _boundary_projection(
            module,
            boundary_id,
            primary_exact_path="exact.backend.trace",
            related_exact_paths=("exact.knowledge_base.return",),
            mapping_mode="derived",
            note="该边界由追踪与返回链路配置共同承接。",
        )
    if boundary_id in {"RESULT", "AUTH", "ERROR", "VALID", "CONSIST"}:
        primary_exact = "exact.backend.auth" if boundary_id in {"AUTH", "VALID"} else "exact.backend.result"
        return _boundary_projection(
            module,
            boundary_id,
            primary_exact_path=primary_exact,
            related_exact_paths=(
                "exact.knowledge_base.chat",
                "exact.knowledge_base.library",
                "exact.knowledge_base.preview",
            ),
            mapping_mode="derived",
            note="该边界由统一返回结构与跨接口约束配置共同承接。",
        )
    return _boundary_projection(
        module,
        boundary_id,
        primary_exact_path="exact.backend.result",
        related_exact_paths=("exact.knowledge_base.chat",),
        mapping_mode="derived",
        note="该边界由后端结果与工作台主链配置共同承接。",
    )


def _boundary_projection_map(module: ParsedFrameworkModule) -> dict[str, dict[str, Any]]:
    resolver = {
        "frontend": _frontend_boundary_projection,
        "knowledge_base": _knowledge_base_boundary_projection,
        "backend": _backend_boundary_projection,
    }.get(module.framework)
    if resolver is None:
        return {}
    return {
        boundary.boundary_id: resolver(module, boundary.boundary_id)
        for boundary in module.boundaries
    }


def _module_exact_overlay_paths(module: ParsedFrameworkModule) -> tuple[str, ...]:
    if module.framework == "frontend":
        return ("exact.code.frontend",)
    if module.framework == "knowledge_base":
        return ("exact.knowledge_base.documents",)
    if module.framework == "backend":
        return ("exact.code.backend",)
    return tuple()


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


def _build_module_class(module: ParsedFrameworkModule) -> type[FrameworkModuleClass]:
    base_classes = tuple(_build_base_class(module, index) for index in range(len(module.bases)))
    rule_classes = tuple(_build_rule_class(module, index) for index in range(len(module.rules)))
    boundary_projection_map = _boundary_projection_map(module)
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
