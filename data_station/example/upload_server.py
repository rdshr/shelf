from __future__ import annotations

import json
import os
import pathlib
import time
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


HOST = "127.0.0.1"
PORT = 8000
MAX_UPLOAD_SIZE = 5 * 1024 * 1024
BASE_DIR = pathlib.Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / "index.html"
UPLOAD_DIR = BASE_DIR / "uploads"


def safe_filename(raw_name: str) -> str:
    decoded = urllib.parse.unquote(raw_name or "").strip()
    filename = os.path.basename(decoded)
    filename = filename.replace("\\", "_").replace("/", "_")
    return filename or "uploaded.bin"


class UploadHandler(BaseHTTPRequestHandler):
    server_version = "UploadExample/0.1"

    def do_GET(self) -> None:
        if self.path not in ("/", "/index.html"):
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        body = INDEX_FILE.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self.path != "/upload":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        length_header = self.headers.get("Content-Length", "0")
        try:
            content_length = int(length_header)
        except ValueError:
            self.write_json(
                HTTPStatus.BAD_REQUEST,
                {"ok": False, "message": "Invalid Content-Length."},
            )
            return

        if content_length <= 0:
            self.write_json(
                HTTPStatus.BAD_REQUEST,
                {"ok": False, "message": "Empty request body."},
            )
            return

        if content_length > MAX_UPLOAD_SIZE:
            self.write_json(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                {
                    "ok": False,
                    "message": f"File is too large. Max size is {MAX_UPLOAD_SIZE} bytes.",
                },
            )
            return

        raw_name = self.headers.get("X-Filename", "")
        filename = safe_filename(raw_name)
        body = self.rfile.read(content_length)

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        saved_name = f"{int(time.time())}_{filename}"
        target = UPLOAD_DIR / saved_name
        target.write_bytes(body)

        self.write_json(
            HTTPStatus.OK,
            {
                "ok": True,
                "message": "Upload succeeded.",
                "filename": filename,
                "size": len(body),
                "saved_to": str(target.relative_to(BASE_DIR.parent.parent)),
            },
        )

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"[upload-example] {self.address_string()} - {fmt % args}")

    def write_json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), UploadHandler)
    print(f"Serving upload example at http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
