from __future__ import annotations

from typing import TYPE_CHECKING

from knowledge_base_runtime.runtime_profile import load_knowledge_base_runtime_profile
from knowledge_base_runtime.runtime_exports import (
    resolve_backend_service_spec,
    resolve_knowledge_base_domain_spec,
)

if TYPE_CHECKING:
    from project_runtime import ProjectRuntimeAssembly

from rule_validation_models import RuleValidationOutcome, RuleValidationSummary


def _outcome(
    rule_id: str,
    name: str,
    passed: bool,
    reasons: list[str],
    evidence: dict[str, object],
) -> RuleValidationOutcome:
    return RuleValidationOutcome(
        rule_id=rule_id,
        name=name,
        passed=passed,
        reasons=tuple(reasons),
        evidence=evidence,
    )


def validate_workbench_rules(project: "ProjectRuntimeAssembly") -> tuple[RuleValidationOutcome, ...]:
    contract_spec = load_knowledge_base_runtime_profile()
    frontend_spec = project.require_runtime_export("frontend_app_spec")
    domain_spec = resolve_knowledge_base_domain_spec(project)
    service_spec = resolve_backend_service_spec(project)
    workbench = domain_spec["workbench"]
    library = workbench.get("library")
    preview = workbench.get("preview")
    chat = workbench.get("chat")
    context = workbench.get("context")
    return_contract = workbench.get("return")
    if not isinstance(library, dict):
        raise ValueError("knowledge_base_domain_spec.workbench.library must be a dict")
    if not isinstance(preview, dict):
        raise ValueError("knowledge_base_domain_spec.workbench.preview must be a dict")
    if not isinstance(chat, dict):
        raise ValueError("knowledge_base_domain_spec.workbench.chat must be a dict")
    if not isinstance(context, dict):
        raise ValueError("knowledge_base_domain_spec.workbench.context must be a dict")
    if not isinstance(return_contract, dict):
        raise ValueError("knowledge_base_domain_spec.workbench.return must be a dict")
    frontend_ui = frontend_spec["ui"]
    region_ids = tuple(workbench["regions"])
    flow = workbench["flow"]
    documents = workbench["documents"]
    citation_return = workbench["citation_return"]
    knowledge_bases = workbench["knowledge_bases"]

    r1_reasons: list[str] = []
    for region in contract_spec.workbench_region_ids:
        if region not in region_ids:
            r1_reasons.append(f"missing workbench region: {region}")
    if workbench["layout_variant"] != frontend_ui.get("shell", {}).get("layout_variant"):
        r1_reasons.append("workbench layout_variant must match frontend_app_spec.ui.shell.layout_variant")
    if workbench["surface"]["preview_mode"] != frontend_ui.get("shell", {}).get("preview_mode"):
        r1_reasons.append("surface.preview_mode must match frontend_app_spec.ui.shell.preview_mode")
    if library.get("default_focus") != contract_spec.required_library_default_focus:
        r1_reasons.append(f"library.default_focus must stay {contract_spec.required_library_default_focus}")
    if preview.get("anchor_mode") != contract_spec.required_preview_anchor_mode:
        r1_reasons.append(f"preview.anchor_mode must stay {contract_spec.required_preview_anchor_mode}")
    library_actions = workbench["library"].get("actions", [])
    for action_id in contract_spec.workbench_base_library_actions:
        if action_id not in library_actions:
            r1_reasons.append(f"missing library action: {action_id}")
    if bool(library.get("allow_create")) and contract_spec.workbench_optional_create_action_id not in library_actions:
        r1_reasons.append(f"missing library action: {contract_spec.workbench_optional_create_action_id}")
    if bool(library.get("allow_delete")) and contract_spec.workbench_optional_delete_action_id not in library_actions:
        r1_reasons.append(f"missing library action: {contract_spec.workbench_optional_delete_action_id}")

    r2_reasons: list[str] = []
    if not bool(chat.get("enabled")):
        r2_reasons.append("chat must stay enabled")
    if chat.get("mode") != contract_spec.required_chat_mode:
        r2_reasons.append(f"chat.mode must stay {contract_spec.required_chat_mode}")
    if chat.get("citation_style") != service_spec.get("answer_policy", {}).get("citation_style"):
        r2_reasons.append("chat.citation_style must match backend_service_spec.answer_policy.citation_style")
    if int(context.get("max_citations", 0)) <= 0:
        r2_reasons.append("context.max_citations must be positive")
    missing_return_targets = contract_spec.required_return_target_set() - set(citation_return["targets"])
    for target in sorted(missing_return_targets):
        r2_reasons.append(f"citation return contract must include {target}")

    r3_reasons: list[str] = []
    if [item["stage_id"] for item in flow] != [item["stage_id"] for item in contract_spec.workbench_flow_dicts()]:
        r3_reasons.append(
            "workbench flow must stay knowledge_base_select -> conversation -> citation_review -> document_detail"
        )
    if not citation_return["anchor_restore"]:
        r3_reasons.append("citation return contract must restore anchors")
    if not all(item["section_count"] >= 2 for item in documents):
        r3_reasons.append("every document must expose at least summary plus one anchored section")
    if len(knowledge_bases) != 1:
        r3_reasons.append("current project instance must expose exactly one selected knowledge base")
    if flow != service_spec.get("interaction_flow", flow):
        r3_reasons.append("workbench flow must match backend_service_spec.interaction_flow")

    r4_reasons: list[str] = []
    if not all((bool(library.get("enabled")), bool(preview.get("enabled")), bool(chat.get("enabled")))):
        r4_reasons.append("library, preview, and chat must stay enabled together")
    if not bool(chat.get("citations_enabled")):
        r4_reasons.append("citation cannot be removed from the workbench chain")
    if not bool(return_contract.get("enabled")):
        r4_reasons.append("return_to_anchor cannot be removed from the workbench chain")
    if return_contract.get("citation_card_variant") not in contract_spec.supported_citation_card_variants:
        r4_reasons.append("return.citation_card_variant must stay within supported framework set")

    return (
        _outcome(
            "R1",
            "知识聊天主链",
            not r1_reasons,
            r1_reasons,
            {
                "regions": region_ids,
                "library": dict(library),
                "preview": dict(preview),
            },
        ),
        _outcome(
            "R2",
            "对话引用并轨",
            not r2_reasons,
            r2_reasons,
            {
                "chat": dict(chat),
                "context": dict(context),
                "citation_return": citation_return,
            },
        ),
        _outcome(
            "R3",
            "来源回路闭合",
            not r3_reasons,
            r3_reasons,
            {
                "flow": flow,
                "documents": documents,
                "knowledge_bases": knowledge_bases,
            },
        ),
        _outcome(
            "R4",
            "禁止组合",
            not r4_reasons,
            r4_reasons,
            {
                "features": {
                    "library": bool(library.get("enabled")),
                    "preview": bool(preview.get("enabled")),
                    "chat": bool(chat.get("enabled")),
                    "citation": bool(chat.get("citations_enabled")),
                    "return_to_anchor": bool(return_contract.get("enabled")),
                    "upload": bool(library.get("allow_create")) or bool(library.get("allow_delete")),
                },
                "return": dict(return_contract),
            },
        ),
    )


def summarize_workbench_rules(results: tuple[RuleValidationOutcome, ...]) -> RuleValidationSummary:
    return RuleValidationSummary(module_id="knowledge_base.L2.M0", rules=results)
