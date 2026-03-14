from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from project_runtime.project_config_source import load_project_config_document


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECTS_DIR = REPO_ROOT / "projects"
PROJECT_FILE_NAME = "project.toml"


def _relative_path(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def _require_table(parent: dict[str, Any], key: str, *, file_path: Path) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{file_path}: missing table {key}")
    return value


def _require_string(parent: dict[str, Any], key: str, *, file_path: Path) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{file_path}: missing string {key}")
    return value.strip()


@dataclass(frozen=True)
class FrameworkDrivenProjectRecord:
    project_id: str
    runtime_scene: str
    project_file: str
    generated_dir: str
    root_modules: dict[str, str]
    artifact_contract: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "runtime_scene": self.runtime_scene,
            "project_file": self.project_file,
            "generated_dir": self.generated_dir,
            "root_modules": dict(self.root_modules),
            "artifact_contract": dict(self.artifact_contract),
        }


@dataclass(frozen=True)
class ProjectDiscoveryAuditEntry:
    project_id: str
    directory: str
    classification: str
    reasons: tuple[str, ...]
    project_file: str
    runtime_scene: str
    root_modules: dict[str, str]
    generated_dir: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "directory": self.directory,
            "classification": self.classification,
            "reasons": list(self.reasons),
            "project_file": self.project_file,
            "runtime_scene": self.runtime_scene,
            "root_modules": dict(self.root_modules),
            "generated_dir": self.generated_dir,
        }


def _artifact_contract(data: dict[str, Any], *, file_path: Path) -> dict[str, str]:
    refinement = _require_table(data, "refinement", file_path=file_path)
    artifacts = _require_table(refinement, "artifacts", file_path=file_path)
    names: dict[str, str] = {}
    for key in (
        "canonical_graph_json",
        "runtime_bundle_py",
        "generation_manifest_json",
        "governance_manifest_json",
        "governance_tree_json",
        "strict_zone_report_json",
        "object_coverage_report_json",
    ):
        names[key] = _require_string(artifacts, key, file_path=file_path)
    return names


def discover_framework_driven_projects(projects_dir: Path | None = None) -> tuple[FrameworkDrivenProjectRecord, ...]:
    root = (projects_dir or PROJECTS_DIR).resolve()
    records: list[FrameworkDrivenProjectRecord] = []
    for project_file in sorted(root.glob(f"*/{PROJECT_FILE_NAME}")):
        document = load_project_config_document(project_file)
        project_table = _require_table(document.merged_data, "project", file_path=project_file)
        selection_table = _require_table(document.merged_data, "selection", file_path=project_file)
        root_modules = _require_table(selection_table, "root_modules", file_path=project_file)
        records.append(
            FrameworkDrivenProjectRecord(
                project_id=_require_string(project_table, "project_id", file_path=project_file),
                runtime_scene=_require_string(project_table, "runtime_scene", file_path=project_file),
                project_file=_relative_path(project_file),
                generated_dir=_relative_path(project_file.parent / "generated"),
                root_modules={
                    "frontend": _require_string(root_modules, "frontend", file_path=project_file),
                    "knowledge_base": _require_string(root_modules, "knowledge_base", file_path=project_file),
                    "backend": _require_string(root_modules, "backend", file_path=project_file),
                },
                artifact_contract=_artifact_contract(document.merged_data, file_path=project_file),
            )
        )
    return tuple(records)


def build_project_discovery_audit(projects_dir: Path | None = None) -> dict[str, Any]:
    projects = discover_framework_driven_projects(projects_dir)
    entries = [
        ProjectDiscoveryAuditEntry(
            project_id=item.project_id,
            directory=Path(item.project_file).parent.as_posix(),
            classification="framework-package-project",
            reasons=(
                "contains project.toml",
                "declares root framework modules",
                "declares canonical-derived artifact contract",
            ),
            project_file=item.project_file,
            runtime_scene=item.runtime_scene,
            root_modules=item.root_modules,
            generated_dir=item.generated_dir,
        )
        for item in projects
    ]
    return {
        "schema_version": "project-discovery-audit/v2",
        "project_count": len(entries),
        "projects": [item.to_dict() for item in entries],
    }


def render_project_discovery_audit_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Project Discovery Audit",
        "",
        f"- schema_version: `{payload.get('schema_version', 'unknown')}`",
        f"- project_count: `{payload.get('project_count', 0)}`",
        "",
    ]
    for item in payload.get("projects", []):
        if not isinstance(item, dict):
            continue
        lines.append(f"## {item.get('project_id', 'unknown')}")
        lines.append("")
        lines.append(f"- project_file: `{item.get('project_file', '')}`")
        lines.append(f"- runtime_scene: `{item.get('runtime_scene', '')}`")
        lines.append(f"- generated_dir: `{item.get('generated_dir', '')}`")
        lines.append(f"- classification: `{item.get('classification', '')}`")
        root_modules = item.get("root_modules", {})
        if isinstance(root_modules, dict):
            lines.append(f"- frontend_root: `{root_modules.get('frontend', '')}`")
            lines.append(f"- knowledge_base_root: `{root_modules.get('knowledge_base', '')}`")
            lines.append(f"- backend_root: `{root_modules.get('backend', '')}`")
        reasons = item.get("reasons", [])
        if isinstance(reasons, list):
            for reason in reasons:
                lines.append(f"- reason: {reason}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def project_discovery_audit_json(projects_dir: Path | None = None) -> str:
    return json.dumps(build_project_discovery_audit(projects_dir), ensure_ascii=False, indent=2)

