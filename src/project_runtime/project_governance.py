from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECTS_DIR = REPO_ROOT / "projects"
PROJECT_FILE_NAME = "project.toml"


def _relative_path(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def discover_project_entry_files(projects_dir: Path | None = None) -> tuple[Path, ...]:
    root = (projects_dir or PROJECTS_DIR).resolve()
    return tuple(sorted(project_file.resolve() for project_file in root.glob(f"*/{PROJECT_FILE_NAME}")))


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must decode into object")
    return payload


def _load_canonical_graph(project_dir: Path) -> tuple[Path, dict[str, Any]]:
    generated_dir = project_dir / "generated"
    if not generated_dir.exists():
        raise ValueError(f"{project_dir}: missing generated directory")
    candidates = sorted(generated_dir.glob("*.json"))
    for path in candidates:
        payload = _read_json(path)
        schema_version = payload.get("schema_version")
        if isinstance(schema_version, str) and schema_version.startswith("framework-package-canonical/"):
            return path, payload
    raise ValueError(f"{project_dir}: canonical graph not found in generated directory")


@dataclass(frozen=True)
class FrameworkDrivenProjectRecord:
    project_id: str
    runtime_scene: str
    project_file: str
    generated_dir: str
    root_modules: dict[str, str]
    artifact_contract: dict[str, str]
    canonical_graph_path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "runtime_scene": self.runtime_scene,
            "project_file": self.project_file,
            "generated_dir": self.generated_dir,
            "root_modules": dict(self.root_modules),
            "artifact_contract": dict(self.artifact_contract),
            "canonical_graph_path": self.canonical_graph_path,
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
    canonical_graph_path: str

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
            "canonical_graph_path": self.canonical_graph_path,
        }


def discover_framework_driven_projects(projects_dir: Path | None = None) -> tuple[FrameworkDrivenProjectRecord, ...]:
    records: list[FrameworkDrivenProjectRecord] = []
    for project_file in discover_project_entry_files(projects_dir):
        project_dir = project_file.parent
        canonical_path, canonical = _load_canonical_graph(project_dir)
        project_payload = canonical.get("project", {})
        framework_layer = canonical.get("layers", {}).get("framework", {})
        root_modules = framework_layer.get("selection", {}).get("root_modules", {})
        evidence_layer = canonical.get("layers", {}).get("evidence", {})
        generated_artifacts = evidence_layer.get("generated_artifacts", {})
        artifact_contract = {
            key: Path(value).name
            for key, value in generated_artifacts.items()
            if isinstance(key, str) and isinstance(value, str) and key != "directory"
        }
        records.append(
            FrameworkDrivenProjectRecord(
                project_id=str(project_payload.get("project_id", project_dir.name)),
                runtime_scene=str(project_payload.get("runtime_scene", "")),
                project_file=_relative_path(project_file),
                generated_dir=_relative_path(project_dir / "generated"),
                root_modules={str(key): str(value) for key, value in root_modules.items()} if isinstance(root_modules, dict) else {},
                artifact_contract=artifact_contract,
                canonical_graph_path=_relative_path(canonical_path),
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
                "contains project entry file",
                "governance metadata derived from canonical graph",
                "derived artifacts point back to canonical graph",
            ),
            project_file=item.project_file,
            runtime_scene=item.runtime_scene,
            root_modules=item.root_modules,
            generated_dir=item.generated_dir,
            canonical_graph_path=item.canonical_graph_path,
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
        lines.append(f"- canonical_graph: `{item.get('canonical_graph_path', '')}`")
        lines.append(f"- classification: `{item.get('classification', '')}`")
        root_modules = item.get("root_modules", {})
        if isinstance(root_modules, dict):
            for role, framework_file in sorted(root_modules.items()):
                lines.append(f"- root[{role}]: `{framework_file}`")
        reasons = item.get("reasons", [])
        if isinstance(reasons, list):
            for reason in reasons:
                lines.append(f"- reason: {reason}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def project_discovery_audit_json(projects_dir: Path | None = None) -> str:
    return json.dumps(build_project_discovery_audit(projects_dir), ensure_ascii=False, indent=2)
