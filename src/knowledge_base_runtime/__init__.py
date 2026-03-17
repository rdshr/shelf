from __future__ import annotations

from importlib import import_module
from typing import Any


_EXPORTS = {
    "DEFAULT_PROJECT_FILE": ("project_runtime", "DEFAULT_PROJECT_FILE"),
    "build_project_runtime_app": ("project_runtime.runtime_app", "build_project_runtime_app"),
}

__all__ = sorted(_EXPORTS)


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(name)
    module_name, attr_name = _EXPORTS[name]
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
