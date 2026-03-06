from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from .config import AppConfig
from .models import DocumentRecord, ModuleResult, SessionRecord, UserRecord, utc_now_iso
from .modules.authentication import AuthenticationModule
from .modules.authorization import AuthorizationGovernanceModule
from .modules.display import DisplayRetrievalModule
from .modules.folders import FolderTreeModule
from .modules.processing_review import ProcessingReviewModule
from .modules.state import StateManagementModule
from .modules.trace import TraceManagementModule
from .modules.upload import UploadIngressModule
from .storage import DocumentRepository, ExportRepository, FolderRepository, SessionRepository, TraceRepository, UserRepository


class DataStationService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.document_repository = DocumentRepository(config.document_store_file)
        self.trace_repository = TraceRepository(config.trace_store_file)
        self.export_repository = ExportRepository(config.exports_dir)
        self.folder_repository = FolderRepository(config.folder_store_file)
        self.session_repository = SessionRepository(config.session_store_file)
        self.user_repository = UserRepository(config.users_dir)
        self.upload = UploadIngressModule(config)
        self.state = StateManagementModule(config)
        self.trace = TraceManagementModule(config, self.trace_repository)
        self.authorization = AuthorizationGovernanceModule(config)
        self.authentication = AuthenticationModule(config, self.session_repository, self.user_repository)
        self.folders = FolderTreeModule(config, self.folder_repository)
        self.processing_review = ProcessingReviewModule(config)
        self.display = DisplayRetrievalModule(config, self.export_repository)
        self.folders.ensure_defaults()

    def frontend_bootstrap(self, user: UserRecord | None = None) -> dict[str, Any]:
        review_config = self.config.section("l2_review_writeback")
        display_config = self.config.section("l1_display_retrieval")
        auth_config = self.config.section("l1_authentication")
        registration_config = self.config.section("l2_registration_policy")
        folder_ui = self.config.section("l1_folder_tree")
        return {
            "upload": self.upload.public_config(),
            "server": {
                "origin": self.config.section("server").get("public_origin", f"http://{self.config.host}:{self.config.port}"),
            },
            "review": {
                "allowedDecisions": [str(item) for item in review_config.get("allowed_review_results", ["approved", "rejected"])],
            },
            "display": {
                "defaultPageSize": int(display_config.get("default_page_size", 20)),
                "maxPageSize": int(display_config.get("max_page_size", 100)),
            },
            "auth": {
                "sessionCookie": str(auth_config.get("session_cookie_name", "data_station_session")),
                "loginTitle": str(auth_config.get("login_title", "Data Station")),
                "currentUser": user.to_public_dict() if user is not None else None,
                "registrationEnabled": bool(registration_config.get("enabled", True)),
                "minimumPasswordLength": int(registration_config.get("minimum_password_length", 8)),
                "assignableRoles": [str(item) for item in registration_config.get("assignable_roles", ["viewer", "engineer", "root"])],
            },
            "folders": {
                "collapsedByDefault": bool(folder_ui.get("collapsed_by_default", True)),
                "menuActions": [str(item) for item in folder_ui.get("context_menu_actions", ["移动", "清洗", "删除", "审核", "提交"])],
            },
        }

    def current_user(self, token: str | None) -> tuple[UserRecord | None, SessionRecord | None]:
        return self.authentication.current_user(token)

    def login(self, email: str, password: str) -> tuple[ModuleResult, SessionRecord | None, dict[str, Any] | None]:
        user, session, message = self.authentication.login(email, password)
        if user is None or session is None:
            return ModuleResult(False, 401, {"ok": False, "message": message}), None, None
        self._record_trace("auth.login", user.user_id, "session", session.token, "accepted", "login_succeeded", 0)
        return (
            ModuleResult(
                True,
                200,
                {
                    "ok": True,
                    "user": user.to_public_dict(),
                    "bootstrap": self.frontend_bootstrap(user),
                },
            ),
            session,
            self.authentication.sessions.cookie_settings(),
        )

    def register(self, email: str, password: str, username: str, duties: list[str]) -> ModuleResult:
        if not bool(self.config.section("l2_registration_policy").get("enabled", True)):
            return ModuleResult(False, 403, {"ok": False, "message": "Registration is disabled."})
        user, message = self.authentication.register(email, password, username, duties)
        if user is None:
            return ModuleResult(False, 400, {"ok": False, "message": message})
        self._record_trace("auth.register", user.user_id, "user_directory", user.user_id, "pending", "registration_submitted", 0)
        return ModuleResult(True, 201, {"ok": True, "message": "Registration submitted for root approval.", "user": user.to_public_dict()})

    def logout(self, token: str | None) -> ModuleResult:
        user, session = self.current_user(token)
        if session is not None:
            self.authentication.logout(session.token)
            if user is not None:
                self._record_trace("auth.logout", user.user_id, "session", session.token, "accepted", "logout_succeeded", 0)
        return ModuleResult(True, 200, {"ok": True})

    def session_state(self, token: str | None) -> ModuleResult:
        user, session = self.current_user(token)
        if user is None or session is None:
            return ModuleResult(False, 401, {"ok": False, "message": "Authentication required."})
        return ModuleResult(True, 200, {"ok": True, "user": user.to_public_dict(), "bootstrap": self.frontend_bootstrap(user)})

    def list_users(self, root_user: UserRecord) -> ModuleResult:
        auth_error = self._authorize(root_user, "admin.user.view", "user_directory", {"scope": "internal"})
        if auth_error is not None:
            return auth_error
        users = [item.to_public_dict() for item in self.authentication.list_users()]
        users.sort(key=lambda item: (item.get("status") != "pending", item.get("email", "")))
        return ModuleResult(True, 200, {"ok": True, "users": users})

    def approve_user(self, root_user: UserRecord, user_id: str) -> ModuleResult:
        auth_error = self._authorize(root_user, "admin.user.approve", "user_directory", {"scope": "internal", "user_id": user_id})
        if auth_error is not None:
            return auth_error
        user, message = self.authentication.approve_user(root_user, user_id)
        if user is None:
            return ModuleResult(False, 404, {"ok": False, "message": message})
        self._record_trace("user.approved", root_user.user_id, user.user_id, user.user_id, "approved", "root_approved", 0)
        return ModuleResult(True, 200, {"ok": True, "user": user.to_public_dict()})

    def update_user(self, root_user: UserRecord, user_id: str, payload: dict[str, Any]) -> ModuleResult:
        auth_error = self._authorize(root_user, "admin.user.update", "user_directory", {"scope": "internal", "user_id": user_id})
        if auth_error is not None:
            return auth_error
        user, message = self.authentication.update_user(root_user, user_id, payload)
        if user is None:
            status_code = 404 if message == "User not found." else 400
            return ModuleResult(False, status_code, {"ok": False, "message": message})
        self._record_trace("user.updated", root_user.user_id, user.user_id, user.user_id, user.role, "root_updated", 0)
        return ModuleResult(True, 200, {"ok": True, "user": user.to_public_dict()})

    def _authorize(self, user: UserRecord, action: str, resource: str, context: dict[str, Any]) -> ModuleResult | None:
        decision = self.authorization.authorize(user.user_id, user.role, action, resource, context)
        if decision.allowed:
            return None
        return ModuleResult(False, 403, {"ok": False, "reason_code": decision.reason_code, "message": decision.message})

    def _record_trace(self, event: str, subject: str, resource: str, request_id: str, result: str, reason: str, version: int) -> None:
        self.trace.record(
            {
                "event": event,
                "subject": subject,
                "resource": resource,
                "request_id": request_id,
                "result": result,
                "reason": reason,
                "version": version,
            }
        )

    def list_folder_tree(self, user: UserRecord) -> ModuleResult:
        auth_error = self._authorize(user, "document.view", "document_collection", {"scope": "internal"})
        if auth_error is not None:
            return auth_error
        folders = self.folders.list_folders()
        documents = self.document_repository.list_documents()
        tree = self.folders.build_tree(folders, documents)
        return ModuleResult(True, 200, {"ok": True, "folders": tree, "selected_folder_id": self.folders.default_uncategorized_id()})

    def create_folder(self, user: UserRecord, name: str, parent_id: str | None) -> ModuleResult:
        auth_error = self._authorize(user, "folder.create", "folder_tree", {"scope": "internal"})
        if auth_error is not None:
            return auth_error
        try:
            folder = self.folders.create_folder(name, parent_id, user)
        except ValueError as exc:
            return ModuleResult(False, 400, {"ok": False, "message": str(exc)})
        self._record_trace("folder.created", user.user_id, folder.folder_id, folder.folder_id, "accepted", "folder_created", 0)
        return ModuleResult(True, 201, {"ok": True, "folder": folder.to_dict()})

    def upload_document(self, path: str, method: str, headers: dict[str, str], body: bytes, user: UserRecord) -> ModuleResult:
        admission = self.upload.backend.admit_request(path, method, headers)
        if not admission.ok:
            return admission
        context = admission.payload["context"]
        header_metadata = context["metadata"]
        metadata = {
            **header_metadata,
            "uploaded_by": user.username,
            "uploaded_by_email": user.email,
            "uploaded_by_user_id": user.user_id,
            "actor_role": user.role,
            "duties": user.duties,
        }
        auth_error = self._authorize(user, "upload.create", "manual_document", {"scope": "internal", "path": path})
        if auth_error is not None:
            self._record_trace("upload.denied", user.user_id, "manual_document", metadata.get("request_id", "unknown"), "denied", auth_error.payload["reason_code"], 0)
            return auth_error
        existing = self.document_repository.find_by_request_id(metadata["request_id"])
        duplicate, existing_document = self.state.register_initial(
            DocumentRecord(
                document_id="placeholder",
                request_id=metadata["request_id"],
                original_filename=context["filename"],
                stored_filename="",
                stored_path="",
                mime_type=context["mime_type"],
                extension=Path(context["filename"]).suffix.lower(),
                size_bytes=context["content_length"],
                sha256="",
                metadata=metadata,
                state="",
                version=0,
                folder_id=self.folders.default_uncategorized_id(),
            ),
            existing,
        )
        if duplicate:
            document = existing_document.to_dict()
            self._record_trace("upload.duplicate", user.user_id, existing_document.document_id, metadata["request_id"], "accepted", "duplicate_request", existing_document.version)
            return self.upload.backend.build_success(document, True)
        ingest = self.upload.backend.ingest(body, {**context, "metadata": metadata})
        if not ingest.ok:
            self._record_trace("upload.rejected", user.user_id, "manual_document", metadata["request_id"], "rejected", ingest.payload["reason_code"], 0)
            return ingest
        payload = ingest.payload["payload"]
        document = DocumentRecord(
            document_id=uuid.uuid4().hex,
            request_id=metadata["request_id"],
            original_filename=payload["filename"],
            stored_filename=payload["stored_filename"],
            stored_path=payload["stored_path"],
            mime_type=payload["mime_type"],
            extension=payload["extension"],
            size_bytes=payload["size_bytes"],
            sha256=payload["sha256"],
            metadata=metadata,
            state="",
            version=0,
            folder_id=self.folders.default_uncategorized_id(),
        )
        _, document = self.state.register_initial(document, None)
        document.updated_at = utc_now_iso()
        self.document_repository.save_document(document)
        self._record_trace("upload.accepted", user.user_id, document.document_id, metadata["request_id"], document.state, "upload_saved", document.version)
        return self.upload.backend.build_success(document.to_dict(), False)

    def list_documents(self, user: UserRecord, query: str, state: str, page: int, page_size: int | None, folder_id: str | None = None) -> ModuleResult:
        auth_error = self._authorize(user, "document.view", "document_collection", {"scope": "internal"})
        if auth_error is not None:
            return auth_error
        result = self.display.listing.list_documents(self.document_repository.list_documents(), query, state, page, page_size, folder_id)
        return ModuleResult(True, 200, {"ok": True, **result})

    def get_document_detail(self, user: UserRecord, document_id: str) -> ModuleResult:
        auth_error = self._authorize(user, "document.view", "manual_document", {"scope": "internal", "document_id": document_id})
        if auth_error is not None:
            return auth_error
        document = self.document_repository.get_document(document_id)
        if document is None:
            return ModuleResult(False, 404, {"ok": False, "message": "Document not found."})
        payload = self.display.detail_display.detail(document)
        folder = self.folder_repository.get_folder(document.folder_id)
        payload["folder_name"] = folder.name if folder is not None else document.folder_id
        return ModuleResult(True, 200, {"ok": True, "document": payload})

    def process_document(self, user: UserRecord, document_id: str) -> ModuleResult:
        auth_error = self._authorize(user, "process.execute", "manual_document", {"scope": "internal", "document_id": document_id})
        if auth_error is not None:
            return auth_error
        document = self.document_repository.get_document(document_id)
        if document is None:
            return ModuleResult(False, 404, {"ok": False, "message": "Document not found."})
        ok, message, processing_result, target_state = self.processing_review.process_document(document)
        if not ok:
            return ModuleResult(False, 400, {"ok": False, "message": message})
        transitioned, transition_message = self.state.transition(document, target_state)
        if not transitioned:
            return ModuleResult(False, 409, {"ok": False, "message": transition_message})
        document.processing = processing_result or {}
        document.updated_at = utc_now_iso()
        self.document_repository.save_document(document)
        self._record_trace("document.processed", user.user_id, document.document_id, document.request_id, document.state, "processing_completed", document.version)
        return ModuleResult(True, 200, {"ok": True, "message": message, "document": document.to_dict()})

    def review_document(self, user: UserRecord, document_id: str, payload: dict[str, Any]) -> ModuleResult:
        auth_error = self._authorize(user, "review.submit", "manual_document", {"scope": "internal", "document_id": document_id})
        if auth_error is not None:
            return auth_error
        document = self.document_repository.get_document(document_id)
        if document is None:
            return ModuleResult(False, 404, {"ok": False, "message": "Document not found."})
        try:
            review_result, target_state = self.processing_review.review_document(document, payload)
        except ValueError as exc:
            return ModuleResult(False, 400, {"ok": False, "message": str(exc)})
        transitioned, transition_message = self.state.transition(document, target_state)
        if not transitioned:
            return ModuleResult(False, 409, {"ok": False, "message": transition_message})
        document.review = review_result
        document.updated_at = utc_now_iso()
        self.document_repository.save_document(document)
        self._record_trace("document.reviewed", user.user_id, document.document_id, document.request_id, document.state, review_result["decision"], document.version)
        return ModuleResult(True, 200, {"ok": True, "document": document.to_dict()})

    def export_document(self, user: UserRecord, document_id: str) -> tuple[ModuleResult, bytes | None, str | None]:
        auth_error = self._authorize(user, "document.export", "manual_document", {"scope": "internal", "document_id": document_id})
        if auth_error is not None:
            return auth_error, None, None
        document = self.document_repository.get_document(document_id)
        if document is None:
            return ModuleResult(False, 404, {"ok": False, "message": "Document not found."}), None, None
        target, export_payload = self.display.reuse_export.export(document)
        document.exports.append({"path": str(target), "exported_at": utc_now_iso()})
        document.updated_at = utc_now_iso()
        self.document_repository.save_document(document)
        self._record_trace("document.exported", user.user_id, document.document_id, document.request_id, "exported", "export_generated", document.version)
        return ModuleResult(True, 200, {"ok": True, "path": str(target)}), json.dumps(export_payload, ensure_ascii=False, indent=2).encode("utf-8"), target.name
