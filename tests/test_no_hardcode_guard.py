from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ForbiddenPattern:
    name: str
    regex: re.Pattern[str]


TARGET_FILES = (
    REPO_ROOT / "src" / "project_runtime",
    REPO_ROOT / "src" / "frontend_kernel",
    REPO_ROOT / "tools" / "vscode" / "shelf-ai",
    REPO_ROOT / "scripts",
)

SUFFIXES = {".py", ".pyi", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx"}

FORBIDDEN_PATTERNS = (
    ForbiddenPattern(
        name="fixed_root_role_lookup",
        regex=re.compile(r'root_module_ids\.get\("(?:frontend|knowledge_base|backend)"\)'),
    ),
    ForbiddenPattern(
        name="fixed_project_file_fallback",
        regex=re.compile(
            r"(projects/project\.toml|"
            r"path\.join\(\s*(?:[^,\n]+,\s*)?[\"']projects[\"']\s*,\s*[\"']project\.toml[\"']\s*\)|"
            r"Path\(\s*[\"']projects[\"']\s*\)\s*/\s*[\"']project\.toml[\"']|"
            r"(?:REPO_ROOT|repo_root)\s*/\s*[\"']projects[\"']\s*/\s*[\"']project\.toml[\"'])"
        ),
    ),
    ForbiddenPattern(
        name="fixed_three_root_requirement_message",
        regex=re.compile(r"frontend, knowledge_base, and backend root modules are required"),
    ),
    ForbiddenPattern(
        name="module_id_if_branch",
        regex=re.compile(r"if\s+binding\.framework_module\.module_id\s*=="),
    ),
    ForbiddenPattern(
        name="framework_name_if_branch",
        regex=re.compile(r'if\s+module\.framework\s*==\s*"'),
    ),
)


def _iter_source_files() -> list[Path]:
    paths: list[Path] = []
    for root in TARGET_FILES:
        if not root.exists():
            continue
        for file_path in root.rglob("*"):
            if not file_path.is_file() or file_path.suffix not in SUFFIXES:
                continue
            if file_path.name.endswith(".min.js"):
                continue
            paths.append(file_path)
    return sorted(paths)


def _line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def test_no_forbidden_hardcode_patterns() -> None:
    violations: list[str] = []
    for file_path in _iter_source_files():
        text = file_path.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_PATTERNS:
            for match in forbidden.regex.finditer(text):
                line_no = _line_number(text, match.start())
                violations.append(
                    f"{file_path.relative_to(REPO_ROOT)}:{line_no}: {forbidden.name}: {match.group(0)}"
                )
    assert not violations, "\n".join(["forbidden hardcode patterns found:", *violations])
