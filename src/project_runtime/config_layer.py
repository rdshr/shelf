from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib
from typing import Any

from project_runtime.correspondence_contracts import boundary_field_name, module_key_from_id
from project_runtime.framework_layer import FrameworkModuleClass
from project_runtime.models import ArtifactConfig, ProjectConfig, ProjectMetadata, SelectedFrameworkModule
from project_runtime.utils import lookup_dotted_path, normalize_project_path, relative_path


class ConfigModuleClass:
    class_id: str
    module_id: str
    module_key: str
    framework_file: str
    source_ref: dict[str, Any]
    communication_export: dict[str, Any]
    exact_export: dict[str, Any]
    compiled_config_export: dict[str, Any]
    boundary_static_classes: tuple[type["ConfigBoundaryStaticClass"], ...]
    boundary_runtime_classes: tuple[type["ConfigBoundaryRuntimeClass"], ...]

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        return {
            "class_id": cls.class_id,
            "module_id": cls.module_id,
            "module_key": cls.module_key,
            "framework_file": cls.framework_file,
            "source_ref": dict(cls.source_ref),
            "communication_export": cls.communication_export,
            "exact_export": cls.exact_export,
            "compiled_config_export": cls.compiled_config_export,
            "boundary_static_classes": [item.to_dict() for item in cls.boundary_static_classes],
            "boundary_runtime_classes": [item.to_dict() for item in cls.boundary_runtime_classes],
            "class_name": cls.__name__,
        }


class ConfigBoundaryStaticClass:
    class_id: str
    canonical_id: str
    module_id: str
    boundary_id: str
    communication_path: str
    exact_path: str
    communication_value: dict[str, Any]
    exact_value: dict[str, Any]
    source_ref: dict[str, Any]

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        return {
            "class_id": cls.class_id,
            "canonical_id": cls.canonical_id,
            "module_id": cls.module_id,
            "boundary_id": cls.boundary_id,
            "communication_path": cls.communication_path,
            "exact_path": cls.exact_path,
            "communication_value": cls.communication_value,
            "exact_value": cls.exact_value,
            "source_ref": dict(cls.source_ref),
            "class_name": cls.__name__,
        }


class ConfigBoundaryRuntimeClass:
    class_id: str
    canonical_id: str
    module_id: str
    boundary_id: str
    projection_id: str
    mapping_mode: str
    note: str
    static_class_id: str
    exact_anchor_path: str
    communication_anchor_path: str
    static_field_name: str
    runtime_field_name: str
    merge_policy: str
    source_ref: dict[str, Any]

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        return {
            "class_id": cls.class_id,
            "canonical_id": cls.canonical_id,
            "module_id": cls.module_id,
            "boundary_id": cls.boundary_id,
            "projection_id": cls.projection_id,
            "mapping_mode": cls.mapping_mode,
            "note": cls.note,
            "static_class_id": cls.static_class_id,
            "exact_anchor_path": cls.exact_anchor_path,
            "communication_anchor_path": cls.communication_anchor_path,
            "static_field_name": cls.static_field_name,
            "runtime_field_name": cls.runtime_field_name,
            "merge_policy": cls.merge_policy,
            "source_ref": dict(cls.source_ref),
            "class_name": cls.__name__,
        }


_BOUNDARY_PAYLOAD_MIRROR_KEYS = frozenset({"boundary_id", "mapping_mode"})


@dataclass(frozen=True)
class ConfigModuleBinding:
    framework_module: type[FrameworkModuleClass]
    config_module: type[ConfigModuleClass]

    def to_dict(self) -> dict[str, Any]:
        payload = self.config_module.to_dict()
        payload["framework_module_id"] = self.framework_module.module_id
        return payload


def _require_table(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"missing required table: {key}")
    return value


def _require_string(parent: dict[str, Any], key: str) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing required string: {key}")
    return value.strip()


def _require_boundary_payload(value: Any, *, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"boundary path must be a table: {path}")
    return {
        key: item
        for key, item in value.items()
        if key not in _BOUNDARY_PAYLOAD_MIRROR_KEYS
    }


def _load_toml(project_file: Path) -> dict[str, Any]:
    return tomllib.loads(project_file.read_text(encoding="utf-8"))


def load_project_config(project_file: str | Path) -> ProjectConfig:
    resolved_file = normalize_project_path(project_file)
    raw = _load_toml(resolved_file)
    project_table = _require_table(raw, "project")
    framework_table = _require_table(raw, "framework")
    communication_table = _require_table(raw, "communication")
    exact_table = _require_table(raw, "exact")
    evidence_table = _require_table(exact_table, "evidence")
    artifacts_table = _require_table(evidence_table, "artifacts")
    raw_modules = framework_table.get("modules")
    if not isinstance(raw_modules, list) or not raw_modules:
        raise ValueError("framework must define non-empty [[framework.modules]]")
    framework_modules: list[SelectedFrameworkModule] = []
    seen_roles: set[str] = set()
    for item in raw_modules:
        if not isinstance(item, dict):
            raise ValueError("each [[framework.modules]] entry must be a table")
        module = SelectedFrameworkModule(
            role=_require_string(item, "role"),
            framework_file=_require_string(item, "framework_file"),
        )
        if module.role in seen_roles:
            raise ValueError(f"duplicate framework role: {module.role}")
        seen_roles.add(module.role)
        framework_modules.append(module)
    return ProjectConfig(
        project_file=relative_path(resolved_file),
        metadata=ProjectMetadata(
            project_id=_require_string(project_table, "project_id"),
            runtime_scene=_require_string(project_table, "runtime_scene"),
            display_name=_require_string(project_table, "display_name"),
            description=_require_string(project_table, "description"),
            version=_require_string(project_table, "version"),
        ),
        framework_modules=tuple(framework_modules),
        communication=communication_table,
        exact=exact_table,
        artifacts=ArtifactConfig(
            canonical_json=_require_string(artifacts_table, "canonical_json"),
        ),
    )


def build_config_modules(
    project_config: ProjectConfig,
    framework_modules: tuple[type[FrameworkModuleClass], ...],
) -> tuple[ConfigModuleBinding, ...]:
    bindings: list[ConfigModuleBinding] = []
    project_payload = project_config.to_dict()
    for module_class in framework_modules:
        module_key = module_key_from_id(module_class.module_id)
        boundary_pairs: list[dict[str, Any]] = []
        module_static_communication: dict[str, Any] = {}
        module_static_exact: dict[str, Any] = {}
        module_static_param_bindings: list[dict[str, Any]] = []
        boundary_projection_map: dict[str, dict[str, Any]] = {}
        boundary_static_classes: list[type[ConfigBoundaryStaticClass]] = []
        boundary_runtime_classes: list[type[ConfigBoundaryRuntimeClass]] = []
        for boundary in module_class.boundaries:
            projection = module_class.boundary_projection_map.get(boundary.boundary_id)
            if projection is None:
                continue
            communication_path = str(projection["primary_communication_path"])
            exact_path = str(projection["primary_exact_path"])
            static_field = str(
                projection.get("static_field_name")
                or boundary_field_name(boundary.boundary_id)
            )
            runtime_field = str(
                projection.get("runtime_field_name")
                or static_field
            )
            exact_export_static_path = str(
                projection.get("exact_export_static_path")
                or f"exact_export.modules.{module_key}.static_params.{static_field}"
            )
            communication_export_static_path = str(
                projection.get("communication_export_static_path")
                or f"communication_export.modules.{module_key}.static_params.{static_field}"
            )
            merge_policy = str(projection.get("merge_policy") or "runtime_override_else_static")
            communication_payload = _require_boundary_payload(
                lookup_dotted_path(project_payload, communication_path),
                path=communication_path,
            )
            exact_payload = _require_boundary_payload(
                lookup_dotted_path(project_payload, exact_path),
                path=exact_path,
            )
            module_static_communication[static_field] = communication_payload
            module_static_exact[static_field] = exact_payload
            boundary_projection_map[boundary.boundary_id] = dict(projection)
            boundary_projection = dict(projection)
            boundary_projection["module_key"] = module_key
            boundary_projection["static_field_name"] = static_field
            boundary_projection["runtime_field_name"] = runtime_field
            boundary_projection["exact_export_static_path"] = exact_export_static_path
            boundary_projection["communication_export_static_path"] = communication_export_static_path
            boundary_projection["merge_policy"] = merge_policy
            boundary_pairs.append(boundary_projection)
            module_static_param_bindings.append(
                {
                    "module_id": module_class.module_id,
                    "module_key": module_key,
                    "boundary_id": boundary.boundary_id,
                    "config_source_exact_path": exact_path,
                    "config_source_communication_path": communication_path,
                    "exact_export_static_path": exact_export_static_path,
                    "communication_export_static_path": communication_export_static_path,
                    "static_field_name": static_field,
                    "runtime_field_name": runtime_field,
                    "merge_policy": merge_policy,
                    "mapping_mode": str(projection.get("mapping_mode") or ""),
                    "projection_id": str(projection.get("projection_id") or ""),
                }
            )
            static_class_name = (
                f"{module_class.__name__.replace('FrameworkModule', '')}"
                f"{boundary.boundary_id}BoundaryStaticConfig"
            )
            static_class_id = f"config_boundary_static_class::{module_class.module_id}::{boundary.boundary_id}"
            static_class = type(
                static_class_name,
                (ConfigBoundaryStaticClass,),
                {
                    "class_id": static_class_id,
                    "canonical_id": f"config_boundary_static::{module_class.module_id}::{boundary.boundary_id}",
                    "module_id": module_class.module_id,
                    "boundary_id": boundary.boundary_id,
                    "communication_path": communication_path,
                    "exact_path": exact_path,
                    "communication_value": dict(communication_payload),
                    "exact_value": dict(exact_payload),
                    "source_ref": {
                        "file_path": project_config.project_file,
                        "section": "config_boundary_static",
                        "anchor": f"{module_class.module_id}:{boundary.boundary_id}",
                        "token": boundary.boundary_id,
                    },
                },
            )
            boundary_static_classes.append(static_class)
            runtime_class_name = (
                f"{module_class.__name__.replace('FrameworkModule', '')}"
                f"{boundary.boundary_id}BoundaryRuntimeConfig"
            )
            boundary_runtime_classes.append(
                type(
                    runtime_class_name,
                    (ConfigBoundaryRuntimeClass,),
                    {
                        "class_id": (
                            f"config_boundary_runtime_class::{module_class.module_id}::{boundary.boundary_id}"
                        ),
                        "canonical_id": (
                            f"config_boundary_runtime::{module_class.module_id}::{boundary.boundary_id}"
                        ),
                        "module_id": module_class.module_id,
                        "boundary_id": boundary.boundary_id,
                        "projection_id": str(projection.get("projection_id") or ""),
                        "mapping_mode": str(projection.get("mapping_mode") or ""),
                        "note": str(projection.get("note") or ""),
                        "static_class_id": static_class_id,
                        "exact_anchor_path": exact_export_static_path,
                        "communication_anchor_path": communication_export_static_path,
                        "static_field_name": static_field,
                        "runtime_field_name": runtime_field,
                        "merge_policy": merge_policy,
                        "source_ref": {
                            "file_path": project_config.project_file,
                            "section": "config_boundary_runtime",
                            "anchor": f"{module_class.module_id}:{boundary.boundary_id}",
                            "token": boundary.boundary_id,
                        },
                    },
                )
            )
        overlays: dict[str, Any] = {}
        for overlay_path in module_class.exact_overlay_paths:
            overlay_key = overlay_path.rsplit(".", 1)[-1]
            try:
                overlays[overlay_key] = lookup_dotted_path(project_payload, overlay_path)
            except KeyError:
                continue
        communication_export = {
            "module_id": module_class.module_id,
            "module_key": module_key,
            "source_ref": dict(module_class.source_ref),
            "boundary_projections": boundary_projection_map,
            "modules": {
                module_key: {
                    "module_id": module_class.module_id,
                    "module_key": module_key,
                    "static_params": module_static_communication,
                }
            },
        }
        exact_export = {
            "module_id": module_class.module_id,
            "module_key": module_key,
            "source_ref": dict(module_class.source_ref),
            "boundary_projections": boundary_projection_map,
            "modules": {
                module_key: {
                    "module_id": module_class.module_id,
                    "module_key": module_key,
                    "static_params": module_static_exact,
                }
            },
            "overlays": overlays,
        }
        class_name = module_class.__name__.replace("FrameworkModule", "ConfigModule")
        config_module = type(
            class_name,
            (ConfigModuleClass,),
            {
                "class_id": f"config_module_class::{module_class.module_id}",
                "module_id": module_class.module_id,
                "module_key": module_key,
                "framework_file": module_class.framework_file,
                "source_ref": {
                    "file_path": project_config.project_file,
                    "section": "config_module",
                    "anchor": module_class.module_id,
                    "token": module_class.module_id,
                },
                "communication_export": communication_export,
                "exact_export": exact_export,
                "compiled_config_export": {
                    "module_id": module_class.module_id,
                    "framework_file": module_class.framework_file,
                    "module_key": module_key,
                    "projection_source": "framework_export",
                    "boundary_bindings": boundary_pairs,
                    "module_static_param_bindings": module_static_param_bindings,
                    "exact_overlay_paths": list(module_class.exact_overlay_paths),
                    "communication_export": communication_export,
                    "exact_export": exact_export,
                },
                "boundary_static_classes": tuple(boundary_static_classes),
                "boundary_runtime_classes": tuple(boundary_runtime_classes),
            },
        )
        bindings.append(ConfigModuleBinding(framework_module=module_class, config_module=config_module))
    return tuple(bindings)
