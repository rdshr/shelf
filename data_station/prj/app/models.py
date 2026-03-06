from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class DocumentRecord:
    document_id: str
    request_id: str
    original_filename: str
    stored_filename: str
    stored_path: str
    mime_type: str
    extension: str
    size_bytes: int
    sha256: str
    metadata: dict[str, Any]
    state: str
    version: int
    folder_id: str = "uncategorized"
    processing: dict[str, Any] = field(default_factory=dict)
    review: dict[str, Any] = field(default_factory=dict)
    exports: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DocumentRecord":
        return cls(**payload)


@dataclass
class AuthorizationDecision:
    allowed: bool
    reason_code: str
    message: str
    scope: str


@dataclass
class ModuleResult:
    ok: bool
    status_code: int
    payload: dict[str, Any]


@dataclass
class UserRecord:
    user_id: str
    email: str
    username: str
    role: str
    duties: list[str] = field(default_factory=list)
    status: str = "approved"
    active: bool = True
    password_hash: str = ""
    password_salt: str = ""
    password_iterations: int = 200000
    approved_at: str = ""
    approved_by: str = ""
    last_login_at: str = ""
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    profile: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_public_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("password_hash", None)
        payload.pop("password_salt", None)
        payload.pop("password_iterations", None)
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "UserRecord":
        return cls(**payload)


@dataclass
class SessionRecord:
    token: str
    user_id: str
    email: str
    created_at: str = field(default_factory=utc_now_iso)
    expires_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SessionRecord":
        return cls(**payload)


@dataclass
class FolderRecord:
    folder_id: str
    name: str
    parent_id: str | None
    system: bool
    created_by: str
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "FolderRecord":
        return cls(**payload)
