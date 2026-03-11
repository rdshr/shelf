from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, cast

from project_runtime import discover_framework_driven_projects, load_registered_project
from project_runtime.project_governance import (
    build_project_discovery_audit,
    render_project_discovery_audit_markdown,
)
from project_runtime.governance import build_governance_tree
from standards_tree import build_standards_tree


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKSPACE_GOVERNANCE_JSON = REPO_ROOT / "docs/hierarchy/shelf_governance_tree.json"
DEFAULT_WORKSPACE_GOVERNANCE_HTML = REPO_ROOT / "docs/hierarchy/shelf_governance_tree.html"
DEFAULT_PROJECT_DISCOVERY_AUDIT_JSON = REPO_ROOT / "docs/hierarchy/project_discovery_audit.json"
DEFAULT_PROJECT_DISCOVERY_AUDIT_MD = REPO_ROOT / "docs/project_discovery_audit.md"
WORKSPACE_GOVERNANCE_VERSION = "workspace-governance/v1"
MAPPING_REGISTRY_PATH = REPO_ROOT / "mapping/mapping_registry.json"
SECTION_HEADER_PATTERN = re.compile(r"^\s*\[([A-Za-z0-9_.-]+)\]\s*$")


def discover_workspace_product_spec_files(projects_dir: Path | None = None) -> list[Path]:
    root = projects_dir or (REPO_ROOT / "projects")
    return [
        (REPO_ROOT / item.product_spec_file).resolve()
        for item in discover_framework_driven_projects(root)
    ]


def _relative(path: Path | str) -> str:
    candidate = Path(path)
    if candidate.is_absolute():
        try:
            return candidate.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            return str(candidate)
    return candidate.as_posix()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must decode into object")
    return payload


def _first_heading_line(file_path: Path) -> int:
    if not file_path.exists():
        return 1
    for index, line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.lstrip().startswith("# "):
            return index
    return 1


def _toml_section_line(file_path: Path, section_path: str) -> int:
    if not file_path.exists():
        return 1
    wanted = section_path.strip()
    for index, line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), start=1):
        match = SECTION_HEADER_PATTERN.match(line)
        if match is None:
            continue
        if match.group(1).strip() == wanted:
            return index
    return 1


def _node_label(title: str | None, fallback: str) -> str:
    if isinstance(title, str) and title.strip():
        return title.strip()
    return fallback


def _node_description(parts: dict[str, Any]) -> str:
    ordered: list[str] = []
    for key in (
        "kind",
        "layer",
        "project_id",
        "file",
        "locator",
        "object_id",
        "role_id",
        "candidate_id",
        "symbol_id",
        "artifact",
        "minimality_status",
        "audit_classification",
    ):
        value = parts.get(key)
        if value in (None, "", [], {}):
            continue
        ordered.append(f"{key}={value}")
    return " | ".join(ordered) or "workspace governance node"


def _mapping_tree_to_hierarchy_nodes() -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    raw_tree = build_standards_tree()

    standards_root_id = "workspace:shelf:standards"
    nodes: list[dict[str, Any]] = [
        {
            "id": standards_root_id,
            "label": "Standards",
            "level": 1,
            "description": "kind=standards_root | layer=Standards",
            "source_file": _relative(MAPPING_REGISTRY_PATH),
            "source_line": 1,
            "node_kind": "standards_root",
            "layer": "Standards",
        }
    ]
    edges: list[dict[str, Any]] = []

    def walk(node_obj: dict[str, Any], parent_id: str, depth: int) -> None:
        node_id = f"standards:{str(node_obj.get('id') or '').strip()}"
        kind = str(node_obj.get("kind") or "").strip() or "file"
        level_value = str(node_obj.get("level") or "").strip()
        rel_file = str(node_obj.get("file") or "").strip()
        source_file = rel_file or _relative(MAPPING_REGISTRY_PATH)
        source_line = _first_heading_line(REPO_ROOT / rel_file) if rel_file else 1
        label = Path(rel_file).stem if rel_file else node_id.split(":")[-1]
        nodes.append(
            {
                "id": node_id,
                "label": label,
                "level": depth,
                "description": _node_description(
                    {
                        "kind": kind,
                        "layer": "Standards",
                        "file": rel_file,
                        "registry_level": level_value,
                    }
                ),
                "source_file": source_file,
                "source_line": source_line,
                "node_kind": kind,
                "layer": "Standards",
                "registry_level": level_value,
                "raw_node_id": str(node_obj.get("id") or ""),
            }
        )
        edges.append({"from": parent_id, "to": node_id, "relation": "tree_child"})
        children = node_obj.get("children")
        if not isinstance(children, list):
            raise ValueError(f"mapping tree children must be list for {node_id}")
        for child in children:
            if not isinstance(child, dict):
                raise ValueError(f"mapping tree child must be object for {node_id}")
            walk(child, node_id, depth + 1)

    walk(raw_tree, standards_root_id, 2)
    return nodes, edges, standards_root_id


def _project_node_source_line(node: dict[str, Any]) -> int:
    bindings = node.get("bindings")
    if isinstance(bindings, list):
        for item in bindings:
            if isinstance(item, dict) and isinstance(item.get("line"), int):
                return int(item["line"])
    kind = str(node.get("kind") or "").strip()
    rel_file = str(node.get("file") or "").strip()
    if not rel_file:
        return 1
    file_path = REPO_ROOT / rel_file
    if kind == "product_section":
        return _toml_section_line(file_path, str(node.get("ref_id") or ""))
    if kind == "implementation_section":
        return _toml_section_line(file_path, str(node.get("ref_id") or ""))
    return _first_heading_line(file_path)


def _project_tree_to_hierarchy_nodes(
    project_tree: dict[str, Any],
    *,
    project_id: str,
    product_spec_file: str,
    parent_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    tree_nodes = project_tree.get("nodes")
    if not isinstance(tree_nodes, list):
        raise ValueError(f"governance tree for {project_id} must contain nodes list")
    node_index: dict[str, dict[str, Any]] = {}
    for node in tree_nodes:
        if not isinstance(node, dict):
            raise ValueError(f"governance tree node for {project_id} must be object")
        node_id = str(node.get("node_id") or "").strip()
        if not node_id:
            raise ValueError(f"governance tree node for {project_id} is missing node_id")
        node_index[node_id] = node

    project_root_id = str(project_tree.get("root_node_id") or "").strip()
    if not project_root_id or project_root_id not in node_index:
        raise ValueError(f"governance tree for {project_id} has invalid root_node_id")

    level_cache: dict[str, int] = {}

    def depth(node_id: str) -> int:
        cached = level_cache.get(node_id)
        if cached is not None:
            return cached
        node = node_index[node_id]
        parent = node.get("parent")
        if parent is None:
            level_cache[node_id] = 2
            return 2
        if not isinstance(parent, str) or parent not in node_index:
            level_cache[node_id] = 2
            return 2
        level_cache[node_id] = depth(parent) + 1
        return level_cache[node_id]

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    for node_id in sorted(node_index):
        node = node_index[node_id]
        rel_file = str(node.get("file") or "").strip()
        label = _node_label(str(node.get("title") or ""), node_id.split(":")[-1])
        nodes.append(
            {
                "id": node_id,
                "label": label,
                "level": depth(node_id),
                "description": _node_description(
                    {
                        "kind": node.get("kind"),
                        "layer": node.get("layer"),
                        "project_id": project_id,
                        "file": rel_file,
                        "locator": node.get("locator"),
                        "object_id": node.get("object_id"),
                        "role_id": node.get("role_id"),
                        "candidate_id": node.get("candidate_id"),
                        "symbol_id": node.get("symbol_id"),
                        "artifact": node.get("artifact"),
                        "minimality_status": node.get("minimality_status"),
                        "audit_classification": node.get("audit_classification"),
                    }
                ),
                "source_file": rel_file or product_spec_file,
                "source_line": _project_node_source_line(node),
                "node_kind": node.get("kind"),
                "layer": node.get("layer"),
                "project_id": project_id,
                "project_product_spec_file": product_spec_file,
                "parent_node_id": node.get("parent"),
                "derived_from": list(node.get("derived_from") or []),
                "owner": node.get("owner"),
                "artifact": node.get("artifact"),
                "symbol_id": node.get("symbol_id"),
                "object_id": node.get("object_id"),
                "role_id": node.get("role_id"),
                "candidate_id": node.get("candidate_id"),
                "symbol_kind": node.get("symbol_kind"),
                "risk": node.get("risk"),
                "validator": node.get("validator"),
                "minimality_status": node.get("minimality_status"),
                "audit_classification": node.get("audit_classification"),
            }
        )
        parent_node_id = node.get("parent")
        edge_parent = parent_id if parent_node_id is None else str(parent_node_id)
        edges.append({"from": edge_parent, "to": node_id, "relation": "tree_child"})

    return nodes, edges, project_root_id


def _build_governance_indexes(nodes: list[dict[str, Any]], project_roots: dict[str, str]) -> dict[str, Any]:
    file_index: dict[str, list[str]] = {}
    parent_index: dict[str, str | None] = {}
    children_index: dict[str, list[str]] = {}
    derived_index: dict[str, list[str]] = {}
    reverse_derived_index: dict[str, list[str]] = {}
    project_index: dict[str, dict[str, Any]] = {}

    for node in nodes:
        node_id = str(node["id"])
        rel_file = str(node.get("source_file") or "").strip()
        if rel_file:
            file_index.setdefault(rel_file, []).append(node_id)
        parent = node.get("parent_node_id")
        if parent is None and node_id in project_roots.values():
            parent = "workspace:shelf:projects"
        parent_index[node_id] = str(parent) if isinstance(parent, str) else None
        children_index.setdefault(node_id, [])
        if isinstance(parent, str):
            children_index.setdefault(parent, []).append(node_id)
        derived = [str(item) for item in list(node.get("derived_from") or []) if str(item).strip()]
        derived_index[node_id] = derived
        for upstream in derived:
            reverse_derived_index.setdefault(upstream, []).append(node_id)
        project_id = str(node.get("project_id") or "").strip()
        if project_id:
            project_entry = project_index.setdefault(
                project_id,
                {
                    "root_node_id": project_roots.get(project_id, ""),
                    "product_spec_file": str(node.get("project_product_spec_file") or ""),
                    "node_ids": [],
                    "evidence_root_id": "",
                },
            )
            project_entry["node_ids"].append(node_id)
            if node.get("node_kind") == "evidence_root":
                project_entry["evidence_root_id"] = node_id

    return {
        "file_index": {key: sorted(value) for key, value in sorted(file_index.items())},
        "parent_index": parent_index,
        "children_index": {key: sorted(value) for key, value in sorted(children_index.items())},
        "derived_index": {key: sorted(value) for key, value in sorted(derived_index.items())},
        "reverse_derived_index": {
            key: sorted(value) for key, value in sorted(reverse_derived_index.items())
        },
        "project_index": project_index,
    }


def build_workspace_governance_payload(
    product_spec_files: list[Path] | None = None,
) -> dict[str, Any]:
    workspace_root_id = "workspace:shelf"
    standards_root_id = "workspace:shelf:standards"
    projects_root_id = "workspace:shelf:projects"
    evidence_root_id = "workspace:shelf:evidence"
    governance_json_rel = _relative(DEFAULT_WORKSPACE_GOVERNANCE_JSON)
    governance_html_rel = _relative(DEFAULT_WORKSPACE_GOVERNANCE_HTML)
    discovery_audit_json_rel = _relative(DEFAULT_PROJECT_DISCOVERY_AUDIT_JSON)
    discovery_audit_md_rel = _relative(DEFAULT_PROJECT_DISCOVERY_AUDIT_MD)
    discovery_audit = build_project_discovery_audit()

    nodes: list[dict[str, Any]] = [
        {
            "id": workspace_root_id,
            "label": "Shelf Workspace",
            "level": 0,
            "description": "kind=workspace_root | layer=Workspace",
            "source_file": "README.md",
            "source_line": 1,
            "node_kind": "workspace_root",
            "layer": "Workspace",
        },
        {
            "id": projects_root_id,
            "label": "Projects",
            "level": 1,
            "description": "kind=projects_root | layer=Projects",
            "source_file": "projects",
            "source_line": 1,
            "node_kind": "projects_root",
            "layer": "Projects",
            "parent_node_id": workspace_root_id,
        },
        {
            "id": evidence_root_id,
            "label": "Workspace Evidence",
            "level": 1,
            "description": "kind=workspace_evidence_root | layer=Workspace Evidence",
            "source_file": governance_json_rel,
            "source_line": 1,
            "node_kind": "workspace_evidence_root",
            "layer": "Workspace Evidence",
            "parent_node_id": workspace_root_id,
        },
        {
            "id": "workspace:shelf:evidence:artifact:governance_tree_json",
            "label": "shelf_governance_tree.json",
            "level": 2,
            "description": (
                "kind=workspace_evidence_artifact | layer=Workspace Evidence"
                f" | file={governance_json_rel} | artifact=governance_tree_json"
            ),
            "source_file": governance_json_rel,
            "source_line": 1,
            "node_kind": "workspace_evidence_artifact",
            "layer": "Workspace Evidence",
            "parent_node_id": evidence_root_id,
            "artifact": "governance_tree_json",
            "derived_from": [workspace_root_id, standards_root_id, projects_root_id],
        },
        {
            "id": "workspace:shelf:evidence:artifact:governance_tree_html",
            "label": "shelf_governance_tree.html",
            "level": 2,
            "description": (
                "kind=workspace_evidence_artifact | layer=Workspace Evidence"
                f" | file={governance_html_rel} | artifact=governance_tree_html"
            ),
            "source_file": governance_html_rel,
            "source_line": 1,
            "node_kind": "workspace_evidence_artifact",
            "layer": "Workspace Evidence",
            "parent_node_id": evidence_root_id,
            "artifact": "governance_tree_html",
            "derived_from": [workspace_root_id, standards_root_id, projects_root_id],
        },
        {
            "id": "workspace:shelf:evidence:artifact:project_discovery_audit_json",
            "label": "project_discovery_audit.json",
            "level": 2,
            "description": (
                "kind=workspace_evidence_artifact | layer=Workspace Evidence"
                f" | file={discovery_audit_json_rel} | artifact=project_discovery_audit_json"
            ),
            "source_file": discovery_audit_json_rel,
            "source_line": 1,
            "node_kind": "workspace_evidence_artifact",
            "layer": "Workspace Evidence",
            "parent_node_id": evidence_root_id,
            "artifact": "project_discovery_audit_json",
            "derived_from": [workspace_root_id, projects_root_id],
        },
        {
            "id": "workspace:shelf:evidence:artifact:project_discovery_audit_md",
            "label": "project_discovery_audit.md",
            "level": 2,
            "description": (
                "kind=workspace_evidence_artifact | layer=Workspace Evidence"
                f" | file={discovery_audit_md_rel} | artifact=project_discovery_audit_md"
            ),
            "source_file": discovery_audit_md_rel,
            "source_line": 1,
            "node_kind": "workspace_evidence_artifact",
            "layer": "Workspace Evidence",
            "parent_node_id": evidence_root_id,
            "artifact": "project_discovery_audit_md",
            "derived_from": [workspace_root_id, projects_root_id],
        },
    ]
    edges: list[dict[str, Any]] = [
        {"from": workspace_root_id, "to": projects_root_id, "relation": "tree_child"},
        {"from": workspace_root_id, "to": evidence_root_id, "relation": "tree_child"},
    ]

    standard_nodes, standard_edges, standards_root_id = _mapping_tree_to_hierarchy_nodes()
    for node in nodes:
        if node["id"] in {
            "workspace:shelf:evidence:artifact:governance_tree_json",
            "workspace:shelf:evidence:artifact:governance_tree_html",
            "workspace:shelf:evidence:artifact:project_discovery_audit_json",
            "workspace:shelf:evidence:artifact:project_discovery_audit_md",
        }:
            node["derived_from"] = [workspace_root_id, standards_root_id, projects_root_id]
    nodes.extend(standard_nodes)
    edges.append({"from": workspace_root_id, "to": standards_root_id, "relation": "tree_child"})
    edges.extend(standard_edges)

    requested_product_spec_files = (
        [path.resolve() for path in product_spec_files]
        if product_spec_files is not None
        else discover_workspace_product_spec_files()
    )
    project_trees: dict[str, dict[str, Any]] = {}
    project_roots: dict[str, str] = {}

    for product_spec_file in requested_product_spec_files:
        project = load_registered_project(product_spec_file)
        project_tree = build_governance_tree(project)
        project_id = str(project_tree.get("project_id") or project.metadata.project_id)
        rel_product_spec_file = _relative(product_spec_file)
        project_trees[project_id] = project_tree
        project_nodes, project_edges, project_root_id = _project_tree_to_hierarchy_nodes(
            project_tree,
            project_id=project_id,
            product_spec_file=rel_product_spec_file,
            parent_id=projects_root_id,
        )
        project_roots[project_id] = project_root_id
        nodes.extend(project_nodes)
        edges.extend(project_edges)

    audited_directories = {
        str(item.get("directory") or "").strip(): item
        for item in discovery_audit.get("entries", [])
        if isinstance(item, dict)
    }
    for directory, entry in sorted(audited_directories.items()):
        if not directory:
            continue
        project_id = str(entry.get("project_id") or Path(directory).name)
        if project_id in project_roots:
            continue
        node_id = f"workspace:shelf:projects:audit:{project_id}"
        nodes.append(
            {
                "id": node_id,
                "label": project_id,
                "level": 2,
                "description": _node_description(
                    {
                        "kind": "project_audit_entry",
                        "layer": "Projects",
                        "project_id": project_id,
                        "file": directory,
                        "artifact": entry.get("classification"),
                    }
                ),
                "source_file": directory,
                "source_line": 1,
                "node_kind": "project_audit_entry",
                "layer": "Projects",
                "project_id": project_id,
                "audit_classification": entry.get("classification"),
                "framework_driven": entry.get("framework_driven"),
                "parent_node_id": projects_root_id,
                "derived_from": [],
            }
        )
        edges.append({"from": projects_root_id, "to": node_id, "relation": "tree_child"})

    indexes = _build_governance_indexes(nodes, project_roots)
    level_labels = {
        "0": "Workspace",
        "1": "Top Level",
        "2": "Project / Standard Root",
        "3": "Layer Root",
        "4": "Module / File / Root",
        "5": "Rule / Section / Symbol / Artifact",
        "6": "Deep Node",
        "7": "Deep Node",
    }

    return {
        "root": {
            "title": "Shelf Governance Tree",
            "description": (
                "统一治理树，覆盖 Standards -> Projects -> Framework/Product/Implementation/Code/Evidence。"
            ),
            "storage_key_stem": "governanceTree",
            "level_labels": level_labels,
            "nodes": nodes,
            "edges": edges,
        },
        "governance": {
            "version": WORKSPACE_GOVERNANCE_VERSION,
            "workspace_root_id": workspace_root_id,
            "standards_root_id": standards_root_id,
            "projects_root_id": projects_root_id,
            "project_roots": project_roots,
            "project_trees": project_trees,
            "project_discovery_audit": discovery_audit,
            **indexes,
        },
    }


def parse_workspace_governance_payload(path: Path) -> dict[str, Any]:
    payload = _read_json(path)
    root = payload.get("root")
    governance = payload.get("governance")
    if not isinstance(root, dict):
        raise ValueError("workspace governance tree missing root object")
    if not isinstance(governance, dict):
        raise ValueError("workspace governance tree missing governance object")
    if governance.get("version") != WORKSPACE_GOVERNANCE_VERSION:
        raise ValueError(f"unsupported workspace governance version: {governance.get('version')}")
    nodes = root.get("nodes")
    edges = root.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise ValueError("workspace governance tree root must contain nodes and edges")
    return payload


def resolve_workspace_change_context(
    payload: dict[str, Any],
    changed_files: set[str],
) -> dict[str, Any]:
    governance = payload.get("governance")
    if not isinstance(governance, dict):
        raise ValueError("workspace governance payload missing governance object")
    raw_file_index = governance.get("file_index")
    raw_parent_index = governance.get("parent_index")
    raw_children_index = governance.get("children_index")
    raw_derived_index = governance.get("derived_index")
    raw_reverse_derived_index = governance.get("reverse_derived_index")
    raw_project_index = governance.get("project_index")
    if not all(
        isinstance(item, dict)
        for item in (
            raw_file_index,
            raw_parent_index,
            raw_children_index,
            raw_derived_index,
            raw_reverse_derived_index,
            raw_project_index,
        )
    ):
        raise ValueError("workspace governance payload indexes are incomplete")
    file_index = cast(dict[str, Any], raw_file_index)
    parent_index = cast(dict[str, Any], raw_parent_index)
    children_index = cast(dict[str, Any], raw_children_index)
    derived_index = cast(dict[str, Any], raw_derived_index)
    reverse_derived_index = cast(dict[str, Any], raw_reverse_derived_index)
    project_index = cast(dict[str, Any], raw_project_index)

    touched_nodes: set[str] = set()
    for rel_file in changed_files:
        touched_nodes.update(str(node_id) for node_id in list(file_index.get(rel_file, [])))

    affected_nodes: set[str] = set(touched_nodes)
    queue = list(touched_nodes)
    while queue:
        node_id = queue.pop()
        parent = parent_index.get(node_id)
        if isinstance(parent, str) and parent and parent not in affected_nodes:
            affected_nodes.add(parent)
            queue.append(parent)
        for child_id in list(children_index.get(node_id, [])):
            child = str(child_id)
            if child not in affected_nodes:
                affected_nodes.add(child)
                queue.append(child)
        for upstream in list(derived_index.get(node_id, [])):
            upstream_id = str(upstream)
            if upstream_id not in affected_nodes:
                affected_nodes.add(upstream_id)
                queue.append(upstream_id)
        for dependent in list(reverse_derived_index.get(node_id, [])):
            dependent_id = str(dependent)
            if dependent_id not in affected_nodes:
                affected_nodes.add(dependent_id)
                queue.append(dependent_id)

    affected_projects: dict[str, str] = {}
    materialize_projects: dict[str, str] = {}
    run_standard_checks = False
    run_project_checks = False

    root = payload.get("root")
    if not isinstance(root, dict):
        raise ValueError("workspace governance payload missing root object")
    root_nodes = root.get("nodes")
    if not isinstance(root_nodes, list):
        raise ValueError("workspace governance payload root.nodes must be a list")
    node_lookup = {
        str(item.get("id") or ""): item
        for item in root_nodes
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }

    for node_id in affected_nodes:
        node = node_lookup.get(node_id)
        if node is None:
            continue
        project_id = str(node.get("project_id") or "").strip()
        if project_id:
            project_entry = project_index.get(project_id)
            if not isinstance(project_entry, dict):
                project_entry = {}
            product_spec_file = str(project_entry.get("product_spec_file") or "")
            if product_spec_file:
                affected_projects[project_id] = product_spec_file
                run_project_checks = True
        if str(node.get("layer") or "") == "Standards":
            run_standard_checks = True

    for node_id in touched_nodes:
        node = node_lookup.get(node_id)
        if node is None:
            continue
        layer = str(node.get("layer") or "").strip()
        project_id = str(node.get("project_id") or "").strip()
        if not project_id:
            continue
        if layer in {"Framework", "Product Spec", "Implementation Config"}:
            project_entry = project_index.get(project_id)
            if not isinstance(project_entry, dict):
                project_entry = {}
            product_spec_file = str(project_entry.get("product_spec_file") or "")
            if product_spec_file:
                materialize_projects[project_id] = product_spec_file

    for rel_file in changed_files:
        if rel_file.startswith(("framework/", "specs/", "mapping/")):
            run_standard_checks = True

    return {
        "touched_nodes": sorted(touched_nodes),
        "affected_nodes": sorted(affected_nodes),
        "affected_project_spec_files": sorted(affected_projects.values()),
        "materialize_project_spec_files": sorted(materialize_projects.values()),
        "run_standard_checks": run_standard_checks,
        "run_project_checks": run_project_checks,
    }
