from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from .config import AppConfig
from .service import DataStationService


class DataStationRequestHandler(BaseHTTPRequestHandler):
    server_version = "DataStationPRJ/0.3"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/api/health":
            self._write_json(HTTPStatus.OK, {"ok": True, "status": "up"})
            return
        if path == "/api/bootstrap":
            user, _ = self._current_user()
            self._write_json(HTTPStatus.OK, self.service.frontend_bootstrap(user))
            return
        if path == "/api/auth/session":
            self._handle_session_state()
            return
        if path == "/api/admin/users":
            self._handle_admin_users()
            return
        if path == "/api/tree":
            self._handle_tree()
            return
        if path == "/api/documents":
            self._handle_list_documents(query)
            return
        if path.startswith("/api/documents/") and path.endswith("/export"):
            document_id = path[len("/api/documents/") : -len("/export")].strip("/")
            self._handle_export(document_id)
            return
        if path.startswith("/api/documents/"):
            document_id = path[len("/api/documents/") :].strip("/")
            self._handle_document_detail(document_id)
            return
        self._serve_web_asset(path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/auth/login":
            self._handle_login()
            return
        if path == "/api/auth/register":
            self._handle_register()
            return
        if path == "/api/auth/logout":
            self._handle_logout()
            return
        if path == "/api/folders":
            self._handle_create_folder()
            return
        if path.startswith("/api/admin/users/") and path.endswith("/approve"):
            user_id = path[len("/api/admin/users/") : -len("/approve")].strip("/")
            self._handle_approve_user(user_id)
            return
        if path.startswith("/api/admin/users/") and path.endswith("/update"):
            user_id = path[len("/api/admin/users/") : -len("/update")].strip("/")
            self._handle_update_user(user_id)
            return
        if path == "/api/upload":
            self._handle_upload()
            return
        if path.startswith("/api/documents/") and path.endswith("/process"):
            document_id = path[len("/api/documents/") : -len("/process")].strip("/")
            self._handle_process(document_id)
            return
        if path.startswith("/api/documents/") and path.endswith("/review"):
            document_id = path[len("/api/documents/") : -len("/review")].strip("/")
            self._handle_review(document_id)
            return
        self._write_json(HTTPStatus.NOT_FOUND, {"ok": False, "message": "API route not found."})

    @property
    def service(self) -> DataStationService:
        return self.server.service  # type: ignore[attr-defined]

    @property
    def config(self) -> AppConfig:
        return self.server.config  # type: ignore[attr-defined]

    def log_message(self, format: str, *args: object) -> None:
        message = "%s - - [%s] %s\n" % (
            self.client_address[0],
            self.log_date_time_string(),
            format % args,
        )
        print(message, end="")

    def _handle_session_state(self) -> None:
        result = self.service.session_state(self._session_token())
        self._write_json(result.status_code, result.payload)

    def _handle_login(self) -> None:
        body = self._read_json_body()
        if isinstance(body, tuple):
            status_code, payload = body
            self._write_json(status_code, payload)
            return
        email = str(body.get("email", "")).strip()
        password = str(body.get("password", ""))
        result, session, cookie_settings = self.service.login(email, password)
        if not result.ok or session is None or cookie_settings is None:
            self._write_json(result.status_code, result.payload)
            return
        self._write_json(result.status_code, result.payload, cookies=[self._session_cookie(session.token, cookie_settings)])

    def _handle_register(self) -> None:
        body = self._read_json_body()
        if isinstance(body, tuple):
            status_code, payload = body
            self._write_json(status_code, payload)
            return
        duties = body.get("duties", [])
        if isinstance(duties, str):
            duties = [item.strip() for item in duties.split(",") if item.strip()]
        result = self.service.register(
            str(body.get("email", "")),
            str(body.get("password", "")),
            str(body.get("username", "")),
            duties if isinstance(duties, list) else [],
        )
        self._write_json(result.status_code, result.payload)

    def _handle_logout(self) -> None:
        result = self.service.logout(self._session_token())
        self._write_json(result.status_code, result.payload, cookies=[self._expired_session_cookie()])

    def _handle_admin_users(self) -> None:
        user = self._require_user()
        if user is None:
            return
        result = self.service.list_users(user)
        self._write_json(result.status_code, result.payload)

    def _handle_approve_user(self, user_id: str) -> None:
        user = self._require_user()
        if user is None:
            return
        self._discard_body()
        result = self.service.approve_user(user, user_id)
        self._write_json(result.status_code, result.payload)

    def _handle_update_user(self, user_id: str) -> None:
        user = self._require_user()
        if user is None:
            return
        body = self._read_json_body()
        if isinstance(body, tuple):
            status_code, payload = body
            self._write_json(status_code, payload)
            return
        result = self.service.update_user(user, user_id, body)
        self._write_json(result.status_code, result.payload)

    def _handle_tree(self) -> None:
        user = self._require_user()
        if user is None:
            return
        result = self.service.list_folder_tree(user)
        self._write_json(result.status_code, result.payload)

    def _handle_create_folder(self) -> None:
        user = self._require_user()
        if user is None:
            return
        body = self._read_json_body()
        if isinstance(body, tuple):
            status_code, payload = body
            self._write_json(status_code, payload)
            return
        result = self.service.create_folder(user, str(body.get("name", "")), body.get("parent_id"))
        self._write_json(result.status_code, result.payload)

    def _handle_list_documents(self, query: dict[str, list[str]]) -> None:
        user = self._require_user()
        if user is None:
            return
        page = self._query_int(query, "page", 1)
        page_size = self._query_int(query, "page_size", self.service.frontend_bootstrap(user)["display"]["defaultPageSize"])
        result = self.service.list_documents(
            user,
            self._query_value(query, "query") or "",
            self._query_value(query, "state") or "",
            page,
            page_size,
            self._query_value(query, "folder_id"),
        )
        self._write_json(result.status_code, result.payload)

    def _handle_document_detail(self, document_id: str) -> None:
        user = self._require_user()
        if user is None:
            return
        result = self.service.get_document_detail(user, document_id)
        self._write_json(result.status_code, result.payload)

    def _handle_upload(self) -> None:
        user = self._require_user()
        if user is None:
            return
        content_length = self._content_length()
        if content_length < 0:
            self._write_json(HTTPStatus.LENGTH_REQUIRED, {"ok": False, "message": "Content-Length is required."})
            return
        body = self.rfile.read(content_length)
        result = self.service.upload_document(self.path, self.command, self._request_headers(), body, user)
        self._write_json(result.status_code, result.payload)

    def _handle_process(self, document_id: str) -> None:
        user = self._require_user()
        if user is None:
            return
        self._discard_body()
        result = self.service.process_document(user, document_id)
        self._write_json(result.status_code, result.payload)

    def _handle_review(self, document_id: str) -> None:
        user = self._require_user()
        if user is None:
            return
        body = self._read_json_body()
        if isinstance(body, tuple):
            status_code, payload = body
            self._write_json(status_code, payload)
            return
        result = self.service.review_document(user, document_id, body)
        self._write_json(result.status_code, result.payload)

    def _handle_export(self, document_id: str) -> None:
        user = self._require_user()
        if user is None:
            return
        result, content, filename = self.service.export_document(user, document_id)
        if not result.ok or content is None or filename is None:
            self._write_json(result.status_code, result.payload)
            return
        self.send_response(result.status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _serve_web_asset(self, path: str) -> None:
        normalized = "/index.html" if path in {"", "/"} else path
        candidate = (self.config.web_dir / normalized.lstrip("/")).resolve()
        try:
            candidate.relative_to(self.config.web_dir.resolve())
        except ValueError:
            self._write_json(HTTPStatus.FORBIDDEN, {"ok": False, "message": "Access denied."})
            return
        if not candidate.exists() or not candidate.is_file():
            self._write_json(HTTPStatus.NOT_FOUND, {"ok": False, "message": "File not found."})
            return
        content = candidate.read_bytes()
        mime_type = mimetypes.guess_type(str(candidate))[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _write_json(self, status_code: int, payload: dict[str, Any], cookies: list[str] | None = None) -> None:
        content = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status_code)
        if cookies:
            for cookie in cookies:
                self.send_header("Set-Cookie", cookie)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _request_headers(self) -> dict[str, str]:
        return {key: value for key, value in self.headers.items()}

    def _session_token(self) -> str | None:
        raw_cookie = self.headers.get("Cookie", "")
        if not raw_cookie:
            return None
        cookie = SimpleCookie()
        cookie.load(raw_cookie)
        cookie_name = self.service.authentication.sessions.cookie_name
        morsel = cookie.get(cookie_name)
        return morsel.value if morsel is not None else None

    def _current_user(self):
        return self.service.current_user(self._session_token())

    def _require_user(self):
        user, _ = self._current_user()
        if user is None:
            self._write_json(HTTPStatus.UNAUTHORIZED, {"ok": False, "message": "Authentication required."})
            return None
        return user

    def _session_cookie(self, token: str, settings: dict[str, Any]) -> str:
        cookie = SimpleCookie()
        name = self.service.authentication.sessions.cookie_name
        cookie[name] = token
        cookie[name]["path"] = settings.get("path", "/")
        cookie[name]["max-age"] = str(settings.get("max_age", 3600))
        cookie[name]["samesite"] = settings.get("same_site", "Lax")
        if settings.get("http_only", True):
            cookie[name]["httponly"] = True
        return cookie.output(header="").strip()

    def _expired_session_cookie(self) -> str:
        cookie = SimpleCookie()
        name = self.service.authentication.sessions.cookie_name
        cookie[name] = ""
        cookie[name]["path"] = "/"
        cookie[name]["max-age"] = "0"
        cookie[name]["expires"] = "Thu, 01 Jan 1970 00:00:00 GMT"
        return cookie.output(header="").strip()

    def _read_json_body(self) -> dict[str, Any] | tuple[int, dict[str, Any]]:
        content_length = self._content_length()
        if content_length < 0:
            return int(HTTPStatus.LENGTH_REQUIRED), {"ok": False, "message": "Content-Length is required."}
        raw = self.rfile.read(content_length)
        if not raw:
            return {}
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return int(HTTPStatus.BAD_REQUEST), {"ok": False, "message": "Request body must be valid JSON."}
        if not isinstance(payload, dict):
            return int(HTTPStatus.BAD_REQUEST), {"ok": False, "message": "Request body must be a JSON object."}
        return payload

    def _discard_body(self) -> None:
        content_length = self._content_length()
        if content_length > 0:
            self.rfile.read(content_length)

    def _content_length(self) -> int:
        value = self.headers.get("Content-Length")
        if value is None:
            return -1
        try:
            return int(value)
        except ValueError:
            return -1

    @staticmethod
    def _query_value(query: dict[str, list[str]], key: str) -> str | None:
        values = query.get(key, [])
        return values[0] if values else None

    @staticmethod
    def _query_int(query: dict[str, list[str]], key: str, default: int) -> int:
        raw = DataStationRequestHandler._query_value(query, key)
        if raw is None:
            return default
        try:
            return int(raw)
        except ValueError:
            return default


class DataStationHTTPServer(ThreadingHTTPServer):
    def __init__(self, host: str, port: int, config: AppConfig, service: DataStationService) -> None:
        super().__init__((host, port), DataStationRequestHandler)
        self.config = config
        self.service = service



def create_server(config: AppConfig, service: DataStationService) -> DataStationHTTPServer:
    return DataStationHTTPServer(config.host, config.port, config, service)
