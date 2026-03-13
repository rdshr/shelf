from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from document_chunking_runtime.pipeline import run_document_chunking_pipeline, run_document_chunking_pipeline_on_file


class ProcessTextRequest(BaseModel):
    document_name: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)


class ProcessFileRequest(BaseModel):
    input_file: str = Field(..., min_length=1)


def build_document_chunking_app(project: Any) -> FastAPI:
    app = FastAPI(
        title=project.metadata.display_name,
        description=project.metadata.description,
        version=project.metadata.version,
    )

    api_prefix = project.implementation.runtime.api_prefix.rstrip("/")

    @app.get(project.implementation.evidence.product_spec_endpoint)
    def get_product_spec() -> dict[str, Any]:
        return project.public_summary()

    @app.post(project.implementation.evidence.process_text_endpoint)
    def process_text(request: ProcessTextRequest) -> dict[str, Any]:
        result = run_document_chunking_pipeline(
            document_name=request.document_name,
            text=request.text,
            document_format=project.product.output.document_format_value,
            heading_pattern=project.implementation.pipeline.heading_pattern,
            max_block_chars=project.implementation.pipeline.max_block_chars,
            max_chunk_items=project.product.validation.max_chunk_items,
        )
        return result.to_dict()

    @app.post(project.implementation.evidence.process_file_endpoint)
    def process_file(request: ProcessFileRequest) -> dict[str, Any]:
        resolved_path = Path(request.input_file)
        if not resolved_path.is_absolute():
            resolved_path = (Path(project.repo_root) / resolved_path).resolve()
        if not resolved_path.exists():
            raise HTTPException(status_code=404, detail=f"input file not found: {resolved_path}")
        result = run_document_chunking_pipeline_on_file(
            resolved_path,
            document_format=project.product.output.document_format_value,
            heading_pattern=project.implementation.pipeline.heading_pattern,
            max_block_chars=project.implementation.pipeline.max_block_chars,
            max_chunk_items=project.product.validation.max_chunk_items,
        )
        return result.to_dict()

    @app.get(f"{api_prefix}/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
