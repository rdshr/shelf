from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = REPO_ROOT / "mapping/mapping_registry.json"
DEFAULT_FRAMEWORK_DIR = REPO_ROOT / "framework"
DEFAULT_OUTPUT_JSON = REPO_ROOT / "docs/hierarchy/shelf_framework_tree.json"
DEFAULT_OUTPUT_HTML = REPO_ROOT / "docs/hierarchy/shelf_framework_tree.html"
LEVEL_PATTERN = re.compile(r"^L(\d+)$")
FRAMEWORK_FILE_LEVEL_PREFIX_PATTERN = re.compile(r"^L(\d+)-[^/]+\.md$")


def parse_level(level_value: Any, *, node_id: str) -> int:
    if not isinstance(level_value, str):
        raise ValueError(f"{node_id}: level must be a string like L0")
    level_match = LEVEL_PATTERN.fullmatch(level_value.strip())
    if level_match is None:
        raise ValueError(f"{node_id}: invalid level '{level_value}', expected Lx")
    return int(level_match.group(1))


def normalize_path(input_path: Path) -> Path:
    if input_path.is_absolute():
        return input_path
    return (REPO_ROOT / input_path).resolve()


def node_label(node_kind: str, level_num: int, file_name: str | None) -> str:
    if node_kind == "layer":
        return f"L{level_num}.layer"
    if file_name:
        stem = Path(file_name).stem
        return f"L{level_num}.{stem}"
    return f"L{level_num}.file"


def build_payload_from_registry(registry_path: Path) -> dict[str, Any]:
    raw = json.loads(registry_path.read_text(encoding="utf-8"))
    tree = raw.get("tree")
    if not isinstance(tree, dict):
        raise ValueError("mapping_registry.json: tree must be an object")

    seen_ids: set[str] = set()
    level_order_counter: dict[int, int] = {}
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    def walk(node_obj: dict[str, Any], parent_id: str | None) -> None:
        node_id = node_obj.get("id")
        if not isinstance(node_id, str) or not node_id.strip():
            raise ValueError("tree node must have non-empty string id")
        if node_id in seen_ids:
            raise ValueError(f"duplicate tree node id: {node_id}")
        seen_ids.add(node_id)

        kind = node_obj.get("kind")
        if kind not in {"layer", "file"}:
            raise ValueError(f"{node_id}: kind must be 'layer' or 'file'")

        level_num = parse_level(node_obj.get("level"), node_id=node_id)
        file_name = node_obj.get("file")
        if kind == "file":
            if not isinstance(file_name, str) or not file_name.strip():
                raise ValueError(f"{node_id}: file node must include non-empty file")
        else:
            file_name = None

        level_order_counter[level_num] = level_order_counter.get(level_num, 0) + 1
        order = level_order_counter[level_num]

        description_parts = [f"id={node_id}", f"kind={kind}", f"level=L{level_num}"]
        if file_name:
            description_parts.append(f"file={file_name}")

        nodes.append(
            {
                "id": node_id,
                "label": node_label(kind, level_num, file_name),
                "level": level_num,
                "order": order,
                "description": " | ".join(description_parts),
            }
        )

        if parent_id is not None:
            edges.append(
                {
                    "from": parent_id,
                    "to": node_id,
                    "relation": "tree_child",
                }
            )

        children = node_obj.get("children", [])
        if not isinstance(children, list):
            raise ValueError(f"{node_id}: children must be a list")
        for child in children:
            if not isinstance(child, dict):
                raise ValueError(f"{node_id}: each child must be an object")
            walk(child, node_id)

    walk(tree, None)

    levels = sorted({node["level"] for node in nodes})
    level_labels = {str(level): f"L{level} 标准层" for level in levels}

    root = {
        "title": "框架标准树结构图",
        "description": (
            "从 mapping/mapping_registry.json 的 tree 自动生成，"
            "展示框架标准树父子关系。"
        ),
        "level_labels": level_labels,
        "nodes": nodes,
        "edges": edges,
    }
    return {"root": root}


def iter_framework_docs(framework_dir: Path) -> list[tuple[str, int, Path]]:
    docs: list[tuple[str, int, Path]] = []
    if not framework_dir.exists():
        return docs

    for module_dir in sorted(framework_dir.iterdir()):
        if not module_dir.is_dir():
            continue
        module_name = module_dir.name
        for markdown_file in sorted(module_dir.glob("*.md")):
            level_match = FRAMEWORK_FILE_LEVEL_PREFIX_PATTERN.fullmatch(markdown_file.name)
            if level_match is None:
                continue
            level_num = int(level_match.group(1))
            docs.append((module_name, level_num, markdown_file))
    return docs


def build_payload_from_framework(framework_dir: Path) -> tuple[dict[str, Any], list[str]]:
    docs = iter_framework_docs(framework_dir)
    if not docs:
        raise ValueError("no framework Lx-*.md files found under framework directory")

    module_level_files: dict[str, dict[int, list[str]]] = {}
    for module_name, level_num, markdown_file in docs:
        rel = markdown_file.relative_to(REPO_ROOT).as_posix()
        module_level_files.setdefault(module_name, {}).setdefault(level_num, []).append(rel)

    warnings: list[str] = []
    seen_warnings: set[str] = set()

    def add_warning(message: str) -> None:
        if message in seen_warnings:
            return
        seen_warnings.add(message)
        warnings.append(message)

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    level_order_counter: dict[int, int] = {}
    node_id_by_file: dict[str, str] = {}

    node_seq = 0
    for module_name in sorted(module_level_files):
        level_map = module_level_files[module_name]
        levels = sorted(level_map)

        if levels and levels[0] != 0:
            add_warning(
                f"module '{module_name}' has no L0 base (lowest existing level: L{levels[0]})."
            )

        for current_level, next_level in zip(levels, levels[1:]):
            if next_level - current_level > 1:
                add_warning(
                    (
                        f"module '{module_name}' has level gap L{current_level} -> L{next_level}; "
                        "only adjacent edges are generated."
                    )
                )

        for level_num in levels:
            for rel in sorted(level_map[level_num]):
                node_seq += 1
                node_id = f"NODE-FW-{node_seq:04d}"
                node_id_by_file[rel] = node_id

                level_order_counter[level_num] = level_order_counter.get(level_num, 0) + 1
                order = level_order_counter[level_num]

                nodes.append(
                    {
                        "id": node_id,
                        "label": f"L{level_num}.{module_name}.{Path(rel).stem}",
                        "level": level_num,
                        "order": order,
                        "description": (
                            f"module={module_name} | level=L{level_num} | file={rel}"
                        ),
                    }
                )

    # Enforce adjacent-level visibility only: Lx -> L(x+1)
    for module_name in sorted(module_level_files):
        level_map = module_level_files[module_name]
        for level_num in sorted(level_map):
            next_level = level_num + 1
            if next_level not in level_map:
                continue
            for source_file in sorted(level_map[level_num]):
                for target_file in sorted(level_map[next_level]):
                    edges.append(
                        {
                            "from": node_id_by_file[source_file],
                            "to": node_id_by_file[target_file],
                            "relation": "framework_adjacent_level",
                            "module": module_name,
                            "from_level": f"L{level_num}",
                            "to_level": f"L{next_level}",
                        }
                    )

    levels = sorted({node["level"] for node in nodes})
    level_labels = {str(level): f"L{level} 标准层" for level in levels}

    description = (
        "从 framework/<module>/Lx-*.md 自动生成，"
        "仅生成相邻层级连接（Lx -> Lx+1），禁止跨级可见。"
    )
    if warnings:
        description = f"{description} 警告数量={len(warnings)}。"

    root = {
        "title": "框架标准树结构图",
        "description": description,
        "level_labels": level_labels,
        "nodes": nodes,
        "edges": edges,
    }
    return {"root": root}, warnings


def render_html(input_json: Path, output_html: Path, width: int, height: int) -> None:
    command = [
        sys.executable,
        str(REPO_ROOT / "scripts/generate_module_hierarchy_html.py"),
        "--input",
        str(input_json),
        "--output",
        str(output_html),
        "--width",
        str(width),
        "--height",
        str(height),
    ]
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate framework hierarchy graph. "
            "Source can be mapping registry tree or framework files."
        ),
    )
    parser.add_argument(
        "--source",
        choices=("framework", "registry"),
        default="framework",
        help="Hierarchy source: framework (default) or registry",
    )
    parser.add_argument(
        "--framework-dir",
        type=Path,
        default=DEFAULT_FRAMEWORK_DIR,
        help="Path to framework directory (used when --source framework)",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY,
        help="Path to mapping registry JSON (used when --source registry)",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=DEFAULT_OUTPUT_JSON,
        help="Output hierarchy JSON path",
    )
    parser.add_argument(
        "--output-html",
        type=Path,
        default=DEFAULT_OUTPUT_HTML,
        help="Output hierarchy HTML path",
    )
    parser.add_argument("--width", type=int, default=1680, help="SVG width")
    parser.add_argument("--height", type=int, default=1180, help="SVG height")
    parser.add_argument("--skip-html", action="store_true", help="Only generate JSON")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    output_json = normalize_path(args.output_json)
    output_html = normalize_path(args.output_html)

    if args.source == "framework":
        framework_dir = normalize_path(args.framework_dir)
        payload, warnings = build_payload_from_framework(framework_dir)
        for message in warnings:
            print(f"[WARN] {message}")
    else:
        registry_path = normalize_path(args.registry)
        payload = build_payload_from_registry(registry_path)

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] framework tree JSON generated: {output_json}")

    if args.skip_html:
        return

    render_html(output_json, output_html, args.width, args.height)
    print(f"[OK] framework tree HTML generated: {output_html}")


if __name__ == "__main__":
    main()
