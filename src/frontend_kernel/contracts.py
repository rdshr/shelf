from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from project_runtime.knowledge_base import KnowledgeBaseProject


def build_frontend_contract(project: "KnowledgeBaseProject") -> dict[str, Any]:
    interaction_actions = [
        {"action_id": "start_new_chat", "boundary": "INTERACT"},
        {"action_id": "select_session", "boundary": "INTERACT"},
        {"action_id": "open_knowledge_switch", "boundary": "INTERACT"},
        {"action_id": "search_documents", "boundary": "INTERACT"},
        {"action_id": "select_document", "boundary": "INTERACT"},
        {"action_id": "submit_chat", "boundary": "INTERACT"},
        {"action_id": "open_citation_drawer", "boundary": "INTERACT"},
        {"action_id": "browse_knowledge_bases", "boundary": "ROUTE"},
        {"action_id": "open_knowledge_base_detail", "boundary": "ROUTE"},
        {"action_id": "open_document_detail", "boundary": "ROUTE"},
        {"action_id": "return_from_citation", "boundary": "ROUTE"},
    ]
    if project.library.allow_create:
        interaction_actions.append({"action_id": "create_document", "boundary": "INTERACT"})
    if project.library.allow_delete:
        interaction_actions.append({"action_id": "delete_document", "boundary": "INTERACT"})
    if project.auth.enabled:
        interaction_actions.extend(
            [
                {"action_id": "open_login", "boundary": "ROUTE"},
                {"action_id": "complete_login", "boundary": "INTERACT"},
                {"action_id": "sign_out", "boundary": "INTERACT"},
            ]
        )

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
            "sidebar": ["conversation_sidebar"],
            "main": ["chat_header", "message_stream", "chat_composer"],
            "overlay": ["citation_drawer", "knowledge_switch_dialog"],
            "secondary_pages": [
                "knowledge_list_page",
                "knowledge_detail_page",
                "document_detail_page",
            ],
        },
        "surface_regions": [
            {"region_id": "conversation_sidebar", "title": "Conversation Sidebar", "boundary": "SURFACE"},
            {"region_id": "chat_main", "title": project.copy["chat_title"], "boundary": "SURFACE"},
            {"region_id": "citation_drawer", "title": project.copy["preview_title"], "boundary": "SURFACE"},
            {"region_id": "knowledge_pages", "title": project.copy["library_title"], "boundary": "SURFACE"},
        ],
        "interaction_actions": interaction_actions,
        "state_channels": [
            {"state_id": "session_state", "sticky": True},
            {"state_id": "current_conversation", "sticky": True},
            {"state_id": "current_knowledge_base", "sticky": True},
            {"state_id": "current_document", "sticky": project.context.sticky_document},
            {"state_id": "current_section", "sticky": True},
            {"state_id": "citation_drawer_state", "sticky": True},
            {"state_id": "streaming_reply", "sticky": False},
        ],
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
