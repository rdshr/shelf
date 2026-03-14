from framework_packages.static import StaticFrameworkPackage


class MessageQueueL1M0Package(StaticFrameworkPackage):
    FRAMEWORK_FILE = "framework/message_queue/L1-M0-消息队列标准模块.md"
    MODULE_ID = "message_queue.L1.M0"


__all__ = ["MessageQueueL1M0Package"]
