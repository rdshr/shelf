from __future__ import annotations

from enum import Enum

from shelf_domain import MODULE_ROLE, Module


class StructureFamily(str, Enum):
    FRAME = "frame"
    SHELF = "shelf"


__all__ = ["Module", "MODULE_ROLE", "StructureFamily"]
