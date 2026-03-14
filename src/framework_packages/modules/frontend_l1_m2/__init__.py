from framework_packages.contract import PackageCompileInput, PackageCompileResult, PackageConfigContract, PackageConfigFieldRule
from framework_packages.modules.runtime_support import compose_frontend_surface_fragment
from framework_packages.static import StaticFrameworkPackage


def _required_field(path: str) -> PackageConfigFieldRule:
    return PackageConfigFieldRule(path=path, presence="required")


class FrontendL1M2Package(StaticFrameworkPackage):
    FRAMEWORK_FILE = "framework/frontend/L1-M2-展示与容器原子模块.md"
    MODULE_ID = "frontend.L1.M2"

    def config_contract(self) -> PackageConfigContract:
        return PackageConfigContract(
            fields=(
                _required_field("truth.surface.shell"),
                _required_field("truth.surface.layout_variant"),
                _required_field("truth.surface.sidebar_width"),
                _required_field("truth.surface.preview_mode"),
                _required_field("truth.surface.density"),
                _required_field("truth.surface.copy.hero_kicker"),
                _required_field("truth.surface.copy.hero_title"),
                _required_field("truth.surface.copy.hero_copy"),
                _required_field("truth.surface.copy.library_title"),
                _required_field("truth.surface.copy.preview_title"),
                _required_field("truth.surface.copy.toc_title"),
                _required_field("truth.surface.copy.chat_title"),
                _required_field("truth.surface.copy.empty_state_title"),
                _required_field("truth.surface.copy.empty_state_copy"),
                _required_field("truth.visual.brand"),
                _required_field("truth.visual.accent"),
                _required_field("truth.visual.surface_preset"),
                _required_field("truth.visual.radius_scale"),
                _required_field("truth.visual.shadow_level"),
                _required_field("truth.visual.font_scale"),
                _required_field("truth.preview.preview_variant"),
                _required_field("truth.library.knowledge_base_name"),
                _required_field("truth.showcase_page.title"),
            ),
            covered_roots=(
                "truth.surface",
                "truth.visual",
                "truth.preview.preview_variant",
                "truth.library.knowledge_base_name",
                "truth.showcase_page.title",
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
            runtime_exports={"frontend_surface_fragment": compose_frontend_surface_fragment(payload)},
        )


__all__ = ["FrontendL1M2Package"]
