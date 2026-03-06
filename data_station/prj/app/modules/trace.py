from __future__ import annotations

import uuid
from typing import Any

from ..config import AppConfig
from ..models import utc_now_iso
from ..storage import TraceRepository


class TraceEventIntakeModule:
    def __init__(self, app_config: AppConfig) -> None:
        self.required_fields = [str(item) for item in app_config.section("l2_trace_event_intake").get("required_event_fields", [])]

    def intake(self, event: dict[str, Any]) -> dict[str, Any]:
        missing = [name for name in self.required_fields if not event.get(name)]
        if missing:
            raise ValueError(f"Missing trace event fields: {', '.join(missing)}")
        return dict(event)


class TraceFieldNormalizationModule:
    def __init__(self, app_config: AppConfig) -> None:
        self.required_fields = [str(item) for item in app_config.section("l2_trace_field_normalization").get("required_normalized_fields", [])]

    def normalize(self, event: dict[str, Any]) -> dict[str, Any]:
        normalized = {
            "trace_id": uuid.uuid4().hex,
            "recorded_at": utc_now_iso(),
            **event,
        }
        for name in self.required_fields:
            normalized.setdefault(name, "")
        return normalized


class TraceRecordOutputModule:
    def __init__(self, repository: TraceRepository) -> None:
        self.repository = repository

    def write(self, record: dict[str, Any]) -> dict[str, Any]:
        self.repository.append(record)
        return {"trace_id": record["trace_id"]}


class TraceManagementModule:
    def __init__(self, app_config: AppConfig, repository: TraceRepository) -> None:
        self.enabled = bool(app_config.section("l1_trace_management").get("enabled", True))
        self.intake = TraceEventIntakeModule(app_config)
        self.normalize = TraceFieldNormalizationModule(app_config)
        self.output = TraceRecordOutputModule(repository)

    def record(self, event: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled:
            return {"trace_id": "disabled"}
        accepted = self.intake.intake(event)
        normalized = self.normalize.normalize(accepted)
        return self.output.write(normalized)
