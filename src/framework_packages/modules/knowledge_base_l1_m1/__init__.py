from framework_packages.contract import PackageCompileInput, PackageCompileResult, PackageConfigContract, PackageConfigFieldRule
from framework_packages.modules.runtime_support import compose_knowledge_base_context_fragment
from framework_packages.static import StaticFrameworkPackage


def _required_field(path: str) -> PackageConfigFieldRule:
    return PackageConfigFieldRule(path=path, presence="required")


class KnowledgeBaseL1M1Package(StaticFrameworkPackage):
    FRAMEWORK_FILE = "framework/knowledge_base/L1-M1-知识引用上下文编排模块.md"
    MODULE_ID = "knowledge_base.L1.M1"

    def config_contract(self) -> PackageConfigContract:
        return PackageConfigContract(
            fields=(
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
            package_source_file=base.package_source_file,
            config_contract=base.config_contract,
            child_slots=base.child_slots,
            config_slice=base.config_slice,
            export=base.export,
            evidence=base.evidence,
            runtime_exports={"knowledge_base_context_fragment": compose_knowledge_base_context_fragment(payload)},
        )


__all__ = ["KnowledgeBaseL1M1Package"]
