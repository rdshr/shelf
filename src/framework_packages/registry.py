from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from framework_ir import FrameworkModule, FrameworkRegistry

from .contract import instantiate_framework_package_contract


@dataclass(frozen=True)
class FrameworkPackageRegistration:
    framework_file: str
    module_id: str
    entry_class_name: str
    package_module: str
    entry_class: type[Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "framework_file": self.framework_file,
            "module_id": self.module_id,
            "entry_class_name": self.entry_class_name,
            "package_module": self.package_module,
            "entry_class_path": f"{self.package_module}.{self.entry_class_name}",
        }


class FrameworkPackageRegistry:
    def __init__(self) -> None:
        self._by_framework_file: dict[str, FrameworkPackageRegistration] = {}
        self._by_module_id: dict[str, FrameworkPackageRegistration] = {}

    def register(self, entry_class: type[Any]) -> None:
        contract = instantiate_framework_package_contract(entry_class)
        framework_file = contract.framework_file()
        module_id = contract.module_id()
        package_module = entry_class.__module__
        registration = FrameworkPackageRegistration(
            framework_file=framework_file,
            module_id=module_id,
            entry_class_name=entry_class.__name__,
            package_module=package_module,
            entry_class=entry_class,
        )

        existing_by_file = self._by_framework_file.get(framework_file)
        if existing_by_file is not None and existing_by_file.entry_class is not entry_class:
            raise ValueError(f"framework file registered more than once: {framework_file}")

        existing_by_module = self._by_module_id.get(module_id)
        if existing_by_module is not None and existing_by_module.entry_class is not entry_class:
            raise ValueError(f"module id registered more than once: {module_id}")

        self._by_framework_file[framework_file] = registration
        self._by_module_id[module_id] = registration

    def iter_registrations(self) -> tuple[FrameworkPackageRegistration, ...]:
        return tuple(sorted(self._by_module_id.values(), key=lambda item: item.module_id))

    def get_by_framework_file(self, framework_file: str) -> FrameworkPackageRegistration:
        registration = self._by_framework_file.get(framework_file)
        if registration is None:
            raise KeyError(f"unimplemented framework file: {framework_file}")
        return registration

    def get_by_module_id(self, module_id: str) -> FrameworkPackageRegistration:
        registration = self._by_module_id.get(module_id)
        if registration is None:
            raise KeyError(f"unregistered module id: {module_id}")
        return registration

    def detect_unimplemented_framework_files(self, framework_registry: FrameworkRegistry) -> tuple[str, ...]:
        missing = [
            item.path
            for item in framework_registry.modules
            if item.path not in self._by_framework_file
        ]
        return tuple(sorted(missing))

    def detect_orphan_packages(self, framework_registry: FrameworkRegistry) -> tuple[str, ...]:
        framework_files = {item.path for item in framework_registry.modules}
        orphans = [
            item.framework_file
            for item in self.iter_registrations()
            if item.framework_file not in framework_files
        ]
        return tuple(sorted(orphans))

    def validate_against_framework(self, framework_registry: FrameworkRegistry) -> None:
        from .validators import validate_package_config_contracts, validate_unique_package_entry_classes

        validate_unique_package_entry_classes(self)
        validate_package_config_contracts(self)
        missing = self.detect_unimplemented_framework_files(framework_registry)
        if missing:
            raise ValueError("framework files missing package implementations: " + ", ".join(missing))
        orphans = self.detect_orphan_packages(framework_registry)
        if orphans:
            raise ValueError("package registrations point at missing framework files: " + ", ".join(orphans))
        for module in framework_registry.modules:
            registration = self.get_by_framework_file(module.path)
            if registration.module_id != module.module_id:
                raise ValueError(
                    f"module id mismatch for {module.path}: registry={registration.module_id} framework={module.module_id}"
                )
