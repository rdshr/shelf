from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
import tomllib
from typing import Any, Callable

from fastapi import FastAPI

from project_runtime.config_layout import ProjectConfigLayout


Loader = Callable[[str | Path], Any]
Materializer = Callable[[str | Path, Path | None], Any]
RuntimeAppBuilder = Callable[[str | Path], FastAPI]
GovernanceClosureBuilder = Callable[[Any], Any]
ImplementationEffectBuilder = Callable[[Any], dict[str, dict[str, Any]]]
ProjectScaffolder = Callable[[Path, str | None, bool, bool], tuple[str, ...]]

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECTS_DIR = REPO_ROOT / "projects"


@dataclass(frozen=True)
class ProjectTemplateRegistration:
    template_id: str
    default_product_spec_file: Path
    product_spec_layout: ProjectConfigLayout
    implementation_config_layout: ProjectConfigLayout
    load_project: Loader
    materialize_project: Materializer
    build_runtime_app_from_spec: RuntimeAppBuilder
    build_governance_closure: GovernanceClosureBuilder
    build_implementation_effect_manifest: ImplementationEffectBuilder
    scaffold_project: ProjectScaffolder | None = None
    default: bool = False


_REGISTRY: dict[str, ProjectTemplateRegistration] = {}


def _ensure_builtin_project_templates_loaded() -> None:
    if _REGISTRY:
        return
    import_module("project_runtime.knowledge_base")


def _callable_identity(value: Callable[..., Any] | None) -> tuple[str, str] | None:
    if value is None:
        return None
    return (getattr(value, "__module__", ""), getattr(value, "__name__", ""))


def _alias_normalized_module(module_name: str) -> str:
    return module_name.removeprefix("src.")


def _callable_equivalent(
    left: Callable[..., Any] | None,
    right: Callable[..., Any] | None,
) -> bool:
    left_identity = _callable_identity(left)
    right_identity = _callable_identity(right)
    if left_identity is None or right_identity is None:
        return left_identity == right_identity
    return (
        _alias_normalized_module(left_identity[0]) == _alias_normalized_module(right_identity[0])
        and left_identity[1] == right_identity[1]
    )


def _registrations_equivalent(
    left: ProjectTemplateRegistration,
    right: ProjectTemplateRegistration,
) -> bool:
    return (
        left.template_id == right.template_id
        and left.default_product_spec_file == right.default_product_spec_file
        and left.product_spec_layout == right.product_spec_layout
        and left.implementation_config_layout == right.implementation_config_layout
        and left.default == right.default
        and _callable_equivalent(left.load_project, right.load_project)
        and _callable_equivalent(left.materialize_project, right.materialize_project)
        and _callable_equivalent(left.build_runtime_app_from_spec, right.build_runtime_app_from_spec)
        and _callable_equivalent(left.build_governance_closure, right.build_governance_closure)
        and _callable_equivalent(
            left.build_implementation_effect_manifest,
            right.build_implementation_effect_manifest,
        )
        and _callable_equivalent(left.scaffold_project, right.scaffold_project)
    )


def register_project_template(registration: ProjectTemplateRegistration) -> None:
    existing = _REGISTRY.get(registration.template_id)
    if existing is not None:
        if existing == registration or _registrations_equivalent(existing, registration):
            return
        raise ValueError(f"project template already registered: {registration.template_id}")
    _REGISTRY[registration.template_id] = registration


def iter_project_template_registrations() -> tuple[ProjectTemplateRegistration, ...]:
    _ensure_builtin_project_templates_loaded()
    return tuple(sorted(_REGISTRY.values(), key=lambda item: item.template_id))


def get_default_project_template_registration() -> ProjectTemplateRegistration:
    registrations = iter_project_template_registrations()
    for registration in registrations:
        if registration.default:
            return registration
    if len(registrations) == 1:
        return registrations[0]
    raise ValueError("no default project template registration configured")


def _normalize_project_spec_path(product_spec_file: str | Path) -> Path:
    candidate = Path(product_spec_file)
    if not candidate.is_absolute():
        candidate = (REPO_ROOT / candidate).resolve()
    return candidate


def detect_project_template_id(product_spec_file: str | Path) -> str:
    product_spec_path = _normalize_project_spec_path(product_spec_file)
    with product_spec_path.open("rb") as fh:
        data = tomllib.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"project config must decode into object: {product_spec_path}")
    project_table = data.get("project")
    if not isinstance(project_table, dict):
        raise ValueError(f"missing required table: project in {product_spec_path}")
    template_id = project_table.get("template")
    if not isinstance(template_id, str) or not template_id.strip():
        raise ValueError(f"missing required string: project.template in {product_spec_path}")
    return template_id.strip()


def resolve_project_template_registration(product_spec_file: str | Path) -> ProjectTemplateRegistration:
    _ensure_builtin_project_templates_loaded()
    template_id = detect_project_template_id(product_spec_file)
    registration = _REGISTRY.get(template_id)
    if registration is None:
        raise ValueError(f"unsupported project template: {template_id}")
    return registration


def load_registered_project(product_spec_file: str | Path | None = None) -> Any:
    registration = (
        get_default_project_template_registration()
        if product_spec_file is None
        else resolve_project_template_registration(product_spec_file)
    )
    target_file = product_spec_file or registration.default_product_spec_file
    return registration.load_project(target_file)


def materialize_registered_project(
    product_spec_file: str | Path | None = None,
    *,
    output_dir: str | Path | None = None,
) -> Any:
    registration = (
        get_default_project_template_registration()
        if product_spec_file is None
        else resolve_project_template_registration(product_spec_file)
    )
    target_file = product_spec_file or registration.default_product_spec_file
    normalized_output = None if output_dir is None else Path(output_dir)
    return registration.materialize_project(target_file, normalized_output)


def scaffold_registered_project(
    project_dir: str | Path,
    *,
    template_id: str,
    display_name: str | None = None,
    modular_product_spec: bool = True,
    force: bool = False,
) -> tuple[str, ...]:
    _ensure_builtin_project_templates_loaded()
    registration = _REGISTRY.get(template_id)
    if registration is None:
        raise ValueError(f"unsupported project template: {template_id}")
    if registration.scaffold_project is None:
        raise ValueError(f"template does not expose project scaffold support: {template_id}")
    return registration.scaffold_project(Path(project_dir), display_name, modular_product_spec, force)
