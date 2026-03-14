from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]


def _module_nodes(canonical_graph: dict[str, Any]) -> list[dict[str, Any]]:
    framework = canonical_graph.get("layers", {}).get("framework", {})
    modules = framework.get("module_tree", {}).get("modules", [])
    if not isinstance(modules, list):
        return []
    return [item for item in modules if isinstance(item, dict)]


def _package_results(canonical_graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    code = canonical_graph.get("layers", {}).get("code", {})
    raw = code.get("package_results", {})
    if not isinstance(raw, dict):
        return {}
    return {
        key: value
        for key, value in raw.items()
        if isinstance(key, str) and isinstance(value, dict)
    }


def _derived_path_map(generated_artifacts: dict[str, str]) -> dict[str, dict[str, str]]:
    canonical_path = generated_artifacts.get("canonical_graph_json", "")
    return {
        key: {
            "path": value,
            "derived_from": canonical_path,
        }
        for key, value in generated_artifacts.items()
        if key != "canonical_graph_json"
    }


def build_governance_manifest(canonical_graph: dict[str, Any]) -> dict[str, Any]:
    framework = canonical_graph.get("layers", {}).get("framework", {})
    code = canonical_graph.get("layers", {}).get("code", {})
    evidence = canonical_graph.get("layers", {}).get("evidence", {})
    generated_artifacts = evidence.get("generated_artifacts", {})
    bindings = framework.get("registry_binding", [])
    return {
        "schema_version": "derived-governance-manifest/v2",
        "project_id": canonical_graph.get("project", {}).get("project_id"),
        "derived_from": generated_artifacts.get("canonical_graph_json"),
        "binding_count": len(bindings) if isinstance(bindings, list) else 0,
        "package_count": len(_package_results(canonical_graph)),
        "registry_binding": bindings,
        "root_modules": framework.get("selection", {}).get("root_modules", {}),
        "package_compile_order": code.get("package_compile_order", []),
    }


def build_governance_tree(canonical_graph: dict[str, Any]) -> dict[str, Any]:
    evidence = canonical_graph.get("layers", {}).get("evidence", {})
    generated_artifacts = evidence.get("generated_artifacts", {})
    project_id = canonical_graph.get("project", {}).get("project_id", "unknown")
    nodes: list[dict[str, Any]] = [
        {
            "id": f"project:{project_id}",
            "label": str(project_id),
            "kind": "project",
            "layer": "project",
        }
    ]
    edges: list[dict[str, str]] = []

    framework_root = f"project:{project_id}:framework"
    config_root = f"project:{project_id}:config"
    code_root = f"project:{project_id}:code"
    evidence_root = f"project:{project_id}:evidence"
    for node_id, label, layer in (
        (framework_root, "Framework", "framework"),
        (config_root, "Config", "config"),
        (code_root, "Code", "code"),
        (evidence_root, "Evidence", "evidence"),
    ):
        nodes.append({"id": node_id, "label": label, "kind": "layer", "layer": layer})
        edges.append({"from": f"project:{project_id}", "to": node_id, "relation": "layer"})

    for module in _module_nodes(canonical_graph):
        module_id = str(module.get("module_id", ""))
        node_id = f"{framework_root}:{module_id}"
        nodes.append(
            {
                "id": node_id,
                "label": module_id,
                "kind": "framework_module",
                "layer": "framework",
                "framework_file": module.get("framework_file"),
            }
        )
        edges.append({"from": framework_root, "to": node_id, "relation": "selected_or_closure"})

    for module_id, result in _package_results(canonical_graph).items():
        package_node_id = f"{code_root}:{module_id}"
        nodes.append(
            {
                "id": package_node_id,
                "label": module_id,
                "kind": "package",
                "layer": "code",
                "entry_class": result.get("entry_class"),
            }
        )
        edges.append({"from": code_root, "to": package_node_id, "relation": "package_compile"})
        for child_slot in result.get("child_slots", []):
            if not isinstance(child_slot, dict):
                continue
            child_module_id = str(child_slot.get("child_module_id", ""))
            if child_module_id:
                edges.append(
                    {
                        "from": package_node_id,
                        "to": f"{code_root}:{child_module_id}",
                        "relation": "depends_on",
                    }
                )

    derived_views = evidence.get("derived_views", {})
    if isinstance(derived_views, dict):
        for view_name, view_data in derived_views.items():
            if not isinstance(view_name, str) or not isinstance(view_data, dict):
                continue
            nodes.append(
                {
                    "id": f"{evidence_root}:{view_name}",
                    "label": view_name,
                    "kind": "derived_view",
                    "layer": "evidence",
                    "path": view_data.get("path"),
                }
            )
            edges.append({"from": evidence_root, "to": f"{evidence_root}:{view_name}", "relation": "derived_view"})

    return {
        "schema_version": "derived-governance-tree/v2",
        "derived_from": generated_artifacts.get("canonical_graph_json"),
        "nodes": nodes,
        "edges": edges,
    }


def build_strict_zone_report(canonical_graph: dict[str, Any]) -> dict[str, Any]:
    framework_files = sorted(
        {
            str(item.get("framework_file", ""))
            for item in _module_nodes(canonical_graph)
            if isinstance(item.get("framework_file"), str)
        }
    )
    config_layer = canonical_graph.get("layers", {}).get("config", {})
    project_file = config_layer.get("project_file")
    package_results = _package_results(canonical_graph)
    code_files = sorted(
        {
            str(result.get("package_module", "")).replace(".", "/") + ".py"
            for result in package_results.values()
            if isinstance(result.get("package_module"), str)
        }
    )
    files: list[dict[str, Any]] = []
    for file_path in framework_files:
        files.append({"file": file_path, "layer": "framework", "reason": "selected framework or dependency"})
    if isinstance(project_file, str):
        files.append({"file": project_file, "layer": "config", "reason": "unified project config"})
    for file_path in code_files:
        files.append({"file": file_path, "layer": "code", "reason": "registered framework package"})
    return {
        "schema_version": "derived-strict-zone-report/v2",
        "project_id": canonical_graph.get("project", {}).get("project_id"),
        "file_count": len(files),
        "files": files,
    }


def build_object_coverage_report(canonical_graph: dict[str, Any]) -> dict[str, Any]:
    framework_modules = _module_nodes(canonical_graph)
    package_results = _package_results(canonical_graph)
    registry_binding = canonical_graph.get("layers", {}).get("framework", {}).get("registry_binding", [])
    return {
        "schema_version": "derived-object-coverage-report/v2",
        "project_id": canonical_graph.get("project", {}).get("project_id"),
        "framework_module_count": len(framework_modules),
        "compiled_package_count": len(package_results),
        "registry_binding_count": len(registry_binding) if isinstance(registry_binding, list) else 0,
        "compiled_module_ids": sorted(package_results),
    }


@dataclass(frozen=True)
class DerivedViewPayloads:
    generation_manifest: dict[str, Any]
    governance_manifest: dict[str, Any]
    governance_tree: dict[str, Any]
    strict_zone_report: dict[str, Any]
    object_coverage_report: dict[str, Any]


def build_derived_view_payloads(
    canonical_graph: dict[str, Any],
    *,
    generated_artifacts: dict[str, str],
) -> DerivedViewPayloads:
    canonical_path = generated_artifacts.get("canonical_graph_json", "")
    generation_manifest = {
        "schema_version": "derived-generation-manifest/v2",
        "project_id": canonical_graph.get("project", {}).get("project_id"),
        "derived_from": canonical_path,
        "generated_files": dict(generated_artifacts),
        "derived_views": _derived_path_map(generated_artifacts),
    }
    return DerivedViewPayloads(
        generation_manifest=generation_manifest,
        governance_manifest=build_governance_manifest(canonical_graph),
        governance_tree=build_governance_tree(canonical_graph),
        strict_zone_report=build_strict_zone_report(canonical_graph),
        object_coverage_report=build_object_coverage_report(canonical_graph),
    )

