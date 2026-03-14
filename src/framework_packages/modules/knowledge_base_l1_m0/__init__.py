from framework_packages.contract import PackageCompileInput, PackageCompileResult, PackageConfigContract, PackageConfigFieldRule
from framework_packages.modules.runtime_support import compose_knowledge_base_surface_fragment
from framework_packages.static import StaticFrameworkPackage


def _required_field(path: str) -> PackageConfigFieldRule:
    return PackageConfigFieldRule(path=path, presence="required")


class KnowledgeBaseL1M0Package(StaticFrameworkPackage):
    FRAMEWORK_FILE = "framework/knowledge_base/L1-M0-知识库界面骨架模块.md"
    MODULE_ID = "knowledge_base.L1.M0"

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
            package_source_file=base.package_source_file,
            config_contract=base.config_contract,
            child_slots=base.child_slots,
            config_slice=base.config_slice,
            export=base.export,
            evidence=base.evidence,
            runtime_exports={"knowledge_base_surface_fragment": compose_knowledge_base_surface_fragment(payload)},
        )


__all__ = ["KnowledgeBaseL1M0Package"]
