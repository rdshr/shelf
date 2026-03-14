from __future__ import annotations

import argparse
from collections import defaultdict
from html import escape
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from project_runtime import DEFAULT_PROJECT_FILE, materialize_project_runtime


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate framework tree views derived from canonical.json.")
    parser.add_argument(
        "--project-file",
        default=str(DEFAULT_PROJECT_FILE.relative_to(REPO_ROOT)),
        help="path to the project.toml file",
    )
    parser.add_argument("--output-json", required=True, help="path to generated framework tree JSON")
    parser.add_argument("--output-html", required=True, help="path to generated framework tree HTML")
    return parser


def _framework_payload(canonical: dict[str, object]) -> dict[str, object]:
    framework = canonical["framework"]
    if not isinstance(framework, dict):
        raise ValueError("canonical.framework must be an object")
    modules = framework["modules"]
    if not isinstance(modules, list):
        raise ValueError("canonical.framework.modules must be a list")
    nodes = []
    edges = []
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for item in modules:
        if not isinstance(item, dict):
            continue
        module_id = str(item["module_id"])
        framework_file = str(item["framework_file"])
        label = f"{module_id} {item.get('title_cn', '')}".strip()
        nodes.append(
            {
                "id": module_id,
                "label": label,
                "source_file": framework_file,
                "node_kind": "framework_module",
            }
        )
        for upstream in item.get("export_surface", {}).get("upstream_module_ids", []):
            edges.append(
                {
                    "from": str(upstream),
                    "to": module_id,
                    "relation": "tree_child",
                }
            )
        grouped[module_id.split(".")[0]].append(item)
    return {
        "root": {
            "nodes": nodes,
            "edges": edges,
        },
        "grouped_frameworks": {
            name: [str(item["module_id"]) for item in sorted(items, key=lambda value: str(value["module_id"]))]
            for name, items in sorted(grouped.items())
        },
    }


def _framework_html(payload: dict[str, object]) -> str:
    grouped = payload.get("grouped_frameworks", {})
    if not isinstance(grouped, dict):
        raise ValueError("framework grouped payload must be a dict")
    groups_html = []
    for framework_name, module_ids in grouped.items():
        if not isinstance(module_ids, list):
            continue
        items = "".join(f"<li>{escape(str(module_id))}</li>" for module_id in module_ids)
        groups_html.append(f"<section><h2>{escape(str(framework_name))}</h2><ul>{items}</ul></section>")
    return (
        "<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        "<title>Shelf Framework Tree</title>"
        "<style>body{font-family:\"IBM Plex Sans\",\"Segoe UI\",sans-serif;padding:24px;line-height:1.6}"
        "section{margin-bottom:24px}h1,h2{margin:0 0 12px}ul{margin:0;padding-left:20px}</style>"
        "</head><body><h1>Shelf Framework Tree</h1>"
        + "".join(groups_html)
        + "</body></html>\n"
    )


def main() -> int:
    args = _build_parser().parse_args()
    assembly = materialize_project_runtime(args.project_file)
    payload = _framework_payload(assembly.canonical)
    output_json = Path(args.output_json)
    output_html = Path(args.output_html)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_html.write_text(_framework_html(payload), encoding="utf-8")
    print(f"[OK] framework tree JSON generated: {output_json}")
    print(f"[OK] framework tree HTML generated: {output_html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
