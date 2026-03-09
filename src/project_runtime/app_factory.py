from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from fastapi import FastAPI

from project_runtime.knowledge_base import (
    DEFAULT_KNOWLEDGE_BASE_PROJECT_FILE,
    SUPPORTED_PROJECT_TEMPLATE,
    materialize_knowledge_base_project,
)

PROJECT_FILE_ENV = "SHELF_PROJECT_FILE"

if TYPE_CHECKING:
    from project_runtime.knowledge_base import KnowledgeBaseProject

ProjectAppBuilder = Callable[["KnowledgeBaseProject"], FastAPI]


def _build_knowledge_base_project_app(project_config: "KnowledgeBaseProject") -> FastAPI:
    from knowledge_base_demo.app import build_knowledge_base_demo_app

    return build_knowledge_base_demo_app(project_config)


TEMPLATE_APP_BUILDERS: dict[str, ProjectAppBuilder] = {
    SUPPORTED_PROJECT_TEMPLATE: _build_knowledge_base_project_app,
}


def build_project_app(project_file: str | Path | None = None) -> FastAPI:
    resolved_file = project_file or os.environ.get(PROJECT_FILE_ENV) or DEFAULT_KNOWLEDGE_BASE_PROJECT_FILE
    project_config = materialize_knowledge_base_project(resolved_file)
    builder = TEMPLATE_APP_BUILDERS.get(project_config.metadata.template)
    if builder is None:
        raise ValueError(f"unsupported project template: {project_config.metadata.template}")
    return builder(project_config)


app = build_project_app()
