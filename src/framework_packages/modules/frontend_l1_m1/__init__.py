from framework_packages.contract import PackageCompileInput, PackageCompileResult, PackageConfigContract, PackageConfigFieldRule
from framework_packages.modules.runtime_support import compose_frontend_conversation_fragment
from framework_packages.static import StaticFrameworkPackage


def _required_field(path: str) -> PackageConfigFieldRule:
    return PackageConfigFieldRule(path=path, presence="required")


class FrontendL1M1Package(StaticFrameworkPackage):
    FRAMEWORK_FILE = "framework/frontend/L1-M1-文本输入原子模块.md"
    MODULE_ID = "frontend.L1.M1"

    def config_contract(self) -> PackageConfigContract:
        return PackageConfigContract(
            fields=(
                _required_field("truth.chat.enabled"),
                _required_field("truth.chat.citations_enabled"),
                _required_field("truth.chat.mode"),
                _required_field("truth.chat.citation_style"),
                _required_field("truth.chat.bubble_variant"),
                _required_field("truth.chat.composer_variant"),
                _required_field("truth.chat.system_prompt"),
                _required_field("truth.chat.welcome_prompts"),
                _required_field("truth.chat.placeholder"),
                _required_field("truth.chat.welcome"),
                _required_field("truth.surface.copy.chat_title"),
                _required_field("truth.showcase_page.title"),
                _required_field("refinement.frontend.renderer"),
                _required_field("refinement.frontend.style_profile"),
                _required_field("refinement.frontend.script_profile"),
            ),
            covered_roots=(
                "truth.chat",
                "truth.surface.copy.chat_title",
                "truth.showcase_page.title",
                "refinement.frontend",
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
            runtime_exports={"frontend_conversation_fragment": compose_frontend_conversation_fragment(payload)},
        )


__all__ = ["FrontendL1M1Package"]
