from __future__ import annotations

import uuid
from collections import defaultdict
from typing import Any

from ..config import AppConfig
from ..models import DocumentRecord, FolderRecord, UserRecord, utc_now_iso
from ..storage import FolderRepository


class FolderTreeModule:
    def __init__(self, app_config: AppConfig, repository: FolderRepository) -> None:
        self.defaults = [item for item in app_config.section("l2_folder_defaults").get("folders", []) if isinstance(item, dict)]
        self.creation_config = app_config.section("l2_folder_creation")
        self.repository = repository

    def ensure_defaults(self) -> None:
        existing = {folder.folder_id for folder in self.repository.list_folders()}
        for item in self.defaults:
            folder_id = str(item.get("folder_id", "")).strip()
            if not folder_id or folder_id in existing:
                continue
            folder = FolderRecord(
                folder_id=folder_id,
                name=str(item.get("name", folder_id)),
                parent_id=item.get("parent_id"),
                system=bool(item.get("system", True)),
                created_by=str(item.get("created_by", "system")),
            )
            self.repository.save_folder(folder)
            existing.add(folder.folder_id)

    def list_folders(self) -> list[FolderRecord]:
        self.ensure_defaults()
        return self.repository.list_folders()

    def create_folder(self, name: str, parent_id: str | None, user: UserRecord) -> FolderRecord:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Folder name is required.")
        if len(normalized_name) > int(self.creation_config.get("max_name_length", 48)):
            raise ValueError("Folder name is too long.")
        if parent_id:
            parent = self.repository.get_folder(parent_id)
            if parent is None:
                raise ValueError("Parent folder does not exist.")
            if self._folder_depth(parent.folder_id) >= int(self.creation_config.get("max_folder_depth", 4)):
                raise ValueError("Folder depth exceeds configured limit.")
        folder = FolderRecord(
            folder_id=uuid.uuid4().hex,
            name=normalized_name,
            parent_id=parent_id,
            system=False,
            created_by=user.user_id,
            created_at=utc_now_iso(),
            updated_at=utc_now_iso(),
        )
        self.repository.save_folder(folder)
        return folder

    def build_tree(self, folders: list[FolderRecord], documents: list[DocumentRecord]) -> list[dict[str, Any]]:
        children_map: dict[str | None, list[FolderRecord]] = defaultdict(list)
        for folder in folders:
            children_map[folder.parent_id].append(folder)
        for items in children_map.values():
            items.sort(key=lambda folder: (not folder.system, folder.name.lower()))

        document_map: dict[str, list[DocumentRecord]] = defaultdict(list)
        for document in documents:
            document_map[document.folder_id].append(document)
        for items in document_map.values():
            items.sort(key=lambda document: document.created_at, reverse=True)

        def render(folder: FolderRecord) -> dict[str, Any]:
            return {
                "folder_id": folder.folder_id,
                "name": folder.name,
                "parent_id": folder.parent_id,
                "system": folder.system,
                "created_by": folder.created_by,
                "children": [render(child) for child in children_map.get(folder.folder_id, [])],
                "documents": [
                    {
                        "document_id": document.document_id,
                        "filename": document.original_filename,
                        "state": document.state,
                        "uploaded_at": document.created_at,
                        "folder_id": document.folder_id,
                    }
                    for document in document_map.get(folder.folder_id, [])
                ],
            }

        return [render(folder) for folder in children_map.get(None, [])]

    def default_uncategorized_id(self) -> str:
        for item in self.defaults:
            if str(item.get("name", "")) == "未分类":
                return str(item.get("folder_id", "uncategorized"))
        return "uncategorized"

    def _folder_depth(self, folder_id: str) -> int:
        depth = 0
        current = self.repository.get_folder(folder_id)
        while current is not None and current.parent_id is not None:
            depth += 1
            current = self.repository.get_folder(current.parent_id)
        return depth
