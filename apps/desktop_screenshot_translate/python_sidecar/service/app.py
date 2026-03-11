from __future__ import annotations

from functools import lru_cache
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field
import uvicorn

from apps.desktop_screenshot_translate.python_sidecar.service.config_loader import load_runtime_bundle


class CaptureSelection(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    display_id: str = Field(alias="displayId")
    x: int
    y: int
    width: int
    height: int
    scale_factor: float = Field(alias="scaleFactor")


class TranslateStubRequest(BaseModel):
    selection: CaptureSelection
    image_ref: str | None = None


@lru_cache(maxsize=1)
def get_bundle() -> dict[str, Any]:
    loaded = load_runtime_bundle()
    return {
        "product_spec": loaded.project_spec,
        "implementation_config": loaded.implementation_config,
        "runtime_bundle": loaded.runtime_bundle,
        "generated_dir": str(loaded.generated_dir),
    }


app = FastAPI(title="AiTrans Screenshot Translate Sidecar", version="0.1.0")


@app.get("/health")
def health() -> dict[str, Any]:
    bundle = get_bundle()
    product = bundle["product_spec"]["project"]
    return {
        "status": "ok",
        "project_id": product["project_id"],
        "display_name": product["display_name"],
    }


@app.get("/api/config")
def config() -> dict[str, Any]:
    bundle = get_bundle()
    return {
        "project": bundle["product_spec"]["project"],
        "desktop": bundle["product_spec"]["desktop"],
        "pipeline": bundle["product_spec"]["pipeline"],
        "providers": bundle["implementation_config"]["providers"],
        "generated_dir": bundle["generated_dir"],
    }


@app.post("/api/translate/stub")
def translate_stub(request: TranslateStubRequest) -> dict[str, Any]:
    bundle = get_bundle()
    target_language = bundle["product_spec"]["pipeline"]["target_language"]
    return {
        "stage_status": "stub_ready",
        "source_text": (
            f"Stub OCR: captured {request.selection.width}x{request.selection.height} "
            f"region on display {request.selection.display_id}."
        ),
        "translated_text": f"Stub Translation ({target_language}): Windows MVP 主链已接入 sidecar 占位实现。",
        "error_origin": None,
        "selection": request.model_dump(by_alias=True),
    }


if __name__ == "__main__":
    uvicorn.run(
        "apps.desktop_screenshot_translate.python_sidecar.service.app:app",
        host="127.0.0.1",
        port=8765,
        reload=False,
    )
