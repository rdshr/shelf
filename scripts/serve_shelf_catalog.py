from __future__ import annotations

import argparse
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = REPO_ROOT / "src"
WEB_ROOT = REPO_ROOT / "web" / "shelf_viewer"

import sys

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from shelf_catalog_engine import (  # noqa: E402
    CATALOG_CACHE_PATH,
    BoundaryConstraint,
    SearchSpace,
    _load_or_build_fixed_cache,
    build_catalog,
    default_boundary,
)


LOGGER = logging.getLogger("shelf_catalog_server")


def _parse_scalar(raw: str, *, is_float: bool) -> int | float:
    text = raw.strip()
    if not text:
        raise ValueError("empty scalar")

    # 兼容历史输入形式：只取首个值，语义改为固定系统参数。
    if "," in text:
        text = text.split(",", maxsplit=1)[0].strip()
    if "-" in text and text.count("-") == 1 and not text.startswith("-"):
        text = text.split("-", maxsplit=1)[0].strip()

    if is_float:
        return float(text)
    return int(text)


def _qs_value(params: dict[str, list[str]], key: str, default: str) -> str:
    values = params.get(key)
    if not values:
        return default
    return values[0]


def _build_space_from_query(params: dict[str, list[str]]) -> SearchSpace:
    del params
    return SearchSpace(
        slots_x=3,
        slots_y=3,
        slots_z=3,
        panel_length=1.0,
        panel_width=1.0,
        rod_length=1.0,
        dedupe_symmetry=True,
    )


def _build_boundary_from_query(params: dict[str, list[str]]) -> BoundaryConstraint:
    boundary = default_boundary()
    max_layers_n = int(
        _parse_scalar(_qs_value(params, "boundary_n", str(boundary.max_layers_n)), is_float=False)
    )
    baseline_gain = float(
        _parse_scalar(
            _qs_value(
                params,
                "boundary_g",
                _qs_value(params, "boundary_s", str(boundary.baseline_gain)),
            ),
            is_float=True,
        )
    )
    return BoundaryConstraint(
        max_layers_n=max_layers_n,
        baseline_gain=max(1e-9, baseline_gain),
    )


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class ShelfCatalogHandler(BaseHTTPRequestHandler):
    server_version = "ShelfCatalog/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        LOGGER.info("%s | INFO | shelf_catalog_server | %s", _timestamp(), fmt % args)

    def _send_json(self, payload: dict[str, Any], status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self, relative: str) -> None:
        target = (WEB_ROOT / relative).resolve()
        if not str(target).startswith(str(WEB_ROOT.resolve())):
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        if not target.exists() or not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        content_type = "text/plain; charset=utf-8"
        if target.suffix == ".html":
            content_type = "text/html; charset=utf-8"
        elif target.suffix == ".css":
            content_type = "text/css; charset=utf-8"
        elif target.suffix == ".js":
            content_type = "application/javascript; charset=utf-8"
        elif target.suffix == ".json":
            content_type = "application/json; charset=utf-8"

        body = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path or "/"

        if path == "/api/health":
            self._send_json({"ok": True})
            return

        if path == "/api/catalog":
            query = parse_qs(parsed.query, keep_blank_values=False)
            try:
                space = _build_space_from_query(query)
                boundary = _build_boundary_from_query(query)
                family_filter = _qs_value(query, "family", "all")
                status_filter = _qs_value(query, "status", "all")
                sort_key = _qs_value(query, "sort", "goal_desc")
                offset = max(0, int(_qs_value(query, "offset", "0")))
                limit = max(1, int(_qs_value(query, "limit", "80")))

                payload = build_catalog(
                    space=space,
                    boundary=boundary,
                    family_filter=family_filter,
                    status_filter=status_filter,
                    sort_key=sort_key,
                    offset=offset,
                    limit=limit,
                )
                self._send_json(payload)
            except Exception as exc:  # noqa: BLE001
                LOGGER.exception("%s | ERROR | shelf_catalog_server | /api/catalog failed", _timestamp())
                self._send_json(
                    {"ok": False, "error": str(exc)},
                    status=HTTPStatus.BAD_REQUEST,
                )
            return

        if path == "/" or path == "":
            self._serve_static("index.html")
            return

        relative = path.lstrip("/")
        self._serve_static(relative)


def main() -> None:
    parser = argparse.ArgumentParser(description="启动置物架组合可视化服务器。")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )

    if not WEB_ROOT.exists():
        raise FileNotFoundError(f"missing web root: {WEB_ROOT}")

    LOGGER.info("%s | INFO | shelf_catalog_server | warming cache: %s", _timestamp(), CATALOG_CACHE_PATH)
    _load_or_build_fixed_cache()
    LOGGER.info("%s | INFO | shelf_catalog_server | cache ready", _timestamp())

    server = ThreadingHTTPServer((args.host, args.port), ShelfCatalogHandler)
    LOGGER.info(
        "%s | INFO | shelf_catalog_server | server started at http://%s:%s",
        _timestamp(),
        args.host,
        args.port,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        LOGGER.info("%s | INFO | shelf_catalog_server | server stopped by keyboard interrupt", _timestamp())
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
