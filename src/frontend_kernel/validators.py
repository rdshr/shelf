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


def validate_frontend_rules(project: "KnowledgeBaseProject") -> tuple[dict[str, Any], ...]:
    contract = project.frontend_contract
    ui_spec = project.ui_spec
    surface_regions = {item["region_id"] for item in contract["surface_regions"]}
    interaction_actions = {item["action_id"] for item in contract["interaction_actions"]}
    a11y = contract["a11y"]
    route_contract = contract["route_contract"]
    shell_spec = ui_spec.get("shell", {})
    component_spec = ui_spec.get("components", {})
    pages_spec = ui_spec.get("pages", {})

    r1_required_regions = tuple(shell_spec.get("regions", ())) + ("knowledge_pages",)
    r1_missing = [item for item in r1_required_regions if item not in surface_regions]
    r1_reasons = [f"missing surface region: {item}" for item in r1_missing]
    if contract["shell"] != shell_spec.get("id"):
        r1_reasons.append("frontend shell must match ui_spec.shell.id")
    if contract["layout_variant"] != shell_spec.get("layout_variant"):
        r1_reasons.append("frontend layout_variant must match ui_spec.shell.layout_variant")
    if contract["surface_config"]["preview_mode"] != shell_spec.get("preview_mode"):
        r1_reasons.append("surface.preview_mode must match ui_spec.shell.preview_mode")

    r2_required = (
        "start_new_chat",
        "select_session",
        "open_knowledge_switch",
        "search_documents",
        "select_document",
        "submit_chat",
        "open_citation_drawer",
        "browse_knowledge_bases",
        "open_knowledge_base_detail",
        "open_document_detail",
        "return_from_citation",
    )
    r2_missing = [item for item in r2_required if item not in interaction_actions]
    r2_reasons = [f"missing interaction action: {item}" for item in r2_missing]
    if project.library.allow_create and "create_document" not in interaction_actions:
        r2_reasons.append("missing interaction action: create_document")
    if project.library.allow_delete and "delete_document" not in interaction_actions:
        r2_reasons.append("missing interaction action: delete_document")
    expected_reading_order = [
        "conversation_sidebar",
        "chat_header",
        "message_stream",
        "chat_composer",
        "citation_drawer",
    ]
    if project.auth.enabled:
        expected_reading_order = ["login_header", "login_form", *expected_reading_order]
        for action_id in ("open_login", "complete_login", "sign_out"):
            if action_id not in interaction_actions:
                r2_reasons.append(f"missing interaction action: {action_id}")
    if a11y["reading_order"] != expected_reading_order:
        r2_reasons.append(
            "reading order must match the configured protected-workbench sequence"
        )
    if not project.preview.show_toc:
        r2_reasons.append("preview TOC must stay enabled")
    if not route_contract["knowledge_list"].startswith("/"):
        r2_reasons.append("route.knowledge_list must stay routable")
    if not route_contract["knowledge_detail"].startswith(route_contract["knowledge_list"]):
        r2_reasons.append("route.knowledge_detail must stay under route.knowledge_list")
    if not route_contract["document_detail_prefix"].startswith(route_contract["knowledge_detail"]):
        r2_reasons.append("route.document_detail_prefix must stay under route.knowledge_detail")
    for page_id in ("chat_home", "knowledge_list", "knowledge_detail", "document_detail"):
        if page_id not in pages_spec:
            r2_reasons.append(f"missing ui_spec page: {page_id}")

    r3_reasons: list[str] = []
    if project.metadata.template != "knowledge_base_workbench":
        r3_reasons.append("frontend extend slot must target knowledge_base_workbench")
    if contract["extend_slots"][0]["module_id"] != project.domain_ir.module_id:
        r3_reasons.append("domain workbench slot must point to the selected domain framework module")
    if contract["extend_slots"][1]["module_id"] != project.backend_ir.module_id:
        r3_reasons.append("backend contract slot must point to the selected backend framework module")

    r4_reasons: list[str] = []
    if not project.preview.enabled:
        r4_reasons.append("preview cannot be disabled")
    if not project.chat.enabled:
        r4_reasons.append("chat cannot be disabled")
    if project.chat.citations_enabled and not project.return_config.enabled:
        r4_reasons.append("citation cannot be enabled without return_to_anchor")
    if "citation_drawer" not in project.return_config.targets:
        r4_reasons.append("return targets must include citation_drawer")
    if "document_detail" not in project.return_config.targets:
        r4_reasons.append("return targets must include document_detail")
    if contract["component_variants"]["chat_bubble"] not in {"assistant_soft", "assistant_minimal"}:
        r4_reasons.append("chat bubble variant must stay within supported framework set")
    if contract["component_variants"]["chat_composer"] not in {"chatgpt_compact", "expanded"}:
        r4_reasons.append("chat composer variant must stay within supported framework set")
    if component_spec.get("citation_drawer", {}).get("return_targets") != list(project.return_config.targets):
        r4_reasons.append("ui_spec citation drawer return_targets must match return.targets")

    return (
        _outcome(
            "R1",
            "通用承载面收敛",
            not r1_reasons,
            r1_reasons,
            {
                "shell": contract["shell"],
                "surface_regions": contract["surface_regions"],
            },
        ),
        _outcome(
            "R2",
            "场景交互统一",
            not r2_reasons,
            r2_reasons,
            {
                "interaction_actions": contract["interaction_actions"],
                "reading_order": a11y["reading_order"],
                "route_contract": route_contract,
                "component_variants": contract["component_variants"],
            },
        ),
        _outcome(
            "R3",
            "领域扩展承接",
            not r3_reasons,
            r3_reasons,
            {
                "extend_slots": contract["extend_slots"],
                "template": project.metadata.template,
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
                "surface": contract["surface_config"],
            },
        ),
    )


def summarize_frontend_rules(results: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    passed = sum(1 for item in results if item["passed"])
    return {
        "module_id": "frontend.L2.M0",
        "passed": passed == len(results),
        "passed_count": passed,
        "rule_count": len(results),
        "rules": list(results),
    }
