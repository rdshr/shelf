from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from project_runtime.knowledge_base import KnowledgeBaseProject


def _outcome(
    rule_id: str,
    name: str,
    passed: bool,
    reasons: list[str],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    return {
        "rule_id": rule_id,
        "name": name,
        "passed": passed,
        "reasons": reasons,
        "evidence": evidence,
    }


def validate_workbench_rules(project: "KnowledgeBaseProject") -> tuple[dict[str, Any], ...]:
    contract = project.workbench_contract
    ui_spec = project.ui_spec
    backend_spec = project.backend_spec
    region_ids = tuple(contract["regions"])
    flow = contract["flow"]
    documents = contract["documents"]
    citation_return = contract["citation_return_contract"]
    knowledge_bases = contract["knowledge_bases"]

    r1_reasons: list[str] = []
    for region in ("conversation_sidebar", "chat_main", "citation_drawer"):
        if region not in region_ids:
            r1_reasons.append(f"missing workbench region: {region}")
    if contract["layout_variant"] != ui_spec.get("shell", {}).get("layout_variant"):
        r1_reasons.append("workbench layout_variant must match ui_spec.shell.layout_variant")
    if contract["surface"]["preview_mode"] != ui_spec.get("shell", {}).get("preview_mode"):
        r1_reasons.append("surface.preview_mode must match ui_spec.shell.preview_mode")
    if project.library.default_focus != "current_knowledge_base":
        r1_reasons.append("library.default_focus must stay current_knowledge_base")
    if project.preview.anchor_mode != "heading":
        r1_reasons.append("preview.anchor_mode must stay heading")
    library_actions = contract["library"].get("actions", [])
    for action_id in ("switch_knowledge_base", "browse_documents", "open_document_detail"):
        if action_id not in library_actions:
            r1_reasons.append(f"missing library action: {action_id}")
    if project.library.allow_create and "create_document" not in library_actions:
        r1_reasons.append("missing library action: create_document")
    if project.library.allow_delete and "delete_document" not in library_actions:
        r1_reasons.append("missing library action: delete_document")

    r2_reasons: list[str] = []
    if not project.chat.enabled:
        r2_reasons.append("chat must stay enabled")
    if project.chat.mode != "retrieval_stub":
        r2_reasons.append("chat.mode must stay retrieval_stub")
    if project.chat.citation_style != backend_spec.get("answer_policy", {}).get("citation_style"):
        r2_reasons.append("chat.citation_style must match backend_spec.answer_policy.citation_style")
    if project.context.max_citations <= 0:
        r2_reasons.append("context.max_citations must be positive")
    if "citation_drawer" not in citation_return["targets"]:
        r2_reasons.append("citation return contract must include citation_drawer")
    if "document_detail" not in citation_return["targets"]:
        r2_reasons.append("citation return contract must include document_detail")

    r3_reasons: list[str] = []
    expected_flow = [
        "knowledge_base_select",
        "conversation",
        "citation_review",
        "document_detail",
    ]
    if project.auth.enabled:
        expected_flow = ["login_gate", *expected_flow]
    if [item["stage_id"] for item in flow] != expected_flow:
        r3_reasons.append(
            "workbench flow must match the configured knowledge-base scene chain"
        )
    if not citation_return["anchor_restore"]:
        r3_reasons.append("citation return contract must restore anchors")
    if not all(item["section_count"] >= 2 for item in documents):
        r3_reasons.append("every document must expose at least summary plus one anchored section")
    if len(knowledge_bases) != 1:
        r3_reasons.append("current project instance must expose exactly one selected knowledge base")
    if flow != backend_spec.get("interaction_flow", flow):
        r3_reasons.append("workbench flow must match backend_spec.interaction_flow")

    r4_reasons: list[str] = []
    if not all((project.library.enabled, project.preview.enabled, project.chat.enabled)):
        r4_reasons.append("library, preview, and chat must stay enabled together")
    if not project.chat.citations_enabled:
        r4_reasons.append("citation cannot be removed from the workbench chain")
    if not project.return_config.enabled:
        r4_reasons.append("return_to_anchor cannot be removed from the workbench chain")
    if project.return_config.citation_card_variant not in {"chips", "stacked", "compact"}:
        r4_reasons.append("return.citation_card_variant must stay within supported framework set")

    return (
        _outcome(
            "R1",
            "知识聊天主链",
            not r1_reasons,
            r1_reasons,
            {
                "regions": region_ids,
                "library": project.library.to_dict(),
                "preview": project.preview.to_dict(),
            },
        ),
        _outcome(
            "R2",
            "对话引用并轨",
            not r2_reasons,
            r2_reasons,
            {
                "chat": project.chat.to_dict(),
                "context": project.context.to_dict(),
                "citation_return_contract": citation_return,
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
                "features": project.features.to_dict(),
                "return": project.return_config.to_dict(),
            },
        ),
    )


def summarize_workbench_rules(results: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    passed = sum(1 for item in results if item["passed"])
    return {
        "module_id": "knowledge_base.L2.M0",
        "passed": passed == len(results),
        "passed_count": passed,
        "rule_count": len(results),
        "rules": list(results),
    }
