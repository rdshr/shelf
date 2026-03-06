from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ..config import AppConfig
from ..models import DocumentRecord, utc_now_iso


class ProcessingInputPreparationModule:
    def __init__(self, app_config: AppConfig) -> None:
        self.allowed_source_states = [str(item) for item in app_config.section("l2_processing_input_preparation").get("allowed_source_states", ["accepted"])]

    def prepare(self, document: DocumentRecord) -> tuple[bool, str]:
        if document.state not in self.allowed_source_states:
            return False, f"Document state {document.state} is not allowed for processing."
        return True, "processing input prepared"


class StructuredProcessingServiceModule:
    def __init__(self, app_config: AppConfig) -> None:
        self.config = app_config.section("l2_structured_processing_service")

    def process(self, document: DocumentRecord) -> dict[str, Any]:
        file_path = Path(document.stored_path)
        content = file_path.read_bytes()
        preview_bytes = int(self.config.get("preview_bytes", 96))
        charset = str(self.config.get("text_decode_charset", "utf-8"))
        preview = content[:preview_bytes].decode(charset, errors="ignore").strip()
        words = [word for word in re.split(r"[^A-Za-z0-9\u4e00-\u9fff]+", document.original_filename) if word]
        keywords = words[: int(self.config.get("keyword_limit", 8))]
        return {
            "processed_at": utc_now_iso(),
            "summary": {
                "filename": document.original_filename,
                "size_bytes": document.size_bytes,
                "mime_type": document.mime_type,
                "preview": preview,
                "keywords": keywords,
                "sha256": document.sha256,
            },
        }


class ReviewWritebackModule:
    def __init__(self, app_config: AppConfig) -> None:
        self.config = app_config.section("l2_review_writeback")
        self.allowed_results = [str(item) for item in self.config.get("allowed_review_results", ["approved", "rejected"])]

    def apply(self, document: DocumentRecord, review_payload: dict[str, Any]) -> dict[str, Any]:
        decision = str(review_payload.get("decision", "")).lower()
        if decision not in self.allowed_results:
            raise ValueError("Review decision is invalid.")
        return {
            "decision": decision,
            "reviewer": str(review_payload.get("reviewer") or document.metadata.get("uploaded_by", "reviewer")),
            "comment": str(review_payload.get("comment") or self.config.get("default_review_comment", "manual review completed")),
            "reviewed_at": utc_now_iso(),
        }


class ProcessingReviewModule:
    def __init__(self, app_config: AppConfig) -> None:
        self.config = app_config.section("l1_processing_review")
        self.input_preparation = ProcessingInputPreparationModule(app_config)
        self.processing = StructuredProcessingServiceModule(app_config)
        self.review_writeback = ReviewWritebackModule(app_config)

    def process_document(self, document: DocumentRecord) -> tuple[bool, str, dict[str, Any] | None, str]:
        ok, message = self.input_preparation.prepare(document)
        if not ok:
            return False, message, None, document.state
        processing_result = self.processing.process(document)
        target_state = str(self.config.get("processing_target_state", "processed"))
        return True, "document processed", processing_result, target_state

    def review_document(self, document: DocumentRecord, review_payload: dict[str, Any]) -> tuple[dict[str, Any], str]:
        result = self.review_writeback.apply(document, review_payload)
        decision = result["decision"]
        if decision == "approved":
            target_state = str(self.config.get("review_approved_state", "reviewed"))
        else:
            target_state = str(self.config.get("review_rejected_state", "review_rejected"))
        return result, target_state
