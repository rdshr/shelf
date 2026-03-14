from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib
from typing import Any

from project_runtime.framework_layer import FrameworkModuleClass
from project_runtime.models import ArtifactConfig, ProjectConfig, ProjectMetadata, SelectedFrameworkModule
from project_runtime.utils import lookup_dotted_path, normalize_project_path, relative_path


BOUNDARY_CONFIG_PATHS = {
    "SURFACE": ("communication.frontend.surface", "exact.frontend.surface"),
    "VISUAL": ("communication.frontend.visual", "exact.frontend.visual"),
    "INTERACT": ("communication.frontend.interact", "exact.frontend.interact"),
    "STATE": ("communication.frontend.state", "exact.frontend.state"),
    "EXTEND": ("communication.frontend.extend", "exact.frontend.extend"),
    "ROUTE": ("communication.frontend.route", "exact.frontend.route"),
    "A11Y": ("communication.frontend.a11y", "exact.frontend.a11y"),
    "LIBRARY": ("communication.knowledge_base.library", "exact.knowledge_base.library"),
    "PREVIEW": ("communication.knowledge_base.preview", "exact.knowledge_base.preview"),
    "CHAT": ("communication.knowledge_base.chat", "exact.knowledge_base.chat"),
    "CONTEXT": ("communication.knowledge_base.context", "exact.knowledge_base.context"),
    "RETURN": ("communication.knowledge_base.return", "exact.knowledge_base.return"),
    "RESULT": ("communication.backend.result", "exact.backend.result"),
    "AUTH": ("communication.backend.auth", "exact.backend.auth"),
    "TRACE": ("communication.backend.trace", "exact.backend.trace"),
}

MODULE_EXACT_OVERLAYS = {
    "frontend": ("exact.code.frontend",),
    "knowledge_base": ("exact.knowledge_base.documents",),
    "backend": ("exact.code.backend",),
}


class ConfigModuleClass:
    module_id: str
    framework_file: str
    communication_export: dict[str, Any]
    exact_export: dict[str, Any]
    compiled_config_export: dict[str, Any]

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        return {
            "module_id": cls.module_id,
            "framework_file": cls.framework_file,
            "communication_export": cls.communication_export,
            "exact_export": cls.exact_export,
            "compiled_config_export": cls.compiled_config_export,
            "class_name": cls.__name__,
        }


@dataclass(frozen=True)
class ConfigModuleBinding:
    framework_module: type[FrameworkModuleClass]
    config_module: type[ConfigModuleClass]

    def to_dict(self) -> dict[str, Any]:
        return {
            "framework_module_id": self.framework_module.module_id,
            "config_module_id": self.config_module.module_id,
            "framework_file": self.framework_module.framework_file,
            "communication_export": self.config_module.communication_export,
            "exact_export": self.config_module.exact_export,
        }


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
            runtime_snapshot_py=_require_string(artifacts_table, "runtime_snapshot_py"),
        ),
    )


def build_config_modules(
    project_config: ProjectConfig,
    framework_modules: tuple[type[FrameworkModuleClass], ...],
) -> tuple[ConfigModuleBinding, ...]:
    bindings: list[ConfigModuleBinding] = []
    for module_class in framework_modules:
        boundary_pairs: list[dict[str, str]] = []
        communication_boundaries: dict[str, Any] = {}
        exact_boundaries: dict[str, Any] = {}
        for boundary in module_class.boundaries:
            path_pair = BOUNDARY_CONFIG_PATHS.get(boundary.boundary_id)
            if path_pair is None:
                continue
            communication_path, exact_path = path_pair
            communication_boundaries[boundary.boundary_id] = lookup_dotted_path(
                project_config.to_dict(),
                communication_path,
            )
            exact_boundaries[boundary.boundary_id] = lookup_dotted_path(
                project_config.to_dict(),
                exact_path,
            )
            boundary_pairs.append(
                {
                    "boundary_id": boundary.boundary_id,
                    "communication_path": communication_path,
                    "exact_path": exact_path,
                }
            )
        overlays: dict[str, Any] = {}
        for overlay_path in MODULE_EXACT_OVERLAYS.get(module_class.framework, ()):
            overlay_key = overlay_path.rsplit(".", 1)[-1]
            overlays[overlay_key] = lookup_dotted_path(project_config.to_dict(), overlay_path)
        communication_export = {
            "module_id": module_class.module_id,
            "boundaries": communication_boundaries,
        }
        exact_export = {
            "module_id": module_class.module_id,
            "boundaries": exact_boundaries,
            "overlays": overlays,
        }
        class_name = module_class.__name__.replace("FrameworkModule", "ConfigModule")
        config_module = type(
            class_name,
            (ConfigModuleClass,),
            {
                "module_id": module_class.module_id,
                "framework_file": module_class.framework_file,
                "communication_export": communication_export,
                "exact_export": exact_export,
                "compiled_config_export": {
                    "module_id": module_class.module_id,
                    "framework_file": module_class.framework_file,
                    "boundary_bindings": boundary_pairs,
                    "communication_export": communication_export,
                    "exact_export": exact_export,
                },
            },
        )
        bindings.append(ConfigModuleBinding(framework_module=module_class, config_module=config_module))
    return tuple(bindings)
