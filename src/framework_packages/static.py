from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any

from framework_ir import FrameworkModule

from .contract import PackageChildSlot, PackageCompileInput, PackageCompileResult, PackageConfigContract


class StaticFrameworkPackage:
    FRAMEWORK_FILE = ""
    MODULE_ID = ""

    def framework_file(self) -> str:
        if not self.FRAMEWORK_FILE:
            raise ValueError("FRAMEWORK_FILE must be declared")
        return self.FRAMEWORK_FILE

    def module_id(self) -> str:
        if not self.MODULE_ID:
            raise ValueError("MODULE_ID must be declared")
        return self.MODULE_ID

    def config_contract(self) -> PackageConfigContract:
        return PackageConfigContract()

    def child_slots(self, framework_module: FrameworkModule) -> tuple[PackageChildSlot, ...]:
        upstream_ids = framework_module.export_surface().upstream_module_ids
        return tuple(
            PackageChildSlot(
                slot_id=f"dependency:{module_id}",
                child_module_id=module_id,
                required=True,
                role="framework_dependency",
            )
            for module_id in upstream_ids
        )

    def compile(self, payload: PackageCompileInput) -> PackageCompileResult:
        framework_module = payload.framework_module
        child_slots = self.child_slots(framework_module)
        package_source_file = _package_source_file(self.__class__)
        export = {
            "module": framework_module.export_surface().to_dict(),
            "framework_title": {
                "zh_cn": framework_module.title_cn,
                "en": framework_module.title_en,
            },
            "capabilities": [item.to_dict() for item in framework_module.capabilities],
            "boundaries": [item.to_dict() for item in framework_module.boundaries],
            "bases": [item.to_dict() for item in framework_module.bases],
            "rules": [item.to_dict() for item in framework_module.rules],
            "verifications": [item.to_dict() for item in framework_module.verifications],
            "child_modules": [item.child_module_id for item in child_slots],
            "config_consumption": sorted(payload.config_slice),
        }
        evidence = {
            "summary": {
                "capability_count": len(framework_module.capabilities),
                "boundary_count": len(framework_module.boundaries),
                "base_count": len(framework_module.bases),
                "rule_count": len(framework_module.rules),
                "verification_count": len(framework_module.verifications),
            },
            "child_export_module_ids": sorted(payload.child_exports),
            "child_runtime_export_module_ids": sorted(payload.child_runtime_exports),
            "config_paths": sorted(payload.config_slice),
        }
        return PackageCompileResult(
            framework_file=self.framework_file(),
            module_id=self.module_id(),
            entry_class=self.__class__.__name__,
            package_module=self.__class__.__module__,
            package_source_file=package_source_file,
            config_contract=self.config_contract(),
            child_slots=child_slots,
            config_slice=dict(payload.config_slice),
            export=export,
            evidence=evidence,
            runtime_exports={},
        )


def _package_source_file(entry_class: type[Any]) -> str:
    module = import_module(entry_class.__module__)
    module_file = getattr(module, "__file__", None)
    if not isinstance(module_file, str):
        raise ValueError(f"missing __file__ for package module: {entry_class.__module__}")
    return Path(module_file).resolve().relative_to(Path(__file__).resolve().parents[2]).as_posix()
