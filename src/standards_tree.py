from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable


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


@dataclass(frozen=True)
class DiscoveredStandardFile:
    module_name: str
    file_name: str

    @property
    def node_id(self) -> str:
        return _l2_node_id(self.module_name, self.file_name)


@dataclass(frozen=True)
class StandardsTreeNode:
    node_id: str
    kind: str
    level: str
    file_name: str | None = None
    children: tuple["StandardsTreeNode", ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "id": self.node_id,
            "kind": self.kind,
            "level": self.level,
            "children": [child.to_dict() for child in self.children],
        }
        if self.file_name is not None:
            payload["file"] = self.file_name
        return payload

    def walk(self) -> Iterable["StandardsTreeNode"]:
        yield self
        for child in self.children:
            yield from child.walk()


def _rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def discover_l2_standard_files() -> tuple[DiscoveredStandardFile, ...]:
    preferred: list[DiscoveredStandardFile] = []
    extras: list[DiscoveredStandardFile] = []
    for module_dir in sorted((REPO_ROOT / "framework").iterdir()):
        if not module_dir.is_dir():
            continue
        rel_files = sorted(_rel(path) for path in module_dir.glob("L2-M*-*.md"))
        if not rel_files:
            continue
        bucket = preferred if module_dir.name in L2_MODULE_ORDER else extras
        for rel_file in rel_files:
            bucket.append(DiscoveredStandardFile(module_name=module_dir.name, file_name=rel_file))

    ordered_preferred: list[DiscoveredStandardFile] = []
    for module_name in L2_MODULE_ORDER:
        ordered_preferred.extend(item for item in preferred if item.module_name == module_name)
    ordered_extras = sorted(extras, key=lambda item: item.file_name)
    return tuple([*ordered_preferred, *ordered_extras])


def _slug_token(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", value.upper()).strip("-")


def _l2_node_id(module_name: str, rel_file: str) -> str:
    stem = Path(rel_file).stem
    return "NODE-L2-" + _slug_token(module_name) + "-" + _slug_token(stem)


def build_standards_tree_node() -> StandardsTreeNode:
    l1_children = tuple(
        StandardsTreeNode(
            node_id=node_id,
            kind="file",
            level="L1",
            file_name=file_name,
        )
        for node_id, file_name in CORE_STANDARD_FILES
    )

    l2_children = tuple(
        StandardsTreeNode(
            node_id=item.node_id,
            kind="file",
            level="L2",
            file_name=item.file_name,
        )
        for item in discover_l2_standard_files()
    ) + (
        StandardsTreeNode(
            node_id="NODE-L3-LAYER",
            kind="layer",
            level="L3",
            children=(
                StandardsTreeNode(
                    node_id="NODE-L3-REGISTRY",
                    kind="file",
                    level="L3",
                    file_name=REGISTRY_FILE,
                ),
            ),
        ),
    )

    return StandardsTreeNode(
        node_id="NODE-L0-ROOT",
        kind="file",
        level="L0",
        file_name=ROOT_STANDARD_FILE,
        children=(
            StandardsTreeNode(
                node_id="NODE-L1-LAYER",
                kind="layer",
                level="L1",
                children=l1_children
                + (
                    StandardsTreeNode(
                        node_id="NODE-L2-LAYER",
                        kind="layer",
                        level="L2",
                        children=l2_children,
                    ),
                ),
            ),
        ),
    )


def build_standards_tree() -> dict[str, object]:
    return build_standards_tree_node().to_dict()


def level_files_from_tree(tree: dict[str, object] | StandardsTreeNode) -> dict[str, set[str]]:
    level_files: dict[str, set[str]] = {"L0": set(), "L1": set(), "L2": set(), "L3": set()}

    if isinstance(tree, StandardsTreeNode):
        for node in tree.walk():
            if node.file_name:
                level_files.setdefault(node.level, set()).add(node.file_name)
        return level_files

    def walk_payload(node: dict[str, object]) -> None:
        level = str(node.get("level") or "").strip()
        file_name = node.get("file")
        if isinstance(file_name, str) and file_name.strip():
            level_files.setdefault(level, set()).add(file_name)
        children = node.get("children")
        if not isinstance(children, list):
            return
        for child in children:
            if isinstance(child, dict):
                walk_payload(child)

    walk_payload(tree)
    return level_files
