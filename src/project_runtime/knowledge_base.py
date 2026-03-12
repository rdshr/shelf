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
from project_runtime.frontend_app_generator import build_frontend_app_files

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE = REPO_ROOT / "projects/knowledge_base_basic/product_spec.toml"
DEFAULT_KNOWLEDGE_BASE_IMPLEMENTATION_CONFIG_FILE = (
    REPO_ROOT / "projects/knowledge_base_basic/implementation_config.toml"
)
SUPPORTED_PROJECT_TEMPLATE = "knowledge_base_workbench"

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


FRONTEND_APP_PRESERVE_NAMES = {"node_modules", ".env"}


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
    login: str
    workbench: str
    knowledge_list: str
    knowledge_detail: str
    document_detail_prefix: str
    api_prefix: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PageShellsConfig:
    workspace_shell: tuple[str, ...]
    standalone_shell: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "workspace_shell": list(self.workspace_shell),
            "standalone_shell": list(self.standalone_shell),
        }


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
class AuthCopyConfig:
    login_title: str
    login_subtitle: str
    primary_action: str
    secondary_action: str
    guard_message: str
    failure_message: str
    expired_message: str
    cancel_message: str
    reauth_message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_feedback_shell_dict(self) -> dict[str, Any]:
        return {
            "guard_message": self.guard_message,
            "failure_message": self.failure_message,
            "expired_message": self.expired_message,
            "cancel_message": self.cancel_message,
            "reauth_message": self.reauth_message,
        }


@dataclass(frozen=True)
class AuthSurfaceConfig:
    page_variant: str
    shell_variant: str
    entry_variant: str
    sections: tuple[str, ...]
    show_brand: bool
    show_guard_message: bool
    show_return_hint: bool
    show_secondary_action: bool
    container_variant: str
    density: str
    action_emphasis: str
    header_alignment: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "page_variant": self.page_variant,
            "shell_variant": self.shell_variant,
            "entry_variant": self.entry_variant,
            "sections": list(self.sections),
            "show_brand": self.show_brand,
            "show_guard_message": self.show_guard_message,
            "show_return_hint": self.show_return_hint,
            "show_secondary_action": self.show_secondary_action,
            "container_variant": self.container_variant,
            "density": self.density,
            "action_emphasis": self.action_emphasis,
            "header_alignment": self.header_alignment,
        }

    def to_entry_shell_dict(self) -> dict[str, Any]:
        return self.to_dict()


@dataclass(frozen=True)
class AuthFlowConfig:
    guard_behavior: str
    submit_behavior: str
    success_behavior: str
    failure_feedback: str
    cancel_behavior: str
    expired_behavior: str
    reauth_behavior: str
    restore_target: bool
    preserve_query: bool
    preserve_anchor: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_flow_dict(self) -> dict[str, Any]:
        return self.to_dict()


@dataclass(frozen=True)
class AuthContractConfig:
    login_action: str
    logout_action: str
    session_probe: str
    failure_modes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "login_action": self.login_action,
            "logout_action": self.logout_action,
            "session_probe": self.session_probe,
            "failure_modes": list(self.failure_modes),
        }

    def to_auth_request_contract_dict(self) -> dict[str, Any]:
        return {
            "login_action": self.login_action,
            "logout_action": self.logout_action,
        }

    def to_session_flow_requirements_dict(self) -> dict[str, Any]:
        return {
            "session_probe": self.session_probe,
            "failure_modes": list(self.failure_modes),
        }


@dataclass(frozen=True)
class AuthConfig:
    enabled: bool
    mode: str
    entry: str
    session_scope: str
    return_after_login: bool
    protected_routes: tuple[str, ...]
    public_routes: tuple[str, ...]
    default_return_target: str
    copy: AuthCopyConfig
    surface: AuthSurfaceConfig
    flow: AuthFlowConfig
    contract: AuthContractConfig

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "mode": self.mode,
            "entry": self.entry,
            "session_scope": self.session_scope,
            "return_after_login": self.return_after_login,
            "protected_routes": list(self.protected_routes),
            "public_routes": list(self.public_routes),
            "default_return_target": self.default_return_target,
            "copy": self.copy.to_dict(),
            "surface": self.surface.to_dict(),
            "flow": self.flow.to_dict(),
            "contract": self.contract.to_dict(),
        }

    def to_shell_dict(self) -> dict[str, Any]:
        return {
            "AUTHENTRYSHELL": self.surface.to_entry_shell_dict(),
            "RETURNSHELL": {
                "return_after_login": self.return_after_login,
                "default_return_target": self.default_return_target,
            },
            "FEEDBACKSHELL": self.copy.to_feedback_shell_dict(),
            "PROTECTEDSHELL": {
                "protected_routes": list(self.protected_routes),
                "public_routes": list(self.public_routes),
            },
        }

    def to_flow_dict(self) -> dict[str, Any]:
        return {
            "AUTHENTRYFLOW": {
                "entry": self.entry,
                "surface": self.surface.to_entry_shell_dict(),
                "submit_behavior": self.flow.submit_behavior,
            },
            "SESSIONFLOW": {
                **self.contract.to_session_flow_requirements_dict(),
                "session_scope": self.session_scope,
                "expired_behavior": self.flow.expired_behavior,
                "reauth_behavior": self.flow.reauth_behavior,
            },
            "RETURNFLOW": {
                "guard_behavior": self.flow.guard_behavior,
                "success_behavior": self.flow.success_behavior,
                "cancel_behavior": self.flow.cancel_behavior,
                "restore_target": self.flow.restore_target,
                "preserve_query": self.flow.preserve_query,
                "preserve_anchor": self.flow.preserve_anchor,
                "default_return_target": self.default_return_target,
            },
            "FEEDBACKFLOW": {
                "failure_feedback": self.flow.failure_feedback,
                **self.copy.to_feedback_shell_dict(),
            },
            "GUARDFLOW": {
                "mode": self.mode,
                "protected_routes": list(self.protected_routes),
                "public_routes": list(self.public_routes),
                "guard_behavior": self.flow.guard_behavior,
            },
        }

    def to_contract_alignment_dict(self) -> dict[str, Any]:
        return {
            "AUTHREQUEST": self.contract.to_auth_request_contract_dict(),
            "SESSIONSTATE": {
                "session_scope": self.session_scope,
                "failure_modes": list(self.contract.failure_modes),
            },
            "AUTHERROR": {
                "failure_modes": list(self.contract.failure_modes),
                "failure_feedback": self.flow.failure_feedback,
            },
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
    auth_runtime: str
    guard_strategy: str
    login_surface_runtime: str
    session_storage: str
    return_strategy: str
    auth_style_profile: str
    auth_action_emphasis_profile: str
    auth_motion_profile: str
    auth_title_hierarchy_profile: str
    auth_subtitle_tone_profile: str
    auth_theme_binding: str
    workspace_layout_runtime: str
    standalone_layout_runtime: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BackendAuthApiConfig:
    login_endpoint: str
    logout_endpoint: str
    session_endpoint: str
    login_method: str
    logout_method: str
    session_method: str
    session_header: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BackendImplementationConfig:
    renderer: str
    transport: str
    retrieval_strategy: str
    auth_provider: str
    auth_session_transport: str
    auth_verification_mode: str
    auth_api: BackendAuthApiConfig

    def to_dict(self) -> dict[str, Any]:
        return {
            "renderer": self.renderer,
            "transport": self.transport,
            "retrieval_strategy": self.retrieval_strategy,
            "auth_provider": self.auth_provider,
            "auth_session_transport": self.auth_session_transport,
            "auth_verification_mode": self.auth_verification_mode,
            "auth_api": self.auth_api.to_dict(),
        }


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
    frontend_app_dir: str

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
    page_shells: PageShellsConfig
    auth: AuthConfig
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
    frontend_app_dir: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class KnowledgeBaseProject:
    product_spec_file: str
    implementation_config_file: str
    metadata: ProjectMetadata
    framework: FrameworkSelection
    implementation: KnowledgeBaseImplementationConfig
    surface: SurfaceConfig
    visual: VisualConfig
    visual_tokens: dict[str, str]
    features: FeatureConfig
    route: RouteConfig
    page_shells: PageShellsConfig
    auth: AuthConfig
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
            "login": self.route.login,
            "chat_home": self.route.workbench,
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
            "page_shells": self.page_shells.to_dict(),
            "auth": self.auth.to_dict(),
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
            "page_shells": self.page_shells.to_dict(),
            "auth": self.auth.to_dict(),
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
    page_shells_table = _require_table(raw, "page_shells")
    auth_table = _require_table(raw, "auth")
    auth_copy_table = _require_table(auth_table, "copy")
    auth_surface_table = _require_table(auth_table, "surface")
    auth_flow_table = _require_table(auth_table, "flow")
    auth_contract_table = _require_table(auth_table, "contract")
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
    auth_enabled = _require_bool(auth_table, "enabled")
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
            login=_require_string(route_table, "login"),
            workbench=_require_string(route_table, "workbench"),
            knowledge_list=_require_string(route_table, "knowledge_list"),
            knowledge_detail=_require_string(route_table, "knowledge_detail"),
            document_detail_prefix=_require_string(route_table, "document_detail_prefix"),
            api_prefix=_require_string(route_table, "api_prefix"),
        ),
        page_shells=PageShellsConfig(
            workspace_shell=_require_string_tuple(page_shells_table, "workspace_shell"),
            standalone_shell=_require_string_tuple(page_shells_table, "standalone_shell"),
        ),
        auth=AuthConfig(
            enabled=auth_enabled,
            mode=_require_string(auth_table, "mode"),
            entry=_require_string(auth_table, "entry"),
            session_scope=_require_string(auth_table, "session_scope"),
            return_after_login=_require_bool(auth_table, "return_after_login"),
            protected_routes=_require_string_tuple(auth_table, "protected_routes"),
            public_routes=_require_string_tuple(auth_table, "public_routes"),
            default_return_target=_require_string(auth_table, "default_return_target"),
            copy=AuthCopyConfig(
                login_title=_require_string(auth_copy_table, "login_title"),
                login_subtitle=_require_string(auth_copy_table, "login_subtitle"),
                primary_action=_require_string(auth_copy_table, "primary_action"),
                secondary_action=_require_string(auth_copy_table, "secondary_action"),
                guard_message=_require_string(auth_copy_table, "guard_message"),
                failure_message=_require_string(auth_copy_table, "failure_message"),
                expired_message=_require_string(auth_copy_table, "expired_message"),
                cancel_message=_require_string(auth_copy_table, "cancel_message"),
                reauth_message=_require_string(auth_copy_table, "reauth_message"),
            ),
            surface=AuthSurfaceConfig(
                page_variant=_require_string(auth_surface_table, "page_variant"),
                shell_variant=_require_string(auth_surface_table, "shell_variant"),
                entry_variant=_require_string(auth_surface_table, "entry_variant"),
                sections=_require_string_tuple(auth_surface_table, "sections"),
                show_brand=_require_bool(auth_surface_table, "show_brand"),
                show_guard_message=_require_bool(auth_surface_table, "show_guard_message"),
                show_return_hint=_require_bool(auth_surface_table, "show_return_hint"),
                show_secondary_action=_require_bool(auth_surface_table, "show_secondary_action"),
                container_variant=_require_string(auth_surface_table, "container_variant"),
                density=_require_string(auth_surface_table, "density"),
                action_emphasis=_require_string(auth_surface_table, "action_emphasis"),
                header_alignment=_require_string(auth_surface_table, "header_alignment"),
            ),
            flow=AuthFlowConfig(
                guard_behavior=_require_string(auth_flow_table, "guard_behavior"),
                submit_behavior=_require_string(auth_flow_table, "submit_behavior"),
                success_behavior=_require_string(auth_flow_table, "success_behavior"),
                failure_feedback=_require_string(auth_flow_table, "failure_feedback"),
                cancel_behavior=_require_string(auth_flow_table, "cancel_behavior"),
                expired_behavior=_require_string(auth_flow_table, "expired_behavior"),
                reauth_behavior=_require_string(auth_flow_table, "reauth_behavior"),
                restore_target=_require_bool(auth_flow_table, "restore_target"),
                preserve_query=_require_bool(auth_flow_table, "preserve_query"),
                preserve_anchor=_require_bool(auth_flow_table, "preserve_anchor"),
            ),
            contract=AuthContractConfig(
                login_action=_require_string(auth_contract_table, "login_action"),
                logout_action=_require_string(auth_contract_table, "logout_action"),
                session_probe=_require_string(auth_contract_table, "session_probe"),
                failure_modes=_require_string_tuple(auth_contract_table, "failure_modes"),
            ),
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
    frontend_auth_table = _require_table(frontend_table, "auth")
    frontend_auth_style_table = _require_table(frontend_table, "auth_style")
    frontend_layout_table = _require_table(frontend_table, "layout")
    backend_table = _require_table(raw, "backend")
    backend_auth_table = _require_table(backend_table, "auth")
    backend_auth_api_table = _require_table(backend_table, "auth_api")
    evidence_table = _require_table(raw, "evidence")
    artifacts_table = _require_table(raw, "artifacts")
    return KnowledgeBaseImplementationConfig(
        frontend=FrontendImplementationConfig(
            renderer=_require_string(frontend_table, "renderer"),
            style_profile=_require_string(frontend_table, "style_profile"),
            script_profile=_require_string(frontend_table, "script_profile"),
            auth_runtime=_require_string(frontend_auth_table, "auth_runtime"),
            guard_strategy=_require_string(frontend_auth_table, "guard_strategy"),
            login_surface_runtime=_require_string(frontend_auth_table, "login_surface_runtime"),
            session_storage=_require_string(frontend_auth_table, "session_storage"),
            return_strategy=_require_string(frontend_auth_table, "return_strategy"),
            auth_style_profile=_require_string(frontend_auth_style_table, "style_profile"),
            auth_action_emphasis_profile=_require_string(frontend_auth_style_table, "action_emphasis_profile"),
            auth_motion_profile=_require_string(frontend_auth_style_table, "motion_profile"),
            auth_title_hierarchy_profile=_require_string(frontend_auth_style_table, "title_hierarchy_profile"),
            auth_subtitle_tone_profile=_require_string(frontend_auth_style_table, "subtitle_tone_profile"),
            auth_theme_binding=_require_string(frontend_auth_style_table, "theme_binding"),
            workspace_layout_runtime=_require_string(frontend_layout_table, "workspace_layout_runtime"),
            standalone_layout_runtime=_require_string(frontend_layout_table, "standalone_layout_runtime"),
        ),
        backend=BackendImplementationConfig(
            renderer=_require_string(backend_table, "renderer"),
            transport=_require_string(backend_table, "transport"),
            retrieval_strategy=_require_string(backend_table, "retrieval_strategy"),
            auth_provider=_require_string(backend_auth_table, "provider"),
            auth_session_transport=_require_string(backend_auth_table, "session_transport"),
            auth_verification_mode=_require_string(backend_auth_table, "verification_mode"),
            auth_api=BackendAuthApiConfig(
                login_endpoint=_require_string(backend_auth_api_table, "login_endpoint"),
                logout_endpoint=_require_string(backend_auth_api_table, "logout_endpoint"),
                session_endpoint=_require_string(backend_auth_api_table, "session_endpoint"),
                login_method=_require_string(backend_auth_api_table, "login_method"),
                logout_method=_require_string(backend_auth_api_table, "logout_method"),
                session_method=_require_string(backend_auth_api_table, "session_method"),
                session_header=_require_string(backend_auth_api_table, "session_header"),
            ),
        ),
        evidence=EvidenceConfig(
            product_spec_endpoint=_require_string(evidence_table, "product_spec_endpoint"),
        ),
        artifacts=ArtifactConfig(
            framework_ir_json=_require_string(artifacts_table, "framework_ir_json"),
            product_spec_json=_require_string(artifacts_table, "product_spec_json"),
            implementation_bundle_py=_require_string(artifacts_table, "implementation_bundle_py"),
            generation_manifest_json=_require_string(artifacts_table, "generation_manifest_json"),
            frontend_app_dir=_require_string(artifacts_table, "frontend_app_dir"),
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


def _build_ui_spec(project: KnowledgeBaseProject) -> dict[str, Any]:
    knowledge_base_detail_path = f"{project.route.knowledge_detail}/{{knowledge_base_id}}"
    document_detail_path = f"{project.route.document_detail_prefix}/{{document_id}}"
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
                "AUTH": "auth",
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
        "shell": {
            "id": project.surface.shell,
            "layout_variant": project.surface.layout_variant,
            "regions": ["conversation_sidebar", "chat_main", "citation_drawer"],
            "secondary_pages": ["login", "knowledge_list", "knowledge_detail", "document_detail"],
            "default_page": "login" if project.auth.enabled else "chat_home",
            "preview_mode": project.surface.preview_mode,
            "density": project.surface.density,
        },
        "page_shells": {
            "workspace_shell": list(project.page_shells.workspace_shell),
            "standalone_shell": list(project.page_shells.standalone_shell),
            "layout_runtime": {
                "workspace_shell": project.implementation.frontend.workspace_layout_runtime,
                "standalone_shell": project.implementation.frontend.standalone_layout_runtime,
            },
        },
        "visual": {
            "theme": project.visual.to_dict(),
            "tokens": project.visual_tokens,
        },
        "pages": {
            "login": {
                "path": project.route.login,
                "title": project.auth.copy.login_title,
                "subtitle": project.auth.copy.login_subtitle,
                "page_variant": project.auth.surface.page_variant,
                "shell_variant": project.auth.surface.shell_variant,
                "entry_variant": project.auth.surface.entry_variant,
                "slots": list(project.auth.surface.sections),
                "show_brand": project.auth.surface.show_brand,
                "show_guard_message": project.auth.surface.show_guard_message,
                "show_return_hint": project.auth.surface.show_return_hint,
                "show_secondary_action": project.auth.surface.show_secondary_action,
                "container_variant": project.auth.surface.container_variant,
                "density": project.auth.surface.density,
                "action_emphasis": project.auth.surface.action_emphasis,
                "header_alignment": project.auth.surface.header_alignment,
                "entry_state": "login_required",
            },
            "chat_home": {
                "path": project.route.workbench,
                "title": project.metadata.display_name,
                "shell_variant": "workspace_shell",
                "slots": [
                    "conversation_sidebar",
                    "chat_header",
                    "message_stream",
                    "chat_composer",
                    "citation_drawer",
                    "knowledge_switch_dialog",
                ],
                "entry_state": "welcome_prompts",
            },
            "knowledge_list": {
                "path": project.route.knowledge_list,
                "title": project.surface.copy.library_title,
                "shell_variant": "workspace_shell",
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
                "shell_variant": "workspace_shell",
                "chat_action_label": "用此知识库开始聊天",
                "overview_title": "知识库概况",
                "return_chat_with_document_label": "回到聊天并聚焦此文档",
                "document_detail_action_label": "查看文档详情",
                "slots": ["aux_sidebar", "page_header", "document_cards"],
            },
            "document_detail": {
                "path": document_detail_path,
                "shell_variant": "workspace_shell",
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
                "knowledge_entry_label": f"知识库 · {project.library.knowledge_base_name}",
            },
            "login_header": {
                "title": project.auth.copy.login_title,
                "subtitle": project.auth.copy.login_subtitle,
                "guard_message": project.auth.copy.guard_message,
            },
            "login_form": {
                "primary_action": project.auth.copy.primary_action,
                "secondary_action": project.auth.copy.secondary_action,
                "return_after_login": project.auth.return_after_login,
            },
            "aux_sidebar": {
                "nav": {
                    "chat": "返回聊天",
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
            },
            "citation_drawer": {
                "title": project.copy["preview_title"],
                "close_aria_label": "Close citation drawer",
                "tab_variant": "numbered",
                "sections": ["snippet", "source_context"],
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
        "auth": {
            "enabled": project.auth.enabled,
            "mode": project.auth.mode,
            "entry": project.auth.entry,
            "protected_routes": list(project.auth.protected_routes),
            "public_routes": list(project.auth.public_routes),
            "default_return_target": project.auth.default_return_target,
            "surface": project.auth.surface.to_dict(),
            "flow": project.auth.flow.to_dict(),
            "contract": project.auth.contract.to_dict(),
            "shell_alignment": project.auth.to_shell_dict(),
            "flow_alignment": project.auth.to_flow_dict(),
            "contract_alignment": project.auth.to_contract_alignment_dict(),
            "style": {
                "profile": project.implementation.frontend.auth_style_profile,
                "action_emphasis_profile": project.implementation.frontend.auth_action_emphasis_profile,
                "motion_profile": project.implementation.frontend.auth_motion_profile,
                "theme_binding": project.implementation.frontend.auth_theme_binding,
            },
        },
        "citation": {
            "style": project.chat.citation_style,
            "summary_variant": project.return_config.citation_card_variant,
            "drawer_sections": ["snippet", "source_context"],
            "document_detail_path": document_detail_path,
        },
    }


def _build_backend_spec(project: KnowledgeBaseProject) -> dict[str, Any]:
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
                "AUTH": "auth",
            },
            "rule_drivers": {
                "domain": [item.rule_id for item in project.domain_ir.rules],
                "backend": [item.rule_id for item in project.backend_ir.rules],
            },
        },
        "knowledge_base": {
            "knowledge_base_id": project.library.knowledge_base_id,
            "knowledge_base_name": project.library.knowledge_base_name,
            "knowledge_base_description": project.library.knowledge_base_description,
            "source_types": list(project.library.source_types),
            "metadata_fields": list(project.library.metadata_fields),
        },
        "retrieval": {
            "query_token_min_length": 3,
            "focus_section_bonus": 4,
            "token_match_bonus": 3,
            "max_preview_sections": project.context.max_preview_sections,
            "max_citations": project.context.max_citations,
            "selection_mode": project.context.selection_mode,
        },
        "interaction_flow": [
            {
                "stage_id": "login_gate",
                "depends_on": [],
                "produces": ["session_state", "auth_return_target"],
            },
            {
                "stage_id": "knowledge_base_select",
                "depends_on": ["session_state"],
                "produces": ["knowledge_base_id"],
            },
            {
                "stage_id": "conversation",
                "depends_on": ["knowledge_base_id"],
                "produces": ["conversation_id", "answer", "citations"],
            },
            {
                "stage_id": "citation_review",
                "depends_on": ["conversation_id", "citations"],
                "produces": ["document_id", "section_id", "drawer_state"],
            },
            {
                "stage_id": "document_detail",
                "depends_on": ["document_id", "section_id"],
                "produces": ["document_page", "citation_return_path"],
            },
        ],
        "auth": {
            "enabled": project.auth.enabled,
            "provider": project.implementation.backend.auth_provider,
            "session_transport": project.implementation.backend.auth_session_transport,
            "verification_mode": project.implementation.backend.auth_verification_mode,
            "contract": project.auth.contract.to_dict(),
            "flow_alignment": project.auth.to_flow_dict(),
            "contract_alignment": project.auth.to_contract_alignment_dict(),
            "api": project.implementation.backend.auth_api.to_dict(),
            "protected_routes": list(project.auth.protected_routes),
        },
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
) -> None:
    if product_spec.metadata.template != SUPPORTED_PROJECT_TEMPLATE:
        raise ValueError(f"unsupported project template: {product_spec.metadata.template}")
    if product_spec.surface.shell != "conversation_sidebar_shell":
        raise ValueError("surface.shell must be conversation_sidebar_shell")
    if product_spec.surface.layout_variant != "chatgpt_knowledge_client":
        raise ValueError("surface.layout_variant must be chatgpt_knowledge_client")
    if product_spec.surface.preview_mode != "drawer":
        raise ValueError("surface.preview_mode must be drawer")
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
    if (
        not product_spec.route.home.startswith("/")
        or not product_spec.route.login.startswith("/")
        or not product_spec.route.workbench.startswith("/")
    ):
        raise ValueError("route.home, route.login, and route.workbench must start with '/'")
    if not product_spec.route.knowledge_list.startswith("/") or not product_spec.route.knowledge_detail.startswith("/"):
        raise ValueError("route.knowledge_list and route.knowledge_detail must start with '/'")
    if not product_spec.route.document_detail_prefix.startswith("/"):
        raise ValueError("route.document_detail_prefix must start with '/'")
    if product_spec.route.login == product_spec.route.workbench:
        raise ValueError("route.login must differ from route.workbench")
    if not product_spec.route.api_prefix.startswith("/api"):
        raise ValueError("route.api_prefix must start with '/api'")
    if not product_spec.route.knowledge_detail.startswith(product_spec.route.knowledge_list):
        raise ValueError("route.knowledge_detail must stay under route.knowledge_list")
    if not product_spec.route.document_detail_prefix.startswith(product_spec.route.knowledge_detail):
        raise ValueError("route.document_detail_prefix must stay under route.knowledge_detail")
    if not product_spec.library.knowledge_base_id.strip():
        raise ValueError("library.knowledge_base_id must be non-empty")
    if "markdown" not in product_spec.library.source_types:
        raise ValueError("library.source_types must include markdown")
    if "title" not in product_spec.library.metadata_fields:
        raise ValueError("library.metadata_fields must include title")
    if not product_spec.library.allow_create and product_spec.library.allow_delete:
        raise ValueError("library.allow_delete cannot be true when library.allow_create is false")
    if product_spec.library.default_focus != "current_knowledge_base":
        raise ValueError("library.default_focus must be current_knowledge_base")
    if product_spec.preview.anchor_mode != "heading":
        raise ValueError("preview.anchor_mode must be heading")
    if not product_spec.preview.show_toc:
        raise ValueError("preview.show_toc must stay enabled for the knowledge-base workbench")
    if product_spec.preview.preview_variant != "citation_drawer":
        raise ValueError("preview.preview_variant must be citation_drawer")
    if product_spec.chat.mode != "retrieval_stub":
        raise ValueError("chat.mode must be retrieval_stub")
    if product_spec.chat.citation_style != "inline_refs":
        raise ValueError("chat.citation_style must be inline_refs")
    if not product_spec.chat.welcome_prompts:
        raise ValueError("chat.welcome_prompts must not be empty")
    if product_spec.auth.mode != "required_before_workbench":
        raise ValueError("auth.mode must be required_before_workbench")
    if product_spec.auth.entry != "dedicated_login_page":
        raise ValueError("auth.entry must be dedicated_login_page")
    if not product_spec.auth.enabled:
        raise ValueError("auth.enabled must stay enabled for the protected workbench variant")
    if "workbench" not in product_spec.auth.protected_routes:
        raise ValueError("auth.protected_routes must include workbench")
    if "login" not in product_spec.auth.public_routes:
        raise ValueError("auth.public_routes must include login")
    if product_spec.auth.default_return_target != "workbench":
        raise ValueError("auth.default_return_target must be workbench")
    if product_spec.auth.surface.shell_variant != "standalone_shell":
        raise ValueError("auth.surface.shell_variant must be standalone_shell")
    if product_spec.auth.surface.entry_variant not in {
        "username_password",
        "email_password",
        "phone_code",
        "passwordless_code",
        "sso_redirect",
        "oauth_button",
        "magic_link",
    }:
        raise ValueError("auth.surface.entry_variant must stay within AUTHENTRYFLOW legal variants")
    expected_workspace_shell = ("workbench", "knowledge_list", "knowledge_detail", "document_detail")
    if tuple(product_spec.page_shells.workspace_shell) != expected_workspace_shell:
        raise ValueError("page_shells.workspace_shell must stay workbench -> knowledge_list -> knowledge_detail -> document_detail")
    if tuple(product_spec.page_shells.standalone_shell) != ("login",):
        raise ValueError("page_shells.standalone_shell must stay login for the current protected-workbench variant")
    if product_spec.auth.surface.page_variant != "centered_form":
        raise ValueError("auth.surface.page_variant must be centered_form")
    if tuple(product_spec.auth.surface.sections) != ("login_header", "login_form", "secondary_actions"):
        raise ValueError("auth.surface.sections must stay login_header -> login_form -> secondary_actions")
    if product_spec.auth.surface.container_variant != "single_card":
        raise ValueError("auth.surface.container_variant must be single_card")
    if product_spec.auth.surface.density not in {"compact", "comfortable"}:
        raise ValueError("auth.surface.density must be compact or comfortable")
    if product_spec.auth.surface.action_emphasis not in {"primary_strong", "balanced"}:
        raise ValueError("auth.surface.action_emphasis must be primary_strong or balanced")
    if product_spec.auth.surface.header_alignment not in {"left", "center"}:
        raise ValueError("auth.surface.header_alignment must be left or center")
    if product_spec.auth.flow.guard_behavior != "redirect_to_login":
        raise ValueError("auth.flow.guard_behavior must be redirect_to_login")
    if product_spec.auth.flow.success_behavior != "redirect_to_return_target":
        raise ValueError("auth.flow.success_behavior must be redirect_to_return_target")
    if not product_spec.auth.flow.restore_target:
        raise ValueError("auth.flow.restore_target must stay enabled")
    if product_spec.auth.contract.login_action != "session_start":
        raise ValueError("auth.contract.login_action must be session_start")
    if product_spec.auth.contract.logout_action != "session_terminate":
        raise ValueError("auth.contract.logout_action must be session_terminate")
    if product_spec.auth.contract.session_probe != "required_on_protected_entry":
        raise ValueError("auth.contract.session_probe must be required_on_protected_entry")
    if tuple(product_spec.auth.contract.failure_modes) != ("invalid_session", "expired_session"):
        raise ValueError("auth.contract.failure_modes must stay invalid_session -> expired_session")
    if product_spec.context.max_citations <= 0 or product_spec.context.max_preview_sections <= 0:
        raise ValueError("context max values must be positive")
    if not product_spec.return_config.anchor_restore:
        raise ValueError("return.anchor_restore must stay enabled")
    if "citation_drawer" not in product_spec.return_config.targets:
        raise ValueError("return.targets must include citation_drawer")
    if "document_detail" not in product_spec.return_config.targets:
        raise ValueError("return.targets must include document_detail")
    if tuple(product_spec.a11y.reading_order) != (
        "login_header",
        "login_form",
        "conversation_sidebar",
        "chat_header",
        "message_stream",
        "chat_composer",
        "citation_drawer",
    ):
        raise ValueError(
            "a11y.reading_order must stay login_header -> login_form -> conversation_sidebar -> chat_header -> message_stream -> chat_composer -> citation_drawer"
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
) -> None:
    if not implementation.evidence.product_spec_endpoint.startswith(product_spec.route.api_prefix):
        raise ValueError("evidence.product_spec_endpoint must stay under route.api_prefix")
    if implementation.backend.retrieval_strategy != product_spec.chat.mode:
        raise ValueError("backend.retrieval_strategy must match chat.mode")
    if implementation.backend.transport != "http_json":
        raise ValueError("backend.transport must be http_json")
    if implementation.frontend.guard_strategy != "router_guard":
        raise ValueError("frontend.auth.guard_strategy must be router_guard")
    if implementation.frontend.login_surface_runtime != "react_form_page":
        raise ValueError("frontend.auth.login_surface_runtime must be react_form_page")
    if implementation.frontend.auth_style_profile != "auth_centered_card_v1":
        raise ValueError("frontend.auth_style.style_profile must be auth_centered_card_v1")
    if implementation.frontend.auth_action_emphasis_profile not in {
        "primary_strong_secondary_soft",
        "balanced_actions",
    }:
        raise ValueError(
            "frontend.auth_style.action_emphasis_profile must be primary_strong_secondary_soft or balanced_actions"
        )
    if implementation.frontend.auth_motion_profile not in {"minimal", "none"}:
        raise ValueError("frontend.auth_style.motion_profile must be minimal or none")
    if implementation.frontend.auth_title_hierarchy_profile not in {"title_strong", "title_balanced"}:
        raise ValueError("frontend.auth_style.title_hierarchy_profile must be title_strong or title_balanced")
    if implementation.frontend.auth_subtitle_tone_profile not in {"subtitle_muted", "subtitle_balanced"}:
        raise ValueError(
            "frontend.auth_style.subtitle_tone_profile must be subtitle_muted or subtitle_balanced"
        )
    if implementation.frontend.auth_theme_binding != "frontend_visual_tokens":
        raise ValueError("frontend.auth_style.theme_binding must be frontend_visual_tokens")
    if implementation.frontend.workspace_layout_runtime != "app_shell_with_sidebar":
        raise ValueError("frontend.layout.workspace_layout_runtime must be app_shell_with_sidebar")
    if implementation.frontend.standalone_layout_runtime != "centered_single_task_layout":
        raise ValueError("frontend.layout.standalone_layout_runtime must be centered_single_task_layout")
    if implementation.backend.auth_provider != "local_stub":
        raise ValueError("backend.auth.provider must be local_stub")
    if implementation.backend.auth_session_transport != "frontend_bearer_stub":
        raise ValueError("backend.auth.session_transport must be frontend_bearer_stub")
    if implementation.backend.auth_verification_mode != "accept_frontend_session":
        raise ValueError("backend.auth.verification_mode must be accept_frontend_session")
    if implementation.backend.auth_api.login_endpoint != "/auth/login":
        raise ValueError("backend.auth_api.login_endpoint must be /auth/login")
    if implementation.backend.auth_api.logout_endpoint != "/auth/logout":
        raise ValueError("backend.auth_api.logout_endpoint must be /auth/logout")
    if implementation.backend.auth_api.session_endpoint != "/auth/session":
        raise ValueError("backend.auth_api.session_endpoint must be /auth/session")
    if implementation.backend.auth_api.login_method != "POST":
        raise ValueError("backend.auth_api.login_method must be POST")
    if implementation.backend.auth_api.logout_method != "POST":
        raise ValueError("backend.auth_api.logout_method must be POST")
    if implementation.backend.auth_api.session_method != "GET":
        raise ValueError("backend.auth_api.session_method must be GET")
    if implementation.backend.auth_api.session_header != "X-Knowledge-Session":
        raise ValueError("backend.auth_api.session_header must be X-Knowledge-Session")


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
            "generated_files": {
                "framework_ir_json": generated_artifacts.framework_ir_json,
                "product_spec_json": generated_artifacts.product_spec_json,
                "implementation_bundle_py": generated_artifacts.implementation_bundle_py,
                "generation_manifest_json": generated_artifacts.generation_manifest_json,
                "frontend_app_dir": generated_artifacts.frontend_app_dir,
            },
            "content_sha256": {
                "framework_ir_json": _sha256_text(framework_ir_text),
                "product_spec_json": _sha256_text(product_spec_text),
                "implementation_bundle_py": _sha256_text(implementation_bundle_text),
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
    }


def _materialize_frontend_app_dir(frontend_app_path: Path, payloads: dict[str, str]) -> None:
    frontend_app_path.mkdir(parents=True, exist_ok=True)
    expected_paths = {Path(relative_path) for relative_path in payloads}

    for existing in sorted(frontend_app_path.rglob("*"), reverse=True):
        relative = existing.relative_to(frontend_app_path)
        if relative.parts and relative.parts[0] in FRONTEND_APP_PRESERVE_NAMES:
            continue
        if existing.is_file() and relative not in expected_paths:
            existing.unlink()
            continue
        if existing.is_dir() and existing != frontend_app_path:
            if any(child for child in existing.iterdir()):
                continue
            existing.rmdir()

    for relative_path, text in payloads.items():
        file_path = frontend_app_path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(text, encoding="utf-8")


def _compile_project(
    product_spec: KnowledgeBaseProductSpec,
    implementation: KnowledgeBaseImplementationConfig,
) -> KnowledgeBaseProject:
    from frontend_kernel import build_frontend_contract
    from knowledge_base_framework import build_workbench_contract

    frontend_ir = _resolve_framework_module(product_spec.framework.frontend)
    domain_ir = _resolve_framework_module(product_spec.framework.domain)
    backend_ir = _resolve_framework_module(product_spec.framework.backend)
    _validate_product_spec(product_spec, frontend_ir, domain_ir, backend_ir)
    _validate_implementation_config(implementation, product_spec)
    documents = tuple(_compile_document(item) for item in product_spec.documents)
    project = KnowledgeBaseProject(
        product_spec_file=product_spec.product_spec_file,
        implementation_config_file=_relative_path(_implementation_config_path_for(_normalize_project_path(product_spec.product_spec_file))),
        metadata=product_spec.metadata,
        framework=product_spec.framework,
        implementation=implementation,
        surface=product_spec.surface,
        visual=product_spec.visual,
        visual_tokens=_build_visual_tokens(product_spec.visual, product_spec.surface, product_spec.preview),
        features=product_spec.features,
        route=product_spec.route,
        page_shells=product_spec.page_shells,
        auth=product_spec.auth,
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
    implementation_config_path = _implementation_config_path_for(product_spec_path)
    product_spec = _load_product_spec(product_spec_path)
    implementation = _load_implementation_config(implementation_config_path)
    return _compile_project(product_spec, implementation)


def materialize_knowledge_base_project(
    product_spec_file: str | Path = DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE,
    output_dir: str | Path | None = None,
) -> KnowledgeBaseProject:
    product_spec_path = _normalize_project_path(product_spec_file)
    project = load_knowledge_base_project(product_spec_path)
    generated_dir = product_spec_path.parent / "generated"
    output_path = _normalize_project_path(output_dir) if output_dir is not None else generated_dir
    output_path.mkdir(parents=True, exist_ok=True)

    artifact_names = project.implementation.artifacts
    framework_ir_path = output_path / artifact_names.framework_ir_json
    product_spec_path_json = output_path / artifact_names.product_spec_json
    implementation_bundle_path = output_path / artifact_names.implementation_bundle_py
    generation_manifest_path = output_path / artifact_names.generation_manifest_json
    frontend_app_path = output_path / artifact_names.frontend_app_dir
    project = replace(
        project,
        generated_artifacts=GeneratedArtifactPaths(
            directory=_relative_path(generated_dir),
            framework_ir_json=_relative_path(generated_dir / artifact_names.framework_ir_json),
            product_spec_json=_relative_path(generated_dir / artifact_names.product_spec_json),
            implementation_bundle_py=_relative_path(generated_dir / artifact_names.implementation_bundle_py),
            generation_manifest_json=_relative_path(generated_dir / artifact_names.generation_manifest_json),
            frontend_app_dir=_relative_path(generated_dir / artifact_names.frontend_app_dir),
        ),
    )
    payloads = _build_generated_artifact_payloads(project)
    framework_ir_path.write_text(payloads["framework_ir_json"], encoding="utf-8")
    product_spec_path_json.write_text(payloads["product_spec_json"], encoding="utf-8")
    implementation_bundle_path.write_text(payloads["implementation_bundle_py"], encoding="utf-8")
    generation_manifest_path.write_text(payloads["generation_manifest_json"], encoding="utf-8")
    frontend_app_payloads = build_frontend_app_files(project)
    _materialize_frontend_app_dir(frontend_app_path, frontend_app_payloads)

    return project
