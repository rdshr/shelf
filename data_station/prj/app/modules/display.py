from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config import AppConfig
from ..models import DocumentRecord
from ..storage import ExportRepository


class ListRetrievalModule:
    def __init__(self, app_config: AppConfig) -> None:
        self.page_size = int(app_config.section("l1_display_retrieval").get("default_page_size", 20))
        self.max_page_size = int(app_config.section("l1_display_retrieval").get("max_page_size", 100))
        self.default_sort = str(app_config.section("l2_list_retrieval").get("default_sort", "created_at_desc"))

    def list_documents(self, documents: list[DocumentRecord], query: str, state: str, page: int, page_size: int | None, folder_id: str | None = None) -> dict[str, Any]:
        normalized_query = query.strip().lower()
        filtered = []
        for document in documents:
            if folder_id and document.folder_id != folder_id:
                continue
            if state and document.state != state:
                continue
            if normalized_query and normalized_query not in document.original_filename.lower():
                continue
            filtered.append(document)
        if self.default_sort == "created_at_desc":
            filtered.sort(key=lambda item: item.created_at, reverse=True)
        page_size = min(page_size or self.page_size, self.max_page_size)
        page = max(page, 1)
        start = (page - 1) * page_size
        end = start + page_size
        items = [self._list_item(document) for document in filtered[start:end]]
        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": len(filtered),
        }

    def _list_item(self, document: DocumentRecord) -> dict[str, Any]:
        return {
            "document_id": document.document_id,
            "filename": document.original_filename,
            "state": document.state,
            "version": document.version,
            "uploaded_by": document.metadata.get("uploaded_by"),
            "document_type": document.metadata.get("document_type"),
            "folder_id": document.folder_id,
            "created_at": document.created_at,
        }


class DetailDisplayModule:
    def __init__(self, app_config: AppConfig) -> None:
        self.include_internal_paths = bool(app_config.section("l2_detail_display").get("include_internal_paths", True))

    def detail(self, document: DocumentRecord) -> dict[str, Any]:
        payload = document.to_dict()
        if not self.include_internal_paths:
            payload.pop("stored_path", None)
        return payload


class ReuseExportModule:
    def __init__(self, app_config: AppConfig, export_repository: ExportRepository) -> None:
        self.config = app_config.section("l2_reuse_export")
        self.export_repository = export_repository

    def export(self, document: DocumentRecord) -> tuple[Path, dict[str, Any]]:
        pattern = str(self.config.get("export_filename_pattern", "{document_id}.json"))
        filename = pattern.format(document_id=document.document_id)
        payload = {
            "document": document.to_dict(),
            "exported_at": document.updated_at,
            "export_format": self.config.get("export_format", "json"),
        }
        target = self.export_repository.write_export(filename, payload)
        return target, payload


class DisplayRetrievalModule:
    def __init__(self, app_config: AppConfig, export_repository: ExportRepository) -> None:
        self.listing = ListRetrievalModule(app_config)
        self.detail_display = DetailDisplayModule(app_config)
        self.reuse_export = ReuseExportModule(app_config, export_repository)
