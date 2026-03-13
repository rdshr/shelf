from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from html import escape
import hashlib
import json
from pathlib import Path
import re
import tomllib
from typing import Any

from framework_ir import FrameworkModuleIR, load_framework_registry, parse_framework_module
from project_runtime.config_layout import config_layout
from project_runtime.knowledge_base_contract import (
    KnowledgeBaseTemplateContract,
    load_knowledge_base_template_contract,
)
from project_runtime.governance import (
    build_governance_closure,
    build_governance_manifest,
    build_object_coverage_report,
    build_strict_zone_report,
    build_governance_tree,
)
from project_runtime.template_registry import (
    ProjectTemplateRegistration,
    detect_project_template_id as detect_registered_project_template_id,
    register_project_template,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE = REPO_ROOT / "projects/knowledge_base_basic/product_spec.toml"
DEFAULT_KNOWLEDGE_BASE_IMPLEMENTATION_CONFIG_FILE = (
    REPO_ROOT / "projects/knowledge_base_basic/implementation_config.toml"
)
KNOWLEDGE_BASE_TEMPLATE_ID = "knowledge_base_workbench"
KNOWLEDGE_BASE_PRODUCT_SPEC_LAYOUT = config_layout(
    {
        "project",
        "framework",
        "surface",
        "visual",
        "route",
        "showcase_page",
        "a11y",
        "library",
        "preview",
        "chat",
        "context",
        "return",
        "documents",
    },
    {
        "surface": {"copy"},
        "library": {"copy"},
        "chat": {"copy"},
    },
)
KNOWLEDGE_BASE_IMPLEMENTATION_CONFIG_LAYOUT = config_layout(
    {"frontend", "backend", "evidence", "artifacts"},
    {},
)
LEGACY_GENERATED_ARTIFACT_NAMES = frozenset({"project_bundle.py", "workbench_spec.json"})


def detect_project_template_id(product_spec_file: str | Path) -> str:
    return detect_registered_project_template_id(product_spec_file)


def assert_supported_project_template(product_spec_file: str | Path) -> str:
    template_id = detect_project_template_id(product_spec_file)
    if template_id != KNOWLEDGE_BASE_TEMPLATE_ID:
        raise ValueError(f"unsupported project template: {template_id}")
    return template_id

SURFACE_PRESETS: dict[str, dict[str, str]] = {
    "sand": {
        "bg": "#f4efe5",
        "panel": "#fffaf2",
        "panel_soft": "#f7f1e7",
        "ink": "#1b1f24",
        "muted": "#6d6a65",
        "line": "rgba(27, 31, 36, 0.12)",
    },
    "light": {
        "bg": "#f6f7fb",
        "panel": "#ffffff",
        "panel_soft": "#f4f6fb",
        "ink": "#111827",
        "muted": "#667085",
        "line": "rgba(17, 24, 39, 0.10)",
    },
}

RADIUS_PRESETS = {
    "sm": "12px",
    "md": "18px",
    "lg": "24px",
    "xl": "30px",
}

SHADOW_PRESETS = {
    "sm": "0 10px 28px rgba(15, 23, 42, 0.08)",
    "md": "0 18px 48px rgba(15, 23, 42, 0.10)",
    "lg": "0 24px 60px rgba(12, 17, 22, 0.30)",
}

FONT_PRESETS = {
    "sm": {"body": "0.94rem", "title": "1.45rem", "hero": "1.55rem"},
    "md": {"body": "1rem", "title": "1.6rem", "hero": "1.7rem"},
    "lg": {"body": "1.05rem", "title": "1.72rem", "hero": "1.84rem"},
}

SIDEBAR_WIDTH_PRESETS = {
    "compact": "280px",
    "md": "300px",
    "wide": "320px",
}

RAIL_WIDTH_PRESETS = {
    "compact": "340px",
    "md": "370px",
    "wide": "390px",
}

DENSITY_PRESETS = {
    "compact": {"shell_gap": "14px", "shell_padding": "14px", "panel_gap": "12px"},
    "comfortable": {"shell_gap": "18px", "shell_padding": "18px", "panel_gap": "16px"},
}


def _relative_path(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "section"


def _sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _tokenize(text: str) -> tuple[str, ...]:
    return tuple(token for token in re.findall(r"[a-z0-9]{3,}", text.lower()) if token)


def _read_toml_file(project_path: Path) -> dict[str, Any]:
    if not project_path.exists():
        raise FileNotFoundError(f"missing project config: {project_path}")
    with project_path.open("rb") as fh:
        data = tomllib.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"project config must decode into object: {project_path}")
    return data


def _normalize_project_path(project_file: str | Path) -> Path:
    project_path = Path(project_file)
    if not project_path.is_absolute():
        project_path = (REPO_ROOT / project_path).resolve()
    return project_path


def _implementation_config_path_for(product_spec_path: Path) -> Path:
    return product_spec_path.parent / "implementation_config.toml"


def _cleanup_generated_output_dir(output_path: Path, expected_file_names: set[str]) -> None:
    # generated/ is a compiler-owned evidence directory. Remove stale top-level files so
    # old artifact names cannot coexist with the current artifact contract.
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


def _optional_string(parent: dict[str, Any], key: str) -> str | None:
    value = parent.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"optional string must be non-empty when provided: {key}")
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


@dataclass(frozen=True)
class ProjectMetadata:
    project_id: str
    template: str
    display_name: str
    description: str
    version: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FrameworkSelection:
    frontend: str
    domain: str
    backend: str
    preset: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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
class FrontendImplementationConfig:
    renderer: str
    style_profile: str
    script_profile: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BackendImplementationConfig:
    renderer: str
    transport: str
    retrieval_strategy: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceConfig:
    product_spec_endpoint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ArtifactConfig:
    framework_ir_json: str
    product_spec_json: str
    implementation_bundle_py: str
    generation_manifest_json: str
    governance_manifest_json: str
    governance_tree_json: str
    strict_zone_report_json: str
    object_coverage_report_json: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class KnowledgeBaseImplementationConfig:
    frontend: FrontendImplementationConfig
    backend: BackendImplementationConfig
    evidence: EvidenceConfig
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
class KnowledgeBaseProductSpec:
    product_spec_file: str
    metadata: ProjectMetadata
    framework: FrameworkSelection
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
    framework_ir_json: str
    product_spec_json: str
    implementation_bundle_py: str
    generation_manifest_json: str
    governance_manifest_json: str
    governance_tree_json: str
    strict_zone_report_json: str
    object_coverage_report_json: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class KnowledgeBaseProject:
    product_spec_file: str
    implementation_config_file: str
    metadata: ProjectMetadata
    template_contract: KnowledgeBaseTemplateContract
    framework: FrameworkSelection
    implementation: KnowledgeBaseImplementationConfig
    surface: SurfaceConfig
    visual: VisualConfig
    visual_tokens: dict[str, str]
    features: FeatureConfig
    route: RouteConfig
    showcase_page: ShowcasePageConfig
    a11y: A11yConfig
    library: LibraryConfig
    preview: PreviewConfig
    chat: ChatConfig
    context: ContextConfig
    return_config: ReturnConfig
    copy: dict[str, str]
    frontend_ir: FrameworkModuleIR
    domain_ir: FrameworkModuleIR
    backend_ir: FrameworkModuleIR
    resolved_modules: tuple[FrameworkModuleIR, ...]
    documents: tuple[KnowledgeDocument, ...]
    frontend_contract: dict[str, Any] = field(default_factory=dict)
    workbench_contract: dict[str, Any] = field(default_factory=dict)
    ui_spec: dict[str, Any] = field(default_factory=dict)
    backend_spec: dict[str, Any] = field(default_factory=dict)
    validation_reports: dict[str, Any] = field(default_factory=dict)
    generated_artifacts: GeneratedArtifactPaths | None = None

    @property
    def routes(self) -> RouteConfig:
        return self.route

    @property
    def theme(self) -> VisualConfig:
        return self.visual

    @property
    def theme_tokens(self) -> dict[str, str]:
        return self.visual_tokens

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
        }

    def to_product_spec_dict(self) -> dict[str, Any]:
        return {
            "product": self.metadata.to_dict(),
            "surface": self.surface.to_dict(),
            "visual": self.visual.to_dict(),
            "navigation": {
                "pages": self._resolved_page_routes(),
                "return_targets": list(self.return_config.targets),
                "anchor_restore": self.return_config.anchor_restore,
            },
            "features": self.features.to_dict(),
            "route": self.route.to_dict(),
            "showcase_page": self.showcase_page.to_dict(),
            "a11y": self.a11y.to_dict(),
            "library": self.library.to_dict(),
            "preview": self.preview.to_dict(),
            "chat": self.chat.to_dict(),
            "context": self.context.to_dict(),
            "return": self.return_config.to_dict(),
            "content": {
                "surface_copy": self.surface.copy.to_dict(),
                "derived_copy": self.copy,
            },
            "interaction_model": {
                "workspace_flow": self.workbench_contract.get("flow", []),
                "citation_return": self.workbench_contract.get("citation_return_contract", {}),
                "surface_regions": self.frontend_contract.get("surface_regions", []),
                "interaction_actions": self.frontend_contract.get("interaction_actions", []),
            },
            "documents": [item.to_dict() for item in self.documents],
        }

    def to_runtime_bundle_dict(self) -> dict[str, Any]:
        return {
            "product_spec_file": self.product_spec_file,
            "implementation_config_file": self.implementation_config_file,
            "product_spec": self.to_product_spec_dict(),
            "framework": {
                **self.framework.to_dict(),
                "primary_modules": [
                    self.frontend_ir.to_dict(),
                    self.domain_ir.to_dict(),
                    self.backend_ir.to_dict(),
                ],
                "resolved_modules": [item.to_dict() for item in self.resolved_modules],
            },
            "implementation_config": self.implementation.to_dict(),
            "visual_tokens": self.visual_tokens,
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
            "validation_reports": self.validation_reports,
            "generated_artifacts": self.generated_artifacts.to_dict() if self.generated_artifacts else None,
        }

    def to_spec_dict(self) -> dict[str, Any]:
        return self.to_runtime_bundle_dict()

    def public_summary(self) -> dict[str, Any]:
        return {
            "product_spec_file": self.product_spec_file,
            "implementation_config_file": self.implementation_config_file,
            "project": self.metadata.to_dict(),
            "framework": self.framework.to_dict(),
            "implementation": self.implementation.to_dict(),
            "surface": self.surface.to_dict(),
            "visual": self.visual.to_dict(),
            "route": self.route.to_dict(),
            "a11y": self.a11y.to_dict(),
            "routes": {
                **self.route.to_dict(),
                "pages": self._resolved_page_routes(),
                "api": self._resolved_api_routes(),
            },
            "document_count": len(self.documents),
            "resolved_module_ids": [item.module_id for item in self.resolved_modules],
            "ui_spec_summary": {
                "page_ids": list(self.ui_spec.get("pages", {}).keys()),
                "component_ids": list(self.ui_spec.get("components", {}).keys()),
            },
            "backend_spec_summary": {
                "retrieval": self.backend_spec.get("retrieval", {}),
                "answer_policy": {
                    "citation_style": self.backend_spec.get("answer_policy", {}).get("citation_style"),
                },
            },
            "validation_reports": self.validation_reports,
            "validation_summary": {
                key: {
                    "passed": value["passed"],
                    "passed_count": value["passed_count"],
                    "rule_count": value["rule_count"],
                }
                for key, value in self.validation_reports.items()
                if isinstance(value, dict) and {"passed", "passed_count", "rule_count"} <= set(value)
            },
            "generated_artifacts": self.generated_artifacts.to_dict() if self.generated_artifacts else None,
        }


def _effective_generated_artifacts(project: KnowledgeBaseProject) -> GeneratedArtifactPaths:
    if project.generated_artifacts is not None:
        return project.generated_artifacts

    product_spec_path = _normalize_project_path(project.product_spec_file)
    artifact_directory = product_spec_path.parent / "generated"
    artifact_names = project.implementation.artifacts
    return GeneratedArtifactPaths(
        directory=_relative_path(artifact_directory),
        framework_ir_json=_relative_path(artifact_directory / artifact_names.framework_ir_json),
        product_spec_json=_relative_path(artifact_directory / artifact_names.product_spec_json),
        implementation_bundle_py=_relative_path(artifact_directory / artifact_names.implementation_bundle_py),
        generation_manifest_json=_relative_path(artifact_directory / artifact_names.generation_manifest_json),
        governance_manifest_json=_relative_path(artifact_directory / artifact_names.governance_manifest_json),
        governance_tree_json=_relative_path(artifact_directory / artifact_names.governance_tree_json),
        strict_zone_report_json=_relative_path(artifact_directory / artifact_names.strict_zone_report_json),
        object_coverage_report_json=_relative_path(artifact_directory / artifact_names.object_coverage_report_json),
    )


def build_implementation_effect_manifest(project: KnowledgeBaseProject) -> dict[str, dict[str, Any]]:
    generated_artifacts = _effective_generated_artifacts(project)
    return {
        "frontend.renderer": {
            "value": project.implementation.frontend.renderer,
            "relation": "equals",
            "targets": ["ui_spec.implementation.frontend_renderer"],
        },
        "frontend.style_profile": {
            "value": project.implementation.frontend.style_profile,
            "relation": "equals",
            "targets": ["ui_spec.implementation.style_profile"],
        },
        "frontend.script_profile": {
            "value": project.implementation.frontend.script_profile,
            "relation": "equals",
            "targets": ["ui_spec.implementation.script_profile"],
        },
        "backend.renderer": {
            "value": project.implementation.backend.renderer,
            "relation": "equals",
            "targets": ["backend_spec.implementation.backend_renderer"],
        },
        "backend.transport": {
            "value": project.implementation.backend.transport,
            "relation": "equals",
            "targets": ["backend_spec.transport.mode"],
        },
        "backend.retrieval_strategy": {
            "value": project.implementation.backend.retrieval_strategy,
            "relation": "equals",
            "targets": ["backend_spec.retrieval.strategy"],
        },
        "evidence.product_spec_endpoint": {
            "value": project.implementation.evidence.product_spec_endpoint,
            "relation": "equals",
            "targets": ["backend_spec.transport.product_spec_endpoint"],
        },
        "artifacts.framework_ir_json": {
            "value": project.implementation.artifacts.framework_ir_json,
            "relation": "basename",
            "targets": ["generated_artifacts.framework_ir_json"],
        },
        "artifacts.product_spec_json": {
            "value": project.implementation.artifacts.product_spec_json,
            "relation": "basename",
            "targets": ["generated_artifacts.product_spec_json"],
        },
        "artifacts.implementation_bundle_py": {
            "value": project.implementation.artifacts.implementation_bundle_py,
            "relation": "basename",
            "targets": ["generated_artifacts.implementation_bundle_py"],
        },
        "artifacts.generation_manifest_json": {
            "value": project.implementation.artifacts.generation_manifest_json,
            "relation": "basename",
            "targets": ["generated_artifacts.generation_manifest_json"],
        },
        "artifacts.governance_manifest_json": {
            "value": project.implementation.artifacts.governance_manifest_json,
            "relation": "basename",
            "targets": ["generated_artifacts.governance_manifest_json"],
        },
        "artifacts.governance_tree_json": {
            "value": project.implementation.artifacts.governance_tree_json,
            "relation": "basename",
            "targets": ["generated_artifacts.governance_tree_json"],
        },
        "artifacts.strict_zone_report_json": {
            "value": project.implementation.artifacts.strict_zone_report_json,
            "relation": "basename",
            "targets": ["generated_artifacts.strict_zone_report_json"],
        },
        "artifacts.object_coverage_report_json": {
            "value": project.implementation.artifacts.object_coverage_report_json,
            "relation": "basename",
            "targets": ["generated_artifacts.object_coverage_report_json"],
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
        raise ValueError("project config must define non-empty [[documents]]")
    seen_ids: set[str] = set()
    items: list[SeedDocumentSource] = []
    for raw_document in value:
        if not isinstance(raw_document, dict):
            raise ValueError("each [[documents]] entry must be a table")
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


def _load_product_spec(product_spec_path: Path) -> KnowledgeBaseProductSpec:
    raw = _read_toml_file(product_spec_path)
    project_table = _require_table(raw, "project")
    framework_table = _require_table(raw, "framework")
    surface_table = _require_table(raw, "surface")
    surface_copy_table = _require_table(surface_table, "copy")
    visual_table = _require_table(raw, "visual")
    route_table = _require_table(raw, "route")
    showcase_page_table = _require_table(raw, "showcase_page")
    a11y_table = _require_table(raw, "a11y")
    library_table = _require_table(raw, "library")
    library_copy_table = _require_table(library_table, "copy")
    preview_table = _require_table(raw, "preview")
    chat_table = _require_table(raw, "chat")
    chat_copy_table = _require_table(chat_table, "copy")
    context_table = _require_table(raw, "context")
    return_table = _require_table(raw, "return")

    library_enabled = _require_bool(library_table, "enabled")
    preview_enabled = _require_bool(preview_table, "enabled")
    chat_enabled = _require_bool(chat_table, "enabled")
    citations_enabled = _require_bool(chat_table, "citations_enabled")
    return_enabled = _require_bool(return_table, "enabled")
    allow_create = _require_bool(library_table, "allow_create")
    allow_delete = _require_bool(library_table, "allow_delete")

    return KnowledgeBaseProductSpec(
        product_spec_file=_relative_path(product_spec_path),
        metadata=ProjectMetadata(
            project_id=_require_string(project_table, "project_id"),
            template=_require_string(project_table, "template"),
            display_name=_require_string(project_table, "display_name"),
            description=_require_string(project_table, "description"),
            version=_require_string(project_table, "version"),
        ),
        framework=FrameworkSelection(
            frontend=_require_string(framework_table, "frontend"),
            domain=_require_string(framework_table, "domain"),
            backend=_require_string(framework_table, "backend"),
            preset=_require_string(framework_table, "preset"),
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
        documents=_require_documents(raw),
    )


def _load_implementation_config(implementation_config_path: Path) -> KnowledgeBaseImplementationConfig:
    raw = _read_toml_file(implementation_config_path)
    frontend_table = _require_table(raw, "frontend")
    backend_table = _require_table(raw, "backend")
    evidence_table = _require_table(raw, "evidence")
    artifacts_table = _require_table(raw, "artifacts")
    return KnowledgeBaseImplementationConfig(
        frontend=FrontendImplementationConfig(
            renderer=_require_string(frontend_table, "renderer"),
            style_profile=_require_string(frontend_table, "style_profile"),
            script_profile=_require_string(frontend_table, "script_profile"),
        ),
        backend=BackendImplementationConfig(
            renderer=_require_string(backend_table, "renderer"),
            transport=_require_string(backend_table, "transport"),
            retrieval_strategy=_require_string(backend_table, "retrieval_strategy"),
        ),
        evidence=EvidenceConfig(
            product_spec_endpoint=_require_string(evidence_table, "product_spec_endpoint"),
        ),
        artifacts=ArtifactConfig(
            framework_ir_json=_require_string(artifacts_table, "framework_ir_json"),
            product_spec_json=_require_string(artifacts_table, "product_spec_json"),
            implementation_bundle_py=_require_string(artifacts_table, "implementation_bundle_py"),
            generation_manifest_json=_require_string(artifacts_table, "generation_manifest_json"),
            governance_manifest_json=_require_string(artifacts_table, "governance_manifest_json"),
            governance_tree_json=_require_string(artifacts_table, "governance_tree_json"),
            strict_zone_report_json=_require_string(artifacts_table, "strict_zone_report_json"),
            object_coverage_report_json=_require_string(artifacts_table, "object_coverage_report_json"),
        ),
    )


def _resolve_framework_module(ref: str) -> FrameworkModuleIR:
    framework_path = REPO_ROOT / ref
    if not framework_path.exists():
        raise ValueError(f"framework ref does not exist: {ref}")
    return parse_framework_module(framework_path)


def _collect_framework_closure(*roots: FrameworkModuleIR) -> tuple[FrameworkModuleIR, ...]:
    registry = load_framework_registry()
    ordered: list[FrameworkModuleIR] = []
    seen: set[str] = set()

    def visit(module: FrameworkModuleIR) -> None:
        if module.module_id in seen:
            return
        seen.add(module.module_id)
        ordered.append(module)
        for base in module.bases:
            for ref in base.upstream_refs:
                upstream = registry.get_module(ref.framework, ref.level, ref.module)
                visit(upstream)

    for root in roots:
        visit(root)
    return tuple(ordered)


def _build_visual_tokens(visual: VisualConfig, surface: SurfaceConfig, preview: PreviewConfig) -> dict[str, str]:
    surface_tokens = SURFACE_PRESETS.get(visual.surface_preset)
    if surface_tokens is None:
        raise ValueError(f"unsupported visual.surface_preset: {visual.surface_preset}")
    radius_value = RADIUS_PRESETS.get(visual.radius_scale)
    if radius_value is None:
        raise ValueError(f"unsupported visual.radius_scale: {visual.radius_scale}")
    shadow_value = SHADOW_PRESETS.get(visual.shadow_level)
    if shadow_value is None:
        raise ValueError(f"unsupported visual.shadow_level: {visual.shadow_level}")
    font_values = FONT_PRESETS.get(visual.font_scale)
    if font_values is None:
        raise ValueError(f"unsupported visual.font_scale: {visual.font_scale}")
    sidebar_width = SIDEBAR_WIDTH_PRESETS.get(surface.sidebar_width)
    if sidebar_width is None:
        raise ValueError(f"unsupported surface.sidebar_width: {surface.sidebar_width}")
    rail_width = RAIL_WIDTH_PRESETS.get(surface.sidebar_width)
    if rail_width is None:
        raise ValueError(f"unsupported drawer width preset for surface.sidebar_width: {surface.sidebar_width}")
    density_values = DENSITY_PRESETS.get(surface.density)
    if density_values is None:
        raise ValueError(f"unsupported surface.density: {surface.density}")
    return {
        **surface_tokens,
        "accent": visual.accent,
        "accent_soft": f"{visual.accent}22",
        "radius": radius_value,
        "brand": visual.brand,
        "shadow": shadow_value,
        "font_body": font_values["body"],
        "font_title": font_values["title"],
        "font_hero": font_values["hero"],
        "message_width": "820px",
        "sidebar_width": sidebar_width,
        "drawer_width": rail_width,
        "shell_gap": density_values["shell_gap"],
        "shell_padding": density_values["shell_padding"],
        "panel_gap": density_values["panel_gap"],
        "preview_mode": surface.preview_mode,
        "preview_variant": preview.preview_variant,
    }


def _pick_boundary_name(module: FrameworkModuleIR, boundary_id: str, fallback: str) -> str:
    for item in module.boundaries:
        if item.boundary_id == boundary_id:
            return item.name
    return fallback


def _derive_copy(
    product_spec: KnowledgeBaseProductSpec,
    frontend_ir: FrameworkModuleIR,
    domain_ir: FrameworkModuleIR,
    backend_ir: FrameworkModuleIR,
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
    surface_copy = product_spec.surface.copy
    return {
        "hero_kicker": surface_copy.hero_kicker or product_spec.visual.brand,
        "hero_title": surface_copy.hero_title or product_spec.metadata.display_name,
        "hero_copy": surface_copy.hero_copy or hero_copy,
        "mode_label": "知识问答",
        "knowledge_base_name": product_spec.library.knowledge_base_name,
        "knowledge_base_description": product_spec.library.knowledge_base_description,
        "contract_title": "Framework Contract",
        "contract_value": base_labels,
        "contract_meta": f"Boundaries: {boundary_labels}",
        "library_title": surface_copy.library_title or _pick_boundary_name(domain_ir, "LIBRARY", "Library"),
        "preview_title": surface_copy.preview_title or _pick_boundary_name(domain_ir, "PREVIEW", "Preview"),
        "toc_title": surface_copy.toc_title or "TOC",
        "chat_title": surface_copy.chat_title or _pick_boundary_name(domain_ir, "CHAT", "Chat"),
        "search_placeholder": product_spec.library.search_placeholder,
        "chat_placeholder": product_spec.chat.placeholder,
        "chat_welcome": product_spec.chat.welcome,
        "empty_state_title": surface_copy.empty_state_title,
        "empty_state_copy": surface_copy.empty_state_copy,
    }


# @governed_symbol id=kb.ui.surface_spec owner=framework kind=ui_surface risk=high
def _build_ui_spec(project: KnowledgeBaseProject) -> dict[str, Any]:
    contract = project.template_contract
    knowledge_base_detail_path = f"{project.route.knowledge_detail}/{{knowledge_base_id}}"
    document_detail_path = f"{project.route.document_detail_prefix}/{{document_id}}"
    basketball_showcase_path = project.route.basketball_showcase
    return {
        "derived_from": {
            "framework_modules": {
                "frontend": project.frontend_ir.module_id,
                "domain": project.domain_ir.module_id,
            },
            "boundary_sections": {
                "SURFACE": "surface",
                "VISUAL": "visual",
                "ROUTE": "route",
                "A11Y": "a11y",
                "LIBRARY": "library",
                "PREVIEW": "preview",
                "CHAT": "chat",
                "CONTEXT": "context",
                "RETURN": "return",
            },
            "rule_drivers": {
                "frontend": [item.rule_id for item in project.frontend_ir.rules],
                "domain": [item.rule_id for item in project.domain_ir.rules],
            },
        },
        "implementation": {
            "frontend_renderer": project.implementation.frontend.renderer,
            "style_profile": project.implementation.frontend.style_profile,
            "script_profile": project.implementation.frontend.script_profile,
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
        "pages": {
            "chat_home": {
                "path": project.route.workbench,
                "title": project.metadata.display_name,
                "slots": list(contract.chat_home_slots),
                "entry_state": "welcome_prompts",
            },
            "basketball_showcase": {
                "path": basketball_showcase_path,
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
                "path": knowledge_base_detail_path,
                "chat_action_label": "用此知识库开始聊天",
                "overview_title": "知识库概况",
                "return_chat_with_document_label": "回到聊天并聚焦此文档",
                "document_detail_action_label": "查看文档详情",
                "slots": ["aux_sidebar", "page_header", "document_cards"],
            },
            "document_detail": {
                "path": document_detail_path,
                "title": "文档详情",
                "subtitle": "从引用抽屉进入完整文档上下文，再返回聊天继续提问。",
                "return_chat_label": "返回聊天",
                "return_knowledge_detail_label": "返回知识库详情",
                "slots": ["aux_sidebar", "page_header", "document_sections"],
            },
        },
        "components": {
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
        },
        "conversation": {
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
        },
        "citation": {
            "style": project.chat.citation_style,
            "summary_variant": project.return_config.citation_card_variant,
            "drawer_sections": list(contract.drawer_sections),
            "document_detail_path": document_detail_path,
        },
    }


# @governed_symbol id=kb.backend.surface_spec owner=implementation_config kind=backend_surface risk=high
def _build_backend_spec(project: KnowledgeBaseProject) -> dict[str, Any]:
    contract = project.template_contract
    return {
        "derived_from": {
            "framework_modules": {
                "domain": project.domain_ir.module_id,
                "backend": project.backend_ir.module_id,
            },
            "boundary_sections": {
                "LIBRARY": "library",
                "PREVIEW": "preview",
                "CHAT": "chat",
                "CONTEXT": "context",
                "RETURN": "return",
            },
            "rule_drivers": {
                "domain": [item.rule_id for item in project.domain_ir.rules],
                "backend": [item.rule_id for item in project.backend_ir.rules],
            },
        },
        "implementation": {
            "backend_renderer": project.implementation.backend.renderer,
        },
        "knowledge_base": {
            "knowledge_base_id": project.library.knowledge_base_id,
            "knowledge_base_name": project.library.knowledge_base_name,
            "knowledge_base_description": project.library.knowledge_base_description,
            "source_types": list(project.library.source_types),
            "metadata_fields": list(project.library.metadata_fields),
        },
        "transport": {
            "mode": project.implementation.backend.transport,
            "api_prefix": project.route.api_prefix,
            "product_spec_endpoint": project.implementation.evidence.product_spec_endpoint,
        },
        "retrieval": {
            "strategy": project.implementation.backend.retrieval_strategy,
            "query_token_min_length": 3,
            "focus_section_bonus": 4,
            "token_match_bonus": 3,
            "max_preview_sections": project.context.max_preview_sections,
            "max_citations": project.context.max_citations,
            "selection_mode": project.context.selection_mode,
        },
        "interaction_flow": list(contract.workbench_flow_dicts()),
        "answer_policy": {
            "citation_style": project.chat.citation_style,
            "no_match_text": (
                "当前知识库里没有找到足够相关的证据。你可以换一种问法，或者先浏览知识库与文档详情页确认可用来源。"
            ),
            "lead_template": "根据当前知识库，最相关的证据来自《{document_title}》的“{section_title}”。[{citation_index}]",
            "lead_snippet_template": "该片段指出：{snippet}",
            "followup_template": "补充来源还包括《{document_title}》的“{section_title}”。[{citation_index}] {snippet}",
            "closing_text": "点击文中引用可打开来源抽屉，并继续进入文档详情页查看完整上下文。",
        },
        "interaction_copy": {
            "loading_text": "正在检索知识库并整理回答…",
            "error_text": "回答生成失败。你可以重新提问，或稍后再试。",
        },
        "return_policy": {
            "targets": list(project.return_config.targets),
            "anchor_restore": project.return_config.anchor_restore,
            "chat_path": project.route.workbench,
            "knowledge_base_detail_path": f"{project.route.knowledge_detail}/{{knowledge_base_id}}",
            "document_detail_path": f"{project.route.document_detail_prefix}/{{document_id}}",
        },
        "write_policy": {
            "allow_create": project.library.allow_create,
            "allow_delete": project.library.allow_delete,
        },
    }


def _validate_product_spec(
    product_spec: KnowledgeBaseProductSpec,
    frontend_ir: FrameworkModuleIR,
    domain_ir: FrameworkModuleIR,
    backend_ir: FrameworkModuleIR,
    template_contract: KnowledgeBaseTemplateContract,
) -> None:
    if product_spec.metadata.template != KNOWLEDGE_BASE_TEMPLATE_ID:
        raise ValueError(f"unsupported project template: {product_spec.metadata.template}")
    if product_spec.surface.shell != template_contract.required_surface_shell:
        raise ValueError(f"surface.shell must be {template_contract.required_surface_shell}")
    if product_spec.surface.layout_variant != template_contract.required_layout_variant:
        raise ValueError(f"surface.layout_variant must be {template_contract.required_layout_variant}")
    if product_spec.surface.preview_mode != template_contract.required_preview_mode:
        raise ValueError(f"surface.preview_mode must be {template_contract.required_preview_mode}")
    if not all(
        (
            product_spec.library.enabled,
            product_spec.preview.enabled,
            product_spec.chat.enabled,
            product_spec.chat.citations_enabled,
            product_spec.return_config.enabled,
        )
    ):
        raise ValueError("knowledge_base_workbench requires library, preview, chat, citations, and return")
    if not product_spec.route.home.startswith("/") or not product_spec.route.workbench.startswith("/"):
        raise ValueError("route.home and route.workbench must start with '/'")
    if not product_spec.route.basketball_showcase.startswith("/"):
        raise ValueError("route.basketball_showcase must start with '/'")
    if not product_spec.route.knowledge_list.startswith("/") or not product_spec.route.knowledge_detail.startswith("/"):
        raise ValueError("route.knowledge_list and route.knowledge_detail must start with '/'")
    if not product_spec.route.document_detail_prefix.startswith("/"):
        raise ValueError("route.document_detail_prefix must start with '/'")
    if not product_spec.route.api_prefix.startswith("/api"):
        raise ValueError("route.api_prefix must start with '/api'")
    if not product_spec.route.knowledge_detail.startswith(product_spec.route.knowledge_list):
        raise ValueError("route.knowledge_detail must stay under route.knowledge_list")
    if not product_spec.route.document_detail_prefix.startswith(product_spec.route.knowledge_detail):
        raise ValueError("route.document_detail_prefix must stay under route.knowledge_detail")
    if not product_spec.route.basketball_showcase.startswith(product_spec.route.workbench):
        raise ValueError("route.basketball_showcase must stay under route.workbench")
    if not product_spec.library.knowledge_base_id.strip():
        raise ValueError("library.knowledge_base_id must be non-empty")
    if not template_contract.required_library_source_types.issubset(set(product_spec.library.source_types)):
        missing_source_types = sorted(template_contract.required_library_source_types - set(product_spec.library.source_types))
        raise ValueError(f"library.source_types missing required values: {', '.join(missing_source_types)}")
    if not template_contract.required_library_metadata_fields.issubset(set(product_spec.library.metadata_fields)):
        missing_metadata_fields = sorted(
            template_contract.required_library_metadata_fields - set(product_spec.library.metadata_fields)
        )
        raise ValueError(f"library.metadata_fields missing required values: {', '.join(missing_metadata_fields)}")
    if not product_spec.library.allow_create and product_spec.library.allow_delete:
        raise ValueError("library.allow_delete cannot be true when library.allow_create is false")
    if product_spec.library.default_focus != template_contract.required_library_default_focus:
        raise ValueError(f"library.default_focus must be {template_contract.required_library_default_focus}")
    if product_spec.preview.anchor_mode != template_contract.required_preview_anchor_mode:
        raise ValueError(f"preview.anchor_mode must be {template_contract.required_preview_anchor_mode}")
    if template_contract.preview_show_toc_required and not product_spec.preview.show_toc:
        raise ValueError("preview.show_toc must stay enabled for the knowledge-base workbench")
    if product_spec.preview.preview_variant != template_contract.required_preview_variant:
        raise ValueError(f"preview.preview_variant must be {template_contract.required_preview_variant}")
    if product_spec.chat.mode != template_contract.required_chat_mode:
        raise ValueError(f"chat.mode must be {template_contract.required_chat_mode}")
    if product_spec.chat.citation_style != template_contract.required_chat_citation_style:
        raise ValueError(f"chat.citation_style must be {template_contract.required_chat_citation_style}")
    if not product_spec.chat.welcome_prompts:
        raise ValueError("chat.welcome_prompts must not be empty")
    if product_spec.context.max_citations <= 0 or product_spec.context.max_preview_sections <= 0:
        raise ValueError("context max values must be positive")
    if template_contract.return_anchor_restore_required and not product_spec.return_config.anchor_restore:
        raise ValueError("return.anchor_restore must stay enabled")
    missing_return_targets = template_contract.required_return_target_set() - set(product_spec.return_config.targets)
    if missing_return_targets:
        raise ValueError(f"return.targets missing required values: {', '.join(sorted(missing_return_targets))}")
    if tuple(product_spec.a11y.reading_order) != template_contract.required_reading_order:
        raise ValueError(
            "a11y.reading_order must stay "
            + " -> ".join(template_contract.required_reading_order)
        )
    if len(product_spec.documents) < 1:
        raise ValueError("at least one document is required")
    if not frontend_ir.bases or not domain_ir.bases or not backend_ir.bases:
        raise ValueError("selected framework modules must define bases")
    for document in product_spec.documents:
        if len(_tokenize(document.summary)) < 3:
            raise ValueError(f"document summary is too short for retrieval: {document.document_id}")
        if "## " not in document.body_markdown:
            raise ValueError(f"document body must contain level-2 headings for anchor navigation: {document.document_id}")


def _validate_implementation_config(
    implementation: KnowledgeBaseImplementationConfig,
    product_spec: KnowledgeBaseProductSpec,
    template_contract: KnowledgeBaseTemplateContract,
) -> None:
    if implementation.frontend.renderer not in template_contract.supported_frontend_renderers:
        raise ValueError(f"unsupported frontend.renderer: {implementation.frontend.renderer}")
    if implementation.frontend.style_profile not in template_contract.supported_frontend_style_profiles:
        raise ValueError(f"unsupported frontend.style_profile: {implementation.frontend.style_profile}")
    if implementation.frontend.script_profile not in template_contract.supported_frontend_script_profiles:
        raise ValueError(f"unsupported frontend.script_profile: {implementation.frontend.script_profile}")
    if implementation.backend.renderer not in template_contract.supported_backend_renderers:
        raise ValueError(f"unsupported backend.renderer: {implementation.backend.renderer}")
    if implementation.backend.transport not in template_contract.supported_backend_transports:
        raise ValueError(f"unsupported backend.transport: {implementation.backend.transport}")
    if implementation.backend.retrieval_strategy not in template_contract.supported_backend_retrieval_strategies:
        raise ValueError(f"unsupported backend.retrieval_strategy: {implementation.backend.retrieval_strategy}")
    if not implementation.evidence.product_spec_endpoint.startswith(product_spec.route.api_prefix):
        raise ValueError("evidence.product_spec_endpoint must stay under route.api_prefix")
    if implementation.backend.retrieval_strategy != product_spec.chat.mode:
        raise ValueError("backend.retrieval_strategy must match chat.mode")


def _collect_validation_reports(project: KnowledgeBaseProject) -> dict[str, Any]:
    from frontend_kernel import summarize_frontend_rules, validate_frontend_rules
    from knowledge_base_framework import summarize_workbench_rules, validate_workbench_rules

    frontend_results = validate_frontend_rules(project)
    workbench_results = validate_workbench_rules(project)
    frontend_summary = summarize_frontend_rules(frontend_results)
    workbench_summary = summarize_workbench_rules(workbench_results)
    return {
        "frontend": frontend_summary,
        "knowledge_base": workbench_summary,
        "overall": {
            "passed": frontend_summary["passed"] and workbench_summary["passed"],
            "passed_count": frontend_summary["passed_count"] + workbench_summary["passed_count"],
            "rule_count": frontend_summary["rule_count"] + workbench_summary["rule_count"],
        },
    }


def _raise_on_validation_failures(reports: dict[str, Any]) -> None:
    errors: list[str] = []
    for scope in ("frontend", "knowledge_base"):
        report = reports.get(scope)
        if not isinstance(report, dict):
            continue
        for item in report.get("rules", []):
            if item.get("passed"):
                continue
            reasons = ", ".join(item.get("reasons", [])) or "unknown rule failure"
            errors.append(f"{scope}.{item.get('rule_id')}: {reasons}")
    if errors:
        raise ValueError("framework rule validation failed: " + " | ".join(errors))


def _build_generated_artifact_payloads(project: KnowledgeBaseProject) -> dict[str, str]:
    generated_artifacts = project.generated_artifacts
    if generated_artifacts is None:
        raise ValueError("generated_artifacts must be populated before payload generation")

    framework_ir_payload = {
        "primary_modules": [
            project.frontend_ir.to_dict(),
            project.domain_ir.to_dict(),
            project.backend_ir.to_dict(),
        ],
        "resolved_modules": [item.to_dict() for item in project.resolved_modules],
    }
    framework_ir_text = json.dumps(framework_ir_payload, ensure_ascii=False, indent=2)

    product_spec = project.to_product_spec_dict()
    runtime_bundle = project.to_runtime_bundle_dict()
    configuration_effects = build_implementation_effect_manifest(project)
    product_spec_text = json.dumps(product_spec, ensure_ascii=False, indent=2)
    implementation_bundle_text = "\n".join(
        [
            "from __future__ import annotations",
            "",
            "# GENERATED FILE. DO NOT EDIT.",
            "# Change framework markdown, product_spec.toml, or implementation_config.toml, then re-materialize.",
            "",
            "import json",
            "",
            f"PRODUCT_SPEC = json.loads(r'''{json.dumps(product_spec, ensure_ascii=False)}''')",
            f"IMPLEMENTATION_CONFIG = json.loads(r'''{json.dumps(project.implementation.to_dict(), ensure_ascii=False)}''')",
            f"RUNTIME_BUNDLE = json.loads(r'''{json.dumps(runtime_bundle, ensure_ascii=False)}''')",
            "",
        ]
    )
    governance_manifest_text = json.dumps(
        build_governance_manifest(project),
        ensure_ascii=False,
        indent=2,
    )
    governance_tree_text = json.dumps(
        build_governance_tree(project),
        ensure_ascii=False,
        indent=2,
    )
    strict_zone_report_text = json.dumps(
        build_strict_zone_report(build_governance_closure(project)),
        ensure_ascii=False,
        indent=2,
    )
    object_coverage_report_text = json.dumps(
        build_object_coverage_report(build_governance_closure(project)),
        ensure_ascii=False,
        indent=2,
    )
    generation_manifest_text = json.dumps(
        {
            "project_id": project.metadata.project_id,
            "template": project.metadata.template,
            "product_spec_file": project.product_spec_file,
            "implementation_config_file": project.implementation_config_file,
            "generator": {
                "entry": "project_runtime.knowledge_base.materialize_knowledge_base_project",
                "discipline": (
                    "project behavior is derived from framework markdown, product spec, and implementation config; "
                    "generated code must not be edited directly"
                ),
            },
            "framework_inputs": {
                "frontend": project.frontend_ir.path,
                "domain": project.domain_ir.path,
                "backend": project.backend_ir.path,
                "resolved_modules": [item.path for item in project.resolved_modules],
            },
            "configuration_effects": configuration_effects,
            "generated_files": {
                "framework_ir_json": generated_artifacts.framework_ir_json,
                "product_spec_json": generated_artifacts.product_spec_json,
                "implementation_bundle_py": generated_artifacts.implementation_bundle_py,
                "generation_manifest_json": generated_artifacts.generation_manifest_json,
                "governance_manifest_json": generated_artifacts.governance_manifest_json,
                "governance_tree_json": generated_artifacts.governance_tree_json,
                "strict_zone_report_json": generated_artifacts.strict_zone_report_json,
                "object_coverage_report_json": generated_artifacts.object_coverage_report_json,
            },
            "content_sha256": {
                "framework_ir_json": _sha256_text(framework_ir_text),
                "product_spec_json": _sha256_text(product_spec_text),
                "implementation_bundle_py": _sha256_text(implementation_bundle_text),
                "governance_manifest_json": _sha256_text(governance_manifest_text),
                "governance_tree_json": _sha256_text(governance_tree_text),
                "strict_zone_report_json": _sha256_text(strict_zone_report_text),
                "object_coverage_report_json": _sha256_text(object_coverage_report_text),
            },
        },
        ensure_ascii=False,
        indent=2,
    )
    return {
        "framework_ir_json": framework_ir_text,
        "product_spec_json": product_spec_text,
        "implementation_bundle_py": implementation_bundle_text,
        "generation_manifest_json": generation_manifest_text,
        "governance_manifest_json": governance_manifest_text,
        "governance_tree_json": governance_tree_text,
        "strict_zone_report_json": strict_zone_report_text,
        "object_coverage_report_json": object_coverage_report_text,
    }


def _compile_project(
    product_spec: KnowledgeBaseProductSpec,
    implementation: KnowledgeBaseImplementationConfig,
) -> KnowledgeBaseProject:
    from frontend_kernel import build_frontend_contract
    from knowledge_base_framework import build_workbench_contract

    template_contract = load_knowledge_base_template_contract()
    frontend_ir = _resolve_framework_module(product_spec.framework.frontend)
    domain_ir = _resolve_framework_module(product_spec.framework.domain)
    backend_ir = _resolve_framework_module(product_spec.framework.backend)
    _validate_product_spec(product_spec, frontend_ir, domain_ir, backend_ir, template_contract)
    _validate_implementation_config(implementation, product_spec, template_contract)
    documents = tuple(_compile_document(item) for item in product_spec.documents)
    project = KnowledgeBaseProject(
        product_spec_file=product_spec.product_spec_file,
        implementation_config_file=_relative_path(_implementation_config_path_for(_normalize_project_path(product_spec.product_spec_file))),
        metadata=product_spec.metadata,
        template_contract=template_contract,
        framework=product_spec.framework,
        implementation=implementation,
        surface=product_spec.surface,
        visual=product_spec.visual,
        visual_tokens=_build_visual_tokens(product_spec.visual, product_spec.surface, product_spec.preview),
        features=product_spec.features,
        route=product_spec.route,
        showcase_page=product_spec.showcase_page,
        a11y=product_spec.a11y,
        library=product_spec.library,
        preview=product_spec.preview,
        chat=product_spec.chat,
        context=product_spec.context,
        return_config=product_spec.return_config,
        copy=_derive_copy(product_spec, frontend_ir, domain_ir, backend_ir),
        frontend_ir=frontend_ir,
        domain_ir=domain_ir,
        backend_ir=backend_ir,
        resolved_modules=_collect_framework_closure(frontend_ir, domain_ir, backend_ir),
        documents=documents,
    )
    project = replace(project, backend_spec=_build_backend_spec(project))
    project = replace(
        project,
        frontend_contract=build_frontend_contract(project),
        workbench_contract=build_workbench_contract(project),
    )
    project = replace(
        project,
        ui_spec=_build_ui_spec(project),
    )
    validation_reports = _collect_validation_reports(project)
    _raise_on_validation_failures(validation_reports)
    return replace(project, validation_reports=validation_reports)


def load_knowledge_base_project(
    product_spec_file: str | Path = DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE,
) -> KnowledgeBaseProject:
    product_spec_path = _normalize_project_path(product_spec_file)
    assert_supported_project_template(product_spec_path)
    implementation_config_path = _implementation_config_path_for(product_spec_path)
    product_spec = _load_product_spec(product_spec_path)
    implementation = _load_implementation_config(implementation_config_path)
    return _compile_project(product_spec, implementation)


def materialize_knowledge_base_project(
    product_spec_file: str | Path = DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE,
    output_dir: str | Path | None = None,
) -> KnowledgeBaseProject:
    product_spec_path = _normalize_project_path(product_spec_file)
    assert_supported_project_template(product_spec_path)
    project = load_knowledge_base_project(product_spec_path)
    generated_dir = product_spec_path.parent / "generated"
    output_path = _normalize_project_path(output_dir) if output_dir is not None else generated_dir
    output_path.mkdir(parents=True, exist_ok=True)

    artifact_names = project.implementation.artifacts
    expected_file_names = {
        artifact_names.framework_ir_json,
        artifact_names.product_spec_json,
        artifact_names.implementation_bundle_py,
        artifact_names.generation_manifest_json,
        artifact_names.governance_manifest_json,
        artifact_names.governance_tree_json,
        artifact_names.strict_zone_report_json,
        artifact_names.object_coverage_report_json,
    }
    _cleanup_generated_output_dir(output_path, expected_file_names)
    framework_ir_path = output_path / artifact_names.framework_ir_json
    product_spec_path_json = output_path / artifact_names.product_spec_json
    implementation_bundle_path = output_path / artifact_names.implementation_bundle_py
    generation_manifest_path = output_path / artifact_names.generation_manifest_json
    governance_manifest_path = output_path / artifact_names.governance_manifest_json
    governance_tree_path = output_path / artifact_names.governance_tree_json
    strict_zone_report_path = output_path / artifact_names.strict_zone_report_json
    object_coverage_report_path = output_path / artifact_names.object_coverage_report_json
    # Keep generated evidence stable even when callers materialize into a temp directory.
    # The output path controls where files are written, but the manifest and runtime bundle
    # should continue to point at the project's canonical generated directory.
    artifact_directory = generated_dir
    project = replace(
        project,
        generated_artifacts=GeneratedArtifactPaths(
            directory=_relative_path(artifact_directory),
            framework_ir_json=_relative_path(artifact_directory / artifact_names.framework_ir_json),
            product_spec_json=_relative_path(artifact_directory / artifact_names.product_spec_json),
            implementation_bundle_py=_relative_path(artifact_directory / artifact_names.implementation_bundle_py),
            generation_manifest_json=_relative_path(artifact_directory / artifact_names.generation_manifest_json),
            governance_manifest_json=_relative_path(artifact_directory / artifact_names.governance_manifest_json),
            governance_tree_json=_relative_path(artifact_directory / artifact_names.governance_tree_json),
            strict_zone_report_json=_relative_path(artifact_directory / artifact_names.strict_zone_report_json),
            object_coverage_report_json=_relative_path(artifact_directory / artifact_names.object_coverage_report_json),
        ),
    )
    payloads = _build_generated_artifact_payloads(project)
    framework_ir_path.write_text(payloads["framework_ir_json"], encoding="utf-8")
    product_spec_path_json.write_text(payloads["product_spec_json"], encoding="utf-8")
    implementation_bundle_path.write_text(payloads["implementation_bundle_py"], encoding="utf-8")
    generation_manifest_path.write_text(payloads["generation_manifest_json"], encoding="utf-8")
    governance_manifest_path.write_text(payloads["governance_manifest_json"], encoding="utf-8")
    governance_tree_path.write_text(payloads["governance_tree_json"], encoding="utf-8")
    strict_zone_report_path.write_text(payloads["strict_zone_report_json"], encoding="utf-8")
    object_coverage_report_path.write_text(payloads["object_coverage_report_json"], encoding="utf-8")

    return project


def build_knowledge_base_runtime_app_from_spec(
    product_spec_file: str | Path = DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE,
) -> Any:
    from knowledge_base_runtime.app import build_knowledge_base_runtime_app

    project = materialize_knowledge_base_project(product_spec_file)
    return build_knowledge_base_runtime_app(project)


register_project_template(
    ProjectTemplateRegistration(
        template_id=KNOWLEDGE_BASE_TEMPLATE_ID,
        default_product_spec_file=DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE,
        product_spec_layout=KNOWLEDGE_BASE_PRODUCT_SPEC_LAYOUT,
        implementation_config_layout=KNOWLEDGE_BASE_IMPLEMENTATION_CONFIG_LAYOUT,
        load_project=load_knowledge_base_project,
        materialize_project=materialize_knowledge_base_project,
        build_runtime_app_from_spec=build_knowledge_base_runtime_app_from_spec,
        build_governance_closure=build_governance_closure,
        build_implementation_effect_manifest=build_implementation_effect_manifest,
        default=True,
    )
)
