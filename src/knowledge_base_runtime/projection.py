from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from project_runtime import KnowledgeDocument, ProjectRuntimeAssembly
from project_runtime.knowledge_base_contract import KnowledgeBaseTemplateContract, load_knowledge_base_template_contract


@dataclass(frozen=True)
class KnowledgeBaseRuntimeProjection:
    assembly: ProjectRuntimeAssembly
    template_contract: KnowledgeBaseTemplateContract
    documents: tuple[KnowledgeDocument, ...]
    frontend_contract: dict[str, Any]
    workbench_contract: dict[str, Any]
    ui_spec: dict[str, Any]
    backend_spec: dict[str, Any]
    copy: dict[str, str]

    @property
    def metadata(self) -> Any:
        return self.assembly.metadata

    @property
    def selection(self) -> Any:
        return self.assembly.selection

    @property
    def features(self) -> Any:
        return self.assembly.features

    @property
    def route(self) -> Any:
        return self.assembly.route

    @property
    def showcase_page(self) -> Any:
        return self.assembly.showcase_page

    @property
    def a11y(self) -> Any:
        return self.assembly.a11y

    @property
    def library(self) -> Any:
        return self.assembly.library

    @property
    def preview(self) -> Any:
        return self.assembly.preview

    @property
    def chat(self) -> Any:
        return self.assembly.chat

    @property
    def context(self) -> Any:
        return self.assembly.context

    @property
    def return_config(self) -> Any:
        return self.assembly.return_config

    @property
    def refinement(self) -> Any:
        return self.assembly.refinement

    @property
    def root_module_ids(self) -> dict[str, str]:
        return dict(self.assembly.root_module_ids)

    @property
    def package_compile_order(self) -> tuple[str, ...]:
        return self.assembly.package_compile_order

    @property
    def runtime_exports(self) -> dict[str, Any]:
        return self.assembly.runtime_exports

    @property
    def generated_artifacts(self) -> Any:
        return self.assembly.generated_artifacts

    @property
    def canonical_graph(self) -> dict[str, Any]:
        return self.assembly.canonical_graph

    @property
    def validation_reports(self) -> Any:
        return self.assembly.validation_reports

    def to_runtime_bundle_dict(self) -> dict[str, Any]:
        payload = self.assembly.to_runtime_bundle_dict()
        payload.update(
            {
                "documents": [item.to_dict() for item in self.documents],
                "frontend_contract": self.frontend_contract,
                "workbench_contract": self.workbench_contract,
                "ui_spec": self.ui_spec,
                "backend_spec": self.backend_spec,
                "derived_copy": dict(self.copy),
                "project_config": self.project_config_view,
            }
        )
        return payload

    def to_spec_dict(self) -> dict[str, Any]:
        return self.to_runtime_bundle_dict()

    @property
    def project_config_view(self) -> dict[str, Any]:
        return {
            "project": self.metadata.to_dict(),
            "selection": self.selection.to_dict(),
            "truth": self.assembly.config.truth_payload(),
            "refinement": self.refinement.to_dict(),
            "narrative": self.assembly.config.narrative,
            "interaction_model": {
                "workspace_flow": self.workbench_contract.get("flow", []),
                "citation_return": self.workbench_contract.get("citation_return_contract", {}),
                "surface_regions": self.frontend_contract.get("surface_regions", []),
                "interaction_actions": self.frontend_contract.get("interaction_actions", []),
            },
        }

    @property
    def public_summary(self) -> dict[str, Any]:
        return {
            "project_file": self.assembly.project_file,
            "project": self.metadata.to_dict(),
            "selection": self.selection.to_dict(),
            "route": self.route.to_dict(),
            "a11y": self.a11y.to_dict(),
            "routes": {
                **self.route.to_dict(),
                "pages": self.resolved_page_routes(),
                "api": self.resolved_api_routes(),
            },
            "document_count": len(self.documents),
            "resolved_module_ids": list(self.package_compile_order),
            "package_compile_order": list(self.package_compile_order),
            "ui_spec_summary": {
                "page_ids": list(self.ui_spec.get("pages", {}).keys()),
                "component_ids": list(self.ui_spec.get("components", {}).keys()),
            },
            "backend_spec_summary": {
                "retrieval": self.backend_spec.get("retrieval", {}),
                "answer_policy": {
                    "citation_style": self.backend_spec.get("answer_policy", {}).get("citation_style"),
                },
            },
            "validation_reports": self.validation_reports.to_dict(),
            "generated_artifacts": self.generated_artifacts.to_dict() if self.generated_artifacts else None,
        }

    def resolved_page_routes(self) -> dict[str, str]:
        return {
            "home": self.route.home,
            "chat_home": self.route.workbench,
            "basketball_showcase": self.route.basketball_showcase,
            "knowledge_list": self.route.knowledge_list,
            "knowledge_detail": f"{self.route.knowledge_detail}/{{knowledge_base_id}}",
            "document_detail": f"{self.route.document_detail_prefix}/{{document_id}}",
        }

    def resolved_api_routes(self) -> dict[str, str]:
        return {
            "knowledge_bases": f"{self.route.api_prefix}/knowledge-bases",
            "knowledge_base_detail": f"{self.route.api_prefix}/knowledge-bases/{{knowledge_base_id}}",
            "documents": f"{self.route.api_prefix}/documents",
            "create_document": f"{self.route.api_prefix}/documents",
            "document_detail": f"{self.route.api_prefix}/documents/{{document_id}}",
            "delete_document": f"{self.route.api_prefix}/documents/{{document_id}}",
            "section_detail": f"{self.route.api_prefix}/documents/{{document_id}}/sections/{{section_id}}",
            "tags": f"{self.route.api_prefix}/tags",
            "chat_turns": f"{self.route.api_prefix}/chat/turns",
            "project_config": self.refinement.evidence.project_config_endpoint,
        }


def resolve_knowledge_base_projection(assembly: ProjectRuntimeAssembly) -> KnowledgeBaseRuntimeProjection:
    raw_documents = assembly.require_runtime_export("documents")
    if not isinstance(raw_documents, list):
        raise ValueError("knowledge base runtime requires documents export")
    documents = tuple(
        KnowledgeDocument.from_dict(item)
        for item in raw_documents
        if isinstance(item, dict)
    )
    if not documents:
        raise ValueError("knowledge base runtime requires at least one document")
    frontend_contract = _require_dict_export(assembly, "frontend_contract")
    workbench_contract = _require_dict_export(assembly, "workbench_contract")
    ui_spec = _require_dict_export(assembly, "ui_spec")
    backend_spec = _require_dict_export(assembly, "backend_spec")
    copy = _require_dict_export(assembly, "derived_copy")
    return KnowledgeBaseRuntimeProjection(
        assembly=assembly,
        template_contract=load_knowledge_base_template_contract(),
        documents=documents,
        frontend_contract=frontend_contract,
        workbench_contract=workbench_contract,
        ui_spec=ui_spec,
        backend_spec=backend_spec,
        copy={str(key): str(value) for key, value in copy.items()},
    )


def _require_dict_export(assembly: ProjectRuntimeAssembly, export_key: str) -> dict[str, Any]:
    value = assembly.require_runtime_export(export_key)
    if not isinstance(value, dict):
        raise ValueError(f"knowledge base runtime requires dict export: {export_key}")
    return dict(value)
