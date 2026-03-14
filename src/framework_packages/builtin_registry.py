from __future__ import annotations

from .registry import FrameworkPackageRegistry
from .modules.backend_l0_m0 import BackendL0M0Package
from .modules.backend_l1_m0 import BackendL1M0Package
from .modules.backend_l2_m0 import BackendL2M0Package
from .modules.curtain_l0_m0 import CurtainL0M0Package
from .modules.curtain_l1_m0 import CurtainL1M0Package
from .modules.curtain_l2_m0 import CurtainL2M0Package
from .modules.frontend_l0_m0 import FrontendL0M0Package
from .modules.frontend_l0_m1 import FrontendL0M1Package
from .modules.frontend_l0_m2 import FrontendL0M2Package
from .modules.frontend_l1_m0 import FrontendL1M0Package
from .modules.frontend_l1_m1 import FrontendL1M1Package
from .modules.frontend_l1_m2 import FrontendL1M2Package
from .modules.frontend_l1_m3 import FrontendL1M3Package
from .modules.frontend_l1_m4 import FrontendL1M4Package
from .modules.frontend_l2_m0 import FrontendL2M0Package
from .modules.frontend_l2_m1 import FrontendL2M1Package
from .modules.frontend_l3_m0 import FrontendL3M0Package
from .modules.knowledge_base_l0_m0 import KnowledgeBaseL0M0Package
from .modules.knowledge_base_l0_m1 import KnowledgeBaseL0M1Package
from .modules.knowledge_base_l0_m2 import KnowledgeBaseL0M2Package
from .modules.knowledge_base_l1_m0 import KnowledgeBaseL1M0Package
from .modules.knowledge_base_l1_m1 import KnowledgeBaseL1M1Package
from .modules.knowledge_base_l2_m0 import KnowledgeBaseL2M0Package
from .modules.message_queue_l0_m0 import MessageQueueL0M0Package
from .modules.message_queue_l1_m0 import MessageQueueL1M0Package
from .modules.runtime_env_l0_m0 import RuntimeEnvL0M0Package
from .modules.shelf_l0_m0 import ShelfL0M0Package
from .modules.shelf_l1_m0 import ShelfL1M0Package
from .modules.shelf_l2_m0 import ShelfL2M0Package


def load_builtin_package_registry() -> FrameworkPackageRegistry:
    registry = FrameworkPackageRegistry()
    for entry_class in (
        BackendL0M0Package,
        BackendL1M0Package,
        BackendL2M0Package,
        CurtainL0M0Package,
        CurtainL1M0Package,
        CurtainL2M0Package,
        FrontendL0M0Package,
        FrontendL0M1Package,
        FrontendL0M2Package,
        FrontendL1M0Package,
        FrontendL1M1Package,
        FrontendL1M2Package,
        FrontendL1M3Package,
        FrontendL1M4Package,
        FrontendL2M0Package,
        FrontendL2M1Package,
        FrontendL3M0Package,
        KnowledgeBaseL0M0Package,
        KnowledgeBaseL0M1Package,
        KnowledgeBaseL0M2Package,
        KnowledgeBaseL1M0Package,
        KnowledgeBaseL1M1Package,
        KnowledgeBaseL2M0Package,
        MessageQueueL0M0Package,
        MessageQueueL1M0Package,
        RuntimeEnvL0M0Package,
        ShelfL0M0Package,
        ShelfL1M0Package,
        ShelfL2M0Package,
    ):
        registry.register(entry_class)
    return registry
