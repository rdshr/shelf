from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from generate_module_hierarchy_html import render_html
from hierarchy_models import HierarchyEdge, HierarchyGraph, HierarchyNode
from project_runtime import DEFAULT_PROJECT_FILE, materialize_project_runtime

MODULE_ID_PATTERN = re.compile(
    r"^(?P<framework>[A-Za-z][A-Za-z0-9_]*)\.L(?P<level>\d+)\.M(?P<module>\d+)$"
)


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


def _parse_module_id(module_id: str) -> tuple[str, int, int]:
    match = MODULE_ID_PATTERN.fullmatch(module_id)
    if match is None:
        raise ValueError(f"invalid framework module id: {module_id}")
    return (
        match.group("framework"),
        int(match.group("level")),
        int(match.group("module")),
    )


def _find_first_h1_line(relative_file: str) -> int:
    file_path = REPO_ROOT / relative_file
    if not file_path.exists():
        return 1
    for index, line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.lstrip().startswith("# "):
            return index
    return 1


def _evidence_graph(project_file: str, canonical_path: str, canonical: dict[str, object]) -> HierarchyGraph:
    project = canonical["project"]
    if not isinstance(project, dict):
        raise ValueError("canonical.project must be an object")
    framework = canonical["framework"]
    if not isinstance(framework, dict):
        raise ValueError("canonical.framework must be an object")
    framework_modules = framework["modules"]
    if not isinstance(framework_modules, list):
        raise ValueError("canonical.framework.modules must be a list")
    config = canonical["config"]
    if not isinstance(config, dict):
        raise ValueError("canonical.config must be an object")
    config_modules = config["modules"]
    if not isinstance(config_modules, list):
        raise ValueError("canonical.config.modules must be a list")
    code = canonical["code"]
    if not isinstance(code, dict):
        raise ValueError("canonical.code must be an object")
    code_modules = code["modules"]
    if not isinstance(code_modules, list):
        raise ValueError("canonical.code.modules must be a list")
    evidence = canonical["evidence"]
    if not isinstance(evidence, dict):
        raise ValueError("canonical.evidence must be an object")
    evidence_modules = evidence["modules"]
    if not isinstance(evidence_modules, list):
        raise ValueError("canonical.evidence.modules must be a list")
    links = canonical["links"]
    if not isinstance(links, dict):
        raise ValueError("canonical.links must be an object")
    framework_module_lookup = {
        str(item["module_id"]): item
        for item in framework_modules
        if isinstance(item, dict) and isinstance(item.get("module_id"), str)
    }
    config_module_lookup = {
        str(item["module_id"]): item
        for item in config_modules
        if isinstance(item, dict) and isinstance(item.get("module_id"), str)
    }
    code_module_lookup = {
        str(item["module_id"]): item
        for item in code_modules
        if isinstance(item, dict) and isinstance(item.get("module_id"), str)
    }
    evidence_module_lookup = {
        str(item["module_id"]): item
        for item in evidence_modules
        if isinstance(item, dict) and isinstance(item.get("module_id"), str)
    }

    project_id = str(project["project_id"])
    project_node_id = f"project:{project_id}"
    canonical_node_id = f"{project_node_id}:canonical"
    nodes = [
        HierarchyNode(
            node_id=project_node_id,
            label=f"project:{project_id}",
            level=0,
            description=f"project={project_id} | file={project_file}",
            metadata={
                "source_file": project_file,
                "source_line": 1,
                "doc_line": 1,
                "node_kind": "project",
                "module_title": f"Project {project_id}",
                "hover_kicker": "Project",
                "capability_items": [{"token": "Config", "text": project_file}],
                "base_items": [{"token": "Truth", "text": canonical_path}],
            },
        ),
        HierarchyNode(
            node_id=canonical_node_id,
            label="canonical.json",
            level=1,
            description=f"artifact=canonical.json | file={canonical_path}",
            metadata={
                "source_file": canonical_path,
                "source_line": 1,
                "doc_line": 1,
                "node_kind": "canonical",
                "module_title": "Canonical JSON",
                "hover_kicker": "Canonical Artifact",
                "capability_items": [{"token": "Schema", "text": str(canonical.get("schema_version") or "")}],
                "base_items": [{"token": "Layers", "text": "framework / config / code / evidence"}],
            },
        ),
    ]
    edges = [
        HierarchyEdge(
            source=project_node_id,
            target=canonical_node_id,
            relation="tree_child",
            metadata={},
        )
    ]

    ordered_modules: list[tuple[str, int, int, dict[str, object]]] = []
    for item in framework_modules:
        if not isinstance(item, dict):
            continue
        module_id = str(item["module_id"])
        framework_name, level_num, module_num = _parse_module_id(module_id)
        ordered_modules.append((framework_name, level_num, module_num, item))
    ordered_modules.sort(key=lambda item: (item[1], item[0], item[2]))

    for framework_name, level_num, module_num, item in ordered_modules:
        module_id = str(item["module_id"])
        framework_file = str(item["framework_file"])
        doc_line = _find_first_h1_line(framework_file)
        title_cn = str(item.get("title_cn") or "")
        title_en = str(item.get("title_en") or "")
        config_module = config_module_lookup.get(module_id, {})
        code_module = code_module_lookup.get(module_id, {})
        evidence_module = evidence_module_lookup.get(module_id, {})
        config_class = str(config_module.get("class_name") or "")
        code_class = str(code_module.get("class_name") or "")
        evidence_class = str(evidence_module.get("class_name") or "")
        boundaries = item.get("boundaries")
        config_node_id = f"config:{module_id}"
        code_node_id = f"code:{module_id}"
        evidence_node_id = f"evidence:{module_id}"
        framework_node_id = f"framework:{module_id}"

        nodes.append(
            HierarchyNode(
                node_id=framework_node_id,
                label=f"framework:{module_id}",
                level=2,
                order=module_num,
                description=(
                    f"layer=framework | module={module_id} | framework={framework_name} | "
                    f"level=L{level_num} | file={framework_file}"
                ),
                metadata={
                    "source_file": framework_file,
                    "source_line": doc_line,
                    "doc_line": doc_line,
                    "node_kind": "framework_module",
                    "module_name": framework_name,
                    "module_ref": f"L{level_num}.M{module_num}",
                    "module_title": title_cn or title_en or module_id,
                    "hover_kicker": "Evidence Trace Node",
                    "capability_items": [
                        {"token": "Config", "text": config_class or "未记录"},
                        {"token": "Code", "text": code_class or "未记录"},
                        {"token": "Evidence", "text": evidence_class or "未记录"},
                    ],
                    "base_items": [
                        {"token": "Framework", "text": framework_file},
                        {
                            "token": "Boundaries",
                            "text": ", ".join(
                                str(boundary.get("boundary_id") or "")
                                for boundary in boundaries
                                if isinstance(boundary, dict)
                            )
                            if isinstance(boundaries, list)
                            else "无",
                        },
                    ],
                },
            )
        )
        edges.append(
            HierarchyEdge(
                source=canonical_node_id,
                target=framework_node_id,
                relation="tree_child",
                metadata={},
            )
        )
        config_source_file = str(config_module.get("source_ref", {}).get("file_path") or project_file)
        nodes.append(
            HierarchyNode(
                node_id=config_node_id,
                label=f"config:{module_id}",
                level=3,
                order=module_num,
                description=(
                    f"layer=config | module={module_id} | class={config_class or 'n/a'} | "
                    f"file={config_source_file}"
                ),
                metadata={
                    "source_file": config_source_file,
                    "source_line": 1,
                    "doc_line": 1,
                    "node_kind": "config_module",
                    "module_name": framework_name,
                    "module_ref": f"L{level_num}.M{module_num}",
                    "module_title": title_cn or title_en or module_id,
                    "hover_kicker": "Config Module",
                    "capability_items": [{"token": "Class", "text": config_class or "未记录"}],
                    "base_items": [
                        {
                            "token": "Bindings",
                            "text": ", ".join(
                                str(entry.get("boundary_id") or "")
                                for entry in config_module.get("compiled_config_export", {}).get("boundary_bindings", [])
                                if isinstance(entry, dict)
                            )
                            or "无",
                        }
                    ],
                },
            )
        )
        edges.append(
            HierarchyEdge(
                source=framework_node_id,
                target=config_node_id,
                relation="tree_child",
                metadata={"link_role": "mainline"},
            )
        )
        code_source_file = str(code_module.get("source_ref", {}).get("file_path") or "src/project_runtime/code_layer.py")
        nodes.append(
            HierarchyNode(
                node_id=code_node_id,
                label=f"code:{module_id}",
                level=4,
                order=module_num,
                description=(
                    f"layer=code | module={module_id} | class={code_class or 'n/a'} | "
                    f"file={code_source_file}"
                ),
                metadata={
                    "source_file": code_source_file,
                    "source_line": 1,
                    "doc_line": 1,
                    "node_kind": "code_module",
                    "module_name": framework_name,
                    "module_ref": f"L{level_num}.M{module_num}",
                    "module_title": title_cn or title_en or module_id,
                    "hover_kicker": "Code Module",
                    "capability_items": [
                        {
                            "token": "Owner",
                            "text": str(code_module.get("code_bindings", {}).get("owner", {}).get("owner_class_name") or "未记录"),
                        }
                    ],
                    "base_items": [
                        {
                            "token": "Slots",
                            "text": str(len(code_module.get("code_bindings", {}).get("implementation_slots", []))),
                        }
                    ],
                },
            )
        )
        edges.append(
            HierarchyEdge(
                source=config_node_id,
                target=code_node_id,
                relation="tree_child",
                metadata={"link_role": "mainline"},
            )
        )
        evidence_source_file = str(
            evidence_module.get("source_ref", {}).get("file_path") or "src/project_runtime/evidence_layer.py"
        )
        nodes.append(
            HierarchyNode(
                node_id=evidence_node_id,
                label=f"evidence:{module_id}",
                level=5,
                order=module_num,
                description=(
                    f"layer=evidence | module={module_id} | class={evidence_class or 'n/a'} | "
                    f"file={evidence_source_file}"
                ),
                metadata={
                    "source_file": evidence_source_file,
                    "source_line": 1,
                    "doc_line": 1,
                    "node_kind": "evidence_module",
                    "module_name": framework_name,
                    "module_ref": f"L{level_num}.M{module_num}",
                    "module_title": title_cn or title_en or module_id,
                    "hover_kicker": "Evidence Module",
                    "capability_items": [{"token": "Class", "text": evidence_class or "未记录"}],
                    "base_items": [{"token": "Source", "text": code_class or "未记录"}],
                },
            )
        )
        edges.append(
            HierarchyEdge(
                source=code_node_id,
                target=evidence_node_id,
                relation="tree_child",
                metadata={"link_role": "mainline"},
            )
        )

    level_labels = {
        0: "Project",
        1: "Canonical",
        2: "Framework",
        3: "Config",
        4: "Code",
        5: "Evidence",
    }

    return HierarchyGraph(
        title="Shelf Evidence Tree",
        description=(
            "从 canonical.json 派生，沿 Framework -> Config -> Code -> Evidence 主链展示模块证据结构；"
            "boundary/base 绑定只保留为 canonical 内的辅助追溯视图，不再作为树图主链。"
        ),
        foot_text="图中按四层主链展示 project / canonical / framework / config / code / evidence 的逐层关系。",
        level_labels=level_labels,
        nodes=nodes,
        edges=edges,
        storage_key_stem="evidenceTree",
    )


def main() -> int:
    args = _build_parser().parse_args()
    assembly = materialize_project_runtime(args.project_file)
    artifacts = assembly.generated_artifacts
    if artifacts is None:
        raise ValueError("generated artifact paths are required after materialization")
    graph = _evidence_graph(assembly.project_file, artifacts.canonical_json, assembly.canonical)
    payload = graph.to_payload_dict()
    output_json = Path(args.output_json)
    output_html = Path(args.output_html)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    render_html(graph, output_html, width=1680, height=1080)
    print(f"[OK] evidence tree JSON generated: {output_json}")
    print(f"[OK] evidence tree HTML generated: {output_html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
