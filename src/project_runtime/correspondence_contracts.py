from __future__ import annotations

import keyword
import re
from dataclasses import asdict, fields, is_dataclass
from typing import Any, ClassVar, cast


class UnsetValue:
    """Sentinel that means runtime value is not provided."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "UNSET"


UNSET = UnsetValue()


def is_unset(value: Any) -> bool:
    return isinstance(value, UnsetValue)


def module_key_from_id(module_id: str) -> str:
    return str(module_id).strip().replace(".", "__")


def boundary_field_name(boundary_id: str) -> str:
    text = str(boundary_id).strip().lower()
    text = re.sub(r"[^a-z0-9_]", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    if not text:
        text = "boundary"
    if text[0].isdigit():
        text = f"field_{text}"
    if keyword.iskeyword(text):
        text = f"{text}_value"
    return text


def module_class_name_fragment(module_id: str) -> str:
    parts = [segment for segment in str(module_id).replace(".", "_").split("_") if segment]
    return "".join(part.capitalize() for part in parts)


class StaticBoundaryParamsContract:
    framework_module_id: ClassVar[str]
    module_key: ClassVar[str]
    boundary_field_map: ClassVar[dict[str, str]]

    def to_dict(self) -> dict[str, Any]:
        if is_dataclass(self):
            return asdict(self)
        return {
            field_name: getattr(self, field_name)
            for field_name in dir(self)
            if not field_name.startswith("_")
        }


class RuntimeBoundaryParamsContract:
    framework_module_id: ClassVar[str]
    module_key: ClassVar[str]
    boundary_field_map: ClassVar[dict[str, str]]

    def to_dict(self) -> dict[str, Any]:
        if is_dataclass(self):
            payload = asdict(self)
        else:
            payload = {
                field_name: getattr(self, field_name)
                for field_name in dir(self)
                if not field_name.startswith("_")
            }
        for key, value in list(payload.items()):
            if is_unset(value):
                payload[key] = "UNSET"
        return payload


class BaseContract:
    framework_base_id: ClassVar[str]
    owner_module_id: ClassVar[str]
    framework_base_short_id: ClassVar[str]
    boundary_ids: ClassVar[tuple[str, ...]]

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        return {
            "framework_base_id": cls.framework_base_id,
            "framework_base_short_id": cls.framework_base_short_id,
            "owner_module_id": cls.owner_module_id,
            "boundary_ids": list(cls.boundary_ids),
            "class_name": cls.__name__,
        }


class RuleContract:
    framework_rule_id: ClassVar[str]
    owner_module_id: ClassVar[str]
    framework_rule_short_id: ClassVar[str]
    base_ids: ClassVar[tuple[str, ...]]
    boundary_ids: ClassVar[tuple[str, ...]]

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        return {
            "framework_rule_id": cls.framework_rule_id,
            "framework_rule_short_id": cls.framework_rule_short_id,
            "owner_module_id": cls.owner_module_id,
            "base_ids": list(cls.base_ids),
            "boundary_ids": list(cls.boundary_ids),
            "class_name": cls.__name__,
        }


class ModuleContract:
    framework_module_id: ClassVar[str]
    module_key: ClassVar[str]
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]]
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]]
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]]
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]]
    boundary_field_map: ClassVar[dict[str, str]]
    merge_policy: ClassVar[str]

    @classmethod
    def static_params_from_mapping(cls, payload: dict[str, Any]) -> StaticBoundaryParamsContract:
        field_names = {
            field.name
            for field in fields(cast(Any, cls.StaticBoundaryParams))
        }
        kwargs = {field_name: payload.get(field_name) for field_name in field_names}
        return cls.StaticBoundaryParams(**kwargs)

    @classmethod
    def runtime_params_default(cls) -> RuntimeBoundaryParamsContract:
        return cls.RuntimeBoundaryParams()

    @classmethod
    def build_boundary_context(
        cls,
        static_params: StaticBoundaryParamsContract,
        runtime_params: RuntimeBoundaryParamsContract,
    ) -> dict[str, dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {}
        for boundary_id, field_name in cls.boundary_field_map.items():
            static_value = getattr(static_params, field_name)
            runtime_value = getattr(runtime_params, field_name)
            runtime_provided = not is_unset(runtime_value)
            value = runtime_value if runtime_provided else static_value
            merged[boundary_id] = {
                "field_name": field_name,
                "static_value": static_value,
                "runtime_value": "UNSET" if is_unset(runtime_value) else runtime_value,
                "runtime_provided": runtime_provided,
                "value": value,
                "merge_policy": cls.merge_policy,
            }
        return merged
