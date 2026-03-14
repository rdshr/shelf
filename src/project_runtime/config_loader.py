from __future__ import annotations

from pathlib import Path
from typing import Any

from project_runtime.models import (
    A11yConfig,
    ArtifactConfig,
    BackendRefinementConfig,
    ChatConfig,
    ContextConfig,
    EvidenceRefinementConfig,
    FeatureConfig,
    FrontendRefinementConfig,
    LibraryConfig,
    ModuleSelection,
    PreviewConfig,
    ProjectMetadata,
    RefinementConfig,
    ReturnConfig,
    RouteConfig,
    SeedDocumentSource,
    SelectedRootModule,
    ShowcasePageConfig,
    SurfaceConfig,
    SurfaceCopyConfig,
    UnifiedProjectConfig,
    VisualConfig,
)
from project_runtime.project_config_source import ComposedTomlDocument, load_project_config_document
from project_runtime.utils import relative_path


def require_table(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"missing required table: {key}")
    return value


def optional_table(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"optional table must decode into object: {key}")
    return value


def require_string(parent: dict[str, Any], key: str) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing required string: {key}")
    return value.strip()


def require_bool(parent: dict[str, Any], key: str) -> bool:
    value = parent.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"missing required bool: {key}")
    return value


def require_int(parent: dict[str, Any], key: str) -> int:
    value = parent.get(key)
    if not isinstance(value, int):
        raise ValueError(f"missing required int: {key}")
    return value


def require_string_tuple(parent: dict[str, Any], key: str) -> tuple[str, ...]:
    value = parent.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"missing required string list: {key}")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{key} must only contain non-empty strings")
        items.append(item.strip())
    return tuple(items)


def require_documents(data: dict[str, Any]) -> tuple[SeedDocumentSource, ...]:
    value = data.get("documents")
    if not isinstance(value, list) or not value:
        raise ValueError("truth must define non-empty [[truth.documents]]")
    seen_ids: set[str] = set()
    items: list[SeedDocumentSource] = []
    for raw_document in value:
        if not isinstance(raw_document, dict):
            raise ValueError("each [[truth.documents]] entry must be a table")
        document = SeedDocumentSource(
            document_id=require_string(raw_document, "document_id"),
            title=require_string(raw_document, "title"),
            summary=require_string(raw_document, "summary"),
            body_markdown=require_string(raw_document, "body_markdown"),
            tags=require_string_tuple(raw_document, "tags"),
            updated_at=require_string(raw_document, "updated_at"),
        )
        if document.document_id in seen_ids:
            raise ValueError(f"duplicate document_id: {document.document_id}")
        seen_ids.add(document.document_id)
        items.append(document)
    return tuple(items)


def require_selection_roots(selection_table: dict[str, Any]) -> tuple[SelectedRootModule, ...]:
    raw_roots = selection_table.get("roots")
    if not isinstance(raw_roots, list) or not raw_roots:
        raise ValueError("selection must define non-empty [[selection.roots]]")
    roots: list[SelectedRootModule] = []
    seen_slots: set[str] = set()
    seen_roles: set[str] = set()
    for raw_root in raw_roots:
        if not isinstance(raw_root, dict):
            raise ValueError("each [[selection.roots]] entry must be a table")
        root = SelectedRootModule(
            slot_id=require_string(raw_root, "slot_id"),
            role=require_string(raw_root, "role"),
            framework_file=require_string(raw_root, "framework_file"),
        )
        if root.slot_id in seen_slots:
            raise ValueError(f"duplicate selection root slot_id: {root.slot_id}")
        if root.role in seen_roles:
            raise ValueError(f"duplicate selection root role: {root.role}")
        seen_slots.add(root.slot_id)
        seen_roles.add(root.role)
        roots.append(root)
    return tuple(roots)


def load_project_config(project_file: Path) -> UnifiedProjectConfig:
    document: ComposedTomlDocument = load_project_config_document(project_file)
    raw = document.merged_data
    project_table = require_table(raw, "project")
    selection_table = require_table(raw, "selection")
    truth_table = require_table(raw, "truth")
    surface_table = require_table(truth_table, "surface")
    surface_copy_table = require_table(surface_table, "copy")
    visual_table = require_table(truth_table, "visual")
    route_table = require_table(truth_table, "route")
    showcase_page_table = require_table(truth_table, "showcase_page")
    a11y_table = require_table(truth_table, "a11y")
    library_table = require_table(truth_table, "library")
    library_copy_table = require_table(library_table, "copy")
    preview_table = require_table(truth_table, "preview")
    chat_table = require_table(truth_table, "chat")
    chat_copy_table = require_table(chat_table, "copy")
    context_table = require_table(truth_table, "context")
    return_table = require_table(truth_table, "return")
    refinement_table = require_table(raw, "refinement")
    frontend_table = require_table(refinement_table, "frontend")
    backend_table = require_table(refinement_table, "backend")
    evidence_table = require_table(refinement_table, "evidence")
    artifacts_table = require_table(refinement_table, "artifacts")

    library_enabled = require_bool(library_table, "enabled")
    preview_enabled = require_bool(preview_table, "enabled")
    chat_enabled = require_bool(chat_table, "enabled")
    citations_enabled = require_bool(chat_table, "citations_enabled")
    return_enabled = require_bool(return_table, "enabled")
    allow_create = require_bool(library_table, "allow_create")
    allow_delete = require_bool(library_table, "allow_delete")

    truth_payload = {
        "surface": SurfaceConfig(
            shell=require_string(surface_table, "shell"),
            layout_variant=require_string(surface_table, "layout_variant"),
            sidebar_width=require_string(surface_table, "sidebar_width"),
            preview_mode=require_string(surface_table, "preview_mode"),
            density=require_string(surface_table, "density"),
            copy=SurfaceCopyConfig(
                hero_kicker=require_string(surface_copy_table, "hero_kicker"),
                hero_title=require_string(surface_copy_table, "hero_title"),
                hero_copy=require_string(surface_copy_table, "hero_copy"),
                library_title=require_string(surface_copy_table, "library_title"),
                preview_title=require_string(surface_copy_table, "preview_title"),
                toc_title=require_string(surface_copy_table, "toc_title"),
                chat_title=require_string(surface_copy_table, "chat_title"),
                empty_state_title=require_string(surface_copy_table, "empty_state_title"),
                empty_state_copy=require_string(surface_copy_table, "empty_state_copy"),
            ),
        ).to_dict(),
        "visual": VisualConfig(
            brand=require_string(visual_table, "brand"),
            accent=require_string(visual_table, "accent"),
            surface_preset=require_string(visual_table, "surface_preset"),
            radius_scale=require_string(visual_table, "radius_scale"),
            shadow_level=require_string(visual_table, "shadow_level"),
            font_scale=require_string(visual_table, "font_scale"),
        ).to_dict(),
        "features": FeatureConfig(
            library=library_enabled,
            preview=preview_enabled,
            chat=chat_enabled,
            citation=citations_enabled,
            return_to_anchor=return_enabled,
            upload=allow_create or allow_delete,
        ).to_dict(),
        "route": RouteConfig(
            home=require_string(route_table, "home"),
            workbench=require_string(route_table, "workbench"),
            basketball_showcase=require_string(route_table, "basketball_showcase"),
            knowledge_list=require_string(route_table, "knowledge_list"),
            knowledge_detail=require_string(route_table, "knowledge_detail"),
            document_detail_prefix=require_string(route_table, "document_detail_prefix"),
            api_prefix=require_string(route_table, "api_prefix"),
        ).to_dict(),
        "showcase_page": ShowcasePageConfig(
            title=require_string(showcase_page_table, "title"),
            kicker=require_string(showcase_page_table, "kicker"),
            headline=require_string(showcase_page_table, "headline"),
            intro=require_string(showcase_page_table, "intro"),
            back_to_chat_label=require_string(showcase_page_table, "back_to_chat_label"),
            browse_knowledge_label=require_string(showcase_page_table, "browse_knowledge_label"),
        ).to_dict(),
        "a11y": A11yConfig(
            reading_order=require_string_tuple(a11y_table, "reading_order"),
            keyboard_nav=require_string_tuple(a11y_table, "keyboard_nav"),
            announcements=require_string_tuple(a11y_table, "announcements"),
        ).to_dict(),
        "library": LibraryConfig(
            knowledge_base_id=require_string(library_table, "knowledge_base_id"),
            knowledge_base_name=require_string(library_table, "knowledge_base_name"),
            knowledge_base_description=require_string(library_table, "knowledge_base_description"),
            enabled=library_enabled,
            source_types=require_string_tuple(library_table, "source_types"),
            metadata_fields=require_string_tuple(library_table, "metadata_fields"),
            default_focus=require_string(library_table, "default_focus"),
            list_variant=require_string(library_table, "list_variant"),
            allow_create=allow_create,
            allow_delete=allow_delete,
            search_placeholder=require_string(library_copy_table, "search_placeholder"),
        ).to_dict(),
        "preview": PreviewConfig(
            enabled=preview_enabled,
            renderers=require_string_tuple(preview_table, "renderers"),
            anchor_mode=require_string(preview_table, "anchor_mode"),
            show_toc=require_bool(preview_table, "show_toc"),
            preview_variant=require_string(preview_table, "preview_variant"),
        ).to_dict(),
        "chat": ChatConfig(
            enabled=chat_enabled,
            citations_enabled=citations_enabled,
            mode=require_string(chat_table, "mode"),
            citation_style=require_string(chat_table, "citation_style"),
            bubble_variant=require_string(chat_table, "bubble_variant"),
            composer_variant=require_string(chat_table, "composer_variant"),
            system_prompt=require_string(chat_table, "system_prompt"),
            placeholder=require_string(chat_copy_table, "placeholder"),
            welcome=require_string(chat_copy_table, "welcome"),
            welcome_prompts=require_string_tuple(chat_table, "welcome_prompts"),
        ).to_dict(),
        "context": ContextConfig(
            selection_mode=require_string(context_table, "selection_mode"),
            max_citations=require_int(context_table, "max_citations"),
            max_preview_sections=require_int(context_table, "max_preview_sections"),
            sticky_document=require_bool(context_table, "sticky_document"),
        ).to_dict(),
        "return": ReturnConfig(
            enabled=return_enabled,
            targets=require_string_tuple(return_table, "targets"),
            anchor_restore=require_bool(return_table, "anchor_restore"),
            citation_card_variant=require_string(return_table, "citation_card_variant"),
        ).to_dict(),
        "documents": [item.to_dict() for item in require_documents(truth_table)],
    }
    artifact_config = ArtifactConfig(
        canonical_graph_json=require_string(artifacts_table, "canonical_graph_json"),
        runtime_snapshot_py=require_string(artifacts_table, "runtime_snapshot_py"),
        generation_manifest_json=require_string(artifacts_table, "generation_manifest_json"),
        derived_governance_manifest_json=require_string(
            artifacts_table,
            "derived_governance_manifest_json",
        ),
        derived_governance_tree_json=require_string(
            artifacts_table,
            "derived_governance_tree_json",
        ),
        strict_zone_report_json=require_string(artifacts_table, "strict_zone_report_json"),
        object_coverage_report_json=require_string(artifacts_table, "object_coverage_report_json"),
    )
    refinement_payload = RefinementConfig(
        frontend=FrontendRefinementConfig(
            renderer=require_string(frontend_table, "renderer"),
            style_profile=require_string(frontend_table, "style_profile"),
            script_profile=require_string(frontend_table, "script_profile"),
        ),
        backend=BackendRefinementConfig(
            renderer=require_string(backend_table, "renderer"),
            transport=require_string(backend_table, "transport"),
            retrieval_strategy=require_string(backend_table, "retrieval_strategy"),
        ),
        evidence=EvidenceRefinementConfig(
            project_config_endpoint=require_string(evidence_table, "project_config_endpoint"),
        ),
        artifacts=artifact_config,
    ).to_dict()

    return UnifiedProjectConfig(
        project_file=relative_path(project_file),
        section_sources={
            section_name: relative_path(document.source_file_for_section(section_name))
            for section_name in raw
        },
        metadata=ProjectMetadata(
            project_id=require_string(project_table, "project_id"),
            runtime_scene=require_string(project_table, "runtime_scene"),
            display_name=require_string(project_table, "display_name"),
            description=require_string(project_table, "description"),
            version=require_string(project_table, "version"),
        ),
        selection=ModuleSelection(
            preset=require_string(selection_table, "preset"),
            roots=require_selection_roots(selection_table),
        ),
        truth=truth_payload,
        refinement=refinement_payload,
        artifact_config=artifact_config,
        narrative=optional_table(raw, "narrative"),
    )
