from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

import uvicorn

from examples.legacy_shelf.reference_pipeline import run_reference_pipeline
from project_runtime import (
    get_default_project_template_registration,
    materialize_registered_project,
)
from project_runtime.app_factory import build_project_app

SRC_DIR = Path(__file__).resolve().parent
REPO_ROOT = SRC_DIR.parent
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
KNOWN_COMMANDS = {"serve", "legacy-reference-shelf"}
DEFAULT_PRODUCT_SPEC_FILE = get_default_project_template_registration().default_product_spec_file
PRODUCT_SPEC_FILE_ENV = "SHELF_PRODUCT_SPEC_FILE"
RELOAD_DIRS = [
    SRC_DIR,
    REPO_ROOT / "framework",
    REPO_ROOT / "projects",
    REPO_ROOT / "mapping",
]
RELOAD_INCLUDES = ["*.py", "*.md", "*.toml", "*.json"]


def _normalize_argv(argv: list[str]) -> list[str]:
    if not argv:
        return ["serve"]
    if argv[0] in {"-h", "--help"}:
        return argv
    if argv[0] in KNOWN_COMMANDS:
        return argv
    return ["serve", *argv]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Shelf repository entrypoint. Default behavior serves the project-driven "
            "knowledge-base demo compiled from framework markdown, product spec, and "
            "implementation config."
        )
    )
    subparsers = parser.add_subparsers(dest="command")

    serve_parser = subparsers.add_parser(
        "serve",
        help="materialize the selected project and start the knowledge-base demo server",
    )
    serve_parser.add_argument(
        "--product-spec-file",
        default=str(DEFAULT_PRODUCT_SPEC_FILE.relative_to(REPO_ROOT)),
        help=(
            "path to the product spec file. Defaults to "
            "projects/knowledge_base_basic/product_spec.toml."
        ),
    )
    serve_parser.add_argument("--host", default=DEFAULT_HOST, help=f"bind host (default: {DEFAULT_HOST})")
    serve_parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"bind port (default: {DEFAULT_PORT})")
    serve_parser.add_argument(
        "--reload",
        action="store_true",
        help="enable uvicorn reload mode for local development",
    )

    subparsers.add_parser(
        "legacy-reference-shelf",
        help=(
            "run the legacy shelf reference pipeline that generates docs/legacy_shelf/* "
            "for the historical shelf domain sample"
        ),
    )
    return parser


def _serve_project(product_spec_file: str | Path, *, host: str, port: int, reload: bool) -> None:
    resolved_product_spec = Path(product_spec_file)
    if not resolved_product_spec.is_absolute():
        resolved_product_spec = (SRC_DIR.parent / resolved_product_spec).resolve()

    os.environ[PRODUCT_SPEC_FILE_ENV] = str(resolved_product_spec)

    if reload:
        # Fail fast and keep generated evidence synchronized before the reload server starts.
        materialize_registered_project(resolved_product_spec)
        uvicorn.run(
            "project_runtime.app_factory:app",
            host=host,
            port=port,
            reload=True,
            app_dir=str(SRC_DIR),
            reload_dirs=[str(path) for path in RELOAD_DIRS],
            reload_includes=RELOAD_INCLUDES,
        )
        return

    app = build_project_app(resolved_product_spec)
    uvicorn.run(app, host=host, port=port)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(_normalize_argv(list(sys.argv[1:] if argv is None else argv)))

    if args.command == "legacy-reference-shelf":
        run_reference_pipeline()
        return 0

    if args.command == "serve":
        _serve_project(
            args.product_spec_file,
            host=args.host,
            port=args.port,
            reload=args.reload,
        )
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
