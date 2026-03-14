from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import tomllib
from typing import Any


POLICY_FILE = Path(__file__).with_name("repository_policy.toml")


@dataclass(frozen=True)
class RepositoryPortabilityPolicy:
    text_scan_roots: tuple[str, ...]
    text_scan_extensions: frozenset[str]
    excluded_roots: tuple[str, ...]
    issue_template_files: tuple[str, ...]


@dataclass(frozen=True)
class RepositoryValidationPolicy:
    public_repo_slug: str
    default_level_order: tuple[str, ...]
    valid_node_kinds: frozenset[str]
    level_allowed_prefixes: dict[str, tuple[str, ...]]
    required_l1_anchors_per_l2: tuple[str, ...]
    required_framework_directive_sections: tuple[str, ...]
    allowed_project_top_level_dirs: frozenset[str]
    allowed_project_root_files: frozenset[str]
    allowed_project_doc_suffixes: frozenset[str]
    portability: RepositoryPortabilityPolicy


def _require_table(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"repository policy missing table: {key}")
    return value


def _require_string(parent: dict[str, Any], key: str) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"repository policy missing string: {key}")
    return value.strip()


def _require_string_tuple(parent: dict[str, Any], key: str) -> tuple[str, ...]:
    value = parent.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"repository policy missing string list: {key}")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"repository policy {key} must contain non-empty strings")
        items.append(item.strip())
    return tuple(items)


@lru_cache(maxsize=1)
def load_repository_validation_policy() -> RepositoryValidationPolicy:
    with POLICY_FILE.open("rb") as fh:
        data = tomllib.load(fh)
    if not isinstance(data, dict):
        raise ValueError("repository policy must decode into an object")

    repo_table = _require_table(data, "repo")
    validation_table = _require_table(data, "validation")
    portability_table = _require_table(data, "portability")
    level_allowed_prefixes_table = _require_table(validation_table, "level_allowed_prefixes")

    level_allowed_prefixes: dict[str, tuple[str, ...]] = {}
    for level, prefixes in level_allowed_prefixes_table.items():
        if not isinstance(level, str) or not level.strip():
            raise ValueError("repository policy level_allowed_prefixes keys must be non-empty strings")
        if not isinstance(prefixes, list) or not prefixes:
            raise ValueError(f"repository policy level_allowed_prefixes.{level} must be a non-empty list")
        normalized_prefixes: list[str] = []
        for prefix in prefixes:
            if not isinstance(prefix, str) or not prefix.strip():
                raise ValueError(f"repository policy level_allowed_prefixes.{level} must contain strings")
            normalized_prefixes.append(prefix.strip())
        level_allowed_prefixes[level.strip()] = tuple(normalized_prefixes)

    portability = RepositoryPortabilityPolicy(
        text_scan_roots=_require_string_tuple(portability_table, "text_scan_roots"),
        text_scan_extensions=frozenset(_require_string_tuple(portability_table, "text_scan_extensions")),
        excluded_roots=_require_string_tuple(portability_table, "excluded_roots"),
        issue_template_files=_require_string_tuple(portability_table, "issue_template_files"),
    )
    return RepositoryValidationPolicy(
        public_repo_slug=_require_string(repo_table, "public_repo_slug"),
        default_level_order=_require_string_tuple(validation_table, "default_level_order"),
        valid_node_kinds=frozenset(_require_string_tuple(validation_table, "valid_node_kinds")),
        level_allowed_prefixes=level_allowed_prefixes,
        required_l1_anchors_per_l2=_require_string_tuple(validation_table, "required_l1_anchors_per_l2"),
        required_framework_directive_sections=_require_string_tuple(
            validation_table, "required_framework_directive_sections"
        ),
        allowed_project_top_level_dirs=frozenset(_require_string_tuple(validation_table, "allowed_project_top_level_dirs")),
        allowed_project_root_files=frozenset(_require_string_tuple(validation_table, "allowed_project_root_files")),
        allowed_project_doc_suffixes=frozenset(_require_string_tuple(validation_table, "allowed_project_doc_suffixes")),
        portability=portability,
    )
