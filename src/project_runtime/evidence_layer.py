from __future__ import annotations

import json
from typing import Any

from rule_validation_models import RuleValidationOutcome, RuleValidationSummary
from rule_validation_models import ValidationReports

from project_runtime.config_layer import ConfigModuleBinding
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


def _summarize_kv_database_rules(assembly: ProjectRuntimeAssembly) -> RuleValidationSummary:
    try:
        spec = assembly.require_runtime_export("kv_database_runtime_spec")
    except KeyError as error:
        return RuleValidationSummary(
            module_id=assembly.root_module_ids.get("kv_database", "kv_database"),
            rules=(
                RuleValidationOutcome(
                    rule_id="KV_DATABASE_RUNTIME_SPEC",
                    name="kv database runtime spec export",
                    passed=False,
                    reasons=(str(error),),
                ),
            ),
        )
    if not isinstance(spec, dict):
        return RuleValidationSummary(
            module_id=assembly.root_module_ids.get("kv_database", "kv_database"),
            rules=(
                RuleValidationOutcome(
                    rule_id="KV_DATABASE_RUNTIME_SPEC",
                    name="kv database runtime spec export",
                    passed=False,
                    reasons=("kv_database_runtime_spec must be a dict",),
                ),
            ),
        )
    contract = spec.get("contract", {})
    wal = spec.get("wal", {})
    runtime = spec.get("runtime", {})
    implementation = runtime.get("implementation", {}) if isinstance(runtime, dict) else {}
    operation = contract.get("operation", {}) if isinstance(contract, dict) else {}
    key = contract.get("key", {}) if isinstance(contract, dict) else {}
    value = contract.get("value", {}) if isinstance(contract, dict) else {}
    rules = (
        RuleValidationOutcome(
            rule_id="KV_DATABASE_ALLOWED_OPERATIONS",
            name="allowed operations stay on put/get/delete",
            passed=list(operation.get("allowed_operations", [])) == ["put", "get", "delete"],
            reasons=()
            if list(operation.get("allowed_operations", [])) == ["put", "get", "delete"]
            else ("allowed_operations must be ['put', 'get', 'delete']",),
            evidence={"allowed_operations": operation.get("allowed_operations", [])},
        ),
        RuleValidationOutcome(
            rule_id="KV_DATABASE_KEY_POLICY",
            name="key contract remains string-only",
            passed=str(key.get("python_type")) == "str",
            reasons=() if str(key.get("python_type")) == "str" else ("key python_type must be str",),
            evidence={"python_type": key.get("python_type")},
        ),
        RuleValidationOutcome(
            rule_id="KV_DATABASE_WAL_POLICY",
            name="WAL path and replay strategy are explicit",
            passed=bool(wal.get("path")) and str(wal.get("replay_strategy")) == "append_only_replay",
            reasons=()
            if bool(wal.get("path")) and str(wal.get("replay_strategy")) == "append_only_replay"
            else ("wal.path must be non-empty and wal.replay_strategy must be append_only_replay",),
            evidence={"wal": wal},
        ),
        RuleValidationOutcome(
            rule_id="KV_DATABASE_IMPLEMENTATION_BINDING",
            name="runtime implementation classes are bound",
            passed=all(
                isinstance(implementation.get(key_name), str) and implementation.get(key_name)
                for key_name in ("database_class", "config_class", "log_class", "record_class")
            ) and str(value.get("serialization")) == "repr",
            reasons=()
            if all(
                isinstance(implementation.get(key_name), str) and implementation.get(key_name)
                for key_name in ("database_class", "config_class", "log_class", "record_class")
            ) and str(value.get("serialization")) == "repr"
            else ("implementation class bindings must exist and value.serialization must stay repr",),
            evidence={
                "implementation": implementation,
                "value_serialization": value.get("serialization"),
            },
        ),
    )
    return RuleValidationSummary(
        module_id=assembly.root_module_ids.get("kv_database", "kv_database"),
        rules=rules,
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


def build_evidence_modules(
    assembly: ProjectRuntimeAssembly,
    code_modules: tuple[CodeModuleBinding, ...],
) -> tuple[tuple[type[EvidenceModuleClass], ...], dict[str, Any], ValidationReports]:
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
    guarded_prefixes, ignored_prefixes = _read_path_scope_overrides(assembly.config.communication)
    path_scope_summary = summarize_path_scope_guard(
        repo_root=REPO_ROOT,
        guarded_prefixes=guarded_prefixes,
        ignored_prefixes=ignored_prefixes,
    )
    scopes: dict[str, RuleValidationSummary] = {
        "framework_guard": framework_summary,
        "correspondence_guard": correspondence_summary,
        "path_scope_guard": path_scope_summary,
    }
    evidence_exports: dict[str, Any] = {}
    frontend_root = assembly.root_module_ids.get("frontend")
    knowledge_root = assembly.root_module_ids.get("knowledge_base")
    backend_root = assembly.root_module_ids.get("backend")
    kv_database_root = assembly.root_module_ids.get("kv_database")
    has_knowledge_trio = bool(frontend_root and knowledge_root and backend_root)
    if has_knowledge_trio:
        from frontend_kernel.validators import summarize_frontend_rules, validate_frontend_rules
        from knowledge_base_framework.validators import summarize_workbench_rules, validate_workbench_rules

        frontend_summary = summarize_frontend_rules(validate_frontend_rules(assembly))
        knowledge_summary = summarize_workbench_rules(validate_workbench_rules(assembly))
        scopes["frontend"] = frontend_summary
        scopes["knowledge_base"] = knowledge_summary
        runtime_documents = assembly.require_runtime_export("runtime_documents")
        if not isinstance(runtime_documents, list):
            raise ValueError("runtime_documents export must be a list")
        evidence_exports["runtime_blueprint"] = _runtime_blueprint(assembly)
        evidence_exports["document_digests"] = _document_digests(runtime_documents)
    else:
        frontend_summary = None
        knowledge_summary = None
    if kv_database_root:
        kv_database_summary = _summarize_kv_database_rules(assembly)
        scopes["kv_database"] = kv_database_summary
        kv_database_spec = assembly.require_runtime_export("kv_database_runtime_spec")
        evidence_exports["kv_database_runtime_spec"] = kv_database_spec
        evidence_exports["kv_database_spec_digest"] = sha256_text(
            json.dumps(kv_database_spec, ensure_ascii=False, sort_keys=True)
        )
    else:
        kv_database_summary = None
    validation_reports = ValidationReports(scopes=scopes)
    evidence_exports["validation_reports"] = validation_reports.to_dict()
    evidence_modules: list[type[EvidenceModuleClass]] = []
    for binding in code_modules:
        class_name = binding.code_module.__name__.replace("CodeModule", "EvidenceModule")
        module_exports = {
            "module_id": binding.framework_module.module_id,
            "code_exports": binding.code_module.code_exports,
        }
        if binding.framework_module.module_id == assembly.root_module_ids.get("frontend"):
            if frontend_summary is None:
                raise ValueError("frontend evidence export requires frontend validation summary")
            module_exports["frontend_rules"] = frontend_summary.to_dict()
            module_exports["runtime_blueprint"] = evidence_exports["runtime_blueprint"]
        if binding.framework_module.module_id == assembly.root_module_ids.get("knowledge_base"):
            if knowledge_summary is None:
                raise ValueError("knowledge_base evidence export requires knowledge_base validation summary")
            module_exports["knowledge_base_rules"] = knowledge_summary.to_dict()
            module_exports["document_digests"] = evidence_exports["document_digests"]
        if binding.framework_module.module_id == assembly.root_module_ids.get("kv_database"):
            if kv_database_summary is None:
                raise ValueError("kv_database evidence export requires kv_database validation summary")
            module_exports["kv_database_rules"] = kv_database_summary.to_dict()
            module_exports["kv_database_runtime_spec"] = evidence_exports["kv_database_runtime_spec"]
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
