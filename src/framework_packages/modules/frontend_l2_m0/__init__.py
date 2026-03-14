from framework_packages.contract import (
    PackageCompileInput,
    PackageCompileResult,
    RuntimeValidationHook,
)
from framework_packages.modules.runtime_support import assemble_frontend_app_spec, assemble_runtime_page_blueprint
from framework_packages.static import StaticFrameworkPackage


class FrontendL2M0Package(StaticFrameworkPackage):
    FRAMEWORK_FILE = "framework/frontend/L2-M0-前端框架标准模块.md"
    MODULE_ID = "frontend.L2.M0"

    def compile(self, payload: PackageCompileInput) -> PackageCompileResult:
        base = super().compile(payload)
        frontend_spec = assemble_frontend_app_spec(payload)
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
                "frontend_app_spec": frontend_spec,
                "runtime_page_blueprint": assemble_runtime_page_blueprint(frontend_spec),
            },
            runtime_validation_hooks=(
                RuntimeValidationHook(
                    scope="frontend",
                    validator_path="frontend_kernel.validators:validate_frontend_rules",
                    summarizer_path="frontend_kernel.validators:summarize_frontend_rules",
                ),
            ),
        )


__all__ = ["FrontendL2M0Package"]
