from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import tomllib
from typing import Any


CONTRACT_FILE = Path(__file__).with_name("knowledge_base_contract.toml")


@dataclass(frozen=True)
class ContractAction:
    action_id: str
    boundary: str

    def to_dict(self) -> dict[str, str]:
        return {"action_id": self.action_id, "boundary": self.boundary}


@dataclass(frozen=True)
class ContractStateChannel:
    state_id: str
    sticky: bool | None = None
    sticky_from_context: str | None = None

    def resolve(self, *, sticky_document: bool) -> dict[str, Any]:
        if self.sticky_from_context == "sticky_document":
            return {"state_id": self.state_id, "sticky": sticky_document}
        if self.sticky is None:
            raise ValueError(f"state channel {self.state_id} must define sticky or sticky_from_context")
        return {"state_id": self.state_id, "sticky": self.sticky}


@dataclass(frozen=True)
class ContractFlowStage:
    stage_id: str
    depends_on: tuple[str, ...]
    produces: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage_id": self.stage_id,
            "depends_on": list(self.depends_on),
            "produces": list(self.produces),
        }


@dataclass(frozen=True)
class SurfacePreset:
    bg: str
    panel: str
    panel_soft: str
    ink: str
    muted: str
    line: str


@dataclass(frozen=True)
class FontScalePreset:
    body: str
    title: str
    hero: str


@dataclass(frozen=True)
class DensityPreset:
    shell_gap: str
    shell_padding: str
    panel_gap: str


@dataclass(frozen=True)
class StyleProfileContract:
    message_width: str
    surface_presets: dict[str, SurfacePreset]
    radius_scales: dict[str, str]
    shadow_levels: dict[str, str]
    font_scales: dict[str, FontScalePreset]
    sidebar_widths: dict[str, str]
    drawer_widths: dict[str, str]
    density_presets: dict[str, DensityPreset]

    def resolve_visual_tokens(
        self,
        *,
        surface_preset: str,
        radius_scale: str,
        shadow_level: str,
        font_scale: str,
        sidebar_width: str,
        density: str,
        accent: str,
        brand: str,
        preview_mode: str,
        preview_variant: str,
    ) -> dict[str, str]:
        palette = self.surface_presets.get(surface_preset)
        if palette is None:
            raise ValueError(f"unsupported visual.surface_preset: {surface_preset}")
        radius = self.radius_scales.get(radius_scale)
        if radius is None:
            raise ValueError(f"unsupported visual.radius_scale: {radius_scale}")
        shadow = self.shadow_levels.get(shadow_level)
        if shadow is None:
            raise ValueError(f"unsupported visual.shadow_level: {shadow_level}")
        font = self.font_scales.get(font_scale)
        if font is None:
            raise ValueError(f"unsupported visual.font_scale: {font_scale}")
        sidebar = self.sidebar_widths.get(sidebar_width)
        if sidebar is None:
            raise ValueError(f"unsupported surface.sidebar_width: {sidebar_width}")
        drawer = self.drawer_widths.get(sidebar_width)
        if drawer is None:
            raise ValueError(f"unsupported drawer width preset for surface.sidebar_width: {sidebar_width}")
        density_profile = self.density_presets.get(density)
        if density_profile is None:
            raise ValueError(f"unsupported surface.density: {density}")
        return {
            "bg": palette.bg,
            "panel": palette.panel,
            "panel_soft": palette.panel_soft,
            "ink": palette.ink,
            "muted": palette.muted,
            "line": palette.line,
            "accent": accent,
            "accent_soft": f"{accent}22",
            "radius": radius,
            "brand": brand,
            "shadow": shadow,
            "font_body": font.body,
            "font_title": font.title,
            "font_hero": font.hero,
            "message_width": self.message_width,
            "sidebar_width": sidebar,
            "drawer_width": drawer,
            "shell_gap": density_profile.shell_gap,
            "shell_padding": density_profile.shell_padding,
            "panel_gap": density_profile.panel_gap,
            "preview_mode": preview_mode,
            "preview_variant": preview_variant,
        }


@dataclass(frozen=True)
class KnowledgeBaseTemplateContract:
    template_id: str
    required_surface_shell: str
    required_layout_variant: str
    required_preview_mode: str
    required_library_source_types: frozenset[str]
    required_library_metadata_fields: frozenset[str]
    required_library_default_focus: str
    required_preview_anchor_mode: str
    required_preview_variant: str
    preview_show_toc_required: bool
    required_chat_mode: str
    required_chat_citation_style: str
    required_return_targets: tuple[str, ...]
    return_anchor_restore_required: bool
    supported_citation_card_variants: frozenset[str]
    required_reading_order: tuple[str, ...]
    supported_frontend_renderers: frozenset[str]
    supported_frontend_style_profiles: frozenset[str]
    supported_frontend_script_profiles: frozenset[str]
    supported_backend_renderers: frozenset[str]
    supported_backend_transports: frozenset[str]
    supported_backend_retrieval_strategies: frozenset[str]
    style_profiles: StyleProfileContract
    shell_regions: tuple[str, ...]
    secondary_pages: tuple[str, ...]
    chat_home_slots: tuple[str, ...]
    required_frontend_page_ids: tuple[str, ...]
    drawer_sections: tuple[str, ...]
    surface_composition_sidebar: tuple[str, ...]
    surface_composition_main: tuple[str, ...]
    surface_composition_overlay: tuple[str, ...]
    required_surface_region_ids: tuple[str, ...]
    supported_chat_bubble_variants: frozenset[str]
    supported_chat_composer_variants: frozenset[str]
    frontend_base_interaction_actions: tuple[ContractAction, ...]
    frontend_optional_create_action_id: str
    frontend_optional_create_action_boundary: str
    frontend_optional_delete_action_id: str
    frontend_optional_delete_action_boundary: str
    frontend_state_channels: tuple[ContractStateChannel, ...]
    workbench_region_ids: tuple[str, ...]
    workbench_base_library_actions: tuple[str, ...]
    workbench_citation_query_keys: tuple[str, ...]
    workbench_optional_create_action_id: str
    workbench_optional_delete_action_id: str
    workbench_flow: tuple[ContractFlowStage, ...]

    def frontend_interaction_actions(self, *, allow_create: bool, allow_delete: bool) -> tuple[dict[str, str], ...]:
        items = [action.to_dict() for action in self.frontend_base_interaction_actions]
        if allow_create:
            items.append(
                {
                    "action_id": self.frontend_optional_create_action_id,
                    "boundary": self.frontend_optional_create_action_boundary,
                }
            )
        if allow_delete:
            items.append(
                {
                    "action_id": self.frontend_optional_delete_action_id,
                    "boundary": self.frontend_optional_delete_action_boundary,
                }
            )
        return tuple(items)

    def frontend_interaction_action_ids(self, *, allow_create: bool, allow_delete: bool) -> tuple[str, ...]:
        return tuple(
            item["action_id"] for item in self.frontend_interaction_actions(allow_create=allow_create, allow_delete=allow_delete)
        )

    def resolve_state_channels(self, *, sticky_document: bool) -> tuple[dict[str, Any], ...]:
        return tuple(item.resolve(sticky_document=sticky_document) for item in self.frontend_state_channels)

    def workbench_library_actions(self, *, allow_create: bool, allow_delete: bool) -> tuple[str, ...]:
        items = list(self.workbench_base_library_actions)
        if allow_create:
            items.append(self.workbench_optional_create_action_id)
        if allow_delete:
            items.append(self.workbench_optional_delete_action_id)
        return tuple(items)

    def workbench_flow_dicts(self) -> tuple[dict[str, Any], ...]:
        return tuple(item.to_dict() for item in self.workbench_flow)

    def required_return_target_set(self) -> frozenset[str]:
        return frozenset(self.required_return_targets)


def _require_table(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"knowledge-base contract missing table: {key}")
    return value


def _require_string(parent: dict[str, Any], key: str) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"knowledge-base contract missing string: {key}")
    return value.strip()


def _require_bool(parent: dict[str, Any], key: str) -> bool:
    value = parent.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"knowledge-base contract missing bool: {key}")
    return value


def _require_string_tuple(parent: dict[str, Any], key: str) -> tuple[str, ...]:
    value = parent.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"knowledge-base contract missing string list: {key}")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"knowledge-base contract {key} must contain non-empty strings")
        items.append(item.strip())
    return tuple(items)


def _require_action_list(parent: dict[str, Any], key: str) -> tuple[ContractAction, ...]:
    value = parent.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"knowledge-base contract missing action list: {key}")
    actions: list[ContractAction] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"knowledge-base contract {key} must contain objects")
        actions.append(ContractAction(action_id=_require_string(item, "action_id"), boundary=_require_string(item, "boundary")))
    return tuple(actions)


def _require_state_channel_list(parent: dict[str, Any], key: str) -> tuple[ContractStateChannel, ...]:
    value = parent.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"knowledge-base contract missing state channel list: {key}")
    channels: list[ContractStateChannel] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"knowledge-base contract {key} must contain objects")
        sticky = item.get("sticky")
        sticky_from_context = item.get("sticky_from_context")
        if sticky is not None and not isinstance(sticky, bool):
            raise ValueError(f"knowledge-base contract {key}.sticky must be bool when provided")
        if sticky_from_context is not None and (not isinstance(sticky_from_context, str) or not sticky_from_context.strip()):
            raise ValueError(f"knowledge-base contract {key}.sticky_from_context must be string when provided")
        channels.append(
            ContractStateChannel(
                state_id=_require_string(item, "state_id"),
                sticky=sticky if isinstance(sticky, bool) else None,
                sticky_from_context=sticky_from_context.strip() if isinstance(sticky_from_context, str) else None,
            )
        )
    return tuple(channels)


def _require_flow_stage_list(parent: dict[str, Any], key: str) -> tuple[ContractFlowStage, ...]:
    value = parent.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"knowledge-base contract missing flow stage list: {key}")
    stages: list[ContractFlowStage] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"knowledge-base contract {key} must contain objects")
        stages.append(
            ContractFlowStage(
                stage_id=_require_string(item, "stage_id"),
                depends_on=_require_string_tuple(item, "depends_on") if item.get("depends_on") else (),
                produces=_require_string_tuple(item, "produces"),
            )
        )
    return tuple(stages)


def _require_string_mapping(parent: dict[str, Any], key: str) -> dict[str, str]:
    table = _require_table(parent, key)
    mapping: dict[str, str] = {}
    for item_key, item_value in table.items():
        if not isinstance(item_key, str) or not item_key.strip():
            raise ValueError(f"knowledge-base contract {key} must use non-empty string keys")
        if not isinstance(item_value, str) or not item_value.strip():
            raise ValueError(f"knowledge-base contract {key}.{item_key} must be a non-empty string")
        mapping[item_key.strip()] = item_value.strip()
    return mapping


def _require_surface_presets(parent: dict[str, Any], key: str) -> dict[str, SurfacePreset]:
    table = _require_table(parent, key)
    presets: dict[str, SurfacePreset] = {}
    for preset_name, preset_payload in table.items():
        if not isinstance(preset_name, str) or not preset_name.strip():
            raise ValueError(f"knowledge-base contract {key} must use non-empty string keys")
        if not isinstance(preset_payload, dict):
            raise ValueError(f"knowledge-base contract {key}.{preset_name} must be an object")
        presets[preset_name.strip()] = SurfacePreset(
            bg=_require_string(preset_payload, "bg"),
            panel=_require_string(preset_payload, "panel"),
            panel_soft=_require_string(preset_payload, "panel_soft"),
            ink=_require_string(preset_payload, "ink"),
            muted=_require_string(preset_payload, "muted"),
            line=_require_string(preset_payload, "line"),
        )
    return presets


def _require_font_scales(parent: dict[str, Any], key: str) -> dict[str, FontScalePreset]:
    table = _require_table(parent, key)
    scales: dict[str, FontScalePreset] = {}
    for scale_name, scale_payload in table.items():
        if not isinstance(scale_name, str) or not scale_name.strip():
            raise ValueError(f"knowledge-base contract {key} must use non-empty string keys")
        if not isinstance(scale_payload, dict):
            raise ValueError(f"knowledge-base contract {key}.{scale_name} must be an object")
        scales[scale_name.strip()] = FontScalePreset(
            body=_require_string(scale_payload, "body"),
            title=_require_string(scale_payload, "title"),
            hero=_require_string(scale_payload, "hero"),
        )
    return scales


def _require_density_presets(parent: dict[str, Any], key: str) -> dict[str, DensityPreset]:
    table = _require_table(parent, key)
    presets: dict[str, DensityPreset] = {}
    for density_name, density_payload in table.items():
        if not isinstance(density_name, str) or not density_name.strip():
            raise ValueError(f"knowledge-base contract {key} must use non-empty string keys")
        if not isinstance(density_payload, dict):
            raise ValueError(f"knowledge-base contract {key}.{density_name} must be an object")
        presets[density_name.strip()] = DensityPreset(
            shell_gap=_require_string(density_payload, "shell_gap"),
            shell_padding=_require_string(density_payload, "shell_padding"),
            panel_gap=_require_string(density_payload, "panel_gap"),
        )
    return presets


@lru_cache(maxsize=1)
def load_knowledge_base_template_contract() -> KnowledgeBaseTemplateContract:
    with CONTRACT_FILE.open("rb") as fh:
        data = tomllib.load(fh)
    if not isinstance(data, dict):
        raise ValueError("knowledge-base contract must decode into an object")

    template_table = _require_table(data, "template")
    product_table = _require_table(data, "product")
    product_surface = _require_table(product_table, "surface")
    product_library = _require_table(product_table, "library")
    product_preview = _require_table(product_table, "preview")
    product_chat = _require_table(product_table, "chat")
    product_return = _require_table(product_table, "return")
    product_a11y = _require_table(product_table, "a11y")
    implementation_table = _require_table(data, "implementation")
    style_profiles_table = _require_table(implementation_table, "style_profiles")
    frontend_table = _require_table(data, "frontend")
    workbench_table = _require_table(data, "workbench")

    return KnowledgeBaseTemplateContract(
        template_id=_require_string(template_table, "id"),
        required_surface_shell=_require_string(product_surface, "shell"),
        required_layout_variant=_require_string(product_surface, "layout_variant"),
        required_preview_mode=_require_string(product_surface, "preview_mode"),
        required_library_source_types=frozenset(_require_string_tuple(product_library, "required_source_types")),
        required_library_metadata_fields=frozenset(_require_string_tuple(product_library, "required_metadata_fields")),
        required_library_default_focus=_require_string(product_library, "default_focus"),
        required_preview_anchor_mode=_require_string(product_preview, "anchor_mode"),
        required_preview_variant=_require_string(product_preview, "preview_variant"),
        preview_show_toc_required=_require_bool(product_preview, "show_toc_required"),
        required_chat_mode=_require_string(product_chat, "mode"),
        required_chat_citation_style=_require_string(product_chat, "citation_style"),
        required_return_targets=_require_string_tuple(product_return, "required_targets"),
        return_anchor_restore_required=_require_bool(product_return, "anchor_restore_required"),
        supported_citation_card_variants=frozenset(_require_string_tuple(product_return, "supported_citation_card_variants")),
        required_reading_order=_require_string_tuple(product_a11y, "reading_order"),
        supported_frontend_renderers=frozenset(_require_string_tuple(implementation_table, "supported_frontend_renderers")),
        supported_frontend_style_profiles=frozenset(
            _require_string_tuple(implementation_table, "supported_frontend_style_profiles")
        ),
        supported_frontend_script_profiles=frozenset(
            _require_string_tuple(implementation_table, "supported_frontend_script_profiles")
        ),
        supported_backend_renderers=frozenset(_require_string_tuple(implementation_table, "supported_backend_renderers")),
        supported_backend_transports=frozenset(_require_string_tuple(implementation_table, "supported_backend_transports")),
        supported_backend_retrieval_strategies=frozenset(
            _require_string_tuple(implementation_table, "supported_backend_retrieval_strategies")
        ),
        style_profiles=StyleProfileContract(
            message_width=_require_string(style_profiles_table, "message_width"),
            surface_presets=_require_surface_presets(style_profiles_table, "surface_presets"),
            radius_scales=_require_string_mapping(style_profiles_table, "radius_scales"),
            shadow_levels=_require_string_mapping(style_profiles_table, "shadow_levels"),
            font_scales=_require_font_scales(style_profiles_table, "font_scales"),
            sidebar_widths=_require_string_mapping(style_profiles_table, "sidebar_widths"),
            drawer_widths=_require_string_mapping(style_profiles_table, "drawer_widths"),
            density_presets=_require_density_presets(style_profiles_table, "density_presets"),
        ),
        shell_regions=_require_string_tuple(frontend_table, "shell_regions"),
        secondary_pages=_require_string_tuple(frontend_table, "secondary_pages"),
        chat_home_slots=_require_string_tuple(frontend_table, "chat_home_slots"),
        required_frontend_page_ids=_require_string_tuple(frontend_table, "required_page_ids"),
        drawer_sections=_require_string_tuple(frontend_table, "drawer_sections"),
        surface_composition_sidebar=_require_string_tuple(frontend_table, "surface_composition_sidebar"),
        surface_composition_main=_require_string_tuple(frontend_table, "surface_composition_main"),
        surface_composition_overlay=_require_string_tuple(frontend_table, "surface_composition_overlay"),
        required_surface_region_ids=_require_string_tuple(frontend_table, "required_surface_region_ids"),
        supported_chat_bubble_variants=frozenset(_require_string_tuple(frontend_table, "supported_chat_bubble_variants")),
        supported_chat_composer_variants=frozenset(
            _require_string_tuple(frontend_table, "supported_chat_composer_variants")
        ),
        frontend_base_interaction_actions=_require_action_list(frontend_table, "interaction_actions"),
        frontend_optional_create_action_id=_require_string(frontend_table, "optional_create_action_id"),
        frontend_optional_create_action_boundary=_require_string(frontend_table, "optional_create_action_boundary"),
        frontend_optional_delete_action_id=_require_string(frontend_table, "optional_delete_action_id"),
        frontend_optional_delete_action_boundary=_require_string(frontend_table, "optional_delete_action_boundary"),
        frontend_state_channels=_require_state_channel_list(frontend_table, "state_channels"),
        workbench_region_ids=_require_string_tuple(workbench_table, "required_region_ids"),
        workbench_base_library_actions=_require_string_tuple(workbench_table, "required_library_actions"),
        workbench_citation_query_keys=_require_string_tuple(workbench_table, "citation_query_keys"),
        workbench_optional_create_action_id=_require_string(workbench_table, "optional_create_action_id"),
        workbench_optional_delete_action_id=_require_string(workbench_table, "optional_delete_action_id"),
        workbench_flow=_require_flow_stage_list(workbench_table, "flow"),
    )
