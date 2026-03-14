from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any, Callable

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from project_runtime import ProjectRuntimeAssembly
from project_runtime.pipeline import load_project_runtime


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


def build_project_runtime_app(project: ProjectRuntimeAssembly | None = None) -> FastAPI:
    assembly = project or load_project_runtime()
    blueprint = _load_runtime_blueprint(assembly)
    root_path = _load_root_path(assembly)
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

    return app


def _load_runtime_blueprint(project: ProjectRuntimeAssembly) -> RuntimeBlueprint:
    value = project.require_runtime_export("runtime_blueprint")
    if not isinstance(value, dict):
        raise ValueError("runtime_blueprint export is required for runtime app construction")
    transport = value.get("transport")
    if not isinstance(transport, dict):
        raise ValueError("runtime_blueprint.transport is required for runtime app construction")
    mode = transport.get("mode")
    if not isinstance(mode, str):
        raise ValueError("runtime_blueprint.transport.mode must be a string")
    project_config_endpoint = transport.get("project_config_endpoint")
    if not isinstance(project_config_endpoint, str) or not project_config_endpoint.startswith("/"):
        raise ValueError("runtime_blueprint.transport.project_config_endpoint must be a routable path")
    landing_path = value.get("landing_path")
    if not isinstance(landing_path, str) or not landing_path.startswith("/"):
        raise ValueError("runtime_blueprint.landing_path must be a routable path")
    summary_factory_path = value.get("summary_factory")
    if not isinstance(summary_factory_path, str):
        raise ValueError("runtime_blueprint.summary_factory must be a callable path")
    repository_factory_path = value.get("repository_factory")
    if repository_factory_path is not None and not isinstance(repository_factory_path, str):
        raise ValueError("runtime_blueprint.repository_factory must be a callable path when provided")
    api_router_factory_path = value.get("api_router_factory")
    if api_router_factory_path is not None and not isinstance(api_router_factory_path, str):
        raise ValueError("runtime_blueprint.api_router_factory must be a callable path when provided")
    raw_page_routes = value.get("page_routes")
    if not isinstance(raw_page_routes, list) or not raw_page_routes:
        raise ValueError("runtime_blueprint.page_routes must be a non-empty list")
    page_routes: list[RuntimeRouteSpec] = []
    for item in raw_page_routes:
        if not isinstance(item, dict):
            raise ValueError("runtime_blueprint.page_routes entries must be objects")
        route_id = item.get("route_id")
        path = item.get("path")
        handler_factory = item.get("handler_factory")
        response_class = item.get("response_class")
        if not isinstance(route_id, str) or not route_id:
            raise ValueError("runtime_blueprint.page_routes.route_id must be a string")
        if not isinstance(path, str) or not path.startswith("/"):
            raise ValueError("runtime_blueprint.page_routes.path must be a routable path")
        if not isinstance(handler_factory, str):
            raise ValueError("runtime_blueprint.page_routes.handler_factory must be a callable path")
        if response_class is not None and not isinstance(response_class, str):
            raise ValueError("runtime_blueprint.page_routes.response_class must be a string when provided")
        page_routes.append(
            RuntimeRouteSpec(
                route_id=route_id,
                path=path,
                handler_factory_path=handler_factory,
                response_class=response_class,
            )
        )
    return RuntimeBlueprint(
        mode=mode,
        project_config_endpoint=project_config_endpoint,
        landing_path=landing_path,
        summary_factory_path=summary_factory_path,
        repository_factory_path=repository_factory_path,
        api_router_factory_path=api_router_factory_path,
        page_routes=tuple(page_routes),
    )


def _load_root_path(project: ProjectRuntimeAssembly) -> str:
    frontend_spec = project.require_runtime_export("frontend_app_spec")
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


def _load_callable(path: str) -> Callable[..., Any]:
    module_name, _, attr_name = path.partition(":")
    if not module_name or not attr_name:
        raise ValueError(f"invalid callable path: {path}")
    module = import_module(module_name)
    value = getattr(module, attr_name)
    if not callable(value):
        raise TypeError(f"resolved object is not callable: {path}")
    return value
