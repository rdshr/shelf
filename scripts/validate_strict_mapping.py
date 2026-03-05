from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "mapping/mapping_registry.json"
FRAMEWORK_DIR = REPO_ROOT / "framework"
CORE_L1_STANDARD_FILE = "specs/框架设计核心标准.md"

DEFAULT_LEVEL_ORDER = ("L0", "L1", "L2", "L3")
VALID_NODE_KINDS = {"layer", "file"}
LEVEL_ALLOWED_PREFIXES: dict[str, tuple[str, ...]] = {
    "L0": ("specs/",),
    "L1": ("specs/",),
    "L2": ("framework/",),
    "L3": ("mapping/",),
}
REQUIRED_L1_ANCHORS_PER_L2 = (
    "## 1. 目标（Goal）",
    "## 2. 边界定义（Boundary）",
    "## 3. 最小可行基（Bases）",
    "## 4. 组合原则（Combination Principles）",
    "## 5. 验证（Verification）",
)
ASSIGN_CALL_PATTERN = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([A-Za-z_][A-Za-z0-9_]*)\(\s*$"
)
LAYER_DIR_PATTERN = re.compile(r"^L(\d+)$")
CANONICAL_BASE_ID_PATTERN = re.compile(r"^B(\d+)$")
CANONICAL_NODE_ID_PATTERN = re.compile(r"^L(\d+)\.M([A-Za-z0-9_-]+)\.B(\d+)$")
CANONICAL_CAPABILITY_ID_PATTERN = re.compile(r"^C(\d+)$")
CANONICAL_VERIFY_ID_PATTERN = re.compile(r"^V(\d+)$")
FRAMEWORK_L2_FILE_PATTERN = re.compile(r"^framework/[^/]+/L2/[^/]+\.md$")
LAYER_TAG_PATTERN = re.compile(r"<!--\s*@layer\s+([^>]*)-->", re.IGNORECASE)
BASE_TAG_PATTERN = re.compile(r"<!--\s*@base\s+([^>]*)-->", re.IGNORECASE)
COMPOSE_TAG_PATTERN = re.compile(r"<!--\s*@compose\s+([^>]*)-->", re.IGNORECASE)
FRAMEWORK_DIRECTIVE_LINE_PATTERN = re.compile(r"^\s*@framework(?:\s+(.*))?\s*$", re.MULTILINE)
FRAMEWORK_TITLE_LINE_PATTERN = re.compile(r"^\s*#\s+(.+?)\s*$", re.MULTILINE)
FRAMEWORK_NUMBERED_ITEM_PATTERN = re.compile(
    r"^\s*[-*]\s*`([A-Za-z][A-Za-z0-9]*(?:\.[0-9]+)?)`",
    re.MULTILINE,
)
FRAMEWORK_BOUNDARY_ITEM_LINE_PATTERN = re.compile(
    r"^\s*[-*]\s*`([A-Za-z][A-Za-z0-9]*)`\s+.*$",
    re.MULTILINE,
)
FRAMEWORK_BASE_ITEM_LINE_PATTERN = re.compile(
    r"^\s*[-*]\s*`(B\d+)`\s+.*$",
    re.MULTILINE,
)
FRAMEWORK_SOURCE_EXPR_PATTERN = re.compile(r"来源[：:]\s*`([^`]+)`")
FRAMEWORK_SOURCE_TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:\.[0-9]+)?")
FRAMEWORK_RULE_ID_PATTERN = re.compile(r"^R\d+(?:\.\d+)?$")
FRAMEWORK_RULE_TOP_LINE_PATTERN = re.compile(r"^\s*[-*]\s*`(R\d+)`\s*(.*)$")
FRAMEWORK_RULE_CHILD_LINE_PATTERN = re.compile(r"^\s*[-*]\s*`(R\d+\.\d+)`\s*(.*)$")
FRAMEWORK_BACKTICK_CONTENT_PATTERN = re.compile(r"`([^`]+)`")
FRAMEWORK_SYMBOL_TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
REQUIRED_LAYER_SECTIONS = (
    "## 1. 目标（Goal）",
    "## 2. 边界定义（Boundary）",
    "## 3. 最小可行基（Bases）",
    "## 4. 组合原则（Combination Principles）",
    "## 5. 验证（Verification）",
)
REQUIRED_FRAMEWORK_DIRECTIVE_SECTIONS = (
    "## 1. 能力声明",
    "## 2. 边界定义",
    "## 3. 最小可行基",
    "## 4. 基组合原则",
    "## 5. 验证",
)

Issue = dict[str, Any]


@dataclass(frozen=True)
class ParsedRegistry:
    level_order: list[str]
    level_files: dict[str, set[str]]
    impl_files: set[str]
    framework_layer_files: set[str]


def make_issue(
    message: str,
    file: str,
    line: int = 1,
    column: int = 1,
    code: str = "STRICT_MAPPING",
    related: list[dict[str, Any]] | None = None,
) -> Issue:
    return {
        "message": message,
        "file": file,
        "line": max(1, int(line)),
        "column": max(1, int(column)),
        "code": code,
        "related": related or [],
    }


def load_registry() -> tuple[dict[str, Any], str]:
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(f"missing mapping registry: {REGISTRY_PATH}")
    text = REGISTRY_PATH.read_text(encoding="utf-8")
    return json.loads(text), text


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"missing required file: {path}")
    return path.read_text(encoding="utf-8")


def find_line(text: str, pattern: str) -> int:
    lines = text.splitlines()
    for idx, line in enumerate(lines, start=1):
        if pattern in line:
            return idx
    return 1


def get_mapping_block_bounds(registry_text: str, map_id: str) -> tuple[int, int]:
    lines = registry_text.splitlines()
    start = 1
    end = len(lines)

    id_token = f'"id": "{map_id}"'
    for idx, line in enumerate(lines, start=1):
        if id_token in line:
            start = idx
            break

    for idx in range(start + 1, len(lines) + 1):
        if '"id": "' in lines[idx - 1]:
            end = idx - 1
            break

    return start, end


def find_mapping_key_line(registry_text: str, map_id: str, key: str) -> int:
    lines = registry_text.splitlines()
    start, end = get_mapping_block_bounds(registry_text, map_id)
    key_token = f'"{key}"'
    for idx in range(start, end + 1):
        if key_token in lines[idx - 1]:
            return idx
    return start


def find_mapping_symbol_line(registry_text: str, map_id: str, file_name: str, symbol: str) -> int:
    lines = registry_text.splitlines()
    start, end = get_mapping_block_bounds(registry_text, map_id)
    for idx in range(start, end + 1):
        line = lines[idx - 1]
        if file_name in line and symbol in line:
            return idx
    return start


def find_tree_node_line(registry_text: str, node_id: str) -> int:
    return find_line(registry_text, f'"id": "{node_id}"')


def find_level_order_line(registry_text: str, level: str) -> int:
    return find_line(registry_text, f'"{level}"')


def collect_changed_files() -> set[str]:
    changed: set[str] = set()

    commands = [
        ["git", "-c", "core.quotePath=false", "diff", "--name-only"],
        ["git", "-c", "core.quotePath=false", "diff", "--name-only", "--cached"],
    ]

    for cmd in commands:
        result = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            continue
        for line in result.stdout.splitlines():
            item = line.strip()
            if item:
                changed.add(item)

    untracked = subprocess.run(
        ["git", "-c", "core.quotePath=false", "ls-files", "--others", "--exclude-standard"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if untracked.returncode == 0:
        for line in untracked.stdout.splitlines():
            item = line.strip()
            if item:
                changed.add(item)

    return changed


def line_from_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def parse_tag_attributes(raw: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for part in raw.split(";"):
        token = part.strip()
        if not token or "=" not in token:
            continue
        key, value = token.split("=", 1)
        key_clean = key.strip()
        value_clean = value.strip().strip('"').strip("'")
        if key_clean:
            attrs[key_clean] = value_clean
    return attrs


def find_first_h1_title(text: str) -> tuple[int, str] | None:
    for match in FRAMEWORK_TITLE_LINE_PATTERN.finditer(text):
        line = line_from_offset(text, match.start())
        title = match.group(1).strip()
        if title:
            return line, title
    return None


def iter_section_bullet_lines(text: str, heading_prefix: str) -> list[tuple[int, str]]:
    lines = text.splitlines()
    in_section = False
    bullets: list[tuple[int, str]] = []
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("## "):
            if in_section:
                break
            if stripped.startswith(heading_prefix):
                in_section = True
            continue
        if not in_section:
            continue
        if stripped.startswith("- ") or stripped.startswith("* "):
            bullets.append((idx, line))
    return bullets


def extract_backtick_tokens(text: str) -> list[str]:
    tokens: list[str] = []
    for segment in FRAMEWORK_BACKTICK_CONTENT_PATTERN.findall(text):
        for token in FRAMEWORK_SYMBOL_TOKEN_PATTERN.findall(segment):
            tokens.append(token)
    return tokens


def iter_framework_layer_markdown() -> list[tuple[str, int, Path]]:
    docs: list[tuple[str, int, Path]] = []
    if not FRAMEWORK_DIR.exists():
        return docs

    for module_dir in sorted(FRAMEWORK_DIR.iterdir()):
        if not module_dir.is_dir():
            continue
        module_name = module_dir.name
        for layer_dir in sorted(module_dir.iterdir()):
            if not layer_dir.is_dir():
                continue
            layer_match = LAYER_DIR_PATTERN.fullmatch(layer_dir.name)
            if layer_match is None:
                continue
            layer_num = int(layer_match.group(1))
            for markdown_file in sorted(layer_dir.glob("*.md")):
                docs.append((module_name, layer_num, markdown_file))
    return docs


def is_allowed_level_path(level: str, file_name: str) -> bool:
    allowed_prefixes = LEVEL_ALLOWED_PREFIXES.get(level, ())
    if allowed_prefixes and not any(file_name.startswith(prefix) for prefix in allowed_prefixes):
        return False
    if level == "L2":
        return FRAMEWORK_L2_FILE_PATTERN.fullmatch(file_name) is not None
    return True


def discover_domain_standards() -> list[str]:
    standards: list[str] = []
    for module_name, layer_num, file_path in iter_framework_layer_markdown():
        if layer_num != 2:
            continue
        rel = file_path.relative_to(REPO_ROOT).as_posix()
        if FRAMEWORK_L2_FILE_PATTERN.fullmatch(rel) is not None:
            standards.append(rel)
    return sorted(set(standards))


def discover_framework_layer_docs() -> set[str]:
    return {path.relative_to(REPO_ROOT).as_posix() for _, _, path in iter_framework_layer_markdown()}


def validate_framework_layers() -> tuple[list[Issue], set[str]]:
    issues: list[Issue] = []
    layer_files: set[str] = set()
    node_origin: dict[str, tuple[str, int]] = {}
    compose_edges: list[tuple[str, str, str, int, str]] = []
    module_levels: dict[str, set[int]] = {}
    edge_pairs: set[tuple[str, str]] = set()
    valid_compose_edges: list[tuple[str, str]] = []
    framework_identifier_origin: dict[str, dict[str, tuple[str, int]]] = {}

    if not FRAMEWORK_DIR.exists():
        issues.append(
            make_issue(
                "framework directory is missing",
                REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                1,
                code="FRAMEWORK_DIR_MISSING",
            )
        )
        return issues, layer_files

    for module_dir in sorted(FRAMEWORK_DIR.iterdir()):
        if not module_dir.is_dir():
            continue
        module_name = module_dir.name
        levels = module_levels.setdefault(module_name, set())

        for entry in sorted(module_dir.iterdir()):
            if entry.is_file() and entry.suffix == ".md":
                rel = entry.relative_to(REPO_ROOT).as_posix()
                issues.append(
                    make_issue(
                        "framework module markdown must be under Lx directory",
                        rel,
                        1,
                        code="FRAMEWORK_FILE_NOT_IN_LAYER_DIR",
                    )
                )
            if entry.is_dir() and LAYER_DIR_PATTERN.fullmatch(entry.name) is None:
                rel = entry.relative_to(REPO_ROOT).as_posix()
                issues.append(
                    make_issue(
                        "framework module subdirectory must be named as Lx",
                        rel,
                        1,
                        code="FRAMEWORK_LAYER_DIR_NAME_INVALID",
                    )
                )

    for module_name, level_num, markdown_file in iter_framework_layer_markdown():
        rel_file = markdown_file.relative_to(REPO_ROOT).as_posix()
        layer_files.add(rel_file)
        module_levels.setdefault(module_name, set()).add(level_num)
        file_text = read_text(markdown_file)

        framework_directive_match = FRAMEWORK_DIRECTIVE_LINE_PATTERN.search(file_text)
        if framework_directive_match is not None:
            is_framework_directive_file = True
            directive_line = line_from_offset(file_text, framework_directive_match.start())
            directive_args = (framework_directive_match.group(1) or "").strip()
            if directive_args:
                issues.append(
                    make_issue(
                        "@framework must be plain directive without arguments",
                        rel_file,
                        directive_line,
                        code="FW002",
                    )
                )

            h1_title = find_first_h1_title(file_text)
            if h1_title is None:
                issues.append(
                    make_issue(
                        "framework file must have a level-1 title line",
                        rel_file,
                        1,
                        code="FW003",
                    )
                )
            else:
                title_line, title_text = h1_title
                if ":" not in title_text:
                    issues.append(
                        make_issue(
                            "framework title must include Chinese and English names separated by ':'",
                            rel_file,
                            title_line,
                            code="FW003",
                        )
                    )
                else:
                    left, right = title_text.split(":", 1)
                    if not left.strip() or not right.strip():
                        issues.append(
                            make_issue(
                                "framework title around ':' cannot be empty",
                                rel_file,
                                title_line,
                                code="FW003",
                            )
                        )
                    if re.search(r"[A-Za-z]", right) is None:
                        issues.append(
                            make_issue(
                                "framework title English part must contain ASCII letters",
                                rel_file,
                                title_line,
                                code="FW003",
                            )
                        )

            module_identifier_origin = framework_identifier_origin.setdefault(module_name, {})
            file_identifiers: set[str] = set()
            for id_match in FRAMEWORK_NUMBERED_ITEM_PATTERN.finditer(file_text):
                identifier = id_match.group(1)
                line_num = line_from_offset(file_text, id_match.start(1))
                file_identifiers.add(identifier)
                previous_origin = module_identifier_origin.get(identifier)
                if previous_origin is not None:
                    prev_file, prev_line = previous_origin
                    issues.append(
                        make_issue(
                            f"framework identifier must be unique inside module '{module_name}': {identifier}",
                            rel_file,
                            line_num,
                            code="FW010",
                            related=[
                                {
                                    "message": "previous declaration",
                                    "file": prev_file,
                                    "line": prev_line,
                                    "column": 1,
                                }
                            ],
                        )
                    )
                    continue
                module_identifier_origin[identifier] = (rel_file, line_num)

            for identifier in sorted(file_identifiers):
                origin = module_identifier_origin.get(identifier)
                line_num = origin[1] if origin and origin[0] == rel_file else 1
                if identifier.startswith("C") and CANONICAL_CAPABILITY_ID_PATTERN.fullmatch(identifier) is None:
                    issues.append(
                        make_issue(
                            f"invalid capability identifier format: {identifier}; expected C<number>",
                            rel_file,
                            line_num,
                            code="FW011",
                        )
                    )
                if identifier.startswith("B") and CANONICAL_BASE_ID_PATTERN.fullmatch(identifier) is None:
                    issues.append(
                        make_issue(
                            f"invalid base identifier format: {identifier}; expected B<number>",
                            rel_file,
                            line_num,
                            code="FW011",
                        )
                    )
                if identifier.startswith("V") and CANONICAL_VERIFY_ID_PATTERN.fullmatch(identifier) is None:
                    issues.append(
                        make_issue(
                            f"invalid verification identifier format: {identifier}; expected V<number>",
                            rel_file,
                            line_num,
                            code="FW011",
                        )
                    )

            capability_ids = {
                identifier
                for identifier in file_identifiers
                if CANONICAL_CAPABILITY_ID_PATTERN.fullmatch(identifier) is not None
            }
            boundary_ids: set[str] = set()

            for base_item_match in FRAMEWORK_BASE_ITEM_LINE_PATTERN.finditer(file_text):
                base_id = base_item_match.group(1)
                base_line = base_item_match.group(0)
                base_line_num = line_from_offset(file_text, base_item_match.start(1))
                source_match = FRAMEWORK_SOURCE_EXPR_PATTERN.search(base_line)
                if source_match is None:
                    issues.append(
                        make_issue(
                            f"{base_id} must declare source expression using '来源：`...`'",
                            rel_file,
                            base_line_num,
                            code="FW020",
                        )
                    )
                    continue

                source_expr = source_match.group(1).strip()
                if not source_expr:
                    issues.append(
                        make_issue(
                            f"{base_id} source expression cannot be empty",
                            rel_file,
                            base_line_num,
                            code="FW021",
                        )
                    )
                    continue

                source_tokens = FRAMEWORK_SOURCE_TOKEN_PATTERN.findall(source_expr)
                if not source_tokens:
                    issues.append(
                        make_issue(
                            f"{base_id} source expression is invalid: {source_expr}",
                            rel_file,
                            base_line_num,
                            code="FW021",
                        )
                    )
                    continue

                for token in source_tokens:
                    if token not in file_identifiers:
                        issues.append(
                            make_issue(
                                f"{base_id} source references undefined identifier: {token}",
                                rel_file,
                                base_line_num,
                                code="FW021",
                            )
                        )

                has_capability_ref = any(re.fullmatch(r"C\d+", token) for token in source_tokens)
                has_boundary_ref = any(not re.fullmatch(r"C\d+", token) for token in source_tokens)
                if not has_capability_ref or not has_boundary_ref:
                    issues.append(
                        make_issue(
                            (
                                f"{base_id} source must include at least one capability id (C*) "
                                "and one boundary/parameter identifier"
                            ),
                            rel_file,
                            base_line_num,
                            code="FW022",
                        )
                    )

            for boundary_line_num, boundary_line in iter_section_bullet_lines(file_text, "## 2. 边界定义"):
                boundary_match = FRAMEWORK_BOUNDARY_ITEM_LINE_PATTERN.match(boundary_line)
                if boundary_match is None:
                    continue
                boundary_id = boundary_match.group(1)
                boundary_ids.add(boundary_id)
                source_match = FRAMEWORK_SOURCE_EXPR_PATTERN.search(boundary_line)
                if source_match is None:
                    issues.append(
                        make_issue(
                            f"{boundary_id} must declare source expression using '来源：`...`'",
                            rel_file,
                            boundary_line_num,
                            code="FW030",
                        )
                    )
                    continue

                source_expr = source_match.group(1).strip()
                source_tokens = FRAMEWORK_SOURCE_TOKEN_PATTERN.findall(source_expr)
                if not source_tokens:
                    issues.append(
                        make_issue(
                            f"{boundary_id} source expression is invalid: {source_expr}",
                            rel_file,
                            boundary_line_num,
                            code="FW031",
                        )
                    )
                    continue

                for token in source_tokens:
                    if token not in file_identifiers:
                        issues.append(
                            make_issue(
                                f"{boundary_id} source references undefined identifier: {token}",
                                rel_file,
                                boundary_line_num,
                                code="FW031",
                            )
                        )

                has_capability_ref = any(re.fullmatch(r"C\d+", token) for token in source_tokens)
                if not has_capability_ref:
                    issues.append(
                        make_issue(
                            f"{boundary_id} source must include at least one capability id (C*)",
                            rel_file,
                            boundary_line_num,
                            code="FW031",
                        )
                    )

            for identifier in sorted(file_identifiers):
                if not identifier.startswith("R"):
                    continue
                if FRAMEWORK_RULE_ID_PATTERN.fullmatch(identifier) is None:
                    origin = module_identifier_origin.get(identifier)
                    line_num = origin[1] if origin and origin[0] == rel_file else 1
                    issues.append(
                        make_issue(
                            f"invalid rule identifier format: {identifier}; expected R<number> or R<number>.<number>",
                            rel_file,
                            line_num,
                            code="FW040",
                        )
                    )
                    continue
                if "." in identifier:
                    parent = identifier.split(".", 1)[0]
                    if parent not in file_identifiers:
                        origin = module_identifier_origin.get(identifier)
                        line_num = origin[1] if origin and origin[0] == rel_file else 1
                        issues.append(
                            make_issue(
                                f"rule child identifier requires parent declaration: {identifier} (missing {parent})",
                                rel_file,
                                line_num,
                                code="FW040",
                            )
                        )

            rule_top_lines: dict[str, int] = {}
            rule_child_items: dict[str, list[tuple[int, str]]] = {}
            rule_declared_symbols: dict[str, set[str]] = {}
            for rule_line_num, rule_line in iter_section_bullet_lines(file_text, "## 4. 基组合原则"):
                top_match = FRAMEWORK_RULE_TOP_LINE_PATTERN.match(rule_line)
                if top_match is not None:
                    parent_rule = top_match.group(1)
                    rule_top_lines.setdefault(parent_rule, rule_line_num)
                    rule_child_items.setdefault(parent_rule, [])
                    continue

                child_match = FRAMEWORK_RULE_CHILD_LINE_PATTERN.match(rule_line)
                if child_match is None:
                    continue
                child_rule = child_match.group(1)
                parent_rule = child_rule.split(".", 1)[0]
                content = child_match.group(2).strip()
                rule_child_items.setdefault(parent_rule, []).append((rule_line_num, content))

                if "输出结构" in content:
                    for token in extract_backtick_tokens(content):
                        if token in file_identifiers or token in boundary_ids:
                            continue
                        if (
                            CANONICAL_CAPABILITY_ID_PATTERN.fullmatch(token) is not None
                            or CANONICAL_BASE_ID_PATTERN.fullmatch(token) is not None
                            or FRAMEWORK_RULE_ID_PATTERN.fullmatch(token) is not None
                            or CANONICAL_VERIFY_ID_PATTERN.fullmatch(token) is not None
                        ):
                            continue
                        rule_declared_symbols.setdefault(parent_rule, set()).add(token)

            for parent_rule, parent_line in sorted(rule_top_lines.items()):
                child_items = rule_child_items.get(parent_rule, [])
                required_keywords = ("参与基", "组合方式", "输出能力", "边界绑定")
                for keyword in required_keywords:
                    if any(keyword in content for _, content in child_items):
                        continue
                    issues.append(
                        make_issue(
                            f"{parent_rule} missing required field: {keyword}",
                            rel_file,
                            parent_line,
                            code="FW041",
                        )
                    )

            for parent_rule, child_items in rule_child_items.items():
                for child_line, content in child_items:
                    if "输出能力" not in content:
                        continue
                    capability_refs = re.findall(r"C\d+", content)
                    if not capability_refs:
                        issues.append(
                            make_issue(
                                f"{parent_rule} output capability must reference at least one C*",
                                rel_file,
                                child_line,
                                code="FW050",
                            )
                        )
                        continue
                    for cap_id in capability_refs:
                        if cap_id in capability_ids:
                            continue
                        issues.append(
                            make_issue(
                                f"{parent_rule} output capability references undefined identifier: {cap_id}",
                                rel_file,
                                child_line,
                                code="FW050",
                            )
                        )

            declared_by_order: list[tuple[int, set[str]]] = []
            for parent_rule, symbols in rule_declared_symbols.items():
                try:
                    parent_num = int(parent_rule[1:])
                except ValueError:
                    continue
                declared_by_order.append((parent_num, symbols))
            declared_by_order.sort(key=lambda item: item[0])

            for parent_rule, child_items in rule_child_items.items():
                try:
                    parent_num = int(parent_rule[1:])
                except ValueError:
                    continue
                for child_line, content in child_items:
                    for token in extract_backtick_tokens(content):
                        if token in file_identifiers or token in boundary_ids:
                            continue
                        if (
                            CANONICAL_CAPABILITY_ID_PATTERN.fullmatch(token) is not None
                            or CANONICAL_BASE_ID_PATTERN.fullmatch(token) is not None
                            or FRAMEWORK_RULE_ID_PATTERN.fullmatch(token) is not None
                            or CANONICAL_VERIFY_ID_PATTERN.fullmatch(token) is not None
                        ):
                            continue

                        declared_in_same = token in rule_declared_symbols.get(parent_rule, set())
                        if declared_in_same:
                            continue

                        declared_in_upstream = False
                        for upstream_num, symbols in declared_by_order:
                            if upstream_num >= parent_num:
                                break
                            if token in symbols:
                                declared_in_upstream = True
                                break
                        if declared_in_upstream:
                            continue

                        issues.append(
                            make_issue(
                                (
                                    f"rule symbol '{token}' is used without declaration via '输出结构' "
                                    f"in same or upstream rules for {parent_rule}"
                                ),
                                rel_file,
                                child_line,
                                code="FW060",
                            )
                        )
        else:
            is_framework_directive_file = False

        required_headings = (
            REQUIRED_FRAMEWORK_DIRECTIVE_SECTIONS
            if is_framework_directive_file
            else REQUIRED_LAYER_SECTIONS
        )
        for required_heading in required_headings:
            if required_heading not in file_text:
                issues.append(
                    make_issue(
                        f"missing required section heading: {required_heading}",
                        rel_file,
                        1,
                        code="FRAMEWORK_LAYER_SECTION_MISSING",
                    )
                )

        if not is_framework_directive_file:
            layer_matches = list(LAYER_TAG_PATTERN.finditer(file_text))
            if not layer_matches:
                issues.append(
                    make_issue(
                        "missing @layer tag",
                        rel_file,
                        1,
                        code="FRAMEWORK_LAYER_TAG_MISSING",
                    )
                )
            else:
                attrs = parse_tag_attributes(layer_matches[0].group(1))
                expected_level = f"L{level_num}"
                declared_module = attrs.get("module")
                declared_level = attrs.get("level")
                if declared_module != module_name:
                    issues.append(
                        make_issue(
                            f"@layer module must be '{module_name}', got '{declared_module}'",
                            rel_file,
                            line_from_offset(file_text, layer_matches[0].start()),
                            code="FRAMEWORK_LAYER_TAG_MODULE_MISMATCH",
                        )
                    )
                if declared_level != expected_level:
                    issues.append(
                        make_issue(
                            f"@layer level must be '{expected_level}', got '{declared_level}'",
                            rel_file,
                            line_from_offset(file_text, layer_matches[0].start()),
                            code="FRAMEWORK_LAYER_TAG_LEVEL_MISMATCH",
                        )
                    )

            base_matches = list(BASE_TAG_PATTERN.finditer(file_text))
            if not base_matches:
                issues.append(
                    make_issue(
                        "missing @base tags",
                        rel_file,
                        1,
                        code="FRAMEWORK_BASE_TAG_MISSING",
                    )
                )
            for match in base_matches:
                attrs = parse_tag_attributes(match.group(1))
                base_id = attrs.get("id")
                line = line_from_offset(file_text, match.start())
                if base_id is None or CANONICAL_BASE_ID_PATTERN.fullmatch(base_id) is None:
                    issues.append(
                        make_issue(
                            f"invalid @base id: {base_id}",
                            rel_file,
                            line,
                            code="FRAMEWORK_BASE_ID_INVALID",
                        )
                    )
                    continue

                node_id = f"L{level_num}.M{module_name}.{base_id}"
                if node_id in node_origin:
                    prev_file, prev_line = node_origin[node_id]
                    issues.append(
                        make_issue(
                            f"duplicate canonical base node id: {node_id}",
                            rel_file,
                            line,
                            code="FRAMEWORK_BASE_NODE_DUP",
                            related=[
                                {
                                    "message": "previous declaration",
                                    "file": prev_file,
                                    "line": prev_line,
                                    "column": 1,
                                }
                            ],
                        )
                    )
                    continue
                node_origin[node_id] = (rel_file, line)

        for match in COMPOSE_TAG_PATTERN.finditer(file_text):
            attrs = parse_tag_attributes(match.group(1))
            src = attrs.get("from")
            dst = attrs.get("to")
            line = line_from_offset(file_text, match.start())
            if not src or not dst:
                issues.append(
                    make_issue(
                        "@compose requires from/to",
                        rel_file,
                        line,
                        code="FRAMEWORK_COMPOSE_TAG_INVALID",
                    )
                )
                continue
            compose_edges.append((src, dst, rel_file, line, module_name))

    for src, dst, rel_file, line, module_name in compose_edges:
        src_match = CANONICAL_NODE_ID_PATTERN.fullmatch(src)
        dst_match = CANONICAL_NODE_ID_PATTERN.fullmatch(dst)
        if src_match is None or dst_match is None:
            issues.append(
                make_issue(
                    f"@compose node id must match L{{X}}.M{{module}}.B{{n}}: from={src}, to={dst}",
                    rel_file,
                    line,
                    code="FRAMEWORK_COMPOSE_NODE_ID_INVALID",
                )
            )
            continue

        src_level, src_module = int(src_match.group(1)), src_match.group(2)
        dst_level, dst_module = int(dst_match.group(1)), dst_match.group(2)

        if src_module != dst_module:
            issues.append(
                make_issue(
                    f"cross-module composition is forbidden: {src_module} -> {dst_module}",
                    rel_file,
                    line,
                    code="FRAMEWORK_COMPOSE_CROSS_MODULE",
                )
            )
            continue

        if src_module != module_name:
            issues.append(
                make_issue(
                    f"@compose module mismatch with file module '{module_name}': from={src}",
                    rel_file,
                    line,
                    code="FRAMEWORK_COMPOSE_MODULE_MISMATCH",
                )
            )

        if src_level == dst_level:
            issues.append(
                make_issue(
                    f"same-level composition is forbidden: {src} -> {dst}",
                    rel_file,
                    line,
                    code="FRAMEWORK_COMPOSE_SAME_LEVEL",
                )
            )
            continue

        if dst_level != src_level + 1:
            issues.append(
                make_issue(
                    f"cross-level composition is forbidden: {src} -> {dst}; expected Lx->L(x+1)",
                    rel_file,
                    line,
                    code="FRAMEWORK_COMPOSE_CROSS_LEVEL",
                )
            )
            continue

        if src not in node_origin:
            issues.append(
                make_issue(
                    f"compose source node not declared: {src}",
                    rel_file,
                    line,
                    code="FRAMEWORK_COMPOSE_SOURCE_MISSING",
                )
            )
        if dst not in node_origin:
            issues.append(
                make_issue(
                    f"compose target node not declared: {dst}",
                    rel_file,
                    line,
                    code="FRAMEWORK_COMPOSE_TARGET_MISSING",
                )
            )
        edge_pairs.add((src, dst))
        valid_compose_edges.append((src, dst))

    for module_name, levels in module_levels.items():
        if not levels:
            continue
        if len(levels) > 1 and 0 not in levels:
            issues.append(
                make_issue(
                    f"module '{module_name}' has multi-layer docs but missing L0",
                    REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                    1,
                    code="FRAMEWORK_LAYER_ZERO_MISSING",
                )
            )
        for lower_level in sorted(levels):
            upper_level = lower_level + 1
            if upper_level not in levels:
                continue
            has_adjacent_edge = False
            for src, dst in edge_pairs:
                src_match = CANONICAL_NODE_ID_PATTERN.fullmatch(src)
                dst_match = CANONICAL_NODE_ID_PATTERN.fullmatch(dst)
                if src_match is None or dst_match is None:
                    continue
                if (
                    src_match.group(2) == module_name
                    and dst_match.group(2) == module_name
                    and int(src_match.group(1)) == lower_level
                    and int(dst_match.group(1)) == upper_level
                ):
                    has_adjacent_edge = True
                    break
            if not has_adjacent_edge:
                issues.append(
                    make_issue(
                        (
                            f"module '{module_name}' missing adjacent composition from "
                            f"L{lower_level} to L{upper_level}"
                        ),
                        REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                        1,
                        code="FRAMEWORK_COMPOSE_ADJACENT_MISSING",
                    )
                )

        module_node_ids: list[str] = []
        for node_id in node_origin:
            node_match = CANONICAL_NODE_ID_PATTERN.fullmatch(node_id)
            if node_match is None:
                continue
            if node_match.group(2) == module_name:
                module_node_ids.append(node_id)

        out_degree: dict[str, int] = {node_id: 0 for node_id in module_node_ids}
        in_degree: dict[str, int] = {node_id: 0 for node_id in module_node_ids}
        for src, dst in valid_compose_edges:
            src_match = CANONICAL_NODE_ID_PATTERN.fullmatch(src)
            dst_match = CANONICAL_NODE_ID_PATTERN.fullmatch(dst)
            if src_match is None or dst_match is None:
                continue
            if src_match.group(2) != module_name or dst_match.group(2) != module_name:
                continue
            out_degree[src] = out_degree.get(src, 0) + 1
            in_degree[dst] = in_degree.get(dst, 0) + 1

        for node_id in module_node_ids:
            node_match = CANONICAL_NODE_ID_PATTERN.fullmatch(node_id)
            if node_match is None:
                continue
            level_num = int(node_match.group(1))
            max_level = max(levels)
            if level_num == max_level:
                continue
            out_count = out_degree.get(node_id, 0)
            if out_count < 1:
                file_name, line_num = node_origin[node_id]
                issues.append(
                    make_issue(
                        (
                            f"downstream node must compose to at least one upstream module: "
                            f"{node_id}; outgoing={out_count}"
                        ),
                        file_name,
                        line_num,
                        code="FRAMEWORK_DAG_PARENT_MISSING",
                    )
                )

        for node_id in module_node_ids:
            node_match = CANONICAL_NODE_ID_PATTERN.fullmatch(node_id)
            if node_match is None:
                continue
            level_num = int(node_match.group(1))
            if level_num == 0:
                continue
            if (level_num - 1) not in levels:
                continue
            in_count = in_degree.get(node_id, 0)
            if in_count < 1:
                file_name, line_num = node_origin[node_id]
                issues.append(
                    make_issue(
                        f"upstream node must have at least one downstream child: {node_id}",
                        file_name,
                        line_num,
                        code="FRAMEWORK_TREE_CHILD_MISSING",
                    )
                )

        level_node_counts: dict[int, int] = {level: 0 for level in levels}
        for node_id in module_node_ids:
            node_match = CANONICAL_NODE_ID_PATTERN.fullmatch(node_id)
            if node_match is None:
                continue
            level_num = int(node_match.group(1))
            level_node_counts[level_num] = level_node_counts.get(level_num, 0) + 1

        strict_funnel_exists = False
        for lower_level in sorted(levels):
            upper_level = lower_level + 1
            if upper_level not in levels:
                continue
            lower_count = level_node_counts.get(lower_level, 0)
            upper_count = level_node_counts.get(upper_level, 0)
            if lower_count < upper_count:
                issues.append(
                    make_issue(
                        (
                            f"tree shape invalid for module '{module_name}': "
                            f"L{lower_level} node_count({lower_count}) must be >= "
                            f"L{upper_level} node_count({upper_count})"
                        ),
                        REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                        1,
                        code="FRAMEWORK_TREE_SHAPE_INVALID",
                    )
                )
            if lower_count > upper_count:
                strict_funnel_exists = True

        if len(levels) > 1 and not strict_funnel_exists:
            issues.append(
                make_issue(
                    (
                        f"tree shape too flat for module '{module_name}': expected at least one "
                        "adjacent level pair with fewer upstream nodes"
                    ),
                    REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                    1,
                    code="FRAMEWORK_TREE_SHAPE_FLAT",
                )
            )

    return issues, layer_files



def parse_level_order(registry: dict[str, Any], registry_text: str) -> tuple[list[str], list[Issue]]:
    issues: list[Issue] = []

    validation = registry.get("validation")
    if not isinstance(validation, dict):
        issues.append(
            make_issue(
                "mapping_registry.json: validation must be an object",
                REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                find_line(registry_text, '"validation"'),
                code="REGISTRY_VALIDATION_TYPE",
            )
        )
        return list(DEFAULT_LEVEL_ORDER), issues

    level_order = validation.get("level_order")
    if not isinstance(level_order, list) or not level_order:
        issues.append(
            make_issue(
                "mapping_registry.json: validation.level_order must be non-empty list",
                REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                find_line(registry_text, '"level_order"'),
                code="REGISTRY_LEVEL_ORDER_INVALID",
            )
        )
        return list(DEFAULT_LEVEL_ORDER), issues

    normalized: list[str] = []
    seen: set[str] = set()
    for level in level_order:
        if not isinstance(level, str) or level not in DEFAULT_LEVEL_ORDER:
            issues.append(
                make_issue(
                    f"mapping_registry.json: invalid level in validation.level_order: {level}",
                    REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                    find_line(registry_text, f'"{level}"') if isinstance(level, str) else 1,
                    code="REGISTRY_LEVEL_ORDER_ITEM_INVALID",
                )
            )
            continue
        if level in seen:
            issues.append(
                make_issue(
                    f"mapping_registry.json: duplicate level in validation.level_order: {level}",
                    REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                    find_line(registry_text, f'"{level}"'),
                    code="REGISTRY_LEVEL_ORDER_DUP",
                )
            )
            continue
        seen.add(level)
        normalized.append(level)

    if normalized != list(DEFAULT_LEVEL_ORDER):
        issues.append(
            make_issue(
                "mapping_registry.json: validation.level_order must be exactly [\"L0\", \"L1\", \"L2\", \"L3\"]",
                REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                find_line(registry_text, '"level_order"'),
                code="REGISTRY_LEVEL_ORDER_MISMATCH",
            )
        )
        return list(DEFAULT_LEVEL_ORDER), issues

    reverse_cmd = validation.get("reverse_validation_command")
    if not isinstance(reverse_cmd, str) or not reverse_cmd.strip():
        issues.append(
            make_issue(
                "mapping_registry.json: validation.reverse_validation_command must be non-empty string",
                REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                find_line(registry_text, '"reverse_validation_command"'),
                code="REGISTRY_REVERSE_COMMAND_INVALID",
            )
        )

    return normalized, issues


def walk_tree_and_collect(
    tree_root: dict[str, Any],
    registry_text: str,
    level_order: list[str],
) -> tuple[dict[str, set[str]], list[Issue]]:
    issues: list[Issue] = []
    level_index = {level: idx for idx, level in enumerate(level_order)}
    level_files: dict[str, set[str]] = {level: set() for level in level_order}
    seen_node_ids: set[str] = set()
    seen_files: set[str] = set()

    def walk(node: Any, parent_level: str | None = None) -> None:
        if not isinstance(node, dict):
            issues.append(
                make_issue(
                    "mapping_registry.json: tree node must be an object",
                    REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                    find_line(registry_text, '"tree"'),
                    code="TREE_NODE_TYPE_INVALID",
                )
            )
            return

        node_id = node.get("id")
        level = node.get("level")
        kind = node.get("kind")
        line = find_tree_node_line(registry_text, node_id) if isinstance(node_id, str) else 1

        if not isinstance(node_id, str) or not node_id.strip():
            issues.append(
                make_issue(
                    "mapping_registry.json: each tree node must have non-empty string id",
                    REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                    line,
                    code="TREE_NODE_ID_INVALID",
                )
            )
            return

        if node_id in seen_node_ids:
            issues.append(
                make_issue(
                    f"mapping_registry.json: duplicate tree node id: {node_id}",
                    REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                    line,
                    code="TREE_NODE_ID_DUP",
                )
            )
            return
        seen_node_ids.add(node_id)

        if not isinstance(level, str) or level not in level_index:
            issues.append(
                make_issue(
                    f"{node_id}: invalid or missing level '{level}'",
                    REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                    line,
                    code="TREE_NODE_LEVEL_INVALID",
                )
            )
            return

        if parent_level is not None:
            parent_idx = level_index[parent_level]
            current_idx = level_index[level]
            if current_idx < parent_idx or current_idx > parent_idx + 1:
                issues.append(
                    make_issue(
                        f"{node_id}: level jump is invalid ({parent_level} -> {level})",
                        REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                        line,
                        code="TREE_LEVEL_JUMP_INVALID",
                    )
                )

        if kind not in VALID_NODE_KINDS:
            issues.append(
                make_issue(
                    f"{node_id}: kind must be one of {sorted(VALID_NODE_KINDS)}",
                    REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                    line,
                    code="TREE_NODE_KIND_INVALID",
                )
            )
            kind = "layer"

        file_name = node.get("file")
        if kind == "file":
            if not isinstance(file_name, str) or not file_name.strip():
                issues.append(
                    make_issue(
                        f"{node_id}: file node must provide non-empty file",
                        REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                        line,
                        code="TREE_FILE_NODE_MISSING_FILE",
                    )
                )
            else:
                file_path = REPO_ROOT / file_name
                if not file_path.exists():
                    issues.append(
                        make_issue(
                            f"{node_id}: tree references missing file: {file_name}",
                            REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                            line,
                            code="TREE_FILE_MISSING",
                            related=[
                                {
                                    "message": "Expected file location",
                                    "file": file_name,
                                    "line": 1,
                                    "column": 1,
                                }
                            ],
                        )
                    )

                if file_name in seen_files:
                    issues.append(
                        make_issue(
                            f"{node_id}: duplicate file entry in tree: {file_name}",
                            REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                            line,
                            code="TREE_FILE_DUP",
                        )
                    )
                else:
                    seen_files.add(file_name)
                    level_files[level].add(file_name)

                if not is_allowed_level_path(level, file_name):
                    allowed_prefixes = LEVEL_ALLOWED_PREFIXES.get(level, ())
                    issues.append(
                        make_issue(
                            f"{node_id}: {level} file path is invalid for level constraints; allowed prefixes={list(allowed_prefixes)}",
                            REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                            line,
                            code="TREE_STANDARDS_PATH_LEVEL_MISMATCH",
                        )
                    )
        else:
            if "file" in node and node.get("file"):
                issues.append(
                    make_issue(
                        f"{node_id}: layer node must not define file",
                        REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                        line,
                        code="TREE_LAYER_WITH_FILE",
                    )
                )

        children = node.get("children", [])
        if not isinstance(children, list):
            issues.append(
                make_issue(
                    f"{node_id}: children must be a list",
                    REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                    line,
                    code="TREE_CHILDREN_TYPE_INVALID",
                )
            )
            return

        for child in children:
            walk(child, parent_level=level)

    walk(tree_root)
    return level_files, issues


def validate_registry_structure(
    registry: dict[str, Any], registry_text: str
) -> tuple[list[Issue], ParsedRegistry | None]:
    issues: list[Issue] = []
    framework_layer_files: set[str] = set()

    level_order, level_issues = parse_level_order(registry, registry_text)
    issues.extend(level_issues)

    tree = registry.get("tree")
    if not isinstance(tree, dict):
        issues.append(
            make_issue(
                "mapping_registry.json: tree must be an object",
                REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                find_line(registry_text, '"tree"'),
                code="REGISTRY_TREE_TYPE",
            )
        )
        return issues, None

    level_files, tree_issues = walk_tree_and_collect(tree, registry_text, level_order)
    issues.extend(tree_issues)

    for level in level_order:
        if not level_files.get(level):
            issues.append(
                make_issue(
                    f"mapping_registry.json: {level} must map to a non-empty file set in tree",
                    REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                    find_line(registry_text, f'"{level}"'),
                    code="TREE_LEVEL_EMPTY",
                )
            )

    declared_l2 = set(level_files.get("L2", set()))
    for standard_file in discover_domain_standards():
        if standard_file not in declared_l2:
            issues.append(
                make_issue(
                    "mapping_registry.json: unregistered domain standard under framework/*/L2/: "
                    f"{standard_file}",
                    REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                    find_line(registry_text, '"L2"'),
                    code="TREE_UNREGISTERED_DOMAIN",
                    related=[
                        {
                            "message": "New domain standard added here",
                            "file": standard_file,
                            "line": 1,
                            "column": 1,
                        }
                    ],
                )
            )

    framework_issues, framework_layer_files = validate_framework_layers()
    issues.extend(framework_issues)

    mappings = registry.get("mappings", [])
    if not isinstance(mappings, list) or not mappings:
        issues.append(
            make_issue(
                "mapping_registry.json: mappings must be a non-empty list",
                REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                find_line(registry_text, '"mappings"'),
                code="REGISTRY_MAPPINGS_EMPTY",
            )
            )
        return issues, ParsedRegistry(
            level_order=level_order,
            level_files=level_files,
            impl_files=set(),
            framework_layer_files=framework_layer_files,
        )

    mapping_ids: set[str] = set()
    impl_files: set[str] = set()
    l2_to_l1_anchors: dict[str, set[str]] = {
        file_name: set() for file_name in level_files.get("L2", set())
    }
    required_fields = (
        "l0_file",
        "l0_anchor",
        "l1_file",
        "l1_anchor",
        "l2_file",
        "l2_anchor",
    )

    for item in mappings:
        map_id = item.get("id")
        if not map_id or not isinstance(map_id, str):
            issues.append(
                make_issue(
                    "mapping_registry.json: each mapping must have string id",
                    REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                    find_line(registry_text, '"id"'),
                    code="REGISTRY_MAPPING_ID_INVALID",
                )
            )
            continue

        if map_id in mapping_ids:
            issues.append(
                make_issue(
                    f"mapping_registry.json: duplicate mapping id: {map_id}",
                    REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                    find_mapping_key_line(registry_text, map_id, "id"),
                    code="REGISTRY_MAPPING_ID_DUP",
                )
            )
        mapping_ids.add(map_id)

        for key in required_fields:
            if not item.get(key):
                issues.append(
                    make_issue(
                        f"{map_id}: missing {key}",
                        REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                        find_mapping_key_line(registry_text, map_id, key),
                        code="REGISTRY_MAPPING_KEY_MISSING",
                    )
                )

        for field, level in (("l0_file", "L0"), ("l1_file", "L1"), ("l2_file", "L2")):
            value = item.get(field)
            if isinstance(value, str) and value not in level_files.get(level, set()):
                issues.append(
                    make_issue(
                        f"{map_id}: {field} must reference a {level} file declared in tree",
                        REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                        find_mapping_key_line(registry_text, map_id, field),
                        code="REGISTRY_MAPPING_FILE_LEVEL_MISMATCH",
                    )
                )

        l2_file = item.get("l2_file")
        l1_anchor = item.get("l1_anchor")
        if isinstance(l2_file, str) and isinstance(l1_anchor, str):
            if l2_file in l2_to_l1_anchors:
                l2_to_l1_anchors[l2_file].add(l1_anchor)

        symbols = item.get("impl_symbols")
        if not isinstance(symbols, list) or not symbols:
            issues.append(
                make_issue(
                    f"{map_id}: impl_symbols must be non-empty list",
                    REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                    find_mapping_key_line(registry_text, map_id, "impl_symbols"),
                    code="REGISTRY_IMPL_SYMBOLS_EMPTY",
                )
            )
            continue

        for symbol_ref in symbols:
            if not isinstance(symbol_ref, dict):
                continue
            file_name = symbol_ref.get("file")
            if isinstance(file_name, str) and file_name:
                impl_files.add(file_name)

        # The framework tree is pure L0-L3 standards hierarchy.
        # Implementation files are validated via `impl_symbols` existence checks,
        # and do not need to appear as L3 tree nodes.

    for l2_file, anchors in l2_to_l1_anchors.items():
        if not anchors:
            issues.append(
                make_issue(
                    f"mapping_registry.json: L2 file has no mappings: {l2_file}",
                    REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                    find_line(registry_text, l2_file),
                    code="REGISTRY_L2_MAPPING_EMPTY",
                    related=[
                        {
                            "message": "Expected at least one mapping entry for this L2 file",
                            "file": l2_file,
                            "line": 1,
                            "column": 1,
                        }
                    ],
                )
            )
            continue

        missing_anchors = [
            anchor for anchor in REQUIRED_L1_ANCHORS_PER_L2 if anchor not in anchors
        ]
        if missing_anchors:
            issues.append(
                make_issue(
                    "mapping_registry.json: L2 file missing required mapping coverage: "
                    f"{l2_file}; missing={missing_anchors}",
                    REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                    find_line(registry_text, l2_file),
                    code="REGISTRY_L2_MAPPING_COVERAGE_MISSING",
                    related=[
                        {
                            "message": "Expected these L1 anchors to be mapped",
                            "file": CORE_L1_STANDARD_FILE,
                            "line": 1,
                            "column": 1,
                        }
                    ],
                )
            )

    return issues, ParsedRegistry(
        level_order=level_order,
        level_files=level_files,
        impl_files=impl_files,
        framework_layer_files=framework_layer_files,
    )


def validate_mapping_content(
    registry: dict[str, Any],
    registry_text: str,
    parsed_registry: ParsedRegistry,
) -> list[Issue]:
    del parsed_registry
    issues: list[Issue] = []

    code_cache: dict[Path, str] = {}
    ast_cache: dict[Path, ast.AST] = {}

    for item in registry["mappings"]:
        map_id = item["id"]
        anchor_pairs = (
            ("l0_file", "l0_anchor", "ANCHOR_L0_MISSING"),
            ("l1_file", "l1_anchor", "ANCHOR_L1_MISSING"),
            ("l2_file", "l2_anchor", "ANCHOR_L2_MISSING"),
        )

        for file_key, anchor_key, issue_code in anchor_pairs:
            file_name = item[file_key]
            anchor = item[anchor_key]
            file_path = REPO_ROOT / file_name
            file_text = read_text(file_path)
            if anchor not in file_text:
                issues.append(
                    make_issue(
                        f"{map_id}: {anchor_key} not found in {file_name}",
                        REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                        find_mapping_key_line(registry_text, map_id, anchor_key),
                        code=issue_code,
                        related=[
                            {
                                "message": "Expected anchor target file",
                                "file": file_name,
                                "line": 1,
                                "column": 1,
                            }
                        ],
                    )
                )

        for symbol_ref in item["impl_symbols"]:
            file_name = symbol_ref.get("file")
            symbol = symbol_ref.get("symbol")

            if not file_name or not symbol:
                issues.append(
                    make_issue(
                        f"{map_id}: invalid impl symbol ref: {symbol_ref}",
                        REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                        find_mapping_key_line(registry_text, map_id, "impl_symbols"),
                        code="IMPL_SYMBOL_REF_INVALID",
                    )
                )
                continue

            file_path = REPO_ROOT / file_name
            if file_path not in code_cache:
                code_cache[file_path] = read_text(file_path)
            if file_path.suffix == ".py" and file_path not in ast_cache:
                ast_cache[file_path] = ast.parse(code_cache[file_path], filename=file_name)

            if not symbol_exists(symbol, file_path, code_cache[file_path], ast_cache.get(file_path)):
                issues.append(
                    make_issue(
                        f"{map_id}: symbol '{symbol}' not found in {file_name}",
                        REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                        find_mapping_symbol_line(registry_text, map_id, file_name, symbol),
                        code="IMPL_SYMBOL_MISSING",
                        related=[
                            {
                                "message": "Expected implementation file",
                                "file": file_name,
                                "line": 1,
                                "column": 1,
                            }
                        ],
                    )
                )

    return issues


def symbol_exists(symbol: str, file_path: Path, source_text: str, parsed_ast: ast.AST | None) -> bool:
    if file_path.suffix != ".py" or parsed_ast is None:
        return symbol in source_text

    symbol = symbol.strip()

    if symbol.startswith("class "):
        class_name = symbol[len("class ") :].strip()
        return python_class_exists(parsed_ast, class_name)

    if symbol.startswith("def "):
        func_part = symbol[len("def ") :].strip()
        func_name = func_part.split("(", 1)[0].strip()
        return python_function_exists(parsed_ast, func_name)

    assign_call_match = ASSIGN_CALL_PATTERN.match(symbol)
    if assign_call_match:
        target_name = assign_call_match.group(1)
        func_name = assign_call_match.group(2)
        return python_assign_call_exists(parsed_ast, target_name, func_name)

    return symbol in source_text


def python_class_exists(tree: ast.AST, class_name: str) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return True
    return False


def python_function_exists(tree: ast.AST, func_name: str) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
            return True
    return False


def python_assign_call_exists(tree: ast.AST, target_name: str, func_name: str) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue

        if not node.targets:
            continue
        first_target = node.targets[0]
        if not isinstance(first_target, ast.Name) or first_target.id != target_name:
            continue

        if not isinstance(node.value, ast.Call):
            continue

        called = node.value.func
        if isinstance(called, ast.Name) and called.id == func_name:
            return True

    return False


def validate_change_propagation(
    registry_text: str,
    parsed_registry: ParsedRegistry,
    changed_files: set[str],
) -> list[Issue]:
    issues: list[Issue] = []

    level_order = parsed_registry.level_order
    level_files = parsed_registry.level_files
    impl_files = parsed_registry.impl_files
    framework_layer_files = parsed_registry.framework_layer_files
    level_index = {level: idx for idx, level in enumerate(level_order)}

    def touched(level: str) -> bool:
        candidates = set(level_files.get(level, set()))
        if level == "L2":
            candidates.update(framework_layer_files)
        if level == "L3":
            candidates.update(impl_files)
        return bool(changed_files.intersection(candidates))

    for src_level in level_order:
        if src_level == "L3":
            continue
        if not touched(src_level):
            continue

        src_idx = level_index[src_level]
        for target_level in level_order[src_idx + 1 :]:
            target_candidates = set(level_files.get(target_level, set()))
            if target_level == "L3":
                target_candidates.update(impl_files)
            if not target_candidates:
                continue
            if touched(target_level):
                continue

            missing_target = sorted(target_candidates)[0]
            issues.append(
                make_issue(
                    f"change propagation violation: {src_level} changed but {target_level} not updated",
                    REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                    find_level_order_line(registry_text, src_level),
                    code="PROPAGATION_MISSING_TARGET",
                    related=[
                        {
                            "message": f"Expected changed file in {target_level}",
                            "file": missing_target,
                            "line": 1,
                            "column": 1,
                        }
                    ],
                )
            )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate strict multi-level mapping between standards and code."
    )
    parser.add_argument(
        "--check-changes",
        action="store_true",
        help="validate top-down change propagation on current git diff",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="output result as JSON",
    )
    args = parser.parse_args()

    try:
        registry, registry_text = load_registry()
    except Exception as exc:
        payload = {
            "passed": False,
            "checked_changes": args.check_changes,
            "errors": [
                make_issue(
                    str(exc),
                    REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                    1,
                    code="REGISTRY_LOAD_FAILED",
                )
            ],
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(f"[FAIL] {exc}")
        return 1

    issues: list[Issue] = []
    structure_issues, parsed_registry = validate_registry_structure(registry, registry_text)
    issues.extend(structure_issues)

    if not issues and parsed_registry is not None:
        try:
            issues.extend(validate_mapping_content(registry, registry_text, parsed_registry))
        except Exception as exc:
            issues.append(
                make_issue(
                    str(exc),
                    REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                    1,
                    code="MAPPING_CONTENT_VALIDATION_FAILED",
                )
            )

    if args.check_changes and parsed_registry is not None:
        changed = collect_changed_files()
        issues.extend(validate_change_propagation(registry_text, parsed_registry, changed))

    passed = len(issues) == 0
    result_payload = {
        "passed": passed,
        "checked_changes": args.check_changes,
        "errors": issues,
    }

    if args.json:
        print(json.dumps(result_payload, ensure_ascii=False))
        return 0 if passed else 1

    if not passed:
        print("[FAIL] strict mapping validation failed:")
        for issue in issues:
            print(f"- {issue['file']}:{issue['line']}: {issue['message']}")
        return 1

    print("[PASS] strict mapping validation passed")
    if args.check_changes:
        print("[PASS] change propagation check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
