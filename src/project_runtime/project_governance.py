from __future__ import annotations

from dataclasses import asdict, dataclass, field
import ast
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from project_runtime.template_registry import (
    PROJECTS_DIR,
    detect_project_template_id,
    resolve_project_template_registration,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
STRUCTURAL_GOVERNANCE_VERSION = "project-governance/v1"


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def relative_path(path: Path | str) -> str:
    candidate = Path(path)
    if candidate.is_absolute():
        try:
            return candidate.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            return str(candidate)
    return candidate.as_posix()


def normalize_path(path: str | Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = (REPO_ROOT / candidate).resolve()
    return candidate


@dataclass(frozen=True)
class SourceRef:
    layer: str
    file: str
    ref_kind: str
    ref_id: str
    digest: str | None = None

    def key(self) -> tuple[str, str, str, str]:
        return (self.layer, self.file, self.ref_kind, self.ref_id)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "layer": self.layer,
            "file": self.file,
            "ref_kind": self.ref_kind,
            "ref_id": self.ref_id,
        }
        if self.digest is not None:
            payload["digest"] = self.digest
        return payload


@dataclass(frozen=True)
class RequiredRole:
    role_id: str
    role_kind: str
    description: str
    candidate_kinds: tuple[str, ...]
    locator_patterns: tuple[str, ...] = ()
    file_hints: tuple[str, ...] = ()
    classification: str = "governed"
    min_count: int = 1
    max_count: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StructuralObject:
    object_id: str
    project_id: str
    kind: str
    title: str
    risk_level: str
    cardinality: str
    status: str
    semantic: dict[str, Any]
    required_roles: tuple[RequiredRole, ...]
    sources_framework: tuple[SourceRef, ...] = ()
    sources_product: tuple[SourceRef, ...] = ()
    sources_implementation: tuple[SourceRef, ...] = ()
    expected_evidence: dict[str, Any] = field(default_factory=dict)
    expected_fingerprint: str = ""
    actual_evidence: dict[str, Any] = field(default_factory=dict)
    actual_fingerprint: str = ""
    comparator: str = ""
    extractor: str = ""
    origin_categories: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def all_sources(self) -> tuple[SourceRef, ...]:
        return (*self.sources_framework, *self.sources_product, *self.sources_implementation)

    def to_manifest_dict(self) -> dict[str, Any]:
        return {
            "object_id": self.object_id,
            "project_id": self.project_id,
            "kind": self.kind,
            "title": self.title,
            "risk_level": self.risk_level,
            "cardinality": self.cardinality,
            "status": self.status,
            "semantic": self.semantic,
            "sources": {
                "framework": [item.to_dict() for item in self.sources_framework],
                "product": [item.to_dict() for item in self.sources_product],
                "implementation": [item.to_dict() for item in self.sources_implementation],
            },
            "required_roles": [item.to_dict() for item in self.required_roles],
            "expected_evidence": self.expected_evidence,
            "expected_fingerprint": self.expected_fingerprint,
            "actual_evidence": self.actual_evidence,
            "actual_fingerprint": self.actual_fingerprint,
            "comparator": self.comparator,
            "extractor": self.extractor,
            "origin_categories": list(self.origin_categories),
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class StructuralCandidate:
    candidate_id: str
    project_id: str
    file: str
    locator: str
    kind: str
    confidence: float
    reasons: tuple[str, ...]
    classification: str = ""
    object_id: str | None = None
    role_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["confidence"] = round(self.confidence, 3)
        return payload


@dataclass(frozen=True)
class ResolvedRoleBinding:
    object_id: str
    role_id: str
    role_kind: str
    classification: str
    candidate_ids: tuple[str, ...]
    file_refs: tuple[str, ...]
    status: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StrictZoneEntry:
    file: str
    object_ids: tuple[str, ...]
    role_ids: tuple[str, ...]
    candidate_ids: tuple[str, ...]
    reasons: tuple[str, ...]
    why_required: tuple[str, ...] = ()
    minimality_status: str = "uncertain"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FrameworkDrivenProjectRecord:
    project_id: str
    template_id: str
    product_spec_file: str
    implementation_config_file: str
    generated_dir: str
    discovery_reasons: tuple[str, ...]
    framework_refs: tuple[str, ...]
    artifact_contract: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProjectDiscoveryAuditEntry:
    project_id: str
    directory: str
    framework_driven: bool
    template_id: str | None
    classification: str
    reasons: tuple[str, ...]
    product_spec_file: str | None = None
    implementation_config_file: str | None = None
    generated_dir: str | None = None
    framework_refs: tuple[str, ...] = ()
    artifact_contract: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProjectGovernanceClosure:
    project_id: str
    template_id: str
    product_spec_file: str
    implementation_config_file: str
    discovery: FrameworkDrivenProjectRecord
    structural_objects: tuple[StructuralObject, ...]
    candidates: tuple[StructuralCandidate, ...]
    role_bindings: tuple[ResolvedRoleBinding, ...]
    strict_zone: tuple[StrictZoneEntry, ...]
    upstream_closure: tuple[SourceRef, ...]
    evidence_artifacts: dict[str, str]

    def to_manifest_dict(self) -> dict[str, Any]:
        return {
            "manifest_version": STRUCTURAL_GOVERNANCE_VERSION,
            "project_id": self.project_id,
            "template_id": self.template_id,
            "product_spec_file": self.product_spec_file,
            "implementation_config_file": self.implementation_config_file,
            "discovery": self.discovery.to_dict(),
            "upstream_closure": [item.to_dict() for item in self.upstream_closure],
            "structural_objects": [item.to_manifest_dict() for item in self.structural_objects],
            "role_bindings": [item.to_dict() for item in self.role_bindings],
            "strict_zone": [item.to_dict() for item in self.strict_zone],
            "candidates": [item.to_dict() for item in self.candidates],
            "evidence_artifacts": dict(self.evidence_artifacts),
        }


DISCOVERY_CLASSIFICATIONS = {
    "recognized",
    "missing_required_files",
    "template_not_registered",
    "materialization_failed",
    "not_framework_driven_project",
    "generated_contract_missing",
    "discovery_capability_insufficient",
    "other",
}
DISCOVERY_AUDIT_VERSION = "project-discovery-audit/v1"


def _framework_refs_from_project(project: Any) -> tuple[str, ...]:
    refs: list[str] = []
    for field_name in ("frontend", "domain", "backend"):
        framework_path = getattr(getattr(project, "framework", None), field_name, None)
        if isinstance(framework_path, str) and framework_path.strip():
            refs.append(framework_path.strip())
    return tuple(sorted(refs))


def _artifact_contract_from_project(project: Any) -> tuple[str, ...]:
    artifact_contract: list[str] = []
    implementation = getattr(project, "implementation", None)
    artifacts = getattr(implementation, "artifacts", None)
    if artifacts is None:
        return ()
    for field_name in (
        "framework_ir_json",
        "product_spec_json",
        "implementation_bundle_py",
        "generation_manifest_json",
        "governance_manifest_json",
        "governance_tree_json",
        "strict_zone_report_json",
        "object_coverage_report_json",
    ):
        value = getattr(artifacts, field_name, None)
        if isinstance(value, str) and value.strip():
            artifact_contract.append(value.strip())
    return tuple(artifact_contract)


def _iter_python_files(paths: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for base in paths:
        if not base.exists():
            continue
        if base.is_file() and base.suffix == ".py":
            files.append(base)
            continue
        for item in base.rglob("*.py"):
            if item.is_file():
                files.append(item)
    return sorted({path.resolve() for path in files})


def _dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    if isinstance(node, ast.Call):
        return _dotted_name(node.func)
    if isinstance(node, ast.Subscript):
        return _dotted_name(node.value)
    return ""


def _function_signals(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    signals: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            callee = _dotted_name(child.func)
            if callee.endswith(("FastAPI", "APIRouter")):
                signals.add("router-construction")
            if callee.endswith(("add_api_route", "include_router")):
                signals.add("route-registration")
            if callee.endswith(("write_text", "write_bytes", "dump", "dumps")):
                signals.add("artifact-write")
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            text = child.value
            if "governance" in text:
                signals.add("governance-text")
            if "manifest" in text or "tree" in text:
                signals.add("evidence-text")
            if "citation" in text:
                signals.add("citation-text")
    return signals


def _build_candidate(
    *,
    project_id: str,
    file: Path,
    locator: str,
    kind: str,
    confidence: float,
    reasons: list[str],
) -> StructuralCandidate:
    rel_file = relative_path(file)
    candidate_id = f"{project_id}:{rel_file}:{locator}"
    return StructuralCandidate(
        candidate_id=candidate_id,
        project_id=project_id,
        file=rel_file,
        locator=locator,
        kind=kind,
        confidence=confidence,
        reasons=tuple(reasons),
    )


def scan_python_structural_candidates(
    *,
    project_id: str,
    search_roots: Iterable[Path] | None = None,
) -> tuple[StructuralCandidate, ...]:
    roots = tuple(search_roots or (REPO_ROOT / "src", REPO_ROOT / "scripts"))
    candidates: list[StructuralCandidate] = []
    for file_path in _iter_python_files(roots):
        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=file_path.as_posix())
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                locator = f"function:{node.name}"
                decorator_names = tuple(_dotted_name(item) for item in node.decorator_list)
                if any(name.endswith((".get", ".post", ".put", ".delete", ".patch")) for name in decorator_names):
                    candidates.append(
                        _build_candidate(
                            project_id=project_id,
                            file=file_path,
                            locator=locator,
                            kind="python_route_handler",
                            confidence=0.99,
                            reasons=["decorated FastAPI/APIRouter route handler"],
                        )
                    )
                    continue

                signals = _function_signals(node)
                body_names = {child.id for child in ast.walk(node) if isinstance(child, ast.Name)}
                lowered = node.name.lower()
                if lowered.startswith(
                    (
                        "build_",
                        "_build_",
                        "compile_",
                        "resolve_",
                        "create_",
                        "materialize_",
                        "_expected_",
                        "_actual_",
                    )
                ):
                    reason = ["builder/compiler naming pattern"]
                    confidence = 0.82
                    kind = "python_builder"
                    if "router-construction" in signals or "route-registration" in signals:
                        kind = "python_route_builder"
                        confidence = 0.93
                        reason.append("contains router construction or route registration")
                    if "artifact-write" in signals or "governance" in lowered or "manifest" in lowered or "tree" in lowered:
                        kind = "python_evidence_builder"
                        confidence = max(confidence, 0.91)
                        reason.append("writes or composes governance/evidence artifacts")
                    if {"implementation", "backend_spec", "ui_spec", "generated_artifacts"} & body_names:
                        kind = "python_config_sink"
                        confidence = max(confidence, 0.9)
                        reason.append("consumes implementation/runtime effect structures")
                    candidates.append(
                        _build_candidate(
                            project_id=project_id,
                            file=file_path,
                            locator=locator,
                            kind=kind,
                            confidence=confidence,
                            reasons=reason,
                        )
                    )
                    continue

                if any(token in lowered for token in ("answer", "retrieval", "citation", "merge", "context", "return")):
                    candidates.append(
                        _build_candidate(
                            project_id=project_id,
                            file=file_path,
                            locator=locator,
                            kind="python_behavior_orchestrator",
                            confidence=0.88,
                            reasons=["function name matches user-visible behavior policy surface"],
                        )
                    )
                    continue

                if "artifact-write" in signals or "evidence-text" in signals:
                    candidates.append(
                        _build_candidate(
                            project_id=project_id,
                            file=file_path,
                            locator=locator,
                            kind="python_evidence_builder",
                            confidence=0.84,
                            reasons=["function emits manifest/tree/generated evidence"],
                        )
                    )
                    continue

            if isinstance(node, ast.ClassDef):
                locator = f"class:{node.name}"
                base_names = {_dotted_name(base).split(".")[-1] for base in node.bases}
                class_decorator_names = {
                    _dotted_name(item).split(".")[-1] for item in node.decorator_list
                }
                if {"BaseModel", "TypedDict", "Enum"} & base_names or "dataclass" in class_decorator_names:
                    candidates.append(
                        _build_candidate(
                            project_id=project_id,
                            file=file_path,
                            locator=locator,
                            kind="python_schema_carrier",
                            confidence=0.96,
                            reasons=["class carries request/response/spec schema surface"],
                        )
                    )

    unique: dict[str, StructuralCandidate] = {}
    for candidate in candidates:
        unique[candidate.candidate_id] = candidate
    return tuple(sorted(unique.values(), key=lambda item: (item.file, item.locator, item.kind)))


def _matches_pattern(value: str, patterns: tuple[str, ...]) -> bool:
    if not patterns:
        return True
    for pattern in patterns:
        if pattern == value:
            return True
        if pattern.endswith("*") and value.startswith(pattern[:-1]):
            return True
    return False


def resolve_role_bindings(
    structural_objects: tuple[StructuralObject, ...],
    candidates: tuple[StructuralCandidate, ...],
) -> tuple[ResolvedRoleBinding, ...]:
    bindings: list[ResolvedRoleBinding] = []
    for structural_object in structural_objects:
        for role in structural_object.required_roles:
            matches = [
                candidate
                for candidate in candidates
                if (not role.candidate_kinds or candidate.kind in role.candidate_kinds)
                and _matches_pattern(candidate.locator, role.locator_patterns)
                and _matches_pattern(candidate.file, role.file_hints)
            ]
            if role.max_count is not None:
                matches = matches[: role.max_count]
            status = "satisfied" if len(matches) >= role.min_count else "missing"
            message = (
                f"role {role.role_id} resolved to {len(matches)} candidate(s)"
                if status == "satisfied"
                else f"role {role.role_id} is missing required carriers"
            )
            bindings.append(
                ResolvedRoleBinding(
                    object_id=structural_object.object_id,
                    role_id=role.role_id,
                    role_kind=role.role_kind,
                    classification=role.classification,
                    candidate_ids=tuple(item.candidate_id for item in matches),
                    file_refs=tuple(sorted({item.file for item in matches})),
                    status=status,
                    message=message,
                )
            )
    return tuple(bindings)


def classify_candidates(
    structural_objects: tuple[StructuralObject, ...],
    candidates: tuple[StructuralCandidate, ...],
    role_bindings: tuple[ResolvedRoleBinding, ...],
) -> tuple[StructuralCandidate, ...]:
    by_candidate: dict[str, StructuralCandidate] = {item.candidate_id: item for item in candidates}
    file_object_index: dict[str, set[str]] = {}
    candidate_roles: dict[str, list[ResolvedRoleBinding]] = {}

    for binding in role_bindings:
        for file_ref in binding.file_refs:
            file_object_index.setdefault(file_ref, set()).add(binding.object_id)
        for candidate_id in binding.candidate_ids:
            candidate_roles.setdefault(candidate_id, []).append(binding)

    classified: list[StructuralCandidate] = []
    for candidate in candidates:
        matched_roles = candidate_roles.get(candidate.candidate_id, [])
        if matched_roles:
            primary = matched_roles[0]
            classified.append(
                StructuralCandidate(
                    candidate_id=candidate.candidate_id,
                    project_id=candidate.project_id,
                    file=candidate.file,
                    locator=candidate.locator,
                    kind=candidate.kind,
                    confidence=candidate.confidence,
                    reasons=candidate.reasons,
                    classification=primary.classification,
                    object_id=primary.object_id,
                    role_ids=tuple(sorted({item.role_id for item in matched_roles})),
                )
            )
            continue

        related_objects = sorted(file_object_index.get(candidate.file, set()))
        if candidate.confidence >= 0.75 and related_objects:
            classified.append(
                StructuralCandidate(
                    candidate_id=candidate.candidate_id,
                    project_id=candidate.project_id,
                    file=candidate.file,
                    locator=candidate.locator,
                    kind=candidate.kind,
                    confidence=candidate.confidence,
                    reasons=candidate.reasons,
                    classification="attached",
                    object_id=related_objects[0],
                    role_ids=(),
                )
            )
            continue

        classified.append(
            StructuralCandidate(
                candidate_id=candidate.candidate_id,
                project_id=candidate.project_id,
                file=candidate.file,
                locator=candidate.locator,
                kind=candidate.kind,
                confidence=candidate.confidence,
                reasons=candidate.reasons,
                classification="internal",
                object_id=None,
                role_ids=(),
            )
        )
    return tuple(classified)


def infer_strict_zone(
    structural_objects: tuple[StructuralObject, ...],
    role_bindings: tuple[ResolvedRoleBinding, ...],
    candidates: tuple[StructuralCandidate, ...],
    evidence_artifacts: dict[str, str],
) -> tuple[StrictZoneEntry, ...]:
    object_lookup = {item.object_id: item for item in structural_objects}
    candidate_lookup = {item.candidate_id: item for item in candidates}
    file_payloads: dict[str, dict[str, set[str]]] = {}

    def ensure_file(file_name: str) -> dict[str, set[str]]:
        return file_payloads.setdefault(
            file_name,
            {
                "object_ids": set(),
                "role_ids": set(),
                "candidate_ids": set(),
                "reasons": set(),
            },
        )

    for binding in role_bindings:
        for file_name in binding.file_refs:
            payload = ensure_file(file_name)
            payload["object_ids"].add(binding.object_id)
            payload["role_ids"].add(binding.role_id)
            payload["reasons"].add(f"role:{binding.role_id}")
            payload["reasons"].add(f"object:{binding.object_id}")
        for candidate_id in binding.candidate_ids:
            candidate = candidate_lookup.get(candidate_id)
            if candidate is None:
                continue
            payload = ensure_file(candidate.file)
            payload["candidate_ids"].add(candidate.candidate_id)

    for candidate in candidates:
        if candidate.classification not in {"governed", "attached"}:
            continue
        payload = ensure_file(candidate.file)
        payload["candidate_ids"].add(candidate.candidate_id)
        if candidate.object_id:
            payload["object_ids"].add(candidate.object_id)
        payload["reasons"].add(f"candidate:{candidate.classification}")

    for artifact_key, artifact_path in evidence_artifacts.items():
        payload = ensure_file(artifact_path)
        payload["reasons"].add(f"evidence:{artifact_key}")

    entries: list[StrictZoneEntry] = []
    for file_name in sorted(file_payloads):
        payload = file_payloads[file_name]
        entries.append(
            StrictZoneEntry(
                file=file_name,
                object_ids=tuple(sorted(payload["object_ids"])),
                role_ids=tuple(sorted(payload["role_ids"])),
                candidate_ids=tuple(sorted(payload["candidate_ids"])),
                reasons=tuple(sorted(payload["reasons"])),
            )
        )
    return tuple(entries)


def annotate_strict_zone_minimality(
    strict_zone: tuple[StrictZoneEntry, ...],
    role_bindings: tuple[ResolvedRoleBinding, ...],
    candidates: tuple[StructuralCandidate, ...],
    evidence_artifacts: dict[str, str],
) -> tuple[StrictZoneEntry, ...]:
    role_bindings_by_file: dict[str, list[ResolvedRoleBinding]] = {}
    for binding in role_bindings:
        for file_name in binding.file_refs:
            role_bindings_by_file.setdefault(file_name, []).append(binding)

    candidate_index = {item.candidate_id: item for item in candidates}
    evidence_by_file: dict[str, list[str]] = {}
    for artifact_key, artifact_path in evidence_artifacts.items():
        evidence_by_file.setdefault(artifact_path, []).append(artifact_key)

    annotated: list[StrictZoneEntry] = []
    for entry in strict_zone:
        why_required: list[str] = []
        minimality_status = "redundant"

        file_bindings = role_bindings_by_file.get(entry.file, [])
        if file_bindings:
            minimality_status = "required"
            for binding in sorted(file_bindings, key=lambda item: (item.object_id, item.role_id)):
                why_required.append(
                    f"remove file breaks role closure {binding.object_id} -> {binding.role_id}"
                )

        artifact_keys = sorted(evidence_by_file.get(entry.file, []))
        if artifact_keys:
            minimality_status = "required"
            why_required.extend(
                f"remove file breaks evidence artifact {artifact_key}" for artifact_key in artifact_keys
            )

        if not file_bindings and not artifact_keys:
            attached_candidates = [
                candidate_index[candidate_id]
                for candidate_id in entry.candidate_ids
                if candidate_id in candidate_index
                and candidate_index[candidate_id].classification == "attached"
            ]
            if attached_candidates:
                minimality_status = "uncertain"
                why_required.extend(
                    f"attached candidate {candidate.locator} still rides this carrier"
                    for candidate in sorted(attached_candidates, key=lambda item: item.candidate_id)
                )

        annotated.append(
            StrictZoneEntry(
                file=entry.file,
                object_ids=entry.object_ids,
                role_ids=entry.role_ids,
                candidate_ids=entry.candidate_ids,
                reasons=entry.reasons,
                why_required=tuple(sorted(set(why_required))),
                minimality_status=minimality_status,
            )
        )
    return tuple(annotated)


def build_strict_zone_report(closure: ProjectGovernanceClosure) -> dict[str, Any]:
    summary = {
        "entry_count": len(closure.strict_zone),
        "required_count": sum(1 for item in closure.strict_zone if item.minimality_status == "required"),
        "redundant_count": sum(1 for item in closure.strict_zone if item.minimality_status == "redundant"),
        "uncertain_count": sum(1 for item in closure.strict_zone if item.minimality_status == "uncertain"),
    }
    return {
        "report_version": "strict-zone-report/v1",
        "project_id": closure.project_id,
        "template_id": closure.template_id,
        "strict_zone": [item.to_dict() for item in closure.strict_zone],
        "summary": summary,
    }


def build_object_coverage_report(closure: ProjectGovernanceClosure) -> dict[str, Any]:
    binding_map: dict[tuple[str, str], ResolvedRoleBinding] = {
        (item.object_id, item.role_id): item for item in closure.role_bindings
    }
    candidate_counts = {
        "governed_candidate_count": sum(1 for item in closure.candidates if item.classification == "governed"),
        "attached_candidate_count": sum(1 for item in closure.candidates if item.classification == "attached"),
        "internal_candidate_count": sum(1 for item in closure.candidates if item.classification == "internal"),
    }
    entries: list[dict[str, Any]] = []
    future_categories: set[str] = set()
    fully_closed = 0
    partially_closed = 0

    attached_kinds = sorted({item.kind for item in closure.candidates if item.classification == "attached"})
    if "python_schema_carrier" in attached_kinds:
        future_categories.add("schema carriers that are still attached-only")
    if "python_builder" in attached_kinds or "python_evidence_builder" in attached_kinds:
        future_categories.add("compiler/evidence builders that are still attached-only")
    if any(item.kind == "implementation_effect" for item in closure.structural_objects):
        future_categories.add("implementation effect objects are field-level, not sink-level")

    for structural_object in closure.structural_objects:
        required_roles = [role.role_id for role in structural_object.required_roles]
        bound_roles = [
            role.role_id
            for role in structural_object.required_roles
            if binding_map.get((structural_object.object_id, role.role_id), None) is not None
            and binding_map[(structural_object.object_id, role.role_id)].status == "satisfied"
        ]
        missing_roles = sorted(set(required_roles) - set(bound_roles))
        overbound_roles = sorted(
            binding.role_id
            for binding in closure.role_bindings
            if binding.object_id == structural_object.object_id and binding.role_id not in required_roles
        )
        compare_status = (
            "match"
            if structural_object.actual_fingerprint == structural_object.expected_fingerprint
            else "mismatch"
        )
        closure_status = "fully_closed" if not missing_roles and compare_status == "match" else "partially_closed"
        if closure_status == "fully_closed":
            fully_closed += 1
        else:
            partially_closed += 1
        entries.append(
            {
                "object_id": structural_object.object_id,
                "kind": structural_object.kind,
                "risk_level": structural_object.risk_level,
                "status": structural_object.status,
                "source_categories": list(structural_object.origin_categories),
                "sources": {
                    "framework": [item.to_dict() for item in structural_object.sources_framework],
                    "product": [item.to_dict() for item in structural_object.sources_product],
                    "implementation": [item.to_dict() for item in structural_object.sources_implementation],
                },
                "required_roles": required_roles,
                "actual_roles": bound_roles,
                "missing_roles": missing_roles,
                "overbound_roles": overbound_roles,
                "compare_status": compare_status,
                "compare_coverage": {
                    "extractor": structural_object.extractor,
                    "comparator": structural_object.comparator,
                    "expected_fingerprint": structural_object.expected_fingerprint,
                    "actual_fingerprint": structural_object.actual_fingerprint,
                },
                "closure_status": closure_status,
            }
        )

    return {
        "report_version": "object-coverage-report/v1",
        "project_id": closure.project_id,
        "template_id": closure.template_id,
        "summary": {
            "governed_object_count": len(closure.structural_objects),
            "fully_closed_object_count": fully_closed,
            "partially_closed_object_count": partially_closed,
            **candidate_counts,
            "uncovered_future_categories": sorted(future_categories),
        },
        "objects": entries,
    }


def build_project_discovery_audit(projects_dir: Path | None = None) -> dict[str, Any]:
    root = projects_dir or PROJECTS_DIR
    entries = audit_project_directories(root)
    return {
        "audit_version": DISCOVERY_AUDIT_VERSION,
        "projects_dir": relative_path(root),
        "entries": [item.to_dict() for item in entries],
        "summary": {
            "recognized_count": sum(1 for item in entries if item.framework_driven),
            "excluded_count": sum(1 for item in entries if not item.framework_driven),
            "classification_counts": {
                classification: sum(1 for item in entries if item.classification == classification)
                for classification in sorted(DISCOVERY_CLASSIFICATIONS)
                if any(entry.classification == classification for entry in entries)
            },
        },
    }


def render_project_discovery_audit_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# 项目发现审计",
        "",
        f"- 审计版本：`{payload['audit_version']}`",
        f"- 扫描目录：`{payload['projects_dir']}`",
        f"- 识别为框架驱动项目：`{payload['summary']['recognized_count']}`",
        f"- 排除项目：`{payload['summary']['excluded_count']}`",
        "",
        "| 项目目录 | 结果 | 分类 | 模板 | 原因 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for entry in payload.get("entries", []):
        if not isinstance(entry, dict):
            continue
        result = "识别" if entry.get("framework_driven") else "排除"
        reasons = "<br>".join(str(item) for item in entry.get("reasons", []))
        lines.append(
            "| {directory} | {result} | `{classification}` | `{template}` | {reasons} |".format(
                directory=entry.get("directory", ""),
                result=result,
                classification=entry.get("classification", ""),
                template=entry.get("template_id") or "-",
                reasons=reasons or "-",
            )
        )
    lines.append("")
    return "\n".join(lines)


def discover_framework_driven_projects(projects_dir: Path | None = None) -> tuple[FrameworkDrivenProjectRecord, ...]:
    root = projects_dir or PROJECTS_DIR
    if not root.exists():
        return ()

    discovered: list[FrameworkDrivenProjectRecord] = []
    for product_spec_file in sorted(root.glob("*/product_spec.toml")):
        implementation_config_file = product_spec_file.parent / "implementation_config.toml"
        if not implementation_config_file.exists():
            continue
        try:
            registration = resolve_project_template_registration(product_spec_file)
            project = registration.load_project(product_spec_file)
        except Exception:
            continue

        project_id = str(getattr(getattr(project, "metadata", None), "project_id", product_spec_file.parent.name))
        framework_refs = list(_framework_refs_from_project(project))
        artifact_contract = list(_artifact_contract_from_project(project))

        discovered.append(
            FrameworkDrivenProjectRecord(
                project_id=project_id,
                template_id=registration.template_id,
                product_spec_file=relative_path(product_spec_file),
                implementation_config_file=relative_path(implementation_config_file),
                generated_dir=relative_path(product_spec_file.parent / "generated"),
                discovery_reasons=(
                    "project spec exists under projects/<project_id>/product_spec.toml",
                    "implementation_config.toml exists beside product_spec.toml",
                    f"registered template resolved: {registration.template_id}",
                    "project loads through the registered framework-driven materialization chain",
                    "framework selections resolve to concrete framework modules",
                    "implementation_config defines generated artifact evidence contract",
                ),
                framework_refs=tuple(sorted(framework_refs)),
                artifact_contract=tuple(artifact_contract),
            )
        )
    return tuple(discovered)


def audit_project_directories(projects_dir: Path | None = None) -> tuple[ProjectDiscoveryAuditEntry, ...]:
    root = projects_dir or PROJECTS_DIR
    if not root.exists():
        return ()

    entries: list[ProjectDiscoveryAuditEntry] = []
    for project_dir in sorted(item for item in root.iterdir() if item.is_dir()):
        product_spec_file = project_dir / "product_spec.toml"
        implementation_config_file = project_dir / "implementation_config.toml"
        project_id = project_dir.name

        if not product_spec_file.exists() or not implementation_config_file.exists():
            missing = []
            if not product_spec_file.exists():
                missing.append("missing product_spec.toml")
            if not implementation_config_file.exists():
                missing.append("missing implementation_config.toml")
            entries.append(
                ProjectDiscoveryAuditEntry(
                    project_id=project_id,
                    directory=relative_path(project_dir),
                    framework_driven=False,
                    template_id=None,
                    classification="missing_required_files",
                    reasons=tuple(missing),
                )
            )
            continue

        try:
            template_id = detect_project_template_id(product_spec_file)
        except Exception as exc:
            entries.append(
                ProjectDiscoveryAuditEntry(
                    project_id=project_id,
                    directory=relative_path(project_dir),
                    framework_driven=False,
                    template_id=None,
                    classification="template_not_registered",
                    reasons=(f"unable to resolve project.template: {exc}",),
                    product_spec_file=relative_path(product_spec_file),
                    implementation_config_file=relative_path(implementation_config_file),
                )
            )
            continue

        try:
            registration = resolve_project_template_registration(product_spec_file)
        except Exception as exc:
            entries.append(
                ProjectDiscoveryAuditEntry(
                    project_id=project_id,
                    directory=relative_path(project_dir),
                    framework_driven=False,
                    template_id=template_id,
                    classification="template_not_registered",
                    reasons=(f"template {template_id} is not registered: {exc}",),
                    product_spec_file=relative_path(product_spec_file),
                    implementation_config_file=relative_path(implementation_config_file),
                )
            )
            continue

        try:
            project = registration.load_project(product_spec_file)
        except Exception as exc:
            entries.append(
                ProjectDiscoveryAuditEntry(
                    project_id=project_id,
                    directory=relative_path(project_dir),
                    framework_driven=False,
                    template_id=template_id,
                    classification="materialization_failed",
                    reasons=(f"registered loader failed: {exc}",),
                    product_spec_file=relative_path(product_spec_file),
                    implementation_config_file=relative_path(implementation_config_file),
                )
            )
            continue

        framework_refs = _framework_refs_from_project(project)
        if not framework_refs:
            entries.append(
                ProjectDiscoveryAuditEntry(
                    project_id=project_id,
                    directory=relative_path(project_dir),
                    framework_driven=False,
                    template_id=template_id,
                    classification="not_framework_driven_project",
                    reasons=("loaded project does not expose framework module refs",),
                    product_spec_file=relative_path(product_spec_file),
                    implementation_config_file=relative_path(implementation_config_file),
                )
            )
            continue

        artifact_contract = _artifact_contract_from_project(project)
        if not artifact_contract:
            entries.append(
                ProjectDiscoveryAuditEntry(
                    project_id=project_id,
                    directory=relative_path(project_dir),
                    framework_driven=False,
                    template_id=template_id,
                    classification="generated_contract_missing",
                    reasons=("implementation config does not expose generated artifact contract",),
                    product_spec_file=relative_path(product_spec_file),
                    implementation_config_file=relative_path(implementation_config_file),
                    framework_refs=framework_refs,
                )
            )
            continue

        entries.append(
            ProjectDiscoveryAuditEntry(
                project_id=project_id,
                directory=relative_path(project_dir),
                framework_driven=True,
                template_id=template_id,
                classification="recognized",
                reasons=(
                    "product_spec.toml and implementation_config.toml both exist",
                    f"registered template resolved: {template_id}",
                    "project loads through the registered framework-driven materialization chain",
                    "framework selections resolve to concrete framework modules",
                    "implementation config exposes generated artifact contract",
                ),
                product_spec_file=relative_path(product_spec_file),
                implementation_config_file=relative_path(implementation_config_file),
                generated_dir=relative_path(project_dir / "generated"),
                framework_refs=framework_refs,
                artifact_contract=artifact_contract,
            )
        )
    return tuple(entries)
