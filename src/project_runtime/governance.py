from __future__ import annotations

from dataclasses import dataclass
import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import tomllib
from typing import TYPE_CHECKING, Any, Callable, get_args, get_origin, get_type_hints

from fastapi.routing import APIRoute
from framework_ir import FrameworkModuleIR, parse_framework_module
from project_runtime.project_governance import (
    ProjectGovernanceClosure,
    RequiredRole,
    SourceRef,
    StructuralObject,
    StructuralCandidate,
    annotate_strict_zone_minimality,
    build_object_coverage_report,
    build_project_discovery_audit,
    build_strict_zone_report,
    classify_candidates,
    discover_framework_driven_projects,
    fingerprint,
    infer_strict_zone,
    relative_path,
    resolve_role_bindings,
    scan_python_structural_candidates,
)

if TYPE_CHECKING:
    from project_runtime.knowledge_base import KnowledgeBaseProject


REPO_ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE_MANIFEST_VERSION = "governance-manifest/v1"
GOVERNANCE_TREE_VERSION = "governance-tree/v1"
GOVERNANCE_GENERATOR_VERSION = "project_runtime.governance/v1"

ANNOTATION_LINE_PATTERN = re.compile(r"^\s*#\s*@governed_symbol\s+(.*)$")
ANNOTATION_PAIR_PATTERN = re.compile(r"([a-z_]+)=([^\s]+)")
DEFINITION_LINE_PATTERN = re.compile(r"^\s*(?:async\s+def|def|class)\s+([A-Za-z_][A-Za-z0-9_]*)")


@dataclass(frozen=True)
class GovernedBinding:
    symbol_id: str
    owner: str
    kind: str
    risk: str
    file: str
    locator: str
    line: int

    def to_manifest_dict(self) -> dict[str, Any]:
        return {
            "file": self.file,
            "locator": self.locator,
            "annotation": "governed_symbol",
            "line": self.line,
        }


@dataclass(frozen=True)
class UpstreamRef:
    layer: str
    file: str
    ref_kind: str
    ref_id: str

    def key(self) -> tuple[str, str, str, str]:
        return (self.layer, self.file, self.ref_kind, self.ref_id)

    def to_manifest_dict(self, digest: str | None = None) -> dict[str, Any]:
        payload = {
            "layer": self.layer,
            "file": self.file,
            "ref_kind": self.ref_kind,
            "ref_id": self.ref_id,
        }
        if digest is not None:
            payload["digest"] = digest
        return payload


@dataclass(frozen=True)
class SymbolDefinition:
    symbol_id: str
    owner: str
    kind: str
    risk: str
    expected_builder: Callable[[KnowledgeBaseProject], dict[str, Any]]
    actual_extractor: Callable[[KnowledgeBaseProject], dict[str, Any]]
    extractor: str
    comparator: str
    upstream_ref_builder: Callable[[KnowledgeBaseProject], tuple[UpstreamRef, ...]]
    required_bindings: tuple[tuple[str, str], ...]
    high_risk_file_checks: tuple[tuple[str, str], ...] = ()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _fingerprint(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _relative(path: Path | str) -> str:
    candidate = Path(path)
    if candidate.is_absolute():
        try:
            return candidate.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            return str(candidate)
    return candidate.as_posix()


def _expected_generated_artifact_paths(project: KnowledgeBaseProject) -> dict[str, str]:
    if project.generated_artifacts is not None:
        return {
            "framework_ir_json": project.generated_artifacts.framework_ir_json,
            "product_spec_json": project.generated_artifacts.product_spec_json,
            "implementation_bundle_py": project.generated_artifacts.implementation_bundle_py,
            "generation_manifest_json": project.generated_artifacts.generation_manifest_json,
            "governance_manifest_json": project.generated_artifacts.governance_manifest_json,
            "governance_tree_json": project.generated_artifacts.governance_tree_json,
            "strict_zone_report_json": project.generated_artifacts.strict_zone_report_json,
            "object_coverage_report_json": project.generated_artifacts.object_coverage_report_json,
        }

    generated_dir = Path(project.product_spec_file).parent / "generated"
    artifact_names = project.implementation.artifacts
    return {
        "framework_ir_json": _relative(generated_dir / artifact_names.framework_ir_json),
        "product_spec_json": _relative(generated_dir / artifact_names.product_spec_json),
        "implementation_bundle_py": _relative(generated_dir / artifact_names.implementation_bundle_py),
        "generation_manifest_json": _relative(generated_dir / artifact_names.generation_manifest_json),
        "governance_manifest_json": _relative(generated_dir / artifact_names.governance_manifest_json),
        "governance_tree_json": _relative(generated_dir / artifact_names.governance_tree_json),
        "strict_zone_report_json": _relative(generated_dir / artifact_names.strict_zone_report_json),
        "object_coverage_report_json": _relative(generated_dir / artifact_names.object_coverage_report_json),
    }


def _metadata_pairs(fragment: str) -> dict[str, str]:
    return {match.group(1): match.group(2) for match in ANNOTATION_PAIR_PATTERN.finditer(fragment)}


def scan_governed_python_bindings(file_path: Path) -> list[GovernedBinding]:
    rel_file = _relative(file_path)
    bindings: list[GovernedBinding] = []
    pending: tuple[dict[str, str], int] | None = None
    for line_number, raw_line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), start=1):
        annotation_match = ANNOTATION_LINE_PATTERN.match(raw_line)
        if annotation_match:
            pending = (_metadata_pairs(annotation_match.group(1)), line_number)
            continue
        if pending is None:
            continue
        stripped = raw_line.strip()
        definition_match = DEFINITION_LINE_PATTERN.match(raw_line)
        if definition_match is not None:
            metadata, annotation_line = pending
            symbol_id = metadata.get("id")
            owner = metadata.get("owner")
            kind = metadata.get("kind")
            risk = metadata.get("risk")
            if symbol_id and owner and kind and risk:
                name = definition_match.group(1)
                locator = ("class:" if stripped.startswith("class ") else "function:") + name
                bindings.append(
                    GovernedBinding(
                        symbol_id=symbol_id,
                        owner=owner,
                        kind=kind,
                        risk=risk,
                        file=rel_file,
                        locator=locator,
                        line=annotation_line,
                    )
                )
            pending = None
            continue
        if (
            not stripped
            or stripped.startswith("#")
            or stripped.startswith("@")
            or stripped.endswith("(")
            or stripped.endswith(",")
            or stripped in {")", "]", "}"}
        ):
            continue
        if definition_match is None:
            pending = None
            continue
        pending = None
    return bindings


def collect_governed_bindings(files: list[str]) -> dict[str, list[GovernedBinding]]:
    index: dict[str, list[GovernedBinding]] = {}
    for rel_file in files:
        file_path = REPO_ROOT / rel_file
        if not file_path.exists():
            continue
        for binding in scan_governed_python_bindings(file_path):
            index.setdefault(binding.symbol_id, []).append(binding)
    return index


def _annotation_present_before_line(file_path: Path, line_number: int) -> bool:
    lines = file_path.read_text(encoding="utf-8").splitlines()
    for index in range(line_number - 2, -1, -1):
        if index < 0 or index >= len(lines):
            continue
        candidate = lines[index].strip()
        if not candidate:
            continue
        if ANNOTATION_LINE_PATTERN.match(lines[index]):
            return True
        if (
            not candidate.startswith("#")
            and not candidate.startswith("@")
            and not candidate.endswith("(")
            and not candidate.endswith(",")
            and candidate not in {")", "]", "}"}
        ):
            break
    return False


def _route_decorated_function_names(
    file_path: Path,
    builder_name: str,
    receiver_name: str,
) -> list[tuple[str, int]]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=file_path.as_posix())
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == builder_name:
            results: list[tuple[str, int]] = []
            for child in node.body:
                if not isinstance(child, ast.FunctionDef):
                    continue
                if not any(_is_receiver_route_decorator(item, receiver_name) for item in child.decorator_list):
                    continue
                results.append((child.name, child.lineno))
            return results
    return []


def _is_receiver_route_decorator(node: ast.expr, receiver_name: str) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if not isinstance(func, ast.Attribute):
        return False
    if func.attr not in {"get", "post", "delete"}:
        return False
    if not isinstance(func.value, ast.Name):
        return False
    return func.value.id == receiver_name


def find_unbound_high_risk_structures() -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for rel_file, builder_name in (
        ("src/knowledge_base_runtime/app.py", "build_knowledge_base_runtime_app"),
        ("src/knowledge_base_runtime/backend.py", "build_knowledge_base_router"),
    ):
        file_path = REPO_ROOT / rel_file
        receiver_name = "app" if file_path.name == "app.py" else "router"
        for func_name, line_number in _route_decorated_function_names(file_path, builder_name, receiver_name):
            if _annotation_present_before_line(file_path, line_number):
                continue
            issues.append(
                {
                    "file": rel_file,
                    "line": line_number,
                    "locator": f"function:{func_name}",
                    "message": (
                        "New high-risk governed behavior detected but no governed_symbol binding found."
                    ),
                }
            )
    return issues


def _binding_validation_issues(
    binding_index: dict[str, list[GovernedBinding]],
    definitions: tuple[SymbolDefinition, ...],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    definitions_by_symbol = {item.symbol_id: item for item in definitions}
    allowed_bindings = {
        item.symbol_id: {(rel_file, locator) for rel_file, locator in item.required_bindings}
        for item in definitions
    }
    for symbol_id, bindings in binding_index.items():
        definition = definitions_by_symbol.get(symbol_id)
        if definition is None:
            for binding in bindings:
                issues.append(
                    {
                        "code": "UNKNOWN_BINDING",
                        "message": f"unknown governed symbol binding: {symbol_id}",
                        "file": binding.file,
                        "line": binding.line,
                        "symbol_id": symbol_id,
                        "locator": binding.locator,
                    }
                )
            continue
        allowed = allowed_bindings[symbol_id]
        for binding in bindings:
            if (binding.file, binding.locator) not in allowed:
                issues.append(
                    {
                        "code": "UNEXPECTED_BINDING",
                        "message": (
                            f"unexpected governed binding for {symbol_id}: "
                            f"{binding.file} -> {binding.locator}"
                        ),
                        "file": binding.file,
                        "line": binding.line,
                        "symbol_id": symbol_id,
                        "locator": binding.locator,
                    }
                )
            if (
                binding.owner != definition.owner
                or binding.kind != definition.kind
                or binding.risk != definition.risk
            ):
                issues.append(
                    {
                        "code": "INVALID_BINDING_METADATA",
                        "message": (
                            f"governed binding metadata mismatch for {symbol_id}: "
                            f"expected owner={definition.owner} kind={definition.kind} risk={definition.risk}"
                        ),
                        "file": binding.file,
                        "line": binding.line,
                        "symbol_id": symbol_id,
                        "locator": binding.locator,
                    }
                )
    return issues


def _framework_rule_refs(module: FrameworkModuleIR, rule_ids: tuple[str, ...] | None = None) -> tuple[UpstreamRef, ...]:
    allowed = set(rule_ids) if rule_ids else None
    refs: list[UpstreamRef] = []
    for rule in module.rules:
        if allowed is not None and rule.rule_id not in allowed:
            continue
        refs.append(
            UpstreamRef(
                layer="framework",
                file=module.path,
                ref_kind="rule",
                ref_id=rule.rule_id,
            )
        )
    return tuple(refs)


def _product_section_refs(product_spec_file: str, *sections: str) -> tuple[UpstreamRef, ...]:
    return tuple(
        UpstreamRef(
            layer="product_spec",
            file=product_spec_file,
            ref_kind="section",
            ref_id=section,
        )
        for section in sections
    )


def _implementation_section_refs(implementation_config_file: str, *sections: str) -> tuple[UpstreamRef, ...]:
    return tuple(
        UpstreamRef(
            layer="implementation_config",
            file=implementation_config_file,
            ref_kind="section",
            ref_id=section,
        )
        for section in sections
    )


def _route_detail_path(project: KnowledgeBaseProject) -> str:
    return f"{project.route.knowledge_detail}/{{knowledge_base_id}}"


def _document_detail_path(project: KnowledgeBaseProject) -> str:
    return f"{project.route.document_detail_prefix}/{{document_id}}"


def _expected_runtime_page_routes(project: KnowledgeBaseProject) -> dict[str, Any]:
    return {
        "home": project.route.home,
        "chat_home": project.route.workbench,
        "basketball_showcase": project.route.basketball_showcase,
        "knowledge_list": project.route.knowledge_list,
        "knowledge_detail": _route_detail_path(project),
        "document_detail": _document_detail_path(project),
        "product_spec": project.implementation.evidence.product_spec_endpoint,
    }


def _actual_runtime_page_routes(project: KnowledgeBaseProject) -> dict[str, Any]:
    from knowledge_base_runtime.app import build_knowledge_base_runtime_app

    app = build_knowledge_base_runtime_app(project)
    expected_names = {
        "root": "home",
        "knowledge_base_page": "chat_home",
        "basketball_showcase_page": "basketball_showcase",
        "knowledge_base_list_page": "knowledge_list",
        "knowledge_base_detail_page": "knowledge_detail",
        "document_detail_page": "document_detail",
        "product_spec": "product_spec",
    }
    payload: dict[str, Any] = {}
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        key = expected_names.get(route.endpoint.__name__)
        if key is None:
            continue
        payload[key] = route.path
    return payload


def _expected_frontend_surface_contract(project: KnowledgeBaseProject) -> dict[str, Any]:
    contract = project.template_contract
    return {
        "module_id": project.frontend_ir.module_id,
        "shell": project.surface.shell,
        "layout_variant": project.surface.layout_variant,
        "surface_config": {
            "sidebar_width": project.surface.sidebar_width,
            "preview_mode": project.surface.preview_mode,
            "density": project.surface.density,
        },
        "surface_regions": list(contract.required_surface_region_ids),
        "interaction_actions": list(
            contract.frontend_interaction_action_ids(
                allow_create=project.library.allow_create,
                allow_delete=project.library.allow_delete,
            )
        ),
        "state_channels": list(contract.resolve_state_channels(sticky_document=project.context.sticky_document)),
        "route_contract": project.route.to_dict(),
        "a11y": project.a11y.to_dict(),
        "component_variants": {
            "conversation_list": project.library.list_variant,
            "preview_surface": project.preview.preview_variant,
            "chat_bubble": project.chat.bubble_variant,
            "chat_composer": project.chat.composer_variant,
            "citation_summary": project.return_config.citation_card_variant,
        },
        "base_ids": [item.base_id for item in project.frontend_ir.bases],
        "rule_ids": [item.rule_id for item in project.frontend_ir.rules],
    }


def _actual_frontend_surface_contract(project: KnowledgeBaseProject) -> dict[str, Any]:
    return {
        "module_id": project.frontend_contract["module_id"],
        "shell": project.frontend_contract["shell"],
        "layout_variant": project.frontend_contract["layout_variant"],
        "surface_config": project.frontend_contract["surface_config"],
        "surface_regions": [item["region_id"] for item in project.frontend_contract["surface_regions"]],
        "interaction_actions": [item["action_id"] for item in project.frontend_contract["interaction_actions"]],
        "state_channels": [
            {"state_id": item["state_id"], "sticky": item["sticky"]}
            for item in project.frontend_contract["state_channels"]
        ],
        "route_contract": project.frontend_contract["route_contract"],
        "a11y": project.frontend_contract["a11y"],
        "component_variants": project.frontend_contract["component_variants"],
        "base_ids": project.frontend_contract["base_ids"],
        "rule_ids": project.frontend_contract["rule_ids"],
    }


def _expected_workbench_surface_contract(project: KnowledgeBaseProject) -> dict[str, Any]:
    contract = project.template_contract
    return {
        "module_id": project.domain_ir.module_id,
        "layout_variant": project.surface.layout_variant,
        "regions": list(contract.workbench_region_ids),
        "surface": {
            "sidebar_width": project.surface.sidebar_width,
            "preview_mode": project.surface.preview_mode,
            "density": project.surface.density,
        },
        "library_actions": list(
            contract.workbench_library_actions(
                allow_create=project.library.allow_create,
                allow_delete=project.library.allow_delete,
            )
        ),
        "preview": {
            "anchor_mode": project.preview.anchor_mode,
            "show_toc": project.preview.show_toc,
            "preview_variant": project.preview.preview_variant,
        },
        "chat": {
            "citation_style": project.chat.citation_style,
            "mode": project.chat.mode,
        },
        "context": {
            "selection_mode": project.context.selection_mode,
            "max_citations": project.context.max_citations,
            "max_preview_sections": project.context.max_preview_sections,
        },
        "return": {
            "targets": list(project.return_config.targets),
            "anchor_restore": project.return_config.anchor_restore,
            "citation_card_variant": project.return_config.citation_card_variant,
        },
        "flow": list(contract.workbench_flow_dicts()),
        "citation_return_contract": {
            "query_keys": list(contract.workbench_citation_query_keys),
            "targets": list(project.return_config.targets),
            "anchor_restore": project.return_config.anchor_restore,
        },
        "base_ids": [item.base_id for item in project.domain_ir.bases],
        "rule_ids": [item.rule_id for item in project.domain_ir.rules],
    }


def _actual_workbench_surface_contract(project: KnowledgeBaseProject) -> dict[str, Any]:
    return {
        "module_id": project.workbench_contract["module_id"],
        "layout_variant": project.workbench_contract["layout_variant"],
        "regions": list(project.workbench_contract["regions"]),
        "surface": project.workbench_contract["surface"],
        "library_actions": list(project.workbench_contract["library"]["actions"]),
        "preview": {
            "anchor_mode": project.workbench_contract["preview"]["anchor_mode"],
            "show_toc": project.workbench_contract["preview"]["show_toc"],
            "preview_variant": project.workbench_contract["preview"]["preview_variant"],
        },
        "chat": {
            "citation_style": project.workbench_contract["chat"]["citation_style"],
            "mode": project.workbench_contract["chat"]["mode"],
        },
        "context": {
            "selection_mode": project.workbench_contract["context"]["selection_mode"],
            "max_citations": project.workbench_contract["context"]["max_citations"],
            "max_preview_sections": project.workbench_contract["context"]["max_preview_sections"],
        },
        "return": {
            "targets": list(project.workbench_contract["return"]["targets"]),
            "anchor_restore": project.workbench_contract["return"]["anchor_restore"],
            "citation_card_variant": project.workbench_contract["return"]["citation_card_variant"],
        },
        "flow": project.workbench_contract["flow"],
        "citation_return_contract": project.workbench_contract["citation_return_contract"],
        "base_ids": project.workbench_contract["base_ids"],
        "rule_ids": project.workbench_contract["rule_ids"],
    }


def _expected_ui_surface_spec(project: KnowledgeBaseProject) -> dict[str, Any]:
    contract = project.template_contract
    return {
        "derived_from": {
            "framework_modules": {
                "frontend": project.frontend_ir.module_id,
                "domain": project.domain_ir.module_id,
            },
            "boundary_sections": {
                "SURFACE": "surface",
                "VISUAL": "visual",
                "ROUTE": "route",
                "A11Y": "a11y",
                "LIBRARY": "library",
                "PREVIEW": "preview",
                "CHAT": "chat",
                "CONTEXT": "context",
                "RETURN": "return",
            },
            "rule_drivers": {
                "frontend": [item.rule_id for item in project.frontend_ir.rules],
                "domain": [item.rule_id for item in project.domain_ir.rules],
            },
        },
        "shell": {
            "id": project.surface.shell,
            "layout_variant": project.surface.layout_variant,
            "regions": list(contract.shell_regions),
            "secondary_pages": list(contract.secondary_pages),
            "preview_mode": project.surface.preview_mode,
            "density": project.surface.density,
        },
        "pages": {
            "chat_home": {
                "path": project.route.workbench,
                "slots": list(contract.chat_home_slots),
            },
            "basketball_showcase": {
                "path": project.route.basketball_showcase,
                "title": project.showcase_page.title,
            },
            "knowledge_list": {
                "path": project.route.knowledge_list,
                "title": project.surface.copy.library_title,
            },
            "knowledge_detail": {
                "path": _route_detail_path(project),
            },
            "document_detail": {
                "path": _document_detail_path(project),
            },
        },
        "conversation": {
            "welcome_prompts": list(project.chat.welcome_prompts),
            "welcome_title": "今天想了解什么？",
        },
        "citation": {
            "style": project.chat.citation_style,
            "summary_variant": project.return_config.citation_card_variant,
            "drawer_sections": list(contract.drawer_sections),
            "document_detail_path": _document_detail_path(project),
        },
    }


def _actual_ui_surface_spec(project: KnowledgeBaseProject) -> dict[str, Any]:
    return {
        "derived_from": project.ui_spec["derived_from"],
        "shell": {
            "id": project.ui_spec["shell"]["id"],
            "layout_variant": project.ui_spec["shell"]["layout_variant"],
            "regions": project.ui_spec["shell"]["regions"],
            "secondary_pages": project.ui_spec["shell"]["secondary_pages"],
            "preview_mode": project.ui_spec["shell"]["preview_mode"],
            "density": project.ui_spec["shell"]["density"],
        },
        "pages": {
            "chat_home": {
                "path": project.ui_spec["pages"]["chat_home"]["path"],
                "slots": project.ui_spec["pages"]["chat_home"]["slots"],
            },
            "basketball_showcase": {
                "path": project.ui_spec["pages"]["basketball_showcase"]["path"],
                "title": project.ui_spec["pages"]["basketball_showcase"]["title"],
            },
            "knowledge_list": {
                "path": project.ui_spec["pages"]["knowledge_list"]["path"],
                "title": project.ui_spec["pages"]["knowledge_list"]["title"],
            },
            "knowledge_detail": {
                "path": project.ui_spec["pages"]["knowledge_detail"]["path"],
            },
            "document_detail": {
                "path": project.ui_spec["pages"]["document_detail"]["path"],
            },
        },
        "conversation": {
            "welcome_prompts": project.ui_spec["conversation"]["welcome_prompts"],
            "welcome_title": project.ui_spec["conversation"]["welcome_title"],
        },
        "citation": project.ui_spec["citation"],
    }


def _expected_backend_surface_spec(project: KnowledgeBaseProject) -> dict[str, Any]:
    return {
        "derived_from": {
            "framework_modules": {
                "domain": project.domain_ir.module_id,
                "backend": project.backend_ir.module_id,
            },
            "boundary_sections": {
                "LIBRARY": "library",
                "PREVIEW": "preview",
                "CHAT": "chat",
                "CONTEXT": "context",
                "RETURN": "return",
            },
            "rule_drivers": {
                "domain": [item.rule_id for item in project.domain_ir.rules],
                "backend": [item.rule_id for item in project.backend_ir.rules],
            },
        },
        "knowledge_base": {
            "knowledge_base_id": project.library.knowledge_base_id,
            "knowledge_base_name": project.library.knowledge_base_name,
            "knowledge_base_description": project.library.knowledge_base_description,
            "source_types": list(project.library.source_types),
            "metadata_fields": list(project.library.metadata_fields),
        },
        "retrieval": {
            "max_preview_sections": project.context.max_preview_sections,
            "max_citations": project.context.max_citations,
            "selection_mode": project.context.selection_mode,
        },
        "interaction_flow": _expected_workbench_surface_contract(project)["flow"],
        "answer_policy": {
            "citation_style": project.chat.citation_style,
        },
        "return_policy": {
            "targets": list(project.return_config.targets),
            "anchor_restore": project.return_config.anchor_restore,
            "chat_path": project.route.workbench,
            "knowledge_base_detail_path": _route_detail_path(project),
            "document_detail_path": _document_detail_path(project),
        },
        "write_policy": {
            "allow_create": project.library.allow_create,
            "allow_delete": project.library.allow_delete,
        },
    }


def _actual_backend_surface_spec(project: KnowledgeBaseProject) -> dict[str, Any]:
    return {
        "derived_from": project.backend_spec["derived_from"],
        "knowledge_base": project.backend_spec["knowledge_base"],
        "retrieval": {
            "max_preview_sections": project.backend_spec["retrieval"]["max_preview_sections"],
            "max_citations": project.backend_spec["retrieval"]["max_citations"],
            "selection_mode": project.backend_spec["retrieval"]["selection_mode"],
        },
        "interaction_flow": project.backend_spec["interaction_flow"],
        "answer_policy": {
            "citation_style": project.backend_spec["answer_policy"]["citation_style"],
        },
        "return_policy": project.backend_spec["return_policy"],
        "write_policy": project.backend_spec["write_policy"],
    }


def _expected_api_library_contracts(project: KnowledgeBaseProject) -> dict[str, Any]:
    prefix = project.route.api_prefix
    return {
        "list_knowledge_bases": {
            "path": f"{prefix}/knowledge-bases",
            "method": "GET",
            "request_fields": [],
            "response_fields": [
                "knowledge_base_id",
                "name",
                "description",
                "document_count",
                "source_types",
                "updated_at",
            ],
            "citation_item_fields": [],
        },
        "get_knowledge_base": {
            "path": f"{prefix}/knowledge-bases/{{knowledge_base_id}}",
            "method": "GET",
            "request_fields": [],
            "response_fields": [
                "knowledge_base_id",
                "name",
                "description",
                "document_count",
                "source_types",
                "updated_at",
                "documents",
            ],
            "citation_item_fields": [],
        },
        "list_documents": {
            "path": f"{prefix}/documents",
            "method": "GET",
            "request_fields": [],
            "response_fields": [
                "document_id",
                "title",
                "summary",
                "tags",
                "updated_at",
                "section_count",
            ],
            "citation_item_fields": [],
        },
        "create_document": {
            "path": f"{prefix}/documents",
            "method": "POST",
            "request_fields": ["document_id", "title", "summary", "body_markdown", "tags", "updated_at"],
            "response_fields": ["document_id", "title", "summary", "tags", "updated_at", "section_count", "body_html", "sections"],
            "citation_item_fields": [],
        },
        "get_document": {
            "path": f"{prefix}/documents/{{document_id}}",
            "method": "GET",
            "request_fields": [],
            "response_fields": ["document_id", "title", "summary", "tags", "updated_at", "section_count", "body_html", "sections"],
            "citation_item_fields": [],
        },
        "get_section": {
            "path": f"{prefix}/documents/{{document_id}}/sections/{{section_id}}",
            "method": "GET",
            "request_fields": [],
            "response_fields": ["section_id", "title", "level", "html", "plain_text"],
            "citation_item_fields": [],
        },
        "delete_document": {
            "path": f"{prefix}/documents/{{document_id}}",
            "method": "DELETE",
            "request_fields": [],
            "response_fields": ["document_id", "deleted"],
            "citation_item_fields": [],
        },
        "list_tags": {
            "path": f"{prefix}/tags",
            "method": "GET",
            "request_fields": [],
            "response_fields": ["items"],
            "citation_item_fields": [],
        },
    }


def _expected_api_chat_contract(project: KnowledgeBaseProject) -> dict[str, Any]:
    prefix = project.route.api_prefix
    return {
        "create_chat_turn": {
            "path": f"{prefix}/chat/turns",
            "method": "POST",
            "request_fields": ["message", "document_id", "section_id"],
            "response_fields": ["answer", "citations", "context_document_id", "context_section_id"],
            "citation_item_fields": [
                "citation_id",
                "document_id",
                "document_title",
                "section_id",
                "section_title",
                "snippet",
                "return_path",
                "document_path",
            ],
        }
    }


def _route_contracts_from_router(project: KnowledgeBaseProject) -> dict[str, dict[str, Any]]:
    from knowledge_base_runtime.backend import KnowledgeRepository, build_knowledge_base_router

    router = build_knowledge_base_router(project, KnowledgeRepository(project))
    payload: dict[str, dict[str, Any]] = {}
    for route in router.routes:
        if not isinstance(route, APIRoute):
            continue
        payload[route.endpoint.__name__] = {
            "path": route.path,
            "method": next(iter(sorted(route.methods - {'HEAD', 'OPTIONS'})), ""),
            "request_fields": _request_model_fields(route.endpoint),
            "response_fields": _response_model_fields(route.response_model),
            "citation_item_fields": _nested_response_model_fields(route.response_model, "citations"),
        }
    return payload


def _actual_api_library_contracts(project: KnowledgeBaseProject) -> dict[str, Any]:
    route_contracts = _route_contracts_from_router(project)
    wanted = (
        "list_knowledge_bases",
        "get_knowledge_base",
        "list_documents",
        "create_document",
        "get_document",
        "get_section",
        "delete_document",
        "list_tags",
    )
    return {key: route_contracts[key] for key in wanted}


def _actual_api_chat_contract(project: KnowledgeBaseProject) -> dict[str, Any]:
    route_contracts = _route_contracts_from_router(project)
    return {"create_chat_turn": route_contracts["create_chat_turn"]}


def _response_model_fields(model: Any) -> list[str]:
    model_type = _unwrap_model_type(model)
    if model_type is None:
        return []
    fields = getattr(model_type, "model_fields", None)
    if not isinstance(fields, dict):
        return []
    return list(fields.keys())


def _nested_response_model_fields(model: Any, field_name: str) -> list[str]:
    model_type = _unwrap_model_type(model)
    if model_type is None:
        return []
    fields = getattr(model_type, "model_fields", None)
    if not isinstance(fields, dict) or field_name not in fields:
        return []
    annotation = fields[field_name].annotation
    nested_type = _unwrap_model_type(annotation)
    if nested_type is None:
        return []
    nested_fields = getattr(nested_type, "model_fields", None)
    if not isinstance(nested_fields, dict):
        return []
    return list(nested_fields.keys())


def _request_model_fields(func: Callable[..., Any]) -> list[str]:
    signature = inspect.signature(func)
    try:
        resolved_hints = get_type_hints(func, globalns=getattr(func, "__globals__", {}), localns=None)
    except Exception:
        resolved_hints = {}
    for parameter in signature.parameters.values():
        annotation = resolved_hints.get(parameter.name, parameter.annotation)
        model_type = _unwrap_model_type(annotation)
        if model_type is None:
            continue
        fields = getattr(model_type, "model_fields", None)
        if isinstance(fields, dict):
            return list(fields.keys())
    return []


def _unwrap_model_type(model: Any) -> Any | None:
    if model is None:
        return None
    origin = get_origin(model)
    if origin in {list, tuple}:
        args = get_args(model)
        return _unwrap_model_type(args[0] if args else None)
    return model


def _expected_answer_behavior(project: KnowledgeBaseProject) -> dict[str, Any]:
    return {
        "citation_style": project.chat.citation_style,
        "citation_required": project.chat.citations_enabled,
        "max_citations_respected": True,
        "return_path_prefix": project.route.workbench,
        "document_path_prefix": project.route.document_detail_prefix,
        "context_tracks_lead": True,
    }


def _actual_answer_behavior(project: KnowledgeBaseProject) -> dict[str, Any]:
    from knowledge_base_runtime.backend import KnowledgeRepository

    repository = KnowledgeRepository(project)
    response = repository.answer_question(
        "Explain the generated runtime and citation drawer.",
        document_id="framework-compilation-chain",
        section_id="generated-runtime",
    )
    citations = list(response.citations)
    citation_style = (
        project.template_contract.required_chat_citation_style
        if citations and "[1]" in response.answer
        else f"missing_{project.template_contract.required_chat_citation_style}"
    )
    return_path_prefix = project.route.workbench
    document_path_prefix = project.route.document_detail_prefix
    if citations and not all(item.return_path.startswith(f"{return_path_prefix}?") for item in citations):
        return_path_prefix = "mismatch"
    if citations and not all(item.document_path.startswith(document_path_prefix) for item in citations):
        document_path_prefix = "mismatch"
    context_tracks_lead = True
    if citations:
        lead = citations[0]
        context_tracks_lead = (
            response.context_document_id == lead.document_id
            and response.context_section_id == lead.section_id
        )
    return {
        "citation_style": citation_style,
        "citation_required": bool(citations),
        "max_citations_respected": len(citations) <= project.context.max_citations,
        "return_path_prefix": return_path_prefix,
        "document_path_prefix": document_path_prefix,
        "context_tracks_lead": context_tracks_lead,
    }


def _definitions(project: KnowledgeBaseProject) -> tuple[SymbolDefinition, ...]:
    product_spec_file = project.product_spec_file
    implementation_config_file = project.implementation_config_file
    frontend_refs = _framework_rule_refs(project.frontend_ir)
    domain_refs = _framework_rule_refs(project.domain_ir)
    backend_refs = _framework_rule_refs(project.backend_ir)
    return (
        SymbolDefinition(
            symbol_id="kb.runtime.page_routes",
            owner="framework",
            kind="runtime_routes",
            risk="high",
            expected_builder=_expected_runtime_page_routes,
            actual_extractor=_actual_runtime_page_routes,
            extractor="python.runtime_routes.v1",
            comparator="exact_contract.v1",
            upstream_ref_builder=lambda current: (
                *frontend_refs,
                *_product_section_refs(product_spec_file, "route"),
                *_implementation_section_refs(implementation_config_file, "evidence"),
            ),
            required_bindings=(
                ("src/knowledge_base_runtime/app.py", "function:root"),
                ("src/knowledge_base_runtime/app.py", "function:knowledge_base_page"),
                ("src/knowledge_base_runtime/app.py", "function:basketball_showcase_page"),
                ("src/knowledge_base_runtime/app.py", "function:knowledge_base_list_page"),
                ("src/knowledge_base_runtime/app.py", "function:knowledge_base_detail_page"),
                ("src/knowledge_base_runtime/app.py", "function:document_detail_page"),
                ("src/knowledge_base_runtime/app.py", "function:product_spec"),
            ),
            high_risk_file_checks=(("src/knowledge_base_runtime/app.py", "build_knowledge_base_runtime_app"),),
        ),
        SymbolDefinition(
            symbol_id="kb.frontend.surface_contract",
            owner="framework",
            kind="surface_contract",
            risk="high",
            expected_builder=_expected_frontend_surface_contract,
            actual_extractor=_actual_frontend_surface_contract,
            extractor="frontend.surface_contract.v1",
            comparator="surface_contract_exact.v1",
            upstream_ref_builder=lambda current: (
                *frontend_refs,
                *_product_section_refs(product_spec_file, "surface", "route", "a11y", "library", "preview", "chat", "return"),
            ),
            required_bindings=(("src/frontend_kernel/contracts.py", "function:build_frontend_contract"),),
        ),
        SymbolDefinition(
            symbol_id="kb.workbench.surface_contract",
            owner="framework",
            kind="surface_contract",
            risk="high",
            expected_builder=_expected_workbench_surface_contract,
            actual_extractor=_actual_workbench_surface_contract,
            extractor="python.workbench_surface.v1",
            comparator="surface_contract_exact.v1",
            upstream_ref_builder=lambda current: (
                *domain_refs,
                *_product_section_refs(product_spec_file, "library", "preview", "chat", "context", "return", "surface"),
            ),
            required_bindings=(("src/knowledge_base_framework/workbench.py", "function:build_workbench_contract"),),
        ),
        SymbolDefinition(
            symbol_id="kb.ui.surface_spec",
            owner="framework",
            kind="ui_surface",
            risk="high",
            expected_builder=_expected_ui_surface_spec,
            actual_extractor=_actual_ui_surface_spec,
            extractor="python.ui_surface.v1",
            comparator="surface_contract_exact.v1",
            upstream_ref_builder=lambda current: (
                *frontend_refs,
                *_product_section_refs(product_spec_file, "surface", "route", "showcase_page", "chat", "return"),
            ),
            required_bindings=(("src/project_runtime/knowledge_base.py", "function:_build_ui_spec"),),
        ),
        SymbolDefinition(
            symbol_id="kb.backend.surface_spec",
            owner="implementation_config",
            kind="backend_surface",
            risk="high",
            expected_builder=_expected_backend_surface_spec,
            actual_extractor=_actual_backend_surface_spec,
            extractor="python.backend_surface.v1",
            comparator="surface_contract_exact.v1",
            upstream_ref_builder=lambda current: (
                *backend_refs,
                *_product_section_refs(product_spec_file, "library", "chat", "context", "return", "route"),
                *_implementation_section_refs(implementation_config_file, "backend"),
            ),
            required_bindings=(("src/project_runtime/knowledge_base.py", "function:_build_backend_spec"),),
        ),
        SymbolDefinition(
            symbol_id="kb.api.library_contracts",
            owner="framework",
            kind="api_contract",
            risk="high",
            expected_builder=_expected_api_library_contracts,
            actual_extractor=_actual_api_library_contracts,
            extractor="python.api_contract.v1",
            comparator="exact_contract.v1",
            upstream_ref_builder=lambda current: (
                *backend_refs,
                *_product_section_refs(product_spec_file, "route", "library", "preview"),
            ),
            required_bindings=(
                ("src/knowledge_base_runtime/backend.py", "function:list_knowledge_bases"),
                ("src/knowledge_base_runtime/backend.py", "function:get_knowledge_base"),
                ("src/knowledge_base_runtime/backend.py", "function:list_documents"),
                ("src/knowledge_base_runtime/backend.py", "function:create_document"),
                ("src/knowledge_base_runtime/backend.py", "function:get_document"),
                ("src/knowledge_base_runtime/backend.py", "function:get_section"),
                ("src/knowledge_base_runtime/backend.py", "function:delete_document"),
                ("src/knowledge_base_runtime/backend.py", "function:list_tags"),
            ),
            high_risk_file_checks=(("src/knowledge_base_runtime/backend.py", "build_knowledge_base_router"),),
        ),
        SymbolDefinition(
            symbol_id="kb.api.chat_contract",
            owner="framework",
            kind="api_contract",
            risk="high",
            expected_builder=_expected_api_chat_contract,
            actual_extractor=_actual_api_chat_contract,
            extractor="python.api_contract.v1",
            comparator="exact_contract.v1",
            upstream_ref_builder=lambda current: (
                *backend_refs,
                *_product_section_refs(product_spec_file, "route", "chat", "context", "return"),
            ),
            required_bindings=(("src/knowledge_base_runtime/backend.py", "function:create_chat_turn"),),
            high_risk_file_checks=(("src/knowledge_base_runtime/backend.py", "build_knowledge_base_router"),),
        ),
        SymbolDefinition(
            symbol_id="kb.answer.behavior",
            owner="product_spec",
            kind="answer_behavior",
            risk="high",
            expected_builder=_expected_answer_behavior,
            actual_extractor=_actual_answer_behavior,
            extractor="python.answer_behavior.v1",
            comparator="ordered_behavior_surface.v1",
            upstream_ref_builder=lambda current: (
                *domain_refs,
                *_product_section_refs(product_spec_file, "chat", "context", "return"),
                *_implementation_section_refs(implementation_config_file, "backend"),
            ),
            required_bindings=(
                ("src/knowledge_base_runtime/backend.py", "function:answer_question"),
            ),
        ),
    )


def governed_files_for_project(project: KnowledgeBaseProject) -> list[str]:
    files: set[str] = set()
    for definition in _definitions(project):
        for rel_file, _ in definition.required_bindings:
            files.add(rel_file)
    return sorted(files)


def _callable_role_binding(callable_obj: Callable[..., Any]) -> tuple[str, str]:
    source_file = inspect.getsourcefile(callable_obj)
    if source_file is None:
        raise ValueError(f"callable has no source file: {callable_obj}")
    return (_relative(source_file), f"function:{callable_obj.__name__}")


def _candidate_kinds_for_locator(locator: str, object_kind: str) -> tuple[str, ...]:
    name = locator.split(":", 1)[-1]
    lowered = name.lower()
    if locator.startswith("class:"):
        return ("python_schema_carrier",)
    if lowered.startswith("build_") and ("router" in lowered or "app" in lowered):
        return ("python_route_builder", "python_builder")
    if object_kind == "runtime_routes":
        return ("python_route_handler",)
    if object_kind == "api_contract":
        if lowered.startswith("build_"):
            return ("python_route_builder", "python_builder")
        return ("python_route_handler", "python_builder")
    if object_kind in {"surface_contract", "ui_surface", "backend_surface"}:
        return ("python_builder", "python_config_sink", "python_evidence_builder")
    if object_kind == "answer_behavior":
        return ("python_behavior_orchestrator", "python_builder")
    return ("python_builder", "python_evidence_builder", "python_config_sink")


def _role_kind_for_locator(locator: str, object_kind: str) -> str:
    name = locator.split(":", 1)[-1]
    lowered = name.lower()
    if object_kind == "runtime_routes":
        return "route_handler"
    if object_kind == "api_contract":
        if lowered.startswith("build_"):
            return "route_registration"
        return "api_handler"
    if object_kind in {"surface_contract", "ui_surface", "backend_surface"}:
        return "spec_builder"
    if object_kind == "answer_behavior":
        return "behavior_orchestrator"
    return "implementation_carrier"


def _role_from_binding(
    symbol_id: str,
    object_kind: str,
    rel_file: str,
    locator: str,
    *,
    classification: str = "governed",
) -> RequiredRole:
    name = locator.split(":", 1)[-1]
    return RequiredRole(
        role_id=f"{symbol_id}:{name}",
        role_kind=_role_kind_for_locator(locator, object_kind),
        description=f"{symbol_id} requires {locator} to stay bound",
        candidate_kinds=_candidate_kinds_for_locator(locator, object_kind),
        locator_patterns=(locator,),
        file_hints=(rel_file,),
        classification=classification,
        min_count=1,
        max_count=1,
    )


def _role_from_callable(
    symbol_id: str,
    role_id: str,
    role_kind: str,
    callable_obj: Callable[..., Any],
) -> RequiredRole:
    rel_file, locator = _callable_role_binding(callable_obj)
    return RequiredRole(
        role_id=f"{symbol_id}:{role_id}",
        role_kind=role_kind,
        description=f"{symbol_id} requires governance callable {callable_obj.__name__}",
        candidate_kinds=_candidate_kinds_for_locator(locator, "governance"),
        locator_patterns=(locator,),
        file_hints=(rel_file,),
        classification="attached",
        min_count=1,
        max_count=1,
    )


def _group_sources(refs: tuple[UpstreamRef, ...]) -> tuple[tuple[SourceRef, ...], tuple[SourceRef, ...], tuple[SourceRef, ...]]:
    framework: list[SourceRef] = []
    product: list[SourceRef] = []
    implementation: list[SourceRef] = []
    for ref in refs:
        source = SourceRef(
            layer=ref.layer,
            file=ref.file,
            ref_kind=ref.ref_kind,
            ref_id=ref.ref_id,
            digest=digest_upstream_ref(ref),
        )
        if ref.layer == "framework":
            framework.append(source)
        elif ref.layer == "product_spec":
            product.append(source)
        elif ref.layer == "implementation_config":
            implementation.append(source)
    return (tuple(framework), tuple(product), tuple(implementation))


def _structural_object_from_definition(
    project: KnowledgeBaseProject,
    definition: SymbolDefinition,
) -> StructuralObject:
    upstream_refs = definition.upstream_ref_builder(project)
    framework_sources, product_sources, implementation_sources = _group_sources(upstream_refs)
    required_roles: list[RequiredRole] = [
        _role_from_binding(definition.symbol_id, definition.kind, rel_file, locator)
        for rel_file, locator in definition.required_bindings
    ]
    for rel_file, builder_name in definition.high_risk_file_checks:
        required_roles.append(
            RequiredRole(
                role_id=f"{definition.symbol_id}:{builder_name}",
                role_kind="route_registration" if definition.kind in {"runtime_routes", "api_contract"} else "builder",
                description=f"{definition.symbol_id} requires high-risk carrier {builder_name}",
                candidate_kinds=("python_route_builder", "python_builder", "python_config_sink"),
                locator_patterns=(f"function:{builder_name}",),
                file_hints=(rel_file,),
                classification="governed",
                min_count=1,
                max_count=1,
            )
        )
    required_roles.append(
        _role_from_callable(definition.symbol_id, "expected_builder", "expected_builder", definition.expected_builder)
    )
    required_roles.append(
        _role_from_callable(definition.symbol_id, "actual_extractor", "actual_extractor", definition.actual_extractor)
    )

    expected_evidence = definition.expected_builder(project)
    actual_evidence = definition.actual_extractor(project)
    origin_categories: list[str] = ["legacy-migrated"]
    if framework_sources:
        origin_categories.append("framework-derived")
    if product_sources:
        origin_categories.append("product-instantiated")
    if implementation_sources:
        origin_categories.append("implementation-refined")
    return StructuralObject(
        object_id=definition.symbol_id,
        project_id=project.metadata.project_id,
        kind=definition.kind,
        title=definition.symbol_id,
        risk_level=definition.risk,
        cardinality="exactly_one",
        status="required",
        semantic=expected_evidence,
        required_roles=tuple(required_roles),
        sources_framework=framework_sources,
        sources_product=product_sources,
        sources_implementation=implementation_sources,
        expected_evidence=expected_evidence,
        expected_fingerprint=_fingerprint(expected_evidence),
        actual_evidence=actual_evidence,
        actual_fingerprint=_fingerprint(actual_evidence),
        comparator=definition.comparator,
        extractor=definition.extractor,
        origin_categories=tuple(sorted(set(origin_categories))),
    )


def _normalize_effect_target_value(relation: str, target_value: Any) -> Any:
    if relation == "equals":
        return target_value
    if relation == "basename":
        return Path(str(target_value)).name
    raise ValueError(f"unsupported governance implementation effect relation: {relation}")


def _runtime_value(payload: dict[str, Any], dotted_path: str) -> Any:
    current: Any = payload
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return "__missing__"
        current = current[part]
    return current


def _effect_sink_roles(field_path: str, targets: tuple[str, ...]) -> tuple[RequiredRole, ...]:
    roles: list[RequiredRole] = [
        RequiredRole(
            role_id=f"{field_path}:effect_manifest",
            role_kind="effect_evidence",
            description=f"{field_path} must stay visible in build_implementation_effect_manifest",
            candidate_kinds=("python_config_sink", "python_builder"),
            locator_patterns=("function:build_implementation_effect_manifest",),
            file_hints=("src/project_runtime/knowledge_base.py",),
            classification="attached",
            min_count=1,
            max_count=1,
        )
    ]
    for target_path in targets:
        if target_path.startswith("ui_spec."):
            locator = "function:_build_ui_spec"
        elif target_path.startswith("backend_spec."):
            locator = "function:_build_backend_spec"
        elif target_path.startswith("generated_artifacts."):
            locator = "function:materialize_knowledge_base_project"
        else:
            locator = "function:build_implementation_effect_manifest"
        roles.append(
            RequiredRole(
                role_id=f"{field_path}:{target_path}",
                role_kind="effect_sink",
                description=f"{field_path} must land in downstream target {target_path}",
                candidate_kinds=("python_config_sink", "python_builder", "python_evidence_builder"),
                locator_patterns=(locator,),
                file_hints=("src/project_runtime/knowledge_base.py",),
                classification="governed",
                min_count=1,
                max_count=1,
            )
        )
    return tuple(roles)


def _config_effect_object(
    project: KnowledgeBaseProject,
    field_path: str,
    effect_entry: dict[str, Any],
) -> StructuralObject:
    relation = str(effect_entry.get("relation") or "equals")
    configured_value = effect_entry.get("value")
    targets = tuple(str(item) for item in effect_entry.get("targets", []) if str(item).strip())
    implementation_section = field_path.split(".", 1)[0]
    implementation_ref = SourceRef(
        layer="implementation_config",
        file=project.implementation_config_file,
        ref_kind="section",
        ref_id=implementation_section,
        digest=digest_upstream_ref(
            UpstreamRef(
                layer="implementation_config",
                file=project.implementation_config_file,
                ref_kind="section",
                ref_id=implementation_section,
            )
        ),
    )
    expected_evidence = {
        "field_path": field_path,
        "relation": relation,
        "configured_value": configured_value,
        "targets": [
            {
                "target_path": target_path,
                "observed_value": configured_value,
            }
            for target_path in targets
        ],
    }
    runtime_bundle = project.to_runtime_bundle_dict()
    if runtime_bundle.get("generated_artifacts") in (None, {}, []):
        runtime_bundle["generated_artifacts"] = dict(_expected_generated_artifact_paths(project))
    actual_evidence = {
        "field_path": field_path,
        "relation": relation,
        "configured_value": configured_value,
        "targets": [
            {
                "target_path": target_path,
                "observed_value": _normalize_effect_target_value(
                    relation,
                    _runtime_value(runtime_bundle, target_path),
                ),
            }
            for target_path in targets
        ],
    }
    return StructuralObject(
        object_id=f"{project.metadata.project_id}.config_effect.{field_path}",
        project_id=project.metadata.project_id,
        kind="implementation_effect",
        title=field_path,
        risk_level="high",
        cardinality="exactly_one",
        status="required",
        semantic={
            "configured_value": configured_value,
            "relation": relation,
            "targets": list(targets),
        },
        required_roles=_effect_sink_roles(field_path, targets),
        sources_implementation=(implementation_ref,),
        expected_evidence=expected_evidence,
        expected_fingerprint=_fingerprint(expected_evidence),
        actual_evidence=actual_evidence,
        actual_fingerprint=_fingerprint(actual_evidence),
        comparator="implementation_effect_exact.v1",
        extractor="implementation.effect.v1",
        origin_categories=("implementation-refined", "evidence-only"),
    )


def _project_record_for(project: KnowledgeBaseProject) -> Any:
    rel_product_spec = _relative(project.product_spec_file)
    for item in discover_framework_driven_projects():
        if item.product_spec_file == rel_product_spec:
            return item
    artifact_names = project.implementation.artifacts
    return {
        "project_id": project.metadata.project_id,
        "template_id": project.metadata.template,
        "product_spec_file": rel_product_spec,
        "implementation_config_file": _relative(project.implementation_config_file),
        "generated_dir": _relative(Path(project.product_spec_file).parent / "generated"),
        "discovery_reasons": (
            "project spec exists under projects/<project_id>/product_spec.toml",
            "implementation_config.toml exists beside product_spec.toml",
            "registered template resolved through project.template",
            "project loads through the registered framework-driven materialization chain",
        ),
        "framework_refs": tuple(
            item
            for item in (
                project.framework.frontend,
                project.framework.domain,
                project.framework.backend,
            )
            if isinstance(item, str) and item.strip()
        ),
        "artifact_contract": tuple(
            getattr(artifact_names, field_name)
            for field_name in (
                "framework_ir_json",
                "product_spec_json",
                "implementation_bundle_py",
                "generation_manifest_json",
                "governance_manifest_json",
                "governance_tree_json",
                "strict_zone_report_json",
                "object_coverage_report_json",
            )
        ),
    }


def build_governance_closure(project: KnowledgeBaseProject) -> ProjectGovernanceClosure:
    from project_runtime.knowledge_base import build_implementation_effect_manifest

    definitions = _definitions(project)
    bindings_by_symbol = collect_governed_bindings(governed_files_for_project(project))
    binding_issues = _binding_validation_issues(bindings_by_symbol, definitions)
    if binding_issues:
        details = "; ".join(
            f"{item['file']}:{item['line']} {item['code']} {item['message']}" for item in binding_issues
        )
        raise ValueError(f"invalid governed bindings: {details}")
    unbound = find_unbound_high_risk_structures()
    if unbound:
        details = "; ".join(f"{item['file']}:{item['line']} -> {item['locator']}" for item in unbound)
        raise ValueError(f"missing governed_symbol binding for high-risk structures: {details}")

    for definition in definitions:
        missing_bindings = [
            f"{rel_file} -> {locator}"
            for rel_file, locator in definition.required_bindings
            if not _binding_exists(bindings_by_symbol, definition.symbol_id, rel_file, locator)
        ]
        if missing_bindings:
            raise ValueError(
                f"missing governed_symbol binding(s) for {definition.symbol_id}: {', '.join(missing_bindings)}"
            )

    structural_objects: list[StructuralObject] = [
        _structural_object_from_definition(project, definition)
        for definition in definitions
    ]
    for field_path, effect_entry in sorted(build_implementation_effect_manifest(project).items()):
        structural_objects.append(_config_effect_object(project, field_path, effect_entry))

    raw_candidates = scan_python_structural_candidates(project_id=project.metadata.project_id)
    seed_bindings = resolve_role_bindings(tuple(structural_objects), raw_candidates)
    seed_candidates = classify_candidates(tuple(structural_objects), raw_candidates, seed_bindings)
    seed_strict_zone = infer_strict_zone(
        tuple(structural_objects),
        seed_bindings,
        seed_candidates,
        _expected_generated_artifact_paths(project),
    )
    strict_files = {entry.file for entry in seed_strict_zone}
    seed_candidate_ids = {candidate_id for binding in seed_bindings for candidate_id in binding.candidate_ids}
    project_candidates = tuple(
        candidate
        for candidate in raw_candidates
        if candidate.file in strict_files and (candidate.confidence >= 0.75 or candidate.candidate_id in seed_candidate_ids)
    )
    role_bindings = resolve_role_bindings(tuple(structural_objects), project_candidates)
    candidates = classify_candidates(tuple(structural_objects), project_candidates, role_bindings)
    strict_zone = infer_strict_zone(
        tuple(structural_objects),
        role_bindings,
        candidates,
        _expected_generated_artifact_paths(project),
    )
    strict_zone = annotate_strict_zone_minimality(
        strict_zone,
        role_bindings,
        candidates,
        _expected_generated_artifact_paths(project),
    )
    record = _project_record_for(project)
    if hasattr(record, "to_dict"):
        discovery = record
    else:
        from project_runtime.project_governance import FrameworkDrivenProjectRecord

        discovery = FrameworkDrivenProjectRecord(**record)

    upstream_index: dict[tuple[str, str, str, str], SourceRef] = {}
    for structural_object in structural_objects:
        for source in structural_object.all_sources():
            upstream_index[source.key()] = source
    return ProjectGovernanceClosure(
        project_id=project.metadata.project_id,
        template_id=project.metadata.template,
        product_spec_file=_relative(project.product_spec_file),
        implementation_config_file=_relative(project.implementation_config_file),
        discovery=discovery,
        structural_objects=tuple(sorted(structural_objects, key=lambda item: item.object_id)),
        candidates=tuple(sorted(candidates, key=lambda item: (item.file, item.locator, item.kind))),
        role_bindings=tuple(sorted(role_bindings, key=lambda item: (item.object_id, item.role_id))),
        strict_zone=tuple(sorted(strict_zone, key=lambda item: item.file)),
        upstream_closure=tuple(
            sorted(upstream_index.values(), key=lambda item: (item.layer, item.file, item.ref_kind, item.ref_id))
        ),
        evidence_artifacts=_expected_generated_artifact_paths(project),
    )


def _build_governance_snapshot(project: KnowledgeBaseProject) -> dict[str, Any]:
    definitions = _definitions(project)
    bindings_by_symbol = collect_governed_bindings(governed_files_for_project(project))
    binding_issues = _binding_validation_issues(bindings_by_symbol, definitions)
    if binding_issues:
        details = "; ".join(
            f"{item['file']}:{item['line']} {item['code']} {item['message']}" for item in binding_issues
        )
        raise ValueError(f"invalid governed bindings: {details}")
    unbound = find_unbound_high_risk_structures()
    if unbound:
        details = "; ".join(f"{item['file']}:{item['line']} -> {item['locator']}" for item in unbound)
        raise ValueError(f"missing governed_symbol binding for high-risk structures: {details}")
    upstream_closure: dict[tuple[str, str, str, str], str] = {}
    symbols: list[dict[str, Any]] = []
    for definition in definitions:
        bindings = sorted(
            bindings_by_symbol.get(definition.symbol_id, []),
            key=lambda item: (item.file, item.line, item.locator),
        )
        missing_bindings = [
            f"{rel_file} -> {locator}"
            for rel_file, locator in definition.required_bindings
            if not _binding_exists(bindings_by_symbol, definition.symbol_id, rel_file, locator)
        ]
        if missing_bindings:
            raise ValueError(
                f"missing governed_symbol binding(s) for {definition.symbol_id}: {', '.join(missing_bindings)}"
            )
        expected_evidence = definition.expected_builder(project)
        upstream_refs = definition.upstream_ref_builder(project)
        for ref in upstream_refs:
            upstream_closure[ref.key()] = digest_upstream_ref(ref)
        symbols.append(
            {
                "symbol_id": definition.symbol_id,
                "owner": definition.owner,
                "kind": definition.kind,
                "risk": definition.risk,
                "bindings": [item.to_manifest_dict() for item in bindings],
                "upstream_refs": [
                    ref.to_manifest_dict(digest=upstream_closure[ref.key()])
                    for ref in upstream_refs
                ],
                "expected": {
                    "extractor": definition.extractor,
                    "comparator": definition.comparator,
                    "fingerprint": _fingerprint(expected_evidence),
                    "evidence": expected_evidence,
                },
            }
        )
    closure_items = [
        {
            "layer": layer,
            "file": file_name,
            "ref_kind": ref_kind,
            "ref_id": ref_id,
            "digest": digest,
        }
        for (layer, file_name, ref_kind, ref_id), digest in sorted(upstream_closure.items())
    ]
    return {
        "definitions": definitions,
        "symbols": symbols,
        "upstream_closure": closure_items,
    }


def _object_owner(structural_object: StructuralObject) -> str:
    if structural_object.sources_framework:
        return "framework"
    if structural_object.sources_product:
        return "product_spec"
    if structural_object.sources_implementation:
        return "implementation_config"
    return "project"


def _binding_index_for_project(project: KnowledgeBaseProject) -> dict[str, list[GovernedBinding]]:
    return collect_governed_bindings(governed_files_for_project(project))


def build_governance_manifest(project: KnowledgeBaseProject) -> dict[str, Any]:
    closure = build_governance_closure(project)
    strict_zone_report = build_strict_zone_report(closure)
    object_coverage_report = build_object_coverage_report(closure)
    binding_index = _binding_index_for_project(project)
    symbols = []
    for structural_object in closure.structural_objects:
        bindings = [
            item.to_manifest_dict()
            for item in sorted(
                binding_index.get(structural_object.object_id, []),
                key=lambda entry: (entry.file, entry.line, entry.locator),
            )
        ]
        symbols.append(
            {
                "symbol_id": structural_object.object_id,
                "owner": _object_owner(structural_object),
                "kind": structural_object.kind,
                "risk": structural_object.risk_level,
                "bindings": bindings,
                "expected": {
                    "extractor": structural_object.extractor,
                    "comparator": structural_object.comparator,
                    "fingerprint": structural_object.expected_fingerprint,
                    "evidence": structural_object.expected_evidence,
                },
            }
        )
    payload = closure.to_manifest_dict()
    payload.update(
        {
            "manifest_version": GOVERNANCE_MANIFEST_VERSION,
            "generator_version": GOVERNANCE_GENERATOR_VERSION,
            "symbols": symbols,
            "strict_zone_report": strict_zone_report,
            "object_coverage_report": object_coverage_report,
        }
    )
    return payload


def build_governance_tree(project: KnowledgeBaseProject) -> dict[str, Any]:
    closure = build_governance_closure(project)
    strict_zone_report = build_strict_zone_report(closure)
    object_coverage_report = build_object_coverage_report(closure)
    project_root_id = f"project:{project.metadata.project_id}"
    framework_root_id = f"{project_root_id}:framework"
    product_root_id = f"{project_root_id}:product_spec"
    implementation_root_id = f"{project_root_id}:implementation_config"
    structure_root_id = f"{project_root_id}:structure"
    code_root_id = f"{project_root_id}:code"
    evidence_root_id = f"{project_root_id}:evidence"

    nodes: dict[str, dict[str, Any]] = {}
    source_node_ids: dict[tuple[str, str, str, str], str] = {}
    role_node_ids: dict[tuple[str, str], str] = {}

    def add_node(node_id: str, *, parent: str | None, **payload: Any) -> dict[str, Any]:
        existing = nodes.get(node_id)
        if existing is None:
            existing = {"node_id": node_id, "parent": parent, "children": []}
            existing.update(payload)
            nodes[node_id] = existing
        if parent is not None and parent in nodes and node_id not in nodes[parent]["children"]:
            nodes[parent]["children"].append(node_id)
        return existing

    add_node(
        project_root_id,
        parent=None,
        kind="project_root",
        layer="Project",
        title=project.metadata.display_name,
        file=_relative(project.product_spec_file),
        template_id=project.metadata.template,
        project_id=project.metadata.project_id,
    )
    add_node(framework_root_id, parent=project_root_id, kind="framework_root", layer="Framework", title="Framework")
    add_node(product_root_id, parent=project_root_id, kind="product_root", layer="Product Spec", title="Product Spec")
    add_node(
        implementation_root_id,
        parent=project_root_id,
        kind="implementation_root",
        layer="Implementation Config",
        title="Implementation Config",
    )
    add_node(
        structure_root_id,
        parent=project_root_id,
        kind="structure_root",
        layer="Project Structure",
        title="Project Structure",
    )
    add_node(code_root_id, parent=project_root_id, kind="code_root", layer="Code", title="Code")
    add_node(evidence_root_id, parent=project_root_id, kind="evidence_root", layer="Evidence", title="Evidence")

    framework_modules: dict[str, FrameworkModuleIR] = {}
    for source in closure.upstream_closure:
        if source.layer == "framework":
            module = framework_modules.get(source.file)
            if module is None:
                module = parse_framework_module(REPO_ROOT / source.file)
                framework_modules[source.file] = module
            module_node_id = f"{framework_root_id}:module:{module.module_id}"
            add_node(
                module_node_id,
                parent=framework_root_id,
                kind="framework_module",
                layer="Framework",
                title=module.module_id,
                file=source.file,
                project_id=project.metadata.project_id,
            )
            node_id = f"{module_node_id}:rule:{source.ref_id}"
            add_node(
                node_id,
                parent=module_node_id,
                kind="framework_rule",
                layer="Framework",
                title=source.ref_id,
                file=source.file,
                ref_kind=source.ref_kind,
                ref_id=source.ref_id,
                digest=source.digest,
                project_id=project.metadata.project_id,
            )
            source_node_ids[source.key()] = node_id
            continue

        if source.layer == "product_spec":
            file_node_id = f"{product_root_id}:file:{source.file}"
            add_node(
                file_node_id,
                parent=product_root_id,
                kind="product_file",
                layer="Product Spec",
                title=Path(source.file).name,
                file=source.file,
                project_id=project.metadata.project_id,
            )
            node_id = f"{file_node_id}:section:{source.ref_id}"
            add_node(
                node_id,
                parent=file_node_id,
                kind="product_section",
                layer="Product Spec",
                title=source.ref_id,
                file=source.file,
                ref_kind=source.ref_kind,
                ref_id=source.ref_id,
                digest=source.digest,
                project_id=project.metadata.project_id,
            )
            source_node_ids[source.key()] = node_id
            continue

        if source.layer == "implementation_config":
            file_node_id = f"{implementation_root_id}:file:{source.file}"
            add_node(
                file_node_id,
                parent=implementation_root_id,
                kind="implementation_file",
                layer="Implementation Config",
                title=Path(source.file).name,
                file=source.file,
                project_id=project.metadata.project_id,
            )
            node_id = f"{file_node_id}:section:{source.ref_id}"
            add_node(
                node_id,
                parent=file_node_id,
                kind="implementation_section",
                layer="Implementation Config",
                title=source.ref_id,
                file=source.file,
                ref_kind=source.ref_kind,
                ref_id=source.ref_id,
                digest=source.digest,
                project_id=project.metadata.project_id,
            )
            source_node_ids[source.key()] = node_id

    for structural_object in closure.structural_objects:
        object_node_id = f"{structure_root_id}:object:{structural_object.object_id}"
        upstream_ids = [
            source_node_ids[source.key()]
            for source in structural_object.all_sources()
            if source.key() in source_node_ids
        ]
        add_node(
            object_node_id,
            parent=structure_root_id,
            kind="structural_object",
            layer="Project Structure",
            title=structural_object.title,
            object_id=structural_object.object_id,
            structural_kind=structural_object.kind,
            risk=structural_object.risk_level,
            status=structural_object.status,
            cardinality=structural_object.cardinality,
            comparator=structural_object.comparator,
            extractor=structural_object.extractor,
            origin_categories=list(structural_object.origin_categories),
            expected_evidence=structural_object.expected_evidence,
            expected_fingerprint=structural_object.expected_fingerprint,
            actual_evidence=structural_object.actual_evidence,
            actual_fingerprint=structural_object.actual_fingerprint,
            derived_from=upstream_ids,
            project_id=project.metadata.project_id,
        )
        for role in structural_object.required_roles:
            role_node_id = f"{object_node_id}:role:{role.role_id}"
            add_node(
                role_node_id,
                parent=object_node_id,
                kind="required_role",
                layer="Project Structure",
                title=role.role_id,
                object_id=structural_object.object_id,
                role_id=role.role_id,
                role_kind=role.role_kind,
                classification=role.classification,
                locator_patterns=list(role.locator_patterns),
                file_hints=list(role.file_hints),
                candidate_kinds=list(role.candidate_kinds),
                derived_from=[object_node_id],
                project_id=project.metadata.project_id,
            )
            role_node_ids[(structural_object.object_id, role.role_id)] = role_node_id

    for strict_entry in closure.strict_zone:
        file_node_id = f"{code_root_id}:file:{strict_entry.file}"
        derived_from = [
            role_node_ids[(object_id, role_id)]
            for object_id in strict_entry.object_ids
            for role_id in strict_entry.role_ids
            if (object_id, role_id) in role_node_ids
        ]
        if not derived_from:
            derived_from = [
                f"{structure_root_id}:object:{object_id}"
                for object_id in strict_entry.object_ids
            ]
        add_node(
            file_node_id,
            parent=code_root_id,
            kind="strict_zone_file",
            layer="Code",
            title=Path(strict_entry.file).name,
            file=strict_entry.file,
            object_ids=list(strict_entry.object_ids),
            role_ids=list(strict_entry.role_ids),
            reasons=list(strict_entry.reasons),
            why_required=list(strict_entry.why_required),
            minimality_status=strict_entry.minimality_status,
            derived_from=derived_from,
            project_id=project.metadata.project_id,
        )

    for candidate in closure.candidates:
        file_node_id = f"{code_root_id}:file:{candidate.file}"
        if file_node_id not in nodes:
            add_node(
                file_node_id,
                parent=code_root_id,
                kind="strict_zone_file",
                layer="Code",
                title=Path(candidate.file).name,
                file=candidate.file,
                object_ids=[],
                role_ids=[],
                reasons=["candidate-only strict zone carrier"],
                derived_from=[],
                project_id=project.metadata.project_id,
            )
        derived_from = [
            role_node_ids[(candidate.object_id, role_id)]
            for role_id in candidate.role_ids
            if candidate.object_id is not None and (candidate.object_id, role_id) in role_node_ids
        ]
        if not derived_from and candidate.object_id is not None:
            derived_from = [f"{structure_root_id}:object:{candidate.object_id}"]
        add_node(
            f"{file_node_id}:candidate:{candidate.candidate_id}",
            parent=file_node_id,
            kind="structural_candidate",
            layer="Code",
            title=candidate.locator,
            file=candidate.file,
            locator=candidate.locator,
            candidate_id=candidate.candidate_id,
            candidate_kind=candidate.kind,
            confidence=round(candidate.confidence, 3),
            classification=candidate.classification,
            object_id=candidate.object_id,
            role_ids=list(candidate.role_ids),
            reasons=list(candidate.reasons),
            derived_from=derived_from,
            project_id=project.metadata.project_id,
        )

    all_object_node_ids = [
        f"{structure_root_id}:object:{item.object_id}" for item in closure.structural_objects
    ]
    for artifact_key, rel_path in closure.evidence_artifacts.items():
        add_node(
            f"{evidence_root_id}:artifact:{artifact_key}",
            parent=evidence_root_id,
            kind="evidence_artifact",
            layer="Evidence",
            title=artifact_key,
            artifact=artifact_key,
            file=rel_path,
            derived_from=[project_root_id, *all_object_node_ids],
            project_id=project.metadata.project_id,
        )

    return {
        "tree_version": GOVERNANCE_TREE_VERSION,
        "project_id": project.metadata.project_id,
        "template_id": project.metadata.template,
        "generator_version": GOVERNANCE_GENERATOR_VERSION,
        "root_node_id": project_root_id,
        "project_discovery": closure.discovery.to_dict(),
        "upstream_closure": [item.to_dict() for item in closure.upstream_closure],
        "strict_zone": [item.to_dict() for item in closure.strict_zone],
        "strict_zone_report": strict_zone_report,
        "object_coverage_report": object_coverage_report,
        "evidence_artifacts": dict(closure.evidence_artifacts),
        "structural_objects": [item.to_manifest_dict() for item in closure.structural_objects],
        "role_bindings": [item.to_dict() for item in closure.role_bindings],
        "candidates": [item.to_dict() for item in closure.candidates],
        "nodes": [nodes[node_id] for node_id in sorted(nodes)],
    }


def digest_upstream_ref(ref: UpstreamRef) -> str:
    file_path = REPO_ROOT / ref.file
    if ref.layer == "framework":
        module = parse_framework_module(file_path)
        return _fingerprint(_framework_ref_payload(module, ref))
    if ref.layer in {"product_spec", "implementation_config"}:
        with file_path.open("rb") as fh:
            data = tomllib.load(fh)
        value = _resolve_section(data, ref.ref_id)
        return _fingerprint(value)
    raise ValueError(f"unsupported governance upstream layer: {ref.layer}")


def _framework_ref_payload(module: FrameworkModuleIR, ref: UpstreamRef) -> dict[str, Any]:
    if ref.ref_kind == "rule":
        for rule in module.rules:
            if rule.rule_id == ref.ref_id:
                return rule.to_dict()
        raise KeyError(f"missing framework rule ref {ref.ref_id} in {module.path}")
    raise ValueError(f"unsupported framework ref kind: {ref.ref_kind}")


def _resolve_section(data: dict[str, Any], section_path: str) -> Any:
    current: Any = data
    for part in section_path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(f"missing section path: {section_path}")
        current = current[part]
    return current


def parse_governance_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("governance manifest must decode into object")
    if payload.get("manifest_version") != GOVERNANCE_MANIFEST_VERSION:
        raise ValueError(
            f"unsupported governance manifest version: {payload.get('manifest_version')}"
        )
    if not isinstance(payload.get("upstream_closure"), list):
        raise ValueError("governance manifest missing upstream_closure list")
    if not isinstance(payload.get("structural_objects"), list):
        raise ValueError("governance manifest missing structural_objects list")
    if not isinstance(payload.get("role_bindings"), list):
        raise ValueError("governance manifest missing role_bindings list")
    if not isinstance(payload.get("strict_zone"), list):
        raise ValueError("governance manifest missing strict_zone list")
    if not isinstance(payload.get("strict_zone_report"), dict):
        raise ValueError("governance manifest missing strict_zone_report object")
    if not isinstance(payload.get("candidates"), list):
        raise ValueError("governance manifest missing candidates list")
    if not isinstance(payload.get("object_coverage_report"), dict):
        raise ValueError("governance manifest missing object_coverage_report object")
    return payload


def parse_governance_tree(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("governance tree must decode into object")
    if payload.get("tree_version") != GOVERNANCE_TREE_VERSION:
        raise ValueError(f"unsupported governance tree version: {payload.get('tree_version')}")
    if not isinstance(payload.get("root_node_id"), str) or not payload.get("root_node_id"):
        raise ValueError("governance tree missing root_node_id")
    if not isinstance(payload.get("nodes"), list):
        raise ValueError("governance tree missing nodes list")
    if not isinstance(payload.get("upstream_closure"), list):
        raise ValueError("governance tree missing upstream_closure list")
    if not isinstance(payload.get("project_discovery"), dict):
        raise ValueError("governance tree missing project_discovery object")
    if not isinstance(payload.get("strict_zone"), list):
        raise ValueError("governance tree missing strict_zone list")
    if not isinstance(payload.get("strict_zone_report"), dict):
        raise ValueError("governance tree missing strict_zone_report object")
    if not isinstance(payload.get("structural_objects"), list):
        raise ValueError("governance tree missing structural_objects list")
    if not isinstance(payload.get("role_bindings"), list):
        raise ValueError("governance tree missing role_bindings list")
    if not isinstance(payload.get("candidates"), list):
        raise ValueError("governance tree missing candidates list")
    if not isinstance(payload.get("object_coverage_report"), dict):
        raise ValueError("governance tree missing object_coverage_report object")
    if not isinstance(payload.get("evidence_artifacts"), dict):
        raise ValueError("governance tree missing evidence_artifacts object")
    return payload


def validate_manifest_closure(payload: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for item in payload.get("upstream_closure", []):
        if not isinstance(item, dict):
            continue
        try:
            ref = UpstreamRef(
                layer=str(item["layer"]),
                file=str(item["file"]),
                ref_kind=str(item["ref_kind"]),
                ref_id=str(item["ref_id"]),
            )
        except KeyError as exc:
            issues.append(
                {
                    "code": "STALE_EVIDENCE",
                    "message": f"governance manifest closure entry is invalid: missing {exc}",
                    "file": "",
                    "line": 1,
                }
            )
            continue
        actual_digest = digest_upstream_ref(ref)
        if actual_digest == item.get("digest"):
            continue
        issues.append(
            {
                "code": "STALE_EVIDENCE",
                "message": (
                    "governance manifest is stale; expected evidence no longer matches current upstream closure"
                ),
                "file": ref.file,
                "line": 1,
                "ref": ref.to_manifest_dict(),
            }
        )
    return issues


def _tree_node_index(payload: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    node_index: dict[str, dict[str, Any]] = {}
    for entry in payload.get("nodes", []):
        if not isinstance(entry, dict):
            issues.append(
                {
                    "code": "GOVERNANCE_TREE_INVALID",
                    "message": "governance tree node entry must be an object",
                    "file": "",
                    "line": 1,
                }
            )
            continue
        node_id = str(entry.get("node_id") or "").strip()
        if not node_id:
            issues.append(
                {
                    "code": "GOVERNANCE_TREE_INVALID",
                    "message": "governance tree node entry is missing node_id",
                    "file": "",
                    "line": 1,
                }
            )
            continue
        if node_id in node_index:
            issues.append(
                {
                    "code": "GOVERNANCE_TREE_INVALID",
                    "message": f"duplicate governance tree node entry: {node_id}",
                    "file": "",
                    "line": 1,
                    "node_id": node_id,
                }
            )
            continue
        node_index[node_id] = entry
    return node_index, issues


def validate_tree_closure(payload: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    node_index, node_issues = _tree_node_index(payload)
    issues.extend(node_issues)
    root_node_id = str(payload.get("root_node_id") or "").strip()
    if not root_node_id:
        issues.append(
            {
                "code": "GOVERNANCE_TREE_INVALID",
                "message": "governance tree is missing root_node_id",
                "file": "",
                "line": 1,
            }
        )
    elif root_node_id not in node_index:
        issues.append(
            {
                "code": "GOVERNANCE_TREE_INVALID",
                "message": f"governance tree root node does not exist: {root_node_id}",
                "file": "",
                "line": 1,
                "node_id": root_node_id,
            }
        )
    else:
        if node_index[root_node_id].get("parent") is not None:
            issues.append(
                {
                    "code": "GOVERNANCE_TREE_INVALID",
                    "message": "governance tree root node must not have a parent",
                    "file": "",
                    "line": 1,
                    "node_id": root_node_id,
                }
            )
    for node_id, node in node_index.items():
        children = node.get("children")
        if not isinstance(children, list):
            issues.append(
                {
                    "code": "GOVERNANCE_TREE_INVALID",
                    "message": f"governance tree node must define children list: {node_id}",
                    "file": "",
                    "line": 1,
                    "node_id": node_id,
                }
            )
            children = []
        parent = node.get("parent")
        if parent is not None and parent not in node_index:
            issues.append(
                {
                    "code": "GOVERNANCE_TREE_INVALID",
                    "message": f"governance tree node references missing parent: {node_id} -> {parent}",
                    "file": "",
                    "line": 1,
                    "node_id": node_id,
                }
            )
        for child_id in children:
            if child_id not in node_index:
                issues.append(
                    {
                        "code": "GOVERNANCE_TREE_INVALID",
                        "message": f"governance tree node references missing child: {node_id} -> {child_id}",
                        "file": "",
                        "line": 1,
                        "node_id": node_id,
                    }
                )
                continue
            if node_index[child_id].get("parent") != node_id:
                issues.append(
                    {
                        "code": "GOVERNANCE_TREE_INVALID",
                        "message": (
                            f"governance tree parent/child relationship is inconsistent: "
                            f"{node_id} -> {child_id}"
                        ),
                        "file": "",
                        "line": 1,
                        "node_id": node_id,
                    }
                )
    issues.extend(validate_manifest_closure(payload))
    if not isinstance(payload.get("project_discovery"), dict):
        issues.append(
            {
                "code": "GOVERNANCE_TREE_INVALID",
                "message": "governance tree missing project_discovery object",
                "file": "",
                "line": 1,
            }
        )
    if not isinstance(payload.get("strict_zone"), list):
        issues.append(
            {
                "code": "GOVERNANCE_TREE_INVALID",
                "message": "governance tree missing strict_zone list",
                "file": "",
                "line": 1,
            }
        )
    return issues


def _binding_governance_issues(project: KnowledgeBaseProject) -> list[dict[str, Any]]:
    definitions = _definitions(project)
    binding_index = collect_governed_bindings(governed_files_for_project(project))
    issues = list(_binding_validation_issues(binding_index, definitions))
    for definition in definitions:
        for rel_file, locator in definition.required_bindings:
            if _binding_exists(binding_index, definition.symbol_id, rel_file, locator):
                continue
            issues.append(
                {
                    "code": "MISSING_BINDING",
                    "message": f"required governed binding is missing for {definition.symbol_id}: {rel_file} -> {locator}",
                    "file": rel_file,
                    "line": 1,
                    "symbol_id": definition.symbol_id,
                }
            )
    for item in find_unbound_high_risk_structures():
        issues.append(
            {
                "code": "MISSING_BINDING",
                "message": item["message"],
                "file": item["file"],
                "line": item["line"],
                "locator": item["locator"],
            }
        )
    return issues


def _manifest_object_index(
    payload: dict[str, Any],
    *,
    code: str,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    object_index: dict[str, dict[str, Any]] = {}
    for item in payload.get("structural_objects", []):
        if not isinstance(item, dict):
            issues.append({"code": code, "message": "structural object entry must be an object", "file": "", "line": 1})
            continue
        object_id = str(item.get("object_id") or "").strip()
        if not object_id:
            issues.append({"code": code, "message": "structural object entry is missing object_id", "file": "", "line": 1})
            continue
        if object_id in object_index:
            issues.append(
                {
                    "code": code,
                    "message": f"duplicate structural object entry: {object_id}",
                    "file": "",
                    "line": 1,
                    "object_id": object_id,
                }
            )
            continue
        object_index[object_id] = item
    return object_index, issues


def _role_binding_index(
    payload: dict[str, Any],
    *,
    code: str,
) -> tuple[dict[tuple[str, str], dict[str, Any]], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    binding_index: dict[tuple[str, str], dict[str, Any]] = {}
    for item in payload.get("role_bindings", []):
        if not isinstance(item, dict):
            issues.append({"code": code, "message": "role binding entry must be an object", "file": "", "line": 1})
            continue
        object_id = str(item.get("object_id") or "").strip()
        role_id = str(item.get("role_id") or "").strip()
        if not object_id or not role_id:
            issues.append({"code": code, "message": "role binding entry is missing object_id or role_id", "file": "", "line": 1})
            continue
        key = (object_id, role_id)
        if key in binding_index:
            issues.append(
                {
                    "code": code,
                    "message": f"duplicate role binding entry: {object_id} -> {role_id}",
                    "file": "",
                    "line": 1,
                    "object_id": object_id,
                    "role_id": role_id,
                }
            )
            continue
        binding_index[key] = item
    return binding_index, issues


def _candidate_index(
    payload: dict[str, Any],
    *,
    code: str,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    candidate_index: dict[str, dict[str, Any]] = {}
    for item in payload.get("candidates", []):
        if not isinstance(item, dict):
            issues.append({"code": code, "message": "candidate entry must be an object", "file": "", "line": 1})
            continue
        candidate_id = str(item.get("candidate_id") or "").strip()
        if not candidate_id:
            issues.append({"code": code, "message": "candidate entry is missing candidate_id", "file": "", "line": 1})
            continue
        if candidate_id in candidate_index:
            issues.append(
                {
                    "code": code,
                    "message": f"duplicate candidate entry: {candidate_id}",
                    "file": "",
                    "line": 1,
                    "candidate_id": candidate_id,
                }
            )
            continue
        candidate_index[candidate_id] = item
    return candidate_index, issues


def _strict_zone_index(
    payload: dict[str, Any],
    *,
    code: str,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    strict_zone_index: dict[str, dict[str, Any]] = {}
    for item in payload.get("strict_zone", []):
        if not isinstance(item, dict):
            issues.append({"code": code, "message": "strict zone entry must be an object", "file": "", "line": 1})
            continue
        file_name = str(item.get("file") or "").strip()
        if not file_name:
            issues.append({"code": code, "message": "strict zone entry is missing file", "file": "", "line": 1})
            continue
        if file_name in strict_zone_index:
            issues.append(
                {
                    "code": code,
                    "message": f"duplicate strict zone entry: {file_name}",
                    "file": "",
                    "line": 1,
                }
            )
            continue
        strict_zone_index[file_name] = item
    return strict_zone_index, issues


def _compare_payload_to_closure(
    project: KnowledgeBaseProject,
    payload: dict[str, Any],
    *,
    tree_mode: bool,
) -> list[dict[str, Any]]:
    binding_issues = _binding_governance_issues(project)
    if binding_issues:
        return binding_issues
    try:
        closure = build_governance_closure(project)
    except Exception as exc:
        return [
            {
                "code": "GOVERNANCE_PROJECT_INVALID",
                "message": str(exc),
                "file": _relative(project.product_spec_file),
                "line": 1,
            }
        ]
    issues: list[dict[str, Any]] = []
    payload_code = "GOVERNANCE_TREE_INVALID" if tree_mode else "GOVERNANCE_MANIFEST_INVALID"
    strict_zone_report = build_strict_zone_report(closure)
    object_coverage_report = build_object_coverage_report(closure)

    object_index, object_issues = _manifest_object_index(payload, code=payload_code)
    issues.extend(object_issues)
    binding_index, binding_issues = _role_binding_index(payload, code=payload_code)
    issues.extend(binding_issues)
    candidate_index, candidate_issues = _candidate_index(payload, code=payload_code)
    issues.extend(candidate_issues)
    strict_zone_index, strict_zone_issues = _strict_zone_index(payload, code=payload_code)
    issues.extend(strict_zone_issues)

    expected_artifacts = closure.evidence_artifacts
    payload_artifacts = payload.get("evidence_artifacts", {})
    if not isinstance(payload_artifacts, dict):
        issues.append(
            {
                "code": payload_code,
                "message": "evidence_artifacts payload must be an object",
                "file": "",
                "line": 1,
            }
        )
        payload_artifacts = {}

    for artifact_key, rel_path in expected_artifacts.items():
        if payload_artifacts.get(artifact_key) != rel_path:
            issues.append(
                {
                    "code": payload_code,
                    "message": f"evidence artifact path drifted for {artifact_key}",
                    "file": "",
                    "line": 1,
                    "artifact": artifact_key,
                    "expected": rel_path,
                    "actual": payload_artifacts.get(artifact_key),
                }
            )

    for report_key, expected_report in (
        ("strict_zone_report", strict_zone_report),
        ("object_coverage_report", object_coverage_report),
    ):
        payload_report = payload.get(report_key)
        if _canonical_json(payload_report) != _canonical_json(expected_report):
            issues.append(
                {
                    "code": payload_code,
                    "message": f"{report_key} drifted from current governance closure",
                    "file": "",
                    "line": 1,
                    "report": report_key,
                }
            )

    for object_id in sorted(set(object_index) - {item.object_id for item in closure.structural_objects}):
        issues.append(
            {
                "code": payload_code,
                "message": f"unknown structural object in governance payload: {object_id}",
                "file": "",
                "line": 1,
                "object_id": object_id,
            }
        )

    for structural_object in closure.structural_objects:
        payload_object = object_index.get(structural_object.object_id)
        if payload_object is None:
            issues.append(
                {
                    "code": payload_code,
                    "message": f"governance payload is missing structural object: {structural_object.object_id}",
                    "file": "",
                    "line": 1,
                    "object_id": structural_object.object_id,
                    "symbol_id": structural_object.object_id,
                }
            )
            continue
        if payload_object.get("expected_fingerprint") != structural_object.expected_fingerprint:
            issues.append(
                {
                    "code": payload_code,
                    "message": f"structural object expectation drifted: {structural_object.object_id}",
                    "file": "",
                    "line": 1,
                    "object_id": structural_object.object_id,
                    "symbol_id": structural_object.object_id,
                }
            )
        if structural_object.actual_fingerprint != structural_object.expected_fingerprint:
            mismatch_code = (
                "DEAD_CONFIG_EFFECT"
                if structural_object.kind == "implementation_effect"
                else "EXPECTATION_MISMATCH"
            )
            issues.append(
                {
                    "code": mismatch_code,
                    "message": f"structural object no longer matches derived expectation: {structural_object.object_id}",
                    "file": next(
                        (role.file_hints[0] for role in structural_object.required_roles if role.file_hints),
                        closure.product_spec_file,
                    ),
                    "line": 1,
                    "object_id": structural_object.object_id,
                    "symbol_id": structural_object.object_id,
                    "kind": structural_object.kind,
                    "expected": structural_object.expected_evidence,
                    "actual": structural_object.actual_evidence,
                }
            )
        for role in structural_object.required_roles:
            binding = binding_index.get((structural_object.object_id, role.role_id))
            if binding is None:
                issues.append(
                    {
                        "code": payload_code,
                        "message": f"missing role binding entry: {structural_object.object_id} -> {role.role_id}",
                        "file": "",
                        "line": 1,
                        "object_id": structural_object.object_id,
                        "role_id": role.role_id,
                    }
                )
                continue
            if binding.get("status") != "satisfied":
                issues.append(
                    {
                        "code": "ROLE_CLOSURE_MISSING",
                        "message": f"required role is not satisfied: {structural_object.object_id} -> {role.role_id}",
                        "file": next(iter(binding.get("file_refs", [])), closure.product_spec_file),
                        "line": 1,
                        "object_id": structural_object.object_id,
                        "role_id": role.role_id,
                    }
                )

    for strict_entry in closure.strict_zone:
        payload_entry = strict_zone_index.get(strict_entry.file)
        if payload_entry is None:
            issues.append(
                {
                    "code": payload_code,
                    "message": f"missing strict zone entry: {strict_entry.file}",
                    "file": strict_entry.file,
                    "line": 1,
                }
            )
            continue
        if sorted(payload_entry.get("object_ids", [])) != list(strict_entry.object_ids):
            issues.append(
                {
                    "code": payload_code,
                    "message": f"strict zone object closure drifted for {strict_entry.file}",
                    "file": strict_entry.file,
                    "line": 1,
                }
            )
        if payload_entry.get("minimality_status") != strict_entry.minimality_status:
            issues.append(
                {
                    "code": payload_code,
                    "message": f"strict zone minimality drifted for {strict_entry.file}",
                    "file": strict_entry.file,
                    "line": 1,
                }
            )
        if strict_entry.minimality_status == "redundant":
            issues.append(
                {
                    "code": "STRICT_ZONE_REDUNDANT",
                    "message": f"strict zone contains redundant carrier: {strict_entry.file}",
                    "file": strict_entry.file,
                    "line": 1,
                }
            )

    for candidate in closure.candidates:
        payload_candidate = candidate_index.get(candidate.candidate_id)
        if payload_candidate is None:
            issues.append(
                {
                    "code": payload_code,
                    "message": f"missing structural candidate entry: {candidate.candidate_id}",
                    "file": candidate.file,
                    "line": 1,
                    "candidate_id": candidate.candidate_id,
                }
            )
            continue
        if payload_candidate.get("classification") not in {"governed", "attached", "internal"}:
            issues.append(
                {
                    "code": "CANDIDATE_CLASSIFICATION_INVALID",
                    "message": f"candidate classification is invalid: {candidate.candidate_id}",
                    "file": candidate.file,
                    "line": 1,
                    "candidate_id": candidate.candidate_id,
                }
            )
            continue
        if payload_candidate.get("classification") != candidate.classification:
            issues.append(
                {
                    "code": "CANDIDATE_CLASSIFICATION_INVALID",
                    "message": f"candidate classification drifted: {candidate.candidate_id}",
                    "file": candidate.file,
                    "line": 1,
                    "candidate_id": candidate.candidate_id,
                    "expected": candidate.classification,
                    "actual": payload_candidate.get("classification"),
                }
            )
        if (
            candidate.classification == "internal"
            and candidate.kind in {"python_route_handler", "python_route_builder", "python_behavior_orchestrator"}
        ):
            issues.append(
                {
                    "code": "MISSING_BINDING",
                    "message": f"high-risk structural candidate is not governed or attached: {candidate.candidate_id}",
                    "file": candidate.file,
                    "line": 1,
                    "candidate_id": candidate.candidate_id,
                }
            )

    if tree_mode:
        node_index, node_issues = _tree_node_index(payload)
        issues.extend(node_issues)
        for structural_object in closure.structural_objects:
            object_node_id = f"project:{project.metadata.project_id}:structure:object:{structural_object.object_id}"
            if object_node_id not in node_index:
                issues.append(
                    {
                        "code": "GOVERNANCE_TREE_INVALID",
                        "message": f"governance tree is missing structural object node: {structural_object.object_id}",
                        "file": "",
                        "line": 1,
                        "object_id": structural_object.object_id,
                    }
                )
        for strict_entry in closure.strict_zone:
            file_node_id = f"project:{project.metadata.project_id}:code:file:{strict_entry.file}"
            if file_node_id not in node_index:
                issues.append(
                    {
                        "code": "GOVERNANCE_TREE_INVALID",
                        "message": f"governance tree is missing strict zone file node: {strict_entry.file}",
                        "file": strict_entry.file,
                        "line": 1,
                    }
                )
        for artifact_key in expected_artifacts:
            node_id = f"project:{project.metadata.project_id}:evidence:artifact:{artifact_key}"
            if node_id not in node_index:
                issues.append(
                    {
                        "code": "GOVERNANCE_TREE_INVALID",
                        "message": f"governance tree is missing evidence artifact node: {artifact_key}",
                        "file": "",
                        "line": 1,
                        "artifact": artifact_key,
                    }
                )
    return issues


def compare_project_to_manifest(project: KnowledgeBaseProject, payload: dict[str, Any]) -> list[dict[str, Any]]:
    return _compare_payload_to_closure(project, payload, tree_mode=False)


def compare_project_to_tree(project: KnowledgeBaseProject, payload: dict[str, Any]) -> list[dict[str, Any]]:
    return _compare_payload_to_closure(project, payload, tree_mode=True)


def _binding_exists(
    binding_index: dict[str, list[GovernedBinding]],
    symbol_id: str,
    rel_file: str,
    locator: str,
) -> bool:
    for item in binding_index.get(symbol_id, []):
        if item.file == rel_file and item.locator == locator:
            return True
    return False
