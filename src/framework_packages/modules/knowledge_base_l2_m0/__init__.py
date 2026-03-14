from framework_packages.contract import (
    PackageCompileInput,
    PackageCompileResult,
    PackageConfigContract,
    PackageConfigFieldRule,
    RuntimeAppEntrypoint,
    RuntimeValidationHook,
)
from framework_packages.static import StaticFrameworkPackage
from project_runtime.export_builders import build_knowledge_base_runtime_exports


def _required_field(path: str) -> PackageConfigFieldRule:
    return PackageConfigFieldRule(path=path, presence="required")


class KnowledgeBaseL2M0Package(StaticFrameworkPackage):
    FRAMEWORK_FILE = "framework/knowledge_base/L2-M0-知识库工作台场景模块.md"
    MODULE_ID = "knowledge_base.L2.M0"

    def config_contract(self) -> PackageConfigContract:
        return PackageConfigContract(
            fields=(
                _required_field("truth.surface.layout_variant"),
                _required_field("truth.surface.sidebar_width"),
                _required_field("truth.surface.preview_mode"),
                _required_field("truth.surface.density"),
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
                _required_field("truth.context.selection_mode"),
                _required_field("truth.context.max_citations"),
                _required_field("truth.context.max_preview_sections"),
                _required_field("truth.context.sticky_document"),
                _required_field("truth.return.enabled"),
                _required_field("truth.return.targets"),
                _required_field("truth.return.anchor_restore"),
                _required_field("truth.return.citation_card_variant"),
                _required_field("truth.documents"),
            ),
            covered_roots=(
                "truth.surface.layout_variant",
                "truth.surface.sidebar_width",
                "truth.surface.preview_mode",
                "truth.surface.density",
                "truth.library",
                "truth.preview",
                "truth.chat",
                "truth.context",
                "truth.return",
                "truth.documents",
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
            runtime_exports=build_knowledge_base_runtime_exports(payload),
            runtime_entrypoints=(
                RuntimeAppEntrypoint(
                    entrypoint_id="knowledge_base_runtime_app",
                    factory_path="knowledge_base_runtime.app:build_knowledge_base_runtime_app",
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
