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
REGISTRY_PATH = REPO_ROOT / "standards/L3/mapping_registry.json"

DEFAULT_LEVEL_ORDER = ("L0", "L1", "L2", "L3")
VALID_NODE_KINDS = {"layer", "file"}
REQUIRED_L1_ANCHORS_PER_L2 = (
    "## 1. 目标（Goal）",
    "## 2. 边界定义（Boundary）",
    "## 3. 模块（最小可行基，Module）",
    "## 4. 组合原则（Combination Principles）",
    "## 5. 验证（Verification）",
)
ASSIGN_CALL_PATTERN = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([A-Za-z_][A-Za-z0-9_]*)\(\s*$"
)

Issue = dict[str, Any]


@dataclass(frozen=True)
class ParsedRegistry:
    level_order: list[str]
    level_files: dict[str, set[str]]


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


def discover_domain_standards() -> list[str]:
    standards_dir = REPO_ROOT / "standards" / "L2"
    if not standards_dir.exists():
        return []
    return [
        path.relative_to(REPO_ROOT).as_posix()
        for path in sorted(standards_dir.glob("*.md"))
    ]


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

                if file_name.startswith("standards/") and not file_name.startswith(
                    f"standards/{level}/"
                ):
                    issues.append(
                        make_issue(
                            f"{node_id}: standards file must be under standards/{level}/",
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
                    "mapping_registry.json: unregistered domain standard in standards/L2/: "
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
        return issues, ParsedRegistry(level_order=level_order, level_files=level_files)

    mapping_ids: set[str] = set()
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

        l3_files = level_files.get("L3", set())
        for symbol_ref in symbols:
            file_name = symbol_ref.get("file") if isinstance(symbol_ref, dict) else None
            if not isinstance(file_name, str) or not file_name:
                continue
            if file_name not in l3_files:
                issues.append(
                    make_issue(
                        f"{map_id}: impl symbol file must be registered in L3 tree: {file_name}",
                        REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                        find_mapping_symbol_line(registry_text, map_id, file_name, ""),
                        code="REGISTRY_IMPL_FILE_NOT_IN_TREE",
                    )
                )

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
                            "file": "standards/L1/框架设计核心标准.md",
                            "line": 1,
                            "column": 1,
                        }
                    ],
                )
            )

    return issues, ParsedRegistry(level_order=level_order, level_files=level_files)


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
    level_index = {level: idx for idx, level in enumerate(level_order)}

    def touched(level: str) -> bool:
        return bool(changed_files.intersection(level_files.get(level, set())))

    for src_level in level_order:
        if src_level == "L3":
            continue
        if not touched(src_level):
            continue

        src_idx = level_index[src_level]
        for target_level in level_order[src_idx + 1 :]:
            target_candidates = level_files.get(target_level, set())
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
