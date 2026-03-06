from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from ..config import AppConfig
from ..models import SessionRecord, UserRecord, utc_now_iso
from ..storage import SessionRepository, UserRepository


class UserDirectoryModule:
    def __init__(self, app_config: AppConfig, repository: UserRepository) -> None:
        self.auth_config = app_config.section("l1_authentication")
        self.bootstrap_config = app_config.section("l2_authentication_bootstrap")
        self.registration_config = app_config.section("l2_registration_policy")
        self.repository = repository
        self.default_iterations = int(self.registration_config.get("default_password_iterations", 200000))
        self._ensure_seed_root()

    def authenticate(self, email: str, password: str) -> tuple[UserRecord | None, str]:
        user = self.repository.get_by_email(email)
        if user is None:
            return None, "Email or password is invalid."
        if not user.active:
            return None, "Account is disabled."
        if user.status != "approved":
            return None, "Account is waiting for root approval."
        if not self._verify_password(user, password):
            return None, "Email or password is invalid."
        user.last_login_at = utc_now_iso()
        user.updated_at = utc_now_iso()
        self.repository.save_user(user)
        return user, "login succeeded"

    def register(self, email: str, password: str, username: str, duties: list[str]) -> tuple[UserRecord | None, str]:
        normalized_email = email.strip().lower()
        normalized_username = username.strip()
        if not normalized_email or "@" not in normalized_email:
            return None, "Email is invalid."
        if not normalized_username:
            return None, "Username is required."
        minimum = int(self.registration_config.get("minimum_password_length", 8))
        if len(password) < minimum:
            return None, f"Password must be at least {minimum} characters."
        if self.repository.get_by_email(normalized_email) is not None:
            return None, "Email is already registered."
        salt = secrets.token_hex(16)
        iterations = self.default_iterations
        user = UserRecord(
            user_id=uuid.uuid4().hex,
            email=normalized_email,
            username=normalized_username,
            role=str(self.registration_config.get("default_role", "viewer")),
            duties=duties,
            status="pending",
            active=True,
            password_hash=self._hash_password(password, salt, iterations),
            password_salt=salt,
            password_iterations=iterations,
            created_at=utc_now_iso(),
            updated_at=utc_now_iso(),
        )
        self.repository.save_user(user)
        return user, "registration submitted"

    def get_user_by_email(self, email: str) -> UserRecord | None:
        return self.repository.get_by_email(email)

    def get_user(self, user_id: str) -> UserRecord | None:
        return self.repository.get_user(user_id)

    def list_users(self) -> list[UserRecord]:
        return self.repository.list_users()

    def approve(self, root_user: UserRecord, user_id: str) -> tuple[UserRecord | None, str]:
        user = self.repository.get_user(user_id)
        if user is None:
            return None, "User not found."
        if user.role == "root" and user.user_id != root_user.user_id:
            return None, "Root account cannot be modified by another root operation."
        user.status = "approved"
        user.approved_at = utc_now_iso()
        user.approved_by = root_user.user_id
        user.updated_at = utc_now_iso()
        self.repository.save_user(user)
        return user, "user approved"

    def update_user(self, root_user: UserRecord, user_id: str, payload: dict[str, Any]) -> tuple[UserRecord | None, str]:
        user = self.repository.get_user(user_id)
        if user is None:
            return None, "User not found."
        if user.role == "root" and user.user_id != root_user.user_id:
            return None, "Root account cannot be modified by another root operation."
        allowed_roles = [str(item) for item in self.registration_config.get("assignable_roles", ["viewer", "engineer", "root"])]
        if "username" in payload:
            username = str(payload.get("username", "")).strip()
            if not username:
                return None, "Username is required."
            user.username = username
        if "duties" in payload:
            duties = payload.get("duties", [])
            if not isinstance(duties, list):
                return None, "Duties must be a list."
            user.duties = [str(item).strip() for item in duties if str(item).strip()]
        if "role" in payload:
            role = str(payload.get("role", "")).strip()
            if role not in allowed_roles:
                return None, "Role is not allowed."
            user.role = role
        if "active" in payload:
            user.active = bool(payload.get("active"))
        if "password" in payload:
            password = str(payload.get("password", ""))
            minimum = int(self.registration_config.get("minimum_password_length", 8))
            if len(password) < minimum:
                return None, f"Password must be at least {minimum} characters."
            salt = secrets.token_hex(16)
            user.password_salt = salt
            user.password_iterations = self.default_iterations
            user.password_hash = self._hash_password(password, salt, user.password_iterations)
        if user.status == "pending" and user.role != str(self.registration_config.get("default_role", "viewer")):
            user.status = "approved"
            user.approved_at = user.approved_at or utc_now_iso()
            user.approved_by = user.approved_by or root_user.user_id
        user.updated_at = utc_now_iso()
        self.repository.save_user(user)
        return user, "user updated"

    def _verify_password(self, user: UserRecord, password: str) -> bool:
        candidate = self._hash_password(password, user.password_salt, user.password_iterations)
        return bool(user.password_hash) and hmac.compare_digest(candidate, user.password_hash)

    @staticmethod
    def _hash_password(password: str, salt: str, iterations: int) -> str:
        derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
        return derived.hex()

    def _ensure_seed_root(self) -> None:
        seed_email = str(self.bootstrap_config.get("root_email", "root@root.com")).strip().lower()
        if self.repository.get_by_email(seed_email) is not None:
            return
        root = UserRecord(
            user_id=str(self.bootstrap_config.get("root_user_id", "root.local")),
            email=seed_email,
            username=str(self.bootstrap_config.get("root_username", "root")),
            role="root",
            duties=[str(item) for item in self.bootstrap_config.get("root_duties", ["系统管理", "用户审批", "权限调整"])],
            status="approved",
            active=True,
            password_salt=str(self.bootstrap_config.get("root_password_salt", "root-seed-2026")),
            password_iterations=int(self.bootstrap_config.get("root_password_iterations", self.default_iterations)),
            password_hash=str(self.bootstrap_config.get("root_password_hash", "")),
            approved_at=utc_now_iso(),
            approved_by="system",
            created_at=utc_now_iso(),
            updated_at=utc_now_iso(),
        )
        self.repository.save_user(root)


class SessionManagementModule:
    def __init__(self, app_config: AppConfig, repository: SessionRepository) -> None:
        self.config = app_config.section("l1_authentication")
        self.session_config = app_config.section("l2_session_management")
        self.repository = repository

    @property
    def cookie_name(self) -> str:
        return str(self.config.get("session_cookie_name", "data_station_session"))

    def create_session(self, user: UserRecord) -> SessionRecord:
        ttl_hours = int(self.session_config.get("session_ttl_hours", 12))
        now = datetime.now(timezone.utc)
        session = SessionRecord(
            token=secrets.token_urlsafe(32),
            user_id=user.user_id,
            email=user.email,
            created_at=now.isoformat(),
            expires_at=(now + timedelta(hours=ttl_hours)).isoformat(),
        )
        self.repository.save_session(session)
        return session

    def current_session(self, token: str | None) -> SessionRecord | None:
        if not token:
            return None
        session = self.repository.get_session(token)
        if session is None:
            return None
        try:
            expires_at = datetime.fromisoformat(session.expires_at)
        except ValueError:
            self.repository.delete_session(token)
            return None
        if expires_at <= datetime.now(timezone.utc):
            self.repository.delete_session(token)
            return None
        return session

    def revoke(self, token: str | None) -> None:
        if token:
            self.repository.delete_session(token)

    def cookie_settings(self) -> dict[str, Any]:
        return {
            "path": str(self.session_config.get("cookie_path", "/")),
            "http_only": bool(self.session_config.get("http_only", True)),
            "same_site": str(self.session_config.get("same_site", "Lax")),
            "max_age": int(self.session_config.get("session_ttl_hours", 12)) * 3600,
        }


class AuthenticationModule:
    def __init__(self, app_config: AppConfig, session_repository: SessionRepository, user_repository: UserRepository) -> None:
        self.directory = UserDirectoryModule(app_config, user_repository)
        self.sessions = SessionManagementModule(app_config, session_repository)

    def login(self, email: str, password: str) -> tuple[UserRecord | None, SessionRecord | None, str]:
        user, message = self.directory.authenticate(email, password)
        if user is None:
            return None, None, message
        session = self.sessions.create_session(user)
        return user, session, message

    def register(self, email: str, password: str, username: str, duties: list[str]) -> tuple[UserRecord | None, str]:
        return self.directory.register(email, password, username, duties)

    def current_user(self, token: str | None) -> tuple[UserRecord | None, SessionRecord | None]:
        session = self.sessions.current_session(token)
        if session is None:
            return None, None
        user = self.directory.get_user_by_email(session.email)
        if user is None or not user.active or user.status != "approved":
            if session is not None:
                self.sessions.revoke(session.token)
            return None, None
        return user, session

    def list_users(self) -> list[UserRecord]:
        return self.directory.list_users()

    def approve_user(self, root_user: UserRecord, user_id: str) -> tuple[UserRecord | None, str]:
        return self.directory.approve(root_user, user_id)

    def update_user(self, root_user: UserRecord, user_id: str, payload: dict[str, Any]) -> tuple[UserRecord | None, str]:
        return self.directory.update_user(root_user, user_id, payload)

    def logout(self, token: str | None) -> None:
        self.sessions.revoke(token)
