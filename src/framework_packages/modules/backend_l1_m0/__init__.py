from framework_packages.contract import PackageCompileInput, PackageCompileResult, PackageConfigContract, PackageConfigFieldRule
from framework_packages.modules.runtime_support import compose_backend_service_fragment
from framework_packages.static import StaticFrameworkPackage


def _required_field(path: str) -> PackageConfigFieldRule:
    return PackageConfigFieldRule(path=path, presence="required")


class BackendL1M0Package(StaticFrameworkPackage):
    FRAMEWORK_FILE = "framework/backend/L1-M0-目录预览对话编排模块.md"
    MODULE_ID = "backend.L1.M0"

    def config_contract(self) -> PackageConfigContract:
        return PackageConfigContract(
            fields=(
                _required_field("selection.preset"),
                _required_field("truth.route.home"),
                _required_field("truth.route.workbench"),
                _required_field("truth.route.basketball_showcase"),
                _required_field("truth.route.knowledge_list"),
                _required_field("truth.route.knowledge_detail"),
                _required_field("truth.route.document_detail_prefix"),
                _required_field("truth.route.api_prefix"),
                _required_field("truth.library.knowledge_base_id"),
                _required_field("truth.library.knowledge_base_name"),
                _required_field("truth.library.knowledge_base_description"),
                _required_field("truth.library.source_types"),
                _required_field("truth.library.metadata_fields"),
                _required_field("truth.library.allow_create"),
                _required_field("truth.library.allow_delete"),
                _required_field("truth.chat.citation_style"),
                _required_field("truth.context.selection_mode"),
                _required_field("truth.context.max_citations"),
                _required_field("truth.context.max_preview_sections"),
                _required_field("truth.context.sticky_document"),
                _required_field("truth.return.targets"),
                _required_field("truth.return.anchor_restore"),
                _required_field("refinement.backend.renderer"),
                _required_field("refinement.backend.transport"),
                _required_field("refinement.backend.retrieval_strategy"),
                PackageConfigFieldRule(
                    path="refinement.evidence.project_config_endpoint",
                    presence="default",
                    default_value="/api/knowledge/project-config",
                ),
            ),
            covered_roots=(
                "selection.preset",
                "truth.route",
                "truth.library.knowledge_base_id",
                "truth.library.knowledge_base_name",
                "truth.library.knowledge_base_description",
                "truth.library.source_types",
                "truth.library.metadata_fields",
                "truth.library.allow_create",
                "truth.library.allow_delete",
                "truth.chat.citation_style",
                "truth.context",
                "truth.return.targets",
                "truth.return.anchor_restore",
                "refinement.backend",
                "refinement.evidence",
            ),
        )

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
            runtime_exports={"backend_service_fragment": compose_backend_service_fragment(payload)},
        )


__all__ = ["BackendL1M0Package"]
