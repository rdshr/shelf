from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI

from project_runtime.compiler import DEFAULT_PROJECT_FILE
from project_runtime.runtime_app import build_project_app_from_project_file


PROJECT_FILE_ENV = "SHELF_PROJECT_FILE"


def build_project_app(project_file: str | Path | None = None) -> FastAPI:
    resolved_file = project_file
    if resolved_file is None:
        resolved_file = os.environ.get(PROJECT_FILE_ENV) or DEFAULT_PROJECT_FILE
    return build_project_app_from_project_file(resolved_file)


app = build_project_app()
