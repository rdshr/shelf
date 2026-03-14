from framework_packages.contract import PackageCompileInput, PackageCompileResult, PackageConfigContract, PackageConfigFieldRule
from framework_packages.modules.runtime_support import compose_frontend_action_fragment
from framework_packages.static import StaticFrameworkPackage


def _required_field(path: str) -> PackageConfigFieldRule:
    return PackageConfigFieldRule(path=path, presence="required")


class FrontendL1M0Package(StaticFrameworkPackage):
    FRAMEWORK_FILE = "framework/frontend/L1-M0-触发与选择原子模块.md"
    MODULE_ID = "frontend.L1.M0"

    def config_contract(self) -> PackageConfigContract:
        return PackageConfigContract(
            fields=(
                _required_field("selection.preset"),
                _required_field("truth.a11y.reading_order"),
                _required_field("truth.a11y.keyboard_nav"),
                _required_field("truth.a11y.announcements"),
                _required_field("truth.context.sticky_document"),
                _required_field("truth.library.allow_create"),
                _required_field("truth.library.allow_delete"),
                _required_field("truth.route.home"),
                _required_field("truth.route.workbench"),
                _required_field("truth.route.basketball_showcase"),
                _required_field("truth.route.knowledge_list"),
                _required_field("truth.route.knowledge_detail"),
                _required_field("truth.route.document_detail_prefix"),
                _required_field("truth.route.api_prefix"),
                _required_field("truth.surface.copy.library_title"),
                _required_field("truth.surface.copy.preview_title"),
                _required_field("truth.surface.copy.chat_title"),
            ),
            covered_roots=(
                "selection.preset",
                "truth.a11y",
                "truth.context.sticky_document",
                "truth.library.allow_create",
                "truth.library.allow_delete",
                "truth.route",
                "truth.surface.copy.library_title",
                "truth.surface.copy.preview_title",
                "truth.surface.copy.chat_title",
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
            runtime_exports={"frontend_action_fragment": compose_frontend_action_fragment(payload)},
        )


__all__ = ["FrontendL1M0Package"]
