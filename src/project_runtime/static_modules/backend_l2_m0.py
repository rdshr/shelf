from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Mapping, cast

from knowledge_base_runtime.runtime_profile import (
    KnowledgeBaseRuntimeProfile,
    load_knowledge_base_runtime_profile,
)
from project_runtime.correspondence_contracts import (
    BaseContract,
    ModuleContract,
    RuleContract,
    RuntimeBoundaryParamsContract,
    StaticBoundaryParamsContract,
    UNSET,
)

BACKEND_L2_M0_MODULE_ID = "backend.L2.M0"
BACKEND_L2_M0_MODULE_KEY = "backend__L2__M0"
BACKEND_L2_M0_BOUNDARY_FIELD_MAP = {
    "LIBRARY": "library",
    "PREVIEW": "preview",
    "CHAT": "chat",
    "RESULT": "result",
    "AUTH": "auth",
    "TRACE": "trace",
}


def _require_boundary_dict(payload: dict[str, dict[str, Any]], boundary_id: str) -> dict[str, Any]:
    boundary = payload.get(boundary_id)
    if not isinstance(boundary, dict):
        raise ValueError(f"missing backend boundary context: {boundary_id}")
    value = boundary.get("value")
    if not isinstance(value, dict):
        raise ValueError(f"backend boundary value must be a dict: {boundary_id}")
    return dict(value)


def _require_route_value(route_contract: Mapping[str, Any], field: str) -> str:
    value = route_contract.get(field)
    if not isinstance(value, str) or not value:
        raise ValueError(f"route_contract.{field} must be a non-empty string")
    return value


def _require_backend_overlay(exact_export: Mapping[str, Any]) -> dict[str, Any]:
    overlays = exact_export.get("overlays")
    if not isinstance(overlays, Mapping):
        raise ValueError("exact_export.overlays must be a mapping")
    backend = overlays.get("backend")
    if not isinstance(backend, Mapping):
        raise ValueError("exact_export.overlays.backend must be a mapping")
    return {str(key): value for key, value in backend.items()}


@dataclass(frozen=True, slots=True)
class BackendL2M0StaticBoundaryParams(StaticBoundaryParamsContract):
    library: object = None
    preview: object = None
    chat: object = None
    result: object = None
    auth: object = None
    trace: object = None

    framework_module_id: ClassVar[str] = BACKEND_L2_M0_MODULE_ID
    module_key: ClassVar[str] = BACKEND_L2_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(BACKEND_L2_M0_BOUNDARY_FIELD_MAP)


@dataclass(frozen=True, slots=True)
class BackendL2M0DynamicBoundaryParams(RuntimeBoundaryParamsContract):
    library: object = UNSET
    preview: object = UNSET
    chat: object = UNSET
    result: object = UNSET
    auth: object = UNSET
    trace: object = UNSET

    framework_module_id: ClassVar[str] = BACKEND_L2_M0_MODULE_ID
    module_key: ClassVar[str] = BACKEND_L2_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(BACKEND_L2_M0_BOUNDARY_FIELD_MAP)


class BackendL2M0B1Base(BaseContract):
    framework_base_id: ClassVar[str] = "backend.L2.M0.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = BACKEND_L2_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("AUTH", "CHAT", "LIBRARY", "PREVIEW", "RESULT", "TRACE")

    def __init__(self, module: BackendL2M0Module) -> None:
        self._module = module

    def knowledge_base_payload(self) -> dict[str, Any]:
        library = self._module.boundary_value("LIBRARY")
        return {
            "knowledge_base_id": str(library["knowledge_base_id"]),
            "knowledge_base_name": str(library["knowledge_base_name"]),
            "knowledge_base_description": str(library["knowledge_base_description"]),
            "source_types": list(library["source_types"]),
            "metadata_fields": list(library["metadata_fields"]),
        }

    def preview_retrieval_payload(self) -> dict[str, Any]:
        preview = self._module.boundary_value("PREVIEW")
        return {
            "max_preview_sections": int(preview["max_preview_sections"]),
        }


class BackendL2M0B2Base(BaseContract):
    framework_base_id: ClassVar[str] = "backend.L2.M0.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = BACKEND_L2_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("AUTH", "CHAT", "LIBRARY", "PREVIEW", "RESULT", "TRACE")

    def __init__(self, module: BackendL2M0Module) -> None:
        self._module = module

    def answer_policy_payload(self) -> dict[str, Any]:
        chat = self._module.boundary_value("CHAT")
        result = self._module.boundary_value("RESULT")
        return {
            "citation_style": str(chat["citation_style"]),
            "no_match_text": str(result["no_match_text"]),
            "lead_template": str(result["lead_template"]),
            "lead_snippet_template": str(result["lead_snippet_template"]),
            "followup_template": str(result["followup_template"]),
            "closing_text": str(result["closing_text"]),
        }

    def return_policy_payload(self, route_contract: Mapping[str, Any]) -> dict[str, Any]:
        chat = self._module.boundary_value("CHAT")
        knowledge_detail = _require_route_value(route_contract, "knowledge_detail")
        document_detail_prefix = _require_route_value(route_contract, "document_detail_prefix")
        return {
            "targets": list(chat["return_targets"]),
            "anchor_restore": bool(chat["anchor_restore"]),
            "chat_path": _require_route_value(route_contract, "workbench"),
            "knowledge_base_detail_path": f"{knowledge_detail}/{{knowledge_base_id}}",
            "document_detail_path": f"{document_detail_prefix}/{{document_id}}",
        }

    def chat_retrieval_payload(self) -> dict[str, Any]:
        chat = self._module.boundary_value("CHAT")
        return {
            "max_citations": int(chat["max_citations"]),
        }


class BackendL2M0B3Base(BaseContract):
    framework_base_id: ClassVar[str] = "backend.L2.M0.B3"
    framework_base_short_id: ClassVar[str] = "B3"
    owner_module_id: ClassVar[str] = BACKEND_L2_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("AUTH", "CHAT", "LIBRARY", "PREVIEW", "RESULT", "TRACE")

    def __init__(self, module: BackendL2M0Module) -> None:
        self._module = module

    def transport_payload(self, route_contract: Mapping[str, Any]) -> dict[str, Any]:
        result = self._module.boundary_value("RESULT")
        return {
            "mode": str(result["transport_mode"]),
            "api_prefix": _require_route_value(route_contract, "api_prefix"),
            "project_config_endpoint": str(result["project_config_endpoint"]),
        }

    def interaction_copy_payload(self) -> dict[str, Any]:
        result = self._module.boundary_value("RESULT")
        return {
            "loading_text": str(result["loading_text"]),
            "error_text": str(result["error_text"]),
        }

    def trace_retrieval_payload(self) -> dict[str, Any]:
        trace = self._module.boundary_value("TRACE")
        return {
            "query_token_min_length": int(trace["query_token_min_length"]),
            "focus_section_bonus": int(trace["focus_section_bonus"]),
            "token_match_bonus": int(trace["token_match_bonus"]),
            "selection_mode": str(trace["selection_mode"]),
        }

    def write_policy_payload(self) -> dict[str, Any]:
        auth = self._module.boundary_value("AUTH")
        return {
            "allow_create": bool(auth["allow_create"]),
            "allow_delete": bool(auth["allow_delete"]),
        }


class BackendL2M0R1Rule(RuleContract):
    framework_rule_id: ClassVar[str] = "backend.L2.M0.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = BACKEND_L2_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("backend.L2.M0.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("LIBRARY", "PREVIEW", "RESULT")

    def __init__(self, base_b1: BackendL2M0B1Base) -> None:
        self._base_b1 = base_b1

    def knowledge_base_payload(self) -> dict[str, Any]:
        return self._base_b1.knowledge_base_payload()

    def preview_retrieval_payload(self) -> dict[str, Any]:
        return self._base_b1.preview_retrieval_payload()


class BackendL2M0R2Rule(RuleContract):
    framework_rule_id: ClassVar[str] = "backend.L2.M0.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = BACKEND_L2_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("backend.L2.M0.B2", "backend.L2.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("CHAT", "TRACE", "RESULT", "AUTH")

    def __init__(self, base_b2: BackendL2M0B2Base, base_b3: BackendL2M0B3Base) -> None:
        self._base_b2 = base_b2
        self._base_b3 = base_b3

    def answer_policy_payload(self) -> dict[str, Any]:
        return self._base_b2.answer_policy_payload()

    def return_policy_payload(self, route_contract: Mapping[str, Any]) -> dict[str, Any]:
        return self._base_b2.return_policy_payload(route_contract)

    def chat_retrieval_payload(self) -> dict[str, Any]:
        return self._base_b2.chat_retrieval_payload()


class BackendL2M0R3Rule(RuleContract):
    framework_rule_id: ClassVar[str] = "backend.L2.M0.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = BACKEND_L2_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("backend.L2.M0.B1", "backend.L2.M0.B2", "backend.L2.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("LIBRARY", "PREVIEW", "CHAT", "RESULT", "AUTH", "TRACE")

    def __init__(
        self,
        base_b1: BackendL2M0B1Base,
        base_b2: BackendL2M0B2Base,
        base_b3: BackendL2M0B3Base,
    ) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

    def transport_payload(self, route_contract: Mapping[str, Any]) -> dict[str, Any]:
        return self._base_b3.transport_payload(route_contract)

    def interaction_copy_payload(self) -> dict[str, Any]:
        return self._base_b3.interaction_copy_payload()

    def trace_retrieval_payload(self) -> dict[str, Any]:
        return self._base_b3.trace_retrieval_payload()

    def interaction_flow_payload(self, profile: KnowledgeBaseRuntimeProfile) -> list[dict[str, Any]]:
        return list(profile.workbench_flow_dicts())


class BackendL2M0R4Rule(RuleContract):
    framework_rule_id: ClassVar[str] = "backend.L2.M0.R4"
    framework_rule_short_id: ClassVar[str] = "R4"
    owner_module_id: ClassVar[str] = BACKEND_L2_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("backend.L2.M0.B1", "backend.L2.M0.B2", "backend.L2.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("LIBRARY", "PREVIEW", "CHAT", "RESULT", "AUTH", "TRACE")

    def __init__(self, base_b3: BackendL2M0B3Base) -> None:
        self._base_b3 = base_b3

    def write_policy_payload(self) -> dict[str, Any]:
        return self._base_b3.write_policy_payload()


class BackendL2M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = BACKEND_L2_M0_MODULE_ID
    module_key: ClassVar[str] = BACKEND_L2_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        BackendL2M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        BackendL2M0DynamicBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            BackendL2M0B1Base,
            BackendL2M0B2Base,
            BackendL2M0B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            BackendL2M0R1Rule,
            BackendL2M0R2Rule,
            BackendL2M0R3Rule,
            BackendL2M0R4Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(BACKEND_L2_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: BackendL2M0StaticBoundaryParams,
        dynamic_params: BackendL2M0DynamicBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.dynamic_params = dynamic_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.dynamic_params)
        self.b1 = BackendL2M0B1Base(self)
        self.b2 = BackendL2M0B2Base(self)
        self.b3 = BackendL2M0B3Base(self)
        self.r1 = BackendL2M0R1Rule(self.b1)
        self.r2 = BackendL2M0R2Rule(self.b2, self.b3)
        self.r3 = BackendL2M0R3Rule(self.b1, self.b2, self.b3)
        self.r4 = BackendL2M0R4Rule(self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        dynamic_payload: Mapping[str, Any] | None = None,
    ) -> BackendL2M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, BackendL2M0StaticBoundaryParams):
            raise TypeError("BackendL2M0Module static params type mismatch")
        if dynamic_payload is None:
            dynamic_params = cls.runtime_params_default()
        else:
            dynamic_params = cls.RuntimeBoundaryParams(**dict(dynamic_payload))
        if not isinstance(dynamic_params, BackendL2M0DynamicBoundaryParams):
            raise TypeError("BackendL2M0Module dynamic params type mismatch")
        return cls(static_params, dynamic_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)

    def export_service_spec(
        self,
        *,
        exact_export: Mapping[str, Any],
        route_contract: Mapping[str, Any],
        profile: KnowledgeBaseRuntimeProfile | None = None,
    ) -> dict[str, Any]:
        backend_overlay = _require_backend_overlay(exact_export)
        runtime_profile = profile or load_knowledge_base_runtime_profile()
        retrieval = {
            "strategy": str(backend_overlay["retrieval_strategy"]),
            **self.r1.preview_retrieval_payload(),
            **self.r2.chat_retrieval_payload(),
            **self.r3.trace_retrieval_payload(),
        }
        return {
            "implementation": {
                "backend_renderer": str(backend_overlay["backend_renderer"]),
            },
            "knowledge_base": self.r1.knowledge_base_payload(),
            "transport": self.r3.transport_payload(route_contract),
            "retrieval": retrieval,
            "interaction_flow": self.r3.interaction_flow_payload(runtime_profile),
            "answer_policy": self.r2.answer_policy_payload(),
            "interaction_copy": self.r3.interaction_copy_payload(),
            "return_policy": self.r2.return_policy_payload(route_contract),
            "write_policy": self.r4.write_policy_payload(),
        }


__all__ = [
    "BACKEND_L2_M0_BOUNDARY_FIELD_MAP",
    "BACKEND_L2_M0_MODULE_ID",
    "BACKEND_L2_M0_MODULE_KEY",
    "BackendL2M0B1Base",
    "BackendL2M0B2Base",
    "BackendL2M0B3Base",
    "BackendL2M0DynamicBoundaryParams",
    "BackendL2M0Module",
    "BackendL2M0R1Rule",
    "BackendL2M0R2Rule",
    "BackendL2M0R3Rule",
    "BackendL2M0R4Rule",
    "BackendL2M0StaticBoundaryParams",
]
