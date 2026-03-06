from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class AppConfig:
    def __init__(self, raw: dict[str, Any], config_path: Path) -> None:
        self.raw = raw
        self.config_path = config_path.resolve()
        self.project_root = self.config_path.parent.parent

    def section(self, name: str) -> dict[str, Any]:
        value = self.raw.get(name, {})
        if not isinstance(value, dict):
            raise ValueError(f"Config section {name!r} must be an object.")
        return value

    def resolve_project_path(self, value: str) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return (self.project_root / path).resolve()

    @property
    def host(self) -> str:
        return str(self.section("server").get("host", "127.0.0.1"))

    @property
    def port(self) -> int:
        return int(self.section("server").get("port", 8010))

    @property
    def runtime_dir(self) -> Path:
        return self.resolve_project_path(str(self.section("paths").get("runtime_dir", "runtime")))

    @property
    def uploads_dir(self) -> Path:
        return self.runtime_dir / str(self.section("paths").get("uploads_dir", "uploads"))

    @property
    def exports_dir(self) -> Path:
        return self.runtime_dir / str(self.section("paths").get("exports_dir", "exports"))

    @property
    def document_store_file(self) -> Path:
        return self.runtime_dir / str(self.section("paths").get("document_store_file", "documents.json"))

    @property
    def trace_store_file(self) -> Path:
        return self.runtime_dir / str(self.section("paths").get("trace_store_file", "traces.jsonl"))

    @property
    def folder_store_file(self) -> Path:
        return self.runtime_dir / str(self.section("paths").get("folder_store_file", "folders.json"))

    @property
    def session_store_file(self) -> Path:
        return self.runtime_dir / str(self.section("paths").get("session_store_file", "sessions.json"))

    @property
    def users_dir(self) -> Path:
        return self.runtime_dir / str(self.section("paths").get("users_dir", "users"))

    @property
    def web_dir(self) -> Path:
        return self.resolve_project_path(str(self.section("paths").get("web_dir", "web")))


def load_config(config_path: str | None = None) -> AppConfig:
    candidate = config_path or os.environ.get("DATA_STATION_PRJ_CONFIG")
    if candidate is None:
        candidate = str(Path(__file__).resolve().parents[1] / "config" / "default.json")
    path = Path(candidate)
    raw = json.loads(path.read_text(encoding="utf-8"))
    return AppConfig(raw, path)
