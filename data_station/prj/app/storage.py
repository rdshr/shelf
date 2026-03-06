from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import DocumentRecord, FolderRecord, SessionRecord, UserRecord


class DocumentRepository:
    def __init__(self, store_file: Path) -> None:
        self.store_file = store_file
        self._lock = threading.Lock()
        self._ensure_store()

    def _ensure_store(self) -> None:
        self.store_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.store_file.exists():
            self.store_file.write_text(json.dumps({"documents": []}, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load(self) -> dict[str, Any]:
        self._ensure_store()
        return json.loads(self.store_file.read_text(encoding="utf-8"))

    def _save(self, payload: dict[str, Any]) -> None:
        self.store_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def list_documents(self) -> list[DocumentRecord]:
        with self._lock:
            payload = self._load()
        return [DocumentRecord.from_dict(item) for item in payload.get("documents", [])]

    def get_document(self, document_id: str) -> DocumentRecord | None:
        for document in self.list_documents():
            if document.document_id == document_id:
                return document
        return None

    def find_by_request_id(self, request_id: str) -> DocumentRecord | None:
        for document in self.list_documents():
            if document.request_id == request_id:
                return document
        return None

    def save_document(self, document: DocumentRecord) -> None:
        with self._lock:
            payload = self._load()
            documents = payload.setdefault("documents", [])
            for index, item in enumerate(documents):
                if item["document_id"] == document.document_id:
                    documents[index] = document.to_dict()
                    break
            else:
                documents.append(document.to_dict())
            self._save(payload)


class TraceRepository:
    def __init__(self, trace_file: Path) -> None:
        self.trace_file = trace_file
        self._lock = threading.Lock()
        self._ensure_store()

    def _ensure_store(self) -> None:
        self.trace_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.trace_file.exists():
            self.trace_file.write_text("", encoding="utf-8")

    def append(self, payload: dict[str, Any]) -> None:
        with self._lock:
            self._ensure_store()
            with self.trace_file.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


class ExportRepository:
    def __init__(self, export_dir: Path) -> None:
        self.export_dir = export_dir
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def write_export(self, filename: str, payload: dict[str, Any]) -> Path:
        self._ensure_dir()
        target = self.export_dir / filename
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return target


class FolderRepository:
    def __init__(self, store_file: Path) -> None:
        self.store_file = store_file
        self._lock = threading.Lock()
        self._ensure_store()

    def _ensure_store(self) -> None:
        self.store_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.store_file.exists():
            self.store_file.write_text(json.dumps({"folders": []}, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load(self) -> dict[str, Any]:
        self._ensure_store()
        return json.loads(self.store_file.read_text(encoding="utf-8"))

    def _save(self, payload: dict[str, Any]) -> None:
        self.store_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def list_folders(self) -> list[FolderRecord]:
        with self._lock:
            payload = self._load()
        return [FolderRecord.from_dict(item) for item in payload.get("folders", [])]

    def get_folder(self, folder_id: str) -> FolderRecord | None:
        for folder in self.list_folders():
            if folder.folder_id == folder_id:
                return folder
        return None

    def save_folder(self, folder: FolderRecord) -> None:
        with self._lock:
            payload = self._load()
            folders = payload.setdefault("folders", [])
            for index, item in enumerate(folders):
                if item["folder_id"] == folder.folder_id:
                    folders[index] = folder.to_dict()
                    break
            else:
                folders.append(folder.to_dict())
            self._save(payload)


class SessionRepository:
    def __init__(self, store_file: Path) -> None:
        self.store_file = store_file
        self._lock = threading.Lock()
        self._ensure_store()

    def _ensure_store(self) -> None:
        self.store_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.store_file.exists():
            self.store_file.write_text(json.dumps({"sessions": []}, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load(self) -> dict[str, Any]:
        self._ensure_store()
        return json.loads(self.store_file.read_text(encoding="utf-8"))

    def _save(self, payload: dict[str, Any]) -> None:
        self.store_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def list_sessions(self) -> list[SessionRecord]:
        with self._lock:
            payload = self._load()
        return [SessionRecord.from_dict(item) for item in payload.get("sessions", [])]

    def get_session(self, token: str) -> SessionRecord | None:
        self.cleanup_expired()
        for session in self.list_sessions():
            if session.token == token:
                return session
        return None

    def save_session(self, session: SessionRecord) -> None:
        with self._lock:
            payload = self._load()
            sessions = payload.setdefault("sessions", [])
            for index, item in enumerate(sessions):
                if item["token"] == session.token:
                    sessions[index] = session.to_dict()
                    break
            else:
                sessions.append(session.to_dict())
            self._save(payload)

    def delete_session(self, token: str) -> None:
        with self._lock:
            payload = self._load()
            sessions = [item for item in payload.get("sessions", []) if item.get("token") != token]
            payload["sessions"] = sessions
            self._save(payload)

    def cleanup_expired(self) -> None:
        with self._lock:
            payload = self._load()
            now = datetime.now(timezone.utc)
            sessions = []
            for item in payload.get("sessions", []):
                try:
                    expires_at = datetime.fromisoformat(item["expires_at"])
                except (KeyError, ValueError):
                    continue
                if expires_at > now:
                    sessions.append(item)
            payload["sessions"] = sessions
            self._save(payload)


class UserRepository:
    def __init__(self, users_dir: Path) -> None:
        self.users_dir = users_dir
        self._lock = threading.Lock()
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        self.users_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, user_id: str) -> Path:
        return self.users_dir / f"{user_id}.json"

    def list_users(self) -> list[UserRecord]:
        self._ensure_dir()
        items: list[UserRecord] = []
        for path in sorted(self.users_dir.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            items.append(UserRecord.from_dict(payload))
        return items

    def get_user(self, user_id: str) -> UserRecord | None:
        target = self._path_for(user_id)
        if not target.exists():
            return None
        payload = json.loads(target.read_text(encoding="utf-8"))
        return UserRecord.from_dict(payload)

    def get_by_email(self, email: str) -> UserRecord | None:
        normalized = email.strip().lower()
        for user in self.list_users():
            if user.email.strip().lower() == normalized:
                return user
        return None

    def save_user(self, user: UserRecord) -> None:
        with self._lock:
            self._ensure_dir()
            self._path_for(user.user_id).write_text(
                json.dumps(user.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
