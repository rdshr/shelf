from __future__ import annotations

from dataclasses import dataclass, field
import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import tomllib
from typing import TYPE_CHECKING, Any, Callable, get_args, get_origin, get_type_hints

from fastapi.routing import APIRoute
from framework_ir import FrameworkModule, parse_framework_module
from project_runtime.project_config_source import (
    ProjectConfigLoadError,
    load_product_spec_document,
)
from project_runtime.project_governance import (
    FrameworkDrivenProjectRecord,
    ProjectGovernanceClosure,
    RequiredRole,
    ResolvedRoleBinding,
    SourceRef,
    StructuralObject,
    StructuralCandidate,
    StrictZoneEntry,
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
    from project_runtime.knowledge_base import ImplementationEffectEntry, KnowledgeBaseProject


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


@dataclass(frozen=True)
class GeneratedArtifactPaths:
    canonical_graph_json: str
    framework_ir_json: str
    product_spec_json: str
    implementation_bundle_py: str
    generation_manifest_json: str
    governance_manifest_json: str
    governance_tree_json: str
    strict_zone_report_json: str
    object_coverage_report_json: str

    def items(self) -> tuple[tuple[str, str], ...]:
        return tuple(self.to_dict().items())

    def to_dict(self) -> dict[str, str]:
        return {
            "canonical_graph_json": self.canonical_graph_json,
            "framework_ir_json": self.framework_ir_json,
            "product_spec_json": self.product_spec_json,
            "implementation_bundle_py": self.implementation_bundle_py,
            "generation_manifest_json": self.generation_manifest_json,
            "governance_manifest_json": self.governance_manifest_json,
            "governance_tree_json": self.governance_tree_json,
            "strict_zone_report_json": self.strict_zone_report_json,
            "object_coverage_report_json": self.object_coverage_report_json,
        }


@dataclass(frozen=True)
class GovernanceSnapshotSymbol:
    symbol_id: str
    owner: str
    kind: str
    risk: str
    bindings: tuple[dict[str, Any], ...]
    upstream_refs: tuple[dict[str, Any], ...]
    extractor: str
    comparator: str
    fingerprint: str
    evidence: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol_id": self.symbol_id,
            "owner": self.owner,
            "kind": self.kind,
            "risk": self.risk,
            "bindings": list(self.bindings),
            "upstream_refs": list(self.upstream_refs),
            "expected": {
                "extractor": self.extractor,
                "comparator": self.comparator,
                "fingerprint": self.fingerprint,
                "evidence": self.evidence,
            },
        }


@dataclass(frozen=True)
class GovernanceTreeRoots:
    project_root_id: str
    framework_root_id: str
    product_root_id: str
    implementation_root_id: str
    structure_root_id: str
    code_root_id: str
    evidence_root_id: str

    @classmethod
    def for_project(cls, project_id: str) -> "GovernanceTreeRoots":
        project_root_id = f"project:{project_id}"
        return cls(
            project_root_id=project_root_id,
            framework_root_id=f"{project_root_id}:framework",
            product_root_id=f"{project_root_id}:product_spec",
            implementation_root_id=f"{project_root_id}:implementation_config",
            structure_root_id=f"{project_root_id}:structure",
            code_root_id=f"{project_root_id}:code",
            evidence_root_id=f"{project_root_id}:evidence",
        )


@dataclass
class GovernanceTreeNodeRecord:
    node_id: str
    parent: str | None
    children: list[str] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "parent": self.parent,
            "children": list(self.children),
            **self.payload,
        }


@dataclass
class GovernanceTreeBuilder:
    project_id: str
    roots: GovernanceTreeRoots
    nodes: dict[str, GovernanceTreeNodeRecord] = field(default_factory=dict)
    source_node_ids: dict[tuple[str, str, str, str], str] = field(default_factory=dict)
    role_node_ids: dict[tuple[str, str], str] = field(default_factory=dict)
    framework_modules: dict[str, FrameworkModule] = field(default_factory=dict)

    def add_node(self, node_id: str, *, parent: str | None, **payload: Any) -> GovernanceTreeNodeRecord:
        existing = self.nodes.get(node_id)
        if existing is None:
            existing = GovernanceTreeNodeRecord(
                node_id=node_id,
                parent=parent,
                payload=dict(payload),
            )
            self.nodes[node_id] = existing
        if parent is not None and parent in self.nodes and node_id not in self.nodes[parent].children:
            self.nodes[parent].children.append(node_id)
        return existing

    def add_root_nodes(self, project: KnowledgeBaseProject) -> None:
        self.add_node(
            self.roots.project_root_id,
            parent=None,
            kind="project_root",
            layer="Project",
            title=project.metadata.display_name,
            file=_relative(project.product_spec_file),
            template_id=project.metadata.template,
            project_id=project.metadata.project_id,
        )
        self.add_node(
            self.roots.framework_root_id,
            parent=self.roots.project_root_id,
            kind="framework_root",
            layer="Framework",
            title="Framework",
        )
        self.add_node(
            self.roots.product_root_id,
            parent=self.roots.project_root_id,
            kind="product_root",
            layer="Product Spec",
            title="Product Spec",
        )
        self.add_node(
            self.roots.implementation_root_id,
            parent=self.roots.project_root_id,
            kind="implementation_root",
            layer="Implementation Config",
            title="Implementation Config",
        )
        self.add_node(
            self.roots.structure_root_id,
            parent=self.roots.project_root_id,
            kind="structure_root",
            layer="Project Structure",
            title="Project Structure",
        )
        self.add_node(
            self.roots.code_root_id,
            parent=self.roots.project_root_id,
            kind="code_root",
            layer="Code",
            title="Code",
        )
        self.add_node(
            self.roots.evidence_root_id,
            parent=self.roots.project_root_id,
            kind="evidence_root",
            layer="Evidence",
            title="Evidence",
        )

    def add_source_ref(self, source: SourceRef) -> None:
        if source.layer == "framework":
            module = self.framework_modules.get(source.file)
            if module is None:
                module = parse_framework_module(REPO_ROOT / source.file)
                self.framework_modules[source.file] = module
            module_node_id = f"{self.roots.framework_root_id}:module:{module.module_id}"
            self.add_node(
                module_node_id,
                parent=self.roots.framework_root_id,
                kind="framework_module",
                layer="Framework",
                title=module.module_id,
                file=source.file,
                project_id=self.project_id,
            )
            node_id = f"{module_node_id}:rule:{source.ref_id}"
            self.add_node(
                node_id,
                parent=module_node_id,
                kind="framework_rule",
                layer="Framework",
                title=source.ref_id,
                file=source.file,
                ref_kind=source.ref_kind,
                ref_id=source.ref_id,
                digest=source.digest,
                project_id=self.project_id,
            )
            self.source_node_ids[source.key()] = node_id
            return

        if source.layer == "product_spec":
            root_id = self.roots.product_root_id
            file_kind = "product_file"
            section_kind = "product_section"
            layer = "Product Spec"
        elif source.layer == "implementation_config":
            root_id = self.roots.implementation_root_id
            file_kind = "implementation_file"
            section_kind = "implementation_section"
            layer = "Implementation Config"
        else:
            return

        file_node_id = f"{root_id}:file:{source.file}"
        self.add_node(
            file_node_id,
            parent=root_id,
            kind=file_kind,
            layer=layer,
            title=Path(source.file).name,
            file=source.file,
            project_id=self.project_id,
        )
        node_id = f"{file_node_id}:section:{source.ref_id}"
        self.add_node(
            node_id,
            parent=file_node_id,
            kind=section_kind,
            layer=layer,
            title=source.ref_id,
            file=source.file,
            ref_kind=source.ref_kind,
            ref_id=source.ref_id,
            digest=source.digest,
            project_id=self.project_id,
        )
        self.source_node_ids[source.key()] = node_id

    def add_structural_object(self, structural_object: StructuralObject) -> None:
        object_node_id = f"{self.roots.structure_root_id}:object:{structural_object.object_id}"
        upstream_ids = [
            self.source_node_ids[source.key()]
            for source in structural_object.all_sources()
            if source.key() in self.source_node_ids
        ]
        self.add_node(
            object_node_id,
            parent=self.roots.structure_root_id,
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
            project_id=self.project_id,
        )
        for role in structural_object.required_roles:
            role_node_id = f"{object_node_id}:role:{role.role_id}"
            self.add_node(
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
                project_id=self.project_id,
            )
            self.role_node_ids[(structural_object.object_id, role.role_id)] = role_node_id

    def add_strict_zone_entry(self, strict_entry: Any) -> None:
        file_node_id = f"{self.roots.code_root_id}:file:{strict_entry.file}"
        derived_from = [
            self.role_node_ids[(object_id, role_id)]
            for object_id in strict_entry.object_ids
            for role_id in strict_entry.role_ids
            if (object_id, role_id) in self.role_node_ids
        ]
        if not derived_from:
            derived_from = [
                f"{self.roots.structure_root_id}:object:{object_id}"
                for object_id in strict_entry.object_ids
            ]
        self.add_node(
            file_node_id,
            parent=self.roots.code_root_id,
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
            project_id=self.project_id,
        )

    def add_candidate(self, candidate: StructuralCandidate) -> None:
        file_node_id = f"{self.roots.code_root_id}:file:{candidate.file}"
        if file_node_id not in self.nodes:
            self.add_node(
                file_node_id,
                parent=self.roots.code_root_id,
                kind="strict_zone_file",
                layer="Code",
                title=Path(candidate.file).name,
                file=candidate.file,
                object_ids=[],
                role_ids=[],
                reasons=["candidate-only strict zone carrier"],
                derived_from=[],
                project_id=self.project_id,
            )
        derived_from = [
            self.role_node_ids[(candidate.object_id, role_id)]
            for role_id in candidate.role_ids
            if candidate.object_id is not None and (candidate.object_id, role_id) in self.role_node_ids
        ]
        if not derived_from and candidate.object_id is not None:
            derived_from = [f"{self.roots.structure_root_id}:object:{candidate.object_id}"]
        self.add_node(
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
            project_id=self.project_id,
        )

    def add_evidence_artifacts(self, closure: ProjectGovernanceClosure) -> None:
        all_object_node_ids = [
            f"{self.roots.structure_root_id}:object:{item.object_id}" for item in closure.structural_objects
        ]
        for artifact_key, rel_path in closure.evidence_artifacts.items():
            self.add_node(
                f"{self.roots.evidence_root_id}:artifact:{artifact_key}",
                parent=self.roots.evidence_root_id,
                kind="evidence_artifact",
                layer="Evidence",
                title=artifact_key,
                artifact=artifact_key,
                file=rel_path,
                derived_from=[self.roots.project_root_id, *all_object_node_ids],
                project_id=self.project_id,
            )

    def serialized_nodes(self) -> list[dict[str, Any]]:
        return [self.nodes[node_id].to_dict() for node_id in sorted(self.nodes)]


@dataclass(frozen=True)
class GovernancePayloadIndexes:
    object_index: dict[str, dict[str, Any]]
    binding_index: dict[tuple[str, str], dict[str, Any]]
    candidate_index: dict[str, dict[str, Any]]
    strict_zone_index: dict[str, dict[str, Any]]


@dataclass(frozen=True)
class GovernanceComparisonContext:
    project: KnowledgeBaseProject
    closure: ProjectGovernanceClosure
    payload: dict[str, Any]
    payload_code: str
    tree_mode: bool
    strict_zone_report: dict[str, Any]
    object_coverage_report: dict[str, Any]
    indexes: GovernancePayloadIndexes


@dataclass(frozen=True)
class GovernanceProjectArtifactsContext:
    project: KnowledgeBaseProject
    closure: ProjectGovernanceClosure
    strict_zone_report: dict[str, Any]
    object_coverage_report: dict[str, Any]
    binding_index: dict[str, list[GovernedBinding]]

    @classmethod
    def from_project(cls, project: KnowledgeBaseProject) -> "GovernanceProjectArtifactsContext":
        closure = build_governance_closure(project)
        return cls(
            project=project,
            closure=closure,
            strict_zone_report=build_strict_zone_report(closure),
            object_coverage_report=build_object_coverage_report(closure),
            binding_index=_binding_index_for_project(project),
        )


@dataclass(frozen=True)
class GovernanceDefinitionsContext:
    project: KnowledgeBaseProject
    definitions: tuple[SymbolDefinition, ...]
    bindings_by_symbol: dict[str, list[GovernedBinding]]
    unbound_high_risk: tuple[dict[str, Any], ...]

    def sorted_bindings_for(self, symbol_id: str) -> tuple[GovernedBinding, ...]:
        return tuple(
            sorted(
                self.bindings_by_symbol.get(symbol_id, []),
                key=lambda item: (item.file, item.line, item.locator),
            )
        )

    def missing_bindings_for(self, definition: SymbolDefinition) -> tuple[str, ...]:
        return tuple(
            f"{rel_file} -> {locator}"
            for rel_file, locator in definition.required_bindings
            if not _binding_exists(self.bindings_by_symbol, definition.symbol_id, rel_file, locator)
        )


@dataclass(frozen=True)
class GovernanceStructuralContext:
    structural_objects: tuple[StructuralObject, ...]
    expected_artifacts: dict[str, str]
    discovery: FrameworkDrivenProjectRecord
    upstream_closure: tuple[SourceRef, ...]


@dataclass(frozen=True)
class GovernanceResolutionContext:
    role_bindings: tuple[ResolvedRoleBinding, ...]
    candidates: tuple[StructuralCandidate, ...]
    strict_zone: tuple[StrictZoneEntry, ...]


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


def _build_governance_definitions_context(project: KnowledgeBaseProject) -> GovernanceDefinitionsContext:
    return GovernanceDefinitionsContext(
        project=project,
        definitions=tuple(_definitions(project)),
        bindings_by_symbol=collect_governed_bindings(governed_files_for_project(project)),
        unbound_high_risk=tuple(find_unbound_high_risk_structures()),
    )


def _raise_binding_validation_issues(binding_issues: list[dict[str, Any]]) -> None:
    if not binding_issues:
        return
    details = "; ".join(
        f"{item['file']}:{item['line']} {item['code']} {item['message']}" for item in binding_issues
    )
    raise ValueError(f"invalid governed bindings: {details}")


def _raise_unbound_high_risk_issues(unbound_high_risk: tuple[dict[str, Any], ...]) -> None:
    if not unbound_high_risk:
        return
    details = "; ".join(f"{item['file']}:{item['line']} -> {item['locator']}" for item in unbound_high_risk)
    raise ValueError(f"missing governed_symbol binding for high-risk structures: {details}")


def _raise_missing_required_bindings(
    definition: SymbolDefinition,
    missing_bindings: tuple[str, ...],
) -> None:
    if not missing_bindings:
        return
    raise ValueError(
        f"missing governed_symbol binding(s) for {definition.symbol_id}: {', '.join(missing_bindings)}"
    )


def _validated_governance_definitions_context(project: KnowledgeBaseProject) -> GovernanceDefinitionsContext:
    context = _build_governance_definitions_context(project)
    _raise_binding_validation_issues(_binding_validation_issues(context.bindings_by_symbol, context.definitions))
    _raise_unbound_high_risk_issues(context.unbound_high_risk)
    for definition in context.definitions:
        _raise_missing_required_bindings(definition, context.missing_bindings_for(definition))
    return context


def _expected_generated_artifact_paths(project: KnowledgeBaseProject) -> GeneratedArtifactPaths:
    if project.generated_artifacts is not None:
        return GeneratedArtifactPaths(
            canonical_graph_json=project.generated_artifacts.canonical_graph_json,
            framework_ir_json=project.generated_artifacts.framework_ir_json,
            product_spec_json=project.generated_artifacts.product_spec_json,
            implementation_bundle_py=project.generated_artifacts.implementation_bundle_py,
            generation_manifest_json=project.generated_artifacts.generation_manifest_json,
            governance_manifest_json=project.generated_artifacts.governance_manifest_json,
            governance_tree_json=project.generated_artifacts.governance_tree_json,
            strict_zone_report_json=project.generated_artifacts.strict_zone_report_json,
            object_coverage_report_json=project.generated_artifacts.object_coverage_report_json,
        )

    generated_dir = Path(project.product_spec_file).parent / "generated"
    artifact_names = project.implementation.artifacts
    return GeneratedArtifactPaths(
        canonical_graph_json=_relative(generated_dir / artifact_names.canonical_graph_json),
        framework_ir_json=_relative(generated_dir / artifact_names.framework_ir_json),
        product_spec_json=_relative(generated_dir / artifact_names.product_spec_json),
        implementation_bundle_py=_relative(generated_dir / artifact_names.implementation_bundle_py),
        generation_manifest_json=_relative(generated_dir / artifact_names.generation_manifest_json),
        governance_manifest_json=_relative(generated_dir / artifact_names.governance_manifest_json),
        governance_tree_json=_relative(generated_dir / artifact_names.governance_tree_json),
        strict_zone_report_json=_relative(generated_dir / artifact_names.strict_zone_report_json),
        object_coverage_report_json=_relative(generated_dir / artifact_names.object_coverage_report_json),
    )


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


def _framework_rule_refs(module: FrameworkModule, rule_ids: tuple[str, ...] | None = None) -> tuple[UpstreamRef, ...]:
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
    product_spec_path = REPO_ROOT / product_spec_file
    try:
        document = load_product_spec_document(product_spec_path)
    except ProjectConfigLoadError:
        document = None
    refs: list[UpstreamRef] = []
    for section in sections:
        source_file = (
            relative_path(document.source_file_for_section(section))
            if document is not None
            else product_spec_file
        )
        refs.append(
            UpstreamRef(
                layer="product_spec",
                file=source_file,
                ref_kind="section",
                ref_id=section,
            )
        )
    return tuple(refs)


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

    app = build_knowledge_base_runtime_app(project.code_module)
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

    router = build_knowledge_base_router(project.code_module, KnowledgeRepository(project.code_module))
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

    repository = KnowledgeRepository(project.code_module)
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
    effect_entry: ImplementationEffectEntry,
) -> StructuralObject:
    relation = effect_entry.relation or "equals"
    configured_value = effect_entry.value
    targets = tuple(target_path for target_path in effect_entry.targets if target_path.strip())
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
        runtime_bundle["generated_artifacts"] = _expected_generated_artifact_paths(project).to_dict()
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


def _project_record_for(project: KnowledgeBaseProject) -> FrameworkDrivenProjectRecord:
    rel_product_spec = _relative(project.product_spec_file)
    for item in discover_framework_driven_projects():
        if item.product_spec_file == rel_product_spec:
            return item
    artifact_names = project.implementation.artifacts
    return FrameworkDrivenProjectRecord(
        project_id=project.metadata.project_id,
        template_id=project.metadata.template,
        product_spec_file=rel_product_spec,
        implementation_config_file=_relative(project.implementation_config_file),
        generated_dir=_relative(Path(project.product_spec_file).parent / "generated"),
        discovery_reasons=(
            "project spec exists under projects/<project_id>/product_spec.toml",
            "implementation_config.toml exists beside product_spec.toml",
            "registered template resolved through project.template",
            "project loads through the registered framework-driven materialization chain",
        ),
        framework_refs=tuple(
            item
            for item in (
                project.framework.frontend,
                project.framework.domain,
                project.framework.backend,
            )
            if isinstance(item, str) and item.strip()
        ),
        artifact_contract=tuple(
            getattr(artifact_names, field_name)
            for field_name in (
                "canonical_graph_json",
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
    )


def _implementation_effect_objects(project: KnowledgeBaseProject) -> tuple[StructuralObject, ...]:
    from project_runtime.knowledge_base import build_implementation_effect_manifest

    return tuple(
        _config_effect_object(project, field_path, effect_entry)
        for field_path, effect_entry in sorted(build_implementation_effect_manifest(project).items())
    )


def _upstream_closure_from_structural_objects(
    structural_objects: tuple[StructuralObject, ...],
) -> tuple[SourceRef, ...]:
    upstream_index: dict[tuple[str, str, str, str], SourceRef] = {}
    for structural_object in structural_objects:
        for source in structural_object.all_sources():
            upstream_index[source.key()] = source
    return tuple(
        sorted(upstream_index.values(), key=lambda item: (item.layer, item.file, item.ref_kind, item.ref_id))
    )


def _build_governance_structural_context(
    project: KnowledgeBaseProject,
    definitions_context: GovernanceDefinitionsContext,
) -> GovernanceStructuralContext:
    structural_objects = tuple(
        [
            *(
                _structural_object_from_definition(project, definition)
                for definition in definitions_context.definitions
            ),
            *_implementation_effect_objects(project),
        ]
    )
    return GovernanceStructuralContext(
        structural_objects=tuple(sorted(structural_objects, key=lambda item: item.object_id)),
        expected_artifacts=_expected_generated_artifact_paths(project).to_dict(),
        discovery=_project_record_for(project),
        upstream_closure=_upstream_closure_from_structural_objects(structural_objects),
    )


def _resolve_governance_candidates(
    project: KnowledgeBaseProject,
    structural_context: GovernanceStructuralContext,
) -> GovernanceResolutionContext:
    structural_objects = structural_context.structural_objects
    expected_artifacts = structural_context.expected_artifacts
    raw_candidates = scan_python_structural_candidates(project_id=project.metadata.project_id)
    seed_bindings = resolve_role_bindings(structural_objects, raw_candidates)
    seed_candidates = classify_candidates(structural_objects, raw_candidates, seed_bindings)
    seed_strict_zone = infer_strict_zone(
        structural_objects,
        seed_bindings,
        seed_candidates,
        expected_artifacts,
    )
    strict_files = {entry.file for entry in seed_strict_zone}
    seed_candidate_ids = {candidate_id for binding in seed_bindings for candidate_id in binding.candidate_ids}
    project_candidates = tuple(
        candidate
        for candidate in raw_candidates
        if candidate.file in strict_files
        and (candidate.confidence >= 0.75 or candidate.candidate_id in seed_candidate_ids)
    )
    role_bindings = tuple(resolve_role_bindings(structural_objects, project_candidates))
    candidates = tuple(classify_candidates(structural_objects, project_candidates, role_bindings))
    strict_zone = tuple(
        annotate_strict_zone_minimality(
            infer_strict_zone(
                structural_objects,
                role_bindings,
                candidates,
                expected_artifacts,
            ),
            role_bindings,
            candidates,
            expected_artifacts,
        )
    )
    return GovernanceResolutionContext(
        role_bindings=tuple(sorted(role_bindings, key=lambda item: (item.object_id, item.role_id))),
        candidates=tuple(sorted(candidates, key=lambda item: (item.file, item.locator, item.kind))),
        strict_zone=tuple(sorted(strict_zone, key=lambda item: item.file)),
    )


def build_governance_closure(project: KnowledgeBaseProject) -> ProjectGovernanceClosure:
    definitions_context = _validated_governance_definitions_context(project)
    structural_context = _build_governance_structural_context(project, definitions_context)
    resolution_context = _resolve_governance_candidates(project, structural_context)
    return ProjectGovernanceClosure(
        project_id=project.metadata.project_id,
        template_id=project.metadata.template,
        product_spec_file=_relative(project.product_spec_file),
        implementation_config_file=_relative(project.implementation_config_file),
        discovery=structural_context.discovery,
        structural_objects=structural_context.structural_objects,
        candidates=resolution_context.candidates,
        role_bindings=resolution_context.role_bindings,
        strict_zone=resolution_context.strict_zone,
        upstream_closure=structural_context.upstream_closure,
        evidence_artifacts=structural_context.expected_artifacts,
    )


def _build_governance_snapshot(project: KnowledgeBaseProject) -> dict[str, Any]:
    context = _validated_governance_definitions_context(project)
    upstream_closure: dict[tuple[str, str, str, str], str] = {}
    symbols = [
        _snapshot_symbol_from_definition(project, context, definition, upstream_closure)
        for definition in context.definitions
    ]
    return {
        "definitions": list(context.definitions),
        "symbols": [item.to_dict() for item in symbols],
        "upstream_closure": _upstream_closure_items(upstream_closure),
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


def _manifest_binding_entries(bindings: tuple[GovernedBinding, ...]) -> tuple[dict[str, Any], ...]:
    return tuple(item.to_manifest_dict() for item in bindings)


def _upstream_closure_items(
    upstream_closure: dict[tuple[str, str, str, str], str],
) -> list[dict[str, Any]]:
    return [
        {
            "layer": layer,
            "file": file_name,
            "ref_kind": ref_kind,
            "ref_id": ref_id,
            "digest": digest,
        }
        for (layer, file_name, ref_kind, ref_id), digest in sorted(upstream_closure.items())
    ]


def _snapshot_symbol_from_definition(
    project: KnowledgeBaseProject,
    context: GovernanceDefinitionsContext,
    definition: SymbolDefinition,
    upstream_closure: dict[tuple[str, str, str, str], str],
) -> GovernanceSnapshotSymbol:
    bindings = context.sorted_bindings_for(definition.symbol_id)
    expected_evidence = definition.expected_builder(project)
    upstream_refs = definition.upstream_ref_builder(project)
    for ref in upstream_refs:
        upstream_closure[ref.key()] = digest_upstream_ref(ref)
    return GovernanceSnapshotSymbol(
        symbol_id=definition.symbol_id,
        owner=definition.owner,
        kind=definition.kind,
        risk=definition.risk,
        bindings=_manifest_binding_entries(bindings),
        upstream_refs=tuple(
            ref.to_manifest_dict(digest=upstream_closure[ref.key()])
            for ref in upstream_refs
        ),
        extractor=definition.extractor,
        comparator=definition.comparator,
        fingerprint=_fingerprint(expected_evidence),
        evidence=expected_evidence,
    )


def _snapshot_symbol_from_structural_object(
    structural_object: StructuralObject,
    binding_index: dict[str, list[GovernedBinding]],
) -> GovernanceSnapshotSymbol:
    bindings = tuple(
        sorted(
            binding_index.get(structural_object.object_id, []),
            key=lambda entry: (entry.file, entry.line, entry.locator),
        )
    )
    return GovernanceSnapshotSymbol(
        symbol_id=structural_object.object_id,
        owner=_object_owner(structural_object),
        kind=structural_object.kind,
        risk=structural_object.risk_level,
        bindings=_manifest_binding_entries(bindings),
        upstream_refs=(),
        extractor=structural_object.extractor,
        comparator=structural_object.comparator,
        fingerprint=structural_object.expected_fingerprint,
        evidence=structural_object.expected_evidence,
    )


def build_governance_manifest(project: KnowledgeBaseProject) -> dict[str, Any]:
    context = GovernanceProjectArtifactsContext.from_project(project)
    closure = context.closure
    generated_artifacts = _expected_generated_artifact_paths(project)
    symbols = [
        _snapshot_symbol_from_structural_object(structural_object, context.binding_index)
        for structural_object in closure.structural_objects
    ]
    payload = closure.to_manifest_dict()
    payload.update(
        {
            "manifest_version": GOVERNANCE_MANIFEST_VERSION,
            "generator_version": GOVERNANCE_GENERATOR_VERSION,
            "canonical_source": generated_artifacts.canonical_graph_json,
            "derived_view_of": generated_artifacts.canonical_graph_json,
            "symbols": [item.to_dict() for item in symbols],
            "strict_zone_report": context.strict_zone_report,
            "object_coverage_report": context.object_coverage_report,
        }
    )
    return payload


def build_governance_tree(project: KnowledgeBaseProject) -> dict[str, Any]:
    context = GovernanceProjectArtifactsContext.from_project(project)
    closure = context.closure
    generated_artifacts = _expected_generated_artifact_paths(project)
    roots = GovernanceTreeRoots.for_project(project.metadata.project_id)
    builder = GovernanceTreeBuilder(
        project_id=project.metadata.project_id,
        roots=roots,
    )
    builder.add_root_nodes(project)
    for source in closure.upstream_closure:
        builder.add_source_ref(source)
    for structural_object in closure.structural_objects:
        builder.add_structural_object(structural_object)
    for strict_entry in closure.strict_zone:
        builder.add_strict_zone_entry(strict_entry)
    for candidate in closure.candidates:
        builder.add_candidate(candidate)
    builder.add_evidence_artifacts(closure)

    return {
        "tree_version": GOVERNANCE_TREE_VERSION,
        "project_id": project.metadata.project_id,
        "template_id": project.metadata.template,
        "generator_version": GOVERNANCE_GENERATOR_VERSION,
        "canonical_source": generated_artifacts.canonical_graph_json,
        "derived_view_of": generated_artifacts.canonical_graph_json,
        "root_node_id": roots.project_root_id,
        "project_discovery": closure.discovery.to_dict(),
        "upstream_closure": [item.to_dict() for item in closure.upstream_closure],
        "strict_zone": [item.to_dict() for item in closure.strict_zone],
        "strict_zone_report": context.strict_zone_report,
        "object_coverage_report": context.object_coverage_report,
        "evidence_artifacts": dict(closure.evidence_artifacts),
        "structural_objects": [item.to_manifest_dict() for item in closure.structural_objects],
        "role_bindings": [item.to_dict() for item in closure.role_bindings],
        "candidates": [item.to_dict() for item in closure.candidates],
        "nodes": builder.serialized_nodes(),
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


def _framework_ref_payload(module: FrameworkModule, ref: UpstreamRef) -> dict[str, Any]:
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
    context = _build_governance_definitions_context(project)
    issues = list(_binding_validation_issues(context.bindings_by_symbol, context.definitions))
    for definition in context.definitions:
        for missing_binding in context.missing_bindings_for(definition):
            rel_file, _separator, locator = missing_binding.partition(" -> ")
            issues.append(
                {
                    "code": "MISSING_BINDING",
                    "message": f"required governed binding is missing for {definition.symbol_id}: {rel_file} -> {locator}",
                    "file": rel_file,
                    "line": 1,
                    "symbol_id": definition.symbol_id,
                }
            )
    for item in context.unbound_high_risk:
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


def _governance_payload_indexes(
    payload: dict[str, Any],
    *,
    code: str,
) -> tuple[GovernancePayloadIndexes, list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    object_index, object_issues = _manifest_object_index(payload, code=code)
    issues.extend(object_issues)
    binding_index, binding_issues = _role_binding_index(payload, code=code)
    issues.extend(binding_issues)
    candidate_index, candidate_issues = _candidate_index(payload, code=code)
    issues.extend(candidate_issues)
    strict_zone_index, strict_zone_issues = _strict_zone_index(payload, code=code)
    issues.extend(strict_zone_issues)
    return (
        GovernancePayloadIndexes(
            object_index=object_index,
            binding_index=binding_index,
            candidate_index=candidate_index,
            strict_zone_index=strict_zone_index,
        ),
        issues,
    )


def _compare_evidence_artifacts(context: GovernanceComparisonContext) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    payload_artifacts = context.payload.get("evidence_artifacts", {})
    if not isinstance(payload_artifacts, dict):
        issues.append(
            {
                "code": context.payload_code,
                "message": "evidence_artifacts payload must be an object",
                "file": "",
                "line": 1,
            }
        )
        payload_artifacts = {}
    for artifact_key, rel_path in context.closure.evidence_artifacts.items():
        if payload_artifacts.get(artifact_key) != rel_path:
            issues.append(
                {
                    "code": context.payload_code,
                    "message": f"evidence artifact path drifted for {artifact_key}",
                    "file": "",
                    "line": 1,
                    "artifact": artifact_key,
                    "expected": rel_path,
                    "actual": payload_artifacts.get(artifact_key),
                }
            )
    return issues


def _compare_governance_reports(context: GovernanceComparisonContext) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for report_key, expected_report in (
        ("strict_zone_report", context.strict_zone_report),
        ("object_coverage_report", context.object_coverage_report),
    ):
        if _canonical_json(context.payload.get(report_key)) != _canonical_json(expected_report):
            issues.append(
                {
                    "code": context.payload_code,
                    "message": f"{report_key} drifted from current governance closure",
                    "file": "",
                    "line": 1,
                    "report": report_key,
                }
            )
    return issues


def _compare_structural_objects(context: GovernanceComparisonContext) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    object_index = context.indexes.object_index
    binding_index = context.indexes.binding_index
    closure = context.closure

    expected_object_ids = {item.object_id for item in closure.structural_objects}
    for object_id in sorted(set(object_index) - expected_object_ids):
        issues.append(
            {
                "code": context.payload_code,
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
                    "code": context.payload_code,
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
                    "code": context.payload_code,
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
                        "code": context.payload_code,
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
    return issues


def _compare_strict_zone(context: GovernanceComparisonContext) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    strict_zone_index = context.indexes.strict_zone_index
    for strict_entry in context.closure.strict_zone:
        payload_entry = strict_zone_index.get(strict_entry.file)
        if payload_entry is None:
            issues.append(
                {
                    "code": context.payload_code,
                    "message": f"missing strict zone entry: {strict_entry.file}",
                    "file": strict_entry.file,
                    "line": 1,
                }
            )
            continue
        if sorted(payload_entry.get("object_ids", [])) != list(strict_entry.object_ids):
            issues.append(
                {
                    "code": context.payload_code,
                    "message": f"strict zone object closure drifted for {strict_entry.file}",
                    "file": strict_entry.file,
                    "line": 1,
                }
            )
        if payload_entry.get("minimality_status") != strict_entry.minimality_status:
            issues.append(
                {
                    "code": context.payload_code,
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
    return issues


def _compare_candidates(context: GovernanceComparisonContext) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    candidate_index = context.indexes.candidate_index
    for candidate in context.closure.candidates:
        payload_candidate = candidate_index.get(candidate.candidate_id)
        if payload_candidate is None:
            issues.append(
                {
                    "code": context.payload_code,
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
    return issues


def _compare_tree_nodes(context: GovernanceComparisonContext) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    node_index, node_issues = _tree_node_index(context.payload)
    issues.extend(node_issues)
    project_id = context.project.metadata.project_id
    for structural_object in context.closure.structural_objects:
        object_node_id = f"project:{project_id}:structure:object:{structural_object.object_id}"
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
    for strict_entry in context.closure.strict_zone:
        file_node_id = f"project:{project_id}:code:file:{strict_entry.file}"
        if file_node_id not in node_index:
            issues.append(
                {
                    "code": "GOVERNANCE_TREE_INVALID",
                    "message": f"governance tree is missing strict zone file node: {strict_entry.file}",
                    "file": strict_entry.file,
                    "line": 1,
                }
            )
    for artifact_key in context.closure.evidence_artifacts:
        node_id = f"project:{project_id}:evidence:artifact:{artifact_key}"
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
        project_context = GovernanceProjectArtifactsContext.from_project(project)
    except Exception as exc:
        return [
            {
                "code": "GOVERNANCE_PROJECT_INVALID",
                "message": str(exc),
                "file": _relative(project.product_spec_file),
                "line": 1,
            }
        ]
    payload_code = "GOVERNANCE_TREE_INVALID" if tree_mode else "GOVERNANCE_MANIFEST_INVALID"
    indexes, issues = _governance_payload_indexes(payload, code=payload_code)
    context = GovernanceComparisonContext(
        project=project,
        closure=project_context.closure,
        payload=payload,
        payload_code=payload_code,
        tree_mode=tree_mode,
        strict_zone_report=project_context.strict_zone_report,
        object_coverage_report=project_context.object_coverage_report,
        indexes=indexes,
    )
    issues.extend(_compare_evidence_artifacts(context))
    issues.extend(_compare_governance_reports(context))
    issues.extend(_compare_structural_objects(context))
    issues.extend(_compare_strict_zone(context))
    issues.extend(_compare_candidates(context))
    if tree_mode:
        issues.extend(_compare_tree_nodes(context))
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
