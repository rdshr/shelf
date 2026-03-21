from __future__ import annotations

import json
from typing import Any

from rule_validation_models import RuleValidationOutcome, RuleValidationSummary, ValidationReports

from project_runtime.config_layer import ConfigModuleBinding
from project_runtime.codegen_consistency_guard import summarize_codegen_consistency_guard
from project_runtime.correspondence_validator import summarize_correspondence_guard
from project_runtime.code_layer import CodeModuleBinding
from project_runtime.framework_violation_guard import summarize_framework_violation_guard
from project_runtime.path_scope_guard import summarize_path_scope_guard
from project_runtime.models import ProjectRuntimeAssembly, jsonable
from project_runtime.utils import REPO_ROOT, sha256_text


class EvidenceModuleClass:
    class_id: str
    module_id: str
    framework_file: str
    source_ref: dict[str, Any]
    evidence_exports: dict[str, Any]

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        return {
            "class_id": cls.class_id,
            "module_id": cls.module_id,
            "framework_file": cls.framework_file,
            "source_ref": dict(cls.source_ref),
            "evidence_exports": jsonable(cls.evidence_exports),
            "class_name": cls.__name__,
        }


def _runtime_blueprint(assembly: ProjectRuntimeAssembly) -> dict[str, Any]:
    frontend_app_spec = assembly.require_runtime_export("frontend_app_spec")
    backend_service_spec = assembly.require_runtime_export("backend_service_spec")
    pages = frontend_app_spec["ui"]["pages"]
    return {
        "transport": {
            "mode": backend_service_spec["transport"]["mode"],
            "project_config_endpoint": backend_service_spec["transport"]["project_config_endpoint"],
        },
        "summary_factory": "knowledge_base_runtime.runtime_exports:project_runtime_public_summary",
        "repository_factory": "knowledge_base_runtime.backend:build_runtime_repository",
        "api_router_factory": "knowledge_base_runtime.backend:build_knowledge_base_router",
        "landing_path": pages["chat_home"]["path"],
        "page_routes": [
            {
                "route_id": "chat_home",
                "path": pages["chat_home"]["path"],
                "response_class": "html",
                "handler_factory": "knowledge_base_runtime.frontend:build_knowledge_base_page_handler",
            },
            {
                "route_id": "basketball_showcase",
                "path": pages["basketball_showcase"]["path"],
                "response_class": "html",
                "handler_factory": "knowledge_base_runtime.frontend:build_basketball_showcase_page_handler",
            },
            {
                "route_id": "knowledge_list",
                "path": pages["knowledge_list"]["path"],
                "response_class": "html",
                "handler_factory": "knowledge_base_runtime.frontend:build_knowledge_base_list_page_handler",
            },
            {
                "route_id": "knowledge_detail",
                "path": pages["knowledge_detail"]["path"],
                "response_class": "html",
                "handler_factory": "knowledge_base_runtime.frontend:build_knowledge_base_detail_page_handler",
            },
            {
                "route_id": "document_detail",
                "path": pages["document_detail"]["path"],
                "response_class": "html",
                "handler_factory": "knowledge_base_runtime.frontend:build_document_detail_page_handler",
            },
        ],
    }


def _document_digests(runtime_documents: list[dict[str, Any]]) -> dict[str, str]:
    return {
        item["document_id"]: sha256_text(json.dumps(item, ensure_ascii=False, sort_keys=True))
        for item in runtime_documents
    }


def _build_skipped_summary(
    *,
    module_id: str,
    rule_id: str,
    name: str,
    reason: str,
) -> RuleValidationSummary:
    return RuleValidationSummary(
        module_id=module_id,
        rules=(
            RuleValidationOutcome(
                rule_id=rule_id,
                name=name,
                passed=True,
                reasons=(reason,),
            ),
        ),
    )


def _read_path_scope_overrides(
    communication_config: dict[str, Any],
) -> tuple[list[str] | None, list[str] | None]:
    raw_gate = communication_config.get("intent_gate")
    if not isinstance(raw_gate, dict):
        return None, None

    def read_list(field: str) -> list[str] | None:
        payload = raw_gate.get(field)
        if not isinstance(payload, list):
            return None
        normalized = [str(item).strip() for item in payload if str(item).strip()]
        return normalized or None

    return read_list("guarded_path_prefixes"), read_list("ignored_path_prefixes")


def _module_id_by_export_key(code_modules: tuple[CodeModuleBinding, ...], export_key: str) -> str:
    matches: list[str] = []
    for binding in code_modules:
        exports = binding.code_module.code_exports
        if not isinstance(exports, dict) or export_key not in exports:
            continue
        module_id = str(binding.framework_module.module_id).strip()
        if module_id and module_id not in matches:
            matches.append(module_id)
    if len(matches) != 1:
        return ""
    return matches[0]


def _append_module_evidence_exports(
    exports_by_module_id: dict[str, dict[str, Any]],
    *,
    module_id: str,
    payload: dict[str, Any],
) -> None:
    normalized_module_id = str(module_id).strip()
    if not normalized_module_id or not payload:
        return
    existing = exports_by_module_id.setdefault(normalized_module_id, {})
    for key, value in payload.items():
        if key in existing and existing[key] != value:
            raise ValueError(
                "conflicting evidence export assignment for module: "
                f"module_id={normalized_module_id} key={key}"
            )
        existing[key] = value


def build_evidence_modules(
    assembly: ProjectRuntimeAssembly,
    code_modules: tuple[CodeModuleBinding, ...],
) -> tuple[tuple[type[EvidenceModuleClass], ...], dict[str, Any], ValidationReports]:
    frontend_root_module_id = _module_id_by_export_key(code_modules, "frontend_app_spec")
    knowledge_root_module_id = _module_id_by_export_key(code_modules, "knowledge_base_domain_spec")

    if frontend_root_module_id:
        from frontend_kernel.validators import summarize_frontend_rules, validate_frontend_rules

        frontend_summary = summarize_frontend_rules(
            validate_frontend_rules(assembly),
            module_id=frontend_root_module_id,
        )
    else:
        frontend_summary = _build_skipped_summary(
            module_id="frontend.unselected",
            rule_id="FRONTEND_NOT_SELECTED",
            name="frontend validators skipped",
            reason="frontend root module is not selected in this project.",
        )

    if knowledge_root_module_id:
        try:
            from knowledge_base_framework.validators import summarize_workbench_rules, validate_workbench_rules
        except ModuleNotFoundError:
            knowledge_summary = RuleValidationSummary(
                module_id="knowledge_base.removed",
                rules=(
                    RuleValidationOutcome(
                        rule_id="KB_REMOVED",
                        name="knowledge_base framework validators removed",
                        passed=True,
                        reasons=("knowledge_base_framework package is not present in this workspace snapshot.",),
                    ),
                ),
            )
        else:
            knowledge_summary = summarize_workbench_rules(validate_workbench_rules(assembly))
    else:
        knowledge_summary = _build_skipped_summary(
            module_id="knowledge_base.unselected",
            rule_id="KNOWLEDGE_BASE_NOT_SELECTED",
            name="knowledge_base validators skipped",
            reason="knowledge_base root module is not selected in this project.",
        )

    framework_summary = summarize_framework_violation_guard(
        framework_modules=tuple(binding.framework_module for binding in code_modules),
        communication_config=assembly.config.communication,
        exact_config=assembly.config.exact,
    )
    correspondence_summary = summarize_correspondence_guard(
        framework_modules=tuple(binding.framework_module for binding in code_modules),
        config_modules=tuple(
            ConfigModuleBinding(
                framework_module=binding.framework_module,
                config_module=binding.config_module,
            )
            for binding in code_modules
        ),
        code_modules=code_modules,
    )
    codegen_consistency_summary, codegen_consistency_report = summarize_codegen_consistency_guard(
        framework_modules=tuple(binding.framework_module for binding in code_modules),
        config_modules=tuple(
            ConfigModuleBinding(
                framework_module=binding.framework_module,
                config_module=binding.config_module,
            )
            for binding in code_modules
        ),
        code_modules=code_modules,
    )
    guarded_prefixes, ignored_prefixes = _read_path_scope_overrides(assembly.config.communication)
    path_scope_summary = summarize_path_scope_guard(
        repo_root=REPO_ROOT,
        guarded_prefixes=guarded_prefixes,
        ignored_prefixes=ignored_prefixes,
    )
    validation_reports = ValidationReports(
        scopes={
            "frontend": frontend_summary,
            "knowledge_base": knowledge_summary,
            "framework_guard": framework_summary,
            "correspondence_guard": correspondence_summary,
            "codegen_consistency_guard": codegen_consistency_summary,
            "path_scope_guard": path_scope_summary,
        }
    )

    runtime_blueprint: dict[str, Any] | None = None
    if frontend_root_module_id:
        runtime_blueprint = _runtime_blueprint(assembly)

    document_digests: dict[str, str] | None = None
    if knowledge_root_module_id:
        runtime_documents = assembly.require_runtime_export("runtime_documents")
        if not isinstance(runtime_documents, list):
            raise ValueError("runtime_documents export must be a list")
        document_digests = _document_digests(runtime_documents)

    evidence_exports = {
        "codegen_consistency": codegen_consistency_report,
        "validation_reports": validation_reports.to_dict(),
    }
    if runtime_blueprint is not None:
        evidence_exports["runtime_blueprint"] = runtime_blueprint
    if document_digests is not None:
        evidence_exports["document_digests"] = document_digests
    module_evidence_exports_by_id: dict[str, dict[str, Any]] = {}
    _append_module_evidence_exports(
        module_evidence_exports_by_id,
        module_id=frontend_root_module_id,
        payload={
            "frontend_rules": frontend_summary.to_dict(),
            **({"runtime_blueprint": runtime_blueprint} if runtime_blueprint is not None else {}),
        },
    )
    _append_module_evidence_exports(
        module_evidence_exports_by_id,
        module_id=knowledge_root_module_id,
        payload={
            "knowledge_base_rules": knowledge_summary.to_dict(),
            **({"document_digests": document_digests} if document_digests is not None else {}),
        },
    )

    evidence_modules: list[type[EvidenceModuleClass]] = []
    for binding in code_modules:
        class_name = binding.code_module.__name__.replace("CodeModule", "EvidenceModule")
        module_exports = {
            "module_id": binding.framework_module.module_id,
            "code_exports": binding.code_module.code_exports,
        }
        module_exports.update(module_evidence_exports_by_id.get(binding.framework_module.module_id, {}))
        evidence_module = type(
            class_name,
            (EvidenceModuleClass,),
            {
                "class_id": f"evidence_module_class::{binding.framework_module.module_id}",
                "module_id": binding.framework_module.module_id,
                "framework_file": binding.framework_module.framework_file,
                "source_ref": {
                    "file_path": "src/project_runtime/evidence_layer.py",
                    "section": "evidence_module",
                    "anchor": binding.framework_module.module_id,
                    "token": binding.framework_module.module_id,
                },
                "evidence_exports": module_exports,
            },
        )
        evidence_modules.append(evidence_module)
    return tuple(evidence_modules), evidence_exports, validation_reports
