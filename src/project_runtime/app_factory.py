from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI

from project_runtime.knowledge_base import (
    DEFAULT_KNOWLEDGE_BASE_PROJECT_FILE,
    build_knowledge_base_runtime_app_from_spec,
)


PROJECT_FILE_ENV = "SHELF_PROJECT_FILE"
DEFAULT_PROJECT_FILE = DEFAULT_KNOWLEDGE_BASE_PROJECT_FILE


def build_project_app(project_file: str | Path | None = None) -> FastAPI:
    resolved_file = project_file or os.environ.get(PROJECT_FILE_ENV) or DEFAULT_PROJECT_FILE
    return build_knowledge_base_runtime_app_from_spec(resolved_file)


app = build_project_app()
