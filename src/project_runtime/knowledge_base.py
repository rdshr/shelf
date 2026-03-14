from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from html import escape
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Callable

from framework_ir import FrameworkModule, FrameworkRegistry, load_framework_registry
from framework_packages import FrameworkPackageRegistry, PackageCompileInput, PackageCompileResult, load_builtin_package_registry
from project_runtime.governance import build_derived_view_payloads
from project_runtime.knowledge_base_contract import (
    KnowledgeBaseTemplateContract,
    load_knowledge_base_template_contract,
)
from project_runtime.project_config_source import ComposedTomlDocument, load_project_config_document
from rule_validation_models import ValidationReports


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_KNOWLEDGE_BASE_PROJECT_FILE = REPO_ROOT / "projects/knowledge_base_basic/project.toml"
KNOWLEDGE_BASE_RUNTIME_SCENE = "knowledge_base_workbench"
KNOWLEDGE_BASE_CANONICAL_SCHEMA_VERSION = "framework-package-canonical/v1"
LEGACY_GENERATED_ARTIFACT_NAMES = frozenset(
    {
        "framework_ir.json",
        "product_spec.json",
        "implementation_bundle.py",
        "project_bundle.py",
        "workbench_spec.json",
    }
)


def _jsonable(value: Any) -> Any:
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _jsonable(value.to_dict())
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _relative_path(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def _normalize_project_path(project_file: str | Path) -> Path:
    candidate = Path(project_file)
    if not candidate.is_absolute():
        candidate = (REPO_ROOT / candidate).resolve()
    return candidate


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "section"


def _sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _tokenize(text: str) -> tuple[str, ...]:
    return tuple(token for token in re.findall(r"[a-z0-9]{3,}", text.lower()) if token)


def _cleanup_generated_output_dir(output_path: Path, expected_file_names: set[str]) -> None:
    removable_names = expected_file_names | LEGACY_GENERATED_ARTIFACT_NAMES
    for child in output_path.iterdir():
        if not child.is_file():
            continue
        if child.name in expected_file_names:
            continue
        if child.name in removable_names or child.suffix.lower() in {".json", ".py"}:
            child.unlink()


def _require_table(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"missing required table: {key}")
    return value


def _optional_table(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"optional table must decode into object: {key}")
    return value


def _require_string(parent: dict[str, Any], key: str) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing required string: {key}")
    return value.strip()


def _require_bool(parent: dict[str, Any], key: str) -> bool:
    value = parent.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"missing required bool: {key}")
    return value


def _require_int(parent: dict[str, Any], key: str) -> int:
    value = parent.get(key)
    if not isinstance(value, int):
        raise ValueError(f"missing required int: {key}")
    return value


def _require_string_tuple(parent: dict[str, Any], key: str) -> tuple[str, ...]:
    value = parent.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"missing required string list: {key}")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{key} must only contain non-empty strings")
        items.append(item.strip())
    return tuple(items)


def _lookup_dotted_path(payload: dict[str, Any], dotted_path: str) -> Any:
    current: Any = payload
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(dotted_path)
        current = current[part]
    return current


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
class RootModuleSelection:
    frontend: str
    knowledge_base: str
    backend: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ModuleSelection:
    preset: str
    root_modules: RootModuleSelection

    def to_dict(self) -> dict[str, Any]:
        return {
            "preset": self.preset,
            "root_modules": self.root_modules.to_dict(),
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
    runtime_bundle_py: str
    generation_manifest_json: str
    governance_manifest_json: str
    governance_tree_json: str
    strict_zone_report_json: str
    object_coverage_report_json: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def file_names(self) -> tuple[str, ...]:
        return (
            self.canonical_graph_json,
            self.runtime_bundle_py,
            self.generation_manifest_json,
            self.governance_manifest_json,
            self.governance_tree_json,
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


@dataclass(frozen=True)
class GeneratedArtifactPaths:
    directory: str
    canonical_graph_json: str
    runtime_bundle_py: str
    generation_manifest_json: str
    governance_manifest_json: str
    governance_tree_json: str
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
            runtime_bundle_py=path_renderer(directory / artifact_names.runtime_bundle_py),
            generation_manifest_json=path_renderer(directory / artifact_names.generation_manifest_json),
            governance_manifest_json=path_renderer(directory / artifact_names.governance_manifest_json),
            governance_tree_json=path_renderer(directory / artifact_names.governance_tree_json),
            strict_zone_report_json=path_renderer(directory / artifact_names.strict_zone_report_json),
            object_coverage_report_json=path_renderer(directory / artifact_names.object_coverage_report_json),
        )


@dataclass(frozen=True)
class GeneratedArtifactOutputPaths:
    canonical_graph_json: Path
    runtime_bundle_py: Path
    generation_manifest_json: Path
    governance_manifest_json: Path
    governance_tree_json: Path
    strict_zone_report_json: Path
    object_coverage_report_json: Path

    @classmethod
    def from_artifact_config(cls, artifact_names: ArtifactConfig, *, output_dir: Path) -> "GeneratedArtifactOutputPaths":
        return cls(
            canonical_graph_json=output_dir / artifact_names.canonical_graph_json,
            runtime_bundle_py=output_dir / artifact_names.runtime_bundle_py,
            generation_manifest_json=output_dir / artifact_names.generation_manifest_json,
            governance_manifest_json=output_dir / artifact_names.governance_manifest_json,
            governance_tree_json=output_dir / artifact_names.governance_tree_json,
            strict_zone_report_json=output_dir / artifact_names.strict_zone_report_json,
            object_coverage_report_json=output_dir / artifact_names.object_coverage_report_json,
        )


@dataclass(frozen=True)
class UnifiedProjectConfig:
    project_file: str
    section_sources: dict[str, str]
    metadata: ProjectMetadata
    selection: ModuleSelection
    surface: SurfaceConfig
    visual: VisualConfig
    features: FeatureConfig
    route: RouteConfig
    showcase_page: ShowcasePageConfig
    a11y: A11yConfig
    library: LibraryConfig
    preview: PreviewConfig
    chat: ChatConfig
    context: ContextConfig
    return_config: ReturnConfig
    documents: tuple[SeedDocumentSource, ...]
    refinement: RefinementConfig
    narrative: dict[str, Any]

    def truth_payload(self) -> dict[str, Any]:
        return {
            "surface": self.surface.to_dict(),
            "visual": self.visual.to_dict(),
            "features": self.features.to_dict(),
            "route": self.route.to_dict(),
            "showcase_page": self.showcase_page.to_dict(),
            "a11y": self.a11y.to_dict(),
            "library": self.library.to_dict(),
            "preview": self.preview.to_dict(),
            "chat": self.chat.to_dict(),
            "context": self.context.to_dict(),
            "return": self.return_config.to_dict(),
            "documents": [item.to_dict() for item in self.documents],
        }

    def root_payload(self) -> dict[str, Any]:
        return {
            "project": self.metadata.to_dict(),
            "selection": self.selection.to_dict(),
            "truth": self.truth_payload(),
            "refinement": self.refinement.to_dict(),
            "narrative": _jsonable(self.narrative),
        }


@dataclass(frozen=True)
class UiSpecPaths:
    knowledge_base_detail_path: str
    document_detail_path: str
    basketball_showcase_path: str

    @classmethod
    def from_project(cls, project: "KnowledgeBaseProject") -> "UiSpecPaths":
        return cls(
            knowledge_base_detail_path=f"{project.route.knowledge_detail}/{{knowledge_base_id}}",
            document_detail_path=f"{project.route.document_detail_prefix}/{{document_id}}",
            basketball_showcase_path=project.route.basketball_showcase,
        )


@dataclass(frozen=True)
class KnowledgeBaseProject:
    project_file: str
    config: UnifiedProjectConfig
    scene_contract: KnowledgeBaseTemplateContract
    package_registry: FrameworkPackageRegistry
    frontend_ir: FrameworkModule
    domain_ir: FrameworkModule
    backend_ir: FrameworkModule
    resolved_modules: tuple[FrameworkModule, ...]
    package_results: dict[str, PackageCompileResult]
    visual_tokens: dict[str, str]
    documents: tuple[KnowledgeDocument, ...]
    derived_copy: dict[str, str]
    frontend_contract: dict[str, Any]
    workbench_contract: dict[str, Any]
    ui_spec: dict[str, Any]
    backend_spec: dict[str, Any]
    validation_reports: ValidationReports
    generated_artifacts: GeneratedArtifactPaths | None = None
    derived_views: dict[str, dict[str, str]] = field(default_factory=dict)

    @property
    def metadata(self) -> ProjectMetadata:
        return self.config.metadata

    @property
    def template_contract(self) -> KnowledgeBaseTemplateContract:
        return self.scene_contract

    @property
    def selection(self) -> ModuleSelection:
        return self.config.selection

    @property
    def framework(self) -> ModuleSelection:
        return self.selection

    @property
    def surface(self) -> SurfaceConfig:
        return self.config.surface

    @property
    def visual(self) -> VisualConfig:
        return self.config.visual

    @property
    def features(self) -> FeatureConfig:
        return self.config.features

    @property
    def route(self) -> RouteConfig:
        return self.config.route

    @property
    def showcase_page(self) -> ShowcasePageConfig:
        return self.config.showcase_page

    @property
    def a11y(self) -> A11yConfig:
        return self.config.a11y

    @property
    def library(self) -> LibraryConfig:
        return self.config.library

    @property
    def preview(self) -> PreviewConfig:
        return self.config.preview

    @property
    def chat(self) -> ChatConfig:
        return self.config.chat

    @property
    def context(self) -> ContextConfig:
        return self.config.context

    @property
    def return_config(self) -> ReturnConfig:
        return self.config.return_config

    @property
    def refinement(self) -> RefinementConfig:
        return self.config.refinement

    @property
    def copy(self) -> dict[str, str]:
        return dict(self.derived_copy)

    @property
    def public_summary(self) -> dict[str, Any]:
        return _build_public_summary(self)

    @property
    def project_config_view(self) -> dict[str, Any]:
        return _build_project_config_view(self)

    def _resolved_page_routes(self) -> dict[str, str]:
        return {
            "home": self.route.home,
            "chat_home": self.route.workbench,
            "basketball_showcase": self.route.basketball_showcase,
            "knowledge_list": self.route.knowledge_list,
            "knowledge_detail": f"{self.route.knowledge_detail}/{{knowledge_base_id}}",
            "document_detail": f"{self.route.document_detail_prefix}/{{document_id}}",
        }

    def _resolved_api_routes(self) -> dict[str, str]:
        return {
            "knowledge_bases": f"{self.route.api_prefix}/knowledge-bases",
            "knowledge_base_detail": f"{self.route.api_prefix}/knowledge-bases/{{knowledge_base_id}}",
            "documents": f"{self.route.api_prefix}/documents",
            "create_document": f"{self.route.api_prefix}/documents",
            "document_detail": f"{self.route.api_prefix}/documents/{{document_id}}",
            "delete_document": f"{self.route.api_prefix}/documents/{{document_id}}",
            "section_detail": f"{self.route.api_prefix}/documents/{{document_id}}/sections/{{section_id}}",
            "tags": f"{self.route.api_prefix}/tags",
            "chat_turns": f"{self.route.api_prefix}/chat/turns",
            "project_config": self.refinement.evidence.project_config_endpoint,
        }

    def to_runtime_bundle_dict(self) -> dict[str, Any]:
        return {
            "project_file": self.project_file,
            "project": self.metadata.to_dict(),
            "selection": self.selection.to_dict(),
            "project_config": self.project_config_view,
            "routes": {
                **self.route.to_dict(),
                "pages": self._resolved_page_routes(),
                "api": self._resolved_api_routes(),
            },
            "frontend_contract": self.frontend_contract,
            "workbench_contract": self.workbench_contract,
            "ui_spec": self.ui_spec,
            "backend_spec": self.backend_spec,
            "documents": [item.to_dict() for item in self.documents],
            "validation_reports": self.validation_reports.to_dict(),
            "generated_artifacts": self.generated_artifacts.to_dict() if self.generated_artifacts else None,
            "canonical_graph": self.to_canonical_graph_dict(),
        }

    def to_spec_dict(self) -> dict[str, Any]:
        return self.to_runtime_bundle_dict()

    def to_canonical_graph_dict(self) -> dict[str, Any]:
        generated_artifacts = _effective_generated_artifacts(self).to_dict()
        return {
            "schema_version": KNOWLEDGE_BASE_CANONICAL_SCHEMA_VERSION,
            "project": self.metadata.to_dict(),
            "layers": {
                "framework": {
                    "author_source": "framework/*.md",
                    "selection": self.selection.to_dict(),
                    "module_tree": {
                        "root_module_ids": [
                            self.frontend_ir.module_id,
                            self.domain_ir.module_id,
                            self.backend_ir.module_id,
                        ],
                        "modules": [
                            {
                                "module_id": item.module_id,
                                "framework_file": item.path,
                                "title_cn": item.title_cn,
                                "title_en": item.title_en,
                                "intro": item.intro,
                                "upstream_module_ids": list(item.export_surface().upstream_module_ids),
                            }
                            for item in self.resolved_modules
                        ],
                    },
                    "registry_binding": [item.to_dict() for item in self.package_registry.iter_registrations()],
                },
                "config": {
                    "project_file": self.project_file,
                    "section_sources": dict(self.config.section_sources),
                    "selection": self.selection.to_dict(),
                    "truth": self.config.truth_payload(),
                    "refinement": self.refinement.to_dict(),
                    "narrative": _jsonable(self.config.narrative),
                    "projection": {
                        module_id: {
                            "config_contract": result.config_contract.to_dict(),
                            "config_slice": _jsonable(result.config_slice),
                        }
                        for module_id, result in sorted(self.package_results.items())
                    },
                },
                "code": {
                    "package_compile_order": [item.module_id for item in self.resolved_modules],
                    "root_packages": {
                        "frontend": self.frontend_ir.module_id,
                        "knowledge_base": self.domain_ir.module_id,
                        "backend": self.backend_ir.module_id,
                    },
                    "package_results": {
                        module_id: result.to_dict()
                        for module_id, result in sorted(self.package_results.items())
                    },
                    "runtime_projection": {
                        "frontend_contract": self.frontend_contract,
                        "workbench_contract": self.workbench_contract,
                        "ui_spec": self.ui_spec,
                        "backend_spec": self.backend_spec,
                        "public_summary": self.public_summary,
                    },
                },
                "evidence": {
                    "validation_reports": self.validation_reports.to_dict(),
                    "document_digests": {
                        item.document_id: _sha256_text(item.body_markdown)
                        for item in self.documents
                    },
                    "generated_artifacts": generated_artifacts,
                    "derived_views": dict(self.derived_views),
                },
            },
        }


def _render_markdown(markdown: str) -> str:
    lines = markdown.strip().splitlines()
    html_parts: list[str] = []
    in_list = False
    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            continue
        if stripped.startswith("### "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append(f"<h4>{escape(stripped[4:])}</h4>")
            continue
        if stripped.startswith("## "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append(f"<h3>{escape(stripped[3:])}</h3>")
            continue
        if stripped.startswith("- "):
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            html_parts.append(f"<li>{escape(stripped[2:])}</li>")
            continue
        if in_list:
            html_parts.append("</ul>")
            in_list = False
        html_parts.append(f"<p>{escape(stripped)}</p>")
    if in_list:
        html_parts.append("</ul>")
    return "\n".join(html_parts)


def _plain_text(markdown: str) -> str:
    text = re.sub(r"^#{2,3}\s+", "", markdown, flags=re.MULTILINE)
    text = re.sub(r"^-\s+", "", text, flags=re.MULTILINE)
    return " ".join(part.strip() for part in text.splitlines() if part.strip())


def _split_markdown_sections(summary: str, body_markdown: str) -> tuple[KnowledgeDocumentSection, ...]:
    sections: list[KnowledgeDocumentSection] = [
        KnowledgeDocumentSection(
            section_id="summary",
            title="Summary",
            level=2,
            markdown=summary.strip(),
            html=_render_markdown(summary.strip()),
            plain_text=_plain_text(summary.strip()),
            search_text=f"summary {summary.strip()}",
        )
    ]
    seen_ids = {"summary"}
    current_title = "Overview"
    current_level = 2
    current_lines: list[str] = []
    saw_heading = False

    def flush() -> None:
        nonlocal current_title, current_level, current_lines
        content = "\n".join(current_lines).strip()
        if not content:
            current_lines = []
            return
        section_id = _slugify(current_title)
        counter = 2
        while section_id in seen_ids:
            section_id = f"{section_id}-{counter}"
            counter += 1
        seen_ids.add(section_id)
        plain_text = _plain_text(content)
        sections.append(
            KnowledgeDocumentSection(
                section_id=section_id,
                title=current_title,
                level=current_level,
                markdown=content,
                html=_render_markdown(content),
                plain_text=plain_text,
                search_text=f"{current_title} {plain_text}",
            )
        )
        current_lines = []

    for raw_line in body_markdown.strip().splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("## "):
            saw_heading = True
            flush()
            current_title = stripped[3:].strip()
            current_level = 2
            continue
        if stripped.startswith("### "):
            saw_heading = True
            flush()
            current_title = stripped[4:].strip()
            current_level = 3
            continue
        current_lines.append(raw_line)

    if not saw_heading and body_markdown.strip():
        current_title = "Overview"
        current_level = 2
    flush()
    return tuple(sections)


def _compile_document(source: SeedDocumentSource) -> KnowledgeDocument:
    sections = _split_markdown_sections(source.summary, source.body_markdown)
    body_html = "\n".join(
        f"<section id=\"{escape(item.section_id)}\" data-level=\"{item.level}\"><h3>{escape(item.title)}</h3>{item.html}</section>"
        for item in sections
    )
    return KnowledgeDocument(
        document_id=source.document_id,
        title=source.title,
        summary=source.summary,
        body_markdown=source.body_markdown,
        body_html=body_html,
        tags=source.tags,
        updated_at=source.updated_at,
        sections=sections,
    )


def compile_knowledge_document_source(source: SeedDocumentSource) -> KnowledgeDocument:
    return _compile_document(source)


def _require_documents(data: dict[str, Any]) -> tuple[SeedDocumentSource, ...]:
    value = data.get("documents")
    if not isinstance(value, list) or not value:
        raise ValueError("truth must define non-empty [[truth.documents]]")
    seen_ids: set[str] = set()
    items: list[SeedDocumentSource] = []
    for raw_document in value:
        if not isinstance(raw_document, dict):
            raise ValueError("each [[truth.documents]] entry must be a table")
        document = SeedDocumentSource(
            document_id=_require_string(raw_document, "document_id"),
            title=_require_string(raw_document, "title"),
            summary=_require_string(raw_document, "summary"),
            body_markdown=_require_string(raw_document, "body_markdown"),
            tags=_require_string_tuple(raw_document, "tags"),
            updated_at=_require_string(raw_document, "updated_at"),
        )
        if document.document_id in seen_ids:
            raise ValueError(f"duplicate document_id: {document.document_id}")
        seen_ids.add(document.document_id)
        items.append(document)
    return tuple(items)


def _load_project_config(project_file: Path) -> UnifiedProjectConfig:
    document: ComposedTomlDocument = load_project_config_document(project_file)
    raw = document.merged_data
    project_table = _require_table(raw, "project")
    selection_table = _require_table(raw, "selection")
    root_modules_table = _require_table(selection_table, "root_modules")
    truth_table = _require_table(raw, "truth")
    surface_table = _require_table(truth_table, "surface")
    surface_copy_table = _require_table(surface_table, "copy")
    visual_table = _require_table(truth_table, "visual")
    route_table = _require_table(truth_table, "route")
    showcase_page_table = _require_table(truth_table, "showcase_page")
    a11y_table = _require_table(truth_table, "a11y")
    library_table = _require_table(truth_table, "library")
    library_copy_table = _require_table(library_table, "copy")
    preview_table = _require_table(truth_table, "preview")
    chat_table = _require_table(truth_table, "chat")
    chat_copy_table = _require_table(chat_table, "copy")
    context_table = _require_table(truth_table, "context")
    return_table = _require_table(truth_table, "return")
    refinement_table = _require_table(raw, "refinement")
    frontend_table = _require_table(refinement_table, "frontend")
    backend_table = _require_table(refinement_table, "backend")
    evidence_table = _require_table(refinement_table, "evidence")
    artifacts_table = _require_table(refinement_table, "artifacts")

    library_enabled = _require_bool(library_table, "enabled")
    preview_enabled = _require_bool(preview_table, "enabled")
    chat_enabled = _require_bool(chat_table, "enabled")
    citations_enabled = _require_bool(chat_table, "citations_enabled")
    return_enabled = _require_bool(return_table, "enabled")
    allow_create = _require_bool(library_table, "allow_create")
    allow_delete = _require_bool(library_table, "allow_delete")

    return UnifiedProjectConfig(
        project_file=_relative_path(project_file),
        section_sources={
            section_name: _relative_path(document.source_file_for_section(section_name))
            for section_name in raw
        },
        metadata=ProjectMetadata(
            project_id=_require_string(project_table, "project_id"),
            runtime_scene=_require_string(project_table, "runtime_scene"),
            display_name=_require_string(project_table, "display_name"),
            description=_require_string(project_table, "description"),
            version=_require_string(project_table, "version"),
        ),
        selection=ModuleSelection(
            preset=_require_string(selection_table, "preset"),
            root_modules=RootModuleSelection(
                frontend=_require_string(root_modules_table, "frontend"),
                knowledge_base=_require_string(root_modules_table, "knowledge_base"),
                backend=_require_string(root_modules_table, "backend"),
            ),
        ),
        surface=SurfaceConfig(
            shell=_require_string(surface_table, "shell"),
            layout_variant=_require_string(surface_table, "layout_variant"),
            sidebar_width=_require_string(surface_table, "sidebar_width"),
            preview_mode=_require_string(surface_table, "preview_mode"),
            density=_require_string(surface_table, "density"),
            copy=SurfaceCopyConfig(
                hero_kicker=_require_string(surface_copy_table, "hero_kicker"),
                hero_title=_require_string(surface_copy_table, "hero_title"),
                hero_copy=_require_string(surface_copy_table, "hero_copy"),
                library_title=_require_string(surface_copy_table, "library_title"),
                preview_title=_require_string(surface_copy_table, "preview_title"),
                toc_title=_require_string(surface_copy_table, "toc_title"),
                chat_title=_require_string(surface_copy_table, "chat_title"),
                empty_state_title=_require_string(surface_copy_table, "empty_state_title"),
                empty_state_copy=_require_string(surface_copy_table, "empty_state_copy"),
            ),
        ),
        visual=VisualConfig(
            brand=_require_string(visual_table, "brand"),
            accent=_require_string(visual_table, "accent"),
            surface_preset=_require_string(visual_table, "surface_preset"),
            radius_scale=_require_string(visual_table, "radius_scale"),
            shadow_level=_require_string(visual_table, "shadow_level"),
            font_scale=_require_string(visual_table, "font_scale"),
        ),
        features=FeatureConfig(
            library=library_enabled,
            preview=preview_enabled,
            chat=chat_enabled,
            citation=citations_enabled,
            return_to_anchor=return_enabled,
            upload=allow_create or allow_delete,
        ),
        route=RouteConfig(
            home=_require_string(route_table, "home"),
            workbench=_require_string(route_table, "workbench"),
            basketball_showcase=_require_string(route_table, "basketball_showcase"),
            knowledge_list=_require_string(route_table, "knowledge_list"),
            knowledge_detail=_require_string(route_table, "knowledge_detail"),
            document_detail_prefix=_require_string(route_table, "document_detail_prefix"),
            api_prefix=_require_string(route_table, "api_prefix"),
        ),
        showcase_page=ShowcasePageConfig(
            title=_require_string(showcase_page_table, "title"),
            kicker=_require_string(showcase_page_table, "kicker"),
            headline=_require_string(showcase_page_table, "headline"),
            intro=_require_string(showcase_page_table, "intro"),
            back_to_chat_label=_require_string(showcase_page_table, "back_to_chat_label"),
            browse_knowledge_label=_require_string(showcase_page_table, "browse_knowledge_label"),
        ),
        a11y=A11yConfig(
            reading_order=_require_string_tuple(a11y_table, "reading_order"),
            keyboard_nav=_require_string_tuple(a11y_table, "keyboard_nav"),
            announcements=_require_string_tuple(a11y_table, "announcements"),
        ),
        library=LibraryConfig(
            knowledge_base_id=_require_string(library_table, "knowledge_base_id"),
            knowledge_base_name=_require_string(library_table, "knowledge_base_name"),
            knowledge_base_description=_require_string(library_table, "knowledge_base_description"),
            enabled=library_enabled,
            source_types=_require_string_tuple(library_table, "source_types"),
            metadata_fields=_require_string_tuple(library_table, "metadata_fields"),
            default_focus=_require_string(library_table, "default_focus"),
            list_variant=_require_string(library_table, "list_variant"),
            allow_create=allow_create,
            allow_delete=allow_delete,
            search_placeholder=_require_string(library_copy_table, "search_placeholder"),
        ),
        preview=PreviewConfig(
            enabled=preview_enabled,
            renderers=_require_string_tuple(preview_table, "renderers"),
            anchor_mode=_require_string(preview_table, "anchor_mode"),
            show_toc=_require_bool(preview_table, "show_toc"),
            preview_variant=_require_string(preview_table, "preview_variant"),
        ),
        chat=ChatConfig(
            enabled=chat_enabled,
            citations_enabled=citations_enabled,
            mode=_require_string(chat_table, "mode"),
            citation_style=_require_string(chat_table, "citation_style"),
            bubble_variant=_require_string(chat_table, "bubble_variant"),
            composer_variant=_require_string(chat_table, "composer_variant"),
            system_prompt=_require_string(chat_table, "system_prompt"),
            placeholder=_require_string(chat_copy_table, "placeholder"),
            welcome=_require_string(chat_copy_table, "welcome"),
            welcome_prompts=_require_string_tuple(chat_table, "welcome_prompts"),
        ),
        context=ContextConfig(
            selection_mode=_require_string(context_table, "selection_mode"),
            max_citations=_require_int(context_table, "max_citations"),
            max_preview_sections=_require_int(context_table, "max_preview_sections"),
            sticky_document=_require_bool(context_table, "sticky_document"),
        ),
        return_config=ReturnConfig(
            enabled=return_enabled,
            targets=_require_string_tuple(return_table, "targets"),
            anchor_restore=_require_bool(return_table, "anchor_restore"),
            citation_card_variant=_require_string(return_table, "citation_card_variant"),
        ),
        documents=_require_documents(truth_table),
        refinement=RefinementConfig(
            frontend=FrontendRefinementConfig(
                renderer=_require_string(frontend_table, "renderer"),
                style_profile=_require_string(frontend_table, "style_profile"),
                script_profile=_require_string(frontend_table, "script_profile"),
            ),
            backend=BackendRefinementConfig(
                renderer=_require_string(backend_table, "renderer"),
                transport=_require_string(backend_table, "transport"),
                retrieval_strategy=_require_string(backend_table, "retrieval_strategy"),
            ),
            evidence=EvidenceRefinementConfig(
                project_config_endpoint=_require_string(evidence_table, "project_config_endpoint"),
            ),
            artifacts=ArtifactConfig(
                canonical_graph_json=_require_string(artifacts_table, "canonical_graph_json"),
                runtime_bundle_py=_require_string(artifacts_table, "runtime_bundle_py"),
                generation_manifest_json=_require_string(artifacts_table, "generation_manifest_json"),
                governance_manifest_json=_require_string(artifacts_table, "governance_manifest_json"),
                governance_tree_json=_require_string(artifacts_table, "governance_tree_json"),
                strict_zone_report_json=_require_string(artifacts_table, "strict_zone_report_json"),
                object_coverage_report_json=_require_string(artifacts_table, "object_coverage_report_json"),
            ),
        ),
        narrative=_optional_table(raw, "narrative"),
    )


def _resolve_framework_module(registry: FrameworkRegistry, ref: str) -> FrameworkModule:
    for module in registry.modules:
        if module.path == ref:
            return module
    raise ValueError(f"framework ref does not exist: {ref}")


def _collect_framework_closure(registry: FrameworkRegistry, *roots: FrameworkModule) -> tuple[FrameworkModule, ...]:
    ordered: list[FrameworkModule] = []
    seen: set[str] = set()

    def visit(module: FrameworkModule) -> None:
        if module.module_id in seen:
            return
        seen.add(module.module_id)
        for base in module.bases:
            for ref in base.upstream_refs:
                visit(registry.get_module(ref.framework, ref.level, ref.module))
        ordered.append(module)

    for root in roots:
        visit(root)
    return tuple(ordered)


def _build_visual_tokens(visual: VisualConfig, surface: SurfaceConfig, preview: PreviewConfig) -> dict[str, str]:
    scene_contract = load_knowledge_base_template_contract()
    return scene_contract.style_profiles.resolve_visual_tokens(
        surface_preset=visual.surface_preset,
        radius_scale=visual.radius_scale,
        shadow_level=visual.shadow_level,
        font_scale=visual.font_scale,
        sidebar_width=surface.sidebar_width,
        density=surface.density,
        accent=visual.accent,
        brand=visual.brand,
        preview_mode=surface.preview_mode,
        preview_variant=preview.preview_variant,
    )


def _pick_boundary_name(module: FrameworkModule, boundary_id: str, fallback: str) -> str:
    for item in module.boundaries:
        if item.boundary_id == boundary_id:
            return item.name
    return fallback


def _derive_copy(
    config: UnifiedProjectConfig,
    frontend_ir: FrameworkModule,
    domain_ir: FrameworkModule,
    backend_ir: FrameworkModule,
) -> dict[str, str]:
    hero_copy = " ".join(
        [
            frontend_ir.capabilities[0].statement if frontend_ir.capabilities else "",
            domain_ir.capabilities[0].statement if domain_ir.capabilities else "",
            backend_ir.capabilities[0].statement if backend_ir.capabilities else "",
        ]
    ).strip()
    base_labels = " / ".join(item.name for item in domain_ir.bases)
    boundary_labels = ", ".join(item.boundary_id for item in domain_ir.boundaries)
    surface_copy = config.surface.copy
    return {
        "hero_kicker": surface_copy.hero_kicker or config.visual.brand,
        "hero_title": surface_copy.hero_title or config.metadata.display_name,
        "hero_copy": surface_copy.hero_copy or hero_copy,
        "mode_label": "知识问答",
        "knowledge_base_name": config.library.knowledge_base_name,
        "knowledge_base_description": config.library.knowledge_base_description,
        "contract_title": "Framework Contract",
        "contract_value": base_labels,
        "contract_meta": f"Boundaries: {boundary_labels}",
        "library_title": surface_copy.library_title or _pick_boundary_name(domain_ir, "LIBRARY", "Library"),
        "preview_title": surface_copy.preview_title or _pick_boundary_name(domain_ir, "PREVIEW", "Preview"),
        "toc_title": surface_copy.toc_title or "TOC",
        "chat_title": surface_copy.chat_title or _pick_boundary_name(domain_ir, "CHAT", "Chat"),
        "search_placeholder": config.library.search_placeholder,
        "chat_placeholder": config.chat.placeholder,
        "chat_welcome": config.chat.welcome,
        "empty_state_title": surface_copy.empty_state_title,
        "empty_state_copy": surface_copy.empty_state_copy,
    }


def _validate_project_config(
    config: UnifiedProjectConfig,
    frontend_ir: FrameworkModule,
    domain_ir: FrameworkModule,
    backend_ir: FrameworkModule,
    scene_contract: KnowledgeBaseTemplateContract,
) -> None:
    if config.metadata.runtime_scene != KNOWLEDGE_BASE_RUNTIME_SCENE:
        raise ValueError(f"unsupported runtime_scene: {config.metadata.runtime_scene}")
    if config.surface.shell != scene_contract.required_surface_shell:
        raise ValueError(f"truth.surface.shell must be {scene_contract.required_surface_shell}")
    if config.surface.layout_variant != scene_contract.required_layout_variant:
        raise ValueError(f"truth.surface.layout_variant must be {scene_contract.required_layout_variant}")
    if config.surface.preview_mode != scene_contract.required_preview_mode:
        raise ValueError(f"truth.surface.preview_mode must be {scene_contract.required_preview_mode}")
    if not all(
        (
            config.library.enabled,
            config.preview.enabled,
            config.chat.enabled,
            config.chat.citations_enabled,
            config.return_config.enabled,
        )
    ):
        raise ValueError("knowledge_base_workbench requires library, preview, chat, citations, and return")
    if not config.route.home.startswith("/") or not config.route.workbench.startswith("/"):
        raise ValueError("truth.route.home and truth.route.workbench must start with '/'")
    if not config.route.api_prefix.startswith("/api"):
        raise ValueError("truth.route.api_prefix must start with '/api'")
    if not config.route.knowledge_detail.startswith(config.route.knowledge_list):
        raise ValueError("truth.route.knowledge_detail must stay under truth.route.knowledge_list")
    if not config.route.document_detail_prefix.startswith(config.route.knowledge_detail):
        raise ValueError("truth.route.document_detail_prefix must stay under truth.route.knowledge_detail")
    if not config.route.basketball_showcase.startswith(config.route.workbench):
        raise ValueError("truth.route.basketball_showcase must stay under truth.route.workbench")
    if config.library.default_focus != scene_contract.required_library_default_focus:
        raise ValueError(f"truth.library.default_focus must be {scene_contract.required_library_default_focus}")
    if config.preview.anchor_mode != scene_contract.required_preview_anchor_mode:
        raise ValueError(f"truth.preview.anchor_mode must be {scene_contract.required_preview_anchor_mode}")
    if config.preview.preview_variant != scene_contract.required_preview_variant:
        raise ValueError(f"truth.preview.preview_variant must be {scene_contract.required_preview_variant}")
    if config.chat.mode != scene_contract.required_chat_mode:
        raise ValueError(f"truth.chat.mode must be {scene_contract.required_chat_mode}")
    if config.chat.citation_style != scene_contract.required_chat_citation_style:
        raise ValueError(f"truth.chat.citation_style must be {scene_contract.required_chat_citation_style}")
    if tuple(config.a11y.reading_order) != scene_contract.required_reading_order:
        raise ValueError("truth.a11y.reading_order does not match scene contract")
    missing_return_targets = scene_contract.required_return_target_set() - set(config.return_config.targets)
    if missing_return_targets:
        raise ValueError(f"truth.return.targets missing required values: {', '.join(sorted(missing_return_targets))}")
    if config.refinement.frontend.renderer not in scene_contract.supported_frontend_renderers:
        raise ValueError(f"unsupported refinement.frontend.renderer: {config.refinement.frontend.renderer}")
    if config.refinement.frontend.style_profile not in scene_contract.supported_frontend_style_profiles:
        raise ValueError(f"unsupported refinement.frontend.style_profile: {config.refinement.frontend.style_profile}")
    if config.refinement.frontend.script_profile not in scene_contract.supported_frontend_script_profiles:
        raise ValueError(f"unsupported refinement.frontend.script_profile: {config.refinement.frontend.script_profile}")
    if config.refinement.backend.renderer not in scene_contract.supported_backend_renderers:
        raise ValueError(f"unsupported refinement.backend.renderer: {config.refinement.backend.renderer}")
    if config.refinement.backend.transport not in scene_contract.supported_backend_transports:
        raise ValueError(f"unsupported refinement.backend.transport: {config.refinement.backend.transport}")
    if config.refinement.backend.retrieval_strategy not in scene_contract.supported_backend_retrieval_strategies:
        raise ValueError(
            f"unsupported refinement.backend.retrieval_strategy: {config.refinement.backend.retrieval_strategy}"
        )
    if config.refinement.backend.retrieval_strategy != config.chat.mode:
        raise ValueError("refinement.backend.retrieval_strategy must match truth.chat.mode")
    if not config.refinement.evidence.project_config_endpoint.startswith(config.route.api_prefix):
        raise ValueError("refinement.evidence.project_config_endpoint must stay under truth.route.api_prefix")
    if not frontend_ir.bases or not domain_ir.bases or not backend_ir.bases:
        raise ValueError("selected framework modules must define bases")
    for document in config.documents:
        if len(_tokenize(document.summary)) < 3:
            raise ValueError(f"document summary is too short for retrieval: {document.document_id}")
        if "## " not in document.body_markdown:
            raise ValueError(f"document body must contain level-2 headings: {document.document_id}")


def _config_slice(root_payload: dict[str, Any], result: PackageCompileResult | None, *, entry: Any) -> dict[str, Any]:
    contract = entry.config_contract()
    resolved: dict[str, Any] = {}
    for dotted_path in contract.required_paths:
        try:
            resolved[dotted_path] = _jsonable(_lookup_dotted_path(root_payload, dotted_path))
        except KeyError as exc:
            raise ValueError(f"missing required config path for {entry.module_id()}: {dotted_path}") from exc
    for dotted_path in contract.optional_paths:
        try:
            resolved[dotted_path] = _jsonable(_lookup_dotted_path(root_payload, dotted_path))
        except KeyError:
            continue
    return resolved


def _compile_package_results(
    config: UnifiedProjectConfig,
    package_registry: FrameworkPackageRegistry,
    resolved_modules: tuple[FrameworkModule, ...],
) -> dict[str, PackageCompileResult]:
    root_payload = config.root_payload()
    results: dict[str, PackageCompileResult] = {}
    for module in resolved_modules:
        registration = package_registry.get_by_module_id(module.module_id)
        entry = registration.entry_class()
        child_slots = entry.child_slots(module)
        child_exports: dict[str, dict[str, Any]] = {}
        for slot in child_slots:
            child_result = results.get(slot.child_module_id)
            if child_result is None and slot.required:
                raise ValueError(f"missing compiled child package: {slot.child_module_id}")
            if child_result is not None:
                child_exports[slot.child_module_id] = child_result.export
        config_slice = _config_slice(root_payload, None, entry=entry)
        compiled = entry.compile(
            PackageCompileInput(
                framework_module=module,
                config_slice=config_slice,
                child_exports=child_exports,
            )
        )
        results[module.module_id] = compiled
    return results


def _ui_derived_from(project: KnowledgeBaseProject) -> dict[str, Any]:
    return {
        "framework_modules": {
            "frontend": project.frontend_ir.module_id,
            "knowledge_base": project.domain_ir.module_id,
        },
        "selection": project.selection.to_dict(),
        "registry_binding": {
            module_id: project.package_results[module_id].entry_class
            for module_id in (project.frontend_ir.module_id, project.domain_ir.module_id)
        },
    }


def _ui_pages(project: KnowledgeBaseProject, paths: UiSpecPaths, contract: KnowledgeBaseTemplateContract) -> dict[str, Any]:
    return {
        "chat_home": {
            "path": project.route.workbench,
            "title": project.metadata.display_name,
            "slots": list(contract.chat_home_slots),
            "entry_state": "welcome_prompts",
        },
        "basketball_showcase": {
            "path": paths.basketball_showcase_path,
            "title": project.showcase_page.title,
            "kicker": project.showcase_page.kicker,
            "headline": project.showcase_page.headline,
            "intro": project.showcase_page.intro,
            "back_to_chat_label": project.showcase_page.back_to_chat_label,
            "browse_knowledge_label": project.showcase_page.browse_knowledge_label,
            "slots": ["aux_sidebar", "page_header", "showcase_stage"],
        },
        "knowledge_list": {
            "path": project.route.knowledge_list,
            "title": project.surface.copy.library_title,
            "subtitle": "聊天是主入口，知识库页用于切换上下文和确认可用来源。",
            "primary_action_label": "返回聊天",
            "rationale_title": "为什么这页是二级入口",
            "rationale_copy": (
                "主界面保持 ChatGPT 风格：左侧历史会话，中央聊天区，底部输入框。"
                "知识库管理和文档浏览退到二级页面，只在需要验证来源时展开。"
            ),
            "chat_action_label": "用此知识库开始聊天",
            "detail_action_label": "查看知识库详情",
            "slots": ["aux_sidebar", "page_header", "knowledge_cards"],
        },
        "knowledge_detail": {
            "path": paths.knowledge_base_detail_path,
            "chat_action_label": "用此知识库开始聊天",
            "overview_title": "知识库概况",
            "return_chat_with_document_label": "回到聊天并聚焦此文档",
            "document_detail_action_label": "查看文档详情",
            "slots": ["aux_sidebar", "page_header", "document_cards"],
        },
        "document_detail": {
            "path": paths.document_detail_path,
            "title": "文档详情",
            "subtitle": "从引用抽屉进入完整文档上下文，再返回聊天继续提问。",
            "return_chat_label": "返回聊天",
            "return_knowledge_detail_label": "返回知识库详情",
            "slots": ["aux_sidebar", "page_header", "document_sections"],
        },
    }


def _ui_components(project: KnowledgeBaseProject, contract: KnowledgeBaseTemplateContract) -> dict[str, Any]:
    return {
        "conversation_sidebar": {
            "title": "历史会话",
            "actions": ["start_new_chat", "select_session", "open_knowledge_switch"],
            "new_chat_label": "新建聊天",
            "browse_knowledge_label": "浏览知识库与文档",
            "basketball_showcase_label": project.showcase_page.title,
            "knowledge_entry_label": f"知识库 · {project.library.knowledge_base_name}",
        },
        "aux_sidebar": {
            "nav": {
                "chat": "返回聊天",
                "basketball_showcase": project.showcase_page.title,
                "knowledge_list": "知识库列表",
                "knowledge_detail": "当前知识库详情",
            },
            "note": "辅助页面负责知识库浏览、来源验证与文档追溯，不抢占聊天主舞台。",
        },
        "chat_header": {
            "title_source": "conversation.title",
            "subtitle_template": "知识库 · {knowledge_base_name}",
            "knowledge_badge_template": "基于：{knowledge_base_name}",
            "knowledge_entry_link_label": "知识库入口",
            "showcase_link_label": project.showcase_page.title,
        },
        "message_stream": {
            "max_width": project.visual_tokens["message_width"],
            "roles": ["user", "assistant"],
            "role_labels": {"user": "You", "assistant": "Assistant"},
            "assistant_actions": ["copy_answer"],
            "copy_action_label": "复制回答",
            "copy_failure_message": "复制失败，请手动复制。",
            "loading_label": "正在检索知识库并整理回答…",
            "summary_template": "参考了 {count} 个来源",
            "citation_style": project.chat.citation_style,
        },
        "chat_composer": {
            "placeholder": project.chat.placeholder,
            "submit_label": "发送",
            "context_template": "当前上下文：{context_label}",
            "citation_hint": "引用默认轻量展示，点击后打开来源抽屉",
            "mode_label": "知识问答",
            "knowledge_link_label": "查看知识库",
            "showcase_link_label": project.showcase_page.title,
        },
        "citation_drawer": {
            "title": project.copy["preview_title"],
            "close_aria_label": "Close citation drawer",
            "tab_variant": "numbered",
            "sections": list(contract.drawer_sections),
            "section_label": "章节",
            "snippet_title": "命中片段",
            "source_context_title": "来源上下文",
            "empty_context_text": "暂无来源上下文。",
            "load_failure_text": "无法加载来源片段。",
            "document_link_label": "打开文档详情",
            "return_targets": list(project.return_config.targets),
        },
        "knowledge_switch_dialog": {
            "title": "切换知识库",
            "description": "默认保持 ChatGPT 风格聊天界面，知识库切换只在需要时展开。",
            "close_aria_label": "Close knowledge dialog",
            "select_action_label": "使用此知识库",
            "detail_action_label": "查看详情",
            "card_actions": ["select", "open_knowledge_detail"],
        },
    }


def _ui_conversation(project: KnowledgeBaseProject) -> dict[str, Any]:
    return {
        "default_title": "新建聊天",
        "relative_groups": {
            "today": "今天",
            "last_7_days": "7 天内",
            "last_30_days": "30 天内",
            "older": "更早",
        },
        "welcome_kicker": project.surface.copy.chat_title,
        "welcome_title": "今天想了解什么？",
        "welcome_copy": project.chat.welcome,
        "welcome_prompts": list(project.chat.welcome_prompts),
        "current_knowledge_base_template": "当前知识库：{knowledge_base_name}",
    }


def _ui_citation(project: KnowledgeBaseProject, paths: UiSpecPaths, contract: KnowledgeBaseTemplateContract) -> dict[str, Any]:
    return {
        "style": project.chat.citation_style,
        "summary_variant": project.return_config.citation_card_variant,
        "drawer_sections": list(contract.drawer_sections),
        "document_detail_path": paths.document_detail_path,
    }


def _build_ui_spec(project: KnowledgeBaseProject) -> dict[str, Any]:
    contract = project.template_contract
    paths = UiSpecPaths.from_project(project)
    return {
        "derived_from": _ui_derived_from(project),
        "implementation": {
            "frontend_renderer": project.refinement.frontend.renderer,
            "style_profile": project.refinement.frontend.style_profile,
            "script_profile": project.refinement.frontend.script_profile,
        },
        "shell": {
            "id": project.surface.shell,
            "layout_variant": project.surface.layout_variant,
            "regions": list(contract.shell_regions),
            "secondary_pages": list(contract.secondary_pages),
            "default_page": "chat_home",
            "preview_mode": project.surface.preview_mode,
            "density": project.surface.density,
        },
        "visual": {
            "theme": project.visual.to_dict(),
            "tokens": project.visual_tokens,
        },
        "pages": _ui_pages(project, paths, contract),
        "components": _ui_components(project, contract),
        "conversation": _ui_conversation(project),
        "citation": _ui_citation(project, paths, contract),
    }


def _backend_derived_from(project: KnowledgeBaseProject) -> dict[str, Any]:
    return {
        "framework_modules": {
            "knowledge_base": project.domain_ir.module_id,
            "backend": project.backend_ir.module_id,
        },
        "selection": project.selection.to_dict(),
        "registry_binding": {
            module_id: project.package_results[module_id].entry_class
            for module_id in (project.domain_ir.module_id, project.backend_ir.module_id)
        },
    }


def _backend_answer_policy(project: KnowledgeBaseProject) -> dict[str, Any]:
    return {
        "citation_style": project.chat.citation_style,
        "no_match_text": (
            "当前知识库里没有找到足够相关的证据。你可以换一种问法，或者先浏览知识库与文档详情页确认可用来源。"
        ),
        "lead_template": "根据当前知识库，最相关的证据来自《{document_title}》的“{section_title}”。[{citation_index}]",
        "lead_snippet_template": "该片段指出：{snippet}",
        "followup_template": "补充来源还包括《{document_title}》的“{section_title}”。[{citation_index}] {snippet}",
        "closing_text": "点击文中引用可打开来源抽屉，并继续进入文档详情页查看完整上下文。",
    }


def _backend_return_policy(project: KnowledgeBaseProject, paths: UiSpecPaths) -> dict[str, Any]:
    return {
        "targets": list(project.return_config.targets),
        "anchor_restore": project.return_config.anchor_restore,
        "chat_path": project.route.workbench,
        "knowledge_base_detail_path": paths.knowledge_base_detail_path,
        "document_detail_path": paths.document_detail_path,
    }


def _build_backend_spec(project: KnowledgeBaseProject) -> dict[str, Any]:
    contract = project.template_contract
    paths = UiSpecPaths.from_project(project)
    return {
        "derived_from": _backend_derived_from(project),
        "implementation": {
            "backend_renderer": project.refinement.backend.renderer,
        },
        "knowledge_base": {
            "knowledge_base_id": project.library.knowledge_base_id,
            "knowledge_base_name": project.library.knowledge_base_name,
            "knowledge_base_description": project.library.knowledge_base_description,
            "source_types": list(project.library.source_types),
            "metadata_fields": list(project.library.metadata_fields),
        },
        "transport": {
            "mode": project.refinement.backend.transport,
            "api_prefix": project.route.api_prefix,
            "project_config_endpoint": project.refinement.evidence.project_config_endpoint,
        },
        "retrieval": {
            "strategy": project.refinement.backend.retrieval_strategy,
            "query_token_min_length": 3,
            "focus_section_bonus": 4,
            "token_match_bonus": 3,
            "max_preview_sections": project.context.max_preview_sections,
            "max_citations": project.context.max_citations,
            "selection_mode": project.context.selection_mode,
        },
        "interaction_flow": list(contract.workbench_flow_dicts()),
        "answer_policy": _backend_answer_policy(project),
        "interaction_copy": {
            "loading_text": "正在检索知识库并整理回答…",
            "error_text": "回答生成失败。你可以重新提问，或稍后再试。",
        },
        "return_policy": _backend_return_policy(project, paths),
        "write_policy": {
            "allow_create": project.library.allow_create,
            "allow_delete": project.library.allow_delete,
        },
    }


def _collect_validation_reports(project: KnowledgeBaseProject) -> ValidationReports:
    from frontend_kernel import summarize_frontend_rules, validate_frontend_rules
    from knowledge_base_framework import summarize_workbench_rules, validate_workbench_rules

    frontend_results = validate_frontend_rules(project)
    workbench_results = validate_workbench_rules(project)
    return ValidationReports(
        frontend=summarize_frontend_rules(frontend_results),
        knowledge_base=summarize_workbench_rules(workbench_results),
    )


def _raise_on_validation_failures(reports: ValidationReports) -> None:
    errors: list[str] = []
    for scope, report in (("frontend", reports.frontend), ("knowledge_base", reports.knowledge_base)):
        if report is None:
            continue
        for item in report.rules:
            if item.passed:
                continue
            reasons = ", ".join(item.reasons) or "unknown rule failure"
            errors.append(f"{scope}.{item.rule_id}: {reasons}")
    if errors:
        raise ValueError("framework rule validation failed: " + " | ".join(errors))


def _build_project_config_view(project: KnowledgeBaseProject) -> dict[str, Any]:
    return {
        "project": project.metadata.to_dict(),
        "selection": project.selection.to_dict(),
        "truth": project.config.truth_payload(),
        "refinement": project.refinement.to_dict(),
        "narrative": _jsonable(project.config.narrative),
        "interaction_model": {
            "workspace_flow": project.workbench_contract.get("flow", []),
            "citation_return": project.workbench_contract.get("citation_return_contract", {}),
            "surface_regions": project.frontend_contract.get("surface_regions", []),
            "interaction_actions": project.frontend_contract.get("interaction_actions", []),
        },
    }


def _build_public_summary(project: KnowledgeBaseProject) -> dict[str, Any]:
    return {
        "project_file": project.project_file,
        "project": project.metadata.to_dict(),
        "selection": project.selection.to_dict(),
        "route": project.route.to_dict(),
        "a11y": project.a11y.to_dict(),
        "routes": {
            **project.route.to_dict(),
            "pages": project._resolved_page_routes(),
            "api": project._resolved_api_routes(),
        },
        "document_count": len(project.documents),
        "resolved_module_ids": [item.module_id for item in project.resolved_modules],
        "package_compile_order": [item.module_id for item in project.resolved_modules],
        "ui_spec_summary": {
            "page_ids": list(project.ui_spec.get("pages", {}).keys()),
            "component_ids": list(project.ui_spec.get("components", {}).keys()),
        },
        "backend_spec_summary": {
            "retrieval": project.backend_spec.get("retrieval", {}),
            "answer_policy": {
                "citation_style": project.backend_spec.get("answer_policy", {}).get("citation_style"),
            },
        },
        "validation_reports": project.validation_reports.to_dict(),
        "generated_artifacts": project.generated_artifacts.to_dict() if project.generated_artifacts else None,
    }


def _effective_generated_artifacts(project: KnowledgeBaseProject) -> GeneratedArtifactPaths:
    if project.generated_artifacts is not None:
        return project.generated_artifacts
    project_path = _normalize_project_path(project.project_file)
    return GeneratedArtifactPaths.from_artifact_config(
        project.refinement.artifacts,
        directory=project_path.parent / "generated",
        path_renderer=_relative_path,
    )


def _build_runtime_bundle_text(project: KnowledgeBaseProject, canonical_graph: dict[str, Any]) -> str:
    runtime_bundle = project.to_runtime_bundle_dict()
    return "\n".join(
        [
            "from __future__ import annotations",
            "",
            "# GENERATED FILE. DO NOT EDIT.",
            "# Change framework markdown or projects/*/project.toml, then re-materialize.",
            "",
            "import json",
            "",
            f"CANONICAL_GRAPH = json.loads(r'''{json.dumps(canonical_graph, ensure_ascii=False)}''')",
            f"RUNTIME_BUNDLE = json.loads(r'''{json.dumps(runtime_bundle, ensure_ascii=False)}''')",
            "PROJECT_CONFIG = RUNTIME_BUNDLE['project_config']",
            "",
        ]
    )


def _compile_project(config: UnifiedProjectConfig) -> KnowledgeBaseProject:
    from frontend_kernel import build_frontend_contract
    from knowledge_base_framework import build_workbench_contract

    scene_contract = load_knowledge_base_template_contract()
    framework_registry = load_framework_registry()
    package_registry = load_builtin_package_registry()
    package_registry.validate_against_framework(framework_registry)

    frontend_ir = _resolve_framework_module(framework_registry, config.selection.root_modules.frontend)
    domain_ir = _resolve_framework_module(framework_registry, config.selection.root_modules.knowledge_base)
    backend_ir = _resolve_framework_module(framework_registry, config.selection.root_modules.backend)
    _validate_project_config(config, frontend_ir, domain_ir, backend_ir, scene_contract)

    resolved_modules = _collect_framework_closure(framework_registry, frontend_ir, domain_ir, backend_ir)
    package_results = _compile_package_results(config, package_registry, resolved_modules)
    documents = tuple(_compile_document(item) for item in config.documents)
    project = KnowledgeBaseProject(
        project_file=config.project_file,
        config=config,
        scene_contract=scene_contract,
        package_registry=package_registry,
        frontend_ir=frontend_ir,
        domain_ir=domain_ir,
        backend_ir=backend_ir,
        resolved_modules=resolved_modules,
        package_results=package_results,
        visual_tokens=_build_visual_tokens(config.visual, config.surface, config.preview),
        documents=documents,
        derived_copy=_derive_copy(config, frontend_ir, domain_ir, backend_ir),
        frontend_contract={},
        workbench_contract={},
        ui_spec={},
        backend_spec={},
        validation_reports=ValidationReports.empty(),
    )
    backend_spec = _build_backend_spec(project)
    project = replace(project, backend_spec=backend_spec)
    frontend_contract = build_frontend_contract(project)
    project = replace(project, frontend_contract=frontend_contract)
    workbench_contract = build_workbench_contract(project)
    project = replace(project, workbench_contract=workbench_contract)
    ui_spec = _build_ui_spec(project)
    project = replace(project, ui_spec=ui_spec)
    validation_reports = _collect_validation_reports(project)
    _raise_on_validation_failures(validation_reports)
    return replace(project, validation_reports=validation_reports)


def load_knowledge_base_project(
    project_file: str | Path = DEFAULT_KNOWLEDGE_BASE_PROJECT_FILE,
) -> KnowledgeBaseProject:
    project_path = _normalize_project_path(project_file)
    return _compile_project(_load_project_config(project_path))


def materialize_knowledge_base_project(
    project_file: str | Path = DEFAULT_KNOWLEDGE_BASE_PROJECT_FILE,
    output_dir: str | Path | None = None,
) -> KnowledgeBaseProject:
    project_path = _normalize_project_path(project_file)
    project = load_knowledge_base_project(project_path)
    generated_dir = project_path.parent / "generated"
    output_path = _normalize_project_path(output_dir) if output_dir is not None else generated_dir
    output_path.mkdir(parents=True, exist_ok=True)

    artifact_names = project.refinement.artifacts
    expected_file_names = set(artifact_names.file_names())
    _cleanup_generated_output_dir(output_path, expected_file_names)
    output_paths = GeneratedArtifactOutputPaths.from_artifact_config(artifact_names, output_dir=output_path)
    generated_artifacts = GeneratedArtifactPaths.from_artifact_config(
        artifact_names,
        directory=generated_dir,
        path_renderer=_relative_path,
    )
    project = replace(project, generated_artifacts=generated_artifacts)
    derived_view_payloads = build_derived_view_payloads(
        project.to_canonical_graph_dict(),
        generated_artifacts=generated_artifacts.to_dict(),
    )
    project = replace(
        project,
        derived_views=derived_view_payloads.generation_manifest["derived_views"],
    )
    canonical_graph = project.to_canonical_graph_dict()
    runtime_bundle_text = _build_runtime_bundle_text(project, canonical_graph)

    output_paths.canonical_graph_json.write_text(json.dumps(canonical_graph, ensure_ascii=False, indent=2), encoding="utf-8")
    output_paths.runtime_bundle_py.write_text(runtime_bundle_text, encoding="utf-8")
    output_paths.generation_manifest_json.write_text(
        json.dumps(derived_view_payloads.generation_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    output_paths.governance_manifest_json.write_text(
        json.dumps(derived_view_payloads.governance_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    output_paths.governance_tree_json.write_text(
        json.dumps(derived_view_payloads.governance_tree, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    output_paths.strict_zone_report_json.write_text(
        json.dumps(derived_view_payloads.strict_zone_report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    output_paths.object_coverage_report_json.write_text(
        json.dumps(derived_view_payloads.object_coverage_report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return project


def build_knowledge_base_runtime_app_from_spec(
    project_file: str | Path = DEFAULT_KNOWLEDGE_BASE_PROJECT_FILE,
) -> Any:
    from knowledge_base_runtime.app import build_knowledge_base_runtime_app

    return build_knowledge_base_runtime_app(materialize_knowledge_base_project(project_file))


__all__ = [
    "DEFAULT_KNOWLEDGE_BASE_PROJECT_FILE",
    "DEFAULT_KNOWLEDGE_BASE_PROJECT_FILE",
    "ArtifactConfig",
    "ChatConfig",
    "ContextConfig",
    "FeatureConfig",
    "FrontendRefinementConfig",
    "GeneratedArtifactPaths",
    "KnowledgeBaseProject",
    "KnowledgeDocument",
    "KnowledgeDocumentSection",
    "LibraryConfig",
    "ModuleSelection",
    "PreviewConfig",
    "ProjectMetadata",
    "RefinementConfig",
    "ReturnConfig",
    "RouteConfig",
    "SeedDocumentSource",
    "ShowcasePageConfig",
    "SurfaceConfig",
    "UnifiedProjectConfig",
    "VisualConfig",
    "build_knowledge_base_runtime_app_from_spec",
    "compile_knowledge_document_source",
    "load_knowledge_base_project",
    "materialize_knowledge_base_project",
]
