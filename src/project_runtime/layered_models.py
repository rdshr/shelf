from __future__ import annotations

from dataclasses import dataclass, is_dataclass
from typing import Any

from framework_ir import FrameworkModule
from rule_validation_models import ValidationReports


def _jsonable(value: Any) -> Any:
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _jsonable(value.to_dict())
    if is_dataclass(value):
        return {
            key: _jsonable(getattr(value, key))
            for key in value.__dataclass_fields__  # type: ignore[attr-defined]
        }
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (set, frozenset)):
        return sorted(_jsonable(item) for item in value)
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


@dataclass(frozen=True)
class LayeredTraceRef:
    layer: str
    ref_id: str
    title: str
    file: str | None = None
    anchor: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "layer": self.layer,
            "ref_id": self.ref_id,
            "title": self.title,
        }
        if self.file is not None:
            payload["file"] = self.file
        if self.anchor is not None:
            payload["anchor"] = self.anchor
        return payload


@dataclass(frozen=True)
class KnowledgeBaseFrameworkLayer:
    selection: dict[str, str]
    primary_modules: tuple[FrameworkModule, ...]
    resolved_modules: tuple[FrameworkModule, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "selection": dict(self.selection),
            "primary_modules": [item.to_dict() for item in self.primary_modules],
            "resolved_modules": [item.to_dict() for item in self.resolved_modules],
            "exports": [item.export_surface().to_dict() for item in self.resolved_modules],
        }


@dataclass(frozen=True)
class KnowledgeBaseProductModule:
    module_id: str
    export: dict[str, Any]
    source_file: str
    section_sources: dict[str, str]
    derived_from: tuple[LayeredTraceRef, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "module_id": self.module_id,
            "source_file": self.source_file,
            "section_sources": dict(self.section_sources),
            "derived_from": [item.to_dict() for item in self.derived_from],
            "export": _jsonable(self.export),
        }

    @property
    def metadata(self) -> Any:
        return self.export["metadata"]

    @property
    def framework_selection(self) -> Any:
        return self.export["framework_selection"]

    @property
    def surface(self) -> Any:
        return self.export["surface"]

    @property
    def visual(self) -> Any:
        return self.export["visual"]

    @property
    def features(self) -> Any:
        return self.export["features"]

    @property
    def route(self) -> Any:
        return self.export["route"]

    @property
    def showcase_page(self) -> Any:
        return self.export["showcase_page"]

    @property
    def a11y(self) -> Any:
        return self.export["a11y"]

    @property
    def library(self) -> Any:
        return self.export["library"]

    @property
    def preview(self) -> Any:
        return self.export["preview"]

    @property
    def chat(self) -> Any:
        return self.export["chat"]

    @property
    def context(self) -> Any:
        return self.export["context"]

    @property
    def return_config(self) -> Any:
        return self.export["return_config"]

    @property
    def documents(self) -> Any:
        return self.export["documents"]

    @property
    def copy(self) -> dict[str, Any]:
        return self.export["copy"]


@dataclass(frozen=True)
class KnowledgeBaseImplementationModule:
    module_id: str
    export: dict[str, Any]
    source_file: str
    derived_from: tuple[LayeredTraceRef, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "module_id": self.module_id,
            "source_file": self.source_file,
            "derived_from": [item.to_dict() for item in self.derived_from],
            "export": _jsonable(self.export),
        }

    @property
    def frontend(self) -> Any:
        return self.export["frontend"]

    @property
    def backend(self) -> Any:
        return self.export["backend"]

    @property
    def evidence(self) -> Any:
        return self.export["evidence"]

    @property
    def artifacts(self) -> Any:
        return self.export["artifacts"]

    @property
    def product_module_id(self) -> str:
        return self.export["product_module_id"]

    @property
    def template_contract(self) -> Any:
        return self.export["template_contract"]

    @property
    def visual_tokens(self) -> dict[str, str]:
        return self.export["visual_tokens"]

    @property
    def copy(self) -> dict[str, Any]:
        return self.export["copy"]

    @property
    def documents(self) -> Any:
        return self.export["documents"]

    @property
    def frontend_module(self) -> FrameworkModule:
        return self.export["frontend_module"]

    @property
    def domain_module(self) -> FrameworkModule:
        return self.export["domain_module"]

    @property
    def backend_module(self) -> FrameworkModule:
        return self.export["backend_module"]


@dataclass(frozen=True)
class KnowledgeBaseCodeModule:
    module_id: str
    export: dict[str, Any]
    derived_from: tuple[LayeredTraceRef, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "module_id": self.module_id,
            "derived_from": [item.to_dict() for item in self.derived_from],
            "export": _jsonable(self.export),
        }

    @property
    def metadata(self) -> Any:
        return self.export["metadata"]

    @property
    def template_contract(self) -> Any:
        return self.export["template_contract"]

    @property
    def framework_refs(self) -> dict[str, Any]:
        return self.export["framework_refs"]

    @property
    def framework(self) -> Any:
        return self.export["framework_selection"]

    @property
    def layer_trace(self) -> dict[str, Any]:
        return self.export["layer_trace"]

    @property
    def surface(self) -> Any:
        return self.export["surface"]

    @property
    def visual(self) -> Any:
        return self.export["visual"]

    @property
    def visual_tokens(self) -> dict[str, str]:
        return self.export["visual_tokens"]

    @property
    def features(self) -> Any:
        return self.export["features"]

    @property
    def route(self) -> Any:
        return self.export["route"]

    @property
    def showcase_page(self) -> Any:
        return self.export["showcase_page"]

    @property
    def a11y(self) -> Any:
        return self.export["a11y"]

    @property
    def library(self) -> Any:
        return self.export["library"]

    @property
    def preview(self) -> Any:
        return self.export["preview"]

    @property
    def chat(self) -> Any:
        return self.export["chat"]

    @property
    def context(self) -> Any:
        return self.export["context"]

    @property
    def return_config(self) -> Any:
        return self.export["return_config"]

    @property
    def copy(self) -> dict[str, Any]:
        return self.export["copy"]

    @property
    def documents(self) -> Any:
        return self.export["documents"]

    @property
    def frontend_module(self) -> FrameworkModule:
        return self.export["frontend_module"]

    @property
    def frontend_ir(self) -> FrameworkModule:
        return self.frontend_module

    @property
    def domain_module(self) -> FrameworkModule:
        return self.export["domain_module"]

    @property
    def domain_ir(self) -> FrameworkModule:
        return self.domain_module

    @property
    def backend_module(self) -> FrameworkModule:
        return self.export["backend_module"]

    @property
    def backend_ir(self) -> FrameworkModule:
        return self.backend_module

    @property
    def frontend_contract(self) -> dict[str, Any]:
        return self.export["frontend_contract"]

    @property
    def workbench_contract(self) -> dict[str, Any]:
        return self.export["workbench_contract"]

    @property
    def ui_spec(self) -> dict[str, Any]:
        return self.export["ui_spec"]

    @property
    def backend_spec(self) -> dict[str, Any]:
        return self.export["backend_spec"]

    @property
    def product_view(self) -> dict[str, Any]:
        return self.export["product_view"]

    @property
    def implementation_effects(self) -> dict[str, Any]:
        return self.export["implementation_effects"]

    @property
    def validation_reports(self) -> ValidationReports:
        return self.export["validation_reports"]

    @property
    def generated_artifacts(self) -> Any:
        return self.export.get("generated_artifacts")

    @property
    def public_summary(self) -> dict[str, Any]:
        return self.export["public_summary"]

    def to_spec_dict(self) -> dict[str, Any]:
        return {
            "product_spec": self.product_view,
            "ui_spec": self.ui_spec,
            "backend_spec": self.backend_spec,
            "frontend_contract": self.frontend_contract,
            "workbench_contract": self.workbench_contract,
            "generated_artifacts": self.generated_artifacts.to_dict() if self.generated_artifacts else None,
        }


@dataclass(frozen=True)
class KnowledgeBaseEvidenceModule:
    module_id: str
    export: dict[str, Any]
    derived_from: tuple[LayeredTraceRef, ...]
    validation_reports: ValidationReports

    def to_dict(self) -> dict[str, Any]:
        export_payload = dict(self.export)
        export_payload.pop("canonical_graph", None)
        return {
            "module_id": self.module_id,
            "derived_from": [item.to_dict() for item in self.derived_from],
            "validation_reports": self.validation_reports.to_dict(),
            "export": _jsonable(export_payload),
        }

    @property
    def canonical_graph(self) -> dict[str, Any]:
        return self.export["canonical_graph"]

    @property
    def derived_views(self) -> dict[str, Any]:
        return self.export["derived_views"]


@dataclass(frozen=True)
class CanonicalLayeredProjectGraph:
    schema_version: str
    project_id: str
    product_spec_file: str
    implementation_config_file: str
    framework: KnowledgeBaseFrameworkLayer
    product: KnowledgeBaseProductModule
    implementation: KnowledgeBaseImplementationModule
    code: KnowledgeBaseCodeModule
    evidence: KnowledgeBaseEvidenceModule

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "product_spec_file": self.product_spec_file,
            "implementation_config_file": self.implementation_config_file,
            "layers": {
                "framework": self.framework.to_dict(),
                "product": self.product.to_dict(),
                "implementation": self.implementation.to_dict(),
                "code": self.code.to_dict(),
                "evidence": self.evidence.to_dict(),
            },
        }
