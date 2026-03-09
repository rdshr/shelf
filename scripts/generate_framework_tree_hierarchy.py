from __future__ import annotations

import argparse
import heapq
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = REPO_ROOT / "standards/L3/mapping_registry.json"
DEFAULT_FRAMEWORK_DIR = REPO_ROOT / "framework"
DEFAULT_OUTPUT_JSON = REPO_ROOT / "docs/hierarchy/shelf_framework_tree.json"
DEFAULT_OUTPUT_HTML = REPO_ROOT / "docs/hierarchy/shelf_framework_tree.html"
LEVEL_PATTERN = re.compile(r"^L(\d+)$")
FRAMEWORK_FILE_LEVEL_MODULE_PATTERN = re.compile(r"^L(\d+)-M(\d+)-[^/]+\.md$")
FRAMEWORK_CAPABILITY_ITEM_LINE_PATTERN = re.compile(r"^\s*[-*]\s*`(C(\d+))`\s*(.*)$")
FRAMEWORK_BASE_ITEM_LINE_PATTERN = re.compile(r"^\s*[-*]\s*`(B(\d+))`\s*(.*)$")
FRAMEWORK_UPSTREAM_TERM_PATTERN = re.compile(
    r"^(?:(?P<framework>[A-Za-z][A-Za-z0-9_-]*)\.)?(?P<ref>L\d+\.M\d+)(?:\[(?P<rules>.*?)\])?$"
)
FRAMEWORK_UPSTREAM_SCAN_PATTERN = re.compile(
    r"`?(?:(?P<framework>[A-Za-z][A-Za-z0-9_-]*)\.)?(?P<ref>L\d+\.M\d+)(?:\[(?P<rules>[^\]]*?)\])?`?"
)


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


def line_from_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def node_label(node_kind: str, level_num: int, file_name: str | None) -> str:
    if node_kind == "layer":
        return f"L{level_num}.layer"
    if file_name:
        stem = Path(file_name).stem
        return f"L{level_num}.{stem}"
    return f"L{level_num}.file"


def find_first_h1_line(file_path: Path) -> int:
    if not file_path.exists():
        return 1
    for idx, line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.lstrip().startswith("# "):
            return idx
    return 1


def find_first_h1_text(file_text: str, fallback: str) -> str:
    for line in file_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip() or fallback
    return fallback


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
        source_line = 1
        if file_name:
            description_parts.append(f"file={file_name}")
            source_line = find_first_h1_line(REPO_ROOT / file_name)

        nodes.append(
            {
                "id": node_id,
                "label": node_label(kind, level_num, file_name),
                "level": level_num,
                "order": order,
                "description": " | ".join(description_parts),
                "source_file": file_name,
                "source_line": source_line,
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
            "从 standards/L3/mapping_registry.json 的 tree 自动生成，"
            "展示框架标准树父子关系。"
        ),
        "level_labels": level_labels,
        "nodes": nodes,
        "edges": edges,
    }
    return {"root": root}


def iter_framework_docs(framework_dir: Path) -> list[tuple[str, int, int, Path]]:
    docs: list[tuple[str, int, int, Path]] = []
    if not framework_dir.exists():
        return docs

    for module_dir in sorted(framework_dir.iterdir()):
        if not module_dir.is_dir():
            continue
        module_name = module_dir.name
        for markdown_file in sorted(module_dir.rglob("*.md")):
            module_match = FRAMEWORK_FILE_LEVEL_MODULE_PATTERN.fullmatch(markdown_file.name)
            if module_match is None:
                continue
            level_num = int(module_match.group(1))
            module_num = int(module_match.group(2))
            docs.append((module_name, level_num, module_num, markdown_file))
    return docs


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


def normalize_base_title(raw_text: str, fallback: str) -> str:
    text = str(raw_text or "").strip()
    if "来源：" in text:
        text = text.split("来源：", 1)[0].strip()
    if "来源:" in text:
        text = text.split("来源:", 1)[0].strip()
    for sep in ("：", ":"):
        if sep in text:
            left = text.split(sep, 1)[0].strip()
            if left:
                text = left
                break
    text = text.strip().rstrip("。.;；")
    return text or fallback


def normalize_hover_text(raw_text: str) -> str:
    text = str(raw_text or "").strip()
    if "来源：" in text:
        text = text.split("来源：", 1)[0].strip()
    if "来源:" in text:
        text = text.split("来源:", 1)[0].strip()
    return text.strip().rstrip("。.;；")


def parse_upstream_refs(raw_text: str) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []

    # Support inline module reference style:
    # `B3` xxx基：L0.M0[R2,R3] + L0.M1[R2,R3]。来源：`...`
    source_split = re.split(r"来源[：:]", raw_text, maxsplit=1)
    before_source = source_split[0].strip()
    if "：" not in before_source and ":" not in before_source:
        return refs

    _, _, expr_tail = before_source.partition("：")
    if not expr_tail:
        _, _, expr_tail = before_source.partition(":")
    expr = expr_tail.strip().rstrip("。.;；")
    if "L" not in expr:
        return refs
    refs.extend(parse_upstream_expr(expr))
    if refs:
        return refs

    seen: set[tuple[str, str]] = set()
    for term_match in FRAMEWORK_UPSTREAM_SCAN_PATTERN.finditer(expr):
        framework_name = term_match.group("framework")
        ref = term_match.group("ref")
        rules = (term_match.group("rules") or "").strip()
        qualified_ref = f"{framework_name}.{ref}" if framework_name else ref
        ref_pair = (qualified_ref, rules)
        if ref_pair in seen:
            continue
        seen.add(ref_pair)
        refs.append(ref_pair)
    return refs


def parse_upstream_expr(expr: str) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    for part in expr.split("+"):
        term = part.strip()
        if not term:
            continue
        term_match = FRAMEWORK_UPSTREAM_TERM_PATTERN.fullmatch(term)
        if term_match is None:
            continue
        framework_name = term_match.group("framework")
        ref = term_match.group("ref")
        qualified_ref = f"{framework_name}.{ref}" if framework_name else ref
        refs.append((qualified_ref, (term_match.group("rules") or "").strip()))
    return refs


def compute_framework_group_order(
    framework_names: list[str],
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> list[str]:
    adjacency: dict[str, set[str]] = {name: set() for name in framework_names}
    indegree: dict[str, int] = {name: 0 for name in framework_names}
    node_framework_by_id = {
        str(node["id"]): str(node.get("module_name") or "")
        for node in nodes
        if isinstance(node.get("module_name"), str)
    }

    for edge in edges:
        if edge.get("relation") != "framework_module_growth":
            continue
        source_framework = node_framework_by_id.get(str(edge.get("from") or ""), "")
        target_framework = node_framework_by_id.get(str(edge.get("to") or ""), "")
        if not source_framework or not target_framework or source_framework == target_framework:
            continue
        if target_framework in adjacency[source_framework]:
            continue
        adjacency[source_framework].add(target_framework)
        indegree[target_framework] += 1

    ready = sorted(name for name in framework_names if indegree[name] == 0)
    heapq.heapify(ready)
    ordered: list[str] = []

    while ready:
        current = heapq.heappop(ready)
        ordered.append(current)
        for target in sorted(adjacency[current]):
            indegree[target] -= 1
            if indegree[target] == 0:
                heapq.heappush(ready, target)

    if len(ordered) < len(framework_names):
        remaining = sorted(name for name in framework_names if name not in ordered)
        ordered.extend(remaining)

    return ordered


def build_payload_from_framework(framework_dir: Path) -> tuple[dict[str, Any], list[str]]:
    docs = iter_framework_docs(framework_dir)
    if not docs:
        raise ValueError("no framework Lx-Mn-*.md files found under framework directory")

    module_level_files: dict[str, dict[int, list[str]]] = {}
    module_node_records: list[dict[str, Any]] = []
    module_growth_specs: list[dict[str, Any]] = []

    warnings: list[str] = []
    seen_warnings: set[str] = set()

    def add_warning(message: str) -> None:
        if message in seen_warnings:
            return
        seen_warnings.add(message)
        warnings.append(message)

    for module_name, level_num, module_num, markdown_file in docs:
        rel = markdown_file.relative_to(REPO_ROOT).as_posix()
        module_level_files.setdefault(module_name, {}).setdefault(level_num, []).append(rel)
        file_text = markdown_file.read_text(encoding="utf-8")
        file_module_id = f"M{module_num}"
        heading_title = find_first_h1_text(file_text, Path(markdown_file.name).stem)
        heading_line = find_first_h1_line(markdown_file)

        capability_entries: list[dict[str, str]] = []
        for capability_line_num, capability_line in iter_section_bullet_lines(file_text, "## 1."):
            capability_match = FRAMEWORK_CAPABILITY_ITEM_LINE_PATTERN.match(capability_line)
            if capability_match is None:
                continue
            capability_token = capability_match.group(1)
            capability_text = normalize_hover_text(capability_match.group(3))
            capability_entries.append(
                {
                    "token": capability_token,
                    "text": capability_text or capability_token,
                    "line": str(capability_line_num),
                }
            )

        base_entries: list[dict[str, Any]] = []
        for base_line_num, base_line in iter_section_bullet_lines(file_text, "## 3."):
            base_match = FRAMEWORK_BASE_ITEM_LINE_PATTERN.match(base_line)
            if base_match is None:
                continue
            base_index = int(base_match.group(2))
            base_text = base_match.group(3).strip()
            base_title = normalize_base_title(
                base_text,
                f"Base B{base_index}",
            )
            base_entries.append(
                {
                    "token": str(base_match.group(1)),
                    "base_index": base_index,
                    "base_line_num": base_line_num,
                    "base_title": base_title,
                    "base_hover_text": normalize_hover_text(base_text) or base_title,
                    "upstream_refs": parse_upstream_refs(base_text),
                }
            )

        if base_entries:
            logical_id = f"L{level_num}.{file_module_id}"
            first_base_line = int(base_entries[0]["base_line_num"])
            upstream_refs_set: set[tuple[str, str]] = set()
            for entry in base_entries:
                for source_ref, source_rules in list(entry["upstream_refs"]):
                    upstream_refs_set.add((str(source_ref), str(source_rules)))

            module_node_records.append(
                {
                    "mode": "file",
                    "module_name": module_name,
                    "level_num": level_num,
                    "logical_id": logical_id,
                    "logical_module": file_module_id,
                    "source_file": rel,
                    "source_line": first_base_line,
                    "doc_line": heading_line,
                    "module_title": Path(markdown_file.name).stem,
                    "heading_title": heading_title,
                    "capability_items": capability_entries,
                    "base_items": [
                        {
                            "token": str(entry["token"]),
                            "text": str(entry["base_hover_text"]),
                            "line": str(entry["base_line_num"]),
                        }
                        for entry in base_entries
                    ],
                }
            )
            module_growth_specs.append(
                {
                    "mode": "file",
                    "module_name": module_name,
                    "level_num": level_num,
                    "source_file": rel,
                    "source_line": first_base_line,
                    "target_ref": logical_id,
                    "upstream_refs": sorted(upstream_refs_set),
                }
            )
            continue

        add_warning(f"{rel}: no parseable B* in section ## 3.")

    for module_name in sorted(module_level_files):
        levels = sorted(module_level_files[module_name])
        if levels and levels[0] != 0:
            add_warning(
                f"module '{module_name}' has no L0 base (lowest existing level: L{levels[0]})."
            )
    max_level_by_module = {
        module_name: max(levels)
        for module_name, levels in module_level_files.items()
        if levels
    }

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    level_order_counter: dict[int, int] = {}
    module_node_id_by_qualified_ref: dict[str, str] = {}
    seen_module_refs: set[str] = set()

    node_seq = 0
    all_node_records: list[tuple[int, str, str, dict[str, Any]]] = []
    for record in module_node_records:
        all_node_records.append(
            (
                int(record["level_num"]),
                str(record["module_name"]),
                str(record["logical_id"]),
                record,
            )
        )
    all_node_records.sort(key=lambda item: (item[0], item[1], item[2]))

    for _, _, _, record in all_node_records:
        level_num = int(record["level_num"])
        module_name = str(record["module_name"])
        source_file = str(record["source_file"])

        node_seq += 1
        node_id = f"NODE-FW-{node_seq:04d}"
        level_order_counter[level_num] = level_order_counter.get(level_num, 0) + 1
        order = level_order_counter[level_num]

        if "logical_id" in record:
            logical_id = str(record["logical_id"])
            logical_module = str(record["logical_module"])
            module_title = str(record["module_title"])
            qualified_ref = f"{module_name}:{logical_id}"
            if qualified_ref in seen_module_refs:
                add_warning(
                    f"duplicate module node declaration ignored: {qualified_ref} ({source_file})"
                )
                node_seq -= 1
                level_order_counter[level_num] -= 1
                continue
            seen_module_refs.add(qualified_ref)
            module_node_id_by_qualified_ref[qualified_ref] = node_id

            description_parts = [
                f"module={module_name}",
                f"level=L{level_num}",
                f"node={logical_id}",
                f"file={source_file}",
            ]
            if module_title:
                description_parts.append(f"title={module_title}")

            nodes.append(
                {
                    "id": node_id,
                    "label": f"L{level_num}.{module_name}.{logical_module}",
                    "level": level_num,
                    "order": order,
                    "description": " | ".join(description_parts),
                    "source_file": source_file,
                    "source_line": int(record["source_line"]),
                    "doc_line": int(record.get("doc_line", record["source_line"])),
                    "module_name": module_name,
                    "module_ref": logical_id,
                    "module_title": str(record.get("heading_title") or module_title),
                    "capability_items": record.get("capability_items", []),
                    "base_items": record.get("base_items", []),
                }
            )
            continue

    module_growth_edge_accumulator: dict[tuple[str, str], dict[str, Any]] = {}
    for growth_spec in module_growth_specs:
        module_name = str(growth_spec["module_name"])
        level_num = int(growth_spec["level_num"])
        source_file = str(growth_spec["source_file"])
        source_line = int(growth_spec["source_line"])
        target_ref = str(growth_spec["target_ref"])
        explicit_upstream_refs: list[tuple[str, str]] = growth_spec.get("upstream_refs", [])

        target_node_id = module_node_id_by_qualified_ref.get(f"{module_name}:{target_ref}")
        if target_node_id is None:
            add_warning(
                (
                    f"{source_file}:{source_line}: module target '{target_ref}' is not declared "
                    "in current module directory"
                )
            )
            continue

        if explicit_upstream_refs:
            for source_ref, source_rules in explicit_upstream_refs:
                source_match = re.fullmatch(
                    r"(?:(?P<framework>[A-Za-z][A-Za-z0-9_-]*)\.)?L(?P<level>\d+)\.(?P<module>M\d+)",
                    source_ref,
                )
                if source_match is None:
                    continue
                source_framework = source_match.group("framework") or module_name
                source_level = int(source_match.group("level"))
                source_module = source_match.group("module")
                source_ref_local = f"L{source_level}.{source_module}"
                qualified_lookup = f"{source_framework}:{source_ref_local}"

                if source_framework == module_name and source_ref_local == target_ref:
                    add_warning(
                        (
                            f"{source_file}:{source_line}: self module ref ignored "
                            f"({source_ref} -> {target_ref})"
                        )
                    )
                    continue

                source_node_id = module_node_id_by_qualified_ref.get(qualified_lookup)
                if source_node_id is None:
                    add_warning(
                        (
                            f"{source_file}:{source_line}: upstream source '{source_ref}' not found "
                            f"for target '{target_ref}'"
                        )
                    )
                    continue

                edge_key = (source_node_id, target_node_id)
                edge_bucket = module_growth_edge_accumulator.setdefault(
                    edge_key,
                    {
                        "module_name": module_name,
                        "source_ref": source_ref,
                        "target_ref": target_ref,
                        "from_level": f"L{source_level}",
                        "to_level": f"L{level_num}",
                        "rules": set(),
                        "terms": set(),
                        "source_file": source_file,
                        "source_line": source_line,
                    },
                )
                if source_rules:
                    edge_bucket["rules"].add(source_rules)
                    edge_bucket["terms"].add(f"{source_ref}[{source_rules}]")
                else:
                    edge_bucket["terms"].add(source_ref)
            continue

        if level_num == 0 or level_num == max_level_by_module.get(module_name, level_num):
            continue

        add_warning(
            (
                f"{source_file}:{source_line}: no explicit upstream module refs found for '{target_ref}'"
            )
        )

    for (source_node_id, target_node_id), edge_bucket in sorted(
        module_growth_edge_accumulator.items(),
        key=lambda item: (item[1]["from_level"], item[1]["to_level"], item[1]["source_ref"], item[1]["target_ref"]),
    ):
        rules = sorted(str(rule) for rule in edge_bucket["rules"] if str(rule).strip())
        terms = sorted(str(term) for term in edge_bucket["terms"] if str(term).strip())
        edges.append(
            {
                "from": source_node_id,
                "to": target_node_id,
                "relation": "framework_module_growth",
                "module": edge_bucket["module_name"],
                "from_level": edge_bucket["from_level"],
                "to_level": edge_bucket["to_level"],
                "source_ref": edge_bucket["source_ref"],
                "target_ref": edge_bucket["target_ref"],
                "rules": " | ".join(rules),
                "terms": " + ".join(terms),
                "source_file": edge_bucket["source_file"],
                "source_line": edge_bucket["source_line"],
            }
        )

    levels = sorted({node["level"] for node in nodes})
    level_labels = {str(level): f"L{level} 标准层" for level in levels}
    framework_names = sorted({str(record["module_name"]) for record in module_node_records})
    framework_order = compute_framework_group_order(framework_names, nodes, edges)
    framework_level_counts: dict[str, dict[int, int]] = {name: {} for name in framework_names}
    for node in nodes:
        framework_name = str(node.get("module_name") or "")
        if not framework_name:
            continue
        level_num = int(node["level"])
        framework_level_counts.setdefault(framework_name, {})
        framework_level_counts[framework_name][level_num] = (
            framework_level_counts[framework_name].get(level_num, 0) + 1
        )
    framework_groups = [
        {
            "name": framework_name,
            "order": order,
            "local_levels": sorted(framework_level_counts.get(framework_name, {})),
            "level_node_counts": {
                str(level): count
                for level, count in sorted(framework_level_counts.get(framework_name, {}).items())
            },
        }
        for order, framework_name in enumerate(framework_order)
    ]

    description = (
        "从 framework/<module>/Lx-Mn-*.md 自动生成；"
        "模块级节点为文件级 M 编号（Lx.Mn），边来自基中显式上游模块引用；"
        "按 framework 文件夹分组展示，组间位置由跨框架引用决定；"
        "Lx 只表示各 framework 自己的本地层。"
    )
    if warnings:
        description = f"{description} 警告数量={len(warnings)}。"

    root = {
        "title": "框架标准树结构图",
        "description": description,
        "level_labels": level_labels,
        "layout_mode": "framework_columns",
        "framework_groups": framework_groups,
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
