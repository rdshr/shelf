from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from rule_validation_models import ValidationReports


def jsonable(value: Any) -> Any:
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return jsonable(value.to_dict())
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    return value


@dataclass(frozen=True)
class ProjectMetadata:
    project_id: str
    runtime_scene: str
    display_name: str
    description: str
    version: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class SelectedFrameworkModule:
    role: str
    framework_file: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ArtifactConfig:
    canonical_json: str
    runtime_snapshot_py: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ProjectConfig:
    project_file: str
    metadata: ProjectMetadata
    framework_modules: tuple[SelectedFrameworkModule, ...]
    communication: dict[str, Any]
    exact: dict[str, Any]
    artifacts: ArtifactConfig

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.metadata.to_dict(),
            "framework": {
                "modules": [item.to_dict() for item in self.framework_modules],
            },
            "communication": jsonable(self.communication),
            "exact": jsonable(self.exact),
            "artifacts": self.artifacts.to_dict(),
        }


@dataclass(frozen=True)
class SeedDocumentSource:
    document_id: str
    title: str
    summary: str
    body_markdown: str
    tags: tuple[str, ...]
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SeedDocumentSource":
        return cls(
            document_id=str(payload["document_id"]),
            title=str(payload["title"]),
            summary=str(payload["summary"]),
            body_markdown=str(payload["body_markdown"]),
            tags=tuple(str(item) for item in payload.get("tags", [])),
            updated_at=str(payload["updated_at"]),
        )


@dataclass(frozen=True)
class KnowledgeDocumentSection:
    section_id: str
    title: str
    level: int
    markdown: str
    html: str
    plain_text: str
    search_text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "KnowledgeDocumentSection":
        return cls(
            section_id=str(payload["section_id"]),
            title=str(payload["title"]),
            level=int(payload["level"]),
            markdown=str(payload["markdown"]),
            html=str(payload["html"]),
            plain_text=str(payload["plain_text"]),
            search_text=str(payload["search_text"]),
        )


@dataclass(frozen=True)
class KnowledgeDocument:
    document_id: str
    title: str
    summary: str
    body_markdown: str
    body_html: str
    tags: tuple[str, ...]
    updated_at: str
    sections: tuple[KnowledgeDocumentSection, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "title": self.title,
            "summary": self.summary,
            "body_markdown": self.body_markdown,
            "body_html": self.body_html,
            "tags": list(self.tags),
            "updated_at": self.updated_at,
            "sections": [item.to_dict() for item in self.sections],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "KnowledgeDocument":
        return cls(
            document_id=str(payload["document_id"]),
            title=str(payload["title"]),
            summary=str(payload["summary"]),
            body_markdown=str(payload["body_markdown"]),
            body_html=str(payload["body_html"]),
            tags=tuple(str(item) for item in payload.get("tags", [])),
            updated_at=str(payload["updated_at"]),
            sections=tuple(
                KnowledgeDocumentSection.from_dict(item)
                for item in payload.get("sections", [])
                if isinstance(item, dict)
            ),
        )


@dataclass(frozen=True)
class GeneratedArtifactPaths:
    directory: str
    canonical_json: str
    runtime_snapshot_py: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ProjectRuntimeAssembly:
    project_file: str
    metadata: ProjectMetadata
    config: ProjectConfig
    root_module_ids: dict[str, str]
    runtime_exports: dict[str, Any]
    validation_reports: ValidationReports
    generated_artifacts: GeneratedArtifactPaths | None = None
    canonical: dict[str, Any] = field(default_factory=dict)

    @property
    def project_config_view(self) -> dict[str, Any]:
        return self.config.to_dict()

    def require_runtime_export(self, export_key: str) -> Any:
        if export_key not in self.runtime_exports:
            raise KeyError(f"missing runtime export: {export_key}")
        return self.runtime_exports[export_key]

    @property
    def public_summary(self) -> dict[str, Any]:
        return {
            "project_file": self.project_file,
            "project": self.metadata.to_dict(),
            "framework": [item.to_dict() for item in self.config.framework_modules],
            "runtime_export_keys": sorted(self.runtime_exports),
            "validation_reports": self.validation_reports.to_dict(),
            "generated_artifacts": self.generated_artifacts.to_dict() if self.generated_artifacts else None,
        }

    def to_runtime_snapshot_dict(self) -> dict[str, Any]:
        return {
            "project_file": self.project_file,
            "project": self.metadata.to_dict(),
            "project_config": self.project_config_view,
            "root_module_ids": dict(self.root_module_ids),
            "runtime_exports": jsonable(self.runtime_exports),
            "validation_reports": self.validation_reports.to_dict(),
            "generated_artifacts": self.generated_artifacts.to_dict() if self.generated_artifacts else None,
            "canonical": jsonable(self.canonical),
        }
