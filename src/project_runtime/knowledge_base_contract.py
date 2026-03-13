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
