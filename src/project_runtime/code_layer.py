from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from knowledge_base_runtime.runtime_profile import load_knowledge_base_runtime_profile

from project_runtime.config_layer import ConfigModuleBinding
from project_runtime.documents import export_documents
from project_runtime.framework_layer import FrameworkModuleClass
from project_runtime.models import KnowledgeDocument, SeedDocumentSource


class CodeModuleClass:
    class_id: str
    module_id: str
    framework_file: str
    source_ref: dict[str, Any]
    exact_export: dict[str, Any]
    code_exports: dict[str, Any]
    code_bindings: dict[str, Any]

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        return {
            "class_id": cls.class_id,
            "module_id": cls.module_id,
            "framework_file": cls.framework_file,
            "source_ref": dict(cls.source_ref),
            "exact_export": cls.exact_export,
            "code_exports": cls.code_exports,
            "code_bindings": cls.code_bindings,
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


def _require_boundary(exact_export: dict[str, Any], boundary_id: str) -> dict[str, Any]:
    boundaries = exact_export.get("boundaries")
    if not isinstance(boundaries, dict):
        raise ValueError("exact_export.boundaries must be a dict")
    value = boundaries.get(boundary_id)
    if not isinstance(value, dict):
        raise ValueError(f"missing exact boundary: {boundary_id}")
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
    exact_export: dict[str, Any],
    *,
    root_module_ids: dict[str, str],
) -> dict[str, Any]:
    profile = load_knowledge_base_runtime_profile()
    surface = _require_boundary(exact_export, "SURFACE")
    visual = _require_boundary(exact_export, "VISUAL")
    interact = _require_boundary(exact_export, "INTERACT")
    route = _require_boundary(exact_export, "ROUTE")
    a11y = _require_boundary(exact_export, "A11Y")
    state = _require_boundary(exact_export, "STATE")
    extend = _require_boundary(exact_export, "EXTEND")
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
    exact_export: dict[str, Any],
    *,
    runtime_documents: list[dict[str, Any]],
) -> dict[str, Any]:
    profile = load_knowledge_base_runtime_profile()
    surface = _require_boundary(exact_export, "SURFACE")
    library = _require_boundary(exact_export, "LIBRARY")
    preview = _require_boundary(exact_export, "PREVIEW")
    chat = _require_boundary(exact_export, "CHAT")
    context = _require_boundary(exact_export, "CONTEXT")
    return_policy = _require_boundary(exact_export, "RETURN")
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
    exact_export: dict[str, Any],
    *,
    route_contract: dict[str, Any],
) -> dict[str, Any]:
    profile = load_knowledge_base_runtime_profile()
    library = _require_boundary(exact_export, "LIBRARY")
    preview = _require_boundary(exact_export, "PREVIEW")
    chat = _require_boundary(exact_export, "CHAT")
    result = _require_boundary(exact_export, "RESULT")
    auth = _require_boundary(exact_export, "AUTH")
    trace = _require_boundary(exact_export, "TRACE")
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


def _module_compile_symbol(module_id: str, root_module_ids: dict[str, str]) -> str:
    if module_id == root_module_ids.get("frontend"):
        return "project_runtime.code_layer:_compile_frontend_app_spec"
    if module_id == root_module_ids.get("knowledge_base"):
        return "project_runtime.code_layer:_compile_knowledge_base_domain_spec"
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


def _build_implementation_slots(
    binding: ConfigModuleBinding,
    *,
    root_module_ids: dict[str, str],
) -> list[dict[str, Any]]:
    exact_export = binding.config_module.exact_export
    boundary_projections = exact_export.get("boundary_projections", {})
    if not isinstance(boundary_projections, dict):
        boundary_projections = {}
    slots: list[dict[str, Any]] = []
    runtime_slot_map = _module_runtime_slot_map(binding.framework_module.module_id, root_module_ids)
    compile_symbol = _module_compile_symbol(binding.framework_module.module_id, root_module_ids)
    for boundary in binding.framework_module.boundaries:
        projection = boundary_projections.get(boundary.boundary_id, {})
        related_exact_paths = projection.get("related_exact_paths", [])
        if not isinstance(related_exact_paths, list):
            related_exact_paths = []
        slots.append(
            {
                "slot_id": f"code_slot::{binding.framework_module.module_id}::{boundary.boundary_id}::exact_boundary",
                "slot_kind": "exact_boundary",
                "boundary_id": boundary.boundary_id,
                "owner_id": f"code_owner::{binding.framework_module.module_id}",
                "source_symbol": f"{binding.framework_module.module_id}.exact_export.boundaries.{boundary.boundary_id}",
                "anchor_path": f"exact_export.boundaries.{boundary.boundary_id}",
                "projection_paths": list(dict.fromkeys(related_exact_paths)),
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
                }
            )
    return slots


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


def build_code_modules(
    config_modules: tuple[ConfigModuleBinding, ...],
    *,
    root_module_ids: dict[str, str],
) -> tuple[tuple[CodeModuleBinding, ...], dict[str, Any]]:
    bindings: list[CodeModuleBinding] = []
    runtime_exports: dict[str, Any] = {}
    binding_by_module_id = {
        binding.framework_module.module_id: binding
        for binding in config_modules
    }
    frontend_root = binding_by_module_id.get(root_module_ids.get("frontend", ""))
    knowledge_root = binding_by_module_id.get(root_module_ids.get("knowledge_base", ""))
    backend_root = binding_by_module_id.get(root_module_ids.get("backend", ""))
    if frontend_root is None or knowledge_root is None or backend_root is None:
        raise ValueError("frontend, knowledge_base, and backend root modules are required")
    frontend_app_spec = _compile_frontend_app_spec(frontend_root.config_module.exact_export, root_module_ids=root_module_ids)
    route_contract = frontend_app_spec["contract"]["route_contract"]
    runtime_documents = _compile_runtime_documents(knowledge_root.config_module.exact_export)
    knowledge_base_domain_spec = _compile_knowledge_base_domain_spec(
        knowledge_root.config_module.exact_export,
        runtime_documents=runtime_documents,
    )
    backend_service_spec = _compile_backend_service_spec(
        backend_root.config_module.exact_export,
        route_contract=route_contract,
    )
    runtime_exports["frontend_app_spec"] = frontend_app_spec
    runtime_exports["knowledge_base_domain_spec"] = knowledge_base_domain_spec
    runtime_exports["runtime_documents"] = runtime_documents
    runtime_exports["backend_service_spec"] = backend_service_spec
    for binding in config_modules:
        exact_export = binding.config_module.exact_export
        code_exports: dict[str, Any] = {}
        if binding.framework_module.module_id == root_module_ids.get("frontend"):
            code_exports["frontend_app_spec"] = frontend_app_spec
        if binding.framework_module.module_id == root_module_ids.get("knowledge_base"):
            code_exports["knowledge_base_domain_spec"] = knowledge_base_domain_spec
            code_exports["runtime_documents"] = runtime_documents
        if binding.framework_module.module_id == root_module_ids.get("backend"):
            code_exports["backend_service_spec"] = backend_service_spec
        class_name = binding.framework_module.__name__.replace("FrameworkModule", "CodeModule")
        implementation_slots = _build_implementation_slots(binding, root_module_ids=root_module_ids)
        base_bindings = _base_binding_records(
            binding,
            class_name=class_name,
            implementation_slots=implementation_slots,
            root_module_ids=root_module_ids,
        )
        owner_source_symbol = _module_compile_symbol(binding.framework_module.module_id, root_module_ids)
        code_module = type(
            class_name,
            (CodeModuleClass,),
            {
                "class_id": f"code_module_class::{binding.framework_module.module_id}",
                "module_id": binding.framework_module.module_id,
                "framework_file": binding.framework_module.framework_file,
                "source_ref": {
                    "file_path": "src/project_runtime/code_layer.py",
                    "section": "code_module",
                    "anchor": binding.framework_module.module_id,
                    "token": binding.framework_module.module_id,
                },
                "exact_export": exact_export,
                "code_exports": code_exports,
                "code_bindings": {
                    "module_class": class_name,
                    "module_class_id": f"code_module_class::{binding.framework_module.module_id}",
                    "source_symbol": owner_source_symbol,
                    "owner": {
                        "owner_id": f"code_owner::{binding.framework_module.module_id}",
                        "owner_class_id": f"code_module_class::{binding.framework_module.module_id}",
                        "owner_class_name": class_name,
                        "source_symbol": owner_source_symbol,
                    },
                    "implementation_slots": implementation_slots,
                    "base_bindings": base_bindings,
                },
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
