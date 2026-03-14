from __future__ import annotations

import argparse
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
    parser = argparse.ArgumentParser(description="Generate evidence tree views derived from canonical.json.")
    parser.add_argument(
        "--project-file",
        default=str(DEFAULT_PROJECT_FILE.relative_to(REPO_ROOT)),
        help="path to the project.toml file",
    )
    parser.add_argument("--output-json", required=True, help="path to generated evidence tree JSON")
    parser.add_argument("--output-html", required=True, help="path to generated evidence tree HTML")
    return parser


def _evidence_payload(project_file: str, canonical_path: str, canonical: dict[str, object]) -> dict[str, object]:
    project = canonical["project"]
    if not isinstance(project, dict):
        raise ValueError("canonical.project must be an object")
    framework = canonical["framework"]
    if not isinstance(framework, dict):
        raise ValueError("canonical.framework must be an object")
    modules = framework["modules"]
    if not isinstance(modules, list):
        raise ValueError("canonical.framework.modules must be a list")
    project_id = str(project["project_id"])
    project_node_id = f"project:{project_id}"
    canonical_node_id = f"{project_node_id}:canonical"
    nodes = [
        {
            "id": project_node_id,
            "label": f"Project {project_id}",
            "source_file": project_file,
            "node_kind": "project",
        },
        {
            "id": canonical_node_id,
            "label": "canonical.json",
            "source_file": canonical_path,
            "node_kind": "canonical",
        },
    ]
    edges = [
        {
            "from": project_node_id,
            "to": canonical_node_id,
            "relation": "tree_child",
        }
    ]
    for item in modules:
        if not isinstance(item, dict):
            continue
        module_id = str(item["module_id"])
        framework_file = str(item["framework_file"])
        nodes.append(
            {
                "id": module_id,
                "label": f"{module_id} {item.get('title_cn', '')}".strip(),
                "source_file": framework_file,
                "node_kind": "framework_module",
            }
        )
        edges.append(
            {
                "from": canonical_node_id,
                "to": module_id,
                "relation": "tree_child",
            }
        )
    return {
        "root": {
            "nodes": nodes,
            "edges": edges,
        }
    }


def _evidence_html(payload: dict[str, object]) -> str:
    root = payload.get("root", {})
    if not isinstance(root, dict):
        raise ValueError("evidence payload root must be an object")
    nodes = root.get("nodes", [])
    if not isinstance(nodes, list):
        raise ValueError("evidence payload nodes must be a list")
    items = "".join(
        f"<li><strong>{escape(str(node.get('id', '')))}</strong> - {escape(str(node.get('label', '')))}</li>"
        for node in nodes
        if isinstance(node, dict)
    )
    return (
        "<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        "<title>Shelf Evidence Tree</title>"
        "<style>body{font-family:\"IBM Plex Sans\",\"Segoe UI\",sans-serif;padding:24px;line-height:1.6}"
        "ul{padding-left:20px}</style></head><body><h1>Shelf Evidence Tree</h1><ul>"
        + items
        + "</ul></body></html>\n"
    )


def main() -> int:
    args = _build_parser().parse_args()
    assembly = materialize_project_runtime(args.project_file)
    artifacts = assembly.generated_artifacts
    if artifacts is None:
        raise ValueError("generated artifact paths are required after materialization")
    payload = _evidence_payload(assembly.project_file, artifacts.canonical_json, assembly.canonical)
    output_json = Path(args.output_json)
    output_html = Path(args.output_html)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_html.write_text(_evidence_html(payload), encoding="utf-8")
    print(f"[OK] evidence tree JSON generated: {output_json}")
    print(f"[OK] evidence tree HTML generated: {output_html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
