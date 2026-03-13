from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import json
from pathlib import Path
import tomllib
from typing import Any

from framework_ir import FrameworkModuleIR, load_framework_registry, parse_framework_module
from project_runtime.config_layout import config_layout
from project_runtime.project_governance import (
    FrameworkDrivenProjectRecord,
    ProjectGovernanceClosure,
    RequiredRole,
    SourceRef,
    StructuralObject,
    annotate_strict_zone_minimality,
    build_object_coverage_report,
    build_strict_zone_report,
    classify_candidates,
    fingerprint,
    infer_strict_zone,
    relative_path,
    resolve_role_bindings,
    scan_python_structural_candidates,
)
from project_runtime.template_registry import (
    ProjectTemplateRegistration,
    detect_project_template_id as detect_registered_project_template_id,
    register_project_template,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DOCUMENT_CHUNKING_PRODUCT_SPEC_FILE = REPO_ROOT / "projects/document_chunking_basic/product_spec.toml"
DEFAULT_DOCUMENT_CHUNKING_IMPLEMENTATION_CONFIG_FILE = (
    REPO_ROOT / "projects/document_chunking_basic/implementation_config.toml"
)
DOCUMENT_CHUNKING_TEMPLATE_ID = "document_chunking_pipeline"
DOCUMENT_CHUNKING_PRODUCT_SPEC_LAYOUT = config_layout(
    {
        "project",
        "framework",
        "input",
        "segmentation",
        "role_judgment",
        "composition",
        "output",
        "validation",
    },
    {},
)
DOCUMENT_CHUNKING_IMPLEMENTATION_CONFIG_LAYOUT = config_layout(
    {"runtime", "pipeline", "evidence", "artifacts"},
    {},
)
LEGACY_GENERATED_ARTIFACT_NAMES = frozenset({"project_bundle.py", "workbench_spec.json"})
SUPPORTED_APP_BUILDERS = frozenset({"document_chunking_api_v1"})
SUPPORTED_NORMALIZATION_MODES = frozenset({"normalize_markdown_text_v1"})
SUPPORTED_SPLITTERS = frozenset({"blank_line_blocks_v1"})
SUPPORTED_OUTPUT_ORDERS = frozenset({"chunk_id_ascending"})


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _relative_path(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def _normalize_project_path(project_file: str | Path) -> Path:
    project_path = Path(project_file)
    if not project_path.is_absolute():
        project_path = (REPO_ROOT / project_path).resolve()
    return project_path


def _implementation_config_path_for(product_spec_path: Path) -> Path:
    return product_spec_path.parent / "implementation_config.toml"


def _read_toml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing project config: {path}")
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"project config must decode into object: {path}")
    return data


def _cleanup_generated_output_dir(output_path: Path, expected_file_names: set[str]) -> None:
    removable_names = expected_file_names | LEGACY_GENERATED_ARTIFACT_NAMES
    for child in output_path.iterdir():
        if not child.is_file():
            continue
        if child.name in expected_file_names:
            continue
        if child.name in removable_names or child.suffix.lower() in {".json", ".py"}:
            child.unlink()


def _require_table(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"missing required table: {key}")
    return value


def _require_string(parent: dict[str, Any], key: str) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing required string: {key}")
    return value.strip()


def _require_bool(parent: dict[str, Any], key: str) -> bool:
    value = parent.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"missing required bool: {key}")
    return value


def _require_int(parent: dict[str, Any], key: str) -> int:
    value = parent.get(key)
    if not isinstance(value, int):
        raise ValueError(f"missing required int: {key}")
    return value


def _require_string_tuple(parent: dict[str, Any], key: str) -> tuple[str, ...]:
    value = parent.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"missing required string list: {key}")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{key} must only contain non-empty strings")
        items.append(item.strip())
    return tuple(items)


def _resolve_section(data: dict[str, Any], section_path: str) -> Any:
    current: Any = data
    for part in section_path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(f"missing section path: {section_path}")
        current = current[part]
    return current


def _serialize_upstream_ref(ref: SourceRef) -> dict[str, Any]:
    file_path = REPO_ROOT / ref.file
    if ref.layer == "framework":
        module = parse_framework_module(file_path)
        payload = None
        for rule in module.rules:
            if rule.rule_id == ref.ref_id:
                payload = rule.to_dict()
                break
        if payload is None:
            raise KeyError(f"missing framework rule ref {ref.ref_id} in {ref.file}")
    elif ref.layer in {"product_spec", "implementation_config"}:
        with file_path.open("rb") as handle:
            payload = _resolve_section(tomllib.load(handle), ref.ref_id)
    else:
        raise ValueError(f"unsupported upstream ref layer: {ref.layer}")
    return {
        "layer": ref.layer,
        "file": ref.file,
        "ref_kind": ref.ref_kind,
        "ref_id": ref.ref_id,
        "digest": fingerprint(payload),
    }


def detect_project_template_id(product_spec_file: str | Path) -> str:
    return detect_registered_project_template_id(product_spec_file)


def assert_supported_project_template(product_spec_file: str | Path) -> str:
    template_id = detect_project_template_id(product_spec_file)
    if template_id != DOCUMENT_CHUNKING_TEMPLATE_ID:
        raise ValueError(f"unsupported project template: {template_id}")
    return template_id


@dataclass(frozen=True)
class ProjectMetadata:
    project_id: str
    template: str
    display_name: str
    description: str
    version: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FrameworkSelection:
    frontend: str
    domain: str
    backend: str
    preset: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InputConfig:
    accepted_document_kind: str
    normalization: str
    document_id_strategy: str
    document_name_source: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SegmentationConfig:
    boundary_template: str
    boundary_signals: tuple[str, ...]
    min_block_chars: int
    max_block_chars: int
    allow_cross_document: bool

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["boundary_signals"] = list(self.boundary_signals)
        return payload


@dataclass(frozen=True)
class RoleJudgmentConfig:
    title_rule: str
    body_rule: str
    allowed_roles: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["allowed_roles"] = list(self.allowed_roles)
        return payload


@dataclass(frozen=True)
class CompositionConfig:
    anchor_role: str
    member_role: str
    group_shape: str
    closure: str
    preserve_order: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OutputConfig:
    format_name: str
    render_medium: str
    document_format_field: str
    document_format_value: str
    document_format_scope: str
    expose_paragraph_block_projection: bool
    paragraph_block_projection_name: str
    paragraph_block_projection_fence_scope: str
    expose_chunk_membership_projection: bool
    chunk_membership_projection_name: str
    chunk_membership_include_ordered_block_ids: bool
    chunk_item_layout: str
    text_id_field: str
    chunk_id_field: str
    chunk_text_field: str
    title_block_id_field: str
    body_block_id_set_field: str
    chunk_collection_field: str
    include_paragraph_blocks: bool
    include_trace_meta: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationConfig:
    require_non_empty_blocks: bool
    require_unique_order_index: bool
    require_output_traceability: bool
    max_chunk_items: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DocumentChunkingProduct:
    input: InputConfig
    segmentation: SegmentationConfig
    role_judgment: RoleJudgmentConfig
    composition: CompositionConfig
    output: OutputConfig
    validation: ValidationConfig

    def to_dict(self) -> dict[str, Any]:
        return {
            "input": self.input.to_dict(),
            "segmentation": self.segmentation.to_dict(),
            "role_judgment": self.role_judgment.to_dict(),
            "composition": self.composition.to_dict(),
            "output": self.output.to_dict(),
            "validation": self.validation.to_dict(),
        }


@dataclass(frozen=True)
class RuntimeConfig:
    app_builder: str
    cli_command: str
    api_prefix: str
    write_markdown_output: bool
    default_markdown_output: str
    write_auxiliary_output_files: bool
    paragraph_block_output_suffix: str
    chunk_membership_output_suffix: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PipelineConfig:
    normalization_mode: str
    heading_pattern: str
    splitter: str
    output_order: str
    max_block_chars: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceConfig:
    product_spec_endpoint: str
    process_text_endpoint: str
    process_file_endpoint: str
    default_validation_input: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ArtifactConfig:
    framework_ir_json: str
    product_spec_json: str
    implementation_bundle_py: str
    generation_manifest_json: str
    governance_manifest_json: str
    governance_tree_json: str
    strict_zone_report_json: str
    object_coverage_report_json: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DocumentChunkingImplementationConfig:
    runtime: RuntimeConfig
    pipeline: PipelineConfig
    evidence: EvidenceConfig
    artifacts: ArtifactConfig

    def to_dict(self) -> dict[str, Any]:
        return {
            "runtime": self.runtime.to_dict(),
            "pipeline": self.pipeline.to_dict(),
            "evidence": self.evidence.to_dict(),
            "artifacts": self.artifacts.to_dict(),
        }


@dataclass(frozen=True)
class GeneratedArtifactPaths:
    directory: str
    framework_ir_json: str
    product_spec_json: str
    implementation_bundle_py: str
    generation_manifest_json: str
    governance_manifest_json: str
    governance_tree_json: str
    strict_zone_report_json: str
    object_coverage_report_json: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DocumentChunkingProject:
    repo_root: str
    product_spec_file: str
    implementation_config_file: str
    metadata: ProjectMetadata
    framework: FrameworkSelection
    product: DocumentChunkingProduct
    implementation: DocumentChunkingImplementationConfig
    domain_ir: FrameworkModuleIR
    resolved_modules: tuple[FrameworkModuleIR, ...]
    generated_artifacts: GeneratedArtifactPaths | None = None

    def to_product_spec_dict(self) -> dict[str, Any]:
        return {
            "project": self.metadata.to_dict(),
            "framework": self.framework.to_dict(),
            **self.product.to_dict(),
        }

    def to_runtime_bundle_dict(self) -> dict[str, Any]:
        return {
            "product_spec_file": self.product_spec_file,
            "implementation_config_file": self.implementation_config_file,
            "product_spec": self.to_product_spec_dict(),
            "framework": {
                **self.framework.to_dict(),
                "primary_modules": [self.domain_ir.to_dict()],
                "resolved_modules": [item.to_dict() for item in self.resolved_modules],
            },
            "implementation_config": self.implementation.to_dict(),
            "runtime_contract": {
                "app_builder": self.implementation.runtime.app_builder,
                "api_prefix": self.implementation.runtime.api_prefix,
                "product_spec_endpoint": self.implementation.evidence.product_spec_endpoint,
                "process_text_endpoint": self.implementation.evidence.process_text_endpoint,
                "process_file_endpoint": self.implementation.evidence.process_file_endpoint,
                "default_validation_input": self.implementation.evidence.default_validation_input,
                "cli_command": self.implementation.runtime.cli_command,
                "write_markdown_output": self.implementation.runtime.write_markdown_output,
                "default_markdown_output": self.implementation.runtime.default_markdown_output,
                "write_auxiliary_output_files": self.implementation.runtime.write_auxiliary_output_files,
                "paragraph_block_output_suffix": self.implementation.runtime.paragraph_block_output_suffix,
                "chunk_membership_output_suffix": self.implementation.runtime.chunk_membership_output_suffix,
            },
            "pipeline_contract": {
                "normalization_mode": self.implementation.pipeline.normalization_mode,
                "heading_pattern": self.implementation.pipeline.heading_pattern,
                "splitter": self.implementation.pipeline.splitter,
                "output_order": self.implementation.pipeline.output_order,
                "max_block_chars": self.implementation.pipeline.max_block_chars,
            },
            "output_contract": self.product.output.to_dict(),
            "validation_contract": self.product.validation.to_dict(),
            "generated_artifacts": self.generated_artifacts.to_dict() if self.generated_artifacts else None,
        }

    def to_spec_dict(self) -> dict[str, Any]:
        return self.to_runtime_bundle_dict()

    def public_summary(self) -> dict[str, Any]:
        return {
            "product_spec_file": self.product_spec_file,
            "implementation_config_file": self.implementation_config_file,
            "project": self.metadata.to_dict(),
            "framework": self.framework.to_dict(),
            "product": self.product.to_dict(),
            "implementation": self.implementation.to_dict(),
            "resolved_module_ids": [item.module_id for item in self.resolved_modules],
            "generated_artifacts": self.generated_artifacts.to_dict() if self.generated_artifacts else None,
        }


def _resolve_framework_module(ref: str) -> FrameworkModuleIR:
    framework_path = REPO_ROOT / ref
    if not framework_path.exists():
        raise ValueError(f"framework ref does not exist: {ref}")
    return parse_framework_module(framework_path)


def _collect_framework_closure(root: FrameworkModuleIR) -> tuple[FrameworkModuleIR, ...]:
    registry = load_framework_registry()
    ordered: list[FrameworkModuleIR] = []
    seen: set[str] = set()

    def visit(module: FrameworkModuleIR) -> None:
        if module.module_id in seen:
            return
        seen.add(module.module_id)
        ordered.append(module)
        for base in module.bases:
            for ref in base.upstream_refs:
                upstream = registry.get_module(ref.framework, ref.level, ref.module)
                visit(upstream)

    visit(root)
    return tuple(ordered)


def _load_product_spec(product_spec_path: Path) -> tuple[ProjectMetadata, FrameworkSelection, DocumentChunkingProduct]:
    raw = _read_toml_file(product_spec_path)
    project_table = _require_table(raw, "project")
    framework_table = _require_table(raw, "framework")
    input_table = _require_table(raw, "input")
    segmentation_table = _require_table(raw, "segmentation")
    role_judgment_table = _require_table(raw, "role_judgment")
    composition_table = _require_table(raw, "composition")
    output_table = _require_table(raw, "output")
    validation_table = _require_table(raw, "validation")

    metadata = ProjectMetadata(
        project_id=_require_string(project_table, "project_id"),
        template=_require_string(project_table, "template"),
        display_name=_require_string(project_table, "display_name"),
        description=_require_string(project_table, "description"),
        version=_require_string(project_table, "version"),
    )
    framework = FrameworkSelection(
        frontend=_require_string(framework_table, "frontend"),
        domain=_require_string(framework_table, "domain"),
        backend=_require_string(framework_table, "backend"),
        preset=_require_string(framework_table, "preset"),
    )
    product = DocumentChunkingProduct(
        input=InputConfig(
            accepted_document_kind=_require_string(input_table, "accepted_document_kind"),
            normalization=_require_string(input_table, "normalization"),
            document_id_strategy=_require_string(input_table, "document_id_strategy"),
            document_name_source=_require_string(input_table, "document_name_source"),
        ),
        segmentation=SegmentationConfig(
            boundary_template=_require_string(segmentation_table, "boundary_template"),
            boundary_signals=_require_string_tuple(segmentation_table, "boundary_signals"),
            min_block_chars=_require_int(segmentation_table, "min_block_chars"),
            max_block_chars=_require_int(segmentation_table, "max_block_chars"),
            allow_cross_document=_require_bool(segmentation_table, "allow_cross_document"),
        ),
        role_judgment=RoleJudgmentConfig(
            title_rule=_require_string(role_judgment_table, "title_rule"),
            body_rule=_require_string(role_judgment_table, "body_rule"),
            allowed_roles=_require_string_tuple(role_judgment_table, "allowed_roles"),
        ),
        composition=CompositionConfig(
            anchor_role=_require_string(composition_table, "anchor_role"),
            member_role=_require_string(composition_table, "member_role"),
            group_shape=_require_string(composition_table, "group_shape"),
            closure=_require_string(composition_table, "closure"),
            preserve_order=_require_bool(composition_table, "preserve_order"),
        ),
        output=OutputConfig(
            format_name=_require_string(output_table, "format_name"),
            render_medium=_require_string(output_table, "render_medium"),
            document_format_field=_require_string(output_table, "document_format_field"),
            document_format_value=_require_string(output_table, "document_format_value"),
            document_format_scope=_require_string(output_table, "document_format_scope"),
            expose_paragraph_block_projection=_require_bool(output_table, "expose_paragraph_block_projection"),
            paragraph_block_projection_name=_require_string(output_table, "paragraph_block_projection_name"),
            paragraph_block_projection_fence_scope=_require_string(output_table, "paragraph_block_projection_fence_scope"),
            expose_chunk_membership_projection=_require_bool(output_table, "expose_chunk_membership_projection"),
            chunk_membership_projection_name=_require_string(output_table, "chunk_membership_projection_name"),
            chunk_membership_include_ordered_block_ids=_require_bool(output_table, "chunk_membership_include_ordered_block_ids"),
            chunk_item_layout=_require_string(output_table, "chunk_item_layout"),
            text_id_field=_require_string(output_table, "text_id_field"),
            chunk_id_field=_require_string(output_table, "chunk_id_field"),
            chunk_text_field=_require_string(output_table, "chunk_text_field"),
            title_block_id_field=_require_string(output_table, "title_block_id_field"),
            body_block_id_set_field=_require_string(output_table, "body_block_id_set_field"),
            chunk_collection_field=_require_string(output_table, "chunk_collection_field"),
            include_paragraph_blocks=_require_bool(output_table, "include_paragraph_blocks"),
            include_trace_meta=_require_bool(output_table, "include_trace_meta"),
        ),
        validation=ValidationConfig(
            require_non_empty_blocks=_require_bool(validation_table, "require_non_empty_blocks"),
            require_unique_order_index=_require_bool(validation_table, "require_unique_order_index"),
            require_output_traceability=_require_bool(validation_table, "require_output_traceability"),
            max_chunk_items=_require_int(validation_table, "max_chunk_items"),
        ),
    )
    return metadata, framework, product


def _load_implementation_config(implementation_config_path: Path) -> DocumentChunkingImplementationConfig:
    raw = _read_toml_file(implementation_config_path)
    runtime_table = _require_table(raw, "runtime")
    pipeline_table = _require_table(raw, "pipeline")
    evidence_table = _require_table(raw, "evidence")
    artifacts_table = _require_table(raw, "artifacts")
    return DocumentChunkingImplementationConfig(
        runtime=RuntimeConfig(
            app_builder=_require_string(runtime_table, "app_builder"),
            cli_command=_require_string(runtime_table, "cli_command"),
            api_prefix=_require_string(runtime_table, "api_prefix"),
            write_markdown_output=_require_bool(runtime_table, "write_markdown_output"),
            default_markdown_output=_require_string(runtime_table, "default_markdown_output"),
            write_auxiliary_output_files=_require_bool(runtime_table, "write_auxiliary_output_files"),
            paragraph_block_output_suffix=_require_string(runtime_table, "paragraph_block_output_suffix"),
            chunk_membership_output_suffix=_require_string(runtime_table, "chunk_membership_output_suffix"),
        ),
        pipeline=PipelineConfig(
            normalization_mode=_require_string(pipeline_table, "normalization_mode"),
            heading_pattern=_require_string(pipeline_table, "heading_pattern"),
            splitter=_require_string(pipeline_table, "splitter"),
            output_order=_require_string(pipeline_table, "output_order"),
            max_block_chars=_require_int(pipeline_table, "max_block_chars"),
        ),
        evidence=EvidenceConfig(
            product_spec_endpoint=_require_string(evidence_table, "product_spec_endpoint"),
            process_text_endpoint=_require_string(evidence_table, "process_text_endpoint"),
            process_file_endpoint=_require_string(evidence_table, "process_file_endpoint"),
            default_validation_input=_require_string(evidence_table, "default_validation_input"),
        ),
        artifacts=ArtifactConfig(
            framework_ir_json=_require_string(artifacts_table, "framework_ir_json"),
            product_spec_json=_require_string(artifacts_table, "product_spec_json"),
            implementation_bundle_py=_require_string(artifacts_table, "implementation_bundle_py"),
            generation_manifest_json=_require_string(artifacts_table, "generation_manifest_json"),
            governance_manifest_json=_require_string(artifacts_table, "governance_manifest_json"),
            governance_tree_json=_require_string(artifacts_table, "governance_tree_json"),
            strict_zone_report_json=_require_string(artifacts_table, "strict_zone_report_json"),
            object_coverage_report_json=_require_string(artifacts_table, "object_coverage_report_json"),
        ),
    )


def _validate_product_spec(
    metadata: ProjectMetadata,
    framework: FrameworkSelection,
    product: DocumentChunkingProduct,
    domain_ir: FrameworkModuleIR,
) -> None:
    if metadata.template != DOCUMENT_CHUNKING_TEMPLATE_ID:
        raise ValueError(f"project.template must be {DOCUMENT_CHUNKING_TEMPLATE_ID}")
    if domain_ir.module_id != "document_chunking.L1.M0":
        raise ValueError(f"framework.domain must resolve to document_chunking.L1.M0, got {domain_ir.module_id}")
    if product.segmentation.min_block_chars < 1 or product.segmentation.max_block_chars < product.segmentation.min_block_chars:
        raise ValueError("segmentation block char range is invalid")
    if tuple(product.role_judgment.allowed_roles) != ("title", "body"):
        raise ValueError("role_judgment.allowed_roles must be ['title', 'body']")
    if product.composition.group_shape != "1_title_plus_zero_or_more_body":
        raise ValueError("composition.group_shape must be 1_title_plus_zero_or_more_body")
    if product.composition.anchor_role != "title" or product.composition.member_role != "body":
        raise ValueError("composition anchor/member roles must be title/body")
    if product.output.render_medium != "markdown_document":
        raise ValueError("output.render_medium must be markdown_document")
    if product.output.document_format_field != "document_format":
        raise ValueError("output.document_format_field must be document_format")
    if product.output.document_format_value != "markdown":
        raise ValueError("output.document_format_value must be markdown")
    if product.output.document_format_scope != "document_level":
        raise ValueError("output.document_format_scope must be document_level")
    if not product.output.expose_paragraph_block_projection:
        raise ValueError("output.expose_paragraph_block_projection must be true")
    if product.output.paragraph_block_projection_name != "paragraph_block_set":
        raise ValueError("output.paragraph_block_projection_name must be paragraph_block_set")
    if product.output.paragraph_block_projection_fence_scope != "document_level":
        raise ValueError("output.paragraph_block_projection_fence_scope must be document_level")
    if not product.output.expose_chunk_membership_projection:
        raise ValueError("output.expose_chunk_membership_projection must be true")
    if product.output.chunk_membership_projection_name != "chunk_membership_set":
        raise ValueError("output.chunk_membership_projection_name must be chunk_membership_set")
    if product.output.chunk_membership_include_ordered_block_ids:
        raise ValueError("output.chunk_membership_include_ordered_block_ids must be false")
    if product.output.chunk_item_layout != "chunk_id_then_chunk_text_with_block_refs":
        raise ValueError("output.chunk_item_layout must be chunk_id_then_chunk_text_with_block_refs")
    if product.output.text_id_field != "text_id":
        raise ValueError("output.text_id_field must be text_id")
    if product.output.title_block_id_field != "title_block_id":
        raise ValueError("output.title_block_id_field must be title_block_id")
    if product.output.body_block_id_set_field != "body_block_id_set":
        raise ValueError("output.body_block_id_set_field must be body_block_id_set")
    if product.output.chunk_collection_field != "ordered_chunk_item_set":
        raise ValueError("output.chunk_collection_field must be ordered_chunk_item_set")
    if not product.output.include_paragraph_blocks:
        raise ValueError("output.include_paragraph_blocks must be true")
    if not product.output.include_trace_meta:
        raise ValueError("output.include_trace_meta must be true")
    if product.validation.max_chunk_items < 1:
        raise ValueError("validation.max_chunk_items must be positive")
    if not framework.preset:
        raise ValueError("framework.preset must be non-empty")


def _validate_implementation_config(
    implementation: DocumentChunkingImplementationConfig,
    product: DocumentChunkingProduct,
) -> None:
    if implementation.runtime.app_builder not in SUPPORTED_APP_BUILDERS:
        raise ValueError(f"unsupported runtime.app_builder: {implementation.runtime.app_builder}")
    if implementation.pipeline.normalization_mode not in SUPPORTED_NORMALIZATION_MODES:
        raise ValueError(f"unsupported pipeline.normalization_mode: {implementation.pipeline.normalization_mode}")
    if implementation.pipeline.splitter not in SUPPORTED_SPLITTERS:
        raise ValueError(f"unsupported pipeline.splitter: {implementation.pipeline.splitter}")
    if implementation.pipeline.output_order not in SUPPORTED_OUTPUT_ORDERS:
        raise ValueError(f"unsupported pipeline.output_order: {implementation.pipeline.output_order}")
    if implementation.pipeline.max_block_chars != product.segmentation.max_block_chars:
        raise ValueError("pipeline.max_block_chars must equal product segmentation.max_block_chars")
    if implementation.pipeline.max_block_chars < 1:
        raise ValueError("pipeline.max_block_chars must be positive")
    if not implementation.runtime.api_prefix.startswith("/"):
        raise ValueError("runtime.api_prefix must start with '/'")
    if not implementation.runtime.default_markdown_output.endswith(".md"):
        raise ValueError("runtime.default_markdown_output must end with .md")
    if not implementation.runtime.paragraph_block_output_suffix.endswith(".md"):
        raise ValueError("runtime.paragraph_block_output_suffix must end with .md")
    if not implementation.runtime.chunk_membership_output_suffix.endswith(".md"):
        raise ValueError("runtime.chunk_membership_output_suffix must end with .md")
    for endpoint in (
        implementation.evidence.product_spec_endpoint,
        implementation.evidence.process_text_endpoint,
        implementation.evidence.process_file_endpoint,
    ):
        if not endpoint.startswith("/"):
            raise ValueError(f"endpoint must start with '/': {endpoint}")


def _effective_generated_artifacts(project: DocumentChunkingProject) -> GeneratedArtifactPaths:
    if project.generated_artifacts is not None:
        return project.generated_artifacts

    generated_dir = Path(project.product_spec_file).parent / "generated"
    artifacts = project.implementation.artifacts
    return GeneratedArtifactPaths(
        directory=_relative_path(generated_dir),
        framework_ir_json=_relative_path(generated_dir / artifacts.framework_ir_json),
        product_spec_json=_relative_path(generated_dir / artifacts.product_spec_json),
        implementation_bundle_py=_relative_path(generated_dir / artifacts.implementation_bundle_py),
        generation_manifest_json=_relative_path(generated_dir / artifacts.generation_manifest_json),
        governance_manifest_json=_relative_path(generated_dir / artifacts.governance_manifest_json),
        governance_tree_json=_relative_path(generated_dir / artifacts.governance_tree_json),
        strict_zone_report_json=_relative_path(generated_dir / artifacts.strict_zone_report_json),
        object_coverage_report_json=_relative_path(generated_dir / artifacts.object_coverage_report_json),
    )


def build_implementation_effect_manifest(project: DocumentChunkingProject) -> dict[str, dict[str, Any]]:
    generated_artifacts = _effective_generated_artifacts(project)
    return {
        "runtime.app_builder": {
            "value": project.implementation.runtime.app_builder,
            "relation": "equals",
            "targets": ["runtime_contract.app_builder"],
        },
        "runtime.cli_command": {
            "value": project.implementation.runtime.cli_command,
            "relation": "equals",
            "targets": ["runtime_contract.cli_command"],
        },
        "runtime.write_markdown_output": {
            "value": project.implementation.runtime.write_markdown_output,
            "relation": "equals",
            "targets": ["runtime_contract.write_markdown_output"],
        },
        "runtime.default_markdown_output": {
            "value": project.implementation.runtime.default_markdown_output,
            "relation": "equals",
            "targets": ["runtime_contract.default_markdown_output"],
        },
        "runtime.write_auxiliary_output_files": {
            "value": project.implementation.runtime.write_auxiliary_output_files,
            "relation": "equals",
            "targets": ["runtime_contract.write_auxiliary_output_files"],
        },
        "runtime.paragraph_block_output_suffix": {
            "value": project.implementation.runtime.paragraph_block_output_suffix,
            "relation": "equals",
            "targets": ["runtime_contract.paragraph_block_output_suffix"],
        },
        "runtime.chunk_membership_output_suffix": {
            "value": project.implementation.runtime.chunk_membership_output_suffix,
            "relation": "equals",
            "targets": ["runtime_contract.chunk_membership_output_suffix"],
        },
        "runtime.api_prefix": {
            "value": project.implementation.runtime.api_prefix,
            "relation": "equals",
            "targets": ["runtime_contract.api_prefix"],
        },
        "pipeline.normalization_mode": {
            "value": project.implementation.pipeline.normalization_mode,
            "relation": "equals",
            "targets": ["pipeline_contract.normalization_mode"],
        },
        "pipeline.heading_pattern": {
            "value": project.implementation.pipeline.heading_pattern,
            "relation": "equals",
            "targets": ["pipeline_contract.heading_pattern"],
        },
        "pipeline.splitter": {
            "value": project.implementation.pipeline.splitter,
            "relation": "equals",
            "targets": ["pipeline_contract.splitter"],
        },
        "pipeline.output_order": {
            "value": project.implementation.pipeline.output_order,
            "relation": "equals",
            "targets": ["pipeline_contract.output_order"],
        },
        "pipeline.max_block_chars": {
            "value": project.implementation.pipeline.max_block_chars,
            "relation": "equals",
            "targets": ["pipeline_contract.max_block_chars"],
        },
        "evidence.product_spec_endpoint": {
            "value": project.implementation.evidence.product_spec_endpoint,
            "relation": "equals",
            "targets": ["runtime_contract.product_spec_endpoint"],
        },
        "evidence.process_text_endpoint": {
            "value": project.implementation.evidence.process_text_endpoint,
            "relation": "equals",
            "targets": ["runtime_contract.process_text_endpoint"],
        },
        "evidence.process_file_endpoint": {
            "value": project.implementation.evidence.process_file_endpoint,
            "relation": "equals",
            "targets": ["runtime_contract.process_file_endpoint"],
        },
        "evidence.default_validation_input": {
            "value": project.implementation.evidence.default_validation_input,
            "relation": "equals",
            "targets": ["runtime_contract.default_validation_input"],
        },
        "artifacts.framework_ir_json": {
            "value": project.implementation.artifacts.framework_ir_json,
            "relation": "basename",
            "targets": ["generated_artifacts.framework_ir_json"],
        },
        "artifacts.product_spec_json": {
            "value": project.implementation.artifacts.product_spec_json,
            "relation": "basename",
            "targets": ["generated_artifacts.product_spec_json"],
        },
        "artifacts.implementation_bundle_py": {
            "value": project.implementation.artifacts.implementation_bundle_py,
            "relation": "basename",
            "targets": ["generated_artifacts.implementation_bundle_py"],
        },
        "artifacts.generation_manifest_json": {
            "value": project.implementation.artifacts.generation_manifest_json,
            "relation": "basename",
            "targets": ["generated_artifacts.generation_manifest_json"],
        },
        "artifacts.governance_manifest_json": {
            "value": project.implementation.artifacts.governance_manifest_json,
            "relation": "basename",
            "targets": ["generated_artifacts.governance_manifest_json"],
        },
        "artifacts.governance_tree_json": {
            "value": project.implementation.artifacts.governance_tree_json,
            "relation": "basename",
            "targets": ["generated_artifacts.governance_tree_json"],
        },
        "artifacts.strict_zone_report_json": {
            "value": project.implementation.artifacts.strict_zone_report_json,
            "relation": "basename",
            "targets": ["generated_artifacts.strict_zone_report_json"],
        },
        "artifacts.object_coverage_report_json": {
            "value": project.implementation.artifacts.object_coverage_report_json,
            "relation": "basename",
            "targets": ["generated_artifacts.object_coverage_report_json"],
        },
    }


def _build_expected_artifacts(project: DocumentChunkingProject) -> dict[str, Any]:
    return {
        "generated_files": _effective_generated_artifacts(project).to_dict(),
        "api_endpoints": {
            "product_spec": project.implementation.evidence.product_spec_endpoint,
            "process_text": project.implementation.evidence.process_text_endpoint,
            "process_file": project.implementation.evidence.process_file_endpoint,
        },
    }


def build_governance_closure(project: DocumentChunkingProject) -> ProjectGovernanceClosure:
    generated_artifacts = _effective_generated_artifacts(project)
    evidence_artifacts = {
        "framework_ir_json": generated_artifacts.framework_ir_json,
        "product_spec_json": generated_artifacts.product_spec_json,
        "implementation_bundle_py": generated_artifacts.implementation_bundle_py,
        "generation_manifest_json": generated_artifacts.generation_manifest_json,
        "governance_manifest_json": generated_artifacts.governance_manifest_json,
        "governance_tree_json": generated_artifacts.governance_tree_json,
        "strict_zone_report_json": generated_artifacts.strict_zone_report_json,
        "object_coverage_report_json": generated_artifacts.object_coverage_report_json,
    }
    expected_artifacts = _build_expected_artifacts(project)
    expected_fingerprint = fingerprint(expected_artifacts)
    structural_objects = (
        StructuralObject(
            object_id="document_chunking.pipeline",
            project_id=project.metadata.project_id,
            kind="runtime_pipeline",
            title="Document Chunking Pipeline",
            risk_level="high",
            cardinality="1",
            status="implemented",
            semantic={
                "group_shape": project.product.composition.group_shape,
                "allowed_roles": list(project.product.role_judgment.allowed_roles),
                "document_format_scope": project.product.output.document_format_scope,
                "paragraph_block_projection_name": project.product.output.paragraph_block_projection_name,
                "paragraph_block_projection_fence_scope": project.product.output.paragraph_block_projection_fence_scope,
                "chunk_membership_projection_name": project.product.output.chunk_membership_projection_name,
                "chunk_membership_include_ordered_block_ids": project.product.output.chunk_membership_include_ordered_block_ids,
                "output_fields": {
                    "document_format": project.product.output.document_format_field,
                    "text_id": project.product.output.text_id_field,
                    "chunk_id": project.product.output.chunk_id_field,
                    "chunk_text": project.product.output.chunk_text_field,
                    "title_block_id": project.product.output.title_block_id_field,
                    "body_block_id_set": project.product.output.body_block_id_set_field,
                },
            },
            required_roles=(
                RequiredRole(
                    role_id="pipeline_runner",
                    role_kind="builder",
                    description="pipeline entry that composes paragraph blocks into text chunks",
                    candidate_kinds=("python_builder", "python_behavior_orchestrator"),
                    locator_patterns=("function:run_document_chunking_pipeline",),
                    file_hints=("src/document_chunking_runtime/pipeline.py",),
                ),
                RequiredRole(
                    role_id="pipeline_validator",
                    role_kind="validator",
                    description="validation closure for chunking outputs",
                    candidate_kinds=("python_builder", "python_evidence_builder"),
                    locator_patterns=("function:validate_document_chunking_result",),
                    file_hints=("src/document_chunking_runtime/pipeline.py",),
                ),
            ),
            sources_framework=(
                SourceRef("framework", project.framework.domain, "module", project.domain_ir.module_id),
                SourceRef("framework", project.framework.domain, "rule", "R1"),
                SourceRef("framework", project.framework.domain, "rule", "R4"),
            ),
            sources_product=(
                SourceRef("product", project.product_spec_file, "table", "composition"),
                SourceRef("product", project.product_spec_file, "table", "output"),
                SourceRef("product", project.product_spec_file, "table", "validation"),
            ),
            sources_implementation=(
                SourceRef("implementation", project.implementation_config_file, "table", "pipeline"),
            ),
            expected_evidence=expected_artifacts,
            expected_fingerprint=expected_fingerprint,
            actual_evidence=expected_artifacts,
            actual_fingerprint=expected_fingerprint,
            comparator="canonical_json_equals",
            extractor="document_chunking_runtime.pipeline.run_document_chunking_pipeline",
            origin_categories=("framework", "product", "implementation"),
        ),
        StructuralObject(
            object_id="document_chunking.api",
            project_id=project.metadata.project_id,
            kind="runtime_api",
            title="Document Chunking API",
            risk_level="high",
            cardinality="1",
            status="implemented",
            semantic={
                "api_prefix": project.implementation.runtime.api_prefix,
                "process_file_endpoint": project.implementation.evidence.process_file_endpoint,
                "process_text_endpoint": project.implementation.evidence.process_text_endpoint,
            },
            required_roles=(
                RequiredRole(
                    role_id="api_builder",
                    role_kind="route_builder",
                    description="FastAPI application builder for document chunking",
                    candidate_kinds=("python_route_builder", "python_builder"),
                    locator_patterns=("function:build_document_chunking_app",),
                    file_hints=("src/document_chunking_runtime/app.py",),
                ),
                RequiredRole(
                    role_id="project_loader",
                    role_kind="loader",
                    description="project loader for the document chunking template",
                    candidate_kinds=("python_builder",),
                    locator_patterns=("function:load_document_chunking_project",),
                    file_hints=("src/project_runtime/document_chunking.py",),
                ),
            ),
            sources_framework=(
                SourceRef("framework", project.framework.domain, "boundary", "OUTPUT"),
            ),
            sources_product=(
                SourceRef("product", project.product_spec_file, "table", "validation"),
            ),
            sources_implementation=(
                SourceRef("implementation", project.implementation_config_file, "table", "runtime"),
                SourceRef("implementation", project.implementation_config_file, "table", "evidence"),
            ),
            expected_evidence={
                "api_prefix": project.implementation.runtime.api_prefix,
                "cli_command": project.implementation.runtime.cli_command,
            },
            expected_fingerprint=fingerprint(
                {
                    "api_prefix": project.implementation.runtime.api_prefix,
                    "cli_command": project.implementation.runtime.cli_command,
                }
            ),
            actual_evidence={
                "api_prefix": project.implementation.runtime.api_prefix,
                "cli_command": project.implementation.runtime.cli_command,
            },
            actual_fingerprint=fingerprint(
                {
                    "api_prefix": project.implementation.runtime.api_prefix,
                    "cli_command": project.implementation.runtime.cli_command,
                }
            ),
            comparator="canonical_json_equals",
            extractor="document_chunking_runtime.app.build_document_chunking_app",
            origin_categories=("framework", "implementation"),
        ),
        StructuralObject(
            object_id="document_chunking.evidence",
            project_id=project.metadata.project_id,
            kind="generated_evidence",
            title="Document Chunking Generated Evidence",
            risk_level="medium",
            cardinality="1",
            status="implemented",
            semantic={"artifact_directory": generated_artifacts.directory},
            required_roles=(
                RequiredRole(
                    role_id="materializer",
                    role_kind="evidence_builder",
                    description="materializes generated evidence artifacts for the project",
                    candidate_kinds=("python_evidence_builder", "python_builder"),
                    locator_patterns=("function:materialize_document_chunking_project",),
                    file_hints=("src/project_runtime/document_chunking.py",),
                ),
            ),
            sources_framework=(
                SourceRef("framework", project.framework.domain, "rule", "R4"),
            ),
            sources_product=(
                SourceRef("product", project.product_spec_file, "table", "output"),
            ),
            sources_implementation=(
                SourceRef("implementation", project.implementation_config_file, "table", "artifacts"),
            ),
            expected_evidence=generated_artifacts.to_dict(),
            expected_fingerprint=fingerprint(generated_artifacts.to_dict()),
            actual_evidence=generated_artifacts.to_dict(),
            actual_fingerprint=fingerprint(generated_artifacts.to_dict()),
            comparator="canonical_json_equals",
            extractor="project_runtime.document_chunking.materialize_document_chunking_project",
            origin_categories=("framework", "implementation"),
        ),
    )
    search_roots = (
        REPO_ROOT / "src/document_chunking_runtime",
        REPO_ROOT / "src/project_runtime/document_chunking.py",
        REPO_ROOT / "src/main.py",
    )
    candidates = scan_python_structural_candidates(
        project_id=project.metadata.project_id,
        search_roots=search_roots,
    )
    role_bindings = resolve_role_bindings(structural_objects, candidates)
    classified_candidates = classify_candidates(structural_objects, candidates, role_bindings)
    strict_zone = annotate_strict_zone_minimality(
        infer_strict_zone(structural_objects, role_bindings, classified_candidates, evidence_artifacts),
        role_bindings,
        classified_candidates,
        evidence_artifacts,
    )
    upstream_closure = (
        tuple(
            SourceRef("framework", module.path, "rule", rule.rule_id)
            for module in project.resolved_modules
            for rule in module.rules
        )
        + tuple(
            SourceRef("product_spec", project.product_spec_file, "section", section_name)
            for section_name in (
                "framework",
                "input",
                "segmentation",
                "role_judgment",
                "composition",
                "output",
                "validation",
            )
        )
        + tuple(
            SourceRef("implementation_config", project.implementation_config_file, "section", section_name)
            for section_name in ("runtime", "pipeline", "evidence", "artifacts")
        )
    )
    return ProjectGovernanceClosure(
        project_id=project.metadata.project_id,
        template_id=project.metadata.template,
        product_spec_file=project.product_spec_file,
        implementation_config_file=project.implementation_config_file,
        discovery=FrameworkDrivenProjectRecord(
            project_id=project.metadata.project_id,
            template_id=project.metadata.template,
            product_spec_file=project.product_spec_file,
            implementation_config_file=project.implementation_config_file,
            generated_dir=generated_artifacts.directory,
            discovery_reasons=(
                "project spec exists under projects/<project_id>/product_spec.toml",
                "implementation_config.toml exists beside product_spec.toml",
                f"registered template resolved: {project.metadata.template}",
                "project loads through the registered framework-driven materialization chain",
                "framework selections resolve to concrete framework modules",
                "implementation_config defines generated artifact evidence contract",
            ),
            framework_refs=tuple(item.path for item in project.resolved_modules),
            artifact_contract=tuple(project.implementation.artifacts.to_dict().values()),
        ),
        structural_objects=structural_objects,
        candidates=classified_candidates,
        role_bindings=role_bindings,
        strict_zone=strict_zone,
        upstream_closure=upstream_closure,
        evidence_artifacts=evidence_artifacts,
    )


def build_document_chunking_governance_manifest(project: DocumentChunkingProject) -> dict[str, Any]:
    closure = build_governance_closure(project)
    strict_zone_report = build_strict_zone_report(closure)
    object_coverage_report = build_object_coverage_report(closure)
    return {
        "manifest_version": "governance-manifest/v1",
        "project_id": project.metadata.project_id,
        "template_id": project.metadata.template,
        "generator_version": "project_runtime.document_chunking/v1",
        "project_discovery": closure.discovery.to_dict(),
        "upstream_closure": [_serialize_upstream_ref(item) for item in closure.upstream_closure],
        "structural_objects": [item.to_manifest_dict() for item in closure.structural_objects],
        "role_bindings": [item.to_dict() for item in closure.role_bindings],
        "strict_zone": [item.to_dict() for item in closure.strict_zone],
        "strict_zone_report": strict_zone_report,
        "candidates": [item.to_dict() for item in closure.candidates],
        "object_coverage_report": object_coverage_report,
        "evidence_artifacts": closure.evidence_artifacts,
    }


def _build_document_chunking_governance_nodes(
    project: DocumentChunkingProject,
    closure: ProjectGovernanceClosure,
) -> list[dict[str, Any]]:
    root_id = f"project:{closure.project_id}"
    framework_root_id = f"{root_id}:framework"
    product_root_id = f"{root_id}:product_spec"
    implementation_root_id = f"{root_id}:implementation_config"
    structure_root_id = f"{root_id}:structure"
    code_root_id = f"{root_id}:code"
    evidence_root_id = f"{root_id}:evidence"
    nodes: list[dict[str, Any]] = [
        {
            "node_id": root_id,
            "parent": None,
            "children": [
                framework_root_id,
                product_root_id,
                implementation_root_id,
                structure_root_id,
                code_root_id,
                evidence_root_id,
            ],
            "kind": "project_root",
            "layer": "Project",
            "title": project.metadata.display_name,
            "file": project.product_spec_file,
            "template_id": project.metadata.template,
            "project_id": project.metadata.project_id,
        },
        {
            "node_id": framework_root_id,
            "parent": root_id,
            "children": [],
            "kind": "framework_root",
            "layer": "Framework",
            "title": "Framework",
            "file": project.framework.domain,
        },
        {
            "node_id": product_root_id,
            "parent": root_id,
            "children": [],
            "kind": "product_spec_root",
            "layer": "Product Spec",
            "title": "Product Spec",
            "file": project.product_spec_file,
        },
        {
            "node_id": implementation_root_id,
            "parent": root_id,
            "children": [],
            "kind": "implementation_root",
            "layer": "Implementation Config",
            "title": "Implementation Config",
            "file": project.implementation_config_file,
        },
        {
            "node_id": structure_root_id,
            "parent": root_id,
            "children": [],
            "kind": "structure_root",
            "layer": "Structure",
            "title": "Structure",
            "file": project.product_spec_file,
        },
        {
            "node_id": code_root_id,
            "parent": root_id,
            "children": [],
            "kind": "code_root",
            "layer": "Code",
            "title": "Code",
            "file": project.implementation_config_file,
        },
        {
            "node_id": evidence_root_id,
            "parent": root_id,
            "children": [],
            "kind": "evidence_root",
            "layer": "Evidence",
            "title": "Evidence",
            "file": project.implementation_config_file,
        },
    ]
    node_index = {node["node_id"]: node for node in nodes}

    def append_child(parent_id: str, node: dict[str, Any]) -> None:
        node_index[parent_id]["children"].append(node["node_id"])
        nodes.append(node)
        node_index[node["node_id"]] = node

    for section_name in (
        "framework",
        "input",
        "segmentation",
        "role_judgment",
        "composition",
        "output",
        "validation",
    ):
        append_child(
            product_root_id,
            {
                "node_id": f"{product_root_id}:section:{section_name}",
                "parent": product_root_id,
                "children": [],
                "kind": "product_section",
                "layer": "Product Spec",
                "title": section_name,
                "file": project.product_spec_file,
                "ref_id": section_name,
            },
        )

    for section_name in ("runtime", "pipeline", "evidence", "artifacts"):
        append_child(
            implementation_root_id,
            {
                "node_id": f"{implementation_root_id}:section:{section_name}",
                "parent": implementation_root_id,
                "children": [],
                "kind": "implementation_section",
                "layer": "Implementation Config",
                "title": section_name,
                "file": project.implementation_config_file,
                "ref_id": section_name,
            },
        )

    seen_framework_files: set[str] = set()
    for source in closure.upstream_closure:
        if source.file in seen_framework_files:
            continue
        seen_framework_files.add(source.file)
        append_child(
            framework_root_id,
            {
                "node_id": f"{framework_root_id}:file:{source.file}",
                "parent": framework_root_id,
                "children": [],
                "kind": "framework_source",
                "layer": "Framework",
                "title": Path(source.file).name,
                "file": source.file,
            },
        )

    for structural_object in closure.structural_objects:
        append_child(
            structure_root_id,
            {
                "node_id": f"{structure_root_id}:object:{structural_object.object_id}",
                "parent": structure_root_id,
                "children": [],
                "kind": "structural_object",
                "layer": "Structure",
                "title": structural_object.title,
                "file": project.product_spec_file,
                "object_id": structural_object.object_id,
            },
        )

    for strict_zone_entry in closure.strict_zone:
        append_child(
            code_root_id,
            {
                "node_id": f"{code_root_id}:file:{strict_zone_entry.file}",
                "parent": code_root_id,
                "children": [],
                "kind": "strict_zone_file",
                "layer": "Code",
                "title": Path(strict_zone_entry.file).name,
                "file": strict_zone_entry.file,
                "object_ids": list(strict_zone_entry.object_ids),
                "role_ids": list(strict_zone_entry.role_ids),
                "reasons": list(strict_zone_entry.reasons),
                "why_required": list(strict_zone_entry.why_required),
                "minimality_status": strict_zone_entry.minimality_status,
                "project_id": closure.project_id,
            },
        )

    for artifact_name, artifact_path in sorted(closure.evidence_artifacts.items()):
        append_child(
            evidence_root_id,
            {
                "node_id": f"{evidence_root_id}:artifact:{artifact_name}",
                "parent": evidence_root_id,
                "children": [],
                "kind": "evidence_artifact",
                "layer": "Evidence",
                "title": artifact_name,
                "file": artifact_path,
                "artifact": artifact_name,
            },
        )

    return nodes


def build_document_chunking_governance_tree(project: DocumentChunkingProject) -> dict[str, Any]:
    closure = build_governance_closure(project)
    strict_zone_report = build_strict_zone_report(closure)
    object_coverage_report = build_object_coverage_report(closure)
    root_node_id = f"project:{closure.project_id}"
    return {
        "tree_version": "governance-tree/v1",
        "project_id": project.metadata.project_id,
        "template_id": project.metadata.template,
        "generator_version": "project_runtime.document_chunking/v1",
        "root_node_id": root_node_id,
        "project_discovery": closure.discovery.to_dict(),
        "upstream_closure": [_serialize_upstream_ref(item) for item in closure.upstream_closure],
        "strict_zone": [item.to_dict() for item in closure.strict_zone],
        "strict_zone_report": strict_zone_report,
        "object_coverage_report": object_coverage_report,
        "structural_objects": [item.to_manifest_dict() for item in closure.structural_objects],
        "role_bindings": [item.to_dict() for item in closure.role_bindings],
        "candidates": [item.to_dict() for item in closure.candidates],
        "nodes": _build_document_chunking_governance_nodes(project, closure),
        "evidence_artifacts": closure.evidence_artifacts,
    }


def _build_generated_artifact_payloads(project: DocumentChunkingProject) -> dict[str, str]:
    generated_artifacts = project.generated_artifacts
    if generated_artifacts is None:
        raise ValueError("generated_artifacts must be populated before payload generation")

    framework_ir_payload = {
        "primary_modules": [project.domain_ir.to_dict()],
        "resolved_modules": [item.to_dict() for item in project.resolved_modules],
    }
    framework_ir_text = json.dumps(framework_ir_payload, ensure_ascii=False, indent=2)
    product_spec_text = json.dumps(project.to_product_spec_dict(), ensure_ascii=False, indent=2)
    runtime_bundle = project.to_runtime_bundle_dict()
    implementation_bundle_text = "\n".join(
        [
            "from __future__ import annotations",
            "",
            "# GENERATED FILE. DO NOT EDIT.",
            "# Change framework markdown, product_spec.toml, or implementation_config.toml, then re-materialize.",
            "",
            "import json",
            "",
            f"PRODUCT_SPEC = json.loads(r'''{json.dumps(project.to_product_spec_dict(), ensure_ascii=False)}''')",
            f"IMPLEMENTATION_CONFIG = json.loads(r'''{json.dumps(project.implementation.to_dict(), ensure_ascii=False)}''')",
            f"RUNTIME_BUNDLE = json.loads(r'''{json.dumps(runtime_bundle, ensure_ascii=False)}''')",
            "",
        ]
    )
    governance_manifest_text = json.dumps(
        build_document_chunking_governance_manifest(project),
        ensure_ascii=False,
        indent=2,
    )
    governance_tree_text = json.dumps(
        build_document_chunking_governance_tree(project),
        ensure_ascii=False,
        indent=2,
    )
    strict_zone_report_text = json.dumps(
        build_strict_zone_report(build_governance_closure(project)),
        ensure_ascii=False,
        indent=2,
    )
    object_coverage_report_text = json.dumps(
        build_object_coverage_report(build_governance_closure(project)),
        ensure_ascii=False,
        indent=2,
    )
    generation_manifest_text = json.dumps(
        {
            "project_id": project.metadata.project_id,
            "template": project.metadata.template,
            "product_spec_file": project.product_spec_file,
            "implementation_config_file": project.implementation_config_file,
            "generator": {
                "entry": "project_runtime.document_chunking.materialize_document_chunking_project",
                "discipline": (
                    "project behavior is derived from framework markdown, product spec, and implementation config; "
                    "generated code must not be edited directly"
                ),
            },
            "framework_inputs": {
                "domain": project.domain_ir.path,
                "resolved_modules": [item.path for item in project.resolved_modules],
            },
            "configuration_effects": build_implementation_effect_manifest(project),
            "generated_files": generated_artifacts.to_dict(),
            "content_sha256": {
                "framework_ir_json": _sha256_text(framework_ir_text),
                "product_spec_json": _sha256_text(product_spec_text),
                "implementation_bundle_py": _sha256_text(implementation_bundle_text),
                "governance_manifest_json": _sha256_text(governance_manifest_text),
                "governance_tree_json": _sha256_text(governance_tree_text),
                "strict_zone_report_json": _sha256_text(strict_zone_report_text),
                "object_coverage_report_json": _sha256_text(object_coverage_report_text),
            },
        },
        ensure_ascii=False,
        indent=2,
    )
    return {
        "framework_ir_json": framework_ir_text,
        "product_spec_json": product_spec_text,
        "implementation_bundle_py": implementation_bundle_text,
        "generation_manifest_json": generation_manifest_text,
        "governance_manifest_json": governance_manifest_text,
        "governance_tree_json": governance_tree_text,
        "strict_zone_report_json": strict_zone_report_text,
        "object_coverage_report_json": object_coverage_report_text,
    }


def _compile_project(
    metadata: ProjectMetadata,
    framework: FrameworkSelection,
    product: DocumentChunkingProduct,
    implementation: DocumentChunkingImplementationConfig,
    *,
    product_spec_file: str,
    implementation_config_file: str,
) -> DocumentChunkingProject:
    domain_ir = _resolve_framework_module(framework.domain)
    _validate_product_spec(metadata, framework, product, domain_ir)
    _validate_implementation_config(implementation, product)
    return DocumentChunkingProject(
        repo_root=_relative_path(REPO_ROOT),
        product_spec_file=product_spec_file,
        implementation_config_file=implementation_config_file,
        metadata=metadata,
        framework=framework,
        product=product,
        implementation=implementation,
        domain_ir=domain_ir,
        resolved_modules=_collect_framework_closure(domain_ir),
    )


def load_document_chunking_project(
    product_spec_file: str | Path = DEFAULT_DOCUMENT_CHUNKING_PRODUCT_SPEC_FILE,
) -> DocumentChunkingProject:
    product_spec_path = _normalize_project_path(product_spec_file)
    assert_supported_project_template(product_spec_path)
    implementation_config_path = _implementation_config_path_for(product_spec_path)
    metadata, framework, product = _load_product_spec(product_spec_path)
    implementation = _load_implementation_config(implementation_config_path)
    return _compile_project(
        metadata,
        framework,
        product,
        implementation,
        product_spec_file=_relative_path(product_spec_path),
        implementation_config_file=_relative_path(implementation_config_path),
    )


def materialize_document_chunking_project(
    product_spec_file: str | Path = DEFAULT_DOCUMENT_CHUNKING_PRODUCT_SPEC_FILE,
    output_dir: str | Path | None = None,
) -> DocumentChunkingProject:
    product_spec_path = _normalize_project_path(product_spec_file)
    assert_supported_project_template(product_spec_path)
    project = load_document_chunking_project(product_spec_path)
    generated_dir = product_spec_path.parent / "generated"
    output_path = _normalize_project_path(output_dir) if output_dir is not None else generated_dir
    output_path.mkdir(parents=True, exist_ok=True)

    artifact_names = project.implementation.artifacts
    expected_file_names = set(project.implementation.artifacts.to_dict().values())
    _cleanup_generated_output_dir(output_path, expected_file_names)

    artifact_directory = generated_dir
    project = replace(
        project,
        generated_artifacts=GeneratedArtifactPaths(
            directory=_relative_path(artifact_directory),
            framework_ir_json=_relative_path(artifact_directory / artifact_names.framework_ir_json),
            product_spec_json=_relative_path(artifact_directory / artifact_names.product_spec_json),
            implementation_bundle_py=_relative_path(artifact_directory / artifact_names.implementation_bundle_py),
            generation_manifest_json=_relative_path(artifact_directory / artifact_names.generation_manifest_json),
            governance_manifest_json=_relative_path(artifact_directory / artifact_names.governance_manifest_json),
            governance_tree_json=_relative_path(artifact_directory / artifact_names.governance_tree_json),
            strict_zone_report_json=_relative_path(artifact_directory / artifact_names.strict_zone_report_json),
            object_coverage_report_json=_relative_path(artifact_directory / artifact_names.object_coverage_report_json),
        ),
    )
    payloads = _build_generated_artifact_payloads(project)
    (output_path / artifact_names.framework_ir_json).write_text(payloads["framework_ir_json"], encoding="utf-8")
    (output_path / artifact_names.product_spec_json).write_text(payloads["product_spec_json"], encoding="utf-8")
    (output_path / artifact_names.implementation_bundle_py).write_text(
        payloads["implementation_bundle_py"],
        encoding="utf-8",
    )
    (output_path / artifact_names.generation_manifest_json).write_text(
        payloads["generation_manifest_json"],
        encoding="utf-8",
    )
    (output_path / artifact_names.governance_manifest_json).write_text(
        payloads["governance_manifest_json"],
        encoding="utf-8",
    )
    (output_path / artifact_names.governance_tree_json).write_text(
        payloads["governance_tree_json"],
        encoding="utf-8",
    )
    (output_path / artifact_names.strict_zone_report_json).write_text(
        payloads["strict_zone_report_json"],
        encoding="utf-8",
    )
    (output_path / artifact_names.object_coverage_report_json).write_text(
        payloads["object_coverage_report_json"],
        encoding="utf-8",
    )
    return project


def build_document_chunking_runtime_app_from_spec(
    product_spec_file: str | Path = DEFAULT_DOCUMENT_CHUNKING_PRODUCT_SPEC_FILE,
) -> Any:
    from document_chunking_runtime.app import build_document_chunking_app

    project = materialize_document_chunking_project(product_spec_file)
    return build_document_chunking_app(project)


def _resolve_runtime_output_anchor(
    project: DocumentChunkingProject,
    output_file: str | Path | None,
) -> Path:
    resolved_output_file = Path(output_file or project.implementation.runtime.default_markdown_output)
    if not resolved_output_file.is_absolute():
        resolved_output_file = (REPO_ROOT / resolved_output_file).resolve()
    resolved_output_file.parent.mkdir(parents=True, exist_ok=True)
    return resolved_output_file


def _derive_auxiliary_output_path(anchor_file: Path, suffix: str) -> Path:
    resolved_path = anchor_file.with_name(f"{anchor_file.stem}{suffix}")
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    return resolved_path


def _render_paragraph_block_projection_markdown(
    *,
    document_name: str,
    text_id: str,
    projection_name: str,
    projection_fence_scope: str,
    paragraph_blocks: list[dict[str, Any]],
) -> str:
    if projection_fence_scope != "document_level":
        raise ValueError(f"unsupported paragraph_block_projection_fence_scope: {projection_fence_scope}")

    lines = [
        "```markdown",
        f"document_name: {document_name}",
        f"text_id: {text_id}",
        f"projection_name: {projection_name}",
        "",
    ]
    for block in paragraph_blocks:
        lines.append(f"block_id: {block['block_id']}")
        lines.append(f"order_index: {block['order_index']}")
        lines.append(f"start_offset: {block['start_offset']}")
        lines.append(f"end_offset: {block['end_offset']}")
        lines.append(f"document_id: {block['document_id']}")
        lines.append(f"is_document_end: {str(block['is_document_end']).lower()}")
        lines.append("text:")
        lines.extend(str(block["text"]).splitlines())
        lines.append("")
    lines.append("```")
    return "\n".join(lines).rstrip() + "\n"


def _render_chunk_membership_projection_markdown(
    *,
    document_name: str,
    text_id: str,
    projection_name: str,
    include_ordered_block_ids: bool,
    chunk_matches: list[dict[str, Any]],
) -> str:
    lines = [
        f"document_name: {document_name}",
        f"text_id: {text_id}",
        f"projection_name: {projection_name}",
        "",
    ]
    for chunk_match in chunk_matches:
        lines.append(f"chunk_id: {chunk_match['chunk_id']}")
        lines.append(f"text_chunk_id: {chunk_match['text_chunk_id']}")
        lines.append(f"title_block_id: {chunk_match['title_block_id']}")
        lines.append("body_block_id_set:")
        for item in chunk_match["body_block_id_set"]:
            lines.append(f"- {item}")
        if include_ordered_block_ids:
            lines.append("ordered_block_id_set:")
            for item in chunk_match["ordered_block_id_set"]:
                lines.append(f"- {item}")
        lines.append(f"start_order: {chunk_match['start_order']}")
        lines.append(f"end_order: {chunk_match['end_order']}")
        lines.append(f"closure_reason: {chunk_match['closure_reason']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_document_chunking_auxiliary_outputs(
    *,
    product_spec_file: str | Path = DEFAULT_DOCUMENT_CHUNKING_PRODUCT_SPEC_FILE,
    result: dict[str, Any],
    output_file: str | Path | None = None,
) -> dict[str, str]:
    project = load_document_chunking_project(product_spec_file)
    anchor_file = _resolve_runtime_output_anchor(project, output_file)
    written_files: dict[str, str] = {}

    if project.product.output.expose_paragraph_block_projection:
        paragraph_block_output_path = _derive_auxiliary_output_path(
            anchor_file,
            project.implementation.runtime.paragraph_block_output_suffix,
        )
        paragraph_blocks = [dict(item) for item in result["paragraph_block_set"]]
        paragraph_block_payload = {
            "document_name": str(result["document_name"]),
            "text_id": str(result["output"]["text_id"]),
            project.product.output.paragraph_block_projection_name: paragraph_blocks,
        }
        paragraph_block_output_path.write_text(
            _render_paragraph_block_projection_markdown(
                document_name=str(paragraph_block_payload["document_name"]),
                text_id=str(paragraph_block_payload["text_id"]),
                projection_name=project.product.output.paragraph_block_projection_name,
                projection_fence_scope=project.product.output.paragraph_block_projection_fence_scope,
                paragraph_blocks=paragraph_blocks,
            ),
            encoding="utf-8",
        )
        written_files["paragraph_block_output_file"] = _relative_path(paragraph_block_output_path)

    if project.product.output.expose_chunk_membership_projection:
        chunk_membership_output_path = _derive_auxiliary_output_path(
            anchor_file,
            project.implementation.runtime.chunk_membership_output_suffix,
        )
        chunk_matches: list[dict[str, Any]] = [
            {
                "chunk_id": int(item["chunk_id"]),
                "text_chunk_id": str(item["text_chunk_id"]),
                "title_block_id": str(item["title_block_id"]),
                "body_block_id_set": [str(value) for value in item["body_block_id_set"]],
                "ordered_block_id_set": [str(value) for value in item["ordered_block_id_set"]],
                "start_order": int(item["start_order"]),
                "end_order": int(item["end_order"]),
                "closure_reason": str(item["closure_reason"]),
            }
            for item in result["chunk_match_set"]
        ]
        chunk_membership_payload = {
            "document_name": str(result["document_name"]),
            "text_id": str(result["output"]["text_id"]),
            project.product.output.chunk_membership_projection_name: chunk_matches,
        }
        chunk_membership_output_path.write_text(
            _render_chunk_membership_projection_markdown(
                document_name=str(chunk_membership_payload["document_name"]),
                text_id=str(chunk_membership_payload["text_id"]),
                projection_name=project.product.output.chunk_membership_projection_name,
                include_ordered_block_ids=project.product.output.chunk_membership_include_ordered_block_ids,
                chunk_matches=chunk_matches,
            ),
            encoding="utf-8",
        )
        written_files["chunk_membership_output_file"] = _relative_path(chunk_membership_output_path)

    return written_files


def write_document_chunking_markdown_output(
    *,
    product_spec_file: str | Path = DEFAULT_DOCUMENT_CHUNKING_PRODUCT_SPEC_FILE,
    result: dict[str, Any],
    output_file: str | Path | None = None,
) -> Path:
    from document_chunking_runtime.pipeline import (
        ChunkItem,
        DocumentChunkingOutput,
        DocumentChunkingRunResult,
        ValidationReport,
        render_document_chunking_output_markdown,
    )

    project = load_document_chunking_project(product_spec_file)
    resolved_output_file = _resolve_runtime_output_anchor(project, output_file)

    ordered_chunk_items = tuple(
        ChunkItem(
            chunk_id=int(item["chunk_id"]),
            chunk_text=str(item["chunk_text"]),
            title_block_id=str(item["title_block_id"]),
            body_block_id_set=tuple(str(value) for value in item["body_block_id_set"]),
        )
        for item in result["output"]["ordered_chunk_item_set"]
    )
    output = DocumentChunkingOutput(
        document_format=str(result["output"]["document_format"]),
        text_id=str(result["output"]["text_id"]),
        ordered_chunk_item_set=ordered_chunk_items,
        paragraph_block_set=(),
        trace_meta={},
    )
    markdown = render_document_chunking_output_markdown(
        DocumentChunkingRunResult(
            document_name=str(result["document_name"]),
            text_id=str(result["text_id"]),
            normalized_text_sha256=str(result["normalized_text_sha256"]),
            paragraph_block_set=(),
            labeled_paragraph_block_set=(),
            chunk_match_set=(),
            invalid_combination_set=(),
            output=output,
            validation=ValidationReport(passed=bool(result["validation"]["passed"]), checks=()),
        ),
        document_format_field=project.product.output.document_format_field,
        document_format_value=project.product.output.document_format_value,
        document_format_scope=project.product.output.document_format_scope,
        text_id_field=project.product.output.text_id_field,
        chunk_id_field=project.product.output.chunk_id_field,
        chunk_text_field=project.product.output.chunk_text_field,
    )
    resolved_output_file.write_text(markdown, encoding="utf-8")
    return resolved_output_file


def run_document_chunking_file(
    *,
    product_spec_file: str | Path = DEFAULT_DOCUMENT_CHUNKING_PRODUCT_SPEC_FILE,
    input_file: str | Path,
    output_file: str | Path | None = None,
) -> dict[str, Any]:
    from document_chunking_runtime.pipeline import run_document_chunking_pipeline_on_file

    project = load_document_chunking_project(product_spec_file)
    resolved_input_file = Path(input_file)
    if not resolved_input_file.is_absolute():
        resolved_input_file = (REPO_ROOT / resolved_input_file).resolve()
    result = run_document_chunking_pipeline_on_file(
        resolved_input_file,
        document_format=project.product.output.document_format_value,
        heading_pattern=project.implementation.pipeline.heading_pattern,
        max_block_chars=project.implementation.pipeline.max_block_chars,
        max_chunk_items=project.product.validation.max_chunk_items,
    )
    payload = result.to_dict()
    if output_file is not None or project.implementation.runtime.write_markdown_output:
        write_document_chunking_markdown_output(
            product_spec_file=product_spec_file,
            result=payload,
            output_file=output_file,
        )
    if project.implementation.runtime.write_auxiliary_output_files:
        write_document_chunking_auxiliary_outputs(
            product_spec_file=product_spec_file,
            result=payload,
            output_file=output_file,
        )
    return payload


register_project_template(
    ProjectTemplateRegistration(
        template_id=DOCUMENT_CHUNKING_TEMPLATE_ID,
        default_product_spec_file=DEFAULT_DOCUMENT_CHUNKING_PRODUCT_SPEC_FILE,
        product_spec_layout=DOCUMENT_CHUNKING_PRODUCT_SPEC_LAYOUT,
        implementation_config_layout=DOCUMENT_CHUNKING_IMPLEMENTATION_CONFIG_LAYOUT,
        load_project=load_document_chunking_project,
        materialize_project=materialize_document_chunking_project,
        build_runtime_app_from_spec=build_document_chunking_runtime_app_from_spec,
        build_governance_closure=build_governance_closure,
        build_implementation_effect_manifest=build_implementation_effect_manifest,
        default=False,
    )
)
