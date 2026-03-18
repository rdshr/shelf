from __future__ import annotations

from typing import Any

from project_runtime.models import ProjectRuntimeAssembly


def resolve_kv_database_runtime_spec(project: ProjectRuntimeAssembly) -> dict[str, Any]:
    value = project.require_runtime_export("kv_database_runtime_spec")
    if not isinstance(value, dict):
        raise ValueError("kv_database_runtime_spec export must be a dict")
    return dict(value)


def project_runtime_public_summary(project: ProjectRuntimeAssembly) -> dict[str, Any]:
    spec = resolve_kv_database_runtime_spec(project)
    wal = spec.get("wal", {})
    contract = spec.get("contract", {})
    return {
        "project_file": project.project_file,
        "project": project.metadata.to_dict(),
        "framework": [item.to_dict() for item in project.config.framework_modules],
        "resolved_module_ids": sorted(project.root_module_ids.values()),
        "module_chain": ["framework", "config", "code", "evidence"],
        "kv_database_summary": {
            "allowed_operations": contract.get("operation", {}).get("allowed_operations", []),
            "missing_key_policy": contract.get("operation", {}).get("missing_key_policy"),
            "key_python_type": contract.get("key", {}).get("python_type"),
            "value_serialization": contract.get("value", {}).get("serialization"),
            "wal_path": wal.get("path"),
            "replay_strategy": wal.get("replay_strategy"),
        },
        "validation_reports": project.validation_reports.to_dict(),
        "generated_artifacts": project.generated_artifacts.to_dict() if project.generated_artifacts else None,
    }
