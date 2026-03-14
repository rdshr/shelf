from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from framework_ir import FrameworkModule


@dataclass(frozen=True)
class PackageConfigContract:
    required_paths: tuple[str, ...]
    optional_paths: tuple[str, ...] = ()
    allow_extra_paths: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "required_paths": list(self.required_paths),
            "optional_paths": list(self.optional_paths),
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
class PackageCompileInput:
    framework_module: FrameworkModule
    config_slice: dict[str, Any]
    child_exports: dict[str, dict[str, Any]]


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
        }


class FrameworkPackageContract(Protocol):
    def framework_file(self) -> str: ...

    def module_id(self) -> str: ...

    def config_contract(self) -> PackageConfigContract: ...

    def child_slots(self, framework_module: FrameworkModule) -> tuple[PackageChildSlot, ...]: ...

    def compile(self, payload: PackageCompileInput) -> PackageCompileResult: ...
