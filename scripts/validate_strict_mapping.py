from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "standards/mapping_registry.json"

REQUIRED_LEVELS = ("L0", "L1", "L2", "L3")
ASSIGN_CALL_PATTERN = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([A-Za-z_][A-Za-z0-9_]*)\(\s*$"
)


Issue = dict[str, Any]


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


def find_top_down_rule_line(registry_text: str, src_level: str) -> int:
    token = f'"from": "{src_level}"'
    return find_line(registry_text, token)


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
    standards_dir = REPO_ROOT / "standards"
    if not standards_dir.exists():
        return []

    excluded_names = {
        "framework_design_standard.md",
        "框架设计核心标准.md",
    }
    results: list[str] = []
    for path in sorted(standards_dir.glob("*.md")):
        file_name = path.name
        if file_name in excluded_names:
            continue
        if not (
            file_name.endswith("_framework_standard.md")
            or file_name.endswith("框架标准.md")
        ):
            continue
        results.append(path.relative_to(REPO_ROOT).as_posix())
    return results


def validate_registry_structure(registry: dict[str, Any], registry_text: str) -> list[Issue]:
    issues: list[Issue] = []

    levels = registry.get("levels")
    if not isinstance(levels, dict):
        issues.append(
            make_issue(
                "mapping_registry.json: levels must be an object",
                REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                find_line(registry_text, '"levels"'),
                code="REGISTRY_LEVELS_TYPE",
            )
        )
        return issues

    for level in REQUIRED_LEVELS:
        files = levels.get(level)
        if not isinstance(files, list) or not files:
            issues.append(
                make_issue(
                    f"mapping_registry.json: {level} must map to a non-empty file list",
                    REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                    find_line(registry_text, f'"{level}"'),
                    code="REGISTRY_LEVEL_EMPTY",
                )
            )

    for level in REQUIRED_LEVELS:
        for file_name in levels.get(level, []):
            file_path = REPO_ROOT / file_name
            if not file_path.exists():
                line = find_line(registry_text, file_name)
                issues.append(
                    make_issue(
                        f"mapping_registry.json: {level} references missing file: {file_name}",
                        REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                        line,
                        code="REGISTRY_MISSING_FILE",
                        related=[
                            {
                                "message": f"Expected file location: {file_name}",
                                "file": file_name,
                                "line": 1,
                                "column": 1,
                            }
                        ],
                    )
                )

    declared_l2 = set(levels.get("L2", []))
    for standard_file in discover_domain_standards():
        if standard_file not in declared_l2:
            issues.append(
                make_issue(
                    "mapping_registry.json: unregistered domain standard in standards/: "
                    f"{standard_file} (must be listed under L2)",
                    REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                    find_line(registry_text, '"L2"'),
                    code="REGISTRY_UNREGISTERED_DOMAIN",
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
        return issues

    mapping_ids: set[str] = set()
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

        for key in ("l0_anchor", "l1_anchor", "l2_anchor"):
            if not item.get(key):
                issues.append(
                    make_issue(
                        f"{map_id}: missing {key}",
                        REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                        find_mapping_key_line(registry_text, map_id, key),
                        code="REGISTRY_MAPPING_KEY_MISSING",
                    )
                )

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

    return issues


def validate_mapping_content(registry: dict[str, Any], registry_text: str) -> list[Issue]:
    issues: list[Issue] = []

    l0_doc = REPO_ROOT / registry["levels"]["L0"][0]
    l1_doc = REPO_ROOT / registry["levels"]["L1"][0]
    l2_doc = REPO_ROOT / registry["levels"]["L2"][0]

    l0_text = read_text(l0_doc)
    l1_text = read_text(l1_doc)
    l2_text = read_text(l2_doc)

    code_cache: dict[Path, str] = {}
    ast_cache: dict[Path, ast.AST] = {}

    for item in registry["mappings"]:
        map_id = item["id"]

        if item["l0_anchor"] not in l0_text:
            issues.append(
                make_issue(
                    f"{map_id}: l0_anchor not found in {l0_doc.relative_to(REPO_ROOT).as_posix()}",
                    REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                    find_mapping_key_line(registry_text, map_id, "l0_anchor"),
                    code="ANCHOR_L0_MISSING",
                    related=[
                        {
                            "message": "Expected anchor target file",
                            "file": l0_doc.relative_to(REPO_ROOT).as_posix(),
                            "line": 1,
                            "column": 1,
                        }
                    ],
                )
            )

        if item["l1_anchor"] not in l1_text:
            issues.append(
                make_issue(
                    f"{map_id}: l1_anchor not found in {l1_doc.relative_to(REPO_ROOT).as_posix()}",
                    REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                    find_mapping_key_line(registry_text, map_id, "l1_anchor"),
                    code="ANCHOR_L1_MISSING",
                    related=[
                        {
                            "message": "Expected anchor target file",
                            "file": l1_doc.relative_to(REPO_ROOT).as_posix(),
                            "line": 1,
                            "column": 1,
                        }
                    ],
                )
            )

        if item["l2_anchor"] not in l2_text:
            issues.append(
                make_issue(
                    f"{map_id}: l2_anchor not found in {l2_doc.relative_to(REPO_ROOT).as_posix()}",
                    REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                    find_mapping_key_line(registry_text, map_id, "l2_anchor"),
                    code="ANCHOR_L2_MISSING",
                    related=[
                        {
                            "message": "Expected anchor target file",
                            "file": l2_doc.relative_to(REPO_ROOT).as_posix(),
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


def validate_change_propagation(registry: dict[str, Any], registry_text: str, changed_files: set[str]) -> list[Issue]:
    issues: list[Issue] = []

    level_files: dict[str, set[str]] = {
        level: set(files) for level, files in registry["levels"].items()
    }

    def touched(level: str) -> bool:
        return bool(changed_files.intersection(level_files[level]))

    for rule in registry.get("top_down_update_rules", []):
        src = rule.get("from")
        targets = rule.get("must_update", [])
        if src not in level_files:
            continue
        if touched(src):
            for target in targets:
                if target in level_files and not touched(target):
                    missing_target = next(iter(level_files[target]))
                    issues.append(
                        make_issue(
                            f"change propagation violation: {src} changed but {target} not updated",
                            REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                            find_top_down_rule_line(registry_text, src),
                            code="PROPAGATION_MISSING_TARGET",
                            related=[
                                {
                                    "message": f"Expected changed file in {target}",
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
    issues.extend(validate_registry_structure(registry, registry_text))

    if not issues:
        try:
            issues.extend(validate_mapping_content(registry, registry_text))
        except Exception as exc:
            issues.append(
                make_issue(
                    str(exc),
                    REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                    1,
                    code="MAPPING_CONTENT_VALIDATION_FAILED",
                )
            )

    if args.check_changes:
        changed = collect_changed_files()
        issues.extend(validate_change_propagation(registry, registry_text, changed))

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
