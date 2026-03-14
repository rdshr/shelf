from framework_packages.contract import (
    PackageCompileInput,
    PackageCompileResult,
    PackageConfigContract,
    PackageConfigFieldRule,
    RuntimeValidationHook,
)
from framework_packages.static import StaticFrameworkPackage
from project_runtime.export_builders import build_frontend_runtime_exports


def _required_field(path: str) -> PackageConfigFieldRule:
    return PackageConfigFieldRule(path=path, presence="required")


class FrontendL2M0Package(StaticFrameworkPackage):
    FRAMEWORK_FILE = "framework/frontend/L2-M0-前端框架标准模块.md"
    MODULE_ID = "frontend.L2.M0"

    def config_contract(self) -> PackageConfigContract:
        return PackageConfigContract(
            fields=(
                _required_field("selection.preset"),
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
                _required_field("truth.a11y.reading_order"),
                _required_field("truth.a11y.keyboard_nav"),
                _required_field("truth.a11y.announcements"),
                _required_field("truth.library.knowledge_base_id"),
                _required_field("truth.library.knowledge_base_name"),
                _required_field("truth.library.knowledge_base_description"),
                _required_field("truth.library.enabled"),
                _required_field("truth.library.source_types"),
                _required_field("truth.library.metadata_fields"),
                _required_field("truth.library.default_focus"),
                _required_field("truth.library.list_variant"),
                _required_field("truth.library.allow_create"),
                _required_field("truth.library.allow_delete"),
                _required_field("truth.library.search_placeholder"),
                _required_field("truth.preview.enabled"),
                _required_field("truth.preview.renderers"),
                _required_field("truth.preview.anchor_mode"),
                _required_field("truth.preview.show_toc"),
                _required_field("truth.preview.preview_variant"),
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
                PackageConfigFieldRule(
                    path="truth.context.sticky_document",
                    presence="default",
                    default_value=False,
                ),
                _required_field("truth.return.enabled"),
                _required_field("truth.return.targets"),
                _required_field("truth.return.anchor_restore"),
                _required_field("truth.return.citation_card_variant"),
                _required_field("refinement.frontend.renderer"),
                _required_field("refinement.frontend.style_profile"),
                _required_field("refinement.frontend.script_profile"),
            ),
            covered_roots=(
                "selection.preset",
                "truth.surface",
                "truth.visual",
                "truth.route",
                "truth.showcase_page",
                "truth.a11y",
                "truth.library",
                "truth.preview",
                "truth.chat",
                "truth.context.sticky_document",
                "truth.return",
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
            config_contract=base.config_contract,
            child_slots=base.child_slots,
            config_slice=base.config_slice,
            export=base.export,
            evidence=base.evidence,
            runtime_exports=build_frontend_runtime_exports(payload),
            runtime_validation_hooks=(
                RuntimeValidationHook(
                    scope="frontend",
                    validator_path="frontend_kernel.validators:validate_frontend_rules",
                    summarizer_path="frontend_kernel.validators:summarize_frontend_rules",
                ),
            ),
        )


__all__ = ["FrontendL2M0Package"]
