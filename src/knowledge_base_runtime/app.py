from __future__ import annotations

from dataclasses import dataclass
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from knowledge_base_runtime.backend import KnowledgeRepository, build_knowledge_base_router
from knowledge_base_runtime.frontend import (
    compose_basketball_showcase_page,
    compose_document_detail_page,
    compose_knowledge_base_detail_page,
    compose_knowledge_base_list_page,
    compose_knowledge_base_page,
)
from project_runtime.knowledge_base import KnowledgeBaseCodeModule, materialize_knowledge_base_code_module


@dataclass(frozen=True)
class BackendTransportContract:
    mode: str
    product_spec_endpoint: str


def _require_backend_transport(code_module: KnowledgeBaseCodeModule) -> BackendTransportContract:
    transport = code_module.backend_spec.get("transport")
    if not isinstance(transport, dict):
        raise ValueError("backend_spec.transport is required for runtime app construction")
    mode = transport.get("mode")
    if not isinstance(mode, str):
        raise ValueError("backend_spec.transport.mode must be a string")
    if mode not in code_module.template_contract.supported_backend_transports:
        raise ValueError(f"unsupported backend transport: {mode}")
    product_spec_endpoint = transport.get("product_spec_endpoint")
    if not isinstance(product_spec_endpoint, str) or not product_spec_endpoint.startswith(code_module.route.api_prefix):
        raise ValueError("backend_spec.transport.product_spec_endpoint must stay under route.api_prefix")
    return BackendTransportContract(mode=mode, product_spec_endpoint=product_spec_endpoint)


def build_knowledge_base_runtime_app(project: KnowledgeBaseCodeModule | None = None) -> FastAPI:
    resolved = project or materialize_knowledge_base_code_module()
    transport = _require_backend_transport(resolved)
    repository = KnowledgeRepository(resolved)
    app = FastAPI(
        title=resolved.metadata.display_name,
        summary=resolved.metadata.description,
        version=resolved.metadata.version,
    )
    app.include_router(build_knowledge_base_router(resolved, repository))

    # @governed_symbol id=kb.runtime.page_routes owner=framework kind=runtime_routes risk=high
    @app.get(resolved.route.home, include_in_schema=False)
    def root() -> dict[str, object]:
        return {
            "project": resolved.public_summary,
            "frontend": resolved.route.workbench,
            "product_spec": transport.product_spec_endpoint,
        }

    # @governed_symbol id=kb.runtime.page_routes owner=framework kind=runtime_routes risk=high
    @app.get(resolved.route.workbench, response_class=HTMLResponse, include_in_schema=False)
    def knowledge_base_page() -> str:
        return compose_knowledge_base_page(resolved)

    # @governed_symbol id=kb.runtime.page_routes owner=framework kind=runtime_routes risk=high
    @app.get(resolved.route.basketball_showcase, response_class=HTMLResponse, include_in_schema=False)
    def basketball_showcase_page() -> str:
        return compose_basketball_showcase_page(resolved)

    # @governed_symbol id=kb.runtime.page_routes owner=framework kind=runtime_routes risk=high
    @app.get(resolved.route.knowledge_list, response_class=HTMLResponse, include_in_schema=False)
    def knowledge_base_list_page() -> str:
        return compose_knowledge_base_list_page(resolved, repository)

    # @governed_symbol id=kb.runtime.page_routes owner=framework kind=runtime_routes risk=high
    @app.get(f"{resolved.route.knowledge_detail}/{{knowledge_base_id}}", response_class=HTMLResponse, include_in_schema=False)
    def knowledge_base_detail_page(knowledge_base_id: str) -> str:
        knowledge_base = repository.get_knowledge_base(knowledge_base_id)
        if knowledge_base is None:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        return compose_knowledge_base_detail_page(resolved, knowledge_base)

    # @governed_symbol id=kb.runtime.page_routes owner=framework kind=runtime_routes risk=high
    @app.get(
        f"{resolved.route.document_detail_prefix}/{{document_id}}",
        response_class=HTMLResponse,
        include_in_schema=False,
    )
    def document_detail_page(document_id: str, section: str | None = None) -> str:
        document = repository.get_document(document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found")
        return compose_document_detail_page(resolved, document, active_section_id=section)

    # @governed_symbol id=kb.runtime.page_routes owner=framework kind=runtime_routes risk=high
    @app.get(transport.product_spec_endpoint)
    def product_spec() -> dict[str, object]:
        return resolved.product_view

    return app
