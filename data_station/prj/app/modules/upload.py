from __future__ import annotations

import hashlib
import mimetypes
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from ..config import AppConfig
from ..models import ModuleResult


_FILENAME_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


class UploadContractModule:
    def __init__(self, config: AppConfig) -> None:
        self.config = config.section("l2_upload_contract")

    @property
    def upload_path(self) -> str:
        return str(self.config.get("upload_path", "/api/upload"))

    @property
    def allowed_methods(self) -> set[str]:
        return {str(item).upper() for item in self.config.get("allowed_methods", ["POST"]) }

    @property
    def allowed_extensions(self) -> set[str]:
        return {str(item).lower() for item in self.config.get("allowed_extensions", [])}

    @property
    def required_headers(self) -> list[str]:
        return [str(item) for item in self.config.get("required_headers", [])]

    @property
    def max_upload_size_bytes(self) -> int:
        return int(self.config.get("max_upload_size_bytes", 5 * 1024 * 1024))

    def build_success(self, document: dict[str, Any], duplicate: bool) -> ModuleResult:
        message_key = "duplicate_message" if duplicate else "success_message"
        message = str(self.config.get(message_key, "Upload succeeded."))
        payload = {
            "ok": True,
            "duplicate": duplicate,
            "message": message,
            "document": document,
        }
        status_code = 200 if duplicate else 201
        return ModuleResult(True, status_code, payload)

    def build_error(self, status_code: int, reason_code: str, message: str, details: dict[str, Any] | None = None) -> ModuleResult:
        payload = {
            "ok": False,
            "reason_code": reason_code,
            "message": message,
            "details": details or {},
        }
        return ModuleResult(False, status_code, payload)

    def frontend_config(self) -> dict[str, Any]:
        return {
            "uploadPath": self.upload_path,
            "maxUploadSizeBytes": self.max_upload_size_bytes,
            "allowedExtensions": sorted(self.allowed_extensions),
        }


class AdmissionInterfaceModule:
    def __init__(self, app_config: AppConfig, contract: UploadContractModule) -> None:
        self.module_config = app_config.section("l3_admission_interface")
        self.contract = contract

    def _sanitize_filename(self, raw_name: str) -> str:
        filename = os.path.basename(raw_name.strip()) or "uploaded.bin"
        filename = _FILENAME_SAFE.sub("_", filename)
        return filename[:255]

    def admit(self, path: str, method: str, headers: dict[str, str]) -> ModuleResult:
        if path != self.contract.upload_path:
            return self.contract.build_error(404, "path_not_allowed", "Upload path is not allowed.")
        if method.upper() not in self.contract.allowed_methods:
            return self.contract.build_error(405, "method_not_allowed", "Upload method is not allowed.")
        missing = [name for name in self.contract.required_headers if not headers.get(name)]
        if missing:
            return self.contract.build_error(400, "missing_headers", "Required upload headers are missing.", {"missing_headers": missing})
        length_header = headers.get("Content-Length", "")
        if not length_header and self.module_config.get("require_content_length", True):
            return self.contract.build_error(411, "missing_content_length", "Content-Length is required.")
        try:
            content_length = int(length_header)
        except ValueError:
            return self.contract.build_error(400, "invalid_content_length", "Content-Length must be an integer.")
        if content_length <= 0:
            return self.contract.build_error(400, "empty_body", "Upload body must not be empty.")
        filename = unquote(headers["X-Filename"])
        if self.module_config.get("sanitize_filename", True):
            filename = self._sanitize_filename(filename)
        mime_type = headers.get("Content-Type") or mimetypes.guess_type(filename)[0] or "application/octet-stream"
        metadata = {
            "document_type": headers["X-Document-Type"],
            "source": headers["X-Source"],
            "request_id": headers["X-Request-Id"],
        }
        payload = {
            "ok": True,
            "context": {
                "filename": filename,
                "mime_type": mime_type,
                "content_length": content_length,
                "metadata": metadata,
                "path": path,
                "method": method.upper(),
            },
        }
        return ModuleResult(True, 200, payload)


class PayloadHandlingInterfaceModule:
    def __init__(self, app_config: AppConfig, contract: UploadContractModule) -> None:
        self.module_config = app_config.section("l3_payload_handling")
        self.contract = contract

    def read_and_validate(self, body: bytes, context: dict[str, Any]) -> ModuleResult:
        if not self.module_config.get("allow_empty_file", False) and not body:
            return self.contract.build_error(400, "empty_file", "Uploading an empty file is not allowed.")
        if len(body) > self.contract.max_upload_size_bytes:
            return self.contract.build_error(413, "file_too_large", "File exceeds configured size limit.")
        extension = Path(context["filename"]).suffix.lower()
        if self.contract.allowed_extensions and extension not in self.contract.allowed_extensions:
            return self.contract.build_error(400, "extension_not_allowed", "File extension is not allowed.", {"extension": extension})
        digest = hashlib.sha256(body).hexdigest() if self.module_config.get("sha256_enabled", True) else ""
        payload = {
            "ok": True,
            "payload": {
                "bytes": body,
                "size_bytes": len(body),
                "sha256": digest,
                "extension": extension,
                "mime_type": context["mime_type"],
                "filename": context["filename"],
                "metadata": context["metadata"],
            },
        }
        return ModuleResult(True, 200, payload)


class FilePersistenceInterfaceModule:
    def __init__(self, app_config: AppConfig) -> None:
        self.module_config = app_config.section("l3_file_persistence")
        self.uploads_dir = app_config.uploads_dir
        self._ensure_upload_dir()

    def _ensure_upload_dir(self) -> None:
        self.uploads_dir.mkdir(parents=True, exist_ok=True)

    def persist(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._ensure_upload_dir()
        timestamp = datetime.now().strftime(self.module_config.get("timestamp_format", "%Y%m%d%H%M%S"))
        unique = uuid.uuid4().hex[:8]
        pattern = str(self.module_config.get("filename_pattern", "{timestamp}_{uuid}_{filename}"))
        stored_filename = pattern.format(timestamp=timestamp, uuid=unique, filename=payload["filename"])
        target = self.uploads_dir / stored_filename
        target.write_bytes(payload["bytes"])
        return {
            "stored_filename": stored_filename,
            "stored_path": str(target),
        }


class ResultOutputInterfaceModule:
    def __init__(self, app_config: AppConfig, contract: UploadContractModule) -> None:
        self.module_config = app_config.section("l3_result_output")
        self.contract = contract

    def success(self, document: dict[str, Any], duplicate: bool) -> ModuleResult:
        result = self.contract.build_success(document, duplicate)
        if duplicate:
            result.status_code = int(self.module_config.get("duplicate_status", result.status_code))
        else:
            result.status_code = int(self.module_config.get("success_status", result.status_code))
        return result


class BackendUploadIngressServiceModule:
    def __init__(
        self,
        admission: AdmissionInterfaceModule,
        payload_handler: PayloadHandlingInterfaceModule,
        persistence: FilePersistenceInterfaceModule,
        output: ResultOutputInterfaceModule,
    ) -> None:
        self.admission = admission
        self.payload_handler = payload_handler
        self.persistence = persistence
        self.output = output

    def admit_request(self, path: str, method: str, headers: dict[str, str]) -> ModuleResult:
        return self.admission.admit(path, method, headers)

    def ingest(self, body: bytes, context: dict[str, Any]) -> ModuleResult:
        payload_result = self.payload_handler.read_and_validate(body, context)
        if not payload_result.ok:
            return payload_result
        persisted = self.persistence.persist(payload_result.payload["payload"])
        payload = payload_result.payload["payload"] | persisted
        return ModuleResult(True, 200, {"payload": payload})

    def build_success(self, document: dict[str, Any], duplicate: bool) -> ModuleResult:
        return self.output.success(document, duplicate)


class UploadIngressModule:
    def __init__(self, app_config: AppConfig) -> None:
        self.frontend_config = app_config.section("l2_frontend_upload")
        contract = UploadContractModule(app_config)
        self.contract = contract
        self.backend = BackendUploadIngressServiceModule(
            AdmissionInterfaceModule(app_config, contract),
            PayloadHandlingInterfaceModule(app_config, contract),
            FilePersistenceInterfaceModule(app_config),
            ResultOutputInterfaceModule(app_config, contract),
        )

    def public_config(self) -> dict[str, Any]:
        return {
            **self.contract.frontend_config(),
            "refreshAfterUpload": bool(self.frontend_config.get("refresh_after_upload", True)),
            "defaultActorRole": str(self.frontend_config.get("default_actor_role", "engineer")),
        }
