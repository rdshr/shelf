from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Mapping, cast

from project_runtime.correspondence_contracts import (
    BaseContract,
    ModuleContract,
    RuleContract,
    RuntimeBoundaryParamsContract,
    StaticBoundaryParamsContract,
    UNSET,
)
from project_runtime.static_modules.backend_l2_m0 import (
    BACKEND_L2_M0_MODULE_ID,
    BackendL2M0B1Base,
    BackendL2M0B2Base,
    BackendL2M0B3Base,
    BackendL2M0DynamicBoundaryParams,
    BackendL2M0Module,
    BackendL2M0R1Rule,
    BackendL2M0R2Rule,
    BackendL2M0R3Rule,
    BackendL2M0R4Rule,
    BackendL2M0StaticBoundaryParams,
)


def _require_boundary_dict(payload: dict[str, dict[str, Any]], boundary_id: str) -> dict[str, Any]:
    boundary = payload.get(boundary_id)
    if not isinstance(boundary, dict):
        raise ValueError(f"missing module boundary context: {boundary_id}")
    value = boundary.get("value")
    if not isinstance(value, dict):
        raise ValueError(f"module boundary value must be a dict: {boundary_id}")
    return dict(value)


class StaticBaseContract(BaseContract):
    def __init__(self, module: ModuleContract) -> None:
        self._module = module

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        context = getattr(self._module, "boundary_context", {})
        if not isinstance(context, dict):
            raise ValueError("module boundary context missing")
        return _require_boundary_dict(context, boundary_id)


class StaticRuleContract(RuleContract):
    pass


@dataclass(frozen=True)
class StaticModuleContractBundle:
    module_type: type[ModuleContract]
    static_params_type: type[StaticBoundaryParamsContract]
    runtime_params_type: type[RuntimeBoundaryParamsContract]
    base_types: tuple[type[BaseContract], ...]
    rule_types: tuple[type[RuleContract], ...]


BACKEND_L0_M0_MODULE_ID = "backend.L0.M0"
BACKEND_L0_M0_MODULE_KEY = "backend__L0__M0"
BACKEND_L0_M0_BOUNDARY_FIELD_MAP = {
    "FILE": "file",
    "PREVIEW": "preview",
    "CHAT": "chat",
    "CITATION": "citation",
    "VALID": "valid",
    "ERROR": "error",
}

@dataclass(frozen=True, slots=True)
class BackendL0M0StaticBoundaryParams(StaticBoundaryParamsContract):
    file: object = None
    preview: object = None
    chat: object = None
    citation: object = None
    valid: object = None
    error: object = None

    framework_module_id: ClassVar[str] = BACKEND_L0_M0_MODULE_ID
    module_key: ClassVar[str] = BACKEND_L0_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(BACKEND_L0_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class BackendL0M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    file: object = UNSET
    preview: object = UNSET
    chat: object = UNSET
    citation: object = UNSET
    valid: object = UNSET
    error: object = UNSET

    framework_module_id: ClassVar[str] = BACKEND_L0_M0_MODULE_ID
    module_key: ClassVar[str] = BACKEND_L0_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(BACKEND_L0_M0_BOUNDARY_FIELD_MAP)

class BackendL0M0B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "backend.L0.M0.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = BACKEND_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("FILE", "VALID")

class BackendL0M0B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "backend.L0.M0.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = BACKEND_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("PREVIEW", "FILE")

class BackendL0M0B3Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "backend.L0.M0.B3"
    framework_base_short_id: ClassVar[str] = "B3"
    owner_module_id: ClassVar[str] = BACKEND_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("CHAT", "CITATION", "ERROR")

class BackendL0M0R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "backend.L0.M0.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = BACKEND_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("backend.L0.M0.B1", "backend.L0.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("FILE", "PREVIEW", "VALID")

    def __init__(self, base_b1: BackendL0M0B1Base, base_b2: BackendL0M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class BackendL0M0R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "backend.L0.M0.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = BACKEND_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("backend.L0.M0.B2", "backend.L0.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("CHAT", "CITATION", "PREVIEW", "ERROR")

    def __init__(self, base_b2: BackendL0M0B2Base, base_b3: BackendL0M0B3Base) -> None:
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class BackendL0M0R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "backend.L0.M0.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = BACKEND_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("backend.L0.M0.B1", "backend.L0.M0.B2", "backend.L0.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("FILE", "PREVIEW", "CHAT", "CITATION", "VALID", "ERROR")

    def __init__(self, base_b1: BackendL0M0B1Base, base_b2: BackendL0M0B2Base, base_b3: BackendL0M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class BackendL0M0R4Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "backend.L0.M0.R4"
    framework_rule_short_id: ClassVar[str] = "R4"
    owner_module_id: ClassVar[str] = BACKEND_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("backend.L0.M0.B1", "backend.L0.M0.B2", "backend.L0.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("FILE", "PREVIEW", "CHAT", "CITATION", "VALID", "ERROR")

    def __init__(self, base_b1: BackendL0M0B1Base, base_b2: BackendL0M0B2Base, base_b3: BackendL0M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class BackendL0M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = BACKEND_L0_M0_MODULE_ID
    module_key: ClassVar[str] = BACKEND_L0_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        BackendL0M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        BackendL0M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            BackendL0M0B1Base,
            BackendL0M0B2Base,
            BackendL0M0B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            BackendL0M0R1Rule,
            BackendL0M0R2Rule,
            BackendL0M0R3Rule,
            BackendL0M0R4Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(BACKEND_L0_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: BackendL0M0StaticBoundaryParams,
        runtime_params: BackendL0M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = BackendL0M0B1Base(self)
        self.b2 = BackendL0M0B2Base(self)
        self.b3 = BackendL0M0B3Base(self)
        self.r1 = BackendL0M0R1Rule(self.b1, self.b2)
        self.r2 = BackendL0M0R2Rule(self.b2, self.b3)
        self.r3 = BackendL0M0R3Rule(self.b1, self.b2, self.b3)
        self.r4 = BackendL0M0R4Rule(self.b1, self.b2, self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> BackendL0M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, BackendL0M0StaticBoundaryParams):
            raise TypeError("BackendL0M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, BackendL0M0RuntimeBoundaryParams):
            raise TypeError("BackendL0M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)


BACKEND_L1_M0_MODULE_ID = "backend.L1.M0"
BACKEND_L1_M0_MODULE_KEY = "backend__L1__M0"
BACKEND_L1_M0_BOUNDARY_FIELD_MAP = {
    "LIBAPI": "libapi",
    "PREVIEWAPI": "previewapi",
    "CHATAPI": "chatapi",
    "CONSIST": "consist",
    "AUTH": "auth",
    "TRACE": "trace",
}

@dataclass(frozen=True, slots=True)
class BackendL1M0StaticBoundaryParams(StaticBoundaryParamsContract):
    libapi: object = None
    previewapi: object = None
    chatapi: object = None
    consist: object = None
    auth: object = None
    trace: object = None

    framework_module_id: ClassVar[str] = BACKEND_L1_M0_MODULE_ID
    module_key: ClassVar[str] = BACKEND_L1_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(BACKEND_L1_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class BackendL1M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    libapi: object = UNSET
    previewapi: object = UNSET
    chatapi: object = UNSET
    consist: object = UNSET
    auth: object = UNSET
    trace: object = UNSET

    framework_module_id: ClassVar[str] = BACKEND_L1_M0_MODULE_ID
    module_key: ClassVar[str] = BACKEND_L1_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(BACKEND_L1_M0_BOUNDARY_FIELD_MAP)

class BackendL1M0B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "backend.L1.M0.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = BACKEND_L1_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("LIBAPI", "CONSIST", "AUTH")

class BackendL1M0B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "backend.L1.M0.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = BACKEND_L1_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("PREVIEWAPI", "CONSIST", "TRACE")

class BackendL1M0B3Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "backend.L1.M0.B3"
    framework_base_short_id: ClassVar[str] = "B3"
    owner_module_id: ClassVar[str] = BACKEND_L1_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("CHATAPI", "TRACE", "AUTH")

class BackendL1M0R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "backend.L1.M0.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = BACKEND_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("backend.L1.M0.B1", "backend.L1.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("LIBAPI", "PREVIEWAPI", "CONSIST", "TRACE")

    def __init__(self, base_b1: BackendL1M0B1Base, base_b2: BackendL1M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class BackendL1M0R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "backend.L1.M0.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = BACKEND_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("backend.L1.M0.B2", "backend.L1.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("PREVIEWAPI", "CHATAPI", "TRACE", "CONSIST")

    def __init__(self, base_b2: BackendL1M0B2Base, base_b3: BackendL1M0B3Base) -> None:
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class BackendL1M0R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "backend.L1.M0.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = BACKEND_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("backend.L1.M0.B1", "backend.L1.M0.B2", "backend.L1.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("LIBAPI", "PREVIEWAPI", "CHATAPI", "CONSIST", "AUTH", "TRACE")

    def __init__(self, base_b1: BackendL1M0B1Base, base_b2: BackendL1M0B2Base, base_b3: BackendL1M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class BackendL1M0R4Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "backend.L1.M0.R4"
    framework_rule_short_id: ClassVar[str] = "R4"
    owner_module_id: ClassVar[str] = BACKEND_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("backend.L1.M0.B1", "backend.L1.M0.B2", "backend.L1.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("LIBAPI", "PREVIEWAPI", "CHATAPI", "CONSIST", "AUTH", "TRACE")

    def __init__(self, base_b1: BackendL1M0B1Base, base_b2: BackendL1M0B2Base, base_b3: BackendL1M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class BackendL1M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = BACKEND_L1_M0_MODULE_ID
    module_key: ClassVar[str] = BACKEND_L1_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        BackendL1M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        BackendL1M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            BackendL1M0B1Base,
            BackendL1M0B2Base,
            BackendL1M0B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            BackendL1M0R1Rule,
            BackendL1M0R2Rule,
            BackendL1M0R3Rule,
            BackendL1M0R4Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(BACKEND_L1_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: BackendL1M0StaticBoundaryParams,
        runtime_params: BackendL1M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = BackendL1M0B1Base(self)
        self.b2 = BackendL1M0B2Base(self)
        self.b3 = BackendL1M0B3Base(self)
        self.r1 = BackendL1M0R1Rule(self.b1, self.b2)
        self.r2 = BackendL1M0R2Rule(self.b2, self.b3)
        self.r3 = BackendL1M0R3Rule(self.b1, self.b2, self.b3)
        self.r4 = BackendL1M0R4Rule(self.b1, self.b2, self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> BackendL1M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, BackendL1M0StaticBoundaryParams):
            raise TypeError("BackendL1M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, BackendL1M0RuntimeBoundaryParams):
            raise TypeError("BackendL1M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)


CURTAIN_L0_M0_MODULE_ID = "curtain.L0.M0"
CURTAIN_L0_M0_MODULE_KEY = "curtain__L0__M0"
CURTAIN_L0_M0_BOUNDARY_FIELD_MAP = {
    "SPAN": "span",
    "LOAD": "load",
    "TRAVEL": "travel",
    "MOUNT": "mount",
    "SAFETY": "safety",
    "ENV": "env",
    "NOISE": "noise",
}

@dataclass(frozen=True, slots=True)
class CurtainL0M0StaticBoundaryParams(StaticBoundaryParamsContract):
    span: object = None
    load: object = None
    travel: object = None
    mount: object = None
    safety: object = None
    env: object = None
    noise: object = None

    framework_module_id: ClassVar[str] = CURTAIN_L0_M0_MODULE_ID
    module_key: ClassVar[str] = CURTAIN_L0_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(CURTAIN_L0_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class CurtainL0M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    span: object = UNSET
    load: object = UNSET
    travel: object = UNSET
    mount: object = UNSET
    safety: object = UNSET
    env: object = UNSET
    noise: object = UNSET

    framework_module_id: ClassVar[str] = CURTAIN_L0_M0_MODULE_ID
    module_key: ClassVar[str] = CURTAIN_L0_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(CURTAIN_L0_M0_BOUNDARY_FIELD_MAP)

class CurtainL0M0B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "curtain.L0.M0.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = CURTAIN_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("SPAN", "LOAD", "MOUNT")

class CurtainL0M0B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "curtain.L0.M0.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = CURTAIN_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("TRAVEL", "LOAD", "NOISE")

class CurtainL0M0B3Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "curtain.L0.M0.B3"
    framework_base_short_id: ClassVar[str] = "B3"
    owner_module_id: ClassVar[str] = CURTAIN_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("SAFETY", "ENV", "MOUNT")

class CurtainL0M0R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "curtain.L0.M0.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = CURTAIN_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("curtain.L0.M0.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("SPAN", "LOAD", "MOUNT")

    def __init__(self, base_b1: CurtainL0M0B1Base) -> None:
        self._base_b1 = base_b1

class CurtainL0M0R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "curtain.L0.M0.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = CURTAIN_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("curtain.L0.M0.B1", "curtain.L0.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("TRAVEL", "LOAD", "NOISE", "SPAN")

    def __init__(self, base_b1: CurtainL0M0B1Base, base_b2: CurtainL0M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class CurtainL0M0R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "curtain.L0.M0.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = CURTAIN_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("curtain.L0.M0.B1", "curtain.L0.M0.B2", "curtain.L0.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("SAFETY", "ENV", "MOUNT", "TRAVEL")

    def __init__(self, base_b1: CurtainL0M0B1Base, base_b2: CurtainL0M0B2Base, base_b3: CurtainL0M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class CurtainL0M0R4Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "curtain.L0.M0.R4"
    framework_rule_short_id: ClassVar[str] = "R4"
    owner_module_id: ClassVar[str] = CURTAIN_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("curtain.L0.M0.B1", "curtain.L0.M0.B2", "curtain.L0.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("SPAN", "LOAD", "TRAVEL", "MOUNT", "SAFETY", "ENV", "NOISE")

    def __init__(self, base_b1: CurtainL0M0B1Base, base_b2: CurtainL0M0B2Base, base_b3: CurtainL0M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class CurtainL0M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = CURTAIN_L0_M0_MODULE_ID
    module_key: ClassVar[str] = CURTAIN_L0_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        CurtainL0M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        CurtainL0M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            CurtainL0M0B1Base,
            CurtainL0M0B2Base,
            CurtainL0M0B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            CurtainL0M0R1Rule,
            CurtainL0M0R2Rule,
            CurtainL0M0R3Rule,
            CurtainL0M0R4Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(CURTAIN_L0_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: CurtainL0M0StaticBoundaryParams,
        runtime_params: CurtainL0M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = CurtainL0M0B1Base(self)
        self.b2 = CurtainL0M0B2Base(self)
        self.b3 = CurtainL0M0B3Base(self)
        self.r1 = CurtainL0M0R1Rule(self.b1)
        self.r2 = CurtainL0M0R2Rule(self.b1, self.b2)
        self.r3 = CurtainL0M0R3Rule(self.b1, self.b2, self.b3)
        self.r4 = CurtainL0M0R4Rule(self.b1, self.b2, self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> CurtainL0M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, CurtainL0M0StaticBoundaryParams):
            raise TypeError("CurtainL0M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, CurtainL0M0RuntimeBoundaryParams):
            raise TypeError("CurtainL0M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)


CURTAIN_L1_M0_MODULE_ID = "curtain.L1.M0"
CURTAIN_L1_M0_MODULE_KEY = "curtain__L1__M0"
CURTAIN_L1_M0_BOUNDARY_FIELD_MAP = {
    "INSTALL": "install",
    "ALIGN": "align",
    "POWER": "power",
    "CTRL": "ctrl",
    "CAL": "cal",
    "FAULT": "fault",
    "MAINT": "maint",
}

@dataclass(frozen=True, slots=True)
class CurtainL1M0StaticBoundaryParams(StaticBoundaryParamsContract):
    install: object = None
    align: object = None
    power: object = None
    ctrl: object = None
    cal: object = None
    fault: object = None
    maint: object = None

    framework_module_id: ClassVar[str] = CURTAIN_L1_M0_MODULE_ID
    module_key: ClassVar[str] = CURTAIN_L1_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(CURTAIN_L1_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class CurtainL1M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    install: object = UNSET
    align: object = UNSET
    power: object = UNSET
    ctrl: object = UNSET
    cal: object = UNSET
    fault: object = UNSET
    maint: object = UNSET

    framework_module_id: ClassVar[str] = CURTAIN_L1_M0_MODULE_ID
    module_key: ClassVar[str] = CURTAIN_L1_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(CURTAIN_L1_M0_BOUNDARY_FIELD_MAP)

class CurtainL1M0B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "curtain.L1.M0.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = CURTAIN_L1_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("INSTALL", "ALIGN", "MAINT")

class CurtainL1M0B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "curtain.L1.M0.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = CURTAIN_L1_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("CTRL", "POWER", "ALIGN")

class CurtainL1M0B3Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "curtain.L1.M0.B3"
    framework_base_short_id: ClassVar[str] = "B3"
    owner_module_id: ClassVar[str] = CURTAIN_L1_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("CAL", "FAULT", "MAINT")

class CurtainL1M0R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "curtain.L1.M0.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = CURTAIN_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("curtain.L1.M0.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("INSTALL", "ALIGN", "MAINT")

    def __init__(self, base_b1: CurtainL1M0B1Base) -> None:
        self._base_b1 = base_b1

class CurtainL1M0R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "curtain.L1.M0.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = CURTAIN_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("curtain.L1.M0.B1", "curtain.L1.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("CTRL", "POWER", "ALIGN", "INSTALL")

    def __init__(self, base_b1: CurtainL1M0B1Base, base_b2: CurtainL1M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class CurtainL1M0R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "curtain.L1.M0.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = CURTAIN_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("curtain.L1.M0.B1", "curtain.L1.M0.B2", "curtain.L1.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("CAL", "FAULT", "MAINT", "CTRL")

    def __init__(self, base_b1: CurtainL1M0B1Base, base_b2: CurtainL1M0B2Base, base_b3: CurtainL1M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class CurtainL1M0R4Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "curtain.L1.M0.R4"
    framework_rule_short_id: ClassVar[str] = "R4"
    owner_module_id: ClassVar[str] = CURTAIN_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("curtain.L1.M0.B1", "curtain.L1.M0.B2", "curtain.L1.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("INSTALL", "ALIGN", "POWER", "CTRL", "CAL", "FAULT", "MAINT")

    def __init__(self, base_b1: CurtainL1M0B1Base, base_b2: CurtainL1M0B2Base, base_b3: CurtainL1M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class CurtainL1M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = CURTAIN_L1_M0_MODULE_ID
    module_key: ClassVar[str] = CURTAIN_L1_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        CurtainL1M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        CurtainL1M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            CurtainL1M0B1Base,
            CurtainL1M0B2Base,
            CurtainL1M0B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            CurtainL1M0R1Rule,
            CurtainL1M0R2Rule,
            CurtainL1M0R3Rule,
            CurtainL1M0R4Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(CURTAIN_L1_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: CurtainL1M0StaticBoundaryParams,
        runtime_params: CurtainL1M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = CurtainL1M0B1Base(self)
        self.b2 = CurtainL1M0B2Base(self)
        self.b3 = CurtainL1M0B3Base(self)
        self.r1 = CurtainL1M0R1Rule(self.b1)
        self.r2 = CurtainL1M0R2Rule(self.b1, self.b2)
        self.r3 = CurtainL1M0R3Rule(self.b1, self.b2, self.b3)
        self.r4 = CurtainL1M0R4Rule(self.b1, self.b2, self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> CurtainL1M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, CurtainL1M0StaticBoundaryParams):
            raise TypeError("CurtainL1M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, CurtainL1M0RuntimeBoundaryParams):
            raise TypeError("CurtainL1M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)


CURTAIN_L2_M0_MODULE_ID = "curtain.L2.M0"
CURTAIN_L2_M0_MODULE_KEY = "curtain__L2__M0"
CURTAIN_L2_M0_BOUNDARY_FIELD_MAP = {
    "SPAN": "span",
    "LOAD": "load",
    "TRAVEL": "travel",
    "CTRL": "ctrl",
    "SAFE": "safe",
    "ENV": "env",
    "NOISE": "noise",
}

@dataclass(frozen=True, slots=True)
class CurtainL2M0StaticBoundaryParams(StaticBoundaryParamsContract):
    span: object = None
    load: object = None
    travel: object = None
    ctrl: object = None
    safe: object = None
    env: object = None
    noise: object = None

    framework_module_id: ClassVar[str] = CURTAIN_L2_M0_MODULE_ID
    module_key: ClassVar[str] = CURTAIN_L2_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(CURTAIN_L2_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class CurtainL2M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    span: object = UNSET
    load: object = UNSET
    travel: object = UNSET
    ctrl: object = UNSET
    safe: object = UNSET
    env: object = UNSET
    noise: object = UNSET

    framework_module_id: ClassVar[str] = CURTAIN_L2_M0_MODULE_ID
    module_key: ClassVar[str] = CURTAIN_L2_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(CURTAIN_L2_M0_BOUNDARY_FIELD_MAP)

class CurtainL2M0B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "curtain.L2.M0.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = CURTAIN_L2_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("SPAN", "LOAD", "ENV")

class CurtainL2M0B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "curtain.L2.M0.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = CURTAIN_L2_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("TRAVEL", "CTRL", "NOISE")

class CurtainL2M0B3Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "curtain.L2.M0.B3"
    framework_base_short_id: ClassVar[str] = "B3"
    owner_module_id: ClassVar[str] = CURTAIN_L2_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("SAFE", "ENV", "LOAD")

class CurtainL2M0R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "curtain.L2.M0.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = CURTAIN_L2_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("curtain.L2.M0.B1", "curtain.L2.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("SPAN", "LOAD", "TRAVEL", "CTRL")

    def __init__(self, base_b1: CurtainL2M0B1Base, base_b2: CurtainL2M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class CurtainL2M0R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "curtain.L2.M0.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = CURTAIN_L2_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("curtain.L2.M0.B1", "curtain.L2.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("SAFE", "ENV", "LOAD", "SPAN")

    def __init__(self, base_b1: CurtainL2M0B1Base, base_b3: CurtainL2M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b3 = base_b3

class CurtainL2M0R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "curtain.L2.M0.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = CURTAIN_L2_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("curtain.L2.M0.B1", "curtain.L2.M0.B2", "curtain.L2.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("SPAN", "LOAD", "TRAVEL", "CTRL", "SAFE", "ENV", "NOISE")

    def __init__(self, base_b1: CurtainL2M0B1Base, base_b2: CurtainL2M0B2Base, base_b3: CurtainL2M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class CurtainL2M0R4Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "curtain.L2.M0.R4"
    framework_rule_short_id: ClassVar[str] = "R4"
    owner_module_id: ClassVar[str] = CURTAIN_L2_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("curtain.L2.M0.B1", "curtain.L2.M0.B2", "curtain.L2.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("SPAN", "LOAD", "TRAVEL", "CTRL", "SAFE", "ENV", "NOISE")

    def __init__(self, base_b1: CurtainL2M0B1Base, base_b2: CurtainL2M0B2Base, base_b3: CurtainL2M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class CurtainL2M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = CURTAIN_L2_M0_MODULE_ID
    module_key: ClassVar[str] = CURTAIN_L2_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        CurtainL2M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        CurtainL2M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            CurtainL2M0B1Base,
            CurtainL2M0B2Base,
            CurtainL2M0B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            CurtainL2M0R1Rule,
            CurtainL2M0R2Rule,
            CurtainL2M0R3Rule,
            CurtainL2M0R4Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(CURTAIN_L2_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: CurtainL2M0StaticBoundaryParams,
        runtime_params: CurtainL2M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = CurtainL2M0B1Base(self)
        self.b2 = CurtainL2M0B2Base(self)
        self.b3 = CurtainL2M0B3Base(self)
        self.r1 = CurtainL2M0R1Rule(self.b1, self.b2)
        self.r2 = CurtainL2M0R2Rule(self.b1, self.b3)
        self.r3 = CurtainL2M0R3Rule(self.b1, self.b2, self.b3)
        self.r4 = CurtainL2M0R4Rule(self.b1, self.b2, self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> CurtainL2M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, CurtainL2M0StaticBoundaryParams):
            raise TypeError("CurtainL2M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, CurtainL2M0RuntimeBoundaryParams):
            raise TypeError("CurtainL2M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)


FRONTEND_L0_M0_MODULE_ID = "frontend.L0.M0"
FRONTEND_L0_M0_MODULE_KEY = "frontend__L0__M0"
FRONTEND_L0_M0_BOUNDARY_FIELD_MAP = {
    "SURFACE": "surface",
    "SLOT": "slot",
    "HOST": "host",
    "PROP": "prop",
    "FOCUS": "focus",
    "A11Y": "a11y",
}

@dataclass(frozen=True, slots=True)
class FrontendL0M0StaticBoundaryParams(StaticBoundaryParamsContract):
    surface: object = None
    slot: object = None
    host: object = None
    prop: object = None
    focus: object = None
    a11y: object = None

    framework_module_id: ClassVar[str] = FRONTEND_L0_M0_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L0_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L0_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class FrontendL0M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    surface: object = UNSET
    slot: object = UNSET
    host: object = UNSET
    prop: object = UNSET
    focus: object = UNSET
    a11y: object = UNSET

    framework_module_id: ClassVar[str] = FRONTEND_L0_M0_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L0_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L0_M0_BOUNDARY_FIELD_MAP)

class FrontendL0M0B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L0.M0.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = FRONTEND_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("SURFACE", "SLOT")

class FrontendL0M0B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L0.M0.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = FRONTEND_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("HOST", "PROP", "FOCUS", "A11Y")

class FrontendL0M0R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L0.M0.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = FRONTEND_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L0.M0.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("SURFACE", "SLOT")

    def __init__(self, base_b1: FrontendL0M0B1Base) -> None:
        self._base_b1 = base_b1

class FrontendL0M0R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L0.M0.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = FRONTEND_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L0.M0.B1", "frontend.L0.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("HOST", "PROP", "FOCUS", "A11Y", "SURFACE", "SLOT")

    def __init__(self, base_b1: FrontendL0M0B1Base, base_b2: FrontendL0M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL0M0R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L0.M0.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = FRONTEND_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L0.M0.B1", "frontend.L0.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("SURFACE", "SLOT", "HOST", "PROP", "FOCUS", "A11Y")

    def __init__(self, base_b1: FrontendL0M0B1Base, base_b2: FrontendL0M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL0M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = FRONTEND_L0_M0_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L0_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        FrontendL0M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        FrontendL0M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            FrontendL0M0B1Base,
            FrontendL0M0B2Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            FrontendL0M0R1Rule,
            FrontendL0M0R2Rule,
            FrontendL0M0R3Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L0_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: FrontendL0M0StaticBoundaryParams,
        runtime_params: FrontendL0M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = FrontendL0M0B1Base(self)
        self.b2 = FrontendL0M0B2Base(self)
        self.r1 = FrontendL0M0R1Rule(self.b1)
        self.r2 = FrontendL0M0R2Rule(self.b1, self.b2)
        self.r3 = FrontendL0M0R3Rule(self.b1, self.b2)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> FrontendL0M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, FrontendL0M0StaticBoundaryParams):
            raise TypeError("FrontendL0M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, FrontendL0M0RuntimeBoundaryParams):
            raise TypeError("FrontendL0M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)


FRONTEND_L0_M1_MODULE_ID = "frontend.L0.M1"
FRONTEND_L0_M1_MODULE_KEY = "frontend__L0__M1"
FRONTEND_L0_M1_BOUNDARY_FIELD_MAP = {
    "VALUE": "value",
    "ACTION": "action",
    "STATE": "state",
    "RESET": "reset",
    "FEEDBACK": "feedback",
    "TRANSFER": "transfer",
}

@dataclass(frozen=True, slots=True)
class FrontendL0M1StaticBoundaryParams(StaticBoundaryParamsContract):
    value: object = None
    action: object = None
    state: object = None
    reset: object = None
    feedback: object = None
    transfer: object = None

    framework_module_id: ClassVar[str] = FRONTEND_L0_M1_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L0_M1_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L0_M1_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class FrontendL0M1RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    value: object = UNSET
    action: object = UNSET
    state: object = UNSET
    reset: object = UNSET
    feedback: object = UNSET
    transfer: object = UNSET

    framework_module_id: ClassVar[str] = FRONTEND_L0_M1_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L0_M1_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L0_M1_BOUNDARY_FIELD_MAP)

class FrontendL0M1B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L0.M1.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = FRONTEND_L0_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("VALUE", "ACTION", "RESET", "TRANSFER")

class FrontendL0M1B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L0.M1.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = FRONTEND_L0_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("STATE", "FEEDBACK", "TRANSFER")

class FrontendL0M1R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L0.M1.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = FRONTEND_L0_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L0.M1.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("VALUE", "ACTION", "RESET", "TRANSFER")

    def __init__(self, base_b1: FrontendL0M1B1Base) -> None:
        self._base_b1 = base_b1

class FrontendL0M1R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L0.M1.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = FRONTEND_L0_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L0.M1.B1", "frontend.L0.M1.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("STATE", "FEEDBACK", "TRANSFER", "VALUE", "ACTION", "RESET")

    def __init__(self, base_b1: FrontendL0M1B1Base, base_b2: FrontendL0M1B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL0M1R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L0.M1.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = FRONTEND_L0_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L0.M1.B1", "frontend.L0.M1.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("VALUE", "ACTION", "STATE", "RESET", "FEEDBACK", "TRANSFER")

    def __init__(self, base_b1: FrontendL0M1B1Base, base_b2: FrontendL0M1B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL0M1Module(ModuleContract):
    framework_module_id: ClassVar[str] = FRONTEND_L0_M1_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L0_M1_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        FrontendL0M1StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        FrontendL0M1RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            FrontendL0M1B1Base,
            FrontendL0M1B2Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            FrontendL0M1R1Rule,
            FrontendL0M1R2Rule,
            FrontendL0M1R3Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L0_M1_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: FrontendL0M1StaticBoundaryParams,
        runtime_params: FrontendL0M1RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = FrontendL0M1B1Base(self)
        self.b2 = FrontendL0M1B2Base(self)
        self.r1 = FrontendL0M1R1Rule(self.b1)
        self.r2 = FrontendL0M1R2Rule(self.b1, self.b2)
        self.r3 = FrontendL0M1R3Rule(self.b1, self.b2)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> FrontendL0M1Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, FrontendL0M1StaticBoundaryParams):
            raise TypeError("FrontendL0M1Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, FrontendL0M1RuntimeBoundaryParams):
            raise TypeError("FrontendL0M1Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)


FRONTEND_L0_M2_MODULE_ID = "frontend.L0.M2"
FRONTEND_L0_M2_MODULE_KEY = "frontend__L0__M2"
FRONTEND_L0_M2_BOUNDARY_FIELD_MAP = {
    "TOKEN": "token",
    "THEME": "theme",
    "DENSITY": "density",
    "TONE": "tone",
    "A11Y": "a11y",
}

@dataclass(frozen=True, slots=True)
class FrontendL0M2StaticBoundaryParams(StaticBoundaryParamsContract):
    token: object = None
    theme: object = None
    density: object = None
    tone: object = None
    a11y: object = None

    framework_module_id: ClassVar[str] = FRONTEND_L0_M2_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L0_M2_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L0_M2_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class FrontendL0M2RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    token: object = UNSET
    theme: object = UNSET
    density: object = UNSET
    tone: object = UNSET
    a11y: object = UNSET

    framework_module_id: ClassVar[str] = FRONTEND_L0_M2_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L0_M2_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L0_M2_BOUNDARY_FIELD_MAP)

class FrontendL0M2B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L0.M2.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = FRONTEND_L0_M2_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("TOKEN", "DENSITY")

class FrontendL0M2B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L0.M2.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = FRONTEND_L0_M2_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("THEME", "TONE", "A11Y")

class FrontendL0M2R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L0.M2.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = FRONTEND_L0_M2_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L0.M2.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("TOKEN", "DENSITY")

    def __init__(self, base_b1: FrontendL0M2B1Base) -> None:
        self._base_b1 = base_b1

class FrontendL0M2R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L0.M2.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = FRONTEND_L0_M2_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L0.M2.B1", "frontend.L0.M2.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("THEME", "TONE", "A11Y", "TOKEN", "DENSITY")

    def __init__(self, base_b1: FrontendL0M2B1Base, base_b2: FrontendL0M2B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL0M2R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L0.M2.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = FRONTEND_L0_M2_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L0.M2.B1", "frontend.L0.M2.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("TOKEN", "THEME", "DENSITY", "TONE", "A11Y")

    def __init__(self, base_b1: FrontendL0M2B1Base, base_b2: FrontendL0M2B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL0M2Module(ModuleContract):
    framework_module_id: ClassVar[str] = FRONTEND_L0_M2_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L0_M2_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        FrontendL0M2StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        FrontendL0M2RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            FrontendL0M2B1Base,
            FrontendL0M2B2Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            FrontendL0M2R1Rule,
            FrontendL0M2R2Rule,
            FrontendL0M2R3Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L0_M2_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: FrontendL0M2StaticBoundaryParams,
        runtime_params: FrontendL0M2RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = FrontendL0M2B1Base(self)
        self.b2 = FrontendL0M2B2Base(self)
        self.r1 = FrontendL0M2R1Rule(self.b1)
        self.r2 = FrontendL0M2R2Rule(self.b1, self.b2)
        self.r3 = FrontendL0M2R3Rule(self.b1, self.b2)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> FrontendL0M2Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, FrontendL0M2StaticBoundaryParams):
            raise TypeError("FrontendL0M2Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, FrontendL0M2RuntimeBoundaryParams):
            raise TypeError("FrontendL0M2Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)


FRONTEND_L1_M0_MODULE_ID = "frontend.L1.M0"
FRONTEND_L1_M0_MODULE_KEY = "frontend__L1__M0"
FRONTEND_L1_M0_BOUNDARY_FIELD_MAP = {
    "TRIGGER": "trigger",
    "PICK": "pick",
    "OPTION": "option",
    "ACTION": "action",
    "STATUS": "status",
    "A11Y": "a11y",
}

@dataclass(frozen=True, slots=True)
class FrontendL1M0StaticBoundaryParams(StaticBoundaryParamsContract):
    trigger: object = None
    pick: object = None
    option: object = None
    action: object = None
    status: object = None
    a11y: object = None

    framework_module_id: ClassVar[str] = FRONTEND_L1_M0_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L1_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L1_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class FrontendL1M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    trigger: object = UNSET
    pick: object = UNSET
    option: object = UNSET
    action: object = UNSET
    status: object = UNSET
    a11y: object = UNSET

    framework_module_id: ClassVar[str] = FRONTEND_L1_M0_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L1_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L1_M0_BOUNDARY_FIELD_MAP)

class FrontendL1M0B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L1.M0.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("TRIGGER", "ACTION", "STATUS")

class FrontendL1M0B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L1.M0.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("PICK", "OPTION", "ACTION", "A11Y")

class FrontendL1M0R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L1.M0.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L1.M0.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("TRIGGER", "ACTION", "STATUS")

    def __init__(self, base_b1: FrontendL1M0B1Base) -> None:
        self._base_b1 = base_b1

class FrontendL1M0R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L1.M0.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L1.M0.B1", "frontend.L1.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("PICK", "OPTION", "A11Y", "ACTION", "STATUS")

    def __init__(self, base_b1: FrontendL1M0B1Base, base_b2: FrontendL1M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL1M0R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L1.M0.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L1.M0.B1", "frontend.L1.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("TRIGGER", "PICK", "OPTION", "ACTION", "STATUS", "A11Y")

    def __init__(self, base_b1: FrontendL1M0B1Base, base_b2: FrontendL1M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL1M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = FRONTEND_L1_M0_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L1_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        FrontendL1M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        FrontendL1M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            FrontendL1M0B1Base,
            FrontendL1M0B2Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            FrontendL1M0R1Rule,
            FrontendL1M0R2Rule,
            FrontendL1M0R3Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L1_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: FrontendL1M0StaticBoundaryParams,
        runtime_params: FrontendL1M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = FrontendL1M0B1Base(self)
        self.b2 = FrontendL1M0B2Base(self)
        self.r1 = FrontendL1M0R1Rule(self.b1)
        self.r2 = FrontendL1M0R2Rule(self.b1, self.b2)
        self.r3 = FrontendL1M0R3Rule(self.b1, self.b2)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> FrontendL1M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, FrontendL1M0StaticBoundaryParams):
            raise TypeError("FrontendL1M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, FrontendL1M0RuntimeBoundaryParams):
            raise TypeError("FrontendL1M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)


FRONTEND_L1_M1_MODULE_ID = "frontend.L1.M1"
FRONTEND_L1_M1_MODULE_KEY = "frontend__L1__M1"
FRONTEND_L1_M1_BOUNDARY_FIELD_MAP = {
    "FIELD": "field",
    "AREA": "area",
    "VALUE": "value",
    "SUBMIT": "submit",
    "STATUS": "status",
    "A11Y": "a11y",
}

@dataclass(frozen=True, slots=True)
class FrontendL1M1StaticBoundaryParams(StaticBoundaryParamsContract):
    field: object = None
    area: object = None
    value: object = None
    submit: object = None
    status: object = None
    a11y: object = None

    framework_module_id: ClassVar[str] = FRONTEND_L1_M1_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L1_M1_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L1_M1_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class FrontendL1M1RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    field: object = UNSET
    area: object = UNSET
    value: object = UNSET
    submit: object = UNSET
    status: object = UNSET
    a11y: object = UNSET

    framework_module_id: ClassVar[str] = FRONTEND_L1_M1_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L1_M1_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L1_M1_BOUNDARY_FIELD_MAP)

class FrontendL1M1B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L1.M1.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("FIELD", "VALUE", "SUBMIT", "STATUS")

class FrontendL1M1B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L1.M1.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("AREA", "VALUE", "SUBMIT", "A11Y")

class FrontendL1M1R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L1.M1.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L1.M1.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("FIELD", "VALUE", "SUBMIT", "STATUS")

    def __init__(self, base_b1: FrontendL1M1B1Base) -> None:
        self._base_b1 = base_b1

class FrontendL1M1R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L1.M1.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L1.M1.B1", "frontend.L1.M1.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("AREA", "VALUE", "SUBMIT", "A11Y", "STATUS")

    def __init__(self, base_b1: FrontendL1M1B1Base, base_b2: FrontendL1M1B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL1M1R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L1.M1.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L1.M1.B1", "frontend.L1.M1.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("FIELD", "AREA", "VALUE", "SUBMIT", "STATUS", "A11Y")

    def __init__(self, base_b1: FrontendL1M1B1Base, base_b2: FrontendL1M1B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL1M1Module(ModuleContract):
    framework_module_id: ClassVar[str] = FRONTEND_L1_M1_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L1_M1_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        FrontendL1M1StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        FrontendL1M1RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            FrontendL1M1B1Base,
            FrontendL1M1B2Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            FrontendL1M1R1Rule,
            FrontendL1M1R2Rule,
            FrontendL1M1R3Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L1_M1_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: FrontendL1M1StaticBoundaryParams,
        runtime_params: FrontendL1M1RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = FrontendL1M1B1Base(self)
        self.b2 = FrontendL1M1B2Base(self)
        self.r1 = FrontendL1M1R1Rule(self.b1)
        self.r2 = FrontendL1M1R2Rule(self.b1, self.b2)
        self.r3 = FrontendL1M1R3Rule(self.b1, self.b2)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> FrontendL1M1Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, FrontendL1M1StaticBoundaryParams):
            raise TypeError("FrontendL1M1Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, FrontendL1M1RuntimeBoundaryParams):
            raise TypeError("FrontendL1M1Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)


FRONTEND_L1_M2_MODULE_ID = "frontend.L1.M2"
FRONTEND_L1_M2_MODULE_KEY = "frontend__L1__M2"
FRONTEND_L1_M2_BOUNDARY_FIELD_MAP = {
    "TEXT": "text",
    "PANEL": "panel",
    "VIEWPORT": "viewport",
    "META": "meta",
    "EMPTY": "empty",
    "A11Y": "a11y",
}

@dataclass(frozen=True, slots=True)
class FrontendL1M2StaticBoundaryParams(StaticBoundaryParamsContract):
    text: object = None
    panel: object = None
    viewport: object = None
    meta: object = None
    empty: object = None
    a11y: object = None

    framework_module_id: ClassVar[str] = FRONTEND_L1_M2_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L1_M2_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L1_M2_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class FrontendL1M2RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    text: object = UNSET
    panel: object = UNSET
    viewport: object = UNSET
    meta: object = UNSET
    empty: object = UNSET
    a11y: object = UNSET

    framework_module_id: ClassVar[str] = FRONTEND_L1_M2_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L1_M2_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L1_M2_BOUNDARY_FIELD_MAP)

class FrontendL1M2B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L1.M2.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M2_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("TEXT", "META", "A11Y")

class FrontendL1M2B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L1.M2.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M2_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("PANEL", "VIEWPORT", "EMPTY", "A11Y")

class FrontendL1M2R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L1.M2.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M2_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L1.M2.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("TEXT", "META", "A11Y")

    def __init__(self, base_b1: FrontendL1M2B1Base) -> None:
        self._base_b1 = base_b1

class FrontendL1M2R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L1.M2.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M2_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L1.M2.B1", "frontend.L1.M2.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("PANEL", "VIEWPORT", "EMPTY", "TEXT", "META", "A11Y")

    def __init__(self, base_b1: FrontendL1M2B1Base, base_b2: FrontendL1M2B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL1M2R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L1.M2.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M2_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L1.M2.B1", "frontend.L1.M2.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("TEXT", "PANEL", "VIEWPORT", "META", "EMPTY", "A11Y")

    def __init__(self, base_b1: FrontendL1M2B1Base, base_b2: FrontendL1M2B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL1M2Module(ModuleContract):
    framework_module_id: ClassVar[str] = FRONTEND_L1_M2_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L1_M2_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        FrontendL1M2StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        FrontendL1M2RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            FrontendL1M2B1Base,
            FrontendL1M2B2Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            FrontendL1M2R1Rule,
            FrontendL1M2R2Rule,
            FrontendL1M2R3Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L1_M2_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: FrontendL1M2StaticBoundaryParams,
        runtime_params: FrontendL1M2RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = FrontendL1M2B1Base(self)
        self.b2 = FrontendL1M2B2Base(self)
        self.r1 = FrontendL1M2R1Rule(self.b1)
        self.r2 = FrontendL1M2R2Rule(self.b1, self.b2)
        self.r3 = FrontendL1M2R3Rule(self.b1, self.b2)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> FrontendL1M2Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, FrontendL1M2StaticBoundaryParams):
            raise TypeError("FrontendL1M2Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, FrontendL1M2RuntimeBoundaryParams):
            raise TypeError("FrontendL1M2Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)


FRONTEND_L1_M3_MODULE_ID = "frontend.L1.M3"
FRONTEND_L1_M3_MODULE_KEY = "frontend__L1__M3"
FRONTEND_L1_M3_BOUNDARY_FIELD_MAP = {
    "LIST": "list",
    "TREE": "tree",
    "ITEM": "item",
    "NAV": "nav",
    "FOCUS": "focus",
    "A11Y": "a11y",
}

@dataclass(frozen=True, slots=True)
class FrontendL1M3StaticBoundaryParams(StaticBoundaryParamsContract):
    list: object = None
    tree: object = None
    item: object = None
    nav: object = None
    focus: object = None
    a11y: object = None

    framework_module_id: ClassVar[str] = FRONTEND_L1_M3_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L1_M3_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L1_M3_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class FrontendL1M3RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    list: object = UNSET
    tree: object = UNSET
    item: object = UNSET
    nav: object = UNSET
    focus: object = UNSET
    a11y: object = UNSET

    framework_module_id: ClassVar[str] = FRONTEND_L1_M3_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L1_M3_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L1_M3_BOUNDARY_FIELD_MAP)

class FrontendL1M3B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L1.M3.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M3_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("LIST", "TREE", "FOCUS")

class FrontendL1M3B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L1.M3.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M3_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("ITEM", "NAV", "FOCUS", "A11Y")

class FrontendL1M3R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L1.M3.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M3_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L1.M3.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("LIST", "TREE", "FOCUS")

    def __init__(self, base_b1: FrontendL1M3B1Base) -> None:
        self._base_b1 = base_b1

class FrontendL1M3R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L1.M3.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M3_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L1.M3.B1", "frontend.L1.M3.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("ITEM", "NAV", "FOCUS", "A11Y", "LIST", "TREE")

    def __init__(self, base_b1: FrontendL1M3B1Base, base_b2: FrontendL1M3B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL1M3R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L1.M3.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M3_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L1.M3.B1", "frontend.L1.M3.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("LIST", "TREE", "ITEM", "NAV", "FOCUS", "A11Y")

    def __init__(self, base_b1: FrontendL1M3B1Base, base_b2: FrontendL1M3B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL1M3Module(ModuleContract):
    framework_module_id: ClassVar[str] = FRONTEND_L1_M3_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L1_M3_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        FrontendL1M3StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        FrontendL1M3RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            FrontendL1M3B1Base,
            FrontendL1M3B2Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            FrontendL1M3R1Rule,
            FrontendL1M3R2Rule,
            FrontendL1M3R3Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L1_M3_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: FrontendL1M3StaticBoundaryParams,
        runtime_params: FrontendL1M3RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = FrontendL1M3B1Base(self)
        self.b2 = FrontendL1M3B2Base(self)
        self.r1 = FrontendL1M3R1Rule(self.b1)
        self.r2 = FrontendL1M3R2Rule(self.b1, self.b2)
        self.r3 = FrontendL1M3R3Rule(self.b1, self.b2)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> FrontendL1M3Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, FrontendL1M3StaticBoundaryParams):
            raise TypeError("FrontendL1M3Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, FrontendL1M3RuntimeBoundaryParams):
            raise TypeError("FrontendL1M3Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)


FRONTEND_L1_M4_MODULE_ID = "frontend.L1.M4"
FRONTEND_L1_M4_MODULE_KEY = "frontend__L1__M4"
FRONTEND_L1_M4_BOUNDARY_FIELD_MAP = {
    "TAG": "tag",
    "BUBBLE": "bubble",
    "EMPTY": "empty",
    "STATUS": "status",
    "EVENT": "event",
    "A11Y": "a11y",
}

@dataclass(frozen=True, slots=True)
class FrontendL1M4StaticBoundaryParams(StaticBoundaryParamsContract):
    tag: object = None
    bubble: object = None
    empty: object = None
    status: object = None
    event: object = None
    a11y: object = None

    framework_module_id: ClassVar[str] = FRONTEND_L1_M4_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L1_M4_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L1_M4_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class FrontendL1M4RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    tag: object = UNSET
    bubble: object = UNSET
    empty: object = UNSET
    status: object = UNSET
    event: object = UNSET
    a11y: object = UNSET

    framework_module_id: ClassVar[str] = FRONTEND_L1_M4_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L1_M4_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L1_M4_BOUNDARY_FIELD_MAP)

class FrontendL1M4B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L1.M4.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M4_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("TAG", "STATUS", "A11Y")

class FrontendL1M4B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L1.M4.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M4_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("BUBBLE", "EMPTY", "EVENT", "A11Y")

class FrontendL1M4R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L1.M4.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M4_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L1.M4.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("TAG", "STATUS", "A11Y")

    def __init__(self, base_b1: FrontendL1M4B1Base) -> None:
        self._base_b1 = base_b1

class FrontendL1M4R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L1.M4.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M4_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L1.M4.B1", "frontend.L1.M4.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("BUBBLE", "EMPTY", "EVENT", "A11Y", "TAG", "STATUS")

    def __init__(self, base_b1: FrontendL1M4B1Base, base_b2: FrontendL1M4B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL1M4R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L1.M4.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M4_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L1.M4.B1", "frontend.L1.M4.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("TAG", "BUBBLE", "EMPTY", "STATUS", "EVENT", "A11Y")

    def __init__(self, base_b1: FrontendL1M4B1Base, base_b2: FrontendL1M4B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL1M4Module(ModuleContract):
    framework_module_id: ClassVar[str] = FRONTEND_L1_M4_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L1_M4_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        FrontendL1M4StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        FrontendL1M4RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            FrontendL1M4B1Base,
            FrontendL1M4B2Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            FrontendL1M4R1Rule,
            FrontendL1M4R2Rule,
            FrontendL1M4R3Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L1_M4_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: FrontendL1M4StaticBoundaryParams,
        runtime_params: FrontendL1M4RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = FrontendL1M4B1Base(self)
        self.b2 = FrontendL1M4B2Base(self)
        self.r1 = FrontendL1M4R1Rule(self.b1)
        self.r2 = FrontendL1M4R2Rule(self.b1, self.b2)
        self.r3 = FrontendL1M4R3Rule(self.b1, self.b2)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> FrontendL1M4Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, FrontendL1M4StaticBoundaryParams):
            raise TypeError("FrontendL1M4Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, FrontendL1M4RuntimeBoundaryParams):
            raise TypeError("FrontendL1M4Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)


FRONTEND_L2_M0_MODULE_ID = "frontend.L2.M0"
FRONTEND_L2_M0_MODULE_KEY = "frontend__L2__M0"
FRONTEND_L2_M0_BOUNDARY_FIELD_MAP = {
    "SURFACE": "surface",
    "VISUAL": "visual",
    "INTERACT": "interact",
    "STATE": "state",
    "EXTEND": "extend",
    "ROUTE": "route",
    "A11Y": "a11y",
}

@dataclass(frozen=True, slots=True)
class FrontendL2M0StaticBoundaryParams(StaticBoundaryParamsContract):
    surface: object = None
    visual: object = None
    interact: object = None
    state: object = None
    extend: object = None
    route: object = None
    a11y: object = None

    framework_module_id: ClassVar[str] = FRONTEND_L2_M0_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L2_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L2_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class FrontendL2M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    surface: object = UNSET
    visual: object = UNSET
    interact: object = UNSET
    state: object = UNSET
    extend: object = UNSET
    route: object = UNSET
    a11y: object = UNSET

    framework_module_id: ClassVar[str] = FRONTEND_L2_M0_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L2_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L2_M0_BOUNDARY_FIELD_MAP)

class FrontendL2M0B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L2.M0.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = FRONTEND_L2_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("SURFACE", "VISUAL", "INTERACT", "STATE")

class FrontendL2M0B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L2.M0.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = FRONTEND_L2_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("INTERACT", "ROUTE", "EXTEND", "A11Y")

class FrontendL2M0R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L2.M0.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = FRONTEND_L2_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L2.M0.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("SURFACE", "VISUAL", "INTERACT", "STATE")

    def __init__(self, base_b1: FrontendL2M0B1Base) -> None:
        self._base_b1 = base_b1

class FrontendL2M0R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L2.M0.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = FRONTEND_L2_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L2.M0.B1", "frontend.L2.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("INTERACT", "ROUTE", "A11Y", "STATE", "EXTEND", "SURFACE", "VISUAL")

    def __init__(self, base_b1: FrontendL2M0B1Base, base_b2: FrontendL2M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL2M0R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L2.M0.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = FRONTEND_L2_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L2.M0.B1", "frontend.L2.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("SURFACE", "VISUAL", "INTERACT", "STATE", "EXTEND", "ROUTE", "A11Y")

    def __init__(self, base_b1: FrontendL2M0B1Base, base_b2: FrontendL2M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL2M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = FRONTEND_L2_M0_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L2_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        FrontendL2M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        FrontendL2M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            FrontendL2M0B1Base,
            FrontendL2M0B2Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            FrontendL2M0R1Rule,
            FrontendL2M0R2Rule,
            FrontendL2M0R3Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L2_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: FrontendL2M0StaticBoundaryParams,
        runtime_params: FrontendL2M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = FrontendL2M0B1Base(self)
        self.b2 = FrontendL2M0B2Base(self)
        self.r1 = FrontendL2M0R1Rule(self.b1)
        self.r2 = FrontendL2M0R2Rule(self.b1, self.b2)
        self.r3 = FrontendL2M0R3Rule(self.b1, self.b2)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> FrontendL2M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, FrontendL2M0StaticBoundaryParams):
            raise TypeError("FrontendL2M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, FrontendL2M0RuntimeBoundaryParams):
            raise TypeError("FrontendL2M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)


FRONTEND_L2_M1_MODULE_ID = "frontend.L2.M1"
FRONTEND_L2_M1_MODULE_KEY = "frontend__L2__M1"
FRONTEND_L2_M1_BOUNDARY_FIELD_MAP = {
    "HOST": "host",
    "RUNTIME": "runtime",
    "RENDERER": "renderer",
    "STYLE": "style",
    "SCRIPT": "script",
    "BOOT": "boot",
    "TRACE": "trace",
}

@dataclass(frozen=True, slots=True)
class FrontendL2M1StaticBoundaryParams(StaticBoundaryParamsContract):
    host: object = None
    runtime: object = None
    renderer: object = None
    style: object = None
    script: object = None
    boot: object = None
    trace: object = None

    framework_module_id: ClassVar[str] = FRONTEND_L2_M1_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L2_M1_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L2_M1_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class FrontendL2M1RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    host: object = UNSET
    runtime: object = UNSET
    renderer: object = UNSET
    style: object = UNSET
    script: object = UNSET
    boot: object = UNSET
    trace: object = UNSET

    framework_module_id: ClassVar[str] = FRONTEND_L2_M1_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L2_M1_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L2_M1_BOUNDARY_FIELD_MAP)

class FrontendL2M1B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L2.M1.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = FRONTEND_L2_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("HOST", "RENDERER", "BOOT")

class FrontendL2M1B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L2.M1.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = FRONTEND_L2_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("RUNTIME", "STYLE", "SCRIPT", "RENDERER")

class FrontendL2M1B3Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L2.M1.B3"
    framework_base_short_id: ClassVar[str] = "B3"
    owner_module_id: ClassVar[str] = FRONTEND_L2_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("BOOT", "TRACE", "HOST")

class FrontendL2M1R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L2.M1.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = FRONTEND_L2_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L2.M1.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("HOST", "RENDERER", "BOOT")

    def __init__(self, base_b1: FrontendL2M1B1Base) -> None:
        self._base_b1 = base_b1

class FrontendL2M1R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L2.M1.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = FRONTEND_L2_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L2.M1.B1", "frontend.L2.M1.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("RUNTIME", "RENDERER", "STYLE", "SCRIPT", "HOST", "BOOT")

    def __init__(self, base_b1: FrontendL2M1B1Base, base_b2: FrontendL2M1B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL2M1R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L2.M1.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = FRONTEND_L2_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L2.M1.B1", "frontend.L2.M1.B2", "frontend.L2.M1.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("BOOT", "TRACE", "HOST", "RUNTIME", "STYLE", "SCRIPT", "RENDERER")

    def __init__(self, base_b1: FrontendL2M1B1Base, base_b2: FrontendL2M1B2Base, base_b3: FrontendL2M1B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class FrontendL2M1R4Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L2.M1.R4"
    framework_rule_short_id: ClassVar[str] = "R4"
    owner_module_id: ClassVar[str] = FRONTEND_L2_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L2.M1.B1", "frontend.L2.M1.B2", "frontend.L2.M1.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("RUNTIME", "HOST", "RENDERER", "STYLE", "SCRIPT", "BOOT", "TRACE")

    def __init__(self, base_b1: FrontendL2M1B1Base, base_b2: FrontendL2M1B2Base, base_b3: FrontendL2M1B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class FrontendL2M1Module(ModuleContract):
    framework_module_id: ClassVar[str] = FRONTEND_L2_M1_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L2_M1_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        FrontendL2M1StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        FrontendL2M1RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            FrontendL2M1B1Base,
            FrontendL2M1B2Base,
            FrontendL2M1B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            FrontendL2M1R1Rule,
            FrontendL2M1R2Rule,
            FrontendL2M1R3Rule,
            FrontendL2M1R4Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L2_M1_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: FrontendL2M1StaticBoundaryParams,
        runtime_params: FrontendL2M1RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = FrontendL2M1B1Base(self)
        self.b2 = FrontendL2M1B2Base(self)
        self.b3 = FrontendL2M1B3Base(self)
        self.r1 = FrontendL2M1R1Rule(self.b1)
        self.r2 = FrontendL2M1R2Rule(self.b1, self.b2)
        self.r3 = FrontendL2M1R3Rule(self.b1, self.b2, self.b3)
        self.r4 = FrontendL2M1R4Rule(self.b1, self.b2, self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> FrontendL2M1Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, FrontendL2M1StaticBoundaryParams):
            raise TypeError("FrontendL2M1Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, FrontendL2M1RuntimeBoundaryParams):
            raise TypeError("FrontendL2M1Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)


FRONTEND_L3_M0_MODULE_ID = "frontend.L3.M0"
FRONTEND_L3_M0_MODULE_KEY = "frontend__L3__M0"
FRONTEND_L3_M0_BOUNDARY_FIELD_MAP = {
    "PAGESET": "pageset",
    "HOST": "host",
    "RUNTIME": "runtime",
    "BOOT": "boot",
    "TRACE": "trace",
    "ROUTE": "route",
    "RETURN": "return_value",
}

@dataclass(frozen=True, slots=True)
class FrontendL3M0StaticBoundaryParams(StaticBoundaryParamsContract):
    pageset: object = None
    host: object = None
    runtime: object = None
    boot: object = None
    trace: object = None
    route: object = None
    return_value: object = None

    framework_module_id: ClassVar[str] = FRONTEND_L3_M0_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L3_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L3_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class FrontendL3M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    pageset: object = UNSET
    host: object = UNSET
    runtime: object = UNSET
    boot: object = UNSET
    trace: object = UNSET
    route: object = UNSET
    return_value: object = UNSET

    framework_module_id: ClassVar[str] = FRONTEND_L3_M0_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L3_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L3_M0_BOUNDARY_FIELD_MAP)

class FrontendL3M0B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L3.M0.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = FRONTEND_L3_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("PAGESET", "HOST", "ROUTE", "RETURN")

class FrontendL3M0B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L3.M0.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = FRONTEND_L3_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("RUNTIME", "BOOT", "TRACE")

class FrontendL3M0B3Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L3.M0.B3"
    framework_base_short_id: ClassVar[str] = "B3"
    owner_module_id: ClassVar[str] = FRONTEND_L3_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("HOST", "BOOT", "TRACE", "ROUTE")

class FrontendL3M0R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L3.M0.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = FRONTEND_L3_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L3.M0.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("PAGESET", "HOST", "ROUTE", "RETURN")

    def __init__(self, base_b1: FrontendL3M0B1Base) -> None:
        self._base_b1 = base_b1

class FrontendL3M0R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L3.M0.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = FRONTEND_L3_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L3.M0.B1", "frontend.L3.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("RUNTIME", "HOST", "BOOT", "TRACE", "PAGESET", "ROUTE", "RETURN")

    def __init__(self, base_b1: FrontendL3M0B1Base, base_b2: FrontendL3M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL3M0R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L3.M0.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = FRONTEND_L3_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L3.M0.B1", "frontend.L3.M0.B2", "frontend.L3.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("BOOT", "TRACE", "HOST", "RUNTIME", "ROUTE", "RETURN", "PAGESET")

    def __init__(self, base_b1: FrontendL3M0B1Base, base_b2: FrontendL3M0B2Base, base_b3: FrontendL3M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class FrontendL3M0R4Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L3.M0.R4"
    framework_rule_short_id: ClassVar[str] = "R4"
    owner_module_id: ClassVar[str] = FRONTEND_L3_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L3.M0.B1", "frontend.L3.M0.B2", "frontend.L3.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("RUNTIME", "HOST", "BOOT", "TRACE", "PAGESET", "ROUTE", "RETURN")

    def __init__(self, base_b1: FrontendL3M0B1Base, base_b2: FrontendL3M0B2Base, base_b3: FrontendL3M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class FrontendL3M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = FRONTEND_L3_M0_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L3_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        FrontendL3M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        FrontendL3M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            FrontendL3M0B1Base,
            FrontendL3M0B2Base,
            FrontendL3M0B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            FrontendL3M0R1Rule,
            FrontendL3M0R2Rule,
            FrontendL3M0R3Rule,
            FrontendL3M0R4Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L3_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: FrontendL3M0StaticBoundaryParams,
        runtime_params: FrontendL3M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = FrontendL3M0B1Base(self)
        self.b2 = FrontendL3M0B2Base(self)
        self.b3 = FrontendL3M0B3Base(self)
        self.r1 = FrontendL3M0R1Rule(self.b1)
        self.r2 = FrontendL3M0R2Rule(self.b1, self.b2)
        self.r3 = FrontendL3M0R3Rule(self.b1, self.b2, self.b3)
        self.r4 = FrontendL3M0R4Rule(self.b1, self.b2, self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> FrontendL3M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, FrontendL3M0StaticBoundaryParams):
            raise TypeError("FrontendL3M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, FrontendL3M0RuntimeBoundaryParams):
            raise TypeError("FrontendL3M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)


KNOWLEDGE_BASE_L0_M0_MODULE_ID = "knowledge_base.L0.M0"
KNOWLEDGE_BASE_L0_M0_MODULE_KEY = "knowledge_base__L0__M0"
KNOWLEDGE_BASE_L0_M0_BOUNDARY_FIELD_MAP = {
    "FILESET": "fileset",
    "INGEST": "ingest",
    "CLASSIFY": "classify",
    "LIMIT": "limit",
    "VISIBILITY": "visibility",
    "A11Y": "a11y",
}

@dataclass(frozen=True, slots=True)
class KnowledgeBaseL0M0StaticBoundaryParams(StaticBoundaryParamsContract):
    fileset: object = None
    ingest: object = None
    classify: object = None
    limit: object = None
    visibility: object = None
    a11y: object = None

    framework_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M0_MODULE_ID
    module_key: ClassVar[str] = KNOWLEDGE_BASE_L0_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(KNOWLEDGE_BASE_L0_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class KnowledgeBaseL0M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    fileset: object = UNSET
    ingest: object = UNSET
    classify: object = UNSET
    limit: object = UNSET
    visibility: object = UNSET
    a11y: object = UNSET

    framework_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M0_MODULE_ID
    module_key: ClassVar[str] = KNOWLEDGE_BASE_L0_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(KNOWLEDGE_BASE_L0_M0_BOUNDARY_FIELD_MAP)

class KnowledgeBaseL0M0B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "knowledge_base.L0.M0.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("FILESET", "VISIBILITY", "A11Y")

class KnowledgeBaseL0M0B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "knowledge_base.L0.M0.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("INGEST", "LIMIT", "A11Y")

class KnowledgeBaseL0M0B3Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "knowledge_base.L0.M0.B3"
    framework_base_short_id: ClassVar[str] = "B3"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("CLASSIFY", "LIMIT", "VISIBILITY")

class KnowledgeBaseL0M0R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L0.M0.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L0.M0.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("FILESET", "VISIBILITY", "A11Y")

    def __init__(self, base_b1: KnowledgeBaseL0M0B1Base) -> None:
        self._base_b1 = base_b1

class KnowledgeBaseL0M0R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L0.M0.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L0.M0.B1", "knowledge_base.L0.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("INGEST", "LIMIT", "FILESET", "VISIBILITY")

    def __init__(self, base_b1: KnowledgeBaseL0M0B1Base, base_b2: KnowledgeBaseL0M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class KnowledgeBaseL0M0R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L0.M0.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L0.M0.B1", "knowledge_base.L0.M0.B2", "knowledge_base.L0.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("CLASSIFY", "LIMIT", "VISIBILITY", "INGEST", "A11Y")

    def __init__(self, base_b1: KnowledgeBaseL0M0B1Base, base_b2: KnowledgeBaseL0M0B2Base, base_b3: KnowledgeBaseL0M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class KnowledgeBaseL0M0R4Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L0.M0.R4"
    framework_rule_short_id: ClassVar[str] = "R4"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L0.M0.B1", "knowledge_base.L0.M0.B2", "knowledge_base.L0.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("FILESET", "INGEST", "CLASSIFY", "LIMIT", "VISIBILITY", "A11Y")

    def __init__(self, base_b1: KnowledgeBaseL0M0B1Base, base_b2: KnowledgeBaseL0M0B2Base, base_b3: KnowledgeBaseL0M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class KnowledgeBaseL0M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M0_MODULE_ID
    module_key: ClassVar[str] = KNOWLEDGE_BASE_L0_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        KnowledgeBaseL0M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        KnowledgeBaseL0M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            KnowledgeBaseL0M0B1Base,
            KnowledgeBaseL0M0B2Base,
            KnowledgeBaseL0M0B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            KnowledgeBaseL0M0R1Rule,
            KnowledgeBaseL0M0R2Rule,
            KnowledgeBaseL0M0R3Rule,
            KnowledgeBaseL0M0R4Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(KNOWLEDGE_BASE_L0_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: KnowledgeBaseL0M0StaticBoundaryParams,
        runtime_params: KnowledgeBaseL0M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = KnowledgeBaseL0M0B1Base(self)
        self.b2 = KnowledgeBaseL0M0B2Base(self)
        self.b3 = KnowledgeBaseL0M0B3Base(self)
        self.r1 = KnowledgeBaseL0M0R1Rule(self.b1)
        self.r2 = KnowledgeBaseL0M0R2Rule(self.b1, self.b2)
        self.r3 = KnowledgeBaseL0M0R3Rule(self.b1, self.b2, self.b3)
        self.r4 = KnowledgeBaseL0M0R4Rule(self.b1, self.b2, self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> KnowledgeBaseL0M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, KnowledgeBaseL0M0StaticBoundaryParams):
            raise TypeError("KnowledgeBaseL0M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, KnowledgeBaseL0M0RuntimeBoundaryParams):
            raise TypeError("KnowledgeBaseL0M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)


KNOWLEDGE_BASE_L0_M1_MODULE_ID = "knowledge_base.L0.M1"
KNOWLEDGE_BASE_L0_M1_MODULE_KEY = "knowledge_base__L0__M1"
KNOWLEDGE_BASE_L0_M1_BOUNDARY_FIELD_MAP = {
    "DOCVIEW": "docview",
    "TOC": "toc",
    "META": "meta",
    "FOCUS": "focus",
    "EMPTY": "empty",
    "A11Y": "a11y",
}

@dataclass(frozen=True, slots=True)
class KnowledgeBaseL0M1StaticBoundaryParams(StaticBoundaryParamsContract):
    docview: object = None
    toc: object = None
    meta: object = None
    focus: object = None
    empty: object = None
    a11y: object = None

    framework_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M1_MODULE_ID
    module_key: ClassVar[str] = KNOWLEDGE_BASE_L0_M1_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(KNOWLEDGE_BASE_L0_M1_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class KnowledgeBaseL0M1RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    docview: object = UNSET
    toc: object = UNSET
    meta: object = UNSET
    focus: object = UNSET
    empty: object = UNSET
    a11y: object = UNSET

    framework_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M1_MODULE_ID
    module_key: ClassVar[str] = KNOWLEDGE_BASE_L0_M1_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(KNOWLEDGE_BASE_L0_M1_BOUNDARY_FIELD_MAP)

class KnowledgeBaseL0M1B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "knowledge_base.L0.M1.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("DOCVIEW", "META", "A11Y")

class KnowledgeBaseL0M1B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "knowledge_base.L0.M1.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("TOC", "FOCUS", "A11Y")

class KnowledgeBaseL0M1B3Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "knowledge_base.L0.M1.B3"
    framework_base_short_id: ClassVar[str] = "B3"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("FOCUS", "EMPTY", "A11Y")

class KnowledgeBaseL0M1R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L0.M1.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L0.M1.B1", "knowledge_base.L0.M1.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("DOCVIEW", "TOC", "META", "FOCUS")

    def __init__(self, base_b1: KnowledgeBaseL0M1B1Base, base_b2: KnowledgeBaseL0M1B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class KnowledgeBaseL0M1R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L0.M1.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L0.M1.B1", "knowledge_base.L0.M1.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("FOCUS", "EMPTY", "A11Y", "DOCVIEW")

    def __init__(self, base_b1: KnowledgeBaseL0M1B1Base, base_b3: KnowledgeBaseL0M1B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b3 = base_b3

class KnowledgeBaseL0M1R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L0.M1.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L0.M1.B1", "knowledge_base.L0.M1.B2", "knowledge_base.L0.M1.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("DOCVIEW", "TOC", "META", "FOCUS", "EMPTY", "A11Y")

    def __init__(self, base_b1: KnowledgeBaseL0M1B1Base, base_b2: KnowledgeBaseL0M1B2Base, base_b3: KnowledgeBaseL0M1B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class KnowledgeBaseL0M1R4Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L0.M1.R4"
    framework_rule_short_id: ClassVar[str] = "R4"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L0.M1.B1", "knowledge_base.L0.M1.B2", "knowledge_base.L0.M1.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("DOCVIEW", "TOC", "META", "FOCUS", "EMPTY", "A11Y")

    def __init__(self, base_b1: KnowledgeBaseL0M1B1Base, base_b2: KnowledgeBaseL0M1B2Base, base_b3: KnowledgeBaseL0M1B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class KnowledgeBaseL0M1Module(ModuleContract):
    framework_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M1_MODULE_ID
    module_key: ClassVar[str] = KNOWLEDGE_BASE_L0_M1_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        KnowledgeBaseL0M1StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        KnowledgeBaseL0M1RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            KnowledgeBaseL0M1B1Base,
            KnowledgeBaseL0M1B2Base,
            KnowledgeBaseL0M1B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            KnowledgeBaseL0M1R1Rule,
            KnowledgeBaseL0M1R2Rule,
            KnowledgeBaseL0M1R3Rule,
            KnowledgeBaseL0M1R4Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(KNOWLEDGE_BASE_L0_M1_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: KnowledgeBaseL0M1StaticBoundaryParams,
        runtime_params: KnowledgeBaseL0M1RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = KnowledgeBaseL0M1B1Base(self)
        self.b2 = KnowledgeBaseL0M1B2Base(self)
        self.b3 = KnowledgeBaseL0M1B3Base(self)
        self.r1 = KnowledgeBaseL0M1R1Rule(self.b1, self.b2)
        self.r2 = KnowledgeBaseL0M1R2Rule(self.b1, self.b3)
        self.r3 = KnowledgeBaseL0M1R3Rule(self.b1, self.b2, self.b3)
        self.r4 = KnowledgeBaseL0M1R4Rule(self.b1, self.b2, self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> KnowledgeBaseL0M1Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, KnowledgeBaseL0M1StaticBoundaryParams):
            raise TypeError("KnowledgeBaseL0M1Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, KnowledgeBaseL0M1RuntimeBoundaryParams):
            raise TypeError("KnowledgeBaseL0M1Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)


KNOWLEDGE_BASE_L0_M2_MODULE_ID = "knowledge_base.L0.M2"
KNOWLEDGE_BASE_L0_M2_MODULE_KEY = "knowledge_base__L0__M2"
KNOWLEDGE_BASE_L0_M2_BOUNDARY_FIELD_MAP = {
    "TURN": "turn",
    "INPUT": "input",
    "CITATION": "citation",
    "SCOPE": "scope",
    "STATUS": "status",
    "A11Y": "a11y",
}

@dataclass(frozen=True, slots=True)
class KnowledgeBaseL0M2StaticBoundaryParams(StaticBoundaryParamsContract):
    turn: object = None
    input: object = None
    citation: object = None
    scope: object = None
    status: object = None
    a11y: object = None

    framework_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M2_MODULE_ID
    module_key: ClassVar[str] = KNOWLEDGE_BASE_L0_M2_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(KNOWLEDGE_BASE_L0_M2_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class KnowledgeBaseL0M2RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    turn: object = UNSET
    input: object = UNSET
    citation: object = UNSET
    scope: object = UNSET
    status: object = UNSET
    a11y: object = UNSET

    framework_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M2_MODULE_ID
    module_key: ClassVar[str] = KNOWLEDGE_BASE_L0_M2_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(KNOWLEDGE_BASE_L0_M2_BOUNDARY_FIELD_MAP)

class KnowledgeBaseL0M2B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "knowledge_base.L0.M2.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M2_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("TURN", "STATUS", "A11Y")

class KnowledgeBaseL0M2B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "knowledge_base.L0.M2.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M2_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("INPUT", "A11Y", "STATUS")

class KnowledgeBaseL0M2B3Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "knowledge_base.L0.M2.B3"
    framework_base_short_id: ClassVar[str] = "B3"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M2_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("CITATION", "SCOPE")

class KnowledgeBaseL0M2R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L0.M2.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M2_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L0.M2.B1", "knowledge_base.L0.M2.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("TURN", "INPUT", "STATUS", "A11Y")

    def __init__(self, base_b1: KnowledgeBaseL0M2B1Base, base_b2: KnowledgeBaseL0M2B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class KnowledgeBaseL0M2R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L0.M2.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M2_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L0.M2.B1", "knowledge_base.L0.M2.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("CITATION", "SCOPE", "TURN", "STATUS")

    def __init__(self, base_b1: KnowledgeBaseL0M2B1Base, base_b3: KnowledgeBaseL0M2B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b3 = base_b3

class KnowledgeBaseL0M2R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L0.M2.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M2_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L0.M2.B1", "knowledge_base.L0.M2.B2", "knowledge_base.L0.M2.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("TURN", "INPUT", "CITATION", "SCOPE", "STATUS", "A11Y")

    def __init__(self, base_b1: KnowledgeBaseL0M2B1Base, base_b2: KnowledgeBaseL0M2B2Base, base_b3: KnowledgeBaseL0M2B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class KnowledgeBaseL0M2R4Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L0.M2.R4"
    framework_rule_short_id: ClassVar[str] = "R4"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M2_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L0.M2.B1", "knowledge_base.L0.M2.B2", "knowledge_base.L0.M2.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("TURN", "INPUT", "CITATION", "SCOPE", "STATUS", "A11Y")

    def __init__(self, base_b1: KnowledgeBaseL0M2B1Base, base_b2: KnowledgeBaseL0M2B2Base, base_b3: KnowledgeBaseL0M2B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class KnowledgeBaseL0M2Module(ModuleContract):
    framework_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M2_MODULE_ID
    module_key: ClassVar[str] = KNOWLEDGE_BASE_L0_M2_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        KnowledgeBaseL0M2StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        KnowledgeBaseL0M2RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            KnowledgeBaseL0M2B1Base,
            KnowledgeBaseL0M2B2Base,
            KnowledgeBaseL0M2B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            KnowledgeBaseL0M2R1Rule,
            KnowledgeBaseL0M2R2Rule,
            KnowledgeBaseL0M2R3Rule,
            KnowledgeBaseL0M2R4Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(KNOWLEDGE_BASE_L0_M2_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: KnowledgeBaseL0M2StaticBoundaryParams,
        runtime_params: KnowledgeBaseL0M2RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = KnowledgeBaseL0M2B1Base(self)
        self.b2 = KnowledgeBaseL0M2B2Base(self)
        self.b3 = KnowledgeBaseL0M2B3Base(self)
        self.r1 = KnowledgeBaseL0M2R1Rule(self.b1, self.b2)
        self.r2 = KnowledgeBaseL0M2R2Rule(self.b1, self.b3)
        self.r3 = KnowledgeBaseL0M2R3Rule(self.b1, self.b2, self.b3)
        self.r4 = KnowledgeBaseL0M2R4Rule(self.b1, self.b2, self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> KnowledgeBaseL0M2Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, KnowledgeBaseL0M2StaticBoundaryParams):
            raise TypeError("KnowledgeBaseL0M2Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, KnowledgeBaseL0M2RuntimeBoundaryParams):
            raise TypeError("KnowledgeBaseL0M2Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)


KNOWLEDGE_BASE_L1_M0_MODULE_ID = "knowledge_base.L1.M0"
KNOWLEDGE_BASE_L1_M0_MODULE_KEY = "knowledge_base__L1__M0"
KNOWLEDGE_BASE_L1_M0_BOUNDARY_FIELD_MAP = {
    "REGION": "region",
    "FOCUS": "focus",
    "EMPTY": "empty",
    "RESPONSIVE": "responsive",
    "ENTRY": "entry",
    "A11Y": "a11y",
}

@dataclass(frozen=True, slots=True)
class KnowledgeBaseL1M0StaticBoundaryParams(StaticBoundaryParamsContract):
    region: object = None
    focus: object = None
    empty: object = None
    responsive: object = None
    entry: object = None
    a11y: object = None

    framework_module_id: ClassVar[str] = KNOWLEDGE_BASE_L1_M0_MODULE_ID
    module_key: ClassVar[str] = KNOWLEDGE_BASE_L1_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(KNOWLEDGE_BASE_L1_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class KnowledgeBaseL1M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    region: object = UNSET
    focus: object = UNSET
    empty: object = UNSET
    responsive: object = UNSET
    entry: object = UNSET
    a11y: object = UNSET

    framework_module_id: ClassVar[str] = KNOWLEDGE_BASE_L1_M0_MODULE_ID
    module_key: ClassVar[str] = KNOWLEDGE_BASE_L1_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(KNOWLEDGE_BASE_L1_M0_BOUNDARY_FIELD_MAP)

class KnowledgeBaseL1M0B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "knowledge_base.L1.M0.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L1_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("REGION", "ENTRY", "EMPTY")

class KnowledgeBaseL1M0B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "knowledge_base.L1.M0.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L1_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("FOCUS", "REGION", "A11Y")

class KnowledgeBaseL1M0B3Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "knowledge_base.L1.M0.B3"
    framework_base_short_id: ClassVar[str] = "B3"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L1_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("RESPONSIVE", "EMPTY", "FOCUS")

class KnowledgeBaseL1M0R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L1.M0.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L1.M0.B1", "knowledge_base.L1.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("REGION", "FOCUS", "ENTRY", "A11Y")

    def __init__(self, base_b1: KnowledgeBaseL1M0B1Base, base_b2: KnowledgeBaseL1M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class KnowledgeBaseL1M0R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L1.M0.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L1.M0.B1", "knowledge_base.L1.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("EMPTY", "RESPONSIVE", "REGION", "ENTRY")

    def __init__(self, base_b1: KnowledgeBaseL1M0B1Base, base_b3: KnowledgeBaseL1M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b3 = base_b3

class KnowledgeBaseL1M0R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L1.M0.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L1.M0.B1", "knowledge_base.L1.M0.B2", "knowledge_base.L1.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("REGION", "FOCUS", "EMPTY", "RESPONSIVE", "ENTRY", "A11Y")

    def __init__(self, base_b1: KnowledgeBaseL1M0B1Base, base_b2: KnowledgeBaseL1M0B2Base, base_b3: KnowledgeBaseL1M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class KnowledgeBaseL1M0R4Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L1.M0.R4"
    framework_rule_short_id: ClassVar[str] = "R4"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L1.M0.B1", "knowledge_base.L1.M0.B2", "knowledge_base.L1.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("REGION", "FOCUS", "EMPTY", "RESPONSIVE", "ENTRY", "A11Y")

    def __init__(self, base_b1: KnowledgeBaseL1M0B1Base, base_b2: KnowledgeBaseL1M0B2Base, base_b3: KnowledgeBaseL1M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class KnowledgeBaseL1M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = KNOWLEDGE_BASE_L1_M0_MODULE_ID
    module_key: ClassVar[str] = KNOWLEDGE_BASE_L1_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        KnowledgeBaseL1M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        KnowledgeBaseL1M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            KnowledgeBaseL1M0B1Base,
            KnowledgeBaseL1M0B2Base,
            KnowledgeBaseL1M0B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            KnowledgeBaseL1M0R1Rule,
            KnowledgeBaseL1M0R2Rule,
            KnowledgeBaseL1M0R3Rule,
            KnowledgeBaseL1M0R4Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(KNOWLEDGE_BASE_L1_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: KnowledgeBaseL1M0StaticBoundaryParams,
        runtime_params: KnowledgeBaseL1M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = KnowledgeBaseL1M0B1Base(self)
        self.b2 = KnowledgeBaseL1M0B2Base(self)
        self.b3 = KnowledgeBaseL1M0B3Base(self)
        self.r1 = KnowledgeBaseL1M0R1Rule(self.b1, self.b2)
        self.r2 = KnowledgeBaseL1M0R2Rule(self.b1, self.b3)
        self.r3 = KnowledgeBaseL1M0R3Rule(self.b1, self.b2, self.b3)
        self.r4 = KnowledgeBaseL1M0R4Rule(self.b1, self.b2, self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> KnowledgeBaseL1M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, KnowledgeBaseL1M0StaticBoundaryParams):
            raise TypeError("KnowledgeBaseL1M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, KnowledgeBaseL1M0RuntimeBoundaryParams):
            raise TypeError("KnowledgeBaseL1M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)


KNOWLEDGE_BASE_L1_M1_MODULE_ID = "knowledge_base.L1.M1"
KNOWLEDGE_BASE_L1_M1_MODULE_KEY = "knowledge_base__L1__M1"
KNOWLEDGE_BASE_L1_M1_BOUNDARY_FIELD_MAP = {
    "SCOPE": "scope",
    "ANCHOR": "anchor",
    "TURNLINK": "turnlink",
    "RETURN": "return_value",
    "TRACE": "trace",
    "STATUS": "status",
}

@dataclass(frozen=True, slots=True)
class KnowledgeBaseL1M1StaticBoundaryParams(StaticBoundaryParamsContract):
    scope: object = None
    anchor: object = None
    turnlink: object = None
    return_value: object = None
    trace: object = None
    status: object = None

    framework_module_id: ClassVar[str] = KNOWLEDGE_BASE_L1_M1_MODULE_ID
    module_key: ClassVar[str] = KNOWLEDGE_BASE_L1_M1_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(KNOWLEDGE_BASE_L1_M1_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class KnowledgeBaseL1M1RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    scope: object = UNSET
    anchor: object = UNSET
    turnlink: object = UNSET
    return_value: object = UNSET
    trace: object = UNSET
    status: object = UNSET

    framework_module_id: ClassVar[str] = KNOWLEDGE_BASE_L1_M1_MODULE_ID
    module_key: ClassVar[str] = KNOWLEDGE_BASE_L1_M1_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(KNOWLEDGE_BASE_L1_M1_BOUNDARY_FIELD_MAP)

class KnowledgeBaseL1M1B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "knowledge_base.L1.M1.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L1_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("SCOPE", "STATUS", "TRACE")

class KnowledgeBaseL1M1B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "knowledge_base.L1.M1.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L1_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("ANCHOR", "RETURN", "TURNLINK")

class KnowledgeBaseL1M1B3Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "knowledge_base.L1.M1.B3"
    framework_base_short_id: ClassVar[str] = "B3"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L1_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("SCOPE", "ANCHOR", "TRACE")

class KnowledgeBaseL1M1R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L1.M1.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L1_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L1.M1.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("SCOPE", "TURNLINK", "STATUS", "TRACE")

    def __init__(self, base_b1: KnowledgeBaseL1M1B1Base) -> None:
        self._base_b1 = base_b1

class KnowledgeBaseL1M1R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L1.M1.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L1_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L1.M1.B1", "knowledge_base.L1.M1.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("ANCHOR", "RETURN", "TURNLINK", "SCOPE")

    def __init__(self, base_b1: KnowledgeBaseL1M1B1Base, base_b2: KnowledgeBaseL1M1B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class KnowledgeBaseL1M1R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L1.M1.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L1_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L1.M1.B1", "knowledge_base.L1.M1.B2", "knowledge_base.L1.M1.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("SCOPE", "ANCHOR", "TURNLINK", "RETURN", "TRACE", "STATUS")

    def __init__(self, base_b1: KnowledgeBaseL1M1B1Base, base_b2: KnowledgeBaseL1M1B2Base, base_b3: KnowledgeBaseL1M1B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class KnowledgeBaseL1M1R4Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L1.M1.R4"
    framework_rule_short_id: ClassVar[str] = "R4"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L1_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L1.M1.B1", "knowledge_base.L1.M1.B2", "knowledge_base.L1.M1.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("SCOPE", "ANCHOR", "TURNLINK", "RETURN", "TRACE", "STATUS")

    def __init__(self, base_b1: KnowledgeBaseL1M1B1Base, base_b2: KnowledgeBaseL1M1B2Base, base_b3: KnowledgeBaseL1M1B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class KnowledgeBaseL1M1Module(ModuleContract):
    framework_module_id: ClassVar[str] = KNOWLEDGE_BASE_L1_M1_MODULE_ID
    module_key: ClassVar[str] = KNOWLEDGE_BASE_L1_M1_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        KnowledgeBaseL1M1StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        KnowledgeBaseL1M1RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            KnowledgeBaseL1M1B1Base,
            KnowledgeBaseL1M1B2Base,
            KnowledgeBaseL1M1B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            KnowledgeBaseL1M1R1Rule,
            KnowledgeBaseL1M1R2Rule,
            KnowledgeBaseL1M1R3Rule,
            KnowledgeBaseL1M1R4Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(KNOWLEDGE_BASE_L1_M1_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: KnowledgeBaseL1M1StaticBoundaryParams,
        runtime_params: KnowledgeBaseL1M1RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = KnowledgeBaseL1M1B1Base(self)
        self.b2 = KnowledgeBaseL1M1B2Base(self)
        self.b3 = KnowledgeBaseL1M1B3Base(self)
        self.r1 = KnowledgeBaseL1M1R1Rule(self.b1)
        self.r2 = KnowledgeBaseL1M1R2Rule(self.b1, self.b2)
        self.r3 = KnowledgeBaseL1M1R3Rule(self.b1, self.b2, self.b3)
        self.r4 = KnowledgeBaseL1M1R4Rule(self.b1, self.b2, self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> KnowledgeBaseL1M1Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, KnowledgeBaseL1M1StaticBoundaryParams):
            raise TypeError("KnowledgeBaseL1M1Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, KnowledgeBaseL1M1RuntimeBoundaryParams):
            raise TypeError("KnowledgeBaseL1M1Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)


KNOWLEDGE_BASE_L2_M0_MODULE_ID = "knowledge_base.L2.M0"
KNOWLEDGE_BASE_L2_M0_MODULE_KEY = "knowledge_base__L2__M0"
KNOWLEDGE_BASE_L2_M0_BOUNDARY_FIELD_MAP = {
    "SURFACE": "surface",
    "LIBRARY": "library",
    "PREVIEW": "preview",
    "CHAT": "chat",
    "CONTEXT": "context",
    "RETURN": "return_value",
}

@dataclass(frozen=True, slots=True)
class KnowledgeBaseL2M0StaticBoundaryParams(StaticBoundaryParamsContract):
    surface: object = None
    library: object = None
    preview: object = None
    chat: object = None
    context: object = None
    return_value: object = None

    framework_module_id: ClassVar[str] = KNOWLEDGE_BASE_L2_M0_MODULE_ID
    module_key: ClassVar[str] = KNOWLEDGE_BASE_L2_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(KNOWLEDGE_BASE_L2_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class KnowledgeBaseL2M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    surface: object = UNSET
    library: object = UNSET
    preview: object = UNSET
    chat: object = UNSET
    context: object = UNSET
    return_value: object = UNSET

    framework_module_id: ClassVar[str] = KNOWLEDGE_BASE_L2_M0_MODULE_ID
    module_key: ClassVar[str] = KNOWLEDGE_BASE_L2_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(KNOWLEDGE_BASE_L2_M0_BOUNDARY_FIELD_MAP)

class KnowledgeBaseL2M0B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "knowledge_base.L2.M0.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L2_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("SURFACE", "LIBRARY", "PREVIEW")

class KnowledgeBaseL2M0B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "knowledge_base.L2.M0.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L2_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("CHAT", "CONTEXT", "RETURN")

class KnowledgeBaseL2M0B3Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "knowledge_base.L2.M0.B3"
    framework_base_short_id: ClassVar[str] = "B3"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L2_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("SURFACE", "CONTEXT", "RETURN")

class KnowledgeBaseL2M0R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L2.M0.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L2_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L2.M0.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("SURFACE", "LIBRARY", "PREVIEW")

    def __init__(self, base_b1: KnowledgeBaseL2M0B1Base) -> None:
        self._base_b1 = base_b1

class KnowledgeBaseL2M0R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L2.M0.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L2_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L2.M0.B1", "knowledge_base.L2.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("CHAT", "CONTEXT", "RETURN", "LIBRARY", "PREVIEW")

    def __init__(self, base_b1: KnowledgeBaseL2M0B1Base, base_b2: KnowledgeBaseL2M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class KnowledgeBaseL2M0R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L2.M0.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L2_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L2.M0.B1", "knowledge_base.L2.M0.B2", "knowledge_base.L2.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("SURFACE", "LIBRARY", "PREVIEW", "CHAT", "CONTEXT", "RETURN")

    def __init__(self, base_b1: KnowledgeBaseL2M0B1Base, base_b2: KnowledgeBaseL2M0B2Base, base_b3: KnowledgeBaseL2M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class KnowledgeBaseL2M0R4Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L2.M0.R4"
    framework_rule_short_id: ClassVar[str] = "R4"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L2_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L2.M0.B1", "knowledge_base.L2.M0.B2", "knowledge_base.L2.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("SURFACE", "LIBRARY", "PREVIEW", "CHAT", "CONTEXT", "RETURN")

    def __init__(self, base_b1: KnowledgeBaseL2M0B1Base, base_b2: KnowledgeBaseL2M0B2Base, base_b3: KnowledgeBaseL2M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class KnowledgeBaseL2M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = KNOWLEDGE_BASE_L2_M0_MODULE_ID
    module_key: ClassVar[str] = KNOWLEDGE_BASE_L2_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        KnowledgeBaseL2M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        KnowledgeBaseL2M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            KnowledgeBaseL2M0B1Base,
            KnowledgeBaseL2M0B2Base,
            KnowledgeBaseL2M0B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            KnowledgeBaseL2M0R1Rule,
            KnowledgeBaseL2M0R2Rule,
            KnowledgeBaseL2M0R3Rule,
            KnowledgeBaseL2M0R4Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(KNOWLEDGE_BASE_L2_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: KnowledgeBaseL2M0StaticBoundaryParams,
        runtime_params: KnowledgeBaseL2M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = KnowledgeBaseL2M0B1Base(self)
        self.b2 = KnowledgeBaseL2M0B2Base(self)
        self.b3 = KnowledgeBaseL2M0B3Base(self)
        self.r1 = KnowledgeBaseL2M0R1Rule(self.b1)
        self.r2 = KnowledgeBaseL2M0R2Rule(self.b1, self.b2)
        self.r3 = KnowledgeBaseL2M0R3Rule(self.b1, self.b2, self.b3)
        self.r4 = KnowledgeBaseL2M0R4Rule(self.b1, self.b2, self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> KnowledgeBaseL2M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, KnowledgeBaseL2M0StaticBoundaryParams):
            raise TypeError("KnowledgeBaseL2M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, KnowledgeBaseL2M0RuntimeBoundaryParams):
            raise TypeError("KnowledgeBaseL2M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)


MESSAGE_QUEUE_L0_M0_MODULE_ID = "message_queue.L0.M0"
MESSAGE_QUEUE_L0_M0_MODULE_KEY = "message_queue__L0__M0"
MESSAGE_QUEUE_L0_M0_BOUNDARY_FIELD_MAP = {
    "MESSAGEFORM": "messageform",
    "CAPACITY": "capacity",
    "LIFETIME": "lifetime",
    "ORDERRANGE": "orderrange",
    "HANDOFF": "handoff",
    "ACCESSRELATION": "accessrelation",
}

@dataclass(frozen=True, slots=True)
class MessageQueueL0M0StaticBoundaryParams(StaticBoundaryParamsContract):
    messageform: object = None
    capacity: object = None
    lifetime: object = None
    orderrange: object = None
    handoff: object = None
    accessrelation: object = None

    framework_module_id: ClassVar[str] = MESSAGE_QUEUE_L0_M0_MODULE_ID
    module_key: ClassVar[str] = MESSAGE_QUEUE_L0_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(MESSAGE_QUEUE_L0_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class MessageQueueL0M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    messageform: object = UNSET
    capacity: object = UNSET
    lifetime: object = UNSET
    orderrange: object = UNSET
    handoff: object = UNSET
    accessrelation: object = UNSET

    framework_module_id: ClassVar[str] = MESSAGE_QUEUE_L0_M0_MODULE_ID
    module_key: ClassVar[str] = MESSAGE_QUEUE_L0_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(MESSAGE_QUEUE_L0_M0_BOUNDARY_FIELD_MAP)

class MessageQueueL0M0B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "message_queue.L0.M0.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = MESSAGE_QUEUE_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("MESSAGEFORM", "CAPACITY", "LIFETIME")

class MessageQueueL0M0B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "message_queue.L0.M0.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = MESSAGE_QUEUE_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("ORDERRANGE", "HANDOFF", "LIFETIME")

class MessageQueueL0M0B3Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "message_queue.L0.M0.B3"
    framework_base_short_id: ClassVar[str] = "B3"
    owner_module_id: ClassVar[str] = MESSAGE_QUEUE_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("ACCESSRELATION", "HANDOFF")

class MessageQueueL0M0R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "message_queue.L0.M0.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = MESSAGE_QUEUE_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("message_queue.L0.M0.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("MESSAGEFORM", "CAPACITY", "LIFETIME")

    def __init__(self, base_b1: MessageQueueL0M0B1Base) -> None:
        self._base_b1 = base_b1

class MessageQueueL0M0R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "message_queue.L0.M0.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = MESSAGE_QUEUE_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("message_queue.L0.M0.B1", "message_queue.L0.M0.B1")
    boundary_ids: ClassVar[tuple[str, ...]] = ("MESSAGEFORM", "CAPACITY", "LIFETIME")

    def __init__(self, base_b1_1: MessageQueueL0M0B1Base, base_b1_2: MessageQueueL0M0B1Base) -> None:
        self._base_b1_1 = base_b1_1
        self._base_b1_2 = base_b1_2

class MessageQueueL0M0R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "message_queue.L0.M0.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = MESSAGE_QUEUE_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("message_queue.L0.M0.B1", "message_queue.L0.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("ORDERRANGE", "HANDOFF", "LIFETIME")

    def __init__(self, base_b1: MessageQueueL0M0B1Base, base_b2: MessageQueueL0M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class MessageQueueL0M0R4Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "message_queue.L0.M0.R4"
    framework_rule_short_id: ClassVar[str] = "R4"
    owner_module_id: ClassVar[str] = MESSAGE_QUEUE_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("message_queue.L0.M0.B1", "message_queue.L0.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("MESSAGEFORM", "LIFETIME", "ACCESSRELATION", "HANDOFF")

    def __init__(self, base_b1: MessageQueueL0M0B1Base, base_b3: MessageQueueL0M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b3 = base_b3

class MessageQueueL0M0R5Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "message_queue.L0.M0.R5"
    framework_rule_short_id: ClassVar[str] = "R5"
    owner_module_id: ClassVar[str] = MESSAGE_QUEUE_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("message_queue.L0.M0.B1", "message_queue.L0.M0.B2", "message_queue.L0.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("MESSAGEFORM", "CAPACITY", "LIFETIME", "ORDERRANGE", "HANDOFF", "ACCESSRELATION")

    def __init__(self, base_b1: MessageQueueL0M0B1Base, base_b2: MessageQueueL0M0B2Base, base_b3: MessageQueueL0M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class MessageQueueL0M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = MESSAGE_QUEUE_L0_M0_MODULE_ID
    module_key: ClassVar[str] = MESSAGE_QUEUE_L0_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        MessageQueueL0M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        MessageQueueL0M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            MessageQueueL0M0B1Base,
            MessageQueueL0M0B2Base,
            MessageQueueL0M0B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            MessageQueueL0M0R1Rule,
            MessageQueueL0M0R2Rule,
            MessageQueueL0M0R3Rule,
            MessageQueueL0M0R4Rule,
            MessageQueueL0M0R5Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(MESSAGE_QUEUE_L0_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: MessageQueueL0M0StaticBoundaryParams,
        runtime_params: MessageQueueL0M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = MessageQueueL0M0B1Base(self)
        self.b2 = MessageQueueL0M0B2Base(self)
        self.b3 = MessageQueueL0M0B3Base(self)
        self.r1 = MessageQueueL0M0R1Rule(self.b1)
        self.r2 = MessageQueueL0M0R2Rule(self.b1, self.b1)
        self.r3 = MessageQueueL0M0R3Rule(self.b1, self.b2)
        self.r4 = MessageQueueL0M0R4Rule(self.b1, self.b3)
        self.r5 = MessageQueueL0M0R5Rule(self.b1, self.b2, self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> MessageQueueL0M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, MessageQueueL0M0StaticBoundaryParams):
            raise TypeError("MessageQueueL0M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, MessageQueueL0M0RuntimeBoundaryParams):
            raise TypeError("MessageQueueL0M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)


MESSAGE_QUEUE_L1_M0_MODULE_ID = "message_queue.L1.M0"
MESSAGE_QUEUE_L1_M0_MODULE_KEY = "message_queue__L1__M0"
MESSAGE_QUEUE_L1_M0_BOUNDARY_FIELD_MAP = {
    "INGRESS": "ingress",
    "SUBSCRIBE": "subscribe",
    "ACK": "ack",
    "BACKLOG": "backlog",
    "FAILURE": "failure",
    "ORDER": "order",
    "TRACE": "trace",
    "SLA": "sla",
}

@dataclass(frozen=True, slots=True)
class MessageQueueL1M0StaticBoundaryParams(StaticBoundaryParamsContract):
    ingress: object = None
    subscribe: object = None
    ack: object = None
    backlog: object = None
    failure: object = None
    order: object = None
    trace: object = None
    sla: object = None

    framework_module_id: ClassVar[str] = MESSAGE_QUEUE_L1_M0_MODULE_ID
    module_key: ClassVar[str] = MESSAGE_QUEUE_L1_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(MESSAGE_QUEUE_L1_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class MessageQueueL1M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    ingress: object = UNSET
    subscribe: object = UNSET
    ack: object = UNSET
    backlog: object = UNSET
    failure: object = UNSET
    order: object = UNSET
    trace: object = UNSET
    sla: object = UNSET

    framework_module_id: ClassVar[str] = MESSAGE_QUEUE_L1_M0_MODULE_ID
    module_key: ClassVar[str] = MESSAGE_QUEUE_L1_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(MESSAGE_QUEUE_L1_M0_BOUNDARY_FIELD_MAP)

class MessageQueueL1M0B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "message_queue.L1.M0.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = MESSAGE_QUEUE_L1_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("INGRESS", "ORDER", "SLA")

class MessageQueueL1M0B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "message_queue.L1.M0.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = MESSAGE_QUEUE_L1_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("SUBSCRIBE", "ACK", "ORDER")

class MessageQueueL1M0B3Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "message_queue.L1.M0.B3"
    framework_base_short_id: ClassVar[str] = "B3"
    owner_module_id: ClassVar[str] = MESSAGE_QUEUE_L1_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("BACKLOG", "FAILURE", "TRACE")

class MessageQueueL1M0R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "message_queue.L1.M0.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = MESSAGE_QUEUE_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("message_queue.L1.M0.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("INGRESS", "ORDER", "SLA")

    def __init__(self, base_b1: MessageQueueL1M0B1Base) -> None:
        self._base_b1 = base_b1

class MessageQueueL1M0R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "message_queue.L1.M0.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = MESSAGE_QUEUE_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("message_queue.L1.M0.B1", "message_queue.L1.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("SUBSCRIBE", "ACK", "ORDER", "INGRESS")

    def __init__(self, base_b1: MessageQueueL1M0B1Base, base_b2: MessageQueueL1M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class MessageQueueL1M0R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "message_queue.L1.M0.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = MESSAGE_QUEUE_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("message_queue.L1.M0.B1", "message_queue.L1.M0.B2", "message_queue.L1.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("BACKLOG", "FAILURE", "TRACE", "ACK", "SLA")

    def __init__(self, base_b1: MessageQueueL1M0B1Base, base_b2: MessageQueueL1M0B2Base, base_b3: MessageQueueL1M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class MessageQueueL1M0R4Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "message_queue.L1.M0.R4"
    framework_rule_short_id: ClassVar[str] = "R4"
    owner_module_id: ClassVar[str] = MESSAGE_QUEUE_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("message_queue.L1.M0.B1", "message_queue.L1.M0.B2", "message_queue.L1.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("INGRESS", "SUBSCRIBE", "ACK", "BACKLOG", "FAILURE", "ORDER", "TRACE", "SLA")

    def __init__(self, base_b1: MessageQueueL1M0B1Base, base_b2: MessageQueueL1M0B2Base, base_b3: MessageQueueL1M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class MessageQueueL1M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = MESSAGE_QUEUE_L1_M0_MODULE_ID
    module_key: ClassVar[str] = MESSAGE_QUEUE_L1_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        MessageQueueL1M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        MessageQueueL1M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            MessageQueueL1M0B1Base,
            MessageQueueL1M0B2Base,
            MessageQueueL1M0B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            MessageQueueL1M0R1Rule,
            MessageQueueL1M0R2Rule,
            MessageQueueL1M0R3Rule,
            MessageQueueL1M0R4Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(MESSAGE_QUEUE_L1_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: MessageQueueL1M0StaticBoundaryParams,
        runtime_params: MessageQueueL1M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = MessageQueueL1M0B1Base(self)
        self.b2 = MessageQueueL1M0B2Base(self)
        self.b3 = MessageQueueL1M0B3Base(self)
        self.r1 = MessageQueueL1M0R1Rule(self.b1)
        self.r2 = MessageQueueL1M0R2Rule(self.b1, self.b2)
        self.r3 = MessageQueueL1M0R3Rule(self.b1, self.b2, self.b3)
        self.r4 = MessageQueueL1M0R4Rule(self.b1, self.b2, self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> MessageQueueL1M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, MessageQueueL1M0StaticBoundaryParams):
            raise TypeError("MessageQueueL1M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, MessageQueueL1M0RuntimeBoundaryParams):
            raise TypeError("MessageQueueL1M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)


RUNTIME_ENV_L0_M0_MODULE_ID = "runtime_env.L0.M0"
RUNTIME_ENV_L0_M0_MODULE_KEY = "runtime_env__L0__M0"
RUNTIME_ENV_L0_M0_BOUNDARY_FIELD_MAP = {
    "PLATFORM": "platform",
    "CHANNEL": "channel",
    "PERM": "perm",
    "PERF": "perf",
    "NETWORK": "network",
    "POLICY": "policy",
    "FALLBACK": "fallback",
}

@dataclass(frozen=True, slots=True)
class RuntimeEnvL0M0StaticBoundaryParams(StaticBoundaryParamsContract):
    platform: object = None
    channel: object = None
    perm: object = None
    perf: object = None
    network: object = None
    policy: object = None
    fallback: object = None

    framework_module_id: ClassVar[str] = RUNTIME_ENV_L0_M0_MODULE_ID
    module_key: ClassVar[str] = RUNTIME_ENV_L0_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(RUNTIME_ENV_L0_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class RuntimeEnvL0M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    platform: object = UNSET
    channel: object = UNSET
    perm: object = UNSET
    perf: object = UNSET
    network: object = UNSET
    policy: object = UNSET
    fallback: object = UNSET

    framework_module_id: ClassVar[str] = RUNTIME_ENV_L0_M0_MODULE_ID
    module_key: ClassVar[str] = RUNTIME_ENV_L0_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(RUNTIME_ENV_L0_M0_BOUNDARY_FIELD_MAP)

class RuntimeEnvL0M0B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "runtime_env.L0.M0.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = RUNTIME_ENV_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("PLATFORM", "CHANNEL", "PERM")

class RuntimeEnvL0M0B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "runtime_env.L0.M0.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = RUNTIME_ENV_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("PERF", "NETWORK", "POLICY")

class RuntimeEnvL0M0B3Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "runtime_env.L0.M0.B3"
    framework_base_short_id: ClassVar[str] = "B3"
    owner_module_id: ClassVar[str] = RUNTIME_ENV_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("FALLBACK", "POLICY", "PERM")

class RuntimeEnvL0M0R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "runtime_env.L0.M0.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = RUNTIME_ENV_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("runtime_env.L0.M0.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("PLATFORM", "CHANNEL", "PERM")

    def __init__(self, base_b1: RuntimeEnvL0M0B1Base) -> None:
        self._base_b1 = base_b1

class RuntimeEnvL0M0R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "runtime_env.L0.M0.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = RUNTIME_ENV_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("runtime_env.L0.M0.B1", "runtime_env.L0.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("PERF", "NETWORK", "POLICY", "PLATFORM")

    def __init__(self, base_b1: RuntimeEnvL0M0B1Base, base_b2: RuntimeEnvL0M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class RuntimeEnvL0M0R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "runtime_env.L0.M0.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = RUNTIME_ENV_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("runtime_env.L0.M0.B1", "runtime_env.L0.M0.B2", "runtime_env.L0.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("FALLBACK", "POLICY", "PERM", "NETWORK")

    def __init__(self, base_b1: RuntimeEnvL0M0B1Base, base_b2: RuntimeEnvL0M0B2Base, base_b3: RuntimeEnvL0M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class RuntimeEnvL0M0R4Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "runtime_env.L0.M0.R4"
    framework_rule_short_id: ClassVar[str] = "R4"
    owner_module_id: ClassVar[str] = RUNTIME_ENV_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("runtime_env.L0.M0.B1", "runtime_env.L0.M0.B2", "runtime_env.L0.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("PLATFORM", "CHANNEL", "PERM", "PERF", "NETWORK", "POLICY", "FALLBACK")

    def __init__(self, base_b1: RuntimeEnvL0M0B1Base, base_b2: RuntimeEnvL0M0B2Base, base_b3: RuntimeEnvL0M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class RuntimeEnvL0M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = RUNTIME_ENV_L0_M0_MODULE_ID
    module_key: ClassVar[str] = RUNTIME_ENV_L0_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        RuntimeEnvL0M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        RuntimeEnvL0M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            RuntimeEnvL0M0B1Base,
            RuntimeEnvL0M0B2Base,
            RuntimeEnvL0M0B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            RuntimeEnvL0M0R1Rule,
            RuntimeEnvL0M0R2Rule,
            RuntimeEnvL0M0R3Rule,
            RuntimeEnvL0M0R4Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(RUNTIME_ENV_L0_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: RuntimeEnvL0M0StaticBoundaryParams,
        runtime_params: RuntimeEnvL0M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = RuntimeEnvL0M0B1Base(self)
        self.b2 = RuntimeEnvL0M0B2Base(self)
        self.b3 = RuntimeEnvL0M0B3Base(self)
        self.r1 = RuntimeEnvL0M0R1Rule(self.b1)
        self.r2 = RuntimeEnvL0M0R2Rule(self.b1, self.b2)
        self.r3 = RuntimeEnvL0M0R3Rule(self.b1, self.b2, self.b3)
        self.r4 = RuntimeEnvL0M0R4Rule(self.b1, self.b2, self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> RuntimeEnvL0M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, RuntimeEnvL0M0StaticBoundaryParams):
            raise TypeError("RuntimeEnvL0M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, RuntimeEnvL0M0RuntimeBoundaryParams):
            raise TypeError("RuntimeEnvL0M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)


SHELF_L0_M0_MODULE_ID = "shelf.L0.M0"
SHELF_L0_M0_MODULE_KEY = "shelf__L0__M0"
SHELF_L0_M0_BOUNDARY_FIELD_MAP = {
    "LOAD": "load",
    "SIZE": "size",
    "GRID": "grid",
    "JOINT": "joint",
    "SAFE": "safe",
    "SCENE": "scene",
}

@dataclass(frozen=True, slots=True)
class ShelfL0M0StaticBoundaryParams(StaticBoundaryParamsContract):
    load: object = None
    size: object = None
    grid: object = None
    joint: object = None
    safe: object = None
    scene: object = None

    framework_module_id: ClassVar[str] = SHELF_L0_M0_MODULE_ID
    module_key: ClassVar[str] = SHELF_L0_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(SHELF_L0_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class ShelfL0M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    load: object = UNSET
    size: object = UNSET
    grid: object = UNSET
    joint: object = UNSET
    safe: object = UNSET
    scene: object = UNSET

    framework_module_id: ClassVar[str] = SHELF_L0_M0_MODULE_ID
    module_key: ClassVar[str] = SHELF_L0_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(SHELF_L0_M0_BOUNDARY_FIELD_MAP)

class ShelfL0M0B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "shelf.L0.M0.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = SHELF_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("LOAD", "SIZE", "SAFE")

class ShelfL0M0B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "shelf.L0.M0.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = SHELF_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("JOINT", "SIZE")

class ShelfL0M0B3Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "shelf.L0.M0.B3"
    framework_base_short_id: ClassVar[str] = "B3"
    owner_module_id: ClassVar[str] = SHELF_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("GRID", "SCENE", "SAFE")

class ShelfL0M0R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "shelf.L0.M0.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = SHELF_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("shelf.L0.M0.B1", "shelf.L0.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("LOAD", "SIZE", "JOINT", "SAFE")

    def __init__(self, base_b1: ShelfL0M0B1Base, base_b2: ShelfL0M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class ShelfL0M0R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "shelf.L0.M0.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = SHELF_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("shelf.L0.M0.B1", "shelf.L0.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("GRID", "SIZE", "SCENE", "SAFE")

    def __init__(self, base_b1: ShelfL0M0B1Base, base_b3: ShelfL0M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b3 = base_b3

class ShelfL0M0R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "shelf.L0.M0.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = SHELF_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("shelf.L0.M0.B1", "shelf.L0.M0.B2", "shelf.L0.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("LOAD", "SIZE", "GRID", "JOINT", "SCENE", "SAFE")

    def __init__(self, base_b1: ShelfL0M0B1Base, base_b2: ShelfL0M0B2Base, base_b3: ShelfL0M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class ShelfL0M0R4Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "shelf.L0.M0.R4"
    framework_rule_short_id: ClassVar[str] = "R4"
    owner_module_id: ClassVar[str] = SHELF_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("shelf.L0.M0.B1", "shelf.L0.M0.B2", "shelf.L0.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("LOAD", "SIZE", "GRID", "JOINT", "SCENE", "SAFE")

    def __init__(self, base_b1: ShelfL0M0B1Base, base_b2: ShelfL0M0B2Base, base_b3: ShelfL0M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class ShelfL0M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = SHELF_L0_M0_MODULE_ID
    module_key: ClassVar[str] = SHELF_L0_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        ShelfL0M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        ShelfL0M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            ShelfL0M0B1Base,
            ShelfL0M0B2Base,
            ShelfL0M0B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            ShelfL0M0R1Rule,
            ShelfL0M0R2Rule,
            ShelfL0M0R3Rule,
            ShelfL0M0R4Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(SHELF_L0_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: ShelfL0M0StaticBoundaryParams,
        runtime_params: ShelfL0M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = ShelfL0M0B1Base(self)
        self.b2 = ShelfL0M0B2Base(self)
        self.b3 = ShelfL0M0B3Base(self)
        self.r1 = ShelfL0M0R1Rule(self.b1, self.b2)
        self.r2 = ShelfL0M0R2Rule(self.b1, self.b3)
        self.r3 = ShelfL0M0R3Rule(self.b1, self.b2, self.b3)
        self.r4 = ShelfL0M0R4Rule(self.b1, self.b2, self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> ShelfL0M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, ShelfL0M0StaticBoundaryParams):
            raise TypeError("ShelfL0M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, ShelfL0M0RuntimeBoundaryParams):
            raise TypeError("ShelfL0M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)


SHELF_L1_M0_MODULE_ID = "shelf.L1.M0"
SHELF_L1_M0_MODULE_KEY = "shelf__L1__M0"
SHELF_L1_M0_BOUNDARY_FIELD_MAP = {
    "STEP": "step",
    "ALIGN": "align",
    "TOL": "tol",
    "ACCESS": "access",
    "RECOVER": "recover",
    "SCENE": "scene",
}

@dataclass(frozen=True, slots=True)
class ShelfL1M0StaticBoundaryParams(StaticBoundaryParamsContract):
    step: object = None
    align: object = None
    tol: object = None
    access: object = None
    recover: object = None
    scene: object = None

    framework_module_id: ClassVar[str] = SHELF_L1_M0_MODULE_ID
    module_key: ClassVar[str] = SHELF_L1_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(SHELF_L1_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class ShelfL1M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    step: object = UNSET
    align: object = UNSET
    tol: object = UNSET
    access: object = UNSET
    recover: object = UNSET
    scene: object = UNSET

    framework_module_id: ClassVar[str] = SHELF_L1_M0_MODULE_ID
    module_key: ClassVar[str] = SHELF_L1_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(SHELF_L1_M0_BOUNDARY_FIELD_MAP)

class ShelfL1M0B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "shelf.L1.M0.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = SHELF_L1_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("STEP", "ALIGN", "TOL")

class ShelfL1M0B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "shelf.L1.M0.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = SHELF_L1_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("ACCESS", "SCENE", "ALIGN")

class ShelfL1M0B3Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "shelf.L1.M0.B3"
    framework_base_short_id: ClassVar[str] = "B3"
    owner_module_id: ClassVar[str] = SHELF_L1_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("RECOVER", "STEP", "SCENE")

class ShelfL1M0R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "shelf.L1.M0.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = SHELF_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("shelf.L1.M0.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("STEP", "ALIGN", "TOL")

    def __init__(self, base_b1: ShelfL1M0B1Base) -> None:
        self._base_b1 = base_b1

class ShelfL1M0R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "shelf.L1.M0.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = SHELF_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("shelf.L1.M0.B1", "shelf.L1.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("ACCESS", "ALIGN", "SCENE", "STEP")

    def __init__(self, base_b1: ShelfL1M0B1Base, base_b2: ShelfL1M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class ShelfL1M0R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "shelf.L1.M0.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = SHELF_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("shelf.L1.M0.B1", "shelf.L1.M0.B2", "shelf.L1.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("RECOVER", "SCENE", "STEP", "TOL", "ACCESS")

    def __init__(self, base_b1: ShelfL1M0B1Base, base_b2: ShelfL1M0B2Base, base_b3: ShelfL1M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class ShelfL1M0R4Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "shelf.L1.M0.R4"
    framework_rule_short_id: ClassVar[str] = "R4"
    owner_module_id: ClassVar[str] = SHELF_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("shelf.L1.M0.B1", "shelf.L1.M0.B2", "shelf.L1.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("STEP", "ALIGN", "TOL", "ACCESS", "RECOVER", "SCENE")

    def __init__(self, base_b1: ShelfL1M0B1Base, base_b2: ShelfL1M0B2Base, base_b3: ShelfL1M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class ShelfL1M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = SHELF_L1_M0_MODULE_ID
    module_key: ClassVar[str] = SHELF_L1_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        ShelfL1M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        ShelfL1M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            ShelfL1M0B1Base,
            ShelfL1M0B2Base,
            ShelfL1M0B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            ShelfL1M0R1Rule,
            ShelfL1M0R2Rule,
            ShelfL1M0R3Rule,
            ShelfL1M0R4Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(SHELF_L1_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: ShelfL1M0StaticBoundaryParams,
        runtime_params: ShelfL1M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = ShelfL1M0B1Base(self)
        self.b2 = ShelfL1M0B2Base(self)
        self.b3 = ShelfL1M0B3Base(self)
        self.r1 = ShelfL1M0R1Rule(self.b1)
        self.r2 = ShelfL1M0R2Rule(self.b1, self.b2)
        self.r3 = ShelfL1M0R3Rule(self.b1, self.b2, self.b3)
        self.r4 = ShelfL1M0R4Rule(self.b1, self.b2, self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> ShelfL1M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, ShelfL1M0StaticBoundaryParams):
            raise TypeError("ShelfL1M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, ShelfL1M0RuntimeBoundaryParams):
            raise TypeError("ShelfL1M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)


SHELF_L2_M0_MODULE_ID = "shelf.L2.M0"
SHELF_L2_M0_MODULE_KEY = "shelf__L2__M0"
SHELF_L2_M0_BOUNDARY_FIELD_MAP = {
    "LOAD": "load",
    "SIZE": "size",
    "GRID": "grid",
    "JOINT": "joint",
    "MATERIAL": "material",
    "SAFE": "safe",
    "SCENE": "scene",
}

@dataclass(frozen=True, slots=True)
class ShelfL2M0StaticBoundaryParams(StaticBoundaryParamsContract):
    load: object = None
    size: object = None
    grid: object = None
    joint: object = None
    material: object = None
    safe: object = None
    scene: object = None

    framework_module_id: ClassVar[str] = SHELF_L2_M0_MODULE_ID
    module_key: ClassVar[str] = SHELF_L2_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(SHELF_L2_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class ShelfL2M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    load: object = UNSET
    size: object = UNSET
    grid: object = UNSET
    joint: object = UNSET
    material: object = UNSET
    safe: object = UNSET
    scene: object = UNSET

    framework_module_id: ClassVar[str] = SHELF_L2_M0_MODULE_ID
    module_key: ClassVar[str] = SHELF_L2_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(SHELF_L2_M0_BOUNDARY_FIELD_MAP)

class ShelfL2M0B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "shelf.L2.M0.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = SHELF_L2_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("LOAD", "SIZE", "MATERIAL")

class ShelfL2M0B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "shelf.L2.M0.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = SHELF_L2_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("JOINT", "SIZE", "SCENE")

class ShelfL2M0B3Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "shelf.L2.M0.B3"
    framework_base_short_id: ClassVar[str] = "B3"
    owner_module_id: ClassVar[str] = SHELF_L2_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("GRID", "SAFE", "LOAD")

class ShelfL2M0R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "shelf.L2.M0.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = SHELF_L2_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("shelf.L2.M0.B1", "shelf.L2.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("LOAD", "SIZE", "JOINT", "MATERIAL")

    def __init__(self, base_b1: ShelfL2M0B1Base, base_b2: ShelfL2M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class ShelfL2M0R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "shelf.L2.M0.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = SHELF_L2_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("shelf.L2.M0.B1", "shelf.L2.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("GRID", "SIZE", "SAFE", "SCENE")

    def __init__(self, base_b1: ShelfL2M0B1Base, base_b3: ShelfL2M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b3 = base_b3

class ShelfL2M0R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "shelf.L2.M0.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = SHELF_L2_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("shelf.L2.M0.B1", "shelf.L2.M0.B2", "shelf.L2.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("LOAD", "SIZE", "GRID", "JOINT", "SAFE", "SCENE")

    def __init__(self, base_b1: ShelfL2M0B1Base, base_b2: ShelfL2M0B2Base, base_b3: ShelfL2M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class ShelfL2M0R4Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "shelf.L2.M0.R4"
    framework_rule_short_id: ClassVar[str] = "R4"
    owner_module_id: ClassVar[str] = SHELF_L2_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("shelf.L2.M0.B1", "shelf.L2.M0.B2", "shelf.L2.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("LOAD", "SIZE", "GRID", "JOINT", "MATERIAL", "SAFE", "SCENE")

    def __init__(self, base_b1: ShelfL2M0B1Base, base_b2: ShelfL2M0B2Base, base_b3: ShelfL2M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class ShelfL2M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = SHELF_L2_M0_MODULE_ID
    module_key: ClassVar[str] = SHELF_L2_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        ShelfL2M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        ShelfL2M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            ShelfL2M0B1Base,
            ShelfL2M0B2Base,
            ShelfL2M0B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            ShelfL2M0R1Rule,
            ShelfL2M0R2Rule,
            ShelfL2M0R3Rule,
            ShelfL2M0R4Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(SHELF_L2_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: ShelfL2M0StaticBoundaryParams,
        runtime_params: ShelfL2M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = ShelfL2M0B1Base(self)
        self.b2 = ShelfL2M0B2Base(self)
        self.b3 = ShelfL2M0B3Base(self)
        self.r1 = ShelfL2M0R1Rule(self.b1, self.b2)
        self.r2 = ShelfL2M0R2Rule(self.b1, self.b3)
        self.r3 = ShelfL2M0R3Rule(self.b1, self.b2, self.b3)
        self.r4 = ShelfL2M0R4Rule(self.b1, self.b2, self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> ShelfL2M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, ShelfL2M0StaticBoundaryParams):
            raise TypeError("ShelfL2M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, ShelfL2M0RuntimeBoundaryParams):
            raise TypeError("ShelfL2M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)

STATIC_MODULE_CONTRACTS: dict[str, StaticModuleContractBundle] = {
    "backend.L0.M0": StaticModuleContractBundle(
        module_type=BackendL0M0Module,
        static_params_type=BackendL0M0StaticBoundaryParams,
        runtime_params_type=BackendL0M0RuntimeBoundaryParams,
        base_types=(
            BackendL0M0B1Base,
            BackendL0M0B2Base,
            BackendL0M0B3Base,
        ),
        rule_types=(
            BackendL0M0R1Rule,
            BackendL0M0R2Rule,
            BackendL0M0R3Rule,
            BackendL0M0R4Rule,
        ),
    ),
    "backend.L1.M0": StaticModuleContractBundle(
        module_type=BackendL1M0Module,
        static_params_type=BackendL1M0StaticBoundaryParams,
        runtime_params_type=BackendL1M0RuntimeBoundaryParams,
        base_types=(
            BackendL1M0B1Base,
            BackendL1M0B2Base,
            BackendL1M0B3Base,
        ),
        rule_types=(
            BackendL1M0R1Rule,
            BackendL1M0R2Rule,
            BackendL1M0R3Rule,
            BackendL1M0R4Rule,
        ),
    ),
    "curtain.L0.M0": StaticModuleContractBundle(
        module_type=CurtainL0M0Module,
        static_params_type=CurtainL0M0StaticBoundaryParams,
        runtime_params_type=CurtainL0M0RuntimeBoundaryParams,
        base_types=(
            CurtainL0M0B1Base,
            CurtainL0M0B2Base,
            CurtainL0M0B3Base,
        ),
        rule_types=(
            CurtainL0M0R1Rule,
            CurtainL0M0R2Rule,
            CurtainL0M0R3Rule,
            CurtainL0M0R4Rule,
        ),
    ),
    "curtain.L1.M0": StaticModuleContractBundle(
        module_type=CurtainL1M0Module,
        static_params_type=CurtainL1M0StaticBoundaryParams,
        runtime_params_type=CurtainL1M0RuntimeBoundaryParams,
        base_types=(
            CurtainL1M0B1Base,
            CurtainL1M0B2Base,
            CurtainL1M0B3Base,
        ),
        rule_types=(
            CurtainL1M0R1Rule,
            CurtainL1M0R2Rule,
            CurtainL1M0R3Rule,
            CurtainL1M0R4Rule,
        ),
    ),
    "curtain.L2.M0": StaticModuleContractBundle(
        module_type=CurtainL2M0Module,
        static_params_type=CurtainL2M0StaticBoundaryParams,
        runtime_params_type=CurtainL2M0RuntimeBoundaryParams,
        base_types=(
            CurtainL2M0B1Base,
            CurtainL2M0B2Base,
            CurtainL2M0B3Base,
        ),
        rule_types=(
            CurtainL2M0R1Rule,
            CurtainL2M0R2Rule,
            CurtainL2M0R3Rule,
            CurtainL2M0R4Rule,
        ),
    ),
    "frontend.L0.M0": StaticModuleContractBundle(
        module_type=FrontendL0M0Module,
        static_params_type=FrontendL0M0StaticBoundaryParams,
        runtime_params_type=FrontendL0M0RuntimeBoundaryParams,
        base_types=(
            FrontendL0M0B1Base,
            FrontendL0M0B2Base,
        ),
        rule_types=(
            FrontendL0M0R1Rule,
            FrontendL0M0R2Rule,
            FrontendL0M0R3Rule,
        ),
    ),
    "frontend.L0.M1": StaticModuleContractBundle(
        module_type=FrontendL0M1Module,
        static_params_type=FrontendL0M1StaticBoundaryParams,
        runtime_params_type=FrontendL0M1RuntimeBoundaryParams,
        base_types=(
            FrontendL0M1B1Base,
            FrontendL0M1B2Base,
        ),
        rule_types=(
            FrontendL0M1R1Rule,
            FrontendL0M1R2Rule,
            FrontendL0M1R3Rule,
        ),
    ),
    "frontend.L0.M2": StaticModuleContractBundle(
        module_type=FrontendL0M2Module,
        static_params_type=FrontendL0M2StaticBoundaryParams,
        runtime_params_type=FrontendL0M2RuntimeBoundaryParams,
        base_types=(
            FrontendL0M2B1Base,
            FrontendL0M2B2Base,
        ),
        rule_types=(
            FrontendL0M2R1Rule,
            FrontendL0M2R2Rule,
            FrontendL0M2R3Rule,
        ),
    ),
    "frontend.L1.M0": StaticModuleContractBundle(
        module_type=FrontendL1M0Module,
        static_params_type=FrontendL1M0StaticBoundaryParams,
        runtime_params_type=FrontendL1M0RuntimeBoundaryParams,
        base_types=(
            FrontendL1M0B1Base,
            FrontendL1M0B2Base,
        ),
        rule_types=(
            FrontendL1M0R1Rule,
            FrontendL1M0R2Rule,
            FrontendL1M0R3Rule,
        ),
    ),
    "frontend.L1.M1": StaticModuleContractBundle(
        module_type=FrontendL1M1Module,
        static_params_type=FrontendL1M1StaticBoundaryParams,
        runtime_params_type=FrontendL1M1RuntimeBoundaryParams,
        base_types=(
            FrontendL1M1B1Base,
            FrontendL1M1B2Base,
        ),
        rule_types=(
            FrontendL1M1R1Rule,
            FrontendL1M1R2Rule,
            FrontendL1M1R3Rule,
        ),
    ),
    "frontend.L1.M2": StaticModuleContractBundle(
        module_type=FrontendL1M2Module,
        static_params_type=FrontendL1M2StaticBoundaryParams,
        runtime_params_type=FrontendL1M2RuntimeBoundaryParams,
        base_types=(
            FrontendL1M2B1Base,
            FrontendL1M2B2Base,
        ),
        rule_types=(
            FrontendL1M2R1Rule,
            FrontendL1M2R2Rule,
            FrontendL1M2R3Rule,
        ),
    ),
    "frontend.L1.M3": StaticModuleContractBundle(
        module_type=FrontendL1M3Module,
        static_params_type=FrontendL1M3StaticBoundaryParams,
        runtime_params_type=FrontendL1M3RuntimeBoundaryParams,
        base_types=(
            FrontendL1M3B1Base,
            FrontendL1M3B2Base,
        ),
        rule_types=(
            FrontendL1M3R1Rule,
            FrontendL1M3R2Rule,
            FrontendL1M3R3Rule,
        ),
    ),
    "frontend.L1.M4": StaticModuleContractBundle(
        module_type=FrontendL1M4Module,
        static_params_type=FrontendL1M4StaticBoundaryParams,
        runtime_params_type=FrontendL1M4RuntimeBoundaryParams,
        base_types=(
            FrontendL1M4B1Base,
            FrontendL1M4B2Base,
        ),
        rule_types=(
            FrontendL1M4R1Rule,
            FrontendL1M4R2Rule,
            FrontendL1M4R3Rule,
        ),
    ),
    "frontend.L2.M0": StaticModuleContractBundle(
        module_type=FrontendL2M0Module,
        static_params_type=FrontendL2M0StaticBoundaryParams,
        runtime_params_type=FrontendL2M0RuntimeBoundaryParams,
        base_types=(
            FrontendL2M0B1Base,
            FrontendL2M0B2Base,
        ),
        rule_types=(
            FrontendL2M0R1Rule,
            FrontendL2M0R2Rule,
            FrontendL2M0R3Rule,
        ),
    ),
    "frontend.L2.M1": StaticModuleContractBundle(
        module_type=FrontendL2M1Module,
        static_params_type=FrontendL2M1StaticBoundaryParams,
        runtime_params_type=FrontendL2M1RuntimeBoundaryParams,
        base_types=(
            FrontendL2M1B1Base,
            FrontendL2M1B2Base,
            FrontendL2M1B3Base,
        ),
        rule_types=(
            FrontendL2M1R1Rule,
            FrontendL2M1R2Rule,
            FrontendL2M1R3Rule,
            FrontendL2M1R4Rule,
        ),
    ),
    "frontend.L3.M0": StaticModuleContractBundle(
        module_type=FrontendL3M0Module,
        static_params_type=FrontendL3M0StaticBoundaryParams,
        runtime_params_type=FrontendL3M0RuntimeBoundaryParams,
        base_types=(
            FrontendL3M0B1Base,
            FrontendL3M0B2Base,
            FrontendL3M0B3Base,
        ),
        rule_types=(
            FrontendL3M0R1Rule,
            FrontendL3M0R2Rule,
            FrontendL3M0R3Rule,
            FrontendL3M0R4Rule,
        ),
    ),
    "knowledge_base.L0.M0": StaticModuleContractBundle(
        module_type=KnowledgeBaseL0M0Module,
        static_params_type=KnowledgeBaseL0M0StaticBoundaryParams,
        runtime_params_type=KnowledgeBaseL0M0RuntimeBoundaryParams,
        base_types=(
            KnowledgeBaseL0M0B1Base,
            KnowledgeBaseL0M0B2Base,
            KnowledgeBaseL0M0B3Base,
        ),
        rule_types=(
            KnowledgeBaseL0M0R1Rule,
            KnowledgeBaseL0M0R2Rule,
            KnowledgeBaseL0M0R3Rule,
            KnowledgeBaseL0M0R4Rule,
        ),
    ),
    "knowledge_base.L0.M1": StaticModuleContractBundle(
        module_type=KnowledgeBaseL0M1Module,
        static_params_type=KnowledgeBaseL0M1StaticBoundaryParams,
        runtime_params_type=KnowledgeBaseL0M1RuntimeBoundaryParams,
        base_types=(
            KnowledgeBaseL0M1B1Base,
            KnowledgeBaseL0M1B2Base,
            KnowledgeBaseL0M1B3Base,
        ),
        rule_types=(
            KnowledgeBaseL0M1R1Rule,
            KnowledgeBaseL0M1R2Rule,
            KnowledgeBaseL0M1R3Rule,
            KnowledgeBaseL0M1R4Rule,
        ),
    ),
    "knowledge_base.L0.M2": StaticModuleContractBundle(
        module_type=KnowledgeBaseL0M2Module,
        static_params_type=KnowledgeBaseL0M2StaticBoundaryParams,
        runtime_params_type=KnowledgeBaseL0M2RuntimeBoundaryParams,
        base_types=(
            KnowledgeBaseL0M2B1Base,
            KnowledgeBaseL0M2B2Base,
            KnowledgeBaseL0M2B3Base,
        ),
        rule_types=(
            KnowledgeBaseL0M2R1Rule,
            KnowledgeBaseL0M2R2Rule,
            KnowledgeBaseL0M2R3Rule,
            KnowledgeBaseL0M2R4Rule,
        ),
    ),
    "knowledge_base.L1.M0": StaticModuleContractBundle(
        module_type=KnowledgeBaseL1M0Module,
        static_params_type=KnowledgeBaseL1M0StaticBoundaryParams,
        runtime_params_type=KnowledgeBaseL1M0RuntimeBoundaryParams,
        base_types=(
            KnowledgeBaseL1M0B1Base,
            KnowledgeBaseL1M0B2Base,
            KnowledgeBaseL1M0B3Base,
        ),
        rule_types=(
            KnowledgeBaseL1M0R1Rule,
            KnowledgeBaseL1M0R2Rule,
            KnowledgeBaseL1M0R3Rule,
            KnowledgeBaseL1M0R4Rule,
        ),
    ),
    "knowledge_base.L1.M1": StaticModuleContractBundle(
        module_type=KnowledgeBaseL1M1Module,
        static_params_type=KnowledgeBaseL1M1StaticBoundaryParams,
        runtime_params_type=KnowledgeBaseL1M1RuntimeBoundaryParams,
        base_types=(
            KnowledgeBaseL1M1B1Base,
            KnowledgeBaseL1M1B2Base,
            KnowledgeBaseL1M1B3Base,
        ),
        rule_types=(
            KnowledgeBaseL1M1R1Rule,
            KnowledgeBaseL1M1R2Rule,
            KnowledgeBaseL1M1R3Rule,
            KnowledgeBaseL1M1R4Rule,
        ),
    ),
    "knowledge_base.L2.M0": StaticModuleContractBundle(
        module_type=KnowledgeBaseL2M0Module,
        static_params_type=KnowledgeBaseL2M0StaticBoundaryParams,
        runtime_params_type=KnowledgeBaseL2M0RuntimeBoundaryParams,
        base_types=(
            KnowledgeBaseL2M0B1Base,
            KnowledgeBaseL2M0B2Base,
            KnowledgeBaseL2M0B3Base,
        ),
        rule_types=(
            KnowledgeBaseL2M0R1Rule,
            KnowledgeBaseL2M0R2Rule,
            KnowledgeBaseL2M0R3Rule,
            KnowledgeBaseL2M0R4Rule,
        ),
    ),
    "message_queue.L0.M0": StaticModuleContractBundle(
        module_type=MessageQueueL0M0Module,
        static_params_type=MessageQueueL0M0StaticBoundaryParams,
        runtime_params_type=MessageQueueL0M0RuntimeBoundaryParams,
        base_types=(
            MessageQueueL0M0B1Base,
            MessageQueueL0M0B2Base,
            MessageQueueL0M0B3Base,
        ),
        rule_types=(
            MessageQueueL0M0R1Rule,
            MessageQueueL0M0R2Rule,
            MessageQueueL0M0R3Rule,
            MessageQueueL0M0R4Rule,
            MessageQueueL0M0R5Rule,
        ),
    ),
    "message_queue.L1.M0": StaticModuleContractBundle(
        module_type=MessageQueueL1M0Module,
        static_params_type=MessageQueueL1M0StaticBoundaryParams,
        runtime_params_type=MessageQueueL1M0RuntimeBoundaryParams,
        base_types=(
            MessageQueueL1M0B1Base,
            MessageQueueL1M0B2Base,
            MessageQueueL1M0B3Base,
        ),
        rule_types=(
            MessageQueueL1M0R1Rule,
            MessageQueueL1M0R2Rule,
            MessageQueueL1M0R3Rule,
            MessageQueueL1M0R4Rule,
        ),
    ),
    "runtime_env.L0.M0": StaticModuleContractBundle(
        module_type=RuntimeEnvL0M0Module,
        static_params_type=RuntimeEnvL0M0StaticBoundaryParams,
        runtime_params_type=RuntimeEnvL0M0RuntimeBoundaryParams,
        base_types=(
            RuntimeEnvL0M0B1Base,
            RuntimeEnvL0M0B2Base,
            RuntimeEnvL0M0B3Base,
        ),
        rule_types=(
            RuntimeEnvL0M0R1Rule,
            RuntimeEnvL0M0R2Rule,
            RuntimeEnvL0M0R3Rule,
            RuntimeEnvL0M0R4Rule,
        ),
    ),
    "shelf.L0.M0": StaticModuleContractBundle(
        module_type=ShelfL0M0Module,
        static_params_type=ShelfL0M0StaticBoundaryParams,
        runtime_params_type=ShelfL0M0RuntimeBoundaryParams,
        base_types=(
            ShelfL0M0B1Base,
            ShelfL0M0B2Base,
            ShelfL0M0B3Base,
        ),
        rule_types=(
            ShelfL0M0R1Rule,
            ShelfL0M0R2Rule,
            ShelfL0M0R3Rule,
            ShelfL0M0R4Rule,
        ),
    ),
    "shelf.L1.M0": StaticModuleContractBundle(
        module_type=ShelfL1M0Module,
        static_params_type=ShelfL1M0StaticBoundaryParams,
        runtime_params_type=ShelfL1M0RuntimeBoundaryParams,
        base_types=(
            ShelfL1M0B1Base,
            ShelfL1M0B2Base,
            ShelfL1M0B3Base,
        ),
        rule_types=(
            ShelfL1M0R1Rule,
            ShelfL1M0R2Rule,
            ShelfL1M0R3Rule,
            ShelfL1M0R4Rule,
        ),
    ),
    "shelf.L2.M0": StaticModuleContractBundle(
        module_type=ShelfL2M0Module,
        static_params_type=ShelfL2M0StaticBoundaryParams,
        runtime_params_type=ShelfL2M0RuntimeBoundaryParams,
        base_types=(
            ShelfL2M0B1Base,
            ShelfL2M0B2Base,
            ShelfL2M0B3Base,
        ),
        rule_types=(
            ShelfL2M0R1Rule,
            ShelfL2M0R2Rule,
            ShelfL2M0R3Rule,
            ShelfL2M0R4Rule,
        ),
    ),
    BACKEND_L2_M0_MODULE_ID: StaticModuleContractBundle(
        module_type=BackendL2M0Module,
        static_params_type=BackendL2M0StaticBoundaryParams,
        runtime_params_type=BackendL2M0DynamicBoundaryParams,
        base_types=(BackendL2M0B1Base, BackendL2M0B2Base, BackendL2M0B3Base),
        rule_types=(BackendL2M0R1Rule, BackendL2M0R2Rule, BackendL2M0R3Rule, BackendL2M0R4Rule),
    ),
}


def get_static_module_contract_bundle(module_id: str) -> StaticModuleContractBundle | None:
    return STATIC_MODULE_CONTRACTS.get(str(module_id))


__all__ = [
    "BACKEND_L0_M0_BOUNDARY_FIELD_MAP",
    "BACKEND_L0_M0_MODULE_ID",
    "BACKEND_L0_M0_MODULE_KEY",
    "BACKEND_L1_M0_BOUNDARY_FIELD_MAP",
    "BACKEND_L1_M0_MODULE_ID",
    "BACKEND_L1_M0_MODULE_KEY",
    "BACKEND_L2_M0_MODULE_ID",
    "BackendL0M0B1Base",
    "BackendL0M0B2Base",
    "BackendL0M0B3Base",
    "BackendL0M0Module",
    "BackendL0M0R1Rule",
    "BackendL0M0R2Rule",
    "BackendL0M0R3Rule",
    "BackendL0M0R4Rule",
    "BackendL0M0RuntimeBoundaryParams",
    "BackendL0M0StaticBoundaryParams",
    "BackendL1M0B1Base",
    "BackendL1M0B2Base",
    "BackendL1M0B3Base",
    "BackendL1M0Module",
    "BackendL1M0R1Rule",
    "BackendL1M0R2Rule",
    "BackendL1M0R3Rule",
    "BackendL1M0R4Rule",
    "BackendL1M0RuntimeBoundaryParams",
    "BackendL1M0StaticBoundaryParams",
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
    "CURTAIN_L0_M0_BOUNDARY_FIELD_MAP",
    "CURTAIN_L0_M0_MODULE_ID",
    "CURTAIN_L0_M0_MODULE_KEY",
    "CURTAIN_L1_M0_BOUNDARY_FIELD_MAP",
    "CURTAIN_L1_M0_MODULE_ID",
    "CURTAIN_L1_M0_MODULE_KEY",
    "CURTAIN_L2_M0_BOUNDARY_FIELD_MAP",
    "CURTAIN_L2_M0_MODULE_ID",
    "CURTAIN_L2_M0_MODULE_KEY",
    "CurtainL0M0B1Base",
    "CurtainL0M0B2Base",
    "CurtainL0M0B3Base",
    "CurtainL0M0Module",
    "CurtainL0M0R1Rule",
    "CurtainL0M0R2Rule",
    "CurtainL0M0R3Rule",
    "CurtainL0M0R4Rule",
    "CurtainL0M0RuntimeBoundaryParams",
    "CurtainL0M0StaticBoundaryParams",
    "CurtainL1M0B1Base",
    "CurtainL1M0B2Base",
    "CurtainL1M0B3Base",
    "CurtainL1M0Module",
    "CurtainL1M0R1Rule",
    "CurtainL1M0R2Rule",
    "CurtainL1M0R3Rule",
    "CurtainL1M0R4Rule",
    "CurtainL1M0RuntimeBoundaryParams",
    "CurtainL1M0StaticBoundaryParams",
    "CurtainL2M0B1Base",
    "CurtainL2M0B2Base",
    "CurtainL2M0B3Base",
    "CurtainL2M0Module",
    "CurtainL2M0R1Rule",
    "CurtainL2M0R2Rule",
    "CurtainL2M0R3Rule",
    "CurtainL2M0R4Rule",
    "CurtainL2M0RuntimeBoundaryParams",
    "CurtainL2M0StaticBoundaryParams",
    "FRONTEND_L0_M0_BOUNDARY_FIELD_MAP",
    "FRONTEND_L0_M0_MODULE_ID",
    "FRONTEND_L0_M0_MODULE_KEY",
    "FRONTEND_L0_M1_BOUNDARY_FIELD_MAP",
    "FRONTEND_L0_M1_MODULE_ID",
    "FRONTEND_L0_M1_MODULE_KEY",
    "FRONTEND_L0_M2_BOUNDARY_FIELD_MAP",
    "FRONTEND_L0_M2_MODULE_ID",
    "FRONTEND_L0_M2_MODULE_KEY",
    "FRONTEND_L1_M0_BOUNDARY_FIELD_MAP",
    "FRONTEND_L1_M0_MODULE_ID",
    "FRONTEND_L1_M0_MODULE_KEY",
    "FRONTEND_L1_M1_BOUNDARY_FIELD_MAP",
    "FRONTEND_L1_M1_MODULE_ID",
    "FRONTEND_L1_M1_MODULE_KEY",
    "FRONTEND_L1_M2_BOUNDARY_FIELD_MAP",
    "FRONTEND_L1_M2_MODULE_ID",
    "FRONTEND_L1_M2_MODULE_KEY",
    "FRONTEND_L1_M3_BOUNDARY_FIELD_MAP",
    "FRONTEND_L1_M3_MODULE_ID",
    "FRONTEND_L1_M3_MODULE_KEY",
    "FRONTEND_L1_M4_BOUNDARY_FIELD_MAP",
    "FRONTEND_L1_M4_MODULE_ID",
    "FRONTEND_L1_M4_MODULE_KEY",
    "FRONTEND_L2_M0_BOUNDARY_FIELD_MAP",
    "FRONTEND_L2_M0_MODULE_ID",
    "FRONTEND_L2_M0_MODULE_KEY",
    "FRONTEND_L2_M1_BOUNDARY_FIELD_MAP",
    "FRONTEND_L2_M1_MODULE_ID",
    "FRONTEND_L2_M1_MODULE_KEY",
    "FRONTEND_L3_M0_BOUNDARY_FIELD_MAP",
    "FRONTEND_L3_M0_MODULE_ID",
    "FRONTEND_L3_M0_MODULE_KEY",
    "FrontendL0M0B1Base",
    "FrontendL0M0B2Base",
    "FrontendL0M0Module",
    "FrontendL0M0R1Rule",
    "FrontendL0M0R2Rule",
    "FrontendL0M0R3Rule",
    "FrontendL0M0RuntimeBoundaryParams",
    "FrontendL0M0StaticBoundaryParams",
    "FrontendL0M1B1Base",
    "FrontendL0M1B2Base",
    "FrontendL0M1Module",
    "FrontendL0M1R1Rule",
    "FrontendL0M1R2Rule",
    "FrontendL0M1R3Rule",
    "FrontendL0M1RuntimeBoundaryParams",
    "FrontendL0M1StaticBoundaryParams",
    "FrontendL0M2B1Base",
    "FrontendL0M2B2Base",
    "FrontendL0M2Module",
    "FrontendL0M2R1Rule",
    "FrontendL0M2R2Rule",
    "FrontendL0M2R3Rule",
    "FrontendL0M2RuntimeBoundaryParams",
    "FrontendL0M2StaticBoundaryParams",
    "FrontendL1M0B1Base",
    "FrontendL1M0B2Base",
    "FrontendL1M0Module",
    "FrontendL1M0R1Rule",
    "FrontendL1M0R2Rule",
    "FrontendL1M0R3Rule",
    "FrontendL1M0RuntimeBoundaryParams",
    "FrontendL1M0StaticBoundaryParams",
    "FrontendL1M1B1Base",
    "FrontendL1M1B2Base",
    "FrontendL1M1Module",
    "FrontendL1M1R1Rule",
    "FrontendL1M1R2Rule",
    "FrontendL1M1R3Rule",
    "FrontendL1M1RuntimeBoundaryParams",
    "FrontendL1M1StaticBoundaryParams",
    "FrontendL1M2B1Base",
    "FrontendL1M2B2Base",
    "FrontendL1M2Module",
    "FrontendL1M2R1Rule",
    "FrontendL1M2R2Rule",
    "FrontendL1M2R3Rule",
    "FrontendL1M2RuntimeBoundaryParams",
    "FrontendL1M2StaticBoundaryParams",
    "FrontendL1M3B1Base",
    "FrontendL1M3B2Base",
    "FrontendL1M3Module",
    "FrontendL1M3R1Rule",
    "FrontendL1M3R2Rule",
    "FrontendL1M3R3Rule",
    "FrontendL1M3RuntimeBoundaryParams",
    "FrontendL1M3StaticBoundaryParams",
    "FrontendL1M4B1Base",
    "FrontendL1M4B2Base",
    "FrontendL1M4Module",
    "FrontendL1M4R1Rule",
    "FrontendL1M4R2Rule",
    "FrontendL1M4R3Rule",
    "FrontendL1M4RuntimeBoundaryParams",
    "FrontendL1M4StaticBoundaryParams",
    "FrontendL2M0B1Base",
    "FrontendL2M0B2Base",
    "FrontendL2M0Module",
    "FrontendL2M0R1Rule",
    "FrontendL2M0R2Rule",
    "FrontendL2M0R3Rule",
    "FrontendL2M0RuntimeBoundaryParams",
    "FrontendL2M0StaticBoundaryParams",
    "FrontendL2M1B1Base",
    "FrontendL2M1B2Base",
    "FrontendL2M1B3Base",
    "FrontendL2M1Module",
    "FrontendL2M1R1Rule",
    "FrontendL2M1R2Rule",
    "FrontendL2M1R3Rule",
    "FrontendL2M1R4Rule",
    "FrontendL2M1RuntimeBoundaryParams",
    "FrontendL2M1StaticBoundaryParams",
    "FrontendL3M0B1Base",
    "FrontendL3M0B2Base",
    "FrontendL3M0B3Base",
    "FrontendL3M0Module",
    "FrontendL3M0R1Rule",
    "FrontendL3M0R2Rule",
    "FrontendL3M0R3Rule",
    "FrontendL3M0R4Rule",
    "FrontendL3M0RuntimeBoundaryParams",
    "FrontendL3M0StaticBoundaryParams",
    "get_static_module_contract_bundle",
    "KNOWLEDGE_BASE_L0_M0_BOUNDARY_FIELD_MAP",
    "KNOWLEDGE_BASE_L0_M0_MODULE_ID",
    "KNOWLEDGE_BASE_L0_M0_MODULE_KEY",
    "KNOWLEDGE_BASE_L0_M1_BOUNDARY_FIELD_MAP",
    "KNOWLEDGE_BASE_L0_M1_MODULE_ID",
    "KNOWLEDGE_BASE_L0_M1_MODULE_KEY",
    "KNOWLEDGE_BASE_L0_M2_BOUNDARY_FIELD_MAP",
    "KNOWLEDGE_BASE_L0_M2_MODULE_ID",
    "KNOWLEDGE_BASE_L0_M2_MODULE_KEY",
    "KNOWLEDGE_BASE_L1_M0_BOUNDARY_FIELD_MAP",
    "KNOWLEDGE_BASE_L1_M0_MODULE_ID",
    "KNOWLEDGE_BASE_L1_M0_MODULE_KEY",
    "KNOWLEDGE_BASE_L1_M1_BOUNDARY_FIELD_MAP",
    "KNOWLEDGE_BASE_L1_M1_MODULE_ID",
    "KNOWLEDGE_BASE_L1_M1_MODULE_KEY",
    "KNOWLEDGE_BASE_L2_M0_BOUNDARY_FIELD_MAP",
    "KNOWLEDGE_BASE_L2_M0_MODULE_ID",
    "KNOWLEDGE_BASE_L2_M0_MODULE_KEY",
    "KnowledgeBaseL0M0B1Base",
    "KnowledgeBaseL0M0B2Base",
    "KnowledgeBaseL0M0B3Base",
    "KnowledgeBaseL0M0Module",
    "KnowledgeBaseL0M0R1Rule",
    "KnowledgeBaseL0M0R2Rule",
    "KnowledgeBaseL0M0R3Rule",
    "KnowledgeBaseL0M0R4Rule",
    "KnowledgeBaseL0M0RuntimeBoundaryParams",
    "KnowledgeBaseL0M0StaticBoundaryParams",
    "KnowledgeBaseL0M1B1Base",
    "KnowledgeBaseL0M1B2Base",
    "KnowledgeBaseL0M1B3Base",
    "KnowledgeBaseL0M1Module",
    "KnowledgeBaseL0M1R1Rule",
    "KnowledgeBaseL0M1R2Rule",
    "KnowledgeBaseL0M1R3Rule",
    "KnowledgeBaseL0M1R4Rule",
    "KnowledgeBaseL0M1RuntimeBoundaryParams",
    "KnowledgeBaseL0M1StaticBoundaryParams",
    "KnowledgeBaseL0M2B1Base",
    "KnowledgeBaseL0M2B2Base",
    "KnowledgeBaseL0M2B3Base",
    "KnowledgeBaseL0M2Module",
    "KnowledgeBaseL0M2R1Rule",
    "KnowledgeBaseL0M2R2Rule",
    "KnowledgeBaseL0M2R3Rule",
    "KnowledgeBaseL0M2R4Rule",
    "KnowledgeBaseL0M2RuntimeBoundaryParams",
    "KnowledgeBaseL0M2StaticBoundaryParams",
    "KnowledgeBaseL1M0B1Base",
    "KnowledgeBaseL1M0B2Base",
    "KnowledgeBaseL1M0B3Base",
    "KnowledgeBaseL1M0Module",
    "KnowledgeBaseL1M0R1Rule",
    "KnowledgeBaseL1M0R2Rule",
    "KnowledgeBaseL1M0R3Rule",
    "KnowledgeBaseL1M0R4Rule",
    "KnowledgeBaseL1M0RuntimeBoundaryParams",
    "KnowledgeBaseL1M0StaticBoundaryParams",
    "KnowledgeBaseL1M1B1Base",
    "KnowledgeBaseL1M1B2Base",
    "KnowledgeBaseL1M1B3Base",
    "KnowledgeBaseL1M1Module",
    "KnowledgeBaseL1M1R1Rule",
    "KnowledgeBaseL1M1R2Rule",
    "KnowledgeBaseL1M1R3Rule",
    "KnowledgeBaseL1M1R4Rule",
    "KnowledgeBaseL1M1RuntimeBoundaryParams",
    "KnowledgeBaseL1M1StaticBoundaryParams",
    "KnowledgeBaseL2M0B1Base",
    "KnowledgeBaseL2M0B2Base",
    "KnowledgeBaseL2M0B3Base",
    "KnowledgeBaseL2M0Module",
    "KnowledgeBaseL2M0R1Rule",
    "KnowledgeBaseL2M0R2Rule",
    "KnowledgeBaseL2M0R3Rule",
    "KnowledgeBaseL2M0R4Rule",
    "KnowledgeBaseL2M0RuntimeBoundaryParams",
    "KnowledgeBaseL2M0StaticBoundaryParams",
    "MESSAGE_QUEUE_L0_M0_BOUNDARY_FIELD_MAP",
    "MESSAGE_QUEUE_L0_M0_MODULE_ID",
    "MESSAGE_QUEUE_L0_M0_MODULE_KEY",
    "MESSAGE_QUEUE_L1_M0_BOUNDARY_FIELD_MAP",
    "MESSAGE_QUEUE_L1_M0_MODULE_ID",
    "MESSAGE_QUEUE_L1_M0_MODULE_KEY",
    "MessageQueueL0M0B1Base",
    "MessageQueueL0M0B2Base",
    "MessageQueueL0M0B3Base",
    "MessageQueueL0M0Module",
    "MessageQueueL0M0R1Rule",
    "MessageQueueL0M0R2Rule",
    "MessageQueueL0M0R3Rule",
    "MessageQueueL0M0R4Rule",
    "MessageQueueL0M0R5Rule",
    "MessageQueueL0M0RuntimeBoundaryParams",
    "MessageQueueL0M0StaticBoundaryParams",
    "MessageQueueL1M0B1Base",
    "MessageQueueL1M0B2Base",
    "MessageQueueL1M0B3Base",
    "MessageQueueL1M0Module",
    "MessageQueueL1M0R1Rule",
    "MessageQueueL1M0R2Rule",
    "MessageQueueL1M0R3Rule",
    "MessageQueueL1M0R4Rule",
    "MessageQueueL1M0RuntimeBoundaryParams",
    "MessageQueueL1M0StaticBoundaryParams",
    "RUNTIME_ENV_L0_M0_BOUNDARY_FIELD_MAP",
    "RUNTIME_ENV_L0_M0_MODULE_ID",
    "RUNTIME_ENV_L0_M0_MODULE_KEY",
    "RuntimeEnvL0M0B1Base",
    "RuntimeEnvL0M0B2Base",
    "RuntimeEnvL0M0B3Base",
    "RuntimeEnvL0M0Module",
    "RuntimeEnvL0M0R1Rule",
    "RuntimeEnvL0M0R2Rule",
    "RuntimeEnvL0M0R3Rule",
    "RuntimeEnvL0M0R4Rule",
    "RuntimeEnvL0M0RuntimeBoundaryParams",
    "RuntimeEnvL0M0StaticBoundaryParams",
    "SHELF_L0_M0_BOUNDARY_FIELD_MAP",
    "SHELF_L0_M0_MODULE_ID",
    "SHELF_L0_M0_MODULE_KEY",
    "SHELF_L1_M0_BOUNDARY_FIELD_MAP",
    "SHELF_L1_M0_MODULE_ID",
    "SHELF_L1_M0_MODULE_KEY",
    "SHELF_L2_M0_BOUNDARY_FIELD_MAP",
    "SHELF_L2_M0_MODULE_ID",
    "SHELF_L2_M0_MODULE_KEY",
    "ShelfL0M0B1Base",
    "ShelfL0M0B2Base",
    "ShelfL0M0B3Base",
    "ShelfL0M0Module",
    "ShelfL0M0R1Rule",
    "ShelfL0M0R2Rule",
    "ShelfL0M0R3Rule",
    "ShelfL0M0R4Rule",
    "ShelfL0M0RuntimeBoundaryParams",
    "ShelfL0M0StaticBoundaryParams",
    "ShelfL1M0B1Base",
    "ShelfL1M0B2Base",
    "ShelfL1M0B3Base",
    "ShelfL1M0Module",
    "ShelfL1M0R1Rule",
    "ShelfL1M0R2Rule",
    "ShelfL1M0R3Rule",
    "ShelfL1M0R4Rule",
    "ShelfL1M0RuntimeBoundaryParams",
    "ShelfL1M0StaticBoundaryParams",
    "ShelfL2M0B1Base",
    "ShelfL2M0B2Base",
    "ShelfL2M0B3Base",
    "ShelfL2M0Module",
    "ShelfL2M0R1Rule",
    "ShelfL2M0R2Rule",
    "ShelfL2M0R3Rule",
    "ShelfL2M0R4Rule",
    "ShelfL2M0RuntimeBoundaryParams",
    "ShelfL2M0StaticBoundaryParams",
    "STATIC_MODULE_CONTRACTS",
    "StaticModuleContractBundle",
]
