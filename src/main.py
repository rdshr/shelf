from __future__ import annotations

import json

from shelf_framework import (
    BoundaryDefinition,
    CombinationRules,
    ConnectorPlacement,
    ConnectorUnit,
    Footprint2D,
    Goal,
    Hypothesis,
    LogicRecord,
    LogicStep,
    Module,
    Opening2D,
    PanelCorner,
    PanelLayer,
    RodPanelConnection,
    ShelfStructure,
    Space3D,
    SupportKind,
    SupportOrientation,
    SupportUnit,
    VerificationInput,
    VerificationResult,
    modules_to_list,
    strict_mapping_meta,
    verify,
)


def build_demo_structure(boundary: BoundaryDefinition) -> ShelfStructure:
    supports = tuple(
        SupportUnit(
            support_id=f"rod-{idx}",
            kind=SupportKind.ROD,
            orientation=SupportOrientation.VERTICAL,
        )
        for idx in range(1, 5)
    )
    support_ids = tuple(item.support_id for item in supports)

    layers: list[PanelLayer] = []
    connectors: list[ConnectorUnit] = []
    connections: list[RodPanelConnection] = []
    corner_by_support: dict[str, PanelCorner] = {
        support_ids[0]: PanelCorner.FRONT_LEFT,
        support_ids[1]: PanelCorner.FRONT_RIGHT,
        support_ids[2]: PanelCorner.BACK_LEFT,
        support_ids[3]: PanelCorner.BACK_RIGHT,
    }

    for level in range(1, boundary.layers_n + 1):
        panel_id = f"panel-{level}"
        layers.append(
            PanelLayer(
                panel_id=panel_id,
                level_index=level,
                width=boundary.space_s_per_layer.width,
                depth=boundary.space_s_per_layer.depth,
                layer_height=boundary.space_s_per_layer.height,
                opening=Opening2D(
                    width=boundary.opening_o.width,
                    height=boundary.opening_o.height,
                ),
                support_unit_ids=support_ids,
                normal_axis="z",
                contour_offset=0.0,
            )
        )

        for support_id in support_ids:
            connector_id = f"conn-{panel_id}-{support_id}"
            connectors.append(
                ConnectorUnit(
                    connector_id=connector_id,
                    placement=ConnectorPlacement.CORNER,
                )
            )
            connections.append(
                RodPanelConnection(
                    support_unit_id=support_id,
                    panel_id=panel_id,
                    connector_id=connector_id,
                    uses_defined_interface=True,
                    panel_corner=corner_by_support[support_id],
                    illegal_intersection=False,
                    floating=False,
                )
            )

    return ShelfStructure(
        layers=tuple(layers),
        support_units=supports,
        connectors=tuple(connectors),
        connections=tuple(connections),
        opening_direction="front",
    )


def build_logic_record(
    goal: Goal,
    boundary: BoundaryDefinition,
    result: VerificationResult,
) -> LogicRecord:
    """构建可追溯逻辑记录，用于输出 L3 证据文件。"""
    assessments = result.deletion_assessment
    mandatory_conflicts = [item for item in assessments if item["mandatory_conflict"]]
    rule = result.rule_results

    steps = [
        LogicStep("G", "goal", evidence=goal.to_dict()),
        LogicStep("B1", "layers", ["G"], {"N": boundary.layers_n}),
        LogicStep("B2", "payload", ["G"], {"P": boundary.payload_p_per_layer}),
        LogicStep("B3", "space", ["G"], {"S": boundary.space_s_per_layer.__dict__}),
        LogicStep("B4", "opening", ["G"], {"O": boundary.opening_o.__dict__}),
        LogicStep("B5", "footprint", ["G"], {"A": boundary.footprint_a.__dict__}),
        LogicStep("M1", "rod", ["B1", "B2"], {"module": Module.ROD.value}),
        LogicStep("M2", "connector", ["B1", "B4"], {"module": Module.CONNECTOR.value}),
        LogicStep("M3", "panel", ["B2", "B3"], {"module": Module.PANEL.value}),
        LogicStep("R1", "support structure uses rod-only supports", ["M1"], {"passed": rule.get("R1")}),
        LogicStep("R2", "each panel is supported by 4 rods at 4 corners", ["M1", "M2", "M3"], {"passed": rule.get("R2")}),
        LogicStep("R3", "structure is 3D and layered by monotonic height", ["R2"], {"passed": rule.get("R3")}),
        LogicStep("R4", "all links pass legal connector interfaces", ["R3"], {"passed": rule.get("R4")}),
        LogicStep("R5", "each layer forms a closed four-corner support frame", ["R2", "R4"], {"passed": rule.get("R5")}),
        LogicStep("R6", "whole structure graph is single connected", ["R4", "R5"], {"passed": rule.get("R6")}),
        LogicStep("R7", "continuous load path satisfies N/x/y/h/O/A boundary", ["B1", "B3", "B4", "B5", "R5"], {"passed": rule.get("R7")}),
        LogicStep(
            "D1",
            "rule deletion assessment",
            ["R1", "R2", "R3", "R4", "R5", "R6", "R7"],
            {
                "items": assessments,
                "mandatory_conflict_count": len(mandatory_conflicts),
            },
        ),
        LogicStep(
            "H1",
            "efficiency improves under valid constraints",
            ["R1", "R2", "R3", "R4", "R5", "R6", "R7"],
            {"statement_valid": result.mandatory_rules_passed},
        ),
        LogicStep(
            "V1",
            "verify hypothesis",
            ["H1", "D1"],
            {
                "passed": result.passed,
                "boundary_valid": result.boundary_valid,
                "combination_valid": result.combination_valid,
                "efficiency_improved": result.efficiency_improved,
                "reasons": result.reasons,
            },
        ),
        LogicStep("C", "conclusion", ["V1"], {"adopt_now": result.passed}),
    ]
    return LogicRecord.build(steps)


def main() -> None:
    """运行置物架框架示例并输出验证快照。"""
    goal = Goal("Increase storage access efficiency per footprint area")

    boundary = BoundaryDefinition(
        layers_n=4,
        payload_p_per_layer=30.0,
        space_s_per_layer=Space3D(width=80.0, depth=35.0, height=30.0),
        opening_o=Opening2D(width=65.0, height=28.0),
        footprint_a=Footprint2D(width=90.0, depth=40.0),
    )

    rules = CombinationRules.default()
    valid_combos = rules.valid_subsets()
    candidate_combo = {Module.ROD, Module.CONNECTOR, Module.PANEL}
    structure = build_demo_structure(boundary)

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
        structure=structure,
        rules=rules,
        disabled_rules=(),
        include_recommended_rules=False,
    )
    verification_result = verify(verification_input)

    logic_record = build_logic_record(goal, boundary, verification_result)
    logic_record.export_json("docs/logic_record.json")

    snapshot = {
        "goal": goal.to_dict(),
        "boundary": boundary.to_dict(),
        "structure": structure.to_dict(),
        "hypothesis": hypothesis.to_dict(),
        "strict_mapping": strict_mapping_meta(),
        "candidate_combo": modules_to_list(candidate_combo),
        "valid_combinations": [modules_to_list(item) for item in valid_combos],
        "verification": verification_result.to_dict(),
        "logic_record_path": "docs/logic_record.json",
    }

    print(json.dumps(snapshot, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
