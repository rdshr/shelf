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
DEFAULT_OUTPUT_JSON = REPO_ROOT / "docs/hierarchy/shelf_framework_tree.json"
DEFAULT_OUTPUT_HTML = REPO_ROOT / "docs/hierarchy/shelf_framework_tree.html"
LEVEL_PATTERN = re.compile(r"^L(\d+)$")


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


def build_payload(registry_path: Path) -> dict[str, Any]:
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
        description="Generate framework tree hierarchy graph from mapping registry tree.",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY,
        help="Path to mapping registry JSON",
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

    registry_path = normalize_path(args.registry)
    output_json = normalize_path(args.output_json)
    output_html = normalize_path(args.output_html)

    payload = build_payload(registry_path)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] framework tree JSON generated: {output_json}")

    if args.skip_html:
        return

    render_html(output_json, output_html, args.width, args.height)
    print(f"[OK] framework tree HTML generated: {output_html}")


if __name__ == "__main__":
    main()
