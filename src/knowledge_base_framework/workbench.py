from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from project_runtime.knowledge_base import KnowledgeBaseProject


# @governed_symbol id=kb.workbench.surface_contract owner=framework kind=surface_contract risk=high
def build_workbench_contract(project: "KnowledgeBaseProject") -> dict[str, Any]:
    contract = project.template_contract
    library_actions = list(
        contract.workbench_library_actions(
            allow_create=project.library.allow_create,
            allow_delete=project.library.allow_delete,
        )
    )
    flow = project.backend_spec.get("interaction_flow", list(contract.workbench_flow_dicts()))

    return {
        "module_id": project.domain_ir.module_id,
        "layout_variant": project.surface.layout_variant,
        "regions": list(contract.workbench_region_ids),
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
            "query_keys": list(contract.workbench_citation_query_keys),
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
