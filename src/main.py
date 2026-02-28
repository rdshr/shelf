from __future__ import annotations

import json

from shelf_framework import (
    BoundaryDefinition,
    CombinationRules,
    Footprint2D,
    Goal,
    Hypothesis,
    LogicRecord,
    LogicStep,
    Module,
    Opening2D,
    Space3D,
    VerificationInput,
    modules_to_list,
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
        LogicStep("M1", "rod", ["B1", "B2"]),
        LogicStep("M2", "connector", ["B1", "B4"]),
        LogicStep("M3", "panel", ["B2", "B3"]),
        LogicStep("R1", "no isolated module", ["M1", "M2", "M3"]),
        LogicStep("R2", "connector is mandatory", ["M2"]),
        LogicStep("H1", "efficiency improves under valid constraints", ["R1", "R2"]),
        LogicStep("V1", "verify hypothesis", ["H1"], {"passed": result_ok}),
        LogicStep("C", "conclusion", ["V1"], {"adopt_now": result_ok}),
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
    )
    verification_result = verify(verification_input)

    logic_record = build_logic_record(goal, boundary, verification_result.passed)
    logic_record.export_json("docs/logic_record.json")

    snapshot = {
        "goal": goal.to_dict(),
        "boundary": boundary.to_dict(),
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
