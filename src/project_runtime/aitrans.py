from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import json
from pathlib import Path
import tomllib
from typing import Any

from framework_ir import FrameworkModuleIR, load_framework_registry, parse_framework_module

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AITRANS_PRODUCT_SPEC_FILE = REPO_ROOT / "projects/desktop_screenshot_translate/product_spec.toml"
DEFAULT_AITRANS_IMPLEMENTATION_CONFIG_FILE = (
    REPO_ROOT / "projects/desktop_screenshot_translate/implementation_config.toml"
)
SUPPORTED_PROJECT_TEMPLATE = "desktop_screenshot_translate"

SURFACE_PRESETS: dict[str, dict[str, str]] = {
    "mist": {
        "bg": "#eff3f4",
        "panel": "#fcfefd",
        "panel_soft": "#f4f8f6",
        "ink": "#16302b",
        "muted": "#58706c",
        "line": "rgba(22, 48, 43, 0.12)",
    },
    "slate": {
        "bg": "#eef2f7",
        "panel": "#ffffff",
        "panel_soft": "#f7f9fc",
        "ink": "#17212b",
        "muted": "#617182",
        "line": "rgba(23, 33, 43, 0.12)",
    },
}

RADIUS_PRESETS = {
    "sm": "12px",
    "md": "18px",
    "lg": "24px",
    "xl": "28px",
}

SHADOW_PRESETS = {
    "sm": "0 10px 28px rgba(12, 23, 20, 0.08)",
    "md": "0 18px 44px rgba(12, 23, 20, 0.14)",
    "lg": "0 26px 58px rgba(12, 23, 20, 0.20)",
}

FONT_PRESETS = {
    "sm": {"body": "0.93rem", "title": "1.36rem"},
    "md": {"body": "1rem", "title": "1.54rem"},
    "lg": {"body": "1.06rem", "title": "1.72rem"},
}


def _relative_path(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def _sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _normalize_project_path(project_file: str | Path) -> Path:
    project_path = Path(project_file)
    if not project_path.is_absolute():
        project_path = (REPO_ROOT / project_path).resolve()
    return project_path


def _implementation_config_path_for(product_spec_path: Path) -> Path:
    return product_spec_path.parent / "implementation_config.toml"


def _read_toml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing project config: {path}")
    with path.open("rb") as fh:
        data = tomllib.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"project config must decode into a table: {path}")
    return data


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


def _resolve_framework_module(path: str) -> FrameworkModuleIR:
    resolved_path = _normalize_project_path(path)
    return parse_framework_module(resolved_path)


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
    runtime: str
    preset: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SurfaceCopyConfig:
    app_name: str
    tagline: str
    capture_hint: str
    empty_title: str
    empty_copy: str
    processing_title: str
    processing_copy: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SurfaceConfig:
    shell: str
    layout_variant: str
    entry_mode: str
    result_mode: str
    density: str
    copy: SurfaceCopyConfig

    def to_dict(self) -> dict[str, Any]:
        return {
            "shell": self.shell,
            "layout_variant": self.layout_variant,
            "entry_mode": self.entry_mode,
            "result_mode": self.result_mode,
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
class A11yConfig:
    reading_order: tuple[str, ...]
    keyboard_nav: tuple[str, ...]
    announcements: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DesktopConfig:
    platforms: tuple[str, ...]
    entry_points: tuple[str, ...]
    single_instance: bool
    permissions: tuple[str, ...]
    degrade_policy: str
    hotkey_behavior: str
    window_strategy: str
    focus_restore: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CaptureConfig:
    modes: tuple[str, ...]
    selection_shape: str
    cancel_methods: tuple[str, ...]
    include_cursor: bool
    multi_display: bool
    high_dpi: bool
    session_policy: str
    image_format: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PipelineConfig:
    source_languages: tuple[str, ...]
    target_language: str
    deliverables: tuple[str, ...]
    fallback_policy: str
    timeout_budget_ms: int
    latency_budget_p95_ms: int
    ocr_confidence_visible: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PresentationCopyConfig:
    copy_success: str
    retry_label: str
    close_label: str
    recapture_label: str
    failure_title: str
    empty_translation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PresentationConfig:
    panel_variant: str
    show_source_text: bool
    show_translated_text: bool
    show_status: bool
    show_error_reason: bool
    default_pinned: bool
    actions: tuple[str, ...]
    auto_hide: str
    copy: PresentationCopyConfig

    def to_dict(self) -> dict[str, Any]:
        return {
            "panel_variant": self.panel_variant,
            "show_source_text": self.show_source_text,
            "show_translated_text": self.show_translated_text,
            "show_status": self.show_status,
            "show_error_reason": self.show_error_reason,
            "default_pinned": self.default_pinned,
            "actions": list(self.actions),
            "auto_hide": self.auto_hide,
            "copy": self.copy.to_dict(),
        }


@dataclass(frozen=True)
class GovernanceConfig:
    event_scope: tuple[str, ...]
    audit_fields: tuple[str, ...]
    privacy_mode: str
    update_channel: str
    compat_matrix: tuple[str, ...]
    offline_policy: str
    capture_p95_ms: int
    ocr_p95_ms: int
    translation_p95_ms: int
    render_p95_ms: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DesktopRuntimeConfig:
    host: str
    shell_profile: str
    preload_bridge: str
    window_state_store: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CaptureRuntimeConfig:
    frame_source: str
    bitmap_pipeline: str
    coordinate_profile: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProvidersConfig:
    ocr_chain: tuple[str, ...]
    ocr_distribution: str
    ocr_dev_fallback: str
    translation_chain: tuple[str, ...]
    translation_api: str
    translation_model: str
    translation_endpoint_profile: str
    translation_endpoint_source: str
    source_language_detection: str
    secret_source: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PresentationRuntimeConfig:
    renderer: str
    ui_framework: str
    overlay_profile: str
    clipboard_bridge: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReleaseConfig:
    targets: tuple[str, ...]
    package_formats: tuple[str, ...]
    auto_update: bool
    channel: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceConfig:
    product_spec_endpoint: str
    runtime_bundle_endpoint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ArtifactConfig:
    framework_ir_json: str
    product_spec_json: str
    implementation_bundle_py: str
    generation_manifest_json: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AitransImplementationConfig:
    desktop_runtime: DesktopRuntimeConfig
    capture_runtime: CaptureRuntimeConfig
    providers: ProvidersConfig
    presentation_runtime: PresentationRuntimeConfig
    release: ReleaseConfig
    evidence: EvidenceConfig
    artifacts: ArtifactConfig

    def to_dict(self) -> dict[str, Any]:
        return {
            "desktop_runtime": self.desktop_runtime.to_dict(),
            "capture_runtime": self.capture_runtime.to_dict(),
            "providers": self.providers.to_dict(),
            "presentation_runtime": self.presentation_runtime.to_dict(),
            "release": self.release.to_dict(),
            "evidence": self.evidence.to_dict(),
            "artifacts": self.artifacts.to_dict(),
        }


@dataclass(frozen=True)
class AitransProductSpec:
    product_spec_file: str
    metadata: ProjectMetadata
    framework: FrameworkSelection
    surface: SurfaceConfig
    visual: VisualConfig
    a11y: A11yConfig
    desktop: DesktopConfig
    capture: CaptureConfig
    pipeline: PipelineConfig
    presentation: PresentationConfig
    governance: GovernanceConfig


@dataclass(frozen=True)
class GeneratedArtifactPaths:
    directory: str
    framework_ir_json: str
    product_spec_json: str
    implementation_bundle_py: str
    generation_manifest_json: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AitransProject:
    product_spec_file: str
    implementation_config_file: str
    metadata: ProjectMetadata
    framework: FrameworkSelection
    surface: SurfaceConfig
    visual: VisualConfig
    a11y: A11yConfig
    desktop: DesktopConfig
    capture: CaptureConfig
    pipeline: PipelineConfig
    presentation: PresentationConfig
    governance: GovernanceConfig
    implementation: AitransImplementationConfig
    frontend_ir: FrameworkModuleIR
    domain_ir: FrameworkModuleIR
    runtime_ir: FrameworkModuleIR
    resolved_modules: tuple[FrameworkModuleIR, ...]
    execution_contract: dict[str, Any]
    validation_reports: dict[str, Any]
    generated_artifacts: GeneratedArtifactPaths | None = None

    def to_product_spec_dict(self) -> dict[str, Any]:
        return {
            "project": self.metadata.to_dict(),
            "framework": self.framework.to_dict(),
            "surface": self.surface.to_dict(),
            "visual": self.visual.to_dict(),
            "a11y": self.a11y.to_dict(),
            "desktop": self.desktop.to_dict(),
            "capture": self.capture.to_dict(),
            "pipeline": self.pipeline.to_dict(),
            "presentation": self.presentation.to_dict(),
            "governance": self.governance.to_dict(),
        }

    def to_runtime_bundle_dict(self) -> dict[str, Any]:
        return {
            "project": self.metadata.to_dict(),
            "framework": self.framework.to_dict(),
            "visual_tokens": _build_visual_tokens(self.visual),
            "surface": self.surface.to_dict(),
            "a11y": self.a11y.to_dict(),
            "desktop": self.desktop.to_dict(),
            "capture": self.capture.to_dict(),
            "pipeline": self.pipeline.to_dict(),
            "presentation": self.presentation.to_dict(),
            "governance": self.governance.to_dict(),
            "implementation": self.implementation.to_dict(),
            "contracts": self.execution_contract,
            "validation_reports": self.validation_reports,
            "generated_artifacts": None if self.generated_artifacts is None else self.generated_artifacts.to_dict(),
        }


def _load_product_spec(product_spec_path: Path) -> AitransProductSpec:
    data = _read_toml_file(product_spec_path)
    project = _require_table(data, "project")
    framework = _require_table(data, "framework")
    surface = _require_table(data, "surface")
    surface_copy = _require_table(surface, "copy")
    visual = _require_table(data, "visual")
    a11y = _require_table(data, "a11y")
    desktop = _require_table(data, "desktop")
    capture = _require_table(data, "capture")
    pipeline = _require_table(data, "pipeline")
    presentation = _require_table(data, "presentation")
    presentation_copy = _require_table(presentation, "copy")
    governance = _require_table(data, "governance")
    return AitransProductSpec(
        product_spec_file=_relative_path(product_spec_path),
        metadata=ProjectMetadata(
            project_id=_require_string(project, "project_id"),
            template=_require_string(project, "template"),
            display_name=_require_string(project, "display_name"),
            description=_require_string(project, "description"),
            version=_require_string(project, "version"),
        ),
        framework=FrameworkSelection(
            frontend=_require_string(framework, "frontend"),
            domain=_require_string(framework, "domain"),
            runtime=_require_string(framework, "runtime"),
            preset=_require_string(framework, "preset"),
        ),
        surface=SurfaceConfig(
            shell=_require_string(surface, "shell"),
            layout_variant=_require_string(surface, "layout_variant"),
            entry_mode=_require_string(surface, "entry_mode"),
            result_mode=_require_string(surface, "result_mode"),
            density=_require_string(surface, "density"),
            copy=SurfaceCopyConfig(
                app_name=_require_string(surface_copy, "app_name"),
                tagline=_require_string(surface_copy, "tagline"),
                capture_hint=_require_string(surface_copy, "capture_hint"),
                empty_title=_require_string(surface_copy, "empty_title"),
                empty_copy=_require_string(surface_copy, "empty_copy"),
                processing_title=_require_string(surface_copy, "processing_title"),
                processing_copy=_require_string(surface_copy, "processing_copy"),
            ),
        ),
        visual=VisualConfig(
            brand=_require_string(visual, "brand"),
            accent=_require_string(visual, "accent"),
            surface_preset=_require_string(visual, "surface_preset"),
            radius_scale=_require_string(visual, "radius_scale"),
            shadow_level=_require_string(visual, "shadow_level"),
            font_scale=_require_string(visual, "font_scale"),
        ),
        a11y=A11yConfig(
            reading_order=_require_string_tuple(a11y, "reading_order"),
            keyboard_nav=_require_string_tuple(a11y, "keyboard_nav"),
            announcements=_require_string_tuple(a11y, "announcements"),
        ),
        desktop=DesktopConfig(
            platforms=_require_string_tuple(desktop, "platforms"),
            entry_points=_require_string_tuple(desktop, "entry_points"),
            single_instance=_require_bool(desktop, "single_instance"),
            permissions=_require_string_tuple(desktop, "permissions"),
            degrade_policy=_require_string(desktop, "degrade_policy"),
            hotkey_behavior=_require_string(desktop, "hotkey_behavior"),
            window_strategy=_require_string(desktop, "window_strategy"),
            focus_restore=_require_bool(desktop, "focus_restore"),
        ),
        capture=CaptureConfig(
            modes=_require_string_tuple(capture, "modes"),
            selection_shape=_require_string(capture, "selection_shape"),
            cancel_methods=_require_string_tuple(capture, "cancel_methods"),
            include_cursor=_require_bool(capture, "include_cursor"),
            multi_display=_require_bool(capture, "multi_display"),
            high_dpi=_require_bool(capture, "high_dpi"),
            session_policy=_require_string(capture, "session_policy"),
            image_format=_require_string(capture, "image_format"),
        ),
        pipeline=PipelineConfig(
            source_languages=_require_string_tuple(pipeline, "source_languages"),
            target_language=_require_string(pipeline, "target_language"),
            deliverables=_require_string_tuple(pipeline, "deliverables"),
            fallback_policy=_require_string(pipeline, "fallback_policy"),
            timeout_budget_ms=_require_int(pipeline, "timeout_budget_ms"),
            latency_budget_p95_ms=_require_int(pipeline, "latency_budget_p95_ms"),
            ocr_confidence_visible=_require_bool(pipeline, "ocr_confidence_visible"),
        ),
        presentation=PresentationConfig(
            panel_variant=_require_string(presentation, "panel_variant"),
            show_source_text=_require_bool(presentation, "show_source_text"),
            show_translated_text=_require_bool(presentation, "show_translated_text"),
            show_status=_require_bool(presentation, "show_status"),
            show_error_reason=_require_bool(presentation, "show_error_reason"),
            default_pinned=_require_bool(presentation, "default_pinned"),
            actions=_require_string_tuple(presentation, "actions"),
            auto_hide=_require_string(presentation, "auto_hide"),
            copy=PresentationCopyConfig(
                copy_success=_require_string(presentation_copy, "copy_success"),
                retry_label=_require_string(presentation_copy, "retry_label"),
                close_label=_require_string(presentation_copy, "close_label"),
                recapture_label=_require_string(presentation_copy, "recapture_label"),
                failure_title=_require_string(presentation_copy, "failure_title"),
                empty_translation=_require_string(presentation_copy, "empty_translation"),
            ),
        ),
        governance=GovernanceConfig(
            event_scope=_require_string_tuple(governance, "event_scope"),
            audit_fields=_require_string_tuple(governance, "audit_fields"),
            privacy_mode=_require_string(governance, "privacy_mode"),
            update_channel=_require_string(governance, "update_channel"),
            compat_matrix=_require_string_tuple(governance, "compat_matrix"),
            offline_policy=_require_string(governance, "offline_policy"),
            capture_p95_ms=_require_int(governance, "capture_p95_ms"),
            ocr_p95_ms=_require_int(governance, "ocr_p95_ms"),
            translation_p95_ms=_require_int(governance, "translation_p95_ms"),
            render_p95_ms=_require_int(governance, "render_p95_ms"),
        ),
    )


def _load_implementation_config(implementation_config_path: Path) -> AitransImplementationConfig:
    data = _read_toml_file(implementation_config_path)
    desktop_runtime = _require_table(data, "desktop_runtime")
    capture_runtime = _require_table(data, "capture_runtime")
    providers = _require_table(data, "providers")
    presentation_runtime = _require_table(data, "presentation_runtime")
    release = _require_table(data, "release")
    evidence = _require_table(data, "evidence")
    artifacts = _require_table(data, "artifacts")
    return AitransImplementationConfig(
        desktop_runtime=DesktopRuntimeConfig(
            host=_require_string(desktop_runtime, "host"),
            shell_profile=_require_string(desktop_runtime, "shell_profile"),
            preload_bridge=_require_string(desktop_runtime, "preload_bridge"),
            window_state_store=_require_string(desktop_runtime, "window_state_store"),
        ),
        capture_runtime=CaptureRuntimeConfig(
            frame_source=_require_string(capture_runtime, "frame_source"),
            bitmap_pipeline=_require_string(capture_runtime, "bitmap_pipeline"),
            coordinate_profile=_require_string(capture_runtime, "coordinate_profile"),
        ),
        providers=ProvidersConfig(
            ocr_chain=_require_string_tuple(providers, "ocr_chain"),
            ocr_distribution=_require_string(providers, "ocr_distribution"),
            ocr_dev_fallback=_require_string(providers, "ocr_dev_fallback"),
            translation_chain=_require_string_tuple(providers, "translation_chain"),
            translation_api=_require_string(providers, "translation_api"),
            translation_model=_require_string(providers, "translation_model"),
            translation_endpoint_profile=_require_string(providers, "translation_endpoint_profile"),
            translation_endpoint_source=_require_string(providers, "translation_endpoint_source"),
            source_language_detection=_require_string(providers, "source_language_detection"),
            secret_source=_require_string(providers, "secret_source"),
        ),
        presentation_runtime=PresentationRuntimeConfig(
            renderer=_require_string(presentation_runtime, "renderer"),
            ui_framework=_require_string(presentation_runtime, "ui_framework"),
            overlay_profile=_require_string(presentation_runtime, "overlay_profile"),
            clipboard_bridge=_require_string(presentation_runtime, "clipboard_bridge"),
        ),
        release=ReleaseConfig(
            targets=_require_string_tuple(release, "targets"),
            package_formats=_require_string_tuple(release, "package_formats"),
            auto_update=_require_bool(release, "auto_update"),
            channel=_require_string(release, "channel"),
        ),
        evidence=EvidenceConfig(
            product_spec_endpoint=_require_string(evidence, "product_spec_endpoint"),
            runtime_bundle_endpoint=_require_string(evidence, "runtime_bundle_endpoint"),
        ),
        artifacts=ArtifactConfig(
            framework_ir_json=_require_string(artifacts, "framework_ir_json"),
            product_spec_json=_require_string(artifacts, "product_spec_json"),
            implementation_bundle_py=_require_string(artifacts, "implementation_bundle_py"),
            generation_manifest_json=_require_string(artifacts, "generation_manifest_json"),
        ),
    )


def _build_visual_tokens(visual: VisualConfig) -> dict[str, str]:
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
    return {
        **surface_tokens,
        "accent": visual.accent,
        "radius": radius_value,
        "shadow": shadow_value,
        "font_body": font_values["body"],
        "font_title": font_values["title"],
    }


def _build_execution_contract(project: AitransProject) -> dict[str, Any]:
    return {
        "entry": {
            "platforms": list(project.desktop.platforms),
            "entry_points": list(project.desktop.entry_points),
            "permissions": list(project.desktop.permissions),
            "single_instance": project.desktop.single_instance,
        },
        "workflow": [
            {
                "stage_id": "capture",
                "inputs": list(project.desktop.entry_points),
                "outputs": ["image_object", "capture_session_id"],
                "p95_budget_ms": project.governance.capture_p95_ms,
            },
            {
                "stage_id": "ocr",
                "inputs": ["image_object"],
                "outputs": ["source_text", "source_language", "ocr_metadata"],
                "providers": list(project.implementation.providers.ocr_chain),
                "p95_budget_ms": project.governance.ocr_p95_ms,
            },
            {
                "stage_id": "translation",
                "inputs": ["source_text", "source_language"],
                "outputs": ["translated_text", "translation_metadata"],
                "providers": list(project.implementation.providers.translation_chain),
                "p95_budget_ms": project.governance.translation_p95_ms,
            },
            {
                "stage_id": "presentation",
                "inputs": ["source_text", "translated_text", "stage_status", "error_origin"],
                "outputs": ["floating_panel_state"],
                "actions": list(project.presentation.actions),
                "p95_budget_ms": project.governance.render_p95_ms,
            },
        ],
        "fallback": {
            "policy": project.pipeline.fallback_policy,
            "timeout_budget_ms": project.pipeline.timeout_budget_ms,
        },
        "delivery": {
            "panel_variant": project.presentation.panel_variant,
            "show_source_text": project.presentation.show_source_text,
            "show_translated_text": project.presentation.show_translated_text,
            "auto_hide": project.presentation.auto_hide,
        },
        "governance": {
            "event_scope": list(project.governance.event_scope),
            "audit_fields": list(project.governance.audit_fields),
            "privacy_mode": project.governance.privacy_mode,
            "offline_policy": project.governance.offline_policy,
            "compat_matrix": list(project.governance.compat_matrix),
        },
    }


def _rule_result(rule_id: str, passed: bool, reasons: list[str]) -> dict[str, Any]:
    return {
        "rule_id": rule_id,
        "passed": passed,
        "reasons": reasons,
    }


def _collect_validation_reports(project: AitransProject) -> dict[str, Any]:
    required_actions = {"copy_translation", "close_panel", "recapture"}
    required_deliverables = {"source_text", "translated_text", "stage_status", "error_origin"}
    required_events = {"capture", "ocr", "translation", "render"}

    results = [
        _rule_result(
            "AT1",
            set(project.desktop.entry_points) == {"tray", "global_shortcut"} and project.desktop.single_instance,
            [] if set(project.desktop.entry_points) == {"tray", "global_shortcut"} and project.desktop.single_instance else [
                "desktop.entry_points must include tray and global_shortcut, and desktop.single_instance must stay true"
            ],
        ),
        _rule_result(
            "AT2",
            "region" in project.capture.modes and project.capture.multi_display and project.capture.high_dpi,
            [] if "region" in project.capture.modes and project.capture.multi_display and project.capture.high_dpi else [
                "capture must support region mode, multi_display, and high_dpi"
            ],
        ),
        _rule_result(
            "AT3",
            required_deliverables.issubset(project.pipeline.deliverables)
            and project.governance.ocr_p95_ms + project.governance.translation_p95_ms <= project.pipeline.timeout_budget_ms,
            [] if required_deliverables.issubset(project.pipeline.deliverables)
            and project.governance.ocr_p95_ms + project.governance.translation_p95_ms <= project.pipeline.timeout_budget_ms else [
                "pipeline.deliverables must include source_text, translated_text, stage_status, error_origin",
                "ocr + translation p95 budgets must stay within pipeline.timeout_budget_ms",
            ],
        ),
        _rule_result(
            "AT4",
            required_actions.issubset(project.presentation.actions)
            and project.presentation.show_source_text
            and project.presentation.show_translated_text,
            [] if required_actions.issubset(project.presentation.actions)
            and project.presentation.show_source_text
            and project.presentation.show_translated_text else [
                "presentation must expose copy_translation, close_panel, recapture and render both source/translated text"
            ],
        ),
        _rule_result(
            "AT5",
            required_events.issubset(project.governance.event_scope)
            and any(item.startswith("windows") for item in project.governance.compat_matrix)
            and any(item.startswith("macos") for item in project.governance.compat_matrix),
            [] if required_events.issubset(project.governance.event_scope)
            and any(item.startswith("windows") for item in project.governance.compat_matrix)
            and any(item.startswith("macos") for item in project.governance.compat_matrix) else [
                "governance.event_scope must cover capture/ocr/translation/render and compat_matrix must declare both Windows and macOS"
            ],
        ),
    ]

    passed_count = sum(1 for item in results if item["passed"])
    summary = {
        "passed": passed_count == len(results),
        "passed_count": passed_count,
        "rule_count": len(results),
        "rules": results,
    }
    return {
        "aitrans": summary,
        "overall": {
            "passed": summary["passed"],
            "passed_count": passed_count,
            "rule_count": len(results),
        },
    }


def _raise_on_validation_failures(reports: dict[str, Any]) -> None:
    scope = reports.get("aitrans")
    if not isinstance(scope, dict):
        return
    errors: list[str] = []
    for item in scope.get("rules", []):
        if item.get("passed"):
            continue
        reasons = ", ".join(item.get("reasons", [])) or "unknown rule failure"
        errors.append(f"aitrans.{item.get('rule_id')}: {reasons}")
    if errors:
        raise ValueError("framework rule validation failed: " + " | ".join(errors))


def _validate_product_spec(
    product_spec: AitransProductSpec,
    frontend_ir: FrameworkModuleIR,
    domain_ir: FrameworkModuleIR,
    runtime_ir: FrameworkModuleIR,
) -> None:
    if product_spec.metadata.template != SUPPORTED_PROJECT_TEMPLATE:
        raise ValueError(f"unsupported project.template: {product_spec.metadata.template}")
    if frontend_ir.level != 2:
        raise ValueError("framework.frontend must point to an L2 frontend standard module")
    if domain_ir.module_id != "aitrans.L3.M0":
        raise ValueError("framework.domain must point to framework/aitrans/L3-M0-桌面截图翻译框架.md")
    if runtime_ir.module_id != "runtime_env.L0.M0":
        raise ValueError("framework.runtime must point to framework/runtime_env/L0-M0-运行环境识别模块.md")
    if product_spec.surface.entry_mode != "tray_and_shortcut":
        raise ValueError("surface.entry_mode must stay tray_and_shortcut")
    if set(product_spec.desktop.entry_points) != {"tray", "global_shortcut"}:
        raise ValueError("desktop.entry_points must include tray and global_shortcut")
    if "region" not in product_spec.capture.modes:
        raise ValueError("capture.modes must include region")
    if product_spec.pipeline.target_language not in {"zh-Hans", "en", "ja"}:
        raise ValueError("pipeline.target_language must stay within supported product targets")
    if product_spec.pipeline.latency_budget_p95_ms <= 0 or product_spec.pipeline.timeout_budget_ms <= 0:
        raise ValueError("pipeline latency budgets must be positive")
    if not product_spec.presentation.show_translated_text:
        raise ValueError("presentation.show_translated_text must stay true")
    if product_spec.governance.render_p95_ms > product_spec.pipeline.latency_budget_p95_ms:
        raise ValueError("governance.render_p95_ms must stay within total pipeline latency budget")


def _validate_implementation_config(
    implementation: AitransImplementationConfig,
    product_spec: AitransProductSpec,
) -> None:
    if implementation.desktop_runtime.host not in {"electron", "tauri"}:
        raise ValueError("desktop_runtime.host must be electron or tauri")
    if not implementation.providers.ocr_chain or not implementation.providers.translation_chain:
        raise ValueError("providers.ocr_chain and providers.translation_chain must be non-empty")
    if implementation.providers.ocr_distribution not in {"bundle_with_app", "packaged_system_capability"}:
        raise ValueError("providers.ocr_distribution must be bundle_with_app or packaged_system_capability")
    if implementation.providers.ocr_dev_fallback not in {"allow_env_binary_path", "none"}:
        raise ValueError("providers.ocr_dev_fallback must be allow_env_binary_path or none")
    if implementation.providers.translation_api not in {"openai_compatible", "openai_responses_v1", "stub_only"}:
        raise ValueError("providers.translation_api must be openai_compatible, openai_responses_v1 or stub_only")
    if implementation.providers.translation_endpoint_profile not in {"openai_compatible"}:
        raise ValueError("providers.translation_endpoint_profile must be openai_compatible")
    if implementation.providers.translation_endpoint_source not in {"env_or_local_gateway", "env_then_official_default"}:
        raise ValueError(
            "providers.translation_endpoint_source must be env_or_local_gateway or env_then_official_default",
        )
    if implementation.providers.secret_source not in {
        "setup_ui_managed_runtime_store_or_env",
        "windows_credential_manager_or_env",
    }:
        raise ValueError(
            "providers.secret_source must be setup_ui_managed_runtime_store_or_env or windows_credential_manager_or_env",
        )
    if not implementation.evidence.product_spec_endpoint.startswith("/api/"):
        raise ValueError("evidence.product_spec_endpoint must be an API path")
    if not implementation.evidence.runtime_bundle_endpoint.startswith("/api/"):
        raise ValueError("evidence.runtime_bundle_endpoint must be an API path")
    if implementation.release.auto_update and implementation.release.channel != product_spec.governance.update_channel:
        raise ValueError("release.channel must match governance.update_channel when auto_update is enabled")
    if implementation.presentation_runtime.ui_framework not in {"vanilla_html", "vue3"}:
        raise ValueError("presentation_runtime.ui_framework must be vanilla_html or vue3")
    if implementation.presentation_runtime.ui_framework == "vue3" and implementation.presentation_runtime.renderer != "floating_panel_vue_vite_v1":
        raise ValueError("vue3 panel runtime must use floating_panel_vue_vite_v1")


def _build_generated_artifact_payloads(project: AitransProject) -> dict[str, str]:
    generated_artifacts = project.generated_artifacts
    if generated_artifacts is None:
        raise ValueError("generated_artifacts must be populated before payload generation")

    framework_ir_payload = {
        "primary_modules": [
            project.frontend_ir.to_dict(),
            project.domain_ir.to_dict(),
            project.runtime_ir.to_dict(),
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
                "entry": "project_runtime.aitrans.materialize_aitrans_project",
                "discipline": (
                    "project behavior is derived from framework markdown, product spec, and implementation config; "
                    "generated code must not be edited directly"
                ),
            },
            "framework_inputs": {
                "frontend": project.frontend_ir.path,
                "domain": project.domain_ir.path,
                "runtime": project.runtime_ir.path,
                "resolved_modules": [item.path for item in project.resolved_modules],
            },
            "generated_files": {
                "framework_ir_json": generated_artifacts.framework_ir_json,
                "product_spec_json": generated_artifacts.product_spec_json,
                "implementation_bundle_py": generated_artifacts.implementation_bundle_py,
                "generation_manifest_json": generated_artifacts.generation_manifest_json,
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


def _compile_project(
    product_spec: AitransProductSpec,
    implementation: AitransImplementationConfig,
) -> AitransProject:
    frontend_ir = _resolve_framework_module(product_spec.framework.frontend)
    domain_ir = _resolve_framework_module(product_spec.framework.domain)
    runtime_ir = _resolve_framework_module(product_spec.framework.runtime)
    _validate_product_spec(product_spec, frontend_ir, domain_ir, runtime_ir)
    _validate_implementation_config(implementation, product_spec)
    project = AitransProject(
        product_spec_file=product_spec.product_spec_file,
        implementation_config_file=_relative_path(
            _implementation_config_path_for(_normalize_project_path(product_spec.product_spec_file))
        ),
        metadata=product_spec.metadata,
        framework=product_spec.framework,
        surface=product_spec.surface,
        visual=product_spec.visual,
        a11y=product_spec.a11y,
        desktop=product_spec.desktop,
        capture=product_spec.capture,
        pipeline=product_spec.pipeline,
        presentation=product_spec.presentation,
        governance=product_spec.governance,
        implementation=implementation,
        frontend_ir=frontend_ir,
        domain_ir=domain_ir,
        runtime_ir=runtime_ir,
        resolved_modules=_collect_framework_closure(frontend_ir, domain_ir, runtime_ir),
        execution_contract={},
        validation_reports={},
    )
    project = replace(project, execution_contract=_build_execution_contract(project))
    validation_reports = _collect_validation_reports(project)
    _raise_on_validation_failures(validation_reports)
    return replace(project, validation_reports=validation_reports)


def load_aitrans_project(
    product_spec_file: str | Path = DEFAULT_AITRANS_PRODUCT_SPEC_FILE,
) -> AitransProject:
    product_spec_path = _normalize_project_path(product_spec_file)
    implementation_config_path = _implementation_config_path_for(product_spec_path)
    product_spec = _load_product_spec(product_spec_path)
    implementation = _load_implementation_config(implementation_config_path)
    return _compile_project(product_spec, implementation)


def materialize_aitrans_project(
    product_spec_file: str | Path = DEFAULT_AITRANS_PRODUCT_SPEC_FILE,
    output_dir: str | Path | None = None,
) -> AitransProject:
    product_spec_path = _normalize_project_path(product_spec_file)
    project = load_aitrans_project(product_spec_path)
    generated_dir = product_spec_path.parent / "generated"
    output_path = _normalize_project_path(output_dir) if output_dir is not None else generated_dir
    output_path.mkdir(parents=True, exist_ok=True)

    artifact_names = project.implementation.artifacts
    framework_ir_path = output_path / artifact_names.framework_ir_json
    product_spec_path_json = output_path / artifact_names.product_spec_json
    implementation_bundle_path = output_path / artifact_names.implementation_bundle_py
    generation_manifest_path = output_path / artifact_names.generation_manifest_json
    project = replace(
        project,
        generated_artifacts=GeneratedArtifactPaths(
            directory=_relative_path(generated_dir),
            framework_ir_json=_relative_path(generated_dir / artifact_names.framework_ir_json),
            product_spec_json=_relative_path(generated_dir / artifact_names.product_spec_json),
            implementation_bundle_py=_relative_path(generated_dir / artifact_names.implementation_bundle_py),
            generation_manifest_json=_relative_path(generated_dir / artifact_names.generation_manifest_json),
        ),
    )
    payloads = _build_generated_artifact_payloads(project)
    framework_ir_path.write_text(payloads["framework_ir_json"], encoding="utf-8")
    product_spec_path_json.write_text(payloads["product_spec_json"], encoding="utf-8")
    implementation_bundle_path.write_text(payloads["implementation_bundle_py"], encoding="utf-8")
    generation_manifest_path.write_text(payloads["generation_manifest_json"], encoding="utf-8")

    return project
