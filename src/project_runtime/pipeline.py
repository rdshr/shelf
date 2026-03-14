from __future__ import annotations

from dataclasses import replace
from importlib import import_module
import json
from pathlib import Path
from typing import Any, Callable

from framework_ir import FrameworkModule, load_framework_registry
from framework_packages.builtin_registry import load_builtin_package_registry
from framework_packages.contract import PackageCompileInput, PackageCompileResult, PackageSelectedRoot
from framework_packages.registry import FrameworkPackageRegistry
from project_runtime.config_loader import load_project_config
from project_runtime.models import (
    GeneratedArtifactOutputPaths,
    GeneratedArtifactPaths,
    ProjectCompilationState,
    ProjectRuntimeAssembly,
    RuntimeProjection,
    UnifiedProjectConfig,
)
from project_runtime.module_tree import resolve_module_tree
from project_runtime.package_config import (
    flatten_project_payload,
    merge_config_contracts,
    project_owned_config_payload,
    resolve_config_slice,
)
from project_runtime.utils import cleanup_generated_output_dir, normalize_project_path, relative_path, sha256_text
from rule_validation_models import RuleValidationSummary, ValidationReports


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROJECT_FILE = REPO_ROOT / "projects/knowledge_base_basic/project.toml"


def compile_project(project_file: str | Path) -> tuple[ProjectCompilationState, ProjectRuntimeAssembly]:
    project_path = normalize_project_path(project_file)
    config = load_project_config(project_path)
    framework_registry = load_framework_registry()
    package_registry = load_builtin_package_registry()
    package_registry.validate_against_framework(framework_registry)
    module_tree = resolve_module_tree(framework_registry, config.selection)
    _validate_module_tree(module_tree.modules)
    package_results = compile_package_results(
        config=config,
        package_registry=package_registry,
        module_tree=module_tree,
    )
    state = ProjectCompilationState(
        project_file=config.project_file,
        config=config,
        package_registry=package_registry,
        module_tree=module_tree,
        package_results=package_results,
    )
    runtime_projection = assemble_runtime_projection(package_results)
    assembly = ProjectRuntimeAssembly(
        project_file=config.project_file,
        metadata=config.metadata,
        selection=config.selection,
        project_config_view=config.project_config_view(),
        package_compile_order=tuple(package_results),
        root_module_ids=module_tree.root_module_ids(),
        runtime_projection=runtime_projection,
        validation_reports=ValidationReports.empty(),
    )
    validation_reports = collect_validation_reports(assembly)
    raise_on_validation_failures(validation_reports)
    assembly = replace(assembly, validation_reports=validation_reports)
    assembly = replace(assembly, canonical_graph=build_canonical_graph(state, assembly))
    return state, assembly


def compile_project_runtime(
    project_file: str | Path = DEFAULT_PROJECT_FILE,
) -> tuple[ProjectCompilationState, ProjectRuntimeAssembly]:
    return compile_project(project_file)


def load_project_runtime(
    project_file: str | Path = DEFAULT_PROJECT_FILE,
) -> ProjectRuntimeAssembly:
    _, assembly = compile_project(project_file)
    return assembly


def materialize_project_runtime(
    project_file: str | Path = DEFAULT_PROJECT_FILE,
    output_dir: str | Path | None = None,
) -> ProjectRuntimeAssembly:
    from project_runtime.governance import build_derived_view_payloads

    state, assembly = compile_project(project_file)
    project_path = normalize_project_path(project_file)
    generated_dir = project_path.parent / "generated"
    output_path = normalize_project_path(output_dir) if output_dir is not None else generated_dir
    output_path.mkdir(parents=True, exist_ok=True)

    artifact_names = state.config.artifact_config
    expected_file_names = set(artifact_names.file_names())
    cleanup_generated_output_dir(output_path, expected_file_names)
    output_paths = GeneratedArtifactOutputPaths.from_artifact_config(artifact_names, output_dir=output_path)
    generated_artifacts = GeneratedArtifactPaths.from_artifact_config(
        artifact_names,
        directory=generated_dir,
        path_renderer=relative_path,
    )
    assembly = replace(assembly, generated_artifacts=generated_artifacts)
    assembly = replace(assembly, canonical_graph=build_canonical_graph(state, assembly))
    derived_view_payloads = build_derived_view_payloads(
        assembly.canonical_graph,
        generated_artifacts=generated_artifacts.to_dict(),
    )
    assembly = replace(assembly, derived_views=derived_view_payloads.generation_manifest["derived_views"])
    assembly = replace(assembly, canonical_graph=build_canonical_graph(state, assembly))
    runtime_snapshot_text = build_runtime_snapshot_text(assembly, assembly.canonical_graph)

    output_paths.canonical_graph_json.write_text(json.dumps(assembly.canonical_graph, ensure_ascii=False, indent=2), encoding="utf-8")
    output_paths.runtime_snapshot_py.write_text(runtime_snapshot_text, encoding="utf-8")
    output_paths.generation_manifest_json.write_text(
        json.dumps(derived_view_payloads.generation_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    output_paths.derived_governance_manifest_json.write_text(
        json.dumps(derived_view_payloads.governance_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    output_paths.derived_governance_tree_json.write_text(
        json.dumps(derived_view_payloads.governance_tree, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    output_paths.strict_zone_report_json.write_text(
        json.dumps(derived_view_payloads.strict_zone_report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    output_paths.object_coverage_report_json.write_text(
        json.dumps(derived_view_payloads.object_coverage_report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return assembly


def build_project_app_from_project_file(
    project_file: str | Path = DEFAULT_PROJECT_FILE,
) -> Any:
    assembly = load_project_runtime(project_file)
    entrypoints = assembly.runtime_projection.app_entrypoints
    if len(entrypoints) != 1:
        raise ValueError(f"runtime projection must expose exactly one app entrypoint, found {len(entrypoints)}")
    factory = _load_callable(entrypoints[0].factory_path)
    return factory(assembly)


def compile_package_results(
    *,
    config: UnifiedProjectConfig,
    package_registry: FrameworkPackageRegistry,
    module_tree: Any,
) -> dict[str, PackageCompileResult]:
    root_payload = flatten_project_payload(config.root_payload())
    selected_roots = tuple(
        PackageSelectedRoot(
            slot_id=item.slot_id,
            role=item.role,
            module_id=item.module.module_id,
            framework_file=item.framework_file,
            entry_class_name=package_registry.get_by_module_id(item.module.module_id).entry_class_name,
        )
        for item in module_tree.roots
    )
    modules_by_id = {item.module_id: item for item in module_tree.modules}
    entries = {
        module_id: package_registry.get_by_module_id(module_id).entry_class()
        for module_id in modules_by_id
    }
    child_slots = {
        module_id: entries[module_id].child_slots(module)
        for module_id, module in modules_by_id.items()
    }
    subtree_contracts: dict[str, Any] = {}
    compiled: dict[str, PackageCompileResult] = {}
    owned_payloads: dict[str, dict[str, Any]] = {}
    compile_order: list[str] = []

    def subtree_contract(module_id: str) -> Any:
        cached = subtree_contracts.get(module_id)
        if cached is not None:
            return cached
        merged = merge_config_contracts(
            entries[module_id].config_contract(),
            *(subtree_contract(slot.child_module_id) for slot in child_slots[module_id]),
        )
        subtree_contracts[module_id] = merged
        return merged

    def compile_module(module_id: str, available_payload: dict[str, Any]) -> PackageCompileResult:
        existing_payload = owned_payloads.get(module_id)
        if existing_payload is not None:
            if existing_payload != available_payload:
                raise ValueError(f"conflicting parent-owned config payload for module: {module_id}")
            return compiled[module_id]

        owned_payloads[module_id] = dict(available_payload)
        entry = entries[module_id]
        module = modules_by_id[module_id]
        own_config_slice = resolve_config_slice(
            available_payload,
            contract=entry.config_contract(),
            package_id=entry.module_id(),
        )
        child_exports: dict[str, dict[str, Any]] = {}
        child_runtime_exports: dict[str, dict[str, Any]] = {}
        for slot in child_slots[module_id]:
            child_payload = project_owned_config_payload(
                available_payload,
                contract=subtree_contract(slot.child_module_id),
            )
            child_result = compile_module(slot.child_module_id, child_payload)
            child_exports[slot.child_module_id] = child_result.export
            child_runtime_exports[slot.child_module_id] = dict(child_result.runtime_exports)
        result = entry.compile(
            PackageCompileInput(
                framework_module=module,
                config_slice=own_config_slice,
                child_exports=child_exports,
                child_runtime_exports=child_runtime_exports,
                selected_roots=selected_roots,
            )
        )
        compiled[module_id] = result
        compile_order.append(module_id)
        return result

    for root in module_tree.roots:
        root_payload_for_subtree = project_owned_config_payload(
            root_payload,
            contract=subtree_contract(root.module_id),
        )
        compile_module(root.module_id, root_payload_for_subtree)

    return {module_id: compiled[module_id] for module_id in compile_order}


def assemble_runtime_projection(package_results: dict[str, PackageCompileResult]) -> RuntimeProjection:
    package_exports: dict[str, dict[str, Any]] = {}
    export_index: dict[str, dict[str, Any]] = {}
    app_entrypoints = []
    validation_hooks = []
    entrypoint_ids: set[str] = set()
    validation_scopes: set[str] = set()
    for module_id, result in package_results.items():
        package_exports[module_id] = dict(result.runtime_exports)
        for export_key, export_value in sorted(result.runtime_exports.items()):
            if export_key in export_index:
                provider = export_index[export_key]["provider_module_id"]
                raise ValueError(f"runtime export {export_key} declared by both {provider} and {module_id}")
            export_index[export_key] = {
                "provider_module_id": module_id,
                "value": export_value,
            }
        for entrypoint in result.runtime_entrypoints:
            if entrypoint.entrypoint_id in entrypoint_ids:
                raise ValueError(f"runtime app entrypoint declared more than once: {entrypoint.entrypoint_id}")
            entrypoint_ids.add(entrypoint.entrypoint_id)
            app_entrypoints.append(entrypoint)
        for hook in result.runtime_validation_hooks:
            if hook.scope in validation_scopes:
                raise ValueError(f"runtime validation scope declared more than once: {hook.scope}")
            validation_scopes.add(hook.scope)
            validation_hooks.append(hook)
    runtime_blueprint = _assemble_runtime_blueprint(export_index)
    if runtime_blueprint is not None:
        export_index["runtime_blueprint"] = {
            "provider_module_id": "runtime_projection",
            "value": runtime_blueprint,
        }
    return RuntimeProjection(
        package_exports=package_exports,
        export_index=export_index,
        app_entrypoints=tuple(app_entrypoints),
        validation_hooks=tuple(validation_hooks),
    )


def collect_validation_reports(project: ProjectRuntimeAssembly) -> ValidationReports:
    scopes: dict[str, RuleValidationSummary] = {}
    for hook in project.runtime_projection.validation_hooks:
        validator = _load_callable(hook.validator_path)
        summarizer = _load_callable(hook.summarizer_path)
        summary = summarizer(validator(project))
        if not isinstance(summary, RuleValidationSummary):
            raise TypeError(f"runtime validator summarizer must return RuleValidationSummary: {hook.summarizer_path}")
        scopes[hook.scope] = summary
    return ValidationReports(scopes=scopes)


def raise_on_validation_failures(reports: ValidationReports) -> None:
    errors: list[str] = []
    for scope, report in sorted(reports.scopes.items()):
        for item in report.rules:
            if item.passed:
                continue
            reasons = ", ".join(item.reasons) or "unknown rule failure"
            errors.append(f"{scope}.{item.rule_id}: {reasons}")
    if errors:
        raise ValueError("framework rule validation failed: " + " | ".join(errors))


def build_runtime_snapshot_text(project: ProjectRuntimeAssembly, canonical_graph: dict[str, Any]) -> str:
    runtime_snapshot = project.to_runtime_snapshot_dict()
    return "\n".join(
        [
            "from __future__ import annotations",
            "",
            "# GENERATED FILE. DO NOT EDIT.",
            "# Change framework markdown or projects/*/project.toml, then re-materialize.",
            "",
            "import json",
            "",
            f"CANONICAL_GRAPH = json.loads(r'''{json.dumps(canonical_graph, ensure_ascii=False)}''')",
            f"RUNTIME_SNAPSHOT = json.loads(r'''{json.dumps(runtime_snapshot, ensure_ascii=False)}''')",
            "PROJECT_CONFIG = RUNTIME_SNAPSHOT['project_config']",
            "",
        ]
    )

def build_canonical_graph(
    state: ProjectCompilationState,
    project: ProjectRuntimeAssembly,
) -> dict[str, Any]:
    generated_artifacts = project.generated_artifacts.to_dict() if project.generated_artifacts else None
    document_digests = _document_digests(project)
    return {
        "schema_version": "framework-package-canonical/v2",
        "project": project.metadata.to_dict(),
        "layers": {
            "framework": {
                "author_source": "framework/*.md",
                "selection": project.selection.to_dict(),
                "module_tree": {
                    "roots": [item.to_dict() for item in state.module_tree.roots],
                    "modules": [
                        {
                            "module_id": item.module_id,
                            "framework_file": item.path,
                            "title_cn": item.title_cn,
                            "title_en": item.title_en,
                            "intro": item.intro,
                            "upstream_module_ids": list(item.export_surface().upstream_module_ids),
                        }
                        for item in state.module_tree.modules
                    ],
                },
                "registry_binding": [item.to_dict() for item in state.package_registry.iter_registrations()],
            },
            "config": {
                "project_file": project.project_file,
                "section_sources": dict(state.config.section_sources),
                "selection": project.selection.to_dict(),
                "truth": state.config.truth_payload(),
                "refinement": state.config.refinement_payload(),
                "narrative": state.config.narrative,
                "projection": {
                    module_id: {
                        "config_contract": result.config_contract.to_dict(),
                        "config_slice": result.config_slice,
                    }
                    for module_id, result in sorted(state.package_results.items())
                },
            },
            "code": {
                "package_compile_order": list(project.package_compile_order),
                "root_packages": dict(project.root_module_ids),
                "package_results": {
                    module_id: result.to_dict()
                    for module_id, result in sorted(state.package_results.items())
                },
                "runtime_projection": project.runtime_projection.to_dict(),
            },
            "evidence": {
                "validation_reports": project.validation_reports.to_dict(),
                "document_digests": document_digests,
                "generated_artifacts": generated_artifacts,
                "derived_views": dict(project.derived_views),
            },
        },
    }


def _validate_module_tree(modules: tuple[FrameworkModule, ...]) -> None:
    if not all(module.bases for module in modules):
        raise ValueError("selected framework modules must define bases")


def _document_digests(project: ProjectRuntimeAssembly) -> dict[str, str]:
    runtime_documents = project.runtime_projection.export_values.get("runtime_documents")
    if not isinstance(runtime_documents, list):
        return {}
    digests: dict[str, str] = {}
    for item in runtime_documents:
        if not isinstance(item, dict):
            continue
        document_id = item.get("document_id")
        body_markdown = item.get("body_markdown")
        if isinstance(document_id, str) and isinstance(body_markdown, str):
            digests[document_id] = sha256_text(body_markdown)
    return digests


def _assemble_runtime_blueprint(export_index: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    page_blueprint = _dict_export_value(export_index, "runtime_page_blueprint")
    api_blueprint = _dict_export_value(export_index, "runtime_api_blueprint")
    if page_blueprint is None and api_blueprint is None:
        return None
    if page_blueprint is None or api_blueprint is None:
        raise ValueError("runtime_blueprint requires both runtime_page_blueprint and runtime_api_blueprint exports")
    if "runtime_blueprint" in export_index:
        raise ValueError("runtime_blueprint must not be declared directly; derive it from page/api blueprint exports")
    return {**api_blueprint, **page_blueprint}


def _dict_export_value(export_index: dict[str, dict[str, Any]], export_key: str) -> dict[str, Any] | None:
    binding = export_index.get(export_key)
    if binding is None:
        return None
    value = binding.get("value")
    if not isinstance(value, dict):
        raise ValueError(f"runtime export must be a dict: {export_key}")
    return dict(value)


def _load_callable(path: str) -> Callable[..., Any]:
    module_name, _, attr_name = path.partition(":")
    if not module_name or not attr_name:
        raise ValueError(f"invalid callable path: {path}")
    module = import_module(module_name)
    value = getattr(module, attr_name)
    if not callable(value):
        raise TypeError(f"resolved object is not callable: {path}")
    return value
