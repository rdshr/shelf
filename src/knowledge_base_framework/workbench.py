from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from project_runtime.knowledge_base import KnowledgeBaseProject


def build_workbench_contract(project: "KnowledgeBaseProject") -> dict[str, Any]:
    library_actions = ["switch_knowledge_base", "browse_documents", "open_document_detail"]
    if project.library.allow_create:
        library_actions.append("create_document")
    if project.library.allow_delete:
        library_actions.append("delete_document")
    flow = project.backend_spec.get(
        "interaction_flow",
        [
            {
                "stage_id": "knowledge_base_select",
                "depends_on": [],
                "produces": ["knowledge_base_id"],
            },
            {
                "stage_id": "conversation",
                "depends_on": ["knowledge_base_id"],
                "produces": ["conversation_id", "answer", "citations"],
            },
            {
                "stage_id": "citation_review",
                "depends_on": ["conversation_id", "citations"],
                "produces": ["document_id", "section_id", "drawer_state"],
            },
            {
                "stage_id": "document_detail",
                "depends_on": ["document_id", "section_id"],
                "produces": ["document_page", "return_path"],
            },
        ],
    )

    return {
        "module_id": project.domain_ir.module_id,
        "layout_variant": project.surface.layout_variant,
        "regions": [
            "conversation_sidebar",
            "chat_main",
            "citation_drawer",
            "knowledge_list_page",
            "knowledge_detail_page",
            "document_detail_page",
        ],
        "surface": {
            "sidebar_width": project.surface.sidebar_width,
            "preview_mode": project.surface.preview_mode,
            "density": project.surface.density,
        },
        "library": {
            **project.library.to_dict(),
            "actions": library_actions,
        },
        "preview": project.preview.to_dict(),
        "chat": project.chat.to_dict(),
        "context": project.context.to_dict(),
        "return": project.return_config.to_dict(),
        "flow": flow,
        "citation_return_contract": {
            "query_keys": ["document", "section", "citation"],
            "targets": list(project.return_config.targets),
            "anchor_restore": project.return_config.anchor_restore,
        },
        "knowledge_bases": [
            {
                "knowledge_base_id": project.library.knowledge_base_id,
                "name": project.library.knowledge_base_name,
                "description": project.library.knowledge_base_description,
                "document_count": len(project.documents),
            }
        ],
        "documents": [
            {
                "document_id": item.document_id,
                "title": item.title,
                "section_ids": [section.section_id for section in item.sections],
                "section_count": len(item.sections),
            }
            for item in project.documents
        ],
        "base_ids": [item.base_id for item in project.domain_ir.bases],
        "rule_ids": [item.rule_id for item in project.domain_ir.rules],
    }
