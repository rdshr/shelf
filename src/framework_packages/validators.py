from __future__ import annotations

import importlib
import inspect

from .contract import PackageConfigContract, instantiate_framework_package_contract, is_framework_package_entry_class
from .registry import FrameworkPackageRegistry


def validate_unique_package_entry_classes(registry: FrameworkPackageRegistry) -> None:
    errors: list[str] = []
    for registration in registry.iter_registrations():
        module = importlib.import_module(registration.package_module)
        entry_classes = [
            obj
            for _, obj in inspect.getmembers(module, inspect.isclass)
            if is_framework_package_entry_class(obj, module_name=module.__name__)
        ]
        if len(entry_classes) != 1:
            errors.append(
                f"{registration.package_module} must expose exactly one package entry class, found {len(entry_classes)}"
            )
            continue
        if entry_classes[0].__name__ != registration.entry_class_name:
            errors.append(
                f"{registration.package_module} registered {registration.entry_class_name} but formal entry is {entry_classes[0].__name__}"
            )
    if errors:
        raise ValueError("package entry validation failed: " + " | ".join(errors))


def validate_package_config_contracts(registry: FrameworkPackageRegistry) -> None:
    errors: list[str] = []
    for registration in registry.iter_registrations():
        contract = instantiate_framework_package_contract(registration.entry_class).config_contract()
        errors.extend(_validate_config_contract(contract, package_id=registration.module_id))
    if errors:
        raise ValueError("package config contract validation failed: " + " | ".join(errors))


def _validate_config_contract(contract: PackageConfigContract, *, package_id: str) -> list[str]:
    errors: list[str] = []
    seen_paths: set[str] = set()
    for field in contract.fields:
        if field.path in seen_paths:
            errors.append(f"{package_id} declares duplicate config path: {field.path}")
        seen_paths.add(field.path)
        if field.presence not in {"required", "optional", "default", "forbidden"}:
            errors.append(f"{package_id} declares unsupported config presence: {field.presence}")
        if contract.allow_extra_paths:
            continue
        if not any(_covers_path(field.path, root) for root in contract.covered_roots):
            errors.append(f"{package_id} does not cover declared config path: {field.path}")
    return errors


def _covers_path(path: str, root: str) -> bool:
    return path == root or path.startswith(f"{root}.")
