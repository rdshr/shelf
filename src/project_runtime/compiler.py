from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
from typing import Any

from project_runtime.config_layer import build_config_modules, load_project_config
from project_runtime.code_layer import build_code_modules
from project_runtime.evidence_layer import build_evidence_modules
from project_runtime.framework_layer import resolve_selected_framework_modules
from project_runtime.models import GeneratedArtifactPaths, ProjectRuntimeAssembly
from project_runtime.utils import cleanup_generated_output_dir, normalize_project_path, relative_path
from rule_validation_models import ValidationReports


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROJECT_FILE = REPO_ROOT / "projects" / "knowledge_base_basic" / "project.toml"


def _artifact_paths(project_file: Path, canonical_name: str) -> GeneratedArtifactPaths:
    output_dir = project_file.parent / "generated"
    return GeneratedArtifactPaths(
        directory=relative_path(output_dir),
        canonical_json=relative_path(output_dir / canonical_name),
    )


def _build_links(
    framework_modules: tuple[type[Any], ...],
    config_modules: tuple[Any, ...],
    code_modules: tuple[Any, ...],
    evidence_modules: tuple[type[Any], ...],
) -> dict[str, Any]:
    framework_to_config = []
    config_to_code = []
    code_to_evidence = []
    boundary_bindings = []
    base_bindings = []
    for config_binding, code_binding, evidence_module in zip(config_modules, code_modules, evidence_modules):
        framework_to_config.append(
            {
                "framework_module_id": config_binding.framework_module.module_id,
                "framework_module_class_id": config_binding.framework_module.class_id,
                "config_module_id": config_binding.config_module.module_id,
                "config_module_class_id": config_binding.config_module.class_id,
                "config_module_class": config_binding.config_module.__name__,
                "link_role": "mainline",
            }
        )
        config_to_code.append(
            {
                "config_module_id": config_binding.config_module.module_id,
                "config_module_class_id": config_binding.config_module.class_id,
                "code_module_id": code_binding.code_module.module_id,
                "code_module_class_id": code_binding.code_module.class_id,
                "code_module_class": code_binding.code_module.__name__,
                "link_role": "mainline",
            }
        )
        code_to_evidence.append(
            {
                "code_module_id": code_binding.code_module.module_id,
                "code_module_class_id": code_binding.code_module.class_id,
                "evidence_module_id": evidence_module.module_id,
                "evidence_module_class_id": evidence_module.class_id,
                "evidence_module_class": evidence_module.__name__,
                "link_role": "mainline",
            }
        )
        compiled_config = config_binding.config_module.compiled_config_export
        for item in compiled_config["boundary_bindings"]:
            boundary_bindings.append(
                {
                    "module_id": config_binding.framework_module.module_id,
                    "boundary_id": item["boundary_id"],
                    "projection_id": item["projection_id"],
                    "projection_source": item["projection_source"],
                    "mapping_mode": item["mapping_mode"],
                    "primary_communication_path": item["primary_communication_path"],
                    "related_communication_paths": list(item["related_communication_paths"]),
                    "primary_exact_path": item["primary_exact_path"],
                    "related_exact_paths": list(item["related_exact_paths"]),
                    "note": item["note"],
                    "config_module_id": config_binding.config_module.module_id,
                    "config_module_class_id": config_binding.config_module.class_id,
                    "code_module_id": code_binding.code_module.module_id,
                    "code_module_class_id": code_binding.code_module.class_id,
                    "code_module_class": code_binding.code_module.__name__,
                    "evidence_module_id": evidence_module.module_id,
                    "evidence_module_class_id": evidence_module.class_id,
                    "evidence_module_class": evidence_module.__name__,
                    "link_role": "trace_view",
                }
            )
        for item in code_binding.code_module.code_bindings["base_bindings"]:
            base_bindings.append(
                {
                    "module_id": code_binding.framework_module.module_id,
                    **item,
                    "code_module_id": code_binding.code_module.module_id,
                    "code_module_class_id": code_binding.code_module.class_id,
                    "code_module_class": code_binding.code_module.__name__,
                    "link_role": "trace_view",
                }
            )
    return {
        "link_roles": {
            "framework_to_config": "mainline",
            "config_to_code": "mainline",
            "code_to_evidence": "mainline",
            "boundary_bindings": "trace_view",
            "base_bindings": "trace_view",
        },
        "framework_to_config": framework_to_config,
        "config_to_code": config_to_code,
        "code_to_evidence": code_to_evidence,
        "boundary_bindings": boundary_bindings,
        "base_bindings": base_bindings,
    }


def _build_canonical(
    assembly: ProjectRuntimeAssembly,
    framework_modules: tuple[type[Any], ...],
    config_modules: tuple[Any, ...],
    code_modules: tuple[Any, ...],
    evidence_modules: tuple[type[Any], ...],
    evidence_exports: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "four-layer-canonical/v2",
        "project": assembly.metadata.to_dict(),
        "framework": {
            "author_source": "framework/*.md",
            "selected_modules": [item.to_dict() for item in assembly.config.framework_modules],
            "root_module_ids": dict(assembly.root_module_ids),
            "modules": [item.to_dict() for item in framework_modules],
        },
        "config": {
            "project_file": assembly.config.project_file,
            "communication": assembly.config.communication,
            "exact": assembly.config.exact,
            "modules": [item.to_dict() for item in config_modules],
        },
        "code": {
            "modules": [item.to_dict() for item in code_modules],
            "runtime_exports": {
                key: value
                for key, value in assembly.runtime_exports.items()
                if key != "runtime_blueprint"
            },
        },
        "evidence": {
            "modules": [item.to_dict() for item in evidence_modules],
            "exports": evidence_exports,
            "validation_reports": assembly.validation_reports.to_dict(),
        },
        "links": _build_links(framework_modules, config_modules, code_modules, evidence_modules),
    }


def compile_project_runtime(project_file: str | Path = DEFAULT_PROJECT_FILE) -> ProjectRuntimeAssembly:
    resolved_project_file = normalize_project_path(project_file)
    project_config = load_project_config(resolved_project_file)
    framework_modules, root_module_ids = resolve_selected_framework_modules(project_config.framework_modules)
    config_modules = build_config_modules(project_config, framework_modules)
    code_modules, code_exports = build_code_modules(config_modules, root_module_ids=root_module_ids)
    draft_assembly = ProjectRuntimeAssembly(
        project_file=relative_path(resolved_project_file),
        metadata=project_config.metadata,
        config=project_config,
        root_module_ids=root_module_ids,
        runtime_exports=code_exports,
        validation_reports=ValidationReports.empty(),
        generated_artifacts=_artifact_paths(
            resolved_project_file,
            project_config.artifacts.canonical_json,
        ),
    )
    evidence_modules, evidence_exports, validation_reports = build_evidence_modules(draft_assembly, code_modules)
    runtime_exports = dict(code_exports)
    runtime_exports["runtime_blueprint"] = evidence_exports["runtime_blueprint"]
    assembly = ProjectRuntimeAssembly(
        project_file=draft_assembly.project_file,
        metadata=draft_assembly.metadata,
        config=project_config,
        root_module_ids=root_module_ids,
        runtime_exports=runtime_exports,
        validation_reports=validation_reports,
        generated_artifacts=draft_assembly.generated_artifacts,
    )
    canonical = _build_canonical(
        assembly,
        framework_modules,
        config_modules,
        code_modules,
        evidence_modules,
        evidence_exports,
    )
    return ProjectRuntimeAssembly(
        project_file=assembly.project_file,
        metadata=assembly.metadata,
        config=assembly.config,
        root_module_ids=assembly.root_module_ids,
        runtime_exports=assembly.runtime_exports,
        validation_reports=assembly.validation_reports,
        generated_artifacts=assembly.generated_artifacts,
        canonical=canonical,
    )


@lru_cache(maxsize=4)
def load_project_runtime(project_file: str | Path = DEFAULT_PROJECT_FILE) -> ProjectRuntimeAssembly:
    return compile_project_runtime(project_file)


def materialize_project_runtime(project_file: str | Path = DEFAULT_PROJECT_FILE) -> ProjectRuntimeAssembly:
    resolved_project_file = normalize_project_path(project_file)
    assembly = compile_project_runtime(resolved_project_file)
    generated = resolved_project_file.parent / "generated"
    generated.mkdir(parents=True, exist_ok=True)
    expected = {
        assembly.config.artifacts.canonical_json,
    }
    cleanup_generated_output_dir(generated, expected)
    canonical_path = generated / assembly.config.artifacts.canonical_json
    canonical_text = json.dumps(assembly.canonical, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    canonical_path.write_text(canonical_text, encoding="utf-8")
    load_project_runtime.cache_clear()
    return assembly
