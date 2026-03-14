from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from framework_ir import FrameworkModule


@dataclass(frozen=True)
class PackageConfigFieldRule:
    path: str
    presence: str
    default_value: Any | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "path": self.path,
            "presence": self.presence,
        }
        if self.presence == "default":
            payload["default_value"] = self.default_value
        return payload


@dataclass(frozen=True)
class PackageConfigContract:
    fields: tuple[PackageConfigFieldRule, ...] = ()
    covered_roots: tuple[str, ...] = ()
    allow_extra_paths: bool = False

    @property
    def required_paths(self) -> tuple[str, ...]:
        return tuple(item.path for item in self.fields if item.presence == "required")

    @property
    def optional_paths(self) -> tuple[str, ...]:
        return tuple(item.path for item in self.fields if item.presence == "optional")

    @property
    def default_paths(self) -> tuple[str, ...]:
        return tuple(item.path for item in self.fields if item.presence == "default")

    @property
    def forbidden_paths(self) -> tuple[str, ...]:
        return tuple(item.path for item in self.fields if item.presence == "forbidden")

    def to_dict(self) -> dict[str, Any]:
        return {
            "fields": [item.to_dict() for item in self.fields],
            "covered_roots": list(self.covered_roots),
            "allow_extra_paths": self.allow_extra_paths,
        }


@dataclass(frozen=True)
class PackageChildSlot:
    slot_id: str
    child_module_id: str
    required: bool = True
    role: str = "dependency"

    def to_dict(self) -> dict[str, Any]:
        return {
            "slot_id": self.slot_id,
            "child_module_id": self.child_module_id,
            "required": self.required,
            "role": self.role,
        }


@dataclass(frozen=True)
class PackageSelectedRoot:
    slot_id: str
    role: str
    module_id: str
    framework_file: str
    entry_class_name: str

    def to_dict(self) -> dict[str, str]:
        return {
            "slot_id": self.slot_id,
            "role": self.role,
            "module_id": self.module_id,
            "framework_file": self.framework_file,
            "entry_class_name": self.entry_class_name,
        }


@dataclass(frozen=True)
class PackageCompileInput:
    framework_module: FrameworkModule
    config_slice: dict[str, Any]
    child_exports: dict[str, dict[str, Any]]
    selected_roots: tuple[PackageSelectedRoot, ...] = ()

    def root_module_id(self, role: str) -> str:
        for item in self.selected_roots:
            if item.role == role:
                return item.module_id
        raise KeyError(f"missing selected root role: {role}")


@dataclass(frozen=True)
class PackageCompileResult:
    framework_file: str
    module_id: str
    entry_class: str
    package_module: str
    config_contract: PackageConfigContract
    child_slots: tuple[PackageChildSlot, ...]
    config_slice: dict[str, Any]
    export: dict[str, Any]
    evidence: dict[str, Any]
    runtime_exports: dict[str, Any] = field(default_factory=dict)
    runtime_entrypoints: tuple["RuntimeAppEntrypoint", ...] = ()
    runtime_validation_hooks: tuple["RuntimeValidationHook", ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "framework_file": self.framework_file,
            "module_id": self.module_id,
            "entry_class": self.entry_class,
            "package_module": self.package_module,
            "config_contract": self.config_contract.to_dict(),
            "child_slots": [item.to_dict() for item in self.child_slots],
            "config_slice": self.config_slice,
            "export": self.export,
            "evidence": self.evidence,
            "runtime_exports": self.runtime_exports,
            "runtime_entrypoints": [item.to_dict() for item in self.runtime_entrypoints],
            "runtime_validation_hooks": [item.to_dict() for item in self.runtime_validation_hooks],
        }


@dataclass(frozen=True)
class RuntimeAppEntrypoint:
    entrypoint_id: str
    factory_path: str

    def to_dict(self) -> dict[str, str]:
        return {
            "entrypoint_id": self.entrypoint_id,
            "factory_path": self.factory_path,
        }


@dataclass(frozen=True)
class RuntimeValidationHook:
    scope: str
    validator_path: str
    summarizer_path: str

    def to_dict(self) -> dict[str, str]:
        return {
            "scope": self.scope,
            "validator_path": self.validator_path,
            "summarizer_path": self.summarizer_path,
        }


@runtime_checkable
class FrameworkPackageContract(Protocol):
    def framework_file(self) -> str: ...

    def module_id(self) -> str: ...

    def config_contract(self) -> PackageConfigContract: ...

    def child_slots(self, framework_module: FrameworkModule) -> tuple[PackageChildSlot, ...]: ...

    def compile(self, payload: PackageCompileInput) -> PackageCompileResult: ...


def instantiate_framework_package_contract(entry_class: type[Any]) -> FrameworkPackageContract:
    contract = entry_class()
    if not isinstance(contract, FrameworkPackageContract):
        raise TypeError(f"{entry_class.__module__}.{entry_class.__name__} does not implement FrameworkPackageContract")
    return contract


def is_framework_package_entry_class(candidate: object, *, module_name: str) -> bool:
    if not isinstance(candidate, type):
        return False
    if candidate.__module__ != module_name:
        return False
    try:
        instantiate_framework_package_contract(candidate)
    except (TypeError, ValueError):
        return False
    return True
