from framework_packages.static import StaticFrameworkPackage


class MessageQueueL0M0Package(StaticFrameworkPackage):
    FRAMEWORK_FILE = "framework/message_queue/L0-M0-消息队列抽象结构模块.md"
    MODULE_ID = "message_queue.L0.M0"


__all__ = ["MessageQueueL0M0Package"]
