from framework_packages.contract import PackageCompileInput, PackageCompileResult, PackageConfigContract, PackageConfigFieldRule
from framework_packages.modules.runtime_support import compose_frontend_navigation_fragment
from framework_packages.static import StaticFrameworkPackage


def _required_field(path: str) -> PackageConfigFieldRule:
    return PackageConfigFieldRule(path=path, presence="required")


class FrontendL1M3Package(StaticFrameworkPackage):
    FRAMEWORK_FILE = "framework/frontend/L1-M3-集合与导航原子模块.md"
    MODULE_ID = "frontend.L1.M3"

    def config_contract(self) -> PackageConfigContract:
        return PackageConfigContract(
            fields=(
                _required_field("truth.surface.copy.hero_title"),
                _required_field("truth.surface.copy.library_title"),
                _required_field("truth.route.home"),
                _required_field("truth.route.workbench"),
                _required_field("truth.route.basketball_showcase"),
                _required_field("truth.route.knowledge_list"),
                _required_field("truth.route.knowledge_detail"),
                _required_field("truth.route.document_detail_prefix"),
                _required_field("truth.route.api_prefix"),
                _required_field("truth.showcase_page.title"),
                _required_field("truth.showcase_page.kicker"),
                _required_field("truth.showcase_page.headline"),
                _required_field("truth.showcase_page.intro"),
                _required_field("truth.showcase_page.back_to_chat_label"),
                _required_field("truth.showcase_page.browse_knowledge_label"),
            ),
            covered_roots=(
                "truth.surface.copy.hero_title",
                "truth.surface.copy.library_title",
                "truth.route",
                "truth.showcase_page",
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
            runtime_exports={"frontend_navigation_fragment": compose_frontend_navigation_fragment(payload)},
        )


__all__ = ["FrontendL1M3Package"]
