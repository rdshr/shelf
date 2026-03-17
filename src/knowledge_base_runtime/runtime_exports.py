from __future__ import annotations

from typing import Any

from project_runtime.models import KnowledgeDocument, ProjectRuntimeAssembly


def resolve_runtime_blueprint(project: ProjectRuntimeAssembly) -> dict[str, Any]:
    return _require_dict_export(project, "runtime_blueprint")


def resolve_frontend_app_spec(project: ProjectRuntimeAssembly) -> dict[str, Any]:
    return _require_dict_export(project, "frontend_app_spec")


def resolve_knowledge_base_domain_spec(project: ProjectRuntimeAssembly) -> dict[str, Any]:
    return _require_dict_export(project, "knowledge_base_domain_spec")


def resolve_backend_service_spec(project: ProjectRuntimeAssembly) -> dict[str, Any]:
    return _require_dict_export(project, "backend_service_spec")


def resolve_runtime_documents(project: ProjectRuntimeAssembly) -> tuple[KnowledgeDocument, ...]:
    value = project.require_runtime_export("runtime_documents")
    if not isinstance(value, list):
        raise ValueError("runtime blueprint requires runtime_documents export")
    raw_documents = value
    if not isinstance(raw_documents, list):
        raise ValueError("runtime blueprint requires runtime_documents export")
    documents = tuple(
        KnowledgeDocument.from_dict(item)
        for item in raw_documents
        if isinstance(item, dict)
    )
    if not documents:
        raise ValueError("runtime blueprint requires at least one compiled document")
    return documents


def project_runtime_routes(project: ProjectRuntimeAssembly) -> dict[str, dict[str, str]]:
    frontend_spec = resolve_frontend_app_spec(project)
    service_spec = resolve_backend_service_spec(project)
    pages = _require_dict(frontend_spec, "ui", "frontend_app_spec.ui").get("pages")
    if not isinstance(pages, dict):
        raise ValueError("frontend_app_spec.ui.pages must be a dict")
    contract = frontend_spec.get("contract")
    if not isinstance(contract, dict):
        raise ValueError("frontend_app_spec.contract must be a dict")
    route_contract = contract.get("route_contract")
    if not isinstance(route_contract, dict):
        raise ValueError("frontend_app_spec.contract.route_contract must be a dict")
    transport = service_spec.get("transport")
    if not isinstance(transport, dict):
        raise ValueError("backend_service_spec.transport must be a dict")
    api_prefix = transport.get("api_prefix")
    project_config_endpoint = transport.get("project_config_endpoint")
    if not isinstance(api_prefix, str):
        raise ValueError("backend_service_spec.transport.api_prefix must be a string")
    if not isinstance(project_config_endpoint, str):
        raise ValueError("backend_service_spec.transport.project_config_endpoint must be a string")

    return {
        "pages": {
            "home": str(route_contract.get("home", "/")),
            "chat_home": _page_path(pages, "chat_home"),
            "basketball_showcase": _page_path(pages, "basketball_showcase"),
            "knowledge_list": _page_path(pages, "knowledge_list"),
            "knowledge_detail": _page_path(pages, "knowledge_detail"),
            "document_detail": _page_path(pages, "document_detail"),
        },
        "api": {
            "knowledge_bases": f"{api_prefix}/knowledge-bases",
            "knowledge_base_detail": f"{api_prefix}/knowledge-bases/{{knowledge_base_id}}",
            "documents": f"{api_prefix}/documents",
            "create_document": f"{api_prefix}/documents",
            "document_detail": f"{api_prefix}/documents/{{document_id}}",
            "delete_document": f"{api_prefix}/documents/{{document_id}}",
            "section_detail": f"{api_prefix}/documents/{{document_id}}/sections/{{section_id}}",
            "tags": f"{api_prefix}/tags",
            "chat_turns": f"{api_prefix}/chat/turns",
            "project_config": project_config_endpoint,
            "correspondence": f"{api_prefix}/correspondence",
            "correspondence_tree": f"{api_prefix}/correspondence/tree",
            "correspondence_object": f"{api_prefix}/correspondence/object/{{object_id}}",
        },
    }


def project_runtime_public_summary(project: ProjectRuntimeAssembly) -> dict[str, Any]:
    frontend_spec = resolve_frontend_app_spec(project)
    service_spec = resolve_backend_service_spec(project)
    documents = resolve_runtime_documents(project)
    blueprint = resolve_runtime_blueprint(project)
    ui = frontend_spec.get("ui", {})
    framework_modules = [item.to_dict() for item in project.config.framework_modules]
    return {
        "project_file": project.project_file,
        "project": project.metadata.to_dict(),
        "framework": framework_modules,
        "route": frontend_spec.get("contract", {}).get("route_contract", {}),
        "a11y": frontend_spec.get("contract", {}).get("a11y", {}),
        "routes": project_runtime_routes(project),
        "document_count": len(documents),
        "resolved_module_ids": sorted(project.root_module_ids.values()),
        "module_chain": ["framework", "config", "code", "evidence"],
        "frontend_summary": {
            "page_ids": list(ui.get("pages", {}).keys()) if isinstance(ui.get("pages"), dict) else [],
            "component_ids": list(ui.get("components", {}).keys()) if isinstance(ui.get("components"), dict) else [],
        },
        "runtime_summary": {
            "landing_path": blueprint.get("landing_path"),
            "page_route_ids": [
                item.get("route_id")
                for item in blueprint.get("page_routes", [])
                if isinstance(item, dict)
            ],
        },
        "backend_summary": {
            "retrieval": service_spec.get("retrieval", {}),
            "answer_policy": {
                "citation_style": service_spec.get("answer_policy", {}).get("citation_style"),
            },
        },
        "validation_reports": project.validation_reports.to_dict(),
        "generated_artifacts": project.generated_artifacts.to_dict() if project.generated_artifacts else None,
    }


def _require_dict_export(project: ProjectRuntimeAssembly, export_key: str) -> dict[str, Any]:
    value = project.require_runtime_export(export_key)
    if not isinstance(value, dict):
        raise ValueError(f"runtime export must be a dict: {export_key}")
    return dict(value)


def _page_path(pages: dict[str, Any], page_id: str) -> str:
    page = pages.get(page_id)
    if not isinstance(page, dict):
        raise ValueError(f"missing runtime page: {page_id}")
    path = page.get("path")
    if not isinstance(path, str):
        raise ValueError(f"runtime page path must be a string: {page_id}")
    return path


def _require_dict(payload: dict[str, Any], key: str, label: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a dict")
    return dict(value)
