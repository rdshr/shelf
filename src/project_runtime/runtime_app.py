from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from project_runtime.compiler import load_project_runtime
from project_runtime.correspondence_view import build_correspondence_view
from project_runtime.models import ProjectRuntimeAssembly


@dataclass(frozen=True)
class RuntimeRouteSpec:
    route_id: str
    path: str
    handler_factory_path: str
    response_class: str | None = None


@dataclass(frozen=True)
class RuntimeBlueprint:
    mode: str
    project_config_endpoint: str
    landing_path: str
    summary_factory_path: str
    repository_factory_path: str | None
    api_router_factory_path: str | None
    page_routes: tuple[RuntimeRouteSpec, ...]


def project_runtime_public_summary(project: ProjectRuntimeAssembly) -> dict[str, object]:
    return project.public_summary


def build_project_runtime_app(project: ProjectRuntimeAssembly | None = None) -> FastAPI:
    assembly = project or load_project_runtime()
    blueprint = _load_runtime_blueprint(assembly)
    root_path = _load_root_path(assembly)
    _api_prefix, correspondence_endpoint = _resolve_correspondence_endpoint(assembly, blueprint)
    correspondence_view = _resolve_correspondence_view(assembly)
    app = FastAPI(
        title=assembly.metadata.display_name,
        summary=assembly.metadata.description,
        version=assembly.metadata.version,
    )
    repository = None
    if blueprint.repository_factory_path is not None:
        repository_factory = _load_callable(blueprint.repository_factory_path)
        repository = repository_factory(assembly)
    if blueprint.api_router_factory_path is not None:
        router_factory = _load_callable(blueprint.api_router_factory_path)
        app.include_router(router_factory(assembly, repository))
    summary_factory = _load_callable(blueprint.summary_factory_path)

    @app.get(root_path, include_in_schema=False)
    def root() -> dict[str, object]:
        return {
            "project": summary_factory(assembly),
            "frontend": blueprint.landing_path,
            "project_config": blueprint.project_config_endpoint,
            "correspondence": correspondence_endpoint,
        }

    for route_spec in blueprint.page_routes:
        handler_factory = _load_callable(route_spec.handler_factory_path)
        handler = handler_factory(assembly, repository)
        route_kwargs: dict[str, Any] = {
            "endpoint": handler,
            "methods": ["GET"],
            "include_in_schema": False,
        }
        response_class = _resolve_response_class(route_spec.response_class)
        if response_class is not None:
            route_kwargs["response_class"] = response_class
        app.add_api_route(route_spec.path, **route_kwargs)

    @app.get(blueprint.project_config_endpoint)
    def project_config() -> dict[str, object]:
        return assembly.project_config_view

    @app.get(correspondence_endpoint)
    def correspondence() -> dict[str, object]:
        return correspondence_view

    @app.get(f"{correspondence_endpoint}/tree")
    def correspondence_tree() -> dict[str, object]:
        return {
            "correspondence_schema_version": correspondence_view.get("correspondence_schema_version"),
            "tree": correspondence_view.get("tree", []),
            "validation_summary": correspondence_view.get("validation_summary", {}),
        }

    @app.get(f"{correspondence_endpoint}/object/{{object_id:path}}")
    def correspondence_object(object_id: str) -> dict[str, object]:
        index = correspondence_view.get("object_index")
        if not isinstance(index, dict):
            raise HTTPException(status_code=500, detail="correspondence object index is missing")
        payload = index.get(object_id)
        if not isinstance(payload, dict):
            raise HTTPException(status_code=404, detail=f"correspondence object not found: {object_id}")
        return payload

    return app


def build_project_app_from_project_file(project_file: str | Path | None = None) -> FastAPI:
    return build_project_runtime_app(load_project_runtime(project_file))


def _load_runtime_blueprint(project: ProjectRuntimeAssembly) -> RuntimeBlueprint:
    value = project.runtime_exports.get("runtime_blueprint")
    if value is None:
        return RuntimeBlueprint(
            mode="standalone",
            project_config_endpoint="/project/config",
            landing_path="/",
            summary_factory_path="project_runtime.runtime_app:project_runtime_public_summary",
            repository_factory_path=None,
            api_router_factory_path=None,
            page_routes=tuple(),
        )
    if not isinstance(value, dict):
        raise ValueError("runtime_blueprint export is required for runtime app construction")
    transport = value.get("transport")
    if not isinstance(transport, dict):
        raise ValueError("runtime_blueprint.transport is required for runtime app construction")
    raw_page_routes = value.get("page_routes")
    if raw_page_routes is None:
        raw_page_routes = []
    if not isinstance(raw_page_routes, list):
        raise ValueError("runtime_blueprint.page_routes must be a list")
    page_routes = tuple(
        RuntimeRouteSpec(
            route_id=str(item["route_id"]),
            path=str(item["path"]),
            handler_factory_path=str(item["handler_factory"]),
            response_class=str(item["response_class"]) if item.get("response_class") is not None else None,
        )
        for item in raw_page_routes
        if isinstance(item, dict)
    )
    return RuntimeBlueprint(
        mode=str(transport["mode"]),
        project_config_endpoint=str(transport["project_config_endpoint"]),
        landing_path=str(value["landing_path"]),
        summary_factory_path=str(value["summary_factory"]),
        repository_factory_path=(
            str(value["repository_factory"])
            if value.get("repository_factory") is not None
            else None
        ),
        api_router_factory_path=(
            str(value["api_router_factory"])
            if value.get("api_router_factory") is not None
            else None
        ),
        page_routes=page_routes,
    )


def _load_root_path(project: ProjectRuntimeAssembly) -> str:
    frontend_spec = project.runtime_exports.get("frontend_app_spec")
    if frontend_spec is None:
        return "/"
    if not isinstance(frontend_spec, dict):
        raise ValueError("frontend_app_spec export is required for runtime root route")
    contract = frontend_spec.get("contract")
    if not isinstance(contract, dict):
        raise ValueError("frontend_app_spec.contract is required for runtime root route")
    route_contract = contract.get("route_contract")
    if not isinstance(route_contract, dict):
        raise ValueError("frontend_app_spec.contract.route_contract is required for runtime root route")
    home = route_contract.get("home")
    if not isinstance(home, str) or not home.startswith("/"):
        raise ValueError("frontend_app_spec.contract.route_contract.home must be a routable path")
    return home


def _resolve_response_class(response_class: str | None) -> type[Any] | None:
    if response_class is None:
        return None
    if response_class == "html":
        return HTMLResponse
    raise ValueError(f"unsupported runtime response class: {response_class}")


def _resolve_correspondence_endpoint(
    project: ProjectRuntimeAssembly,
    blueprint: RuntimeBlueprint,
) -> tuple[str, str]:
    backend_spec = project.runtime_exports.get("backend_service_spec")
    api_prefix = ""
    if backend_spec is not None:
        if not isinstance(backend_spec, dict):
            raise ValueError("backend_service_spec export must be a dict")
        transport = backend_spec.get("transport")
        if not isinstance(transport, dict):
            raise ValueError("backend_service_spec.transport must be a dict")
        raw_api_prefix = transport.get("api_prefix")
        if not isinstance(raw_api_prefix, str) or not raw_api_prefix.startswith("/"):
            raise ValueError("backend_service_spec.transport.api_prefix must be an absolute path")
        api_prefix = raw_api_prefix
    endpoint = f"{api_prefix}/correspondence" if api_prefix else "/correspondence"
    if endpoint == blueprint.project_config_endpoint:
        raise ValueError("correspondence endpoint conflicts with project_config endpoint")
    return api_prefix, endpoint


def _resolve_correspondence_view(project: ProjectRuntimeAssembly) -> dict[str, Any]:
    canonical = project.canonical
    if not isinstance(canonical, dict):
        return {}
    view = canonical.get("correspondence")
    if isinstance(view, dict):
        return view
    return build_correspondence_view(canonical)


def _load_callable(path: str) -> Callable[..., Any]:
    module_name, _, attr_name = path.partition(":")
    if not module_name or not attr_name:
        raise ValueError(f"invalid callable path: {path}")
    module = import_module(module_name)
    value = getattr(module, attr_name)
    if not callable(value):
        raise TypeError(f"resolved object is not callable: {path}")
    return value
