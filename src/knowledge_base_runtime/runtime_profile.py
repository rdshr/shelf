from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any


@dataclass(frozen=True)
class RuntimeAction:
    action_id: str
    boundary: str

    def to_dict(self) -> dict[str, str]:
        return {"action_id": self.action_id, "boundary": self.boundary}


@dataclass(frozen=True)
class RuntimeStateChannel:
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
class RuntimeFlowStage:
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
class KnowledgeBaseRuntimeProfile:
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
    frontend_base_interaction_actions: tuple[RuntimeAction, ...]
    frontend_optional_create_action_id: str
    frontend_optional_create_action_boundary: str
    frontend_optional_delete_action_id: str
    frontend_optional_delete_action_boundary: str
    frontend_state_channels: tuple[RuntimeStateChannel, ...]
    workbench_region_ids: tuple[str, ...]
    workbench_base_library_actions: tuple[str, ...]
    workbench_citation_query_keys: tuple[str, ...]
    workbench_optional_create_action_id: str
    workbench_optional_delete_action_id: str
    workbench_flow: tuple[RuntimeFlowStage, ...]

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


@lru_cache(maxsize=1)
def load_knowledge_base_runtime_profile() -> KnowledgeBaseRuntimeProfile:
    return KnowledgeBaseRuntimeProfile(
        required_surface_shell="conversation_sidebar_shell",
        required_layout_variant="chatgpt_knowledge_client",
        required_preview_mode="drawer",
        required_library_source_types=frozenset({"markdown"}),
        required_library_metadata_fields=frozenset({"title"}),
        required_library_default_focus="current_knowledge_base",
        required_preview_anchor_mode="heading",
        required_preview_variant="citation_drawer",
        preview_show_toc_required=True,
        required_chat_mode="retrieval_stub",
        required_chat_citation_style="inline_refs",
        required_return_targets=("citation_drawer", "document_detail"),
        return_anchor_restore_required=True,
        supported_citation_card_variants=frozenset({"chips", "stacked", "compact"}),
        required_reading_order=(
            "conversation_sidebar",
            "chat_header",
            "message_stream",
            "chat_composer",
            "citation_drawer",
        ),
        supported_frontend_renderers=frozenset({"knowledge_chat_client_v1"}),
        supported_frontend_style_profiles=frozenset({"knowledge_chat_web_v1"}),
        supported_frontend_script_profiles=frozenset({"knowledge_chat_browser_v1"}),
        supported_backend_renderers=frozenset({"knowledge_chat_backend_v1"}),
        supported_backend_transports=frozenset({"http_json"}),
        supported_backend_retrieval_strategies=frozenset({"retrieval_stub"}),
        style_profiles=StyleProfileContract(
            message_width="820px",
            surface_presets={
                "sand": SurfacePreset(
                    bg="#f4efe5",
                    panel="#fffaf2",
                    panel_soft="#f7f1e7",
                    ink="#1b1f24",
                    muted="#6d6a65",
                    line="rgba(27, 31, 36, 0.12)",
                ),
                "light": SurfacePreset(
                    bg="#f6f7fb",
                    panel="#ffffff",
                    panel_soft="#f4f6fb",
                    ink="#111827",
                    muted="#667085",
                    line="rgba(17, 24, 39, 0.10)",
                ),
            },
            radius_scales={"sm": "12px", "md": "18px", "lg": "24px", "xl": "30px"},
            shadow_levels={
                "sm": "0 10px 28px rgba(15, 23, 42, 0.08)",
                "md": "0 18px 48px rgba(15, 23, 42, 0.10)",
                "lg": "0 24px 60px rgba(12, 17, 22, 0.30)",
            },
            font_scales={
                "sm": FontScalePreset(body="0.94rem", title="1.45rem", hero="1.55rem"),
                "md": FontScalePreset(body="1rem", title="1.6rem", hero="1.7rem"),
                "lg": FontScalePreset(body="1.05rem", title="1.72rem", hero="1.84rem"),
            },
            sidebar_widths={"compact": "280px", "md": "300px", "wide": "320px"},
            drawer_widths={"compact": "340px", "md": "370px", "wide": "390px"},
            density_presets={
                "compact": DensityPreset(shell_gap="14px", shell_padding="14px", panel_gap="12px"),
                "comfortable": DensityPreset(shell_gap="18px", shell_padding="18px", panel_gap="16px"),
            },
        ),
        shell_regions=("conversation_sidebar", "chat_main", "citation_drawer"),
        secondary_pages=("basketball_showcase", "knowledge_list", "knowledge_detail", "document_detail"),
        chat_home_slots=(
            "conversation_sidebar",
            "chat_header",
            "message_stream",
            "chat_composer",
            "citation_drawer",
            "knowledge_switch_dialog",
        ),
        required_frontend_page_ids=("chat_home", "knowledge_list", "knowledge_detail", "document_detail"),
        drawer_sections=("snippet", "source_context"),
        surface_composition_sidebar=("conversation_sidebar",),
        surface_composition_main=("chat_header", "message_stream", "chat_composer"),
        surface_composition_overlay=("citation_drawer", "knowledge_switch_dialog"),
        required_surface_region_ids=("conversation_sidebar", "chat_main", "citation_drawer", "knowledge_pages"),
        supported_chat_bubble_variants=frozenset({"assistant_soft", "assistant_minimal"}),
        supported_chat_composer_variants=frozenset({"chatgpt_compact", "expanded"}),
        frontend_base_interaction_actions=(
            RuntimeAction(action_id="start_new_chat", boundary="INTERACT"),
            RuntimeAction(action_id="select_session", boundary="INTERACT"),
            RuntimeAction(action_id="open_knowledge_switch", boundary="INTERACT"),
            RuntimeAction(action_id="search_documents", boundary="INTERACT"),
            RuntimeAction(action_id="select_document", boundary="INTERACT"),
            RuntimeAction(action_id="submit_chat", boundary="INTERACT"),
            RuntimeAction(action_id="open_citation_drawer", boundary="INTERACT"),
            RuntimeAction(action_id="browse_knowledge_bases", boundary="ROUTE"),
            RuntimeAction(action_id="open_basketball_showcase", boundary="ROUTE"),
            RuntimeAction(action_id="open_knowledge_base_detail", boundary="ROUTE"),
            RuntimeAction(action_id="open_document_detail", boundary="ROUTE"),
            RuntimeAction(action_id="return_from_citation", boundary="ROUTE"),
        ),
        frontend_optional_create_action_id="create_document",
        frontend_optional_create_action_boundary="INTERACT",
        frontend_optional_delete_action_id="delete_document",
        frontend_optional_delete_action_boundary="INTERACT",
        frontend_state_channels=(
            RuntimeStateChannel(state_id="current_conversation", sticky=True),
            RuntimeStateChannel(state_id="current_knowledge_base", sticky=True),
            RuntimeStateChannel(state_id="current_document", sticky_from_context="sticky_document"),
            RuntimeStateChannel(state_id="current_section", sticky=True),
            RuntimeStateChannel(state_id="citation_drawer_state", sticky=True),
            RuntimeStateChannel(state_id="streaming_reply", sticky=False),
        ),
        workbench_region_ids=(
            "conversation_sidebar",
            "chat_main",
            "citation_drawer",
            "basketball_showcase_page",
            "knowledge_list_page",
            "knowledge_detail_page",
            "document_detail_page",
        ),
        workbench_base_library_actions=("switch_knowledge_base", "browse_documents", "open_document_detail"),
        workbench_citation_query_keys=("document", "section", "citation"),
        workbench_optional_create_action_id="create_document",
        workbench_optional_delete_action_id="delete_document",
        workbench_flow=(
            RuntimeFlowStage(stage_id="knowledge_base_select", depends_on=(), produces=("knowledge_base_id",)),
            RuntimeFlowStage(
                stage_id="conversation",
                depends_on=("knowledge_base_id",),
                produces=("conversation_id", "answer", "citations"),
            ),
            RuntimeFlowStage(
                stage_id="citation_review",
                depends_on=("conversation_id", "citations"),
                produces=("document_id", "section_id", "drawer_state"),
            ),
            RuntimeFlowStage(
                stage_id="document_detail",
                depends_on=("document_id", "section_id"),
                produces=("document_page", "return_path"),
            ),
        ),
    )
