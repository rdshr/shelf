from framework_packages.contract import PackageCompileInput, PackageCompileResult
from framework_packages.modules.runtime_support import assemble_backend_service_spec, assemble_runtime_api_blueprint
from framework_packages.static import StaticFrameworkPackage


class BackendL2M0Package(StaticFrameworkPackage):
    FRAMEWORK_FILE = "framework/backend/L2-M0-知识库接口框架标准模块.md"
    MODULE_ID = "backend.L2.M0"

    def compile(self, payload: PackageCompileInput) -> PackageCompileResult:
        base = super().compile(payload)
        service_spec = assemble_backend_service_spec(payload)
        return PackageCompileResult(
            framework_file=base.framework_file,
            module_id=base.module_id,
            entry_class=base.entry_class,
            package_module=base.package_module,
            package_source_file=base.package_source_file,
            config_contract=base.config_contract,
            child_slots=base.child_slots,
            config_slice=base.config_slice,
            export=base.export,
            evidence=base.evidence,
            runtime_exports={
                "backend_service_spec": service_spec,
                "runtime_api_blueprint": assemble_runtime_api_blueprint(service_spec),
            },
        )


__all__ = ["BackendL2M0Package"]
