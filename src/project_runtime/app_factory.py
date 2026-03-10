from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI

from project_runtime.template_registry import (
    get_default_project_template_registration,
    materialize_registered_project,
    resolve_project_template_registration,
)

PRODUCT_SPEC_FILE_ENV = "SHELF_PRODUCT_SPEC_FILE"
DEFAULT_PRODUCT_SPEC_FILE = get_default_project_template_registration().default_product_spec_file


def build_project_app(product_spec_file: str | Path | None = None) -> FastAPI:
    resolved_file = (
        product_spec_file
        or os.environ.get(PRODUCT_SPEC_FILE_ENV)
        or DEFAULT_PRODUCT_SPEC_FILE
    )
    project_config = materialize_registered_project(resolved_file)
    registration = resolve_project_template_registration(resolved_file)
    return registration.build_app(project_config)


app = build_project_app()
