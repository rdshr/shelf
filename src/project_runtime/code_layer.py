from __future__ import annotations

from dataclasses import dataclass, field, make_dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from knowledge_base_runtime.runtime_profile import load_knowledge_base_runtime_profile

from project_runtime.config_layer import ConfigModuleBinding
from project_runtime.correspondence_contracts import (
    BaseContract,
    ModuleContract,
    RuleContract,
    RuntimeBoundaryParamsContract,
    StaticBoundaryParamsContract,
    UNSET,
    boundary_field_name,
    module_class_name_fragment,
    module_key_from_id,
)
from project_runtime.documents import export_documents
from project_runtime.framework_layer import FrameworkModuleClass
from project_runtime.models import KnowledgeDocument, SeedDocumentSource
from project_runtime.static_modules.backend_l2_m0 import (
    BACKEND_L2_M0_MODULE_ID,
    BackendL2M0B1Base,
    BackendL2M0B2Base,
    BackendL2M0B3Base,
    BackendL2M0DynamicBoundaryParams,
    BackendL2M0Module,
    BackendL2M0R1Rule,
    BackendL2M0R2Rule,
    BackendL2M0R3Rule,
    BackendL2M0R4Rule,
    BackendL2M0StaticBoundaryParams,
)


class CodeModuleClass:
    class_id: str
    module_id: str
    module_key: str
    framework_file: str
    source_ref: dict[str, Any]
    exact_export: dict[str, Any]
    code_exports: dict[str, Any]
    code_bindings: dict[str, Any]
    ModuleType: type[ModuleContract]
    StaticBoundaryParamsType: type[StaticBoundaryParamsContract]
    RuntimeBoundaryParamsType: type[RuntimeBoundaryParamsContract]
    BaseTypes: tuple[type[BaseContract], ...]
    RuleTypes: tuple[type[RuleContract], ...]
    boundary_static_classes: tuple[type["CodeBoundaryStaticClass"], ...]
    boundary_runtime_classes: tuple[type["CodeBoundaryRuntimeClass"], ...]

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        return {
            "class_id": cls.class_id,
            "module_id": cls.module_id,
            "module_key": cls.module_key,
            "framework_file": cls.framework_file,
            "source_ref": dict(cls.source_ref),
            "exact_export": cls.exact_export,
            "code_exports": cls.code_exports,
            "code_bindings": cls.code_bindings,
            "module_type_symbol": _class_symbol(cls.ModuleType),
            "static_params_class_symbol": _class_symbol(cls.StaticBoundaryParamsType),
            "runtime_params_class_symbol": _class_symbol(cls.RuntimeBoundaryParamsType),
            "base_class_symbols": [_class_symbol(item) for item in cls.BaseTypes],
            "rule_class_symbols": [_class_symbol(item) for item in cls.RuleTypes],
            "boundary_static_classes": [item.to_dict() for item in cls.boundary_static_classes],
            "boundary_runtime_classes": [item.to_dict() for item in cls.boundary_runtime_classes],
            "class_name": cls.__name__,
        }


@lru_cache(maxsize=1)
def _code_layer_lines() -> tuple[str, ...]:
    return tuple(Path(__file__).read_text(encoding="utf-8").splitlines())


def _find_code_line(needle: str, *, fallback: int = 1) -> int:
    if not needle:
        return fallback
    for index, line_text in enumerate(_code_layer_lines(), start=1):
        if needle in line_text:
            return index
    return fallback


def _class_symbol(class_type: type[Any]) -> str:
    return f"{class_type.__module__}:{class_type.__name__}"


@lru_cache(maxsize=1)
def _backend_l2_m0_module_lines() -> tuple[str, ...]:
    module_file = Path(__file__).resolve().parent / "static_modules" / "backend_l2_m0.py"
    return tuple(module_file.read_text(encoding="utf-8").splitlines())


def _find_backend_l2_m0_line(needle: str, *, fallback: int = 1) -> int:
    if not needle:
        return fallback
    for index, line_text in enumerate(_backend_l2_m0_module_lines(), start=1):
        if needle in line_text:
            return index
    return fallback


class CodeBoundaryStaticClass:
    class_id: str
    canonical_id: str
    module_id: str
    boundary_id: str
    owner_id: str
    source_symbol: str
    anchor_path: str
    projection_paths: list[str]
    field_name: str
    source_ref: dict[str, Any]

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        return {
            "class_id": cls.class_id,
            "canonical_id": cls.canonical_id,
            "module_id": cls.module_id,
            "boundary_id": cls.boundary_id,
            "owner_id": cls.owner_id,
            "source_symbol": cls.source_symbol,
            "anchor_path": cls.anchor_path,
            "projection_paths": list(cls.projection_paths),
            "field_name": cls.field_name,
            "source_ref": dict(cls.source_ref),
            "class_name": cls.__name__,
        }


class CodeBoundaryRuntimeClass:
    class_id: str
    canonical_id: str
    module_id: str
    boundary_id: str
    owner_id: str
    static_class_id: str
    runtime_slots: list[dict[str, Any]]
    source_ref: dict[str, Any]

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        return {
            "class_id": cls.class_id,
            "canonical_id": cls.canonical_id,
            "module_id": cls.module_id,
            "boundary_id": cls.boundary_id,
            "owner_id": cls.owner_id,
            "static_class_id": cls.static_class_id,
            "runtime_slots": list(cls.runtime_slots),
            "source_ref": dict(cls.source_ref),
            "class_name": cls.__name__,
        }


@dataclass(frozen=True)
class CodeModuleBinding:
    framework_module: type[FrameworkModuleClass]
    config_module: type[Any]
    code_module: type[CodeModuleClass]

    def to_dict(self) -> dict[str, Any]:
        payload = self.code_module.to_dict()
        payload["framework_module_id"] = self.framework_module.module_id
        payload["config_module_id"] = self.config_module.module_id
        return payload


def _require_boundary_context_value(
    boundary_context: dict[str, dict[str, Any]],
    boundary_id: str,
) -> dict[str, Any]:
    payload = boundary_context.get(boundary_id)
    if not isinstance(payload, dict):
        raise ValueError(f"missing module boundary context: {boundary_id}")
    value = payload.get("value")
    if not isinstance(value, dict):
        raise ValueError(f"boundary context value must be dict: {boundary_id}")
    return value


def _overlay(exact_export: dict[str, Any], key: str, *, default: Any = None) -> Any:
    overlays = exact_export.get("overlays")
    if not isinstance(overlays, dict):
        return default
    return overlays.get(key, default)


def _section_summaries(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "document_id": item["document_id"],
            "title": item["title"],
            "section_ids": [section["section_id"] for section in item["sections"]],
            "section_count": len(item["sections"]),
        }
        for item in documents
    ]


def _compile_frontend_app_spec(
    *,
    boundary_context: dict[str, dict[str, Any]],
    exact_export: dict[str, Any],
    root_module_ids: dict[str, str],
) -> dict[str, Any]:
    profile = load_knowledge_base_runtime_profile()
    surface = _require_boundary_context_value(boundary_context, "SURFACE")
    visual = _require_boundary_context_value(boundary_context, "VISUAL")
    interact = _require_boundary_context_value(boundary_context, "INTERACT")
    route = _require_boundary_context_value(boundary_context, "ROUTE")
    a11y = _require_boundary_context_value(boundary_context, "A11Y")
    state = _require_boundary_context_value(boundary_context, "STATE")
    extend = _require_boundary_context_value(boundary_context, "EXTEND")
    implementation = _overlay(exact_export, "frontend", default={})
    copy = surface.get("copy", {})
    showcase = route.get("showcase_page", {})
    allow_create = bool(interact.get("allow_create"))
    allow_delete = bool(interact.get("allow_delete"))
    visual_tokens = profile.style_profiles.resolve_visual_tokens(
        surface_preset=str(visual["surface_preset"]),
        radius_scale=str(visual["radius_scale"]),
        shadow_level=str(visual["shadow_level"]),
        font_scale=str(visual["font_scale"]),
        sidebar_width=str(surface["sidebar_width"]),
        density=str(surface["density"]),
        accent=str(visual["accent"]),
        brand=str(visual["brand"]),
        preview_mode=str(surface["preview_mode"]),
        preview_variant=str(surface["preview_variant"]),
    )
    return {
        "ui": {
            "shell": {
                "id": str(surface["shell"]),
                "layout_variant": str(surface["layout_variant"]),
                "preview_mode": str(surface["preview_mode"]),
            },
            "visual": {
                "tokens": visual_tokens,
            },
            "implementation": {
                "frontend_renderer": str(implementation["frontend_renderer"]),
                "style_profile": str(implementation["style_profile"]),
                "script_profile": str(implementation["script_profile"]),
            },
            "components": {
                "conversation_sidebar": {
                    "title": str(copy["library_title"]),
                    "new_chat_label": str(interact["new_chat_label"]),
                    "knowledge_entry_label": str(interact["knowledge_entry_label"]),
                    "browse_knowledge_label": str(interact["browse_knowledge_label"]),
                    "basketball_showcase_label": str(interact["showcase_label"]),
                },
                "chat_header": {
                    "subtitle_template": str(surface["header_subtitle_template"]),
                    "knowledge_badge_template": str(surface["knowledge_badge_template"]),
                    "knowledge_entry_link_label": str(interact["knowledge_link_label"]),
                    "showcase_link_label": str(interact["showcase_link_label"]),
                },
                "message_stream": {
                    "summary_template": str(state["citation_summary_template"]),
                    "copy_action_label": str(interact["copy_answer_label"]),
                    "copy_failure_message": str(state["copy_failure_message"]),
                    "role_labels": dict(state["role_labels"]),
                },
                "chat_composer": {
                    "context_template": str(surface["context_template"]),
                    "citation_hint": str(surface["citation_hint"]),
                    "placeholder": str(surface["composer_placeholder"]),
                    "mode_label": str(surface["mode_label"]),
                    "submit_label": str(interact["submit_chat_label"]),
                    "knowledge_link_label": str(interact["knowledge_link_label"]),
                    "showcase_link_label": str(interact["showcase_link_label"]),
                },
                "citation_drawer": {
                    "section_label": str(surface["toc_label"]),
                    "snippet_title": str(copy["preview_title"]),
                    "source_context_title": str(surface["source_context_title"]),
                    "empty_context_text": str(state["empty_context_text"]),
                    "load_failure_text": str(state["load_failure_text"]),
                    "document_link_label": str(interact["document_link_label"]),
                    "close_aria_label": str(interact.get("drawer_close_aria_label", "关闭来源抽屉")),
                    "return_targets": list(extend["return_targets"]),
                },
                "knowledge_switch_dialog": {
                    "title": str(interact["knowledge_dialog_title"]),
                    "description": str(
                        interact.get(
                            "knowledge_dialog_description",
                            "当前项目只暴露一个知识库，但切换入口仍保留为稳定工作台结构。",
                        )
                    ),
                    "select_action_label": str(interact["knowledge_dialog_select_label"]),
                    "detail_action_label": str(interact["knowledge_dialog_detail_label"]),
                    "close_aria_label": str(
                        interact.get("knowledge_dialog_close_aria_label", "关闭知识库切换弹窗")
                    ),
                },
                "aux_sidebar": {
                    "note": str(surface["aux_note"]),
                    "nav": dict(interact["aux_nav"]),
                },
            },
            "pages": {
                "chat_home": {"path": str(route["workbench"])},
                "basketball_showcase": {
                    "path": str(route["basketball_showcase"]),
                    "title": str(showcase["title"]),
                    "kicker": str(showcase.get("kicker", "Chat-First Special Page")),
                    "headline": str(showcase.get("headline", showcase["title"])),
                    "intro": str(showcase.get("intro", "轻量前端专题页挂载在知识库主产品旁。")),
                    "back_to_chat_label": str(showcase["back_to_chat_label"]),
                    "browse_knowledge_label": str(showcase["browse_knowledge_label"]),
                },
                "knowledge_list": {
                    "path": str(route["knowledge_list"]),
                    "title": str(copy["library_title"]),
                    "subtitle": str(copy["hero_copy"]),
                    "chat_action_label": str(interact["knowledge_list_chat_label"]),
                    "primary_action_label": str(interact["knowledge_list_primary_label"]),
                    "detail_action_label": str(interact.get("knowledge_list_detail_label", "查看详情")),
                    "rationale_title": str(interact.get("knowledge_list_rationale_title", "为什么保留知识页")),
                    "rationale_copy": str(
                        interact.get(
                            "knowledge_list_rationale_copy",
                            "聊天是主舞台，知识页负责列表浏览、信任建立与来源回看。",
                        )
                    ),
                },
                "knowledge_detail": {
                    "path": f"{route['knowledge_detail']}/{{knowledge_base_id}}",
                    "title": str(copy["library_title"]),
                    "chat_action_label": str(interact["knowledge_detail_chat_label"]),
                    "return_chat_with_document_label": str(interact["return_chat_with_document_label"]),
                    "document_detail_action_label": str(
                        interact.get("knowledge_detail_document_action_label", "查看文档详情")
                    ),
                    "overview_title": str(interact.get("knowledge_detail_overview_title", "知识库概览")),
                },
                "document_detail": {
                    "path": f"{route['document_detail_prefix']}/{{document_id}}",
                    "title": str(copy["preview_title"]),
                    "subtitle": str(interact.get("document_detail_subtitle", "查看文档全文与章节上下文")),
                    "return_chat_label": str(interact.get("document_detail_return_chat_label", "回到聊天")),
                    "return_knowledge_detail_label": str(
                        interact.get("document_detail_return_knowledge_label", "返回知识库详情")
                    ),
                },
            },
            "conversation": {
                "default_title": str(state["default_conversation_title"]),
                "relative_groups": dict(state["relative_groups"]),
                "welcome_kicker": str(copy["hero_kicker"]),
                "welcome_title": str(copy["empty_state_title"]),
                "welcome_copy": str(copy["empty_state_copy"]),
                "current_knowledge_base_template": str(surface["current_knowledge_base_template"]),
                "welcome_prompts": list(surface["welcome_prompts"]),
            },
        },
        "copy": dict(copy),
        "contract": {
            "shell": str(surface["shell"]),
            "layout_variant": str(surface["layout_variant"]),
            "surface_config": {
                "sidebar_width": str(surface["sidebar_width"]),
                "preview_mode": str(surface["preview_mode"]),
                "density": str(surface["density"]),
            },
            "surface_regions": list(surface["surface_regions"]),
            "interaction_actions": list(profile.frontend_interaction_actions(allow_create=allow_create, allow_delete=allow_delete)),
            "a11y": dict(a11y),
            "route_contract": {
                "home": str(route["home"]),
                "workbench": str(route["workbench"]),
                "basketball_showcase": str(route["basketball_showcase"]),
                "knowledge_list": str(route["knowledge_list"]),
                "knowledge_detail": str(route["knowledge_detail"]),
                "document_detail_prefix": str(route["document_detail_prefix"]),
                "api_prefix": str(route["api_prefix"]),
            },
            "extend_slots": [
                {"slot_id": "domain_workbench", "module_id": root_module_ids["knowledge_base"]},
                {"slot_id": "backend_contract", "module_id": root_module_ids["backend"]},
            ],
            "component_variants": {
                "conversation_list": str(extend["conversation_list_variant"]),
                "preview_surface": str(surface["preview_variant"]),
                "chat_bubble": str(surface["chat_bubble_variant"]),
                "chat_composer": str(surface["chat_composer_variant"]),
                "citation_summary": str(surface["citation_card_variant"]),
            },
        },
    }


def _compile_runtime_documents(exact_export: dict[str, Any]) -> list[dict[str, Any]]:
    raw_documents = _overlay(exact_export, "documents", default=[])
    if not isinstance(raw_documents, list) or not raw_documents:
        raise ValueError("knowledge_base exact documents must be a non-empty list")
    sources = tuple(
        SeedDocumentSource.from_dict(item)
        for item in raw_documents
        if isinstance(item, dict)
    )
    return export_documents(sources)


def _compile_knowledge_base_domain_spec(
    *,
    boundary_context: dict[str, dict[str, Any]],
    exact_export: dict[str, Any],
    runtime_documents: list[dict[str, Any]],
) -> dict[str, Any]:
    profile = load_knowledge_base_runtime_profile()
    surface = _require_boundary_context_value(boundary_context, "SURFACE")
    library = _require_boundary_context_value(boundary_context, "LIBRARY")
    preview = _require_boundary_context_value(boundary_context, "PREVIEW")
    chat = _require_boundary_context_value(boundary_context, "CHAT")
    context = _require_boundary_context_value(boundary_context, "CONTEXT")
    return_policy = _require_boundary_context_value(boundary_context, "RETURN")
    allow_create = bool(library.get("allow_create"))
    allow_delete = bool(library.get("allow_delete"))
    return {
        "workbench": {
            "layout_variant": str(surface["layout_variant"]),
            "surface": {
                "preview_mode": str(surface["preview_mode"]),
            },
            "regions": list(profile.workbench_region_ids),
            "flow": list(profile.workbench_flow_dicts()),
            "library": {
                **dict(library),
                "actions": list(profile.workbench_library_actions(allow_create=allow_create, allow_delete=allow_delete)),
            },
            "preview": dict(preview),
            "chat": dict(chat),
            "context": dict(context),
            "return": dict(return_policy),
            "citation_return": {
                "query_keys": list(profile.workbench_citation_query_keys),
                "targets": list(return_policy["targets"]),
                "anchor_restore": bool(return_policy["anchor_restore"]),
            },
            "documents": _section_summaries(runtime_documents),
            "knowledge_bases": [
                {
                    "knowledge_base_id": str(library["knowledge_base_id"]),
                    "name": str(library["knowledge_base_name"]),
                    "description": str(library["knowledge_base_description"]),
                    "document_count": len(runtime_documents),
                }
            ],
        }
    }


def _compile_backend_service_spec(
    *,
    boundary_context: dict[str, dict[str, Any]],
    exact_export: dict[str, Any],
    route_contract: dict[str, Any],
) -> dict[str, Any]:
    profile = load_knowledge_base_runtime_profile()
    library = _require_boundary_context_value(boundary_context, "LIBRARY")
    preview = _require_boundary_context_value(boundary_context, "PREVIEW")
    chat = _require_boundary_context_value(boundary_context, "CHAT")
    result = _require_boundary_context_value(boundary_context, "RESULT")
    auth = _require_boundary_context_value(boundary_context, "AUTH")
    trace = _require_boundary_context_value(boundary_context, "TRACE")
    implementation = _overlay(exact_export, "backend", default={})
    return {
        "implementation": {
            "backend_renderer": str(implementation["backend_renderer"]),
        },
        "knowledge_base": {
            "knowledge_base_id": str(library["knowledge_base_id"]),
            "knowledge_base_name": str(library["knowledge_base_name"]),
            "knowledge_base_description": str(library["knowledge_base_description"]),
            "source_types": list(library["source_types"]),
            "metadata_fields": list(library["metadata_fields"]),
        },
        "transport": {
            "mode": str(result["transport_mode"]),
            "api_prefix": str(route_contract["api_prefix"]),
            "project_config_endpoint": str(result["project_config_endpoint"]),
        },
        "retrieval": {
            "strategy": str(implementation["retrieval_strategy"]),
            "query_token_min_length": int(trace["query_token_min_length"]),
            "focus_section_bonus": int(trace["focus_section_bonus"]),
            "token_match_bonus": int(trace["token_match_bonus"]),
            "max_preview_sections": int(preview["max_preview_sections"]),
            "max_citations": int(chat["max_citations"]),
            "selection_mode": str(trace["selection_mode"]),
        },
        "interaction_flow": list(profile.workbench_flow_dicts()),
        "answer_policy": {
            "citation_style": str(chat["citation_style"]),
            "no_match_text": str(result["no_match_text"]),
            "lead_template": str(result["lead_template"]),
            "lead_snippet_template": str(result["lead_snippet_template"]),
            "followup_template": str(result["followup_template"]),
            "closing_text": str(result["closing_text"]),
        },
        "interaction_copy": {
            "loading_text": str(result["loading_text"]),
            "error_text": str(result["error_text"]),
        },
        "return_policy": {
            "targets": list(chat["return_targets"]),
            "anchor_restore": bool(chat["anchor_restore"]),
            "chat_path": str(route_contract["workbench"]),
            "knowledge_base_detail_path": f"{route_contract['knowledge_detail']}/{{knowledge_base_id}}",
            "document_detail_path": f"{route_contract['document_detail_prefix']}/{{document_id}}",
        },
        "write_policy": {
            "allow_create": bool(auth["allow_create"]),
            "allow_delete": bool(auth["allow_delete"]),
        },
    }


def _module_field_bindings(binding: ConfigModuleBinding) -> list[dict[str, str]]:
    projections = binding.config_module.exact_export.get("boundary_projections")
    if not isinstance(projections, dict):
        projections = {}
    records: list[dict[str, str]] = []
    module_key = module_key_from_id(binding.framework_module.module_id)
    for boundary in binding.framework_module.boundaries:
        projection = projections.get(boundary.boundary_id, {})
        if not isinstance(projection, dict):
            projection = {}
        static_field = str(
            projection.get("static_field_name")
            or boundary_field_name(boundary.boundary_id)
        )
        runtime_field = str(
            projection.get("runtime_field_name")
            or static_field
        )
        records.append(
            {
                "boundary_id": boundary.boundary_id,
                "module_key": str(projection.get("module_key") or module_key),
                "static_field_name": static_field,
                "runtime_field_name": runtime_field,
                "exact_export_static_path": str(
                    projection.get("exact_export_static_path")
                    or (
                        f"exact_export.modules."
                        f"{module_key}.static_params.{static_field}"
                    )
                ),
                "communication_export_static_path": str(
                    projection.get("communication_export_static_path")
                    or (
                        "communication_export.modules."
                        f"{module_key}.static_params.{static_field}"
                    )
                ),
                "merge_policy": str(
                    projection.get("merge_policy")
                    or "runtime_override_else_static"
                ),
            }
        )
    return records


def _module_static_payload(
    exact_export: dict[str, Any],
    *,
    module_key: str,
) -> dict[str, Any]:
    modules = exact_export.get("modules")
    if not isinstance(modules, dict):
        raise ValueError("exact_export.modules must be a dict")
    module_payload = modules.get(module_key)
    if not isinstance(module_payload, dict):
        raise ValueError(f"missing exact_export.modules.{module_key}")
    static_params = module_payload.get("static_params")
    if not isinstance(static_params, dict):
        raise ValueError(f"missing exact_export.modules.{module_key}.static_params")
    return static_params


def _build_static_params_type(
    *,
    module_id: str,
    module_key: str,
    module_name_fragment: str,
    field_bindings: list[dict[str, str]],
) -> type[StaticBoundaryParamsContract]:
    field_defs = [
        (binding["static_field_name"], object, field(default=None))
        for binding in field_bindings
    ]
    class_name = f"{module_name_fragment}StaticBoundaryParams"
    class_type = make_dataclass(
        class_name,
        field_defs,
        bases=(StaticBoundaryParamsContract,),
        frozen=True,
        slots=True,
    )
    setattr(class_type, "__module__", __name__)
    setattr(class_type, "framework_module_id", module_id)
    setattr(class_type, "module_key", module_key)
    setattr(
        class_type,
        "boundary_field_map",
        {binding["boundary_id"]: binding["static_field_name"] for binding in field_bindings},
    )
    return class_type


def _build_runtime_params_type(
    *,
    module_id: str,
    module_key: str,
    module_name_fragment: str,
    field_bindings: list[dict[str, str]],
) -> type[RuntimeBoundaryParamsContract]:
    field_defs = [
        (
            binding["runtime_field_name"],
            object,
            field(default=UNSET),
        )
        for binding in field_bindings
    ]
    class_name = f"{module_name_fragment}RuntimeBoundaryParams"
    class_type = make_dataclass(
        class_name,
        field_defs,
        bases=(RuntimeBoundaryParamsContract,),
        frozen=True,
        slots=True,
    )
    setattr(class_type, "__module__", __name__)
    setattr(class_type, "framework_module_id", module_id)
    setattr(class_type, "module_key", module_key)
    setattr(
        class_type,
        "boundary_field_map",
        {binding["boundary_id"]: binding["runtime_field_name"] for binding in field_bindings},
    )
    return class_type


def _build_base_contract_types(
    binding: ConfigModuleBinding,
    *,
    module_name_fragment: str,
) -> tuple[type[BaseContract], ...]:
    module_id = binding.framework_module.module_id
    records: list[type[BaseContract]] = []
    for base_class in binding.framework_module.base_classes:
        class_name = f"{module_name_fragment}{base_class.base_id}Base"
        records.append(
            type(
                class_name,
                (BaseContract,),
                {
                    "__module__": __name__,
                    "framework_base_id": f"{module_id}.{base_class.base_id}",
                    "framework_base_short_id": base_class.base_id,
                    "owner_module_id": module_id,
                    "boundary_ids": tuple(base_class.boundary_bindings),
                },
            )
        )
    return tuple(records)


def _build_rule_contract_types(
    binding: ConfigModuleBinding,
    *,
    module_name_fragment: str,
) -> tuple[type[RuleContract], ...]:
    module_id = binding.framework_module.module_id
    records: list[type[RuleContract]] = []
    for rule_class in binding.framework_module.rule_classes:
        class_name = f"{module_name_fragment}{rule_class.rule_id}Rule"
        records.append(
            type(
                class_name,
                (RuleContract,),
                {
                    "__module__": __name__,
                    "framework_rule_id": f"{module_id}.{rule_class.rule_id}",
                    "framework_rule_short_id": rule_class.rule_id,
                    "owner_module_id": module_id,
                    "base_ids": tuple(
                        f"{module_id}.{base_id}"
                        for base_id in rule_class.participant_bases
                    ),
                    "boundary_ids": tuple(rule_class.boundary_bindings),
                },
            )
        )
    return tuple(records)


def _build_module_contract_type(
    *,
    module_id: str,
    module_key: str,
    module_name_fragment: str,
    static_params_type: type[StaticBoundaryParamsContract],
    runtime_params_type: type[RuntimeBoundaryParamsContract],
    base_types: tuple[type[BaseContract], ...],
    rule_types: tuple[type[RuleContract], ...],
    field_bindings: list[dict[str, str]],
) -> type[ModuleContract]:
    class_name = f"{module_name_fragment}Module"
    return type(
        class_name,
        (ModuleContract,),
        {
            "__module__": __name__,
            "framework_module_id": module_id,
            "module_key": module_key,
            "StaticBoundaryParams": static_params_type,
            "RuntimeBoundaryParams": runtime_params_type,
            "BaseTypes": base_types,
            "RuleTypes": rule_types,
            "boundary_field_map": {
                item["boundary_id"]: item["static_field_name"]
                for item in field_bindings
            },
            "merge_policy": "runtime_override_else_static",
        },
    )


@dataclass(frozen=True)
class ModuleContractState:
    module_id: str
    module_key: str
    module_name_fragment: str
    field_bindings: tuple[dict[str, str], ...]
    static_params_type: type[StaticBoundaryParamsContract]
    runtime_params_type: type[RuntimeBoundaryParamsContract]
    base_types: tuple[type[BaseContract], ...]
    rule_types: tuple[type[RuleContract], ...]
    module_type: type[ModuleContract]
    static_params: StaticBoundaryParamsContract
    runtime_params: RuntimeBoundaryParamsContract
    boundary_context: dict[str, dict[str, Any]]


def _build_module_contract_state(binding: ConfigModuleBinding) -> ModuleContractState:
    module_id = binding.framework_module.module_id
    module_key = module_key_from_id(module_id)
    module_name_fragment = module_class_name_fragment(module_id)
    field_bindings = tuple(_module_field_bindings(binding))
    static_params_type: type[StaticBoundaryParamsContract]
    runtime_params_type: type[RuntimeBoundaryParamsContract]
    base_types: tuple[type[BaseContract], ...]
    rule_types: tuple[type[RuleContract], ...]
    module_type: type[ModuleContract]
    if module_id == BACKEND_L2_M0_MODULE_ID:
        static_params_type = BackendL2M0StaticBoundaryParams
        runtime_params_type = BackendL2M0DynamicBoundaryParams
        base_types = (
            BackendL2M0B1Base,
            BackendL2M0B2Base,
            BackendL2M0B3Base,
        )
        rule_types = (
            BackendL2M0R1Rule,
            BackendL2M0R2Rule,
            BackendL2M0R3Rule,
            BackendL2M0R4Rule,
        )
        module_type = BackendL2M0Module
    else:
        static_params_type = _build_static_params_type(
            module_id=module_id,
            module_key=module_key,
            module_name_fragment=module_name_fragment,
            field_bindings=list(field_bindings),
        )
        runtime_params_type = _build_runtime_params_type(
            module_id=module_id,
            module_key=module_key,
            module_name_fragment=module_name_fragment,
            field_bindings=list(field_bindings),
        )
        base_types = _build_base_contract_types(
            binding,
            module_name_fragment=module_name_fragment,
        )
        rule_types = _build_rule_contract_types(
            binding,
            module_name_fragment=module_name_fragment,
        )
        module_type = _build_module_contract_type(
            module_id=module_id,
            module_key=module_key,
            module_name_fragment=module_name_fragment,
            static_params_type=static_params_type,
            runtime_params_type=runtime_params_type,
            base_types=base_types,
            rule_types=rule_types,
            field_bindings=list(field_bindings),
        )
    raw_static_payload = _module_static_payload(binding.config_module.exact_export, module_key=module_key)
    static_payload: dict[str, Any] = {}
    for item in field_bindings:
        static_field = item["static_field_name"]
        if static_field not in raw_static_payload:
            raise ValueError(
                "missing static boundary value for "
                f"{module_id}:{item['boundary_id']} ({static_field})"
            )
        static_payload[static_field] = raw_static_payload[static_field]
    static_params = module_type.static_params_from_mapping(static_payload)
    runtime_params = module_type.runtime_params_default()
    boundary_context = module_type.build_boundary_context(static_params, runtime_params)
    return ModuleContractState(
        module_id=module_id,
        module_key=module_key,
        module_name_fragment=module_name_fragment,
        field_bindings=field_bindings,
        static_params_type=static_params_type,
        runtime_params_type=runtime_params_type,
        base_types=base_types,
        rule_types=rule_types,
        module_type=module_type,
        static_params=static_params,
        runtime_params=runtime_params,
        boundary_context=boundary_context,
    )


def _module_compile_symbol(module_id: str, root_module_ids: dict[str, str]) -> str:
    if module_id == root_module_ids.get("frontend"):
        return "project_runtime.code_layer:_compile_frontend_app_spec"
    if module_id == root_module_ids.get("knowledge_base"):
        return "project_runtime.code_layer:_compile_knowledge_base_domain_spec"
    if module_id == BACKEND_L2_M0_MODULE_ID:
        return "project_runtime.static_modules.backend_l2_m0:BackendL2M0Module.export_service_spec"
    if module_id == root_module_ids.get("backend"):
        return "project_runtime.code_layer:_compile_backend_service_spec"
    return "project_runtime.code_layer:build_code_modules"


def _module_runtime_slot_map(module_id: str, root_module_ids: dict[str, str]) -> dict[str, tuple[str, ...]]:
    if module_id == root_module_ids.get("frontend"):
        return {
            "SURFACE": (
                "frontend_app_spec.ui.shell",
                "frontend_app_spec.contract.surface_config",
                "frontend_app_spec.contract.surface_regions",
            ),
            "VISUAL": (
                "frontend_app_spec.ui.visual",
                "frontend_app_spec.contract.component_variants",
            ),
            "INTERACT": (
                "frontend_app_spec.ui.components.conversation_sidebar",
                "frontend_app_spec.ui.components.chat_composer",
                "frontend_app_spec.contract.interaction_actions",
            ),
            "STATE": (
                "frontend_app_spec.ui.components.message_stream",
                "frontend_app_spec.ui.conversation",
            ),
            "EXTEND": ("frontend_app_spec.contract.extend_slots",),
            "ROUTE": (
                "frontend_app_spec.ui.pages",
                "frontend_app_spec.contract.route_contract",
            ),
            "A11Y": ("frontend_app_spec.contract.a11y",),
        }
    if module_id == root_module_ids.get("knowledge_base"):
        return {
            "SURFACE": (
                "knowledge_base_domain_spec.workbench.layout_variant",
                "knowledge_base_domain_spec.workbench.surface",
                "knowledge_base_domain_spec.workbench.regions",
            ),
            "LIBRARY": (
                "knowledge_base_domain_spec.workbench.library",
                "knowledge_base_domain_spec.workbench.knowledge_bases",
                "knowledge_base_domain_spec.workbench.documents",
            ),
            "PREVIEW": ("knowledge_base_domain_spec.workbench.preview",),
            "CHAT": ("knowledge_base_domain_spec.workbench.chat",),
            "CONTEXT": ("knowledge_base_domain_spec.workbench.context",),
            "RETURN": (
                "knowledge_base_domain_spec.workbench.return",
                "knowledge_base_domain_spec.workbench.citation_return",
            ),
        }
    if module_id == root_module_ids.get("backend"):
        return {
            "LIBRARY": ("backend_service_spec.knowledge_base",),
            "PREVIEW": ("backend_service_spec.retrieval",),
            "CHAT": (
                "backend_service_spec.answer_policy",
                "backend_service_spec.return_policy",
            ),
            "RESULT": (
                "backend_service_spec.transport",
                "backend_service_spec.answer_policy",
                "backend_service_spec.interaction_copy",
            ),
            "AUTH": ("backend_service_spec.write_policy",),
            "TRACE": ("backend_service_spec.retrieval",),
        }
    return {}


def _boundary_slot_source_ref(
    module_id: str,
    boundary_id: str,
    *,
    root_module_ids: dict[str, str],
) -> dict[str, Any]:
    if module_id == BACKEND_L2_M0_MODULE_ID:
        needle_by_boundary = {
            "LIBRARY": "def knowledge_base_payload(",
            "PREVIEW": "def preview_retrieval_payload(",
            "CHAT": "def answer_policy_payload(",
            "RESULT": "def transport_payload(",
            "AUTH": "def write_policy_payload(",
            "TRACE": "def trace_retrieval_payload(",
        }
        fallback = _find_backend_l2_m0_line("class BackendL2M0Module(", fallback=1)
        line = _find_backend_l2_m0_line(needle_by_boundary.get(boundary_id, ""), fallback=fallback)
        return {
            "file_path": "src/project_runtime/static_modules/backend_l2_m0.py",
            "line": line,
            "section": "backend_l2_m0_module",
            "anchor": f"{module_id}:{boundary_id}",
            "token": boundary_id,
        }
    fallback_line = _find_code_line("def _build_implementation_slots(", fallback=1)
    needle = ""
    section = "implementation_slots"
    if module_id == root_module_ids.get("frontend"):
        needle = f'_require_boundary_context_value(boundary_context, "{boundary_id}")'
        section = "compile_frontend_app_spec"
    elif module_id == root_module_ids.get("knowledge_base"):
        needle = f'_require_boundary_context_value(boundary_context, "{boundary_id}")'
        section = "compile_knowledge_base_domain_spec"
    elif module_id == root_module_ids.get("backend"):
        needle = f'_require_boundary_context_value(boundary_context, "{boundary_id}")'
        section = "compile_backend_service_spec"
    line = _find_code_line(needle, fallback=fallback_line)
    return {
        "file_path": "src/project_runtime/code_layer.py",
        "line": line,
        "section": section,
        "anchor": f"{module_id}:{boundary_id}",
        "token": boundary_id,
    }


def _runtime_slot_source_ref(
    module_id: str,
    boundary_id: str,
    anchor_path: str,
) -> dict[str, Any]:
    if module_id == BACKEND_L2_M0_MODULE_ID:
        needle_by_anchor = {
            "backend_service_spec.knowledge_base": "def knowledge_base_payload(",
            "backend_service_spec.retrieval": "def export_service_spec(",
            "backend_service_spec.answer_policy": "def answer_policy_payload(",
            "backend_service_spec.return_policy": "def return_policy_payload(",
            "backend_service_spec.transport": "def transport_payload(",
            "backend_service_spec.interaction_copy": "def interaction_copy_payload(",
            "backend_service_spec.write_policy": "def write_policy_payload(",
        }
        fallback = _find_backend_l2_m0_line("def export_service_spec(", fallback=1)
        line = _find_backend_l2_m0_line(needle_by_anchor.get(anchor_path, ""), fallback=fallback)
        return {
            "file_path": "src/project_runtime/static_modules/backend_l2_m0.py",
            "line": line,
            "section": "backend_l2_m0_module",
            "anchor": f"{module_id}:{boundary_id}:{anchor_path}",
            "token": boundary_id,
        }
    fallback_line = _find_code_line("def _module_runtime_slot_map(", fallback=1)
    line = _find_code_line(f'"{anchor_path}"', fallback=fallback_line)
    return {
        "file_path": "src/project_runtime/code_layer.py",
        "line": line,
        "section": "runtime_slot_map",
        "anchor": f"{module_id}:{boundary_id}:{anchor_path}",
        "token": boundary_id,
    }


def _build_implementation_slots(
    binding: ConfigModuleBinding,
    *,
    root_module_ids: dict[str, str],
) -> list[dict[str, Any]]:
    exact_export = binding.config_module.exact_export
    module_key = str(
        exact_export.get("module_key")
        or module_key_from_id(binding.framework_module.module_id)
    )
    boundary_projections = exact_export.get("boundary_projections", {})
    if not isinstance(boundary_projections, dict):
        boundary_projections = {}
    slots: list[dict[str, Any]] = []
    runtime_slot_map = _module_runtime_slot_map(binding.framework_module.module_id, root_module_ids)
    compile_symbol = _module_compile_symbol(binding.framework_module.module_id, root_module_ids)
    for boundary in binding.framework_module.boundaries:
        projection = boundary_projections.get(boundary.boundary_id, {})
        if not isinstance(projection, dict):
            projection = {}
        related_exact_paths = projection.get("related_exact_paths", [])
        if not isinstance(related_exact_paths, list):
            related_exact_paths = []
        static_field_name = str(
            projection.get("static_field_name")
            or boundary_field_name(boundary.boundary_id)
        )
        exact_export_static_path = str(
            projection.get("exact_export_static_path")
            or (
                f"exact_export.modules.{module_key}."
                f"static_params.{static_field_name}"
            )
        )
        projection_paths = list(
            dict.fromkeys(
                [*related_exact_paths, exact_export_static_path]
            )
        )
        slots.append(
            {
                "slot_id": (
                    "code_slot::"
                    f"{binding.framework_module.module_id}::"
                    f"{boundary.boundary_id}::module_static_param"
                ),
                "slot_kind": "module_static_param",
                "boundary_id": boundary.boundary_id,
                "module_key": module_key,
                "field_name": static_field_name,
                "owner_id": f"code_owner::{binding.framework_module.module_id}",
                "source_symbol": (
                    f"{binding.framework_module.module_id}."
                    f"{exact_export_static_path}"
                ),
                "anchor_path": exact_export_static_path,
                "projection_paths": projection_paths,
                "source_ref": _boundary_slot_source_ref(
                    binding.framework_module.module_id,
                    boundary.boundary_id,
                    root_module_ids=root_module_ids,
                ),
            }
        )
        for anchor_path in runtime_slot_map.get(boundary.boundary_id, ()):
            slots.append(
                {
                    "slot_id": f"code_slot::{binding.framework_module.module_id}::{boundary.boundary_id}::{anchor_path}",
                    "slot_kind": "runtime_export",
                    "boundary_id": boundary.boundary_id,
                    "owner_id": f"code_owner::{binding.framework_module.module_id}",
                    "source_symbol": f"{compile_symbol}->{anchor_path}",
                    "anchor_path": anchor_path,
                    "projection_paths": list(dict.fromkeys(related_exact_paths)),
                    "source_ref": _runtime_slot_source_ref(
                        binding.framework_module.module_id,
                        boundary.boundary_id,
                        anchor_path,
                    ),
                }
            )
    return slots


def _build_boundary_code_classes(
    binding: ConfigModuleBinding,
    *,
    implementation_slots: list[dict[str, Any]],
) -> tuple[tuple[type[CodeBoundaryStaticClass], ...], tuple[type[CodeBoundaryRuntimeClass], ...]]:
    boundary_slots: dict[str, list[dict[str, Any]]] = {}
    for slot in implementation_slots:
        boundary_id = str(slot.get("boundary_id") or "").strip()
        if not boundary_id:
            continue
        boundary_slots.setdefault(boundary_id, []).append(slot)
    static_classes: list[type[CodeBoundaryStaticClass]] = []
    runtime_classes: list[type[CodeBoundaryRuntimeClass]] = []
    class_prefix = binding.framework_module.__name__.replace("FrameworkModule", "")
    for boundary in binding.framework_module.boundaries:
        boundary_id = boundary.boundary_id
        slots = boundary_slots.get(boundary_id, [])
        exact_slot = next(
            (
                slot
                for slot in slots
                if slot.get("slot_kind") == "module_static_param"
            ),
            None,
        )
        if not exact_slot:
            continue
        static_class_name = f"{class_prefix}{boundary_id}BoundaryStaticCode"
        static_class_id = f"code_boundary_static_class::{binding.framework_module.module_id}::{boundary_id}"
        static_class = type(
            static_class_name,
            (CodeBoundaryStaticClass,),
            {
                "class_id": static_class_id,
                "canonical_id": f"code_boundary_static::{binding.framework_module.module_id}::{boundary_id}",
                "module_id": binding.framework_module.module_id,
                "boundary_id": boundary_id,
                "owner_id": str(exact_slot.get("owner_id") or ""),
                "source_symbol": str(exact_slot.get("source_symbol") or ""),
                "anchor_path": str(exact_slot.get("anchor_path") or ""),
                "projection_paths": list(exact_slot.get("projection_paths") or []),
                "field_name": str(exact_slot.get("field_name") or ""),
                "source_ref": dict(exact_slot.get("source_ref") or {}),
            },
        )
        static_classes.append(static_class)
        runtime_slots = [
            {
                "slot_id": str(slot.get("slot_id") or ""),
                "source_symbol": str(slot.get("source_symbol") or ""),
                "anchor_path": str(slot.get("anchor_path") or ""),
                "slot_kind": str(slot.get("slot_kind") or ""),
            }
            for slot in slots
            if slot.get("slot_kind") == "runtime_export"
        ]
        runtime_class_name = f"{class_prefix}{boundary_id}BoundaryRuntimeCode"
        runtime_classes.append(
            type(
                runtime_class_name,
                (CodeBoundaryRuntimeClass,),
                {
                    "class_id": f"code_boundary_runtime_class::{binding.framework_module.module_id}::{boundary_id}",
                    "canonical_id": f"code_boundary_runtime::{binding.framework_module.module_id}::{boundary_id}",
                    "module_id": binding.framework_module.module_id,
                    "boundary_id": boundary_id,
                    "owner_id": str(exact_slot.get("owner_id") or ""),
                    "static_class_id": static_class_id,
                    "runtime_slots": runtime_slots,
                    "source_ref": dict(exact_slot.get("source_ref") or {}),
                },
            )
        )
    return tuple(static_classes), tuple(runtime_classes)


def _base_binding_records(
    binding: ConfigModuleBinding,
    *,
    class_name: str,
    implementation_slots: list[dict[str, Any]],
    root_module_ids: dict[str, str],
) -> list[dict[str, Any]]:
    slot_lookup = {slot["slot_id"]: slot for slot in implementation_slots}
    owner_id = f"code_owner::{binding.framework_module.module_id}"
    owner_source_symbol = _module_compile_symbol(binding.framework_module.module_id, root_module_ids)
    records: list[dict[str, Any]] = []
    for base_class in binding.framework_module.base_classes:
        boundary_ids = list(base_class.boundary_bindings)
        implementing_slot_ids = [
            slot["slot_id"]
            for slot in implementation_slots
            if slot["boundary_id"] in base_class.boundary_bindings
        ]
        bound_symbols = [
            str(slot_lookup[slot_id]["source_symbol"])
            for slot_id in implementing_slot_ids
            if slot_id in slot_lookup
        ]
        records.append(
            {
                "base_id": base_class.base_id,
                "base_class_id": base_class.class_id,
                "code_owner_id": owner_id,
                "code_owner_class_id": f"code_module_class::{binding.framework_module.module_id}",
                "code_owner_class_name": class_name,
                "binding_kind": "code_owner_slots",
                "boundary_ids": boundary_ids,
                "implementing_slot_ids": implementing_slot_ids,
                "bound_symbols": bound_symbols or [owner_source_symbol],
                "owner_source_symbol": owner_source_symbol,
            }
        )
    return records


def _rule_binding_records(
    binding: ConfigModuleBinding,
    *,
    class_name: str,
    implementation_slots: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    module_id = binding.framework_module.module_id
    boundary_slots_by_id: dict[str, list[str]] = {}
    for slot in implementation_slots:
        boundary_id = str(slot.get("boundary_id") or "")
        slot_id = str(slot.get("slot_id") or "")
        if not boundary_id or not slot_id:
            continue
        boundary_slots_by_id.setdefault(boundary_id, []).append(slot_id)
    records: list[dict[str, Any]] = []
    for rule_class in binding.framework_module.rule_classes:
        full_base_ids = tuple(f"{module_id}.{base_id}" for base_id in rule_class.participant_bases)
        boundary_ids = tuple(rule_class.boundary_bindings)
        slot_ids = [
            slot_id
            for boundary_id in boundary_ids
            for slot_id in boundary_slots_by_id.get(boundary_id, [])
        ]
        records.append(
            {
                "rule_id": f"{module_id}.{rule_class.rule_id}",
                "rule_short_id": rule_class.rule_id,
                "rule_class_id": rule_class.class_id,
                "owner_module_id": module_id,
                "owner_module_class_id": f"code_module_class::{module_id}",
                "owner_module_class_name": class_name,
                "base_ids": list(full_base_ids),
                "boundary_ids": list(boundary_ids),
                "implementation_slot_ids": slot_ids,
            }
        )
    return records


def build_code_modules(
    config_modules: tuple[ConfigModuleBinding, ...],
    *,
    root_module_ids: dict[str, str],
) -> tuple[tuple[CodeModuleBinding, ...], dict[str, Any]]:
    bindings: list[CodeModuleBinding] = []
    runtime_exports: dict[str, Any] = {}
    contract_state_by_module = {
        binding.framework_module.module_id: _build_module_contract_state(binding)
        for binding in config_modules
    }
    binding_by_module_id = {
        binding.framework_module.module_id: binding
        for binding in config_modules
    }
    frontend_root = binding_by_module_id.get(root_module_ids.get("frontend", ""))
    knowledge_root = binding_by_module_id.get(root_module_ids.get("knowledge_base", ""))
    backend_root = binding_by_module_id.get(root_module_ids.get("backend", ""))
    if frontend_root is None or knowledge_root is None or backend_root is None:
        raise ValueError("frontend, knowledge_base, and backend root modules are required")
    frontend_state = contract_state_by_module[frontend_root.framework_module.module_id]
    knowledge_state = contract_state_by_module[knowledge_root.framework_module.module_id]
    backend_state = contract_state_by_module[backend_root.framework_module.module_id]
    frontend_app_spec = _compile_frontend_app_spec(
        boundary_context=frontend_state.boundary_context,
        exact_export=frontend_root.config_module.exact_export,
        root_module_ids=root_module_ids,
    )
    route_contract = frontend_app_spec["contract"]["route_contract"]
    runtime_documents = _compile_runtime_documents(knowledge_root.config_module.exact_export)
    knowledge_base_domain_spec = _compile_knowledge_base_domain_spec(
        boundary_context=knowledge_state.boundary_context,
        exact_export=knowledge_root.config_module.exact_export,
        runtime_documents=runtime_documents,
    )
    if backend_root.framework_module.module_id == BACKEND_L2_M0_MODULE_ID:
        if not isinstance(backend_state.static_params, BackendL2M0StaticBoundaryParams):
            raise ValueError("backend.L2.M0 static params must be BackendL2M0StaticBoundaryParams")
        if not isinstance(backend_state.runtime_params, BackendL2M0DynamicBoundaryParams):
            raise ValueError("backend.L2.M0 runtime params must be BackendL2M0DynamicBoundaryParams")
        backend_module = BackendL2M0Module(
            static_params=backend_state.static_params,
            dynamic_params=backend_state.runtime_params,
        )
        backend_service_spec = backend_module.export_service_spec(
            exact_export=backend_root.config_module.exact_export,
            route_contract=route_contract,
        )
    else:
        backend_service_spec = _compile_backend_service_spec(
            boundary_context=backend_state.boundary_context,
            exact_export=backend_root.config_module.exact_export,
            route_contract=route_contract,
        )
    runtime_exports["frontend_app_spec"] = frontend_app_spec
    runtime_exports["knowledge_base_domain_spec"] = knowledge_base_domain_spec
    runtime_exports["runtime_documents"] = runtime_documents
    runtime_exports["backend_service_spec"] = backend_service_spec
    for binding in config_modules:
        module_id = binding.framework_module.module_id
        state = contract_state_by_module[module_id]
        module_key = state.module_key
        exact_export = binding.config_module.exact_export
        code_exports: dict[str, Any] = {}
        if module_id == root_module_ids.get("frontend"):
            code_exports["frontend_app_spec"] = frontend_app_spec
        if module_id == root_module_ids.get("knowledge_base"):
            code_exports["knowledge_base_domain_spec"] = knowledge_base_domain_spec
            code_exports["runtime_documents"] = runtime_documents
        if module_id == root_module_ids.get("backend"):
            code_exports["backend_service_spec"] = backend_service_spec
        module_name_fragment = state.module_name_fragment
        class_name = f"{module_name_fragment}CodeModule"
        implementation_slots = _build_implementation_slots(binding, root_module_ids=root_module_ids)
        field_bindings = list(state.field_bindings)
        static_params_type = state.static_params_type
        runtime_params_type = state.runtime_params_type
        base_types = state.base_types
        rule_types = state.rule_types
        module_type = state.module_type
        static_params = state.static_params
        runtime_params = state.runtime_params
        merged_boundary_context = state.boundary_context
        boundary_static_classes, boundary_runtime_classes = _build_boundary_code_classes(
            binding,
            implementation_slots=implementation_slots,
        )
        base_bindings = _base_binding_records(
            binding,
            class_name=class_name,
            implementation_slots=implementation_slots,
            root_module_ids=root_module_ids,
        )
        rule_bindings = _rule_binding_records(
            binding,
            class_name=class_name,
            implementation_slots=implementation_slots,
        )
        owner_source_symbol = _class_symbol(module_type)
        config_static_bindings = (
            binding.config_module.compiled_config_export.get("module_static_param_bindings")
            if isinstance(binding.config_module.compiled_config_export, dict)
            else []
        )
        if not isinstance(config_static_bindings, list):
            config_static_bindings = []
        config_static_by_boundary = {
            str(item.get("boundary_id") or ""): item
            for item in config_static_bindings
            if isinstance(item, dict)
        }
        boundary_param_bindings: list[dict[str, Any]] = []
        for item in field_bindings:
            boundary_id = item["boundary_id"]
            config_record = config_static_by_boundary.get(boundary_id, {})
            boundary_param_bindings.append(
                {
                    "boundary_id": boundary_id,
                    "owner_module_id": module_id,
                    "module_key": module_key,
                    "config_source_exact_path": str(
                        config_record.get("config_source_exact_path")
                        or binding.framework_module.boundary_projection_map.get(boundary_id, {}).get("primary_exact_path")
                        or ""
                    ),
                    "config_source_communication_path": str(
                        config_record.get("config_source_communication_path")
                        or binding.framework_module.boundary_projection_map.get(boundary_id, {}).get("primary_communication_path")
                        or ""
                    ),
                    "exact_export_static_path": str(
                        config_record.get("exact_export_static_path")
                        or item["exact_export_static_path"]
                    ),
                    "communication_export_static_path": str(
                        config_record.get("communication_export_static_path")
                        or item["communication_export_static_path"]
                    ),
                    "static_params_class_symbol": _class_symbol(static_params_type),
                    "runtime_params_class_symbol": _class_symbol(runtime_params_type),
                    "static_field_name": item["static_field_name"],
                    "runtime_field_name": item["runtime_field_name"],
                    "merge_policy": item["merge_policy"],
                }
            )
        module_class_binding = {
            "module_id": module_id,
            "module_key": module_key,
            "module_class_symbol": _class_symbol(module_type),
            "static_params_class_symbol": _class_symbol(static_params_type),
            "runtime_params_class_symbol": _class_symbol(runtime_params_type),
            "base_ids": [item.framework_base_id for item in base_types],
            "rule_ids": [item.framework_rule_id for item in rule_types],
            "boundary_ids": [item["boundary_id"] for item in field_bindings],
            "merge_policy": module_type.merge_policy,
        }
        base_class_bindings = [
            {
                "base_id": base_type.framework_base_id,
                "owner_module_id": base_type.owner_module_id,
                "base_class_symbol": _class_symbol(base_type),
                "boundary_ids": list(base_type.boundary_ids),
            }
            for base_type in base_types
        ]
        rule_class_bindings = [
            {
                "rule_id": rule_type.framework_rule_id,
                "owner_module_id": rule_type.owner_module_id,
                "rule_class_symbol": _class_symbol(rule_type),
                "base_ids": list(rule_type.base_ids),
                "boundary_ids": list(rule_type.boundary_ids),
            }
            for rule_type in rule_types
        ]
        source_ref: dict[str, Any] = {
            "file_path": "src/project_runtime/code_layer.py",
            "section": "code_module",
            "anchor": module_id,
            "token": module_id,
        }
        if module_id == BACKEND_L2_M0_MODULE_ID:
            source_ref = {
                "file_path": "src/project_runtime/static_modules/backend_l2_m0.py",
                "line": _find_backend_l2_m0_line("class BackendL2M0Module(", fallback=1),
                "section": "backend_l2_m0_module",
                "anchor": "class BackendL2M0Module",
                "token": module_id,
            }
        code_module = type(
            class_name,
            (CodeModuleClass,),
            {
                "class_id": f"code_module_class::{module_id}",
                "module_id": module_id,
                "module_key": module_key,
                "framework_file": binding.framework_module.framework_file,
                "source_ref": source_ref,
                "exact_export": exact_export,
                "code_exports": code_exports,
                "ModuleType": module_type,
                "StaticBoundaryParamsType": static_params_type,
                "RuntimeBoundaryParamsType": runtime_params_type,
                "BaseTypes": base_types,
                "RuleTypes": rule_types,
                "code_bindings": {
                    "module_class": class_name,
                    "module_class_id": f"code_module_class::{module_id}",
                    "source_symbol": owner_source_symbol,
                    "owner": {
                        "owner_id": f"code_owner::{module_id}",
                        "owner_class_id": f"code_module_class::{module_id}",
                        "owner_class_name": class_name,
                        "source_symbol": owner_source_symbol,
                    },
                    "module_class_binding": module_class_binding,
                    "base_class_bindings": base_class_bindings,
                    "rule_class_bindings": rule_class_bindings,
                    "boundary_param_bindings": boundary_param_bindings,
                    "implementation_slots": implementation_slots,
                    "base_bindings": base_bindings,
                    "rule_bindings": rule_bindings,
                    "static_params_instance": static_params.to_dict(),
                    "runtime_params_template": runtime_params.to_dict(),
                    "boundary_context": merged_boundary_context,
                },
                "boundary_static_classes": boundary_static_classes,
                "boundary_runtime_classes": boundary_runtime_classes,
            },
        )
        bindings.append(
            CodeModuleBinding(
                framework_module=binding.framework_module,
                config_module=binding.config_module,
                code_module=code_module,
            )
        )
    return tuple(bindings), runtime_exports
