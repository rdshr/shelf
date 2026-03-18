from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any


_EXPORTS = {
    "DEFAULT_PROJECT_FILE": ("project_runtime", "DEFAULT_PROJECT_FILE"),
    "build_project_runtime_app": ("project_runtime.runtime_app", "build_project_runtime_app"),
}

__all__ = (
    "DEFAULT_PROJECT_FILE",
    "build_project_runtime_app",
)

if TYPE_CHECKING:
    from project_runtime import DEFAULT_PROJECT_FILE as DEFAULT_PROJECT_FILE
    from project_runtime.runtime_app import build_project_runtime_app as build_project_runtime_app


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(name)
    module_name, attr_name = _EXPORTS[name]
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
