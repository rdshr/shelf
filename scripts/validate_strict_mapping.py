from __future__ import annotations

import argparse
import ast
from importlib import import_module
import json
import re
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    _hierarchy_module = import_module("scripts.generate_module_hierarchy_html")
except ModuleNotFoundError:
    _hierarchy_module = import_module("generate_module_hierarchy_html")

load_hierarchy_graph = _hierarchy_module.load_hierarchy
render_hierarchy_html = _hierarchy_module.render_html

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from project_runtime import (
    detect_project_template_id,
    discover_framework_driven_projects,
    load_registered_project,
    materialize_registered_project,
    resolve_project_template_registration,
)
from project_runtime.project_governance import (
    build_project_discovery_audit,
    render_project_discovery_audit_markdown,
)
from project_runtime.governance import (
    compare_project_to_tree,
    parse_governance_tree,
    validate_tree_closure,
)
from standards_tree import build_standards_tree, level_files_from_tree
from workspace_governance import (
    DEFAULT_PROJECT_DISCOVERY_AUDIT_JSON,
    DEFAULT_PROJECT_DISCOVERY_AUDIT_MD,
    DEFAULT_WORKSPACE_GOVERNANCE_HTML,
    DEFAULT_WORKSPACE_GOVERNANCE_JSON,
    build_workspace_governance_payload,
    parse_workspace_governance_payload,
    resolve_workspace_change_context,
)

REGISTRY_PATH = REPO_ROOT / "mapping/mapping_registry.json"
FRAMEWORK_DIR = REPO_ROOT / "framework"
PROJECTS_DIR = REPO_ROOT / "projects"
CORE_L1_STANDARD_FILE = "specs/框架设计核心标准.md"
COMPATIBILITY_FACADE_FILE = "src/shelf_framework.py"
SHELF_DOMAIN_FILE = "src/shelf_domain.py"

DEFAULT_LEVEL_ORDER = ("L0", "L1", "L2", "L3")
VALID_NODE_KINDS = {"layer", "file"}
LEVEL_ALLOWED_PREFIXES: dict[str, tuple[str, ...]] = {
    "L0": ("specs/",),
    "L1": ("specs/",),
    "L2": ("framework/",),
    "L3": ("mapping/",),
}
REQUIRED_L1_ANCHORS_PER_L2 = (
    "## 1. 能力声明（Capability Statement）",
    "## 2. 边界定义（Boundary）",
    "## 3. 最小可行基（Bases）",
    "## 4. 组合原则（Combination Principles）",
    "## 5. 验证（Verification）",
)
ASSIGN_CALL_PATTERN = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([A-Za-z_][A-Za-z0-9_]*)\(\s*$"
)
LAYER_DIR_PATTERN = re.compile(r"^L(\d+)$")
FRAMEWORK_FILE_LEVEL_PREFIX_PATTERN = re.compile(r"^L(\d+)-M(\d+)-[^/]+\.md$")
CANONICAL_BASE_ID_PATTERN = re.compile(r"^B(\d+)$")
CANONICAL_CAPABILITY_ID_PATTERN = re.compile(r"^C(\d+)$")
CANONICAL_VERIFY_ID_PATTERN = re.compile(r"^V(\d+)$")
FRAMEWORK_L2_FILE_PATTERN = re.compile(r"^framework/[^/]+/L2-M\d+-[^/]+\.md$")
FRAMEWORK_DIRECTIVE_LINE_PATTERN = re.compile(
    r"^[ \t]*@framework(?:[ \t]+([^\r\n]+))?[ \t]*$",
    re.MULTILINE,
)
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
FRAMEWORK_LEGACY_UPSTREAM_CLAUSE_PATTERN = re.compile(r"上游模块[：:]")
FRAMEWORK_SOURCE_TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:\.[0-9]+)?")
FRAMEWORK_INLINE_UPSTREAM_TERM_PATTERN = re.compile(
    r"^(?:(?P<framework>[A-Za-z][A-Za-z0-9_-]*)\.)?L(?P<level>\d+)\.M(?P<module>\d+)(?:\[(?P<rules>.*?)\])?$"
)
FRAMEWORK_RULE_ID_PATTERN = re.compile(r"^R\d+(?:\.\d+)?$")
FRAMEWORK_RULE_TOP_LINE_PATTERN = re.compile(r"^\s*[-*]\s*`(R\d+)`\s*(.*)$")
FRAMEWORK_RULE_CHILD_LINE_PATTERN = re.compile(r"^\s*[-*]\s*`(R\d+\.\d+)`\s*(.*)$")
FRAMEWORK_BACKTICK_CONTENT_PATTERN = re.compile(r"`([^`]+)`")
FRAMEWORK_SYMBOL_TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
REQUIRED_FRAMEWORK_DIRECTIVE_SECTIONS = (
    "## 1. 能力声明",
    "## 2. 边界定义",
    "## 3. 最小可行基",
    "## 4. 基组合原则",
    "## 5. 验证",
)
PROJECT_ALLOWED_TOP_LEVEL_DIRS = {"assets", "generated"}
PROJECT_ALLOWED_ROOT_FILES = {"product_spec.toml", "implementation_config.toml"}
PROJECT_ALLOWED_DOC_SUFFIXES = {".md"}

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


def discover_project_product_spec_files(projects_dir: Path = PROJECTS_DIR) -> list[Path]:
    return [
        (REPO_ROOT / item.product_spec_file).resolve()
        for item in discover_framework_driven_projects(projects_dir)
    ]


def implementation_config_path_for(product_spec_file: Path) -> Path:
    return product_spec_file.parent / "implementation_config.toml"


def expected_generated_files_for(product_spec_file: Path) -> tuple[str, ...]:
    implementation_config_file = implementation_config_path_for(product_spec_file)
    _, data = _load_toml_text_and_data(implementation_config_file)
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, dict):
        raise ValueError("implementation_config.toml must define [artifacts]")
    names: list[str] = []
    for key in (
        "framework_ir_json",
        "product_spec_json",
        "implementation_bundle_py",
        "generation_manifest_json",
        "governance_manifest_json",
        "governance_tree_json",
        "strict_zone_report_json",
        "object_coverage_report_json",
    ):
        value = artifacts.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"implementation_config.toml missing artifacts.{key}")
        names.append(value.strip())
    if len(set(names)) != len(names):
        raise ValueError("artifact file names in implementation_config.toml must be unique")
    return tuple(names)


def _read_file_bytes(path: Path) -> bytes:
    return path.read_bytes()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must decode into an object")
    return payload


def _load_toml_text_and_data(path: Path) -> tuple[str, dict[str, Any]]:
    text = read_text(path)
    data = tomllib.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must decode into a table")
    return text, data


_MISSING = object()


def _collect_leaf_paths(payload: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    items: dict[str, Any] = {}
    for key, value in payload.items():
        dotted = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            items.update(_collect_leaf_paths(value, dotted))
            continue
        items[dotted] = value
    return items


def _get_dotted_value(payload: dict[str, Any], dotted_path: str) -> Any:
    current: Any = payload
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return _MISSING
        current = current[part]
    return current


def _derived_generated_artifacts_payload(
    product_spec_file: Path,
    implementation_data: dict[str, Any],
) -> dict[str, str]:
    artifacts = implementation_data.get("artifacts")
    if not isinstance(artifacts, dict):
        raise ValueError("implementation_config.toml must define [artifacts]")
    generated_dir = product_spec_file.parent / "generated"
    rel_generated_dir = generated_dir.relative_to(REPO_ROOT).as_posix()

    def rel_path(name_key: str) -> str:
        value = artifacts.get(name_key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"implementation_config.toml missing artifacts.{name_key}")
        return f"{rel_generated_dir}/{value.strip()}"

    return {
        "directory": rel_generated_dir,
        "framework_ir_json": rel_path("framework_ir_json"),
        "product_spec_json": rel_path("product_spec_json"),
        "implementation_bundle_py": rel_path("implementation_bundle_py"),
        "generation_manifest_json": rel_path("generation_manifest_json"),
        "governance_manifest_json": rel_path("governance_manifest_json"),
        "governance_tree_json": rel_path("governance_tree_json"),
        "strict_zone_report_json": rel_path("strict_zone_report_json"),
        "object_coverage_report_json": rel_path("object_coverage_report_json"),
    }


def _relation_matches(relation: str, config_value: Any, target_value: Any) -> bool:
    if relation == "equals":
        return target_value == config_value
    if relation == "basename":
        return Path(str(target_value)).name == str(config_value)
    raise ValueError(f"unsupported configuration effect relation: {relation}")


def _validate_project_toml_layout(
    file_path: Path,
    *,
    required_top_level_keys: set[str],
    allowed_top_level_keys: set[str],
    required_nested_tables: dict[str, set[str]],
    allowed_nested_tables: dict[str, set[str]],
    parse_error_code: str,
    missing_section_code: str,
    unknown_section_code: str,
    missing_nested_code: str,
    unknown_nested_code: str,
    kind_label: str,
) -> list[Issue]:
    issues: list[Issue] = []
    rel_file = file_path.relative_to(REPO_ROOT).as_posix()
    try:
        text, data = _load_toml_text_and_data(file_path)
    except Exception as exc:
        issues.append(
            make_issue(
                f"failed to parse {kind_label}: {exc}",
                rel_file,
                1,
                code=parse_error_code,
            )
        )
        return issues

    top_level_keys = set(data)
    for key in sorted(required_top_level_keys - top_level_keys):
        issues.append(
            make_issue(
                f"missing required {kind_label} section or array: {key}",
                rel_file,
                1,
                code=missing_section_code,
            )
        )

    for key in sorted(top_level_keys - allowed_top_level_keys):
        line = find_line(text, f"[{key}]")
        if line == 1:
            line = find_line(text, f"[[{key}]]")
        issues.append(
            make_issue(
                f"unknown {kind_label} top-level section: {key}",
                rel_file,
                line,
                code=unknown_section_code,
            )
        )

    for parent, required_children in required_nested_tables.items():
        parent_value = data.get(parent)
        if not isinstance(parent_value, dict):
            continue
        nested_table_keys = {key for key, value in parent_value.items() if isinstance(value, dict)}
        for child in sorted(required_children - nested_table_keys):
            issues.append(
                make_issue(
                    f"missing required nested {kind_label} section: [{parent}.{child}]",
                    rel_file,
                    find_line(text, f"[{parent}]"),
                    code=missing_nested_code,
                )
            )
        allowed_children = allowed_nested_tables.get(parent, set())
        for child in sorted(nested_table_keys - allowed_children):
            issues.append(
                make_issue(
                    f"unknown nested {kind_label} section: [{parent}.{child}]",
                    rel_file,
                    find_line(text, f"[{parent}.{child}]"),
                    code=unknown_nested_code,
                )
            )

    return issues


def validate_project_configuration_layout(product_spec_files: list[Path] | None = None) -> list[Issue]:
    issues: list[Issue] = []
    project_product_spec_files = product_spec_files or discover_project_product_spec_files()
    if not project_product_spec_files:
        return issues

    for product_spec_file in project_product_spec_files:
        rel_product_spec_file = product_spec_file.relative_to(REPO_ROOT).as_posix()
        try:
            template_id = detect_project_template_id(product_spec_file)
            registration = resolve_project_template_registration(product_spec_file)
        except Exception as exc:
            issues.append(
                make_issue(
                    str(exc),
                    rel_product_spec_file,
                    find_line(read_text(product_spec_file), 'template = "'),
                    code="PROJECT_TEMPLATE_UNSUPPORTED",
                )
            )
            continue

        product_spec_layout = registration.product_spec_layout
        issues.extend(
            _validate_project_toml_layout(
                product_spec_file,
                required_top_level_keys=set(product_spec_layout.required_top_level_keys),
                allowed_top_level_keys=set(product_spec_layout.allowed_top_level_keys),
                required_nested_tables={
                    key: set(value) for key, value in product_spec_layout.required_nested_tables.items()
                },
                allowed_nested_tables={
                    key: set(value) for key, value in product_spec_layout.allowed_nested_tables.items()
                },
                parse_error_code="PROJECT_PRODUCT_SPEC_PARSE_FAILED",
                missing_section_code="PROJECT_PRODUCT_SPEC_SECTION_MISSING",
                unknown_section_code="PROJECT_PRODUCT_SPEC_SECTION_UNKNOWN",
                missing_nested_code="PROJECT_PRODUCT_SPEC_NESTED_SECTION_MISSING",
                unknown_nested_code="PROJECT_PRODUCT_SPEC_NESTED_SECTION_UNKNOWN",
                kind_label="product_spec.toml",
            )
        )
        implementation_config_file = implementation_config_path_for(product_spec_file)
        if not implementation_config_file.exists():
            issues.append(
                make_issue(
                    "missing implementation_config.toml next to product_spec.toml",
                    product_spec_file.relative_to(REPO_ROOT).as_posix(),
                    1,
                    code="PROJECT_IMPLEMENTATION_CONFIG_MISSING",
                    related=[
                        {
                            "message": "Expected implementation config",
                            "file": implementation_config_file.relative_to(REPO_ROOT).as_posix(),
                            "line": 1,
                            "column": 1,
                        }
                    ],
                )
            )
            continue
        implementation_layout = registration.implementation_config_layout
        issues.extend(
            _validate_project_toml_layout(
                implementation_config_file,
                required_top_level_keys=set(implementation_layout.required_top_level_keys),
                allowed_top_level_keys=set(implementation_layout.allowed_top_level_keys),
                required_nested_tables={
                    key: set(value) for key, value in implementation_layout.required_nested_tables.items()
                },
                allowed_nested_tables={
                    key: set(value) for key, value in implementation_layout.allowed_nested_tables.items()
                },
                parse_error_code="PROJECT_IMPLEMENTATION_CONFIG_PARSE_FAILED",
                missing_section_code="PROJECT_IMPLEMENTATION_CONFIG_SECTION_MISSING",
                unknown_section_code="PROJECT_IMPLEMENTATION_CONFIG_SECTION_UNKNOWN",
                missing_nested_code="PROJECT_IMPLEMENTATION_CONFIG_NESTED_SECTION_MISSING",
                unknown_nested_code="PROJECT_IMPLEMENTATION_CONFIG_NESTED_SECTION_UNKNOWN",
                kind_label="implementation_config.toml",
            )
        )
    return issues


def validate_project_generation_discipline(
    product_spec_files: list[Path] | None = None,
) -> list[Issue]:
    issues: list[Issue] = []
    project_product_spec_files = product_spec_files or discover_project_product_spec_files()
    if not project_product_spec_files:
        return issues

    issues.extend(validate_project_configuration_layout(project_product_spec_files))

    for product_spec_file in project_product_spec_files:
        product_spec_file = product_spec_file.resolve()
        project_dir = product_spec_file.parent
        rel_product_spec_file = product_spec_file.relative_to(REPO_ROOT).as_posix()
        implementation_config_file = implementation_config_path_for(product_spec_file)
        rel_implementation_config_file = implementation_config_file.relative_to(REPO_ROOT).as_posix()
        try:
            expected_generated_files = expected_generated_files_for(product_spec_file)
        except Exception as exc:
            issues.append(
                make_issue(
                    f"failed to resolve generated artifact names for {rel_product_spec_file}: {exc}",
                    rel_implementation_config_file,
                    1,
                    code="PROJECT_IMPLEMENTATION_CONFIG_INVALID",
                )
            )
            continue

        for file_path in sorted(project_dir.rglob("*")):
            if not file_path.is_file():
                continue
            rel_parts = file_path.relative_to(project_dir).parts
            top_level = rel_parts[0]
            if top_level in PROJECT_ALLOWED_TOP_LEVEL_DIRS:
                continue
            if len(rel_parts) == 1 and file_path.name in PROJECT_ALLOWED_ROOT_FILES:
                continue
            if file_path.suffix.lower() in PROJECT_ALLOWED_DOC_SUFFIXES:
                continue
            issues.append(
                make_issue(
                    (
                        "project configuration directories must not contain direct implementation files "
                        "outside generated/ or assets/; change framework markdown, product_spec.toml, "
                        "or implementation_config.toml instead"
                    ),
                    file_path.relative_to(REPO_ROOT).as_posix(),
                    1,
                    code="PROJECT_DIRECT_CODE_FORBIDDEN",
                    related=[
                        {
                            "message": "Project product spec",
                            "file": rel_product_spec_file,
                            "line": 1,
                            "column": 1,
                        },
                        {
                            "message": "Project implementation config",
                            "file": rel_implementation_config_file,
                            "line": 1,
                            "column": 1,
                        }
                    ],
                )
            )

        actual_generated_dir = project_dir / "generated"
        if not actual_generated_dir.exists():
            issues.append(
                make_issue(
                    (
                        "missing generated project artifacts; run "
                        f"`uv run python scripts/materialize_project.py --project {rel_product_spec_file}`"
                    ),
                    rel_product_spec_file,
                    1,
                    code="PROJECT_GENERATED_MISSING",
                )
            )
            continue

        expected_generated_file_set = set(expected_generated_files)
        actual_generated_files = {path.name for path in actual_generated_dir.iterdir() if path.is_file()}
        unexpected_generated_files = sorted(actual_generated_files - expected_generated_file_set)
        for extra_name in unexpected_generated_files:
            issues.append(
                make_issue(
                    (
                        f"unexpected generated artifact: {extra_name}; generated/ must only contain "
                        "the canonical artifact set declared in implementation_config.toml"
                    ),
                    (actual_generated_dir / extra_name).relative_to(REPO_ROOT).as_posix(),
                    1,
                    code="PROJECT_GENERATED_EXTRA_FILE",
                    related=[
                        {
                            "message": "Project implementation config",
                            "file": rel_implementation_config_file,
                            "line": 1,
                            "column": 1,
                        }
                    ],
                )
            )

        try:
            with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
                temp_generated_dir = Path(temp_dir) / "generated"
                materialize_registered_project(product_spec_file, output_dir=temp_generated_dir)
                for required_name in expected_generated_files:
                    actual_file = actual_generated_dir / required_name
                    expected_file = temp_generated_dir / required_name
                    if not actual_file.exists():
                        issues.append(
                            make_issue(
                                f"missing generated artifact: {required_name}",
                                rel_product_spec_file,
                                1,
                                code="PROJECT_GENERATED_FILE_MISSING",
                                related=[
                                    {
                                        "message": "Expected generated file",
                                        "file": actual_file.relative_to(REPO_ROOT).as_posix(),
                                        "line": 1,
                                        "column": 1,
                                    }
                                ],
                            )
                        )
                        continue
                    if _read_file_bytes(actual_file) != _read_file_bytes(expected_file):
                        issues.append(
                            make_issue(
                                (
                                    f"generated artifact is stale or manually edited: {required_name}; "
                                    "re-materialize from framework markdown, product spec, and implementation config"
                                ),
                                actual_file.relative_to(REPO_ROOT).as_posix(),
                                1,
                                code="PROJECT_GENERATED_OUT_OF_SYNC",
                                related=[
                                    {
                                        "message": "Project product spec",
                                        "file": rel_product_spec_file,
                                        "line": 1,
                                        "column": 1,
                                    },
                                    {
                                        "message": "Project implementation config",
                                        "file": rel_implementation_config_file,
                                        "line": 1,
                                        "column": 1,
                                    }
                                ],
                            )
                        )
        except Exception as exc:
            issues.append(
                make_issue(
                    f"project materialization failed for {rel_product_spec_file}: {exc}",
                    rel_product_spec_file,
                    1,
                    code="PROJECT_GENERATION_FAILED",
                )
            )

    return issues


def validate_implementation_config_effects(
    product_spec_files: list[Path] | None = None,
) -> list[Issue]:
    issues: list[Issue] = []
    project_product_spec_files = product_spec_files or discover_project_product_spec_files()
    for product_spec_file in project_product_spec_files:
        rel_product_spec_file = product_spec_file.relative_to(REPO_ROOT).as_posix()
        implementation_config_file = implementation_config_path_for(product_spec_file)
        rel_implementation_config_file = implementation_config_file.relative_to(REPO_ROOT).as_posix()
        try:
            _, implementation_data = _load_toml_text_and_data(implementation_config_file)
            implementation_leaf_values = _collect_leaf_paths(implementation_data)
            registration = resolve_project_template_registration(product_spec_file)
            project = load_registered_project(product_spec_file)
            runtime_bundle = project.to_runtime_bundle_dict()
            runtime_bundle["generated_artifacts"] = _derived_generated_artifacts_payload(
                product_spec_file,
                implementation_data,
            )
            effect_manifest = registration.build_implementation_effect_manifest(project)
        except Exception as exc:
            issues.append(
                make_issue(
                    f"failed to build implementation effect graph for {rel_product_spec_file}: {exc}",
                    rel_implementation_config_file,
                    1,
                    code="PROJECT_IMPLEMENTATION_EFFECT_BUILD_FAILED",
                )
            )
            continue

        effect_keys = set(effect_manifest)
        leaf_keys = set(implementation_leaf_values)

        for field_path in sorted(leaf_keys - effect_keys):
            issues.append(
                make_issue(
                    f"implementation_config field has no downstream effect declaration: {field_path}",
                    rel_implementation_config_file,
                    1,
                    code="PROJECT_IMPLEMENTATION_CONFIG_DEAD_FIELD",
                )
            )

        for field_path in sorted(effect_keys - leaf_keys):
            issues.append(
                make_issue(
                    f"implementation effect manifest references unknown config field: {field_path}",
                    rel_implementation_config_file,
                    1,
                    code="PROJECT_IMPLEMENTATION_EFFECT_STALE",
                )
            )

        for field_path in sorted(effect_keys & leaf_keys):
            expected_value = implementation_leaf_values[field_path]
            effect_entry = effect_manifest[field_path]
            manifest_value = effect_entry.get("value")
            if manifest_value != expected_value:
                issues.append(
                    make_issue(
                        (
                            f"implementation effect manifest value mismatch for {field_path}: "
                            f"expected {expected_value!r}, got {manifest_value!r}"
                        ),
                        rel_implementation_config_file,
                        1,
                        code="PROJECT_IMPLEMENTATION_EFFECT_VALUE_MISMATCH",
                    )
                )
                continue

            relation = effect_entry.get("relation")
            if not isinstance(relation, str) or not relation:
                issues.append(
                    make_issue(
                        f"implementation effect manifest missing relation for {field_path}",
                        rel_implementation_config_file,
                        1,
                        code="PROJECT_IMPLEMENTATION_EFFECT_RELATION_MISSING",
                    )
                )
                continue

            targets = effect_entry.get("targets")
            if not isinstance(targets, list) or not targets:
                issues.append(
                    make_issue(
                        f"implementation_config field lacks downstream targets: {field_path}",
                        rel_implementation_config_file,
                        1,
                        code="PROJECT_IMPLEMENTATION_EFFECT_TARGETS_MISSING",
                    )
                )
                continue

            for target_path in targets:
                if not isinstance(target_path, str) or not target_path.strip():
                    issues.append(
                        make_issue(
                            f"implementation effect target must be a non-empty dotted path for {field_path}",
                            rel_implementation_config_file,
                            1,
                            code="PROJECT_IMPLEMENTATION_EFFECT_TARGET_INVALID",
                        )
                    )
                    continue
                if target_path.startswith("implementation_config."):
                    issues.append(
                        make_issue(
                            (
                                f"{field_path} only points back to implementation_config; "
                                "configuration effects must land in downstream compiled/runtime structures"
                            ),
                            rel_implementation_config_file,
                            1,
                            code="PROJECT_IMPLEMENTATION_EFFECT_SELF_REFERENCE",
                        )
                    )
                    continue
                target_value = _get_dotted_value(runtime_bundle, target_path)
                if target_value is _MISSING:
                    issues.append(
                        make_issue(
                            f"implementation effect target is missing for {field_path}: {target_path}",
                            rel_product_spec_file,
                            1,
                            code="PROJECT_IMPLEMENTATION_EFFECT_TARGET_MISSING",
                            related=[
                                {
                                    "message": "Implementation config",
                                    "file": rel_implementation_config_file,
                                    "line": 1,
                                    "column": 1,
                                }
                            ],
                        )
                    )
                    continue
                try:
                    matches = _relation_matches(relation, expected_value, target_value)
                except Exception as exc:
                    issues.append(
                        make_issue(
                            f"failed to evaluate implementation effect for {field_path}: {exc}",
                            rel_implementation_config_file,
                            1,
                            code="PROJECT_IMPLEMENTATION_EFFECT_RELATION_INVALID",
                        )
                    )
                    continue
                if matches:
                    continue
                issues.append(
                    make_issue(
                        (
                            f"implementation effect mismatch for {field_path}: target {target_path} "
                            f"does not reflect configured value {expected_value!r}"
                        ),
                        rel_product_spec_file,
                        1,
                        code="PROJECT_IMPLEMENTATION_EFFECT_MISMATCH",
                        related=[
                            {
                                "message": f"Downstream target {target_path} resolved to {target_value!r}",
                                "file": rel_implementation_config_file,
                                "line": 1,
                                "column": 1,
                            }
                        ],
                    )
                )

    return issues


def validate_project_governance(
    product_spec_files: list[Path] | None = None,
) -> list[Issue]:
    issues: list[Issue] = []
    project_product_spec_files = product_spec_files or discover_project_product_spec_files()
    for product_spec_file in project_product_spec_files:
        rel_product_spec_file = product_spec_file.relative_to(REPO_ROOT).as_posix()
        implementation_config_file = implementation_config_path_for(product_spec_file)
        rel_implementation_config_file = implementation_config_file.relative_to(REPO_ROOT).as_posix()
        try:
            _, implementation_data = _load_toml_text_and_data(implementation_config_file)
            artifacts = implementation_data.get("artifacts")
            if not isinstance(artifacts, dict):
                raise ValueError("implementation_config.toml must define [artifacts]")
            governance_file_name = artifacts.get("governance_tree_json")
            if not isinstance(governance_file_name, str) or not governance_file_name.strip():
                raise ValueError("implementation_config.toml missing artifacts.governance_tree_json")
            governance_tree_path = product_spec_file.parent / "generated" / governance_file_name.strip()
        except Exception as exc:
            issues.append(
                make_issue(
                    f"failed to resolve governance tree path for {rel_product_spec_file}: {exc}",
                    rel_implementation_config_file,
                    1,
                    code="GOVERNANCE_CONFIG_INVALID",
                )
            )
            continue

        if not governance_tree_path.exists():
            issues.append(
                make_issue(
                    "missing governance tree; run "
                    f"`uv run python scripts/materialize_project.py --project {rel_product_spec_file}`",
                    rel_product_spec_file,
                    1,
                    code="STALE_EVIDENCE",
                    related=[
                        {
                            "message": "Expected governance tree",
                            "file": governance_tree_path.relative_to(REPO_ROOT).as_posix(),
                            "line": 1,
                            "column": 1,
                        }
                    ],
                )
            )
            continue

        try:
            tree_payload = parse_governance_tree(governance_tree_path)
        except Exception as exc:
            issues.append(
                make_issue(
                    f"invalid governance tree for {rel_product_spec_file}: {exc}",
                    governance_tree_path.relative_to(REPO_ROOT).as_posix(),
                    1,
                    code="GOVERNANCE_TREE_INVALID",
                )
            )
            continue

        tree_issues = validate_tree_closure(tree_payload)
        if tree_issues:
            for stale in tree_issues:
                issue = make_issue(
                    stale["message"],
                    stale.get("file") or governance_tree_path.relative_to(REPO_ROOT).as_posix(),
                    int(stale.get("line", 1)),
                    code=str(stale["code"]),
                    related=[
                        {
                            "message": "Materialize this project to refresh governance evidence",
                            "file": rel_product_spec_file,
                            "line": 1,
                            "column": 1,
                        }
                    ],
                )
                if "ref" in stale:
                    issue["ref"] = stale["ref"]
                issues.append(issue)
            continue

        try:
            project = load_registered_project(product_spec_file)
        except Exception as exc:
            issues.append(
                make_issue(
                    f"failed to load project for governance validation: {exc}",
                    rel_product_spec_file,
                    1,
                    code="GOVERNANCE_PROJECT_LOAD_FAILED",
                )
            )
            continue

        for finding in compare_project_to_tree(project, tree_payload):
            issue = make_issue(
                str(finding["message"]),
                str(finding.get("file") or rel_product_spec_file),
                int(finding.get("line", 1)),
                code=str(finding["code"]),
            )
            for key in ("symbol_id", "owner", "kind", "expected", "actual", "locator"):
                if key in finding:
                    issue[key] = finding[key]
            issues.append(issue)

    return issues


def validate_workspace_governance_artifacts() -> list[Issue]:
    issues: list[Issue] = []
    rel_json = DEFAULT_WORKSPACE_GOVERNANCE_JSON.relative_to(REPO_ROOT).as_posix()
    rel_html = DEFAULT_WORKSPACE_GOVERNANCE_HTML.relative_to(REPO_ROOT).as_posix()
    rel_audit_json = DEFAULT_PROJECT_DISCOVERY_AUDIT_JSON.relative_to(REPO_ROOT).as_posix()
    rel_audit_md = DEFAULT_PROJECT_DISCOVERY_AUDIT_MD.relative_to(REPO_ROOT).as_posix()

    if not DEFAULT_WORKSPACE_GOVERNANCE_JSON.exists():
        issues.append(
            make_issue(
                "missing workspace governance tree JSON; run `uv run python scripts/materialize_project.py`",
                rel_json,
                1,
                code="WORKSPACE_GOVERNANCE_MISSING",
            )
        )
        return issues

    if not DEFAULT_WORKSPACE_GOVERNANCE_HTML.exists():
        issues.append(
            make_issue(
                "missing workspace governance tree HTML; run `uv run python scripts/materialize_project.py`",
                rel_html,
                1,
                code="WORKSPACE_GOVERNANCE_MISSING",
            )
        )
        return issues

    if not DEFAULT_PROJECT_DISCOVERY_AUDIT_JSON.exists():
        issues.append(
            make_issue(
                "missing project discovery audit JSON; run `uv run python scripts/materialize_project.py`",
                rel_audit_json,
                1,
                code="PROJECT_DISCOVERY_AUDIT_MISSING",
            )
        )
        return issues

    if not DEFAULT_PROJECT_DISCOVERY_AUDIT_MD.exists():
        issues.append(
            make_issue(
                "missing project discovery audit Markdown; run `uv run python scripts/materialize_project.py`",
                rel_audit_md,
                1,
                code="PROJECT_DISCOVERY_AUDIT_MISSING",
            )
        )
        return issues

    try:
        parse_workspace_governance_payload(DEFAULT_WORKSPACE_GOVERNANCE_JSON)
    except Exception as exc:
        issues.append(
            make_issue(
                f"invalid workspace governance tree JSON: {exc}",
                rel_json,
                1,
                code="WORKSPACE_GOVERNANCE_INVALID",
            )
        )
        return issues

    try:
        audit_payload = _read_json(DEFAULT_PROJECT_DISCOVERY_AUDIT_JSON)
        if audit_payload.get("audit_version") != "project-discovery-audit/v1":
            raise ValueError(f"unsupported audit version: {audit_payload.get('audit_version')}")
        if not isinstance(audit_payload.get("entries"), list):
            raise ValueError("project discovery audit missing entries list")
    except Exception as exc:
        issues.append(
            make_issue(
                f"invalid project discovery audit JSON: {exc}",
                rel_audit_json,
                1,
                code="PROJECT_DISCOVERY_AUDIT_INVALID",
            )
        )
        return issues

    try:
        fresh_payload = build_workspace_governance_payload()
        fresh_audit_payload = build_project_discovery_audit()
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            temp_json = Path(temp_dir) / "shelf_governance_tree.json"
            temp_html = Path(temp_dir) / "shelf_governance_tree.html"
            temp_audit_json = Path(temp_dir) / "project_discovery_audit.json"
            temp_audit_md = Path(temp_dir) / "project_discovery_audit.md"
            temp_json.write_text(json.dumps(fresh_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            temp_audit_json.write_text(
                json.dumps(fresh_audit_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temp_audit_md.write_text(
                render_project_discovery_audit_markdown(fresh_audit_payload),
                encoding="utf-8",
            )
            graph = load_hierarchy_graph(temp_json)
            render_hierarchy_html(graph, temp_html, width=1680, height=1080)
            if _read_file_bytes(DEFAULT_WORKSPACE_GOVERNANCE_JSON) != _read_file_bytes(temp_json):
                issues.append(
                    make_issue(
                        "workspace governance tree JSON is stale or manually edited; re-materialize the workspace tree",
                        rel_json,
                        1,
                        code="WORKSPACE_GOVERNANCE_OUT_OF_SYNC",
                    )
                )
            if _read_file_bytes(DEFAULT_WORKSPACE_GOVERNANCE_HTML) != _read_file_bytes(temp_html):
                issues.append(
                    make_issue(
                        "workspace governance tree HTML is stale or manually edited; re-materialize the workspace tree",
                        rel_html,
                        1,
                        code="WORKSPACE_GOVERNANCE_OUT_OF_SYNC",
                    )
                )
            if _read_file_bytes(DEFAULT_PROJECT_DISCOVERY_AUDIT_JSON) != _read_file_bytes(temp_audit_json):
                issues.append(
                    make_issue(
                        "project discovery audit JSON is stale or manually edited; re-materialize the workspace tree",
                        rel_audit_json,
                        1,
                        code="PROJECT_DISCOVERY_AUDIT_OUT_OF_SYNC",
                    )
                )
            if _read_file_bytes(DEFAULT_PROJECT_DISCOVERY_AUDIT_MD) != _read_file_bytes(temp_audit_md):
                issues.append(
                    make_issue(
                        "project discovery audit Markdown is stale or manually edited; re-materialize the workspace tree",
                        rel_audit_md,
                        1,
                        code="PROJECT_DISCOVERY_AUDIT_OUT_OF_SYNC",
                    )
                )
    except Exception as exc:
        issues.append(
            make_issue(
                f"failed to rebuild workspace governance tree: {exc}",
                rel_json,
                1,
                code="WORKSPACE_GOVERNANCE_BUILD_FAILED",
            )
        )

    return issues


def line_from_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


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


def extract_framework_base_inline_expr(base_line: str) -> str:
    source_split = re.split(r"来源[：:]", base_line, maxsplit=1)
    before_source = source_split[0].strip()
    if "：" in before_source:
        _, _, expr_tail = before_source.partition("：")
    else:
        _, _, expr_tail = before_source.partition(":")
    return expr_tail.strip().rstrip("。.;；")


def parse_framework_base_inline_refs(expr: str) -> list[tuple[str | None, int, int, str]]:
    refs: list[tuple[str | None, int, int, str]] = []
    for part in expr.split("+"):
        term = part.strip()
        if not term:
            return []
        match = FRAMEWORK_INLINE_UPSTREAM_TERM_PATTERN.fullmatch(term)
        if match is None:
            return []
        framework_name = match.group("framework")
        refs.append(
            (
                framework_name.strip() if framework_name else None,
                int(match.group("level")),
                int(match.group("module")),
                (match.group("rules") or "").strip(),
            )
        )
    return refs


def iter_framework_layer_markdown() -> list[tuple[str, int, Path]]:
    docs: list[tuple[str, int, Path]] = []
    if not FRAMEWORK_DIR.exists():
        return docs

    for module_dir in sorted(FRAMEWORK_DIR.iterdir()):
        if not module_dir.is_dir():
            continue
        module_name = module_dir.name
        for markdown_file in sorted(module_dir.glob("*.md")):
            layer_match = FRAMEWORK_FILE_LEVEL_PREFIX_PATTERN.fullmatch(markdown_file.name)
            if layer_match is None:
                continue
            layer_num = int(layer_match.group(1))
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


def make_framework_module_key(module_name: str, level_num: int, module_num: int) -> str:
    return f"{module_name}:L{level_num}.M{module_num}"


def format_framework_module_key(module_key: str) -> str:
    framework_name, _, local_ref = module_key.partition(":")
    if not framework_name or not local_ref:
        return module_key
    return f"{framework_name}.{local_ref}"


def validate_framework_reference_graph(
    module_ref_edges: list[dict[str, Any]],
    module_files_by_key: dict[str, str],
) -> list[Issue]:
    issues: list[Issue] = []
    graph: dict[str, list[str]] = {module_key: [] for module_key in module_files_by_key}
    closing_edges: dict[tuple[str, str], dict[str, Any]] = {}

    for edge in module_ref_edges:
        source = str(edge["source"])
        target = str(edge["target"])
        graph.setdefault(source, []).append(target)
        graph.setdefault(target, [])
        closing_edges.setdefault((source, target), edge)

    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []
    reported_edges: set[tuple[str, str]] = set()

    def dfs(module_key: str) -> None:
        visiting.add(module_key)
        stack.append(module_key)

        for target_key in graph.get(module_key, []):
            if target_key in visiting:
                edge_key = (module_key, target_key)
                if edge_key not in reported_edges:
                    reported_edges.add(edge_key)
                    edge = closing_edges.get(edge_key, {})
                    try:
                        target_index = stack.index(target_key)
                    except ValueError:
                        target_index = 0
                    cycle_keys = stack[target_index:] + [target_key]
                    cycle_text = " -> ".join(format_framework_module_key(item) for item in cycle_keys)
                    issues.append(
                        make_issue(
                            f"framework inline refs must be acyclic; detected cycle: {cycle_text}",
                            str(edge.get("file") or module_files_by_key.get(module_key) or ""),
                            int(edge.get("line") or 1),
                            code="FW029",
                        )
                    )
                continue
            if target_key in visited:
                continue
            dfs(target_key)

        stack.pop()
        visiting.remove(module_key)
        visited.add(module_key)

    for module_key in sorted(graph):
        if module_key in visited:
            continue
        dfs(module_key)

    return issues


def validate_framework_layers() -> tuple[list[Issue], set[str]]:
    issues: list[Issue] = []
    layer_files: set[str] = set()
    module_levels: dict[str, set[int]] = {}
    module_level_module_ids: dict[str, dict[int, set[int]]] = {}
    module_files_by_key: dict[str, str] = {}
    module_ref_edges: list[dict[str, Any]] = []

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
        module_levels.setdefault(module_name, set())

        for entry in sorted(module_dir.iterdir()):
            if entry.is_file() and entry.suffix == ".md":
                if FRAMEWORK_FILE_LEVEL_PREFIX_PATTERN.fullmatch(entry.name) is not None:
                    continue
                rel = entry.relative_to(REPO_ROOT).as_posix()
                issues.append(
                    make_issue(
                        "framework markdown filename must use Lx-Mn- prefix, e.g. L2-M0-xxx.md",
                        rel,
                        1,
                        code="FRAMEWORK_FILE_LEVEL_PREFIX_INVALID",
                    )
                )
            if entry.is_dir():
                rel = entry.relative_to(REPO_ROOT).as_posix()
                issues.append(
                    make_issue(
                        "framework module must store markdown directly under module directory; use Lx-Mn-*.md files",
                        rel,
                        1,
                        code="FRAMEWORK_SUBDIR_FORBIDDEN",
                    )
                )

    framework_docs = iter_framework_layer_markdown()
    for module_name, level_num, markdown_file in framework_docs:
        layer_match = FRAMEWORK_FILE_LEVEL_PREFIX_PATTERN.fullmatch(markdown_file.name)
        if layer_match is None:
            continue
        module_num = int(layer_match.group(2))
        module_level_module_ids.setdefault(module_name, {}).setdefault(level_num, set()).add(module_num)
        module_files_by_key[make_framework_module_key(module_name, level_num, module_num)] = (
            markdown_file.relative_to(REPO_ROOT).as_posix()
        )

    module_min_levels = {
        module_name: min(level_map)
        for module_name, level_map in module_level_module_ids.items()
        if level_map
    }

    for module_name, level_num, markdown_file in framework_docs:
        rel_file = markdown_file.relative_to(REPO_ROOT).as_posix()
        layer_files.add(rel_file)
        module_levels.setdefault(module_name, set()).add(level_num)
        layer_match = FRAMEWORK_FILE_LEVEL_PREFIX_PATTERN.fullmatch(markdown_file.name)
        if layer_match is None:
            continue
        module_num = int(layer_match.group(2))
        source_module_key = make_framework_module_key(module_name, level_num, module_num)
        root_level_num = module_min_levels.get(module_name, 0)
        file_text = read_text(markdown_file)

        framework_directive_match = FRAMEWORK_DIRECTIVE_LINE_PATTERN.search(file_text)
        if framework_directive_match is None:
            issues.append(
                make_issue(
                    "framework file must include plain @framework directive",
                    rel_file,
                    1,
                    code="FW001",
                )
            )
            continue

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

        file_identifiers: set[str] = set()
        file_identifier_origin: dict[str, int] = {}
        for id_match in FRAMEWORK_NUMBERED_ITEM_PATTERN.finditer(file_text):
            identifier = id_match.group(1)
            line_num = line_from_offset(file_text, id_match.start(1))
            previous_line = file_identifier_origin.get(identifier)
            if previous_line is not None:
                issues.append(
                    make_issue(
                        f"framework identifier must be unique inside current framework file: {identifier}",
                        rel_file,
                        line_num,
                        code="FW010",
                        related=[
                            {
                                "message": "previous declaration",
                                "file": rel_file,
                                "line": previous_line,
                                "column": 1,
                            }
                        ],
                    )
                )
                continue
            file_identifier_origin[identifier] = line_num
            file_identifiers.add(identifier)

        for identifier in sorted(file_identifiers):
            line_num = file_identifier_origin.get(identifier, 1)
            if re.fullmatch(r"C\d.*", identifier) and CANONICAL_CAPABILITY_ID_PATTERN.fullmatch(identifier) is None:
                issues.append(
                    make_issue(
                        f"invalid capability identifier format: {identifier}; expected C<number>",
                        rel_file,
                        line_num,
                        code="FW011",
                    )
                )
            if re.fullmatch(r"B\d.*", identifier) and CANONICAL_BASE_ID_PATTERN.fullmatch(identifier) is None:
                issues.append(
                    make_issue(
                        f"invalid base identifier format: {identifier}; expected B<number>",
                        rel_file,
                        line_num,
                        code="FW011",
                    )
                )
            if re.fullmatch(r"V\d.*", identifier) and CANONICAL_VERIFY_ID_PATTERN.fullmatch(identifier) is None:
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
        non_capability_ids: set[str] = set()
        for capability_line_num, capability_line in iter_section_bullet_lines(file_text, "## 1. 能力声明"):
            capability_match = FRAMEWORK_NUMBERED_ITEM_PATTERN.match(capability_line)
            if capability_match is None:
                continue
            capability_id = capability_match.group(1)
            if capability_id not in capability_ids:
                continue
            if "非能力项" in capability_line:
                non_capability_ids.add(capability_id)
        positive_capability_ids = capability_ids - non_capability_ids
        base_ids = {
            identifier for identifier in file_identifiers if CANONICAL_BASE_ID_PATTERN.fullmatch(identifier)
        }
        boundary_ids: set[str] = set()
        base_source_tokens_by_base: dict[str, set[str]] = {}

        for base_item_match in FRAMEWORK_BASE_ITEM_LINE_PATTERN.finditer(file_text):
            base_id = base_item_match.group(1)
            base_line = base_item_match.group(0)
            base_line_num = line_from_offset(file_text, base_item_match.start(1))
            inline_expr = extract_framework_base_inline_expr(base_line)
            inline_refs = parse_framework_base_inline_refs(inline_expr)
            if FRAMEWORK_LEGACY_UPSTREAM_CLAUSE_PATTERN.search(base_line):
                issues.append(
                    make_issue(
                        (
                            f"{base_id} must inline upstream module refs before source expression; "
                            "legacy '上游模块：...' clause is forbidden"
                        ),
                        rel_file,
                        base_line_num,
                        code="FW023",
                    )
                )
            local_inline_refs: list[tuple[int, int, str]] = []
            external_inline_refs: list[tuple[str, int, int, str]] = []
            for ref_framework, ref_level, ref_module_num, ref_rules in inline_refs:
                normalized_framework = ref_framework or module_name
                if normalized_framework == module_name:
                    local_inline_refs.append((ref_level, ref_module_num, ref_rules))
                else:
                    external_inline_refs.append(
                        (
                            normalized_framework,
                            ref_level,
                            ref_module_num,
                            ref_rules,
                        )
                    )

            if level_num == root_level_num and local_inline_refs:
                issues.append(
                    make_issue(
                        (
                            f"{base_id} in current framework root layer L{root_level_num} cannot reference "
                            "local upstream modules; root bases must stay self-contained inside current framework"
                        ),
                        rel_file,
                        base_line_num,
                        code="FW026",
                    )
                )

            if external_inline_refs:
                for ext_framework, ref_level, ref_module_num, _ in external_inline_refs:
                    available_external_ids = module_level_module_ids.get(ext_framework, {}).get(ref_level, set())
                    if ref_module_num not in available_external_ids:
                        issues.append(
                            make_issue(
                                (
                                    f"{base_id} external inline ref points to missing framework module: "
                                    f"{ext_framework}.L{ref_level}.M{ref_module_num}"
                                ),
                                rel_file,
                                base_line_num,
                                code="FW028",
                            )
                        )
                        continue

                    module_ref_edges.append(
                        {
                            "source": source_module_key,
                            "target": make_framework_module_key(ext_framework, ref_level, ref_module_num),
                            "file": rel_file,
                            "line": base_line_num,
                            "base_id": base_id,
                        }
                    )

            if level_num > root_level_num:
                if not inline_expr:
                    issues.append(
                        make_issue(
                            (
                                f"{base_id} must inline local upstream module refs before source "
                                "expression, e.g. L0.M0[R1] + L0.M1[R2]"
                            ),
                            rel_file,
                            base_line_num,
                            code="FW024",
                        )
                    )
                elif not inline_refs:
                    issues.append(
                        make_issue(
                            (
                                f"{base_id} inline upstream module expression is invalid: {inline_expr}; "
                                "expected Lx.My[...] or framework.Lx.My[...] terms joined by '+'"
                            ),
                            rel_file,
                            base_line_num,
                            code="FW024",
                        )
                    )
                else:
                    if not local_inline_refs:
                        issues.append(
                            make_issue(
                                (
                                    f"{base_id} must include at least one local upstream ref "
                                    "inside current framework before relying on external refs"
                                ),
                                rel_file,
                                base_line_num,
                                code="FW024",
                            )
                        )
                    for ref_level, ref_module_num, _ in local_inline_refs:
                        if ref_level >= level_num:
                            issues.append(
                                make_issue(
                                    (
                                        f"{base_id} inline upstream ref must target a lower local layer "
                                        f"than L{level_num}: L{ref_level}.M{ref_module_num}"
                                    ),
                                    rel_file,
                                    base_line_num,
                                    code="FW025",
                                )
                            )
                            continue
                        if ref_level < root_level_num:
                            issues.append(
                                make_issue(
                                    (
                                        f"{base_id} inline upstream ref points below current framework root "
                                        f"L{root_level_num}: L{ref_level}.M{ref_module_num}"
                                    ),
                                    rel_file,
                                    base_line_num,
                                    code="FW025",
                                )
                            )
                            continue
                        available_ids = module_level_module_ids.get(module_name, {}).get(ref_level, set())
                        if ref_module_num not in available_ids:
                            issues.append(
                                make_issue(
                                    (
                                        f"{base_id} inline upstream ref points to missing module file "
                                        f"in current framework directory: L{ref_level}.M{ref_module_num}"
                                    ),
                                    rel_file,
                                    base_line_num,
                                    code="FW025",
                                )
                            )
                            continue

                        module_ref_edges.append(
                            {
                                "source": source_module_key,
                                "target": make_framework_module_key(module_name, ref_level, ref_module_num),
                                "file": rel_file,
                                "line": base_line_num,
                                "base_id": base_id,
                            }
                        )
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

            base_source_tokens_by_base[base_id] = set(source_tokens)
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
            if re.fullmatch(r"R\d.*", identifier) is None:
                continue
            if FRAMEWORK_RULE_ID_PATTERN.fullmatch(identifier) is None:
                line_num = file_identifier_origin.get(identifier, 1)
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
                    line_num = file_identifier_origin.get(identifier, 1)
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
        rule_participant_bases: dict[str, set[str]] = {}
        rule_output_capabilities: dict[str, set[str]] = {}
        rule_boundary_bindings: dict[str, set[str]] = {}
        for rule_line_num, rule_line in iter_section_bullet_lines(file_text, "## 4. 基组合原则"):
            top_match = FRAMEWORK_RULE_TOP_LINE_PATTERN.match(rule_line)
            if top_match is not None:
                parent_rule = top_match.group(1)
                rule_top_lines.setdefault(parent_rule, rule_line_num)
                rule_child_items.setdefault(parent_rule, [])
                rule_participant_bases.setdefault(parent_rule, set())
                rule_output_capabilities.setdefault(parent_rule, set())
                rule_boundary_bindings.setdefault(parent_rule, set())
                continue

            child_match = FRAMEWORK_RULE_CHILD_LINE_PATTERN.match(rule_line)
            if child_match is None:
                continue
            child_rule = child_match.group(1)
            parent_rule = child_rule.split(".", 1)[0]
            content = child_match.group(2).strip()
            rule_child_items.setdefault(parent_rule, []).append((rule_line_num, content))
            child_tokens = extract_backtick_tokens(content)

            if "参与基" in content:
                participant_bases = {
                    token for token in child_tokens if CANONICAL_BASE_ID_PATTERN.fullmatch(token) is not None
                }
                rule_participant_bases.setdefault(parent_rule, set()).update(participant_bases)
                if not participant_bases:
                    issues.append(
                        make_issue(
                            f"{parent_rule} participating bases must reference at least one B*",
                            rel_file,
                            rule_line_num,
                            code="FW042",
                        )
                    )
                for token in child_tokens:
                    if token in base_ids:
                        continue
                    issues.append(
                        make_issue(
                            f"{parent_rule} participating bases reference undefined base: {token}",
                            rel_file,
                            rule_line_num,
                            code="FW042",
                        )
                    )

            if "输出能力" in content:
                output_capabilities = set(re.findall(r"C\d+", content))
                rule_output_capabilities.setdefault(parent_rule, set()).update(output_capabilities)

            if "边界绑定" in content:
                boundary_refs = {token for token in child_tokens if token in boundary_ids}
                rule_boundary_bindings.setdefault(parent_rule, set()).update(boundary_refs)
                if not boundary_refs:
                    issues.append(
                        make_issue(
                            f"{parent_rule} boundary binding must reference at least one declared boundary",
                            rel_file,
                            rule_line_num,
                            code="FW043",
                        )
                    )
                for token in child_tokens:
                    if token in boundary_ids:
                        continue
                    issues.append(
                        make_issue(
                            f"{parent_rule} boundary binding references undefined boundary: {token}",
                            rel_file,
                            rule_line_num,
                            code="FW043",
                        )
                    )

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

        capability_source_bases: dict[str, set[str]] = {cap_id: set() for cap_id in positive_capability_ids}
        for base_ref_id, base_source_tokens in base_source_tokens_by_base.items():
            for capability_id in positive_capability_ids:
                if capability_id in base_source_tokens:
                    capability_source_bases.setdefault(capability_id, set()).add(base_ref_id)

        capability_output_rules: dict[str, set[str]] = {cap_id: set() for cap_id in positive_capability_ids}
        for parent_rule, output_capability_refs in rule_output_capabilities.items():
            for capability_id in positive_capability_ids:
                if capability_id in output_capability_refs:
                    capability_output_rules.setdefault(capability_id, set()).add(parent_rule)

        for capability_id in sorted(positive_capability_ids):
            capability_line_num = int(file_identifier_origin.get(capability_id, 1))
            supporting_bases = capability_source_bases.get(capability_id, set())
            output_rules = capability_output_rules.get(capability_id, set())
            if not supporting_bases:
                issues.append(
                    make_issue(
                        (
                            f"{capability_id} lacks weak sufficiency support: no B* source expression "
                            "references this capability"
                        ),
                        rel_file,
                        capability_line_num,
                        code="FW070",
                    )
                )
            if not output_rules:
                issues.append(
                    make_issue(
                        (
                            f"{capability_id} lacks weak sufficiency support: no R* output capability "
                            "references this capability"
                        ),
                        rel_file,
                        capability_line_num,
                        code="FW071",
                    )
                )
            if supporting_bases and output_rules:
                has_chain = any(
                    bool(rule_participant_bases.get(parent_rule, set()).intersection(supporting_bases))
                    for parent_rule in output_rules
                )
                if not has_chain:
                    issues.append(
                        make_issue(
                            (
                                f"{capability_id} lacks weak sufficiency chain: expected at least one "
                                "B -> R -> C derivation path"
                            ),
                            rel_file,
                            capability_line_num,
                            code="FW072",
                        )
                    )

        used_bases = {
            base_id
            for base_refs in rule_participant_bases.values()
            for base_id in base_refs
        }
        for base_id in sorted(base_ids):
            if base_id in used_bases:
                continue
            issues.append(
                make_issue(
                    f"{base_id} is never used by any R* participating bases",
                    rel_file,
                    file_identifier_origin.get(base_id, 1),
                    code="FW073",
                )
            )

        used_boundaries = {
            boundary_id
            for boundary_refs in rule_boundary_bindings.values()
            for boundary_id in boundary_refs
        }
        for boundary_id in sorted(boundary_ids):
            used_in_base_source = any(
                boundary_id in source_tokens for source_tokens in base_source_tokens_by_base.values()
            )
            if used_in_base_source or boundary_id in used_boundaries:
                continue
            issues.append(
                make_issue(
                    f"{boundary_id} is not used by any B* source or R* boundary binding",
                    rel_file,
                    file_identifier_origin.get(boundary_id, 1),
                    code="FW074",
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
        for required_heading in REQUIRED_FRAMEWORK_DIRECTIVE_SECTIONS:
            if required_heading not in file_text:
                issues.append(
                    make_issue(
                        f"missing required section heading: {required_heading}",
                        rel_file,
                        1,
                        code="FRAMEWORK_LAYER_SECTION_MISSING",
                    )
                )

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

    issues.extend(validate_framework_reference_graph(module_ref_edges, module_files_by_key))

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
    expected_tree = build_standards_tree()
    if not isinstance(tree, dict):
        issues.append(
            make_issue(
                "mapping_registry.json: tree must be an object",
                REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                find_line(registry_text, '"tree"'),
                code="REGISTRY_TREE_TYPE",
            )
        )
        tree = expected_tree
    else:
        if json.dumps(tree, ensure_ascii=False, sort_keys=True) != json.dumps(
            expected_tree,
            ensure_ascii=False,
            sort_keys=True,
        ):
            issues.append(
                make_issue(
                    (
                        "mapping_registry.json: tree is out of sync with the canonical standards tree; "
                        "run `uv run python scripts/sync_mapping_registry.py`"
                    ),
                    REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                    find_line(registry_text, '"tree"'),
                    code="REGISTRY_TREE_STALE",
                )
            )

    level_files = level_files_from_tree(expected_tree)

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
                    "mapping_registry.json: unregistered domain standard under framework/*/L2-Mn-*.md: "
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

        issues.extend(validate_impl_mapping_semantics(item, registry_text))

    return issues


def validate_impl_mapping_semantics(item: dict[str, Any], registry_text: str) -> list[Issue]:
    issues: list[Issue] = []
    map_id = item["id"]
    l2_file = item["l2_file"]
    l2_anchor = item["l2_anchor"]
    impl_files = {
        file_name
        for file_name in (
            symbol_ref.get("file")
            for symbol_ref in item.get("impl_symbols", [])
            if isinstance(symbol_ref, dict)
        )
        if isinstance(file_name, str) and file_name
    }

    if COMPATIBILITY_FACADE_FILE in impl_files:
        issues.append(
            make_issue(
                f"{map_id}: impl_symbols must not reference compatibility facade {COMPATIBILITY_FACADE_FILE}",
                REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                find_mapping_key_line(registry_text, map_id, "impl_symbols"),
                code="IMPL_SYMBOL_COMPAT_FACADE_FORBIDDEN",
            )
        )

    if not l2_file.startswith("framework/shelf/") and SHELF_DOMAIN_FILE in impl_files:
        issues.append(
            make_issue(
                f"{map_id}: non-shelf mapping must not reference shelf-specific domain file {SHELF_DOMAIN_FILE}",
                REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                find_mapping_key_line(registry_text, map_id, "impl_symbols"),
                code="IMPL_SYMBOL_SHELF_DOMAIN_SCOPE_INVALID",
            )
        )

    if l2_file.startswith("framework/shelf/"):
        shelf_required_anchors = {
            "## 2. 边界定义（Boundary / 参数）",
            "## 5. 验证（Verification）",
        }
        if l2_anchor in shelf_required_anchors and SHELF_DOMAIN_FILE not in impl_files:
            issues.append(
                make_issue(
                    f"{map_id}: shelf mapping for '{l2_anchor}' must include {SHELF_DOMAIN_FILE}",
                    REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
                    find_mapping_key_line(registry_text, map_id, "impl_symbols"),
                    code="IMPL_SYMBOL_SHELF_DOMAIN_REQUIRED",
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


def validate_change_propagation(change_context: dict[str, Any], changed_files: set[str]) -> list[Issue]:
    issues: list[Issue] = []
    touched_nodes = list(change_context.get("touched_nodes", []))
    affected_nodes = list(change_context.get("affected_nodes", []))

    governed_prefixes = ("framework/", "specs/", "mapping/", "projects/", "src/")
    ignored_governance_artifacts = {
        DEFAULT_WORKSPACE_GOVERNANCE_JSON.relative_to(REPO_ROOT).as_posix(),
        DEFAULT_WORKSPACE_GOVERNANCE_HTML.relative_to(REPO_ROOT).as_posix(),
    }
    governed_changed_files = sorted(
        path
        for path in changed_files
        if path.startswith(governed_prefixes) and path not in ignored_governance_artifacts
    )
    if governed_changed_files and not touched_nodes:
        issues.append(
            make_issue(
                "changed governed files do not map to any workspace governance node; regenerate the governance tree and verify node coverage",
                DEFAULT_WORKSPACE_GOVERNANCE_JSON.relative_to(REPO_ROOT).as_posix(),
                1,
                code="PROPAGATION_NODE_UNRESOLVED",
                related=[
                    {
                        "message": "First unresolved governed file",
                        "file": governed_changed_files[0],
                        "line": 1,
                        "column": 1,
                    }
                ],
            )
        )
    if touched_nodes and not affected_nodes:
        issues.append(
            make_issue(
                "workspace governance tree resolved touched nodes but produced no affected closure",
                DEFAULT_WORKSPACE_GOVERNANCE_JSON.relative_to(REPO_ROOT).as_posix(),
                1,
                code="PROPAGATION_CLOSURE_EMPTY",
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
    changed: set[str] = set()
    change_context: dict[str, Any] | None = None
    scoped_project_spec_files: list[Path] | None = None

    if args.check_changes:
        changed = collect_changed_files()
        try:
            workspace_payload = build_workspace_governance_payload()
            change_context = resolve_workspace_change_context(workspace_payload, changed)
            affected_files = [
                (REPO_ROOT / item).resolve() if not Path(item).is_absolute() else Path(item).resolve()
                for item in list(change_context.get("affected_project_spec_files", []))
            ]
            if affected_files:
                scoped_project_spec_files = affected_files
        except Exception as exc:
            issues.append(
                make_issue(
                    f"failed to resolve workspace governance change context: {exc}",
                    DEFAULT_WORKSPACE_GOVERNANCE_JSON.relative_to(REPO_ROOT).as_posix(),
                    1,
                    code="WORKSPACE_GOVERNANCE_CONTEXT_FAILED",
                )
            )
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

    if not issues:
        issues.extend(validate_project_generation_discipline(scoped_project_spec_files))

    if not issues:
        issues.extend(validate_implementation_config_effects(scoped_project_spec_files))

    if not issues:
        issues.extend(validate_project_governance(scoped_project_spec_files))

    if not issues:
        issues.extend(validate_workspace_governance_artifacts())

    if args.check_changes and change_context is not None:
        issues.extend(validate_change_propagation(change_context, changed))

    passed = len(issues) == 0
    result_payload = {
        "passed": passed,
        "checked_changes": args.check_changes,
        "errors": issues,
    }
    if change_context is not None:
        result_payload["change_context"] = change_context

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
