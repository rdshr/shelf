from __future__ import annotations

from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
ROOT_STANDARD_FILE = "specs/规范总纲与树形结构.md"
CORE_STANDARD_FILES: tuple[tuple[str, str], ...] = (
    ("NODE-L1-CORE", "specs/框架设计核心标准.md"),
    ("NODE-L1-LINT", "specs/框架文档Lint标准.md"),
    ("NODE-L1-TRACEABILITY", "specs/可追溯性标准.md"),
    ("NODE-L1-REDUCIBILITY", "specs/可删减性标准.md"),
    ("NODE-L1-CODE-GIT", "specs/code/Git提交信息标准.md"),
    ("NODE-L1-CODE-PYTHON", "specs/code/Python实现质量标准.md"),
    ("NODE-L1-CODE-RELEASE", "specs/code/发布与版本说明标准.md"),
)
L2_MODULE_ORDER: tuple[str, ...] = (
    "shelf",
    "curtain",
    "backend",
    "frontend",
    "knowledge_base",
)
REGISTRY_FILE = "mapping/mapping_registry.json"


def _rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def discover_l2_standard_files() -> list[tuple[str, str]]:
    preferred: list[tuple[str, str]] = []
    extras: list[tuple[str, str]] = []
    for module_dir in sorted((REPO_ROOT / "framework").iterdir()):
        if not module_dir.is_dir():
            continue
        rel_files = sorted(_rel(path) for path in module_dir.glob("L2-M*-*.md"))
        if not rel_files:
            continue
        bucket = preferred if module_dir.name in L2_MODULE_ORDER else extras
        for rel_file in rel_files:
            bucket.append((module_dir.name, rel_file))

    ordered_preferred: list[tuple[str, str]] = []
    for module_name in L2_MODULE_ORDER:
        ordered_preferred.extend(item for item in preferred if item[0] == module_name)
    ordered_extras = sorted(extras, key=lambda item: item[1])
    return [*ordered_preferred, *ordered_extras]


def _l2_node_id(module_name: str) -> str:
    return "NODE-L2-" + module_name.upper().replace("_", "-")


def build_standards_tree() -> dict[str, Any]:
    l1_children: list[dict[str, Any]] = [
        {
            "id": node_id,
            "kind": "file",
            "level": "L1",
            "file": file_name,
            "children": [],
        }
        for node_id, file_name in CORE_STANDARD_FILES
    ]

    l2_children: list[dict[str, Any]] = [
        {
            "id": _l2_node_id(module_name),
            "kind": "file",
            "level": "L2",
            "file": file_name,
            "children": [],
        }
        for module_name, file_name in discover_l2_standard_files()
    ]
    l2_children.append(
        {
            "id": "NODE-L3-LAYER",
            "kind": "layer",
            "level": "L3",
            "children": [
                {
                    "id": "NODE-L3-REGISTRY",
                    "kind": "file",
                    "level": "L3",
                    "file": REGISTRY_FILE,
                    "children": [],
                }
            ],
        }
    )
    l1_children.append(
        {
            "id": "NODE-L2-LAYER",
            "kind": "layer",
            "level": "L2",
            "children": l2_children,
        }
    )
    return {
        "id": "NODE-L0-ROOT",
        "kind": "file",
        "level": "L0",
        "file": ROOT_STANDARD_FILE,
        "children": [
            {
                "id": "NODE-L1-LAYER",
                "kind": "layer",
                "level": "L1",
                "children": l1_children,
            }
        ],
    }


def level_files_from_tree(tree: dict[str, Any]) -> dict[str, set[str]]:
    level_files: dict[str, set[str]] = {"L0": set(), "L1": set(), "L2": set(), "L3": set()}

    def walk(node: dict[str, Any]) -> None:
        level = str(node.get("level") or "").strip()
        file_name = node.get("file")
        if isinstance(file_name, str) and file_name.strip():
            level_files.setdefault(level, set()).add(file_name)
        children = node.get("children")
        if not isinstance(children, list):
            return
        for child in children:
            if isinstance(child, dict):
                walk(child)

    walk(tree)
    return level_files
