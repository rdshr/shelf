from framework_packages.contract import (
    PackageCompileInput,
    PackageCompileResult,
    RuntimeAppEntrypoint,
    RuntimeValidationHook,
)
from framework_packages.modules.runtime_support import (
    assemble_knowledge_base_domain_spec,
    assemble_runtime_documents,
)
from framework_packages.static import StaticFrameworkPackage


class KnowledgeBaseL2M0Package(StaticFrameworkPackage):
    FRAMEWORK_FILE = "framework/knowledge_base/L2-M0-知识库工作台场景模块.md"
    MODULE_ID = "knowledge_base.L2.M0"

    def compile(self, payload: PackageCompileInput) -> PackageCompileResult:
        base = super().compile(payload)
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
                "knowledge_base_domain_spec": assemble_knowledge_base_domain_spec(payload),
                "runtime_documents": assemble_runtime_documents(payload),
            },
            runtime_entrypoints=(
                RuntimeAppEntrypoint(
                    entrypoint_id="project_runtime_app",
                    factory_path="project_runtime.runtime_app:build_project_runtime_app",
                ),
            ),
            runtime_validation_hooks=(
                RuntimeValidationHook(
                    scope="knowledge_base",
                    validator_path="knowledge_base_framework.validators:validate_workbench_rules",
                    summarizer_path="knowledge_base_framework.validators:summarize_workbench_rules",
                ),
            ),
        )


__all__ = ["KnowledgeBaseL2M0Package"]
