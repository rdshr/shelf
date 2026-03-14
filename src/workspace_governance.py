from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hierarchy_models import HierarchyEdge, HierarchyGraph, HierarchyNode
from project_runtime import discover_framework_driven_projects


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKSPACE_GOVERNANCE_JSON = REPO_ROOT / "docs/hierarchy/shelf_governance_tree.json"
DEFAULT_WORKSPACE_GOVERNANCE_HTML = REPO_ROOT / "docs/hierarchy/shelf_governance_tree.html"
DEFAULT_PROJECT_DISCOVERY_AUDIT_JSON = REPO_ROOT / "docs/hierarchy/project_discovery_audit.json"
DEFAULT_PROJECT_DISCOVERY_AUDIT_MD = REPO_ROOT / "docs/project_discovery_audit.md"


def _relative(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must decode into object")
    return payload


def build_workspace_governance_payload() -> dict[str, Any]:
    projects = discover_framework_driven_projects()
    root_id = "workspace:shelf"
    projects_id = "workspace:shelf:projects"
    evidence_id = "workspace:shelf:evidence"
    nodes = [
        HierarchyNode(root_id, "Shelf Workspace", 0, "workspace root"),
        HierarchyNode(projects_id, "Projects", 1, "configured framework-package projects"),
        HierarchyNode(evidence_id, "Evidence", 1, "canonical-derived workspace evidence"),
    ]
    edges = [
        HierarchyEdge(root_id, projects_id, "tree_child", {}),
        HierarchyEdge(root_id, evidence_id, "tree_child", {}),
    ]

    for index, project in enumerate(projects, start=1):
        project_node_id = f"project:{project.project_id}"
        nodes.append(
            HierarchyNode(
                project_node_id,
                project.project_id,
                2,
                f"runtime_scene={project.runtime_scene} | project_file={project.project_file}",
                order=index,
                metadata={"source_file": project.project_file, "node_kind": "project"},
            )
        )
        edges.append(HierarchyEdge(projects_id, project_node_id, "tree_child", {}))

        canonical_path = REPO_ROOT / project.canonical_graph_path
        governance_file = project.artifact_contract.get("governance_tree_json")
        governance_path = REPO_ROOT / project.generated_dir / governance_file if governance_file else None
        nodes.append(
            HierarchyNode(
                f"{project_node_id}:canonical",
                "canonical_graph.json",
                3,
                f"machine truth | file={_relative(canonical_path)}",
                metadata={"source_file": _relative(canonical_path), "node_kind": "canonical"},
            )
        )
        edges.append(HierarchyEdge(project_node_id, f"{project_node_id}:canonical", "tree_child", {}))
        if governance_path is not None:
            nodes.append(
                HierarchyNode(
                    f"{project_node_id}:governance_tree",
                    "governance_tree.json",
                    3,
                    f"derived view | file={_relative(governance_path)}",
                    metadata={"source_file": _relative(governance_path), "node_kind": "derived_view"},
                )
            )
            edges.append(HierarchyEdge(project_node_id, f"{project_node_id}:governance_tree", "tree_child", {}))

        if canonical_path.exists():
            canonical = _read_json(canonical_path)
            module_ids = canonical.get("layers", {}).get("code", {}).get("package_compile_order", [])
            if isinstance(module_ids, list):
                for module_order, module_id in enumerate(module_ids, start=1):
                    if not isinstance(module_id, str):
                        continue
                    module_node_id = f"{project_node_id}:module:{module_id}"
                    nodes.append(
                        HierarchyNode(
                            module_node_id,
                            module_id,
                            4,
                            "compiled framework package",
                            order=module_order,
                            metadata={"node_kind": "compiled_package"},
                        )
                    )
                    edges.append(HierarchyEdge(f"{project_node_id}:canonical", module_node_id, "tree_child", {}))

    graph = HierarchyGraph(
        title="Shelf Workspace Governance",
        description="Workspace hierarchy derived from project discovery and canonical-generated evidence.",
        level_labels={0: "Workspace", 1: "Root", 2: "Project", 3: "Artifact", 4: "Compiled Package"},
        nodes=nodes,
        edges=edges,
        storage_key_stem="governanceTree",
    )
    return {
        **graph.to_payload_dict(),
        "governance": {
            "schema_version": "workspace-governance/v2",
            "project_count": len(projects),
        },
    }
