from __future__ import annotations

import json
from math import comb
from pathlib import Path
from typing import Any

from shelf_framework import (
    BoundaryDefinition,
    CombinationRules,
    Footprint2D,
    Goal,
    Hypothesis,
    LogicRecord,
    LogicStep,
    MODULE_ROLE,
    Module,
    Opening2D,
    Space3D,
    VerificationInput,
    component_counts_from_combo,
    evaluate_minimum_structure,
    module_counts_to_dict,
    modules_to_list,
    required_component_counts,
    strict_mapping_meta,
    verify,
)


def build_logic_record(goal: Goal, boundary: BoundaryDefinition, result_ok: bool) -> LogicRecord:
    """构建可追溯逻辑记录，用于输出 L3 证据文件。"""
    steps = [
        LogicStep("G", "goal", evidence=goal.to_dict()),
        LogicStep("B1", "layers", ["G"], {"N": boundary.layers_n}),
        LogicStep("B2", "payload", ["G"], {"P": boundary.payload_p_per_layer}),
        LogicStep("B3", "space", ["G"], {"S": boundary.space_s_per_layer.__dict__}),
        LogicStep("B4", "opening", ["G"], {"O": boundary.opening_o.__dict__}),
        LogicStep("B5", "footprint", ["G"], {"A": boundary.footprint_a.__dict__}),
        LogicStep("M1", "vertical_rod", ["B1", "B2"]),
        LogicStep("M2", "horizontal_rod", ["B2", "B3"]),
        LogicStep("M3", "connector", ["B1", "B4"]),
        LogicStep("M4", "panel", ["B2", "B3"]),
        LogicStep("R1", "no isolated module", ["M1", "M2", "M3", "M4"]),
        LogicStep("R2", "connector is mandatory", ["M3"]),
        LogicStep(
            "R3",
            "minimum structure: 4 vertical rods + 4 connectors + 4 horizontal rods + panel",
            ["M1", "M2", "M3", "M4"],
        ),
        LogicStep(
            "R4",
            "single-unit layout requires at least one shelf with layers_n >= 2",
            ["B1", "R3"],
        ),
        LogicStep("H1", "efficiency improves under valid constraints", ["R1", "R2", "R3", "R4"]),
        LogicStep("V1", "verify hypothesis", ["H1"], {"passed": result_ok}),
        LogicStep("C", "conclusion", ["V1"], {"adopt_now": result_ok}),
    ]
    return LogicRecord.build(steps)


def combo_id(combo_modules: list[str]) -> str:
    return "empty" if not combo_modules else "+".join(combo_modules)


def build_combination_catalog(rules: CombinationRules) -> dict[str, Any]:
    all_combos = sorted(
        CombinationRules.all_subsets(),
        key=lambda combo: (len(combo), modules_to_list(combo)),
    )

    records: list[dict[str, Any]] = []
    for combo in all_combos:
        modules = modules_to_list(combo)
        rule_checks = [
            {
                "rule_id": rule.rule_id,
                "description": rule.description,
                "passed": rule.check(combo),
            }
            for rule in rules.rules
        ]
        records.append(
            {
                "combo_id": combo_id(modules),
                "modules": modules,
                "module_count": len(modules),
                "rule_checks": rule_checks,
                "valid": all(check["passed"] for check in rule_checks),
            }
        )

    valid_records = [item for item in records if item["valid"]]
    max_size = len(Module)

    by_size: list[dict[str, int]] = []
    for size in range(max_size + 1):
        total_count = sum(1 for item in records if item["module_count"] == size)
        valid_count = sum(
            1 for item in valid_records if item["module_count"] == size
        )
        by_size.append(
            {
                "module_count": size,
                "total_count": total_count,
                "valid_count": valid_count,
                "invalid_count": total_count - valid_count,
            }
        )

    module_coverage = []
    for module in Module:
        module_coverage.append(
            {
                "module": module.value,
                "role": MODULE_ROLE[module],
                "valid_combo_count": sum(
                    1 for item in valid_records if module.value in item["modules"]
                ),
            }
        )

    rule_pass_rate = []
    for index, rule in enumerate(rules.rules):
        passed_count = sum(
            1 for item in records if item["rule_checks"][index]["passed"]
        )
        rule_pass_rate.append(
            {
                "rule_id": rule.rule_id,
                "description": rule.description,
                "passed_count": passed_count,
                "failed_count": len(records) - passed_count,
            }
        )

    return {
        "total_count": len(records),
        "valid_count": len(valid_records),
        "invalid_count": len(records) - len(valid_records),
        "all_combinations": records,
        "valid_combo_ids": [item["combo_id"] for item in valid_records],
        "valid_combinations": [item["modules"] for item in valid_records],
        "by_size": by_size,
        "module_coverage": module_coverage,
        "rule_pass_rate": rule_pass_rate,
    }


def write_text(path: str | Path, content: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def export_frontend_snapshot(payload: dict[str, Any]) -> dict[str, str]:
    json_path = "docs/frontend_snapshot.json"
    js_path = "docs/frontend_snapshot.js"

    write_text(json_path, json.dumps(payload, ensure_ascii=False, indent=2))
    write_text(
        js_path,
        "window.SHELF_FRONTEND_DATA = "
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + ";\n",
    )
    return {"json": json_path, "js": js_path}


def build_validation_scenario() -> dict[str, Any]:
    return {
        "dimension": {
            "unit_footprint_area": 1,
            "total_area_units": 1,
            "max_shelves_in_unit_area": 4,
            "shelf_slots_per_unit_area": 4,
            "layout_grid": {"rows": 2, "cols": 2},
        },
        "layer_constraint": {
            "min_inclusive": 1,
            "max_exclusive": 4,
            "allowed_values": [1, 2, 3],
            "rule": "1 <= layers_n < 4",
        },
        "efficiency_rule": {
            "at_least_one_shelf_min_layers": 2,
            "rule": "at least one shelf in the unit footprint must have layers_n >= 2",
            "statement": (
                "to improve access efficiency per unit footprint, at least one shelf "
                "must be configured with 2 or more layers"
            ),
        },
        "minimum_structure_rule": {
            "single_layer": module_counts_to_dict(required_component_counts(1)),
            "formula": {
                "vertical_rod": ">= 4",
                "connector": ">= 4 * layers_n",
                "horizontal_rod": ">= 4 * layers_n",
                "panel": ">= layers_n",
            },
            "statement": (
                "minimum structure requires 4 vertical rods; every layer needs "
                "4 connectors and 4 horizontal rods to support panel"
            ),
        },
    }


def build_unit_variants(
    combinations: list[dict[str, Any]], allowed_layers: list[int]
) -> list[dict[str, Any]]:
    variants: list[dict[str, Any]] = []
    module_lookup = {module.value: module for module in Module}
    for combo in combinations:
        combo_set = {module_lookup[name] for name in combo["modules"]}
        for layers_n in allowed_layers:
            variant_id = f"{combo['combo_id']}|L{layers_n}"
            layer_valid = 1 <= layers_n < 4
            structure = evaluate_minimum_structure(combo_set, layers_n)
            variants.append(
                {
                    "variant_id": variant_id,
                    "combo_id": combo["combo_id"],
                    "modules": combo["modules"],
                    "layers_n": layers_n,
                    "combo_valid": combo["valid"],
                    "layer_valid": layer_valid,
                    "structure_valid": structure["passed"],
                    "required_component_counts": structure["required_component_counts"],
                    "actual_component_counts": structure["actual_component_counts"],
                    "structure_reasons": structure["reasons"],
                    "valid": combo["valid"] and layer_valid and structure["passed"],
                }
            )
    return variants


def build_layout_statistics(
    unit_variants: list[dict[str, Any]],
    slot_count: int,
    min_layers_for_efficiency: int,
) -> dict[str, Any]:
    unit_variant_total = len(unit_variants)
    unit_variant_valid = sum(1 for item in unit_variants if item["valid"])
    unit_variant_invalid = unit_variant_total - unit_variant_valid

    total_layout_count = unit_variant_total**slot_count
    valid_variants_with_target_layers = sum(
        1
        for item in unit_variants
        if item["valid"] and item["layers_n"] >= min_layers_for_efficiency
    )
    valid_variants_without_target_layers = (
        unit_variant_valid - valid_variants_with_target_layers
    )

    valid_layout_count = 0
    if unit_variant_valid > 0:
        valid_layout_count = (unit_variant_valid**slot_count) - (
            valid_variants_without_target_layers**slot_count
        )

    invalid_unit_distribution: list[dict[str, int]] = []
    for invalid_units in range(slot_count + 1):
        count = (
            comb(slot_count, invalid_units)
            * (unit_variant_invalid**invalid_units)
            * (unit_variant_valid ** (slot_count - invalid_units))
        )
        invalid_unit_distribution.append(
            {"invalid_units": invalid_units, "layout_count": count}
        )

    return {
        "slot_count": slot_count,
        "efficiency_min_layers": min_layers_for_efficiency,
        "unit_variant_total": unit_variant_total,
        "unit_variant_valid": unit_variant_valid,
        "unit_variant_invalid": unit_variant_invalid,
        "efficiency_qualified_variant_count": valid_variants_with_target_layers,
        "efficiency_unqualified_variant_count": valid_variants_without_target_layers,
        "total_layout_count": total_layout_count,
        "valid_layout_count": valid_layout_count,
        "invalid_layout_count": total_layout_count - valid_layout_count,
        "efficiency_rule_fail_layout_count": (
            valid_variants_without_target_layers**slot_count
            if unit_variant_valid > 0
            else 0
        ),
        "invalid_unit_distribution": invalid_unit_distribution,
    }


def verify_layout_selection(
    selected_variant_ids: list[str],
    unit_variants: list[dict[str, Any]],
    slot_count: int,
    min_layers_for_efficiency: int,
) -> dict[str, Any]:
    reasons: list[str] = []
    variant_map = {item["variant_id"]: item for item in unit_variants}
    has_target_layers = False

    if len(selected_variant_ids) != slot_count:
        reasons.append(f"layout must contain exactly {slot_count} shelves")

    for index, variant_id in enumerate(selected_variant_ids, start=1):
        variant = variant_map.get(variant_id)
        if variant is None:
            reasons.append(f"shelf-{index}: unknown variant {variant_id}")
            continue
        if not variant["valid"]:
            detail = "; ".join(variant.get("structure_reasons", [])) or "rule mismatch"
            reasons.append(
                f"shelf-{index}: variant is invalid ({variant_id}) -> {detail}"
            )
        elif variant["layers_n"] >= min_layers_for_efficiency:
            has_target_layers = True

    if not has_target_layers:
        reasons.append(
            f"at least one shelf must have layers_n >= {min_layers_for_efficiency}"
        )

    return {
        "selected_variant_ids": selected_variant_ids,
        "efficiency_rule_satisfied": has_target_layers,
        "passed": len(reasons) == 0,
        "reasons": reasons,
    }


def main() -> None:
    """运行置物架框架示例并输出验证快照与前端可视化数据。"""
    goal = Goal("Increase storage access efficiency per footprint area")

    boundary = BoundaryDefinition(
        layers_n=3,
        payload_p_per_layer=30.0,
        space_s_per_layer=Space3D(width=1.0, depth=1.0, height=1.0),
        opening_o=Opening2D(width=0.8, height=0.9),
        footprint_a=Footprint2D(width=1.0, depth=1.0),
    )

    rules = CombinationRules.default()
    combination_catalog = build_combination_catalog(rules)
    valid_combos = rules.valid_subsets()
    candidate_combo = {
        Module.VERTICAL_ROD,
        Module.HORIZONTAL_ROD,
        Module.CONNECTOR,
        Module.PANEL,
    }

    hypothesis = Hypothesis(
        hypothesis_id="H1",
        statement="With valid boundary and combination, access efficiency should improve",
    )

    verification_input = VerificationInput(
        boundary=boundary,
        combo=candidate_combo,
        valid_combinations=valid_combos,
        baseline_efficiency=1.0,
        target_efficiency=1.22,
        component_counts=component_counts_from_combo(candidate_combo, boundary.layers_n),
    )
    verification_result = verify(verification_input)

    scenario = build_validation_scenario()
    allowed_layers = scenario["layer_constraint"]["allowed_values"]
    unit_variants = build_unit_variants(
        combination_catalog["all_combinations"], allowed_layers
    )
    slot_count = scenario["dimension"]["shelf_slots_per_unit_area"]
    min_layers_for_efficiency = scenario["efficiency_rule"][
        "at_least_one_shelf_min_layers"
    ]
    layout_stats = build_layout_statistics(
        unit_variants, slot_count, min_layers_for_efficiency
    )
    valid_variant_ids = [item["variant_id"] for item in unit_variants if item["valid"]]
    valid_efficiency_variant_ids = [
        item["variant_id"]
        for item in unit_variants
        if item["valid"] and item["layers_n"] >= min_layers_for_efficiency
    ]
    if valid_variant_ids:
        first_slot = (
            valid_efficiency_variant_ids[0]
            if valid_efficiency_variant_ids
            else valid_variant_ids[0]
        )
        default_layout = [first_slot] + [valid_variant_ids[0]] * (slot_count - 1)
    else:
        default_layout = []
    layout_verification = verify_layout_selection(
        default_layout,
        unit_variants,
        slot_count,
        min_layers_for_efficiency,
    )

    logic_record = build_logic_record(goal, boundary, verification_result.passed)
    logic_record.export_json("docs/logic_record.json")

    snapshot: dict[str, Any] = {
        "goal": goal.to_dict(),
        "boundary": boundary.to_dict(),
        "hypothesis": hypothesis.to_dict(),
        "modules": [
            {"name": module.value, "role": MODULE_ROLE[module]} for module in Module
        ],
        "strict_mapping": strict_mapping_meta(),
        "combination_catalog": combination_catalog,
        "validation_scenario": scenario,
        "required_component_counts_for_boundary_layers": module_counts_to_dict(
            required_component_counts(boundary.layers_n)
        ),
        "unit_variants": unit_variants,
        "layout_statistics": layout_stats,
        "default_layout": default_layout,
        "default_layout_verification": layout_verification,
        "candidate_combo": modules_to_list(candidate_combo),
        "valid_combinations": [modules_to_list(item) for item in valid_combos],
        "verification_input": {
            "baseline_efficiency": verification_input.baseline_efficiency,
            "target_efficiency": verification_input.target_efficiency,
        },
        "verification": verification_result.to_dict(),
        "logic_record_path": "docs/logic_record.json",
    }

    exported_files = export_frontend_snapshot(snapshot)
    snapshot["frontend_snapshot_paths"] = exported_files

    print(json.dumps(snapshot, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
