from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from project_runtime.knowledge_base import KnowledgeBaseProject


# @governed_symbol id=kb.frontend.surface_contract owner=framework kind=surface_contract risk=high
def build_frontend_contract(project: "KnowledgeBaseProject") -> dict[str, Any]:
    contract = project.template_contract
    interaction_actions = list(
        contract.frontend_interaction_actions(
            allow_create=project.library.allow_create,
            allow_delete=project.library.allow_delete,
        )
    )
    surface_region_titles = {
        "conversation_sidebar": "Conversation Sidebar",
        "chat_main": project.copy["chat_title"],
        "citation_drawer": project.copy["preview_title"],
        "knowledge_pages": project.copy["library_title"],
    }

    return {
        "module_id": project.frontend_ir.module_id,
        "shell": project.surface.shell,
        "preset": project.framework.preset,
        "layout_variant": project.surface.layout_variant,
        "surface_config": {
            "sidebar_width": project.surface.sidebar_width,
            "preview_mode": project.surface.preview_mode,
            "density": project.surface.density,
        },
        "visual_config": project.visual.to_dict(),
        "surface_composition": {
            "sidebar": list(contract.surface_composition_sidebar),
            "main": list(contract.surface_composition_main),
            "overlay": list(contract.surface_composition_overlay),
            "secondary_pages": [
                "basketball_showcase_page",
                "knowledge_list_page",
                "knowledge_detail_page",
                "document_detail_page",
            ],
        },
        "surface_regions": [
            {"region_id": region_id, "title": surface_region_titles[region_id], "boundary": "SURFACE"}
            for region_id in contract.required_surface_region_ids
        ],
        "interaction_actions": interaction_actions,
        "state_channels": list(contract.resolve_state_channels(sticky_document=project.context.sticky_document)),
        "extend_slots": [
            {"slot_id": "domain_workbench", "module_id": project.domain_ir.module_id},
            {"slot_id": "backend_contract", "module_id": project.backend_ir.module_id},
        ],
        "route_contract": project.route.to_dict(),
        "a11y": project.a11y.to_dict(),
        "component_variants": {
            "conversation_list": project.library.list_variant,
            "preview_surface": project.preview.preview_variant,
            "chat_bubble": project.chat.bubble_variant,
            "chat_composer": project.chat.composer_variant,
            "citation_summary": project.return_config.citation_card_variant,
        },
        "base_ids": [item.base_id for item in project.frontend_ir.bases],
        "rule_ids": [item.rule_id for item in project.frontend_ir.rules],
    }
