from __future__ import annotations

import hashlib
from pathlib import Path
import re
from typing import Any

from project_runtime.models import jsonable


REPO_ROOT = Path(__file__).resolve().parents[2]
def relative_path(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def normalize_project_path(project_file: str | Path) -> Path:
    candidate = Path(project_file)
    if not candidate.is_absolute():
        candidate = (REPO_ROOT / candidate).resolve()
    return candidate


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "section"


def sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def tokenize(text: str) -> tuple[str, ...]:
    return tuple(token for token in re.findall(r"[a-z0-9]{3,}", text.lower()) if token)


def cleanup_generated_output_dir(output_path: Path, expected_file_names: set[str]) -> None:
    for child in output_path.iterdir():
        if not child.is_file():
            continue
        if child.name in expected_file_names:
            continue
        if child.suffix.lower() in {".json", ".py"}:
            child.unlink()


def lookup_dotted_path(payload: dict[str, Any], dotted_path: str) -> Any:
    current: Any = payload
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(dotted_path)
        current = current[part]
    return current


def flatten_config_paths(payload: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(payload, dict):
        flattened: dict[str, Any] = {}
        for key, value in payload.items():
            next_prefix = f"{prefix}.{key}" if prefix else str(key)
            flattened.update(flatten_config_paths(value, next_prefix))
        return flattened
    return {prefix: jsonable(payload)}
