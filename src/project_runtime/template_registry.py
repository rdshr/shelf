from __future__ import annotations

from dataclasses import dataclass
import importlib
from pathlib import Path
import tomllib
from typing import Any, Callable


@dataclass(frozen=True)
class ProjectConfigLayout:
    required_top_level_keys: frozenset[str]
    allowed_top_level_keys: frozenset[str]
    required_nested_tables: dict[str, frozenset[str]]
    allowed_nested_tables: dict[str, frozenset[str]]


@dataclass(frozen=True)
class ProjectTemplateRegistration:
    template_id: str
    default_product_spec_file: Path
    product_spec_layout: ProjectConfigLayout
    implementation_config_layout: ProjectConfigLayout
    load_project: Callable[[str | Path], Any]
    materialize_project: Callable[[str | Path, str | Path | None], Any]
    build_app: Callable[[Any], Any]


_REGISTERED_TEMPLATES: dict[str, ProjectTemplateRegistration] = {}
_DEFAULT_TEMPLATE_ID: str | None = None
_BUILTINS_REGISTERED = False


def config_layout(
    required_top_level_keys: set[str] | frozenset[str],
    required_nested_tables: dict[str, set[str] | frozenset[str]],
) -> ProjectConfigLayout:
    normalized_required = frozenset(required_top_level_keys)
    normalized_nested = {
        key: frozenset(value)
        for key, value in required_nested_tables.items()
    }
    return ProjectConfigLayout(
        required_top_level_keys=normalized_required,
        allowed_top_level_keys=normalized_required,
        required_nested_tables=normalized_nested,
        allowed_nested_tables=dict(normalized_nested),
    )


def register_project_template(
    registration: ProjectTemplateRegistration,
    *,
    default: bool = False,
) -> ProjectTemplateRegistration:
    global _DEFAULT_TEMPLATE_ID
    existing = _REGISTERED_TEMPLATES.get(registration.template_id)
    if existing is not None:
        if default:
            _DEFAULT_TEMPLATE_ID = registration.template_id
        return existing
    _REGISTERED_TEMPLATES[registration.template_id] = registration
    if default or _DEFAULT_TEMPLATE_ID is None:
        _DEFAULT_TEMPLATE_ID = registration.template_id
    return registration


def ensure_builtin_project_templates_registered() -> None:
    global _BUILTINS_REGISTERED
    if _BUILTINS_REGISTERED:
        return
    knowledge_base = importlib.import_module("project_runtime.knowledge_base")

    knowledge_base.register_knowledge_base_template()
    _BUILTINS_REGISTERED = True


def get_project_template_registration(template_id: str) -> ProjectTemplateRegistration:
    ensure_builtin_project_templates_registered()
    registration = _REGISTERED_TEMPLATES.get(template_id)
    if registration is None:
        raise ValueError(f"unsupported project template: {template_id}")
    return registration


def get_default_project_template_registration() -> ProjectTemplateRegistration:
    ensure_builtin_project_templates_registered()
    if _DEFAULT_TEMPLATE_ID is None:
        raise ValueError("no default project template is registered")
    return get_project_template_registration(_DEFAULT_TEMPLATE_ID)


def detect_project_template_id(product_spec_file: str | Path) -> str:
    product_spec_path = Path(product_spec_file)
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
    template_id = detect_project_template_id(product_spec_file)
    return get_project_template_registration(template_id)


def load_registered_project(product_spec_file: str | Path) -> Any:
    registration = resolve_project_template_registration(product_spec_file)
    return registration.load_project(product_spec_file)


def materialize_registered_project(
    product_spec_file: str | Path,
    output_dir: str | Path | None = None,
) -> Any:
    registration = resolve_project_template_registration(product_spec_file)
    return registration.materialize_project(product_spec_file, output_dir)
