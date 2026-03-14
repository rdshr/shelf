from typing import TYPE_CHECKING

from .app import build_knowledge_base_runtime_app

if TYPE_CHECKING:
    from project_runtime.knowledge_base import DEFAULT_KNOWLEDGE_BASE_PROJECT_FILE
else:
    try:
        from project_runtime import knowledge_base as _knowledge_base
    except ModuleNotFoundError:  # pragma: no cover - compatibility for src.package imports
        from ..project_runtime import knowledge_base as _knowledge_base

    DEFAULT_KNOWLEDGE_BASE_PROJECT_FILE = _knowledge_base.DEFAULT_KNOWLEDGE_BASE_PROJECT_FILE

__all__ = ["DEFAULT_KNOWLEDGE_BASE_PROJECT_FILE", "build_knowledge_base_runtime_app"]
