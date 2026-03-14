from framework_packages.contract import PackageCompileInput, PackageCompileResult, PackageConfigContract, PackageConfigFieldRule
from framework_packages.modules.runtime_support import compose_frontend_feedback_fragment
from framework_packages.static import StaticFrameworkPackage


def _required_field(path: str) -> PackageConfigFieldRule:
    return PackageConfigFieldRule(path=path, presence="required")


class FrontendL1M4Package(StaticFrameworkPackage):
    FRAMEWORK_FILE = "framework/frontend/L1-M4-标记与反馈原子模块.md"
    MODULE_ID = "frontend.L1.M4"

    def config_contract(self) -> PackageConfigContract:
        return PackageConfigContract(
            fields=(
                _required_field("truth.library.list_variant"),
                _required_field("truth.preview.preview_variant"),
                _required_field("truth.chat.citation_style"),
                _required_field("truth.chat.bubble_variant"),
                _required_field("truth.chat.composer_variant"),
                _required_field("truth.return.enabled"),
                _required_field("truth.return.targets"),
                _required_field("truth.return.anchor_restore"),
                _required_field("truth.return.citation_card_variant"),
                _required_field("truth.surface.copy.preview_title"),
            ),
            covered_roots=(
                "truth.library.list_variant",
                "truth.preview.preview_variant",
                "truth.chat.citation_style",
                "truth.chat.bubble_variant",
                "truth.chat.composer_variant",
                "truth.return",
                "truth.surface.copy.preview_title",
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
            runtime_exports={"frontend_feedback_fragment": compose_frontend_feedback_fragment(payload)},
        )


__all__ = ["FrontendL1M4Package"]
