from __future__ import annotations

from typing import TYPE_CHECKING

from knowledge_base_runtime.projection import KnowledgeBaseRuntimeProjection, resolve_knowledge_base_projection

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


def validate_frontend_rules(project: "ProjectRuntimeAssembly") -> tuple[RuleValidationOutcome, ...]:
    projection: KnowledgeBaseRuntimeProjection = resolve_knowledge_base_projection(project)
    contract_spec = projection.template_contract
    contract = projection.frontend_contract
    ui_spec = projection.ui_spec
    surface_regions = {item["region_id"] for item in contract["surface_regions"]}
    interaction_actions = {item["action_id"] for item in contract["interaction_actions"]}
    a11y = contract["a11y"]
    route_contract = contract["route_contract"]
    shell_spec = ui_spec.get("shell", {})
    component_spec = ui_spec.get("components", {})
    pages_spec = ui_spec.get("pages", {})

    r1_required_regions = contract_spec.required_surface_region_ids
    r1_missing = [item for item in r1_required_regions if item not in surface_regions]
    r1_reasons = [f"missing surface region: {item}" for item in r1_missing]
    if contract["shell"] != shell_spec.get("id"):
        r1_reasons.append("frontend shell must match ui_spec.shell.id")
    if contract["layout_variant"] != shell_spec.get("layout_variant"):
        r1_reasons.append("frontend layout_variant must match ui_spec.shell.layout_variant")
    if contract["surface_config"]["preview_mode"] != shell_spec.get("preview_mode"):
        r1_reasons.append("surface.preview_mode must match ui_spec.shell.preview_mode")

    r2_required = contract_spec.frontend_interaction_action_ids(
        allow_create=projection.library.allow_create,
        allow_delete=projection.library.allow_delete,
    )
    r2_missing = [item for item in r2_required if item not in interaction_actions]
    r2_reasons = [f"missing interaction action: {item}" for item in r2_missing]
    if a11y["reading_order"] != list(contract_spec.required_reading_order):
        r2_reasons.append(
            "reading order must stay " + " -> ".join(contract_spec.required_reading_order)
        )
    if contract_spec.preview_show_toc_required and not projection.preview.show_toc:
        r2_reasons.append("preview TOC must stay enabled")
    if not route_contract["knowledge_list"].startswith("/"):
        r2_reasons.append("route.knowledge_list must stay routable")
    if not route_contract["knowledge_detail"].startswith(route_contract["knowledge_list"]):
        r2_reasons.append("route.knowledge_detail must stay under route.knowledge_list")
    if not route_contract["document_detail_prefix"].startswith(route_contract["knowledge_detail"]):
        r2_reasons.append("route.document_detail_prefix must stay under route.knowledge_detail")
    for page_id in contract_spec.required_frontend_page_ids:
        if page_id not in pages_spec:
            r2_reasons.append(f"missing ui_spec page: {page_id}")

    r3_reasons: list[str] = []
    if projection.metadata.runtime_scene != contract_spec.template_id:
        r3_reasons.append(f"frontend extend slot must target {contract_spec.template_id}")
    if contract["extend_slots"][0]["module_id"] != projection.root_module_ids["knowledge_base"]:
        r3_reasons.append("domain workbench slot must point to the selected domain framework module")
    if contract["extend_slots"][1]["module_id"] != projection.root_module_ids["backend"]:
        r3_reasons.append("backend contract slot must point to the selected backend framework module")

    r4_reasons: list[str] = []
    if not projection.preview.enabled:
        r4_reasons.append("preview cannot be disabled")
    if not projection.chat.enabled:
        r4_reasons.append("chat cannot be disabled")
    if projection.chat.citations_enabled and not projection.return_config.enabled:
        r4_reasons.append("citation cannot be enabled without return_to_anchor")
    missing_return_targets = contract_spec.required_return_target_set() - set(projection.return_config.targets)
    for target in sorted(missing_return_targets):
        r4_reasons.append(f"return targets must include {target}")
    if contract["component_variants"]["chat_bubble"] not in contract_spec.supported_chat_bubble_variants:
        r4_reasons.append("chat bubble variant must stay within supported framework set")
    if contract["component_variants"]["chat_composer"] not in contract_spec.supported_chat_composer_variants:
        r4_reasons.append("chat composer variant must stay within supported framework set")
    if component_spec.get("citation_drawer", {}).get("return_targets") != list(projection.return_config.targets):
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
                "runtime_scene": projection.metadata.runtime_scene,
            },
        ),
        _outcome(
            "R4",
            "禁止组合",
            not r4_reasons,
            r4_reasons,
            {
                "features": projection.features.to_dict(),
                "return": projection.return_config.to_dict(),
                "surface": contract["surface_config"],
            },
        ),
    )


def summarize_frontend_rules(results: tuple[RuleValidationOutcome, ...]) -> RuleValidationSummary:
    return RuleValidationSummary(module_id="frontend.L2.M0", rules=results)
