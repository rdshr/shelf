from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

import uvicorn

from project_runtime import DEFAULT_PROJECT_FILE, materialize_project_runtime
from project_runtime.app_factory import PROJECT_FILE_ENV, build_project_app


SRC_DIR = Path(__file__).resolve().parent
REPO_ROOT = SRC_DIR.parent
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
KNOWN_COMMANDS = {"serve"}
RELOAD_DIRS = [
    SRC_DIR,
    REPO_ROOT / "framework",
    REPO_ROOT / "projects",
]
RELOAD_INCLUDES = ["*.py", "*.md", "*.toml", "*.json"]


def _default_project_file_arg() -> str | None:
    if DEFAULT_PROJECT_FILE is None:
        return None
    try:
        return str(DEFAULT_PROJECT_FILE.relative_to(REPO_ROOT))
    except ValueError:
        return str(DEFAULT_PROJECT_FILE)


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
        description="Shelf repository entrypoint. Default behavior loads the configured project runtime and serves it."
    )
    subparsers = parser.add_subparsers(dest="command")
    serve_parser = subparsers.add_parser("serve", help="load the selected project runtime and start the demo server")
    serve_parser.add_argument(
        "--project-file",
        default=_default_project_file_arg(),
        help="path to the project.toml file. Defaults to the auto-discovered project under projects/*/project.toml.",
    )
    serve_parser.add_argument("--host", default=DEFAULT_HOST, help=f"bind host (default: {DEFAULT_HOST})")
    serve_parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"bind port (default: {DEFAULT_PORT})")
    serve_parser.add_argument("--reload", action="store_true", help="enable uvicorn reload mode and pre-materialize generated artifacts")
    return parser


def _serve_project(project_file: str | Path | None, *, host: str, port: int, reload: bool) -> None:
    resolved_project_file: Path | None = None
    if project_file is not None:
        resolved_project_file = Path(project_file)
        if not resolved_project_file.is_absolute():
            resolved_project_file = (REPO_ROOT / resolved_project_file).resolve()
        os.environ[PROJECT_FILE_ENV] = str(resolved_project_file)
    else:
        os.environ.pop(PROJECT_FILE_ENV, None)

    if reload:
        materialize_project_runtime(resolved_project_file)
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

    app = build_project_app(resolved_project_file)
    uvicorn.run(app, host=host, port=port)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(_normalize_argv(list(sys.argv[1:] if argv is None else argv)))
    if args.command == "serve":
        _serve_project(args.project_file, host=args.host, port=args.port, reload=args.reload)
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
