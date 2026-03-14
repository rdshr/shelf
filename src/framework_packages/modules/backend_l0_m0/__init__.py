from framework_packages.static import StaticFrameworkPackage


class BackendL0M0Package(StaticFrameworkPackage):
    FRAMEWORK_FILE = "framework/backend/L0-M0-文件资源与对话契约原子模块.md"
    MODULE_ID = "backend.L0.M0"


__all__ = ["BackendL0M0Package"]
