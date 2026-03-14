from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from framework_ir import FrameworkModule
from framework_packages.contract import RuntimeAppEntrypoint, RuntimeValidationHook
from rule_validation_models import ValidationReports

if TYPE_CHECKING:
    from framework_packages import FrameworkPackageRegistry, PackageCompileResult


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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SelectedRootModule:
    slot_id: str
    role: str
    framework_file: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ModuleSelection:
    preset: str
    roots: tuple[SelectedRootModule, ...]

    @property
    def root_modules(self) -> dict[str, str]:
        return {item.role: item.framework_file for item in self.roots}

    def require_role(self, role: str) -> SelectedRootModule:
        for item in self.roots:
            if item.role == role:
                return item
        raise KeyError(f"missing selected root role: {role}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "preset": self.preset,
            "roots": [item.to_dict() for item in self.roots],
            "root_modules": dict(self.root_modules),
        }


@dataclass(frozen=True)
class SurfaceCopyConfig:
    hero_kicker: str
    hero_title: str
    hero_copy: str
    library_title: str
    preview_title: str
    toc_title: str
    chat_title: str
    empty_state_title: str
    empty_state_copy: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SurfaceConfig:
    shell: str
    layout_variant: str
    sidebar_width: str
    preview_mode: str
    density: str
    copy: SurfaceCopyConfig

    def to_dict(self) -> dict[str, Any]:
        return {
            "shell": self.shell,
            "layout_variant": self.layout_variant,
            "sidebar_width": self.sidebar_width,
            "preview_mode": self.preview_mode,
            "density": self.density,
            "copy": self.copy.to_dict(),
        }


@dataclass(frozen=True)
class VisualConfig:
    brand: str
    accent: str
    surface_preset: str
    radius_scale: str
    shadow_level: str
    font_scale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FeatureConfig:
    library: bool
    preview: bool
    chat: bool
    citation: bool
    return_to_anchor: bool
    upload: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RouteConfig:
    home: str
    workbench: str
    basketball_showcase: str
    knowledge_list: str
    knowledge_detail: str
    document_detail_prefix: str
    api_prefix: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ShowcasePageConfig:
    title: str
    kicker: str
    headline: str
    intro: str
    back_to_chat_label: str
    browse_knowledge_label: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class A11yConfig:
    reading_order: tuple[str, ...]
    keyboard_nav: tuple[str, ...]
    announcements: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "reading_order": list(self.reading_order),
            "keyboard_nav": list(self.keyboard_nav),
            "announcements": list(self.announcements),
        }


@dataclass(frozen=True)
class LibraryConfig:
    knowledge_base_id: str
    knowledge_base_name: str
    knowledge_base_description: str
    enabled: bool
    source_types: tuple[str, ...]
    metadata_fields: tuple[str, ...]
    default_focus: str
    list_variant: str
    allow_create: bool
    allow_delete: bool
    search_placeholder: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "knowledge_base_id": self.knowledge_base_id,
            "knowledge_base_name": self.knowledge_base_name,
            "knowledge_base_description": self.knowledge_base_description,
            "enabled": self.enabled,
            "source_types": list(self.source_types),
            "metadata_fields": list(self.metadata_fields),
            "default_focus": self.default_focus,
            "list_variant": self.list_variant,
            "allow_create": self.allow_create,
            "allow_delete": self.allow_delete,
            "search_placeholder": self.search_placeholder,
        }


@dataclass(frozen=True)
class PreviewConfig:
    enabled: bool
    renderers: tuple[str, ...]
    anchor_mode: str
    show_toc: bool
    preview_variant: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "renderers": list(self.renderers),
            "anchor_mode": self.anchor_mode,
            "show_toc": self.show_toc,
            "preview_variant": self.preview_variant,
        }


@dataclass(frozen=True)
class ChatConfig:
    enabled: bool
    citations_enabled: bool
    mode: str
    citation_style: str
    bubble_variant: str
    composer_variant: str
    system_prompt: str
    placeholder: str
    welcome: str
    welcome_prompts: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["welcome_prompts"] = list(self.welcome_prompts)
        return payload


@dataclass(frozen=True)
class ContextConfig:
    selection_mode: str
    max_citations: int
    max_preview_sections: int
    sticky_document: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReturnConfig:
    enabled: bool
    targets: tuple[str, ...]
    anchor_restore: bool
    citation_card_variant: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "targets": list(self.targets),
            "anchor_restore": self.anchor_restore,
            "citation_card_variant": self.citation_card_variant,
        }


@dataclass(frozen=True)
class FrontendRefinementConfig:
    renderer: str
    style_profile: str
    script_profile: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BackendRefinementConfig:
    renderer: str
    transport: str
    retrieval_strategy: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceRefinementConfig:
    project_config_endpoint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ArtifactConfig:
    canonical_graph_json: str
    runtime_snapshot_py: str
    generation_manifest_json: str
    derived_governance_manifest_json: str
    derived_governance_tree_json: str
    strict_zone_report_json: str
    object_coverage_report_json: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def file_names(self) -> tuple[str, ...]:
        return (
            self.canonical_graph_json,
            self.runtime_snapshot_py,
            self.generation_manifest_json,
            self.derived_governance_manifest_json,
            self.derived_governance_tree_json,
            self.strict_zone_report_json,
            self.object_coverage_report_json,
        )


@dataclass(frozen=True)
class RefinementConfig:
    frontend: FrontendRefinementConfig
    backend: BackendRefinementConfig
    evidence: EvidenceRefinementConfig
    artifacts: ArtifactConfig

    def to_dict(self) -> dict[str, Any]:
        return {
            "frontend": self.frontend.to_dict(),
            "backend": self.backend.to_dict(),
            "evidence": self.evidence.to_dict(),
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
    canonical_graph_json: str
    runtime_snapshot_py: str
    generation_manifest_json: str
    derived_governance_manifest_json: str
    derived_governance_tree_json: str
    strict_zone_report_json: str
    object_coverage_report_json: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    @classmethod
    def from_artifact_config(
        cls,
        artifact_names: ArtifactConfig,
        *,
        directory: Path,
        path_renderer: Callable[[Path], str],
    ) -> "GeneratedArtifactPaths":
        return cls(
            directory=path_renderer(directory),
            canonical_graph_json=path_renderer(directory / artifact_names.canonical_graph_json),
            runtime_snapshot_py=path_renderer(directory / artifact_names.runtime_snapshot_py),
            generation_manifest_json=path_renderer(directory / artifact_names.generation_manifest_json),
            derived_governance_manifest_json=path_renderer(directory / artifact_names.derived_governance_manifest_json),
            derived_governance_tree_json=path_renderer(directory / artifact_names.derived_governance_tree_json),
            strict_zone_report_json=path_renderer(directory / artifact_names.strict_zone_report_json),
            object_coverage_report_json=path_renderer(directory / artifact_names.object_coverage_report_json),
        )


@dataclass(frozen=True)
class GeneratedArtifactOutputPaths:
    canonical_graph_json: Path
    runtime_snapshot_py: Path
    generation_manifest_json: Path
    derived_governance_manifest_json: Path
    derived_governance_tree_json: Path
    strict_zone_report_json: Path
    object_coverage_report_json: Path

    @classmethod
    def from_artifact_config(cls, artifact_names: ArtifactConfig, *, output_dir: Path) -> "GeneratedArtifactOutputPaths":
        return cls(
            canonical_graph_json=output_dir / artifact_names.canonical_graph_json,
            runtime_snapshot_py=output_dir / artifact_names.runtime_snapshot_py,
            generation_manifest_json=output_dir / artifact_names.generation_manifest_json,
            derived_governance_manifest_json=output_dir / artifact_names.derived_governance_manifest_json,
            derived_governance_tree_json=output_dir / artifact_names.derived_governance_tree_json,
            strict_zone_report_json=output_dir / artifact_names.strict_zone_report_json,
            object_coverage_report_json=output_dir / artifact_names.object_coverage_report_json,
        )


@dataclass(frozen=True)
class UnifiedProjectConfig:
    project_file: str
    section_sources: dict[str, str]
    metadata: ProjectMetadata
    selection: ModuleSelection
    truth: dict[str, Any]
    refinement: dict[str, Any]
    artifact_config: ArtifactConfig
    narrative: dict[str, Any]

    def truth_payload(self) -> dict[str, Any]:
        return jsonable(self.truth)

    def refinement_payload(self) -> dict[str, Any]:
        return jsonable(self.refinement)

    def project_config_view(self) -> dict[str, Any]:
        return {
            "project": self.metadata.to_dict(),
            "selection": self.selection.to_dict(),
            "truth": self.truth_payload(),
            "refinement": self.refinement_payload(),
            "narrative": jsonable(self.narrative),
        }

    def root_payload(self) -> dict[str, Any]:
        return {
            "project": self.metadata.to_dict(),
            "selection": self.selection.to_dict(),
            "truth": self.truth_payload(),
            "refinement": self.refinement_payload(),
            "narrative": jsonable(self.narrative),
        }


@dataclass(frozen=True)
class UiSpecPaths:
    knowledge_base_detail_path: str
    document_detail_path: str
    basketball_showcase_path: str

    @classmethod
    def from_route(cls, route: RouteConfig) -> "UiSpecPaths":
        return cls(
            knowledge_base_detail_path=f"{route.knowledge_detail}/{{knowledge_base_id}}",
            document_detail_path=f"{route.document_detail_prefix}/{{document_id}}",
            basketball_showcase_path=route.basketball_showcase,
        )


@dataclass(frozen=True)
class ResolvedModuleRoot:
    slot_id: str
    role: str
    framework_file: str
    module: FrameworkModule

    @property
    def module_id(self) -> str:
        return self.module.module_id

    def to_dict(self) -> dict[str, str]:
        return {
            "slot_id": self.slot_id,
            "role": self.role,
            "framework_file": self.framework_file,
            "module_id": self.module.module_id,
        }


@dataclass(frozen=True)
class ResolvedModuleTree:
    roots: tuple[ResolvedModuleRoot, ...]
    modules: tuple[FrameworkModule, ...]

    def require_role(self, role: str) -> FrameworkModule:
        for item in self.roots:
            if item.role == role:
                return item.module
        raise KeyError(f"missing resolved root role: {role}")

    def root_module_ids(self) -> dict[str, str]:
        return {item.role: item.module.module_id for item in self.roots}

    def root_package_inputs(self) -> tuple[dict[str, str], ...]:
        return tuple(item.to_dict() for item in self.roots)


@dataclass(frozen=True)
class ProjectCompilationState:
    project_file: str
    config: UnifiedProjectConfig
    package_registry: FrameworkPackageRegistry
    module_tree: ResolvedModuleTree
    package_results: dict[str, "PackageCompileResult"]

    @property
    def metadata(self) -> ProjectMetadata:
        return self.config.metadata

    @property
    def selection(self) -> ModuleSelection:
        return self.config.selection


@dataclass(frozen=True)
class RuntimeProjection:
    package_exports: dict[str, dict[str, Any]]
    export_index: dict[str, dict[str, Any]]
    app_entrypoints: tuple[RuntimeAppEntrypoint, ...]
    validation_hooks: tuple[RuntimeValidationHook, ...]

    @property
    def export_values(self) -> dict[str, Any]:
        return {
            export_key: binding["value"]
            for export_key, binding in self.export_index.items()
        }

    def require_export(self, export_key: str) -> Any:
        binding = self.export_index.get(export_key)
        if binding is None:
            raise KeyError(f"missing runtime export: {export_key}")
        return binding["value"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_exports": jsonable(self.package_exports),
            "export_index": jsonable(self.export_index),
            "app_entrypoints": [item.to_dict() for item in self.app_entrypoints],
            "validation_hooks": [item.to_dict() for item in self.validation_hooks],
        }


@dataclass(frozen=True)
class ProjectRuntimeAssembly:
    project_file: str
    metadata: ProjectMetadata
    selection: ModuleSelection
    project_config_view: dict[str, Any]
    package_compile_order: tuple[str, ...]
    root_module_ids: dict[str, str]
    runtime_projection: RuntimeProjection
    validation_reports: ValidationReports
    generated_artifacts: GeneratedArtifactPaths | None = None
    derived_views: dict[str, dict[str, str]] = field(default_factory=dict)
    canonical_graph: dict[str, Any] = field(default_factory=dict)

    @property
    def public_summary(self) -> dict[str, Any]:
        return {
            "project_file": self.project_file,
            "project": self.metadata.to_dict(),
            "selection": self.selection.to_dict(),
            "package_compile_order": list(self.package_compile_order),
            "runtime_export_keys": sorted(self.runtime_projection.export_values),
            "validation_reports": self.validation_reports.to_dict(),
            "generated_artifacts": self.generated_artifacts.to_dict() if self.generated_artifacts else None,
        }

    @property
    def runtime_exports(self) -> dict[str, Any]:
        return dict(self.runtime_projection.export_values)

    def require_runtime_export(self, export_key: str) -> Any:
        return self.runtime_projection.require_export(export_key)

    def to_runtime_snapshot_dict(self) -> dict[str, Any]:
        return {
            "project_file": self.project_file,
            "project": self.metadata.to_dict(),
            "selection": self.selection.to_dict(),
            "root_module_ids": dict(self.root_module_ids),
            "package_compile_order": list(self.package_compile_order),
            "project_config": self.project_config_view,
            "runtime_projection": self.runtime_projection.to_dict(),
            "runtime_exports": jsonable(self.runtime_exports),
            "validation_reports": self.validation_reports.to_dict(),
            "generated_artifacts": self.generated_artifacts.to_dict() if self.generated_artifacts else None,
            "canonical_graph": self.canonical_graph,
        }

    def to_spec_dict(self) -> dict[str, Any]:
        return self.to_runtime_snapshot_dict()
