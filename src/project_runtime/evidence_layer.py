from __future__ import annotations

import json
from typing import Any

from rule_validation_models import ValidationReports

from project_runtime.code_layer import CodeModuleBinding
from project_runtime.models import ProjectRuntimeAssembly, jsonable
from project_runtime.utils import sha256_text


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


def build_evidence_modules(
    assembly: ProjectRuntimeAssembly,
    code_modules: tuple[CodeModuleBinding, ...],
) -> tuple[tuple[type[EvidenceModuleClass], ...], dict[str, Any], ValidationReports]:
    from frontend_kernel.validators import summarize_frontend_rules, validate_frontend_rules
    from knowledge_base_framework.validators import summarize_workbench_rules, validate_workbench_rules

    frontend_summary = summarize_frontend_rules(validate_frontend_rules(assembly))
    knowledge_summary = summarize_workbench_rules(validate_workbench_rules(assembly))
    validation_reports = ValidationReports(
        scopes={
            "frontend": frontend_summary,
            "knowledge_base": knowledge_summary,
        }
    )
    runtime_documents = assembly.require_runtime_export("runtime_documents")
    if not isinstance(runtime_documents, list):
        raise ValueError("runtime_documents export must be a list")
    evidence_exports = {
        "runtime_blueprint": _runtime_blueprint(assembly),
        "document_digests": _document_digests(runtime_documents),
        "validation_reports": validation_reports.to_dict(),
    }
    evidence_modules: list[type[EvidenceModuleClass]] = []
    for binding in code_modules:
        class_name = binding.code_module.__name__.replace("CodeModule", "EvidenceModule")
        module_exports = {
            "module_id": binding.framework_module.module_id,
            "code_exports": binding.code_module.code_exports,
        }
        if binding.framework_module.module_id == assembly.root_module_ids.get("frontend"):
            module_exports["frontend_rules"] = frontend_summary.to_dict()
            module_exports["runtime_blueprint"] = evidence_exports["runtime_blueprint"]
        if binding.framework_module.module_id == assembly.root_module_ids.get("knowledge_base"):
            module_exports["knowledge_base_rules"] = knowledge_summary.to_dict()
            module_exports["document_digests"] = evidence_exports["document_digests"]
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
