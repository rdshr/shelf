from framework_packages.static import StaticFrameworkPackage


class KnowledgeBaseL1M1Package(StaticFrameworkPackage):
    FRAMEWORK_FILE = "framework/knowledge_base/L1-M1-知识引用上下文编排模块.md"
    MODULE_ID = "knowledge_base.L1.M1"


__all__ = ["KnowledgeBaseL1M1Package"]
