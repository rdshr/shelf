from __future__ import annotations

import ast
from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import Iterable, Sequence

from rule_validation_models import RuleValidationOutcome, RuleValidationSummary

_GUARD_ALL_TOKEN = "*"
_MAX_REASONS = 40
_MAX_EVIDENCE_ITEMS = 120
_CODE_SUFFIXES: tuple[str, ...] = (
    ".py",
    ".pyi",
    ".js",
    ".mjs",
    ".cjs",
    ".ts",
    ".tsx",
    ".jsx",
)
_JS_RESOLVE_SUFFIXES: tuple[str, ...] = (
    ".js",
    ".mjs",
    ".cjs",
    ".ts",
    ".tsx",
    ".jsx",
)
_DEFAULT_GUARDED_PREFIXES: tuple[str, ...] = (_GUARD_ALL_TOKEN,)
_DEFAULT_IGNORED_PREFIXES: tuple[str, ...] = (
    ".git/",
    ".github/",
    ".venv/",
    "node_modules/",
    "dist/",
    "build/",
    "out/",
    ".pytest_cache/",
    ".mypy_cache/",
    "__pycache__/",
)
_JS_IMPORT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?m)^\s*import\s+(?:[^\"']+?\s+from\s+)?[\"']([^\"']+)[\"']"),
    re.compile(r"(?m)^\s*export\s+[^\"']+?\s+from\s+[\"']([^\"']+)[\"']"),
    re.compile(r"require\(\s*[\"']([^\"']+)[\"']\s*\)"),
    re.compile(r"import\(\s*[\"']([^\"']+)[\"']\s*\)"),
)


@dataclass(frozen=True)
class PathScopePolicy:
    guarded_prefixes: tuple[str, ...]
    ignored_prefixes: tuple[str, ...]

    @classmethod
    def from_raw(
        cls,
        guarded_prefixes: Sequence[str] | None = None,
        ignored_prefixes: Sequence[str] | None = None,
    ) -> "PathScopePolicy":
        return cls(
            guarded_prefixes=_normalize_prefixes(guarded_prefixes, _DEFAULT_GUARDED_PREFIXES),
            ignored_prefixes=_normalize_prefixes(ignored_prefixes, _DEFAULT_IGNORED_PREFIXES),
        )


@dataclass(frozen=True)
class LocalDependency:
    source_rel_path: str
    target_rel_path: str
    line: int
    language: str
    specifier: str

    def to_dict(self) -> dict[str, str | int]:
        return {
            "source": self.source_rel_path,
            "target": self.target_rel_path,
            "line": self.line,
            "language": self.language,
            "specifier": self.specifier,
        }


def _normalize_rel_path(text: str) -> str:
    return text.replace("\\", "/").lstrip("/")


def _normalize_prefixes(values: Sequence[str] | None, fallback: Sequence[str]) -> tuple[str, ...]:
    source = values if values is not None else fallback
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in source:
        text = str(raw or "").strip()
        if not text:
            continue
        if text == _GUARD_ALL_TOKEN:
            return (_GUARD_ALL_TOKEN,)
        item = _normalize_rel_path(text).rstrip("/")
        if not item or item in seen:
            continue
        seen.add(item)
        normalized.append(item)
    if normalized:
        return tuple(normalized)
    return tuple(_normalize_prefixes(fallback, fallback)) if source is not fallback else tuple()


def _path_matches_prefix(rel_path: str, prefix: str) -> bool:
    if prefix == _GUARD_ALL_TOKEN:
        return True
    if rel_path == prefix:
        return True
    return rel_path.startswith(f"{prefix}/")


def _is_code_file(rel_path: str) -> bool:
    suffix = Path(rel_path).suffix.lower()
    return suffix in _CODE_SUFFIXES


def _is_guarded_code_path(rel_path: str, policy: PathScopePolicy) -> bool:
    if not rel_path or rel_path.startswith("..") or not _is_code_file(rel_path):
        return False
    for ignored in policy.ignored_prefixes:
        if _path_matches_prefix(rel_path, ignored):
            return False
    return any(_path_matches_prefix(rel_path, guarded) for guarded in policy.guarded_prefixes)


def _to_rel_path(repo_root: Path, candidate: Path) -> str | None:
    try:
        resolved = candidate.resolve(strict=True)
    except (FileNotFoundError, OSError):
        return None
    try:
        rel = resolved.relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return None
    return _normalize_rel_path(rel)


def _resolve_python_module(repo_root: Path, module_name: str) -> str | None:
    dotted = module_name.strip(".")
    if not dotted:
        return None
    module_path = Path(*dotted.split("."))
    for root in (repo_root / "src", repo_root):
        file_candidate = root / module_path.with_suffix(".py")
        rel_file = _to_rel_path(repo_root, file_candidate)
        if rel_file:
            return rel_file
        init_candidate = root / module_path / "__init__.py"
        rel_init = _to_rel_path(repo_root, init_candidate)
        if rel_init:
            return rel_init
    return None


def _resolve_python_relative_base(repo_root: Path, source_abs: Path, level: int) -> Path | None:
    if level <= 0:
        return source_abs.parent
    target = source_abs.parent
    for _ in range(level - 1):
        target = target.parent
    rel = _to_rel_path(repo_root, target)
    if rel is None:
        return None
    return target


def _resolve_python_relative_target(repo_root: Path, base_dir: Path, module_name: str) -> str | None:
    if not module_name:
        return None
    rel_path = Path(*module_name.split("."))
    file_candidate = base_dir / rel_path.with_suffix(".py")
    rel_file = _to_rel_path(repo_root, file_candidate)
    if rel_file:
        return rel_file
    init_candidate = base_dir / rel_path / "__init__.py"
    rel_init = _to_rel_path(repo_root, init_candidate)
    if rel_init:
        return rel_init
    return None


def _collect_python_dependencies(repo_root: Path, source_abs: Path, source_rel: str) -> list[LocalDependency]:
    text = source_abs.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=source_rel)
    except SyntaxError:
        return []

    deps: list[LocalDependency] = []
    seen: set[tuple[str, int, str]] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                target_rel = _resolve_python_module(repo_root, alias.name)
                if not target_rel:
                    continue
                key = (target_rel, int(node.lineno or 0), alias.name)
                if key in seen:
                    continue
                seen.add(key)
                deps.append(
                    LocalDependency(
                        source_rel_path=source_rel,
                        target_rel_path=target_rel,
                        line=int(node.lineno or 0),
                        language="python",
                        specifier=alias.name,
                    )
                )
            continue

        if not isinstance(node, ast.ImportFrom):
            continue
        level = int(node.level or 0)
        module_name = str(node.module or "")
        line = int(node.lineno or 0)

        if level > 0:
            base_dir = _resolve_python_relative_base(repo_root, source_abs, level)
            if base_dir is None:
                continue
            targets: list[tuple[str, str]] = []
            if module_name:
                target_rel = _resolve_python_relative_target(repo_root, base_dir, module_name)
                if target_rel:
                    targets.append((target_rel, f"{'.' * level}{module_name}"))
            else:
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    target_rel = _resolve_python_relative_target(repo_root, base_dir, alias.name)
                    if target_rel:
                        targets.append((target_rel, f"{'.' * level}{alias.name}"))
            for target_rel, specifier in targets:
                key = (target_rel, line, specifier)
                if key in seen:
                    continue
                seen.add(key)
                deps.append(
                    LocalDependency(
                        source_rel_path=source_rel,
                        target_rel_path=target_rel,
                        line=line,
                        language="python",
                        specifier=specifier,
                    )
                )
            continue

        targets = []
        if module_name:
            resolved_module = _resolve_python_module(repo_root, module_name)
            if resolved_module:
                targets.append((resolved_module, module_name))
            for alias in node.names:
                if alias.name == "*":
                    continue
                candidate_name = f"{module_name}.{alias.name}"
                resolved_candidate = _resolve_python_module(repo_root, candidate_name)
                if resolved_candidate:
                    targets.append((resolved_candidate, candidate_name))
        for target_rel, specifier in targets:
            key = (target_rel, line, specifier)
            if key in seen:
                continue
            seen.add(key)
            deps.append(
                LocalDependency(
                    source_rel_path=source_rel,
                    target_rel_path=target_rel,
                    line=line,
                    language="python",
                    specifier=specifier,
                )
            )
    return deps


def _resolve_js_target(repo_root: Path, source_abs: Path, specifier: str) -> str | None:
    spec = specifier.strip()
    if not spec:
        return None
    if spec.startswith("/"):
        base = repo_root / spec.lstrip("/")
    elif spec.startswith("./") or spec.startswith("../"):
        base = source_abs.parent / spec
    else:
        return None

    candidates: list[Path] = []
    if base.suffix:
        candidates.append(base)
    else:
        candidates.append(base)
        for suffix in _JS_RESOLVE_SUFFIXES:
            candidates.append(base.with_suffix(suffix))
            candidates.append(base / f"index{suffix}")

    for candidate in candidates:
        rel = _to_rel_path(repo_root, candidate)
        if rel and _is_code_file(rel):
            return rel
    return None


def _collect_js_dependencies(repo_root: Path, source_abs: Path, source_rel: str) -> list[LocalDependency]:
    text = source_abs.read_text(encoding="utf-8")
    deps: list[LocalDependency] = []
    seen: set[tuple[str, int, str]] = set()
    for pattern in _JS_IMPORT_PATTERNS:
        for match in pattern.finditer(text):
            specifier = str(match.group(1) or "").strip()
            target_rel = _resolve_js_target(repo_root, source_abs, specifier)
            if not target_rel:
                continue
            line = text.count("\n", 0, match.start()) + 1
            key = (target_rel, line, specifier)
            if key in seen:
                continue
            seen.add(key)
            deps.append(
                LocalDependency(
                    source_rel_path=source_rel,
                    target_rel_path=target_rel,
                    line=line,
                    language="javascript",
                    specifier=specifier,
                )
            )
    return deps


def _collect_local_dependencies(repo_root: Path, source_abs: Path, source_rel: str) -> list[LocalDependency]:
    suffix = source_abs.suffix.lower()
    if suffix in {".py", ".pyi"}:
        return _collect_python_dependencies(repo_root, source_abs, source_rel)
    if suffix in {".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx"}:
        return _collect_js_dependencies(repo_root, source_abs, source_rel)
    return []


def _iter_guarded_code_files(repo_root: Path, policy: PathScopePolicy) -> Iterable[tuple[Path, str]]:
    root_resolved = repo_root.resolve()
    for current_root, dirnames, filenames in os.walk(root_resolved):
        current = Path(current_root)
        rel_root = _normalize_rel_path(current.relative_to(root_resolved).as_posix())
        if rel_root == ".":
            rel_root = ""

        kept_dirs: list[str] = []
        for dirname in dirnames:
            rel_dir = _normalize_rel_path(f"{rel_root}/{dirname}" if rel_root else dirname)
            if any(_path_matches_prefix(rel_dir, ignored) for ignored in policy.ignored_prefixes):
                continue
            kept_dirs.append(dirname)
        dirnames[:] = kept_dirs

        for filename in filenames:
            rel_path = _normalize_rel_path(f"{rel_root}/{filename}" if rel_root else filename)
            if _is_guarded_code_path(rel_path, policy):
                yield current / filename, rel_path


def summarize_path_scope_guard(
    repo_root: Path,
    guarded_prefixes: Sequence[str] | None = None,
    ignored_prefixes: Sequence[str] | None = None,
) -> RuleValidationSummary:
    policy = PathScopePolicy.from_raw(guarded_prefixes=guarded_prefixes, ignored_prefixes=ignored_prefixes)
    violations: list[LocalDependency] = []

    for source_abs, source_rel in _iter_guarded_code_files(repo_root, policy):
        dependencies = _collect_local_dependencies(repo_root, source_abs, source_rel)
        for dependency in dependencies:
            if _is_guarded_code_path(dependency.target_rel_path, policy):
                continue
            violations.append(dependency)

    reasons = [
        (
            "FRAMEWORK_VIOLATION: guarded import escapes configured path scope: "
            f"{item.source_rel_path}:{item.line} -> {item.target_rel_path} "
            f"(specifier={item.specifier})"
        )
        for item in violations[:_MAX_REASONS]
    ]
    outcome = RuleValidationOutcome(
        rule_id="FRAMEWORK_SCOPE_IMPORT_GUARD",
        name="guarded path import scope",
        passed=not violations,
        reasons=tuple(reasons),
        evidence={
            "guarded_prefixes": list(policy.guarded_prefixes),
            "ignored_prefixes": list(policy.ignored_prefixes),
            "violation_count": len(violations),
            "violations": [item.to_dict() for item in violations[:_MAX_EVIDENCE_ITEMS]],
        },
    )
    return RuleValidationSummary(module_id="framework.path_scope_guard", rules=(outcome,))
