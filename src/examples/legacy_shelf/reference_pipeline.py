from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from domain import (
    Base,
    BoundaryDefinition,
    Capability,
    DiscreteGrid,
    EnumerationConfig,
    Footprint2D,
    Goal,
    Hypothesis,
    LogicStep,
    Module,
    Opening2D,
    Space3D,
    VerificationInput,
)
from enumeration import counting_framework_summary, enumerate_structure_types
from metrics import LoadCheckInput, simplified_load_check
from rules import classify_combo_sets, geometric_type_combinations
from shelf_framework import LogicRecord, strict_mapping_meta, verify
from verification import verify_structure
from visualization import render_structure

LEGACY_DOCS_DIR = Path("docs/legacy_shelf")


def _write_text(path: str | Path, content: str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")


def build_assumptions() -> list[dict[str, str]]:
    return [
        {
            "id": "A1",
            "statement": "连续尺寸先离散化到有限网格，先解可计算穷举，再讨论连续优化。",
            "config_key": "DiscreteGrid(x_cells, y_cells, layers_n)",
        },
        {
            "id": "A2",
            "statement": "默认支持同层多块矩形板分割（占用模式与分割方式分离计数）。",
            "config_key": "partition_into_rectangles",
        },
        {
            "id": "A3",
            "statement": "冗余杆件/连接件不枚举，采用板诱导的最小必需支撑构造。",
            "config_key": "build_geometry(topology, grid)",
        },
        {
            "id": "A4",
            "statement": "默认重力沿 -Z，层板法向沿 +Z（水平层板语义）。",
            "config_key": "check_r4_board_parallel",
        },
        {
            "id": "A5",
            "statement": "opening_o 映射为 access_factor（宽高比均值，裁剪到 [0,1]）。",
            "config_key": "metrics.efficiency::_access_factor",
        },
        {
            "id": "A6",
            "statement": "baseline_utilization 默认由实验输入给定，可替换为任意基准结构。",
            "config_key": "baseline_utilization",
        },
        {
            "id": "A7",
            "statement": "未提供材料/截面/连接强度时，不声称完成真实工程安全验证，仅给简化载荷检查接口。",
            "config_key": "simplified_load_check",
        },
        {
            "id": "A8",
            "statement": "FRAME 结构采用 V1“腔体诱导骨架”：枚举 6-邻接连通单元子集 U，并诱导最小外边界骨架。",
            "config_key": "enumerate_connected_non_empty_cell_subsets + derive_boundary_skeleton_edges",
        },
        {
            "id": "A9",
            "statement": "FRAME 的 R4/R5/R6 视为 not applicable/pass；新增 connected、ground_contact、minimal_under_deletability 规则。",
            "config_key": "evaluate_structural_rules(frame path)",
        },
    ]


def write_architecture_doc() -> None:
    _write_text(
        LEGACY_DOCS_DIR / "architecture.md",
        """# Legacy Shelf 参考架构

> 该目录承载历史置物架参考样本，不代表当前仓库默认主线。

## 项目结构
- `src/domain/`: 核心实体与数据模型
- `src/rules/`: 组合规则与结构规则判定
- `src/geometry/`: 网格与几何诱导构造
- `src/enumeration/`: 有界离散分型穷举与 canonical 去重
- `src/metrics/`: 空间利用度与简化载荷
- `src/verification/`: 统一验证报告
- `src/visualization/`: 3D 渲染（Plotly + OBJ fallback）
- `src/examples/legacy_shelf/reference_pipeline.py`: legacy 置物架流水线入口，输出样本证据与说明文档

## 数据流
自然语言规则 -> 形式化对象 -> 枚举候选 -> 规则判定 -> 计算空间利用度 -> baseline 比较 -> 输出证据

## 规则流
- R1/R2：模块种类组合过滤（FRAME/SHELF 通用）
- R3：对所有结构适用
- R4/R5/R6：仅对 SHELF 适用；FRAME 视为 not applicable/pass
- FRAME 特有规则：connected、ground_contact、minimal_under_deletability、可选 forbid_dangling_rods
- Verification：边界有效 + 组合有效 + 空间利用度提升

## 可追溯性
核心类名与规则函数保持与 L2 -> L3 映射一致，输出 `docs/legacy_shelf/logic_record.json` 保存步骤级证据链，输出 `docs/legacy_shelf/run_summary.json` 保存运行摘要。
""",
    )


def write_math_model_doc() -> None:
    _write_text(
        LEGACY_DOCS_DIR / "math_model.md",
        """# 数学模型（双族）

## 1. 结构抽象
定义结构为：`S = (V, E, B)`，并引入结构族：
- `FRAME`: `B = empty`，仅含 `ROD + CONNECTOR`
- `SHELF`: `B != empty`，含 `ROD + CONNECTOR + PANEL`

结构全集：
`Omega = Omega_frame ⊔ Omega_shelf`

## 2. 离散网格
`X={x_0<...<x_m}`, `Y={y_0<...<y_n}`, `Z={z_0<...<z_N}`
- `X,Y` 将 footprint 离散化
- `Z` 表示层高索引

## 3. 占用变量
`u_{ijk} in {0,1}`，表示第 `k` 层 `(i,j)` 单元是否被板覆盖。

## 4. 模块组合集合
- 类型组合：`M_type = {X subseteq {R,C,P} | |X|>=2 and C in X}`
- 几何可实现组合：`M_geo = {{R,C},{R,C,P}}`
说明：`{C,P}` 虽满足 R1/R2，但因 R5 的四角支撑需要 rods，被几何约束淘汰。

## 5. 规则适用域
- `R3` 对所有结构适用。
- `R4/R5/R6` 仅对存在 panel 的结构（SHELF）适用。
- 对 FRAME 结构，`R4/R5/R6` 视为 `not applicable / pass`，并启用 frame-specific 规则。

## 6. 计数框架
设第 `k` 层占用区域为 `Q_k`，其矩形板分割方式数为 `tau(Q_k)`。

SHELF（保留原枚举器）：
`C_raw^shelf = (T_layer)^N`，其中 `T_layer = delta_empty + sum_Q tau(Q)`。

FRAME（V1，腔体诱导骨架）：
- 三维单元集合：`C = {0..m-1} x {0..n-1} x {0..N-1}`
- 枚举非空 6-邻接连通子集 `U subseteq C`
- 诱导骨架：`S_frame(U) = (V_boundary(U), E_boundary(U), empty)`
- 计数：`C_raw^frame = |{U subseteq C | U!=empty and connected_6(U)}|`

总计数：
`C_raw^all = C_raw^frame + C_raw^shelf`

## 7. 空间利用度函数
SHELF：
`u_shelf(S) = (1/V_total) * sum_k(A_usable_k * h_clear_k * alpha_access_k)`

FRAME：
`u_frame(S) = (1/V_total) * sum_b(volume(bay_b) * access_coeff(bay_b))`

说明：`V_total = footprint_area * total_height`。这样利用度会被归一化到总包络体积上，避免结果退化成带长度量纲的“高度分数”。

## 8. 有限与无限边界
连续尺寸空间通常是无限问题。
本项目通过有界离散网格把问题转为有限可穷举问题，完备性仅在离散边界内成立。
""",
    )


def write_assumptions_doc(assumptions: list[dict[str, str]]) -> None:
    lines = ["# 默认假设\n", "以下假设全部显式参数化，可替换。\n"]
    for item in assumptions:
        lines.append(f"## {item['id']}\n")
        lines.append(f"- 假设：{item['statement']}\n")
        lines.append(f"- 配置位置：`{item['config_key']}`\n")
    _write_text(LEGACY_DOCS_DIR / "assumptions.md", "\n".join(lines) + "\n")


def write_teaching_notes_doc() -> None:
    _write_text(
        LEGACY_DOCS_DIR / "teaching_notes.md",
        """# 教学讲解笔记

## 讲解主线
1. 先区分三层对象：模块种类组合 / 拓扑分型 / 几何实例。
2. 先离散化再穷举，避免连续空间下“总数不可判定”。
3. 规则必须落为判定器（predicate），失败必须给原因。
4. canonical form 用来去重等价结构，避免统计失真。
5. 可视化是证据层，不是建模本身。

## 常见误区
- 误区1：把“组合数”当“分型数”。
- 误区2：把“画出来”当“规则已证明”。
- 误区3：把“简化载荷检查”当“真实工程安全验证”。

## 关键认知转折
- 从自然语言条款转到可执行约束；
- 从单个案例演示转到全空间可枚举。
""",
    )


def write_slides_outline_doc() -> None:
    _write_text(
        LEGACY_DOCS_DIR / "slides_outline.md",
        """# 分享提纲（12页）

1. 问题定义：从 L2 规范出发
2. 目标与验证条件
3. 歧义与假设闭环
4. 三层对象分离：组合/分型/实例
5. 离散网格建模
6. R1-R6 规则形式化
7. 穷举器与剪枝策略
8. canonical 去重
9. 空间利用度函数与 baseline
10. 示例：3个有效 + 3个无效
11. 3D 可视化与证据输出
12. 结论、边界与下一步
""",
    )


def write_examples_doc(
    valid_examples: list[dict[str, object]],
    invalid_examples: list[dict[str, object]],
) -> None:
    lines = ["# 示例判定\n"]
    lines.append("## 有效结构示例\n")
    for idx, item in enumerate(valid_examples[:3], start=1):
        lines.append(f"### V{idx}\n")
        lines.append(f"- canonical_key: `{item['canonical_key']}`\n")
        lines.append(f"- panel_count: {item['panel_count']}\n")
        lines.append(f"- target_utilization: {item['target_utilization']:.6f}\n")
        lines.append(f"- 结论: {item['passed']}\n")

    lines.append("## 无效结构示例\n")
    for idx, item in enumerate(invalid_examples[:3], start=1):
        lines.append(f"### I{idx}\n")
        lines.append(f"- case: {item['case']}\n")
        lines.append(f"- 结论: {item['passed']}\n")
        lines.append(f"- 原因: {item['reasons']}\n")

    _write_text(LEGACY_DOCS_DIR / "examples.md", "\n".join(lines) + "\n")


def build_run_summary(
    assumptions: list[dict[str, str]],
    combo_sets: dict[str, list[list[str]]],
    enumeration_summary: dict[str, object],
    valid_count: int,
    invalid_count: int,
) -> dict[str, object]:
    return {
        "goal": "提升单位占地面积下的空间利用度",
        "metric_name": "space_utilization",
        "formalization_chain": [
            "自然语言规范",
            "形式化对象",
            "规则约束",
            "数学模型",
            "分型穷举",
            "判定验证",
            "3D 可视化",
            "证据输出",
        ],
        "assumptions": assumptions,
        "module_combinations": combo_sets,
        "enumeration_summary": enumeration_summary,
        "examples": {
            "valid_count": valid_count,
            "invalid_count": invalid_count,
        },
        "limitations": [
            "离散边界内完备，不代表连续空间完备",
            "真实工程安全验证依赖材料/截面/连接强度参数",
        ],
    }


def run_reference_pipeline() -> None:
    # Optional design intent can exist, but capability remains the primary framework object.
    goal = Goal("Increase space utilization per footprint area")
    capabilities = [
        Capability("C1", "Construct stable load-bearing paths and preserve structural integrity"),
        Capability("C2", "Generate reusable storage units and access channels"),
        Capability("C3", "Remain extensible and maintainable under scene constraints"),
    ]

    boundary = BoundaryDefinition(
        layers_n=2,
        payload_p_per_layer=30.0,
        space_s_per_layer=Space3D(width=80.0, depth=35.0, height=30.0),
        opening_o=Opening2D(width=65.0, height=28.0),
        footprint_a=Footprint2D(width=90.0, depth=40.0),
    )
    bases = [
        Base("B1", "load-bearing skeleton base", "L1.M0[R1]"),
        Base("B2", "connection extension base", "L1.M0[R2]"),
        Base("B3", "surface organization base", "L1.M0[R3]"),
    ]
    assumptions = build_assumptions()

    combo_sets = classify_combo_sets()
    valid_combos = geometric_type_combinations()
    candidate_combo = {Module.ROD, Module.CONNECTOR, Module.PANEL}

    baseline_efficiency = 0.08

    # Keep strict mapping symbol for verification mapping.
    verification_result = verify(
        VerificationInput(
            boundary=boundary,
            combo=candidate_combo,
            valid_combinations=valid_combos,
            baseline_efficiency=baseline_efficiency,
            target_efficiency=0.2,
        )
    )

    grid = DiscreteGrid(
        x_cells=2,
        y_cells=2,
        layers_n=boundary.layers_n,
        cell_width=boundary.footprint_a.width / 2.0,
        cell_depth=boundary.footprint_a.depth / 2.0,
        layer_height=boundary.space_s_per_layer.height,
    )

    enum_result = enumerate_structure_types(
        EnumerationConfig(
            grid=grid,
            allow_empty_layer=True,
            mirror_equivalent=True,
            axis_permutation_equivalent=True,
            max_type_count=5000,
        )
    )

    valid_candidates = enum_result.valid_candidates()
    invalid_candidates = enum_result.invalid_candidates()

    valid_reports: list[dict[str, object]] = []
    for candidate in valid_candidates[:6]:
        report = verify_structure(
            topology=candidate.topology,
            boundary=boundary,
            grid=grid,
            baseline_efficiency=baseline_efficiency,
        )
        valid_reports.append(
            {
                "canonical_key": candidate.canonical_key,
                "panel_count": candidate.topology.panel_count(),
                "passed": report.passed,
                "target_utilization": report.target_utilization,
                "reasons": report.reasons,
            }
        )

    manual_invalid_cases: list[dict[str, object]] = []

    bad_boundary = BoundaryDefinition(
        layers_n=0,
        payload_p_per_layer=-1.0,
        space_s_per_layer=Space3D(width=80.0, depth=35.0, height=30.0),
        opening_o=Opening2D(width=65.0, height=28.0),
        footprint_a=Footprint2D(width=90.0, depth=40.0),
    )
    bad_boundary_report = verify_structure(
        topology=valid_candidates[0].topology if valid_candidates else invalid_candidates[0].topology,
        boundary=bad_boundary,
        grid=grid,
        baseline_efficiency=baseline_efficiency,
    )
    manual_invalid_cases.append(
        {
            "case": "边界非法",
            "passed": bad_boundary_report.passed,
            "reasons": bad_boundary_report.reasons,
        }
    )

    not_improved_report = verify_structure(
        topology=valid_candidates[0].topology if valid_candidates else invalid_candidates[0].topology,
        boundary=boundary,
        grid=grid,
        baseline_efficiency=9999.0,
    )
    manual_invalid_cases.append(
        {
            "case": "空间利用度未超过 baseline",
            "passed": not_improved_report.passed,
            "reasons": not_improved_report.reasons,
        }
    )

    combo_invalid_result = verify(
        VerificationInput(
            boundary=boundary,
            combo={Module.CONNECTOR, Module.PANEL},
            valid_combinations=valid_combos,
            baseline_efficiency=baseline_efficiency,
            target_efficiency=0.2,
        )
    )
    manual_invalid_cases.append(
        {
            "case": "{C,P} 组合被 R5 几何可实现性淘汰",
            "passed": combo_invalid_result.passed,
            "reasons": combo_invalid_result.reasons,
        }
    )

    visualization_artifacts: list[dict[str, str]] = []
    for idx, candidate in enumerate(valid_candidates[:3], start=1):
        artifacts = render_structure(
            candidate.topology,
            grid,
            str(LEGACY_DOCS_DIR / "examples"),
            f"valid_{idx}",
        )
        visualization_artifacts.append(artifacts)
    for idx, candidate in enumerate(invalid_candidates[:3], start=1):
        artifacts = render_structure(
            candidate.topology,
            grid,
            str(LEGACY_DOCS_DIR / "examples"),
            f"invalid_{idx}",
        )
        visualization_artifacts.append(artifacts)

    counting_summary = counting_framework_summary(enum_result, grid)

    load_check = simplified_load_check(
        LoadCheckInput(
            payload_per_layer=boundary.payload_p_per_layer,
            panel_capacity=None,
            rod_capacity=None,
            connector_capacity=None,
            safety_factor=1.5,
        )
    )

    write_architecture_doc()
    write_math_model_doc()
    write_assumptions_doc(assumptions)
    write_teaching_notes_doc()
    write_slides_outline_doc()
    write_examples_doc(valid_reports, manual_invalid_cases)

    logic_steps = [
        LogicStep("G", "goal", evidence=goal.to_dict()),
        LogicStep("B", "boundary", ["G"], evidence=boundary.to_dict()),
        LogicStep("M", "module combinations", ["B"], evidence=combo_sets),
        LogicStep("E", "enumeration", ["M"], evidence=asdict(enum_result.stats)),
        LogicStep(
            "V",
            "verification",
            ["E"],
            evidence={
                "seed_verification_passed": verification_result.passed,
                "valid_examples": valid_reports[:3],
                "invalid_examples": manual_invalid_cases[:3],
            },
        ),
        LogicStep("C", "conclusion", ["V"], evidence={"adopt_now": bool(valid_reports)}),
    ]
    logic_record = LogicRecord.build(logic_steps)
    logic_record.export_json(LEGACY_DOCS_DIR / "logic_record.json")

    run_summary = build_run_summary(
        assumptions=assumptions,
        combo_sets=combo_sets,
        enumeration_summary={
            **counting_summary,
            **asdict(enum_result.stats),
            "layer_pattern_count": enum_result.layer_pattern_count,
        },
        valid_count=len(valid_reports),
        invalid_count=len(manual_invalid_cases),
    )
    run_summary["strict_mapping"] = strict_mapping_meta()
    run_summary["load_check"] = load_check.to_dict()
    run_summary["visualization_artifacts"] = visualization_artifacts
    (LEGACY_DOCS_DIR / "run_summary.json").write_text(
        json.dumps(run_summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    hypothesis = Hypothesis(
        hypothesis_id="H1",
        statement="With valid boundary and combination, space utilization should improve",
    )

    output = {
        "step_1": {
            "formalization_summary": {
                "capabilities": [item.to_dict() for item in capabilities],
                "goal": goal.to_dict(),
                "boundary": boundary.to_dict(),
                "bases": [item.to_dict() for item in bases],
                "modules": [item.value for item in Module],
                "rules": [
                    "R1",
                    "R2",
                    "R3(all)",
                    "R4/R5/R6(shelf-only)",
                    "FRAME.connected",
                    "FRAME.ground_contact",
                    "FRAME.minimal_under_deletability",
                ],
            },
            "ambiguities": [item["statement"] for item in assumptions],
            "default_assumptions": assumptions,
            "math_model": counting_summary,
            "codebase_design": [
                "src/domain",
                "src/rules",
                "src/geometry",
                "src/enumeration",
                "src/metrics",
                "src/verification",
                "src/visualization",
            ],
        },
        "step_3_summary": {
            "enumeration_stats": asdict(enum_result.stats),
            "valid_type_count": len(valid_candidates),
            "invalid_type_count": len(invalid_candidates),
            "valid_examples": valid_reports[:3],
            "invalid_examples": manual_invalid_cases[:3],
        },
        "artifacts": {
            "logic_record": str(LEGACY_DOCS_DIR / "logic_record.json"),
            "run_summary": str(LEGACY_DOCS_DIR / "run_summary.json"),
            "architecture": str(LEGACY_DOCS_DIR / "architecture.md"),
            "math_model": str(LEGACY_DOCS_DIR / "math_model.md"),
            "assumptions": str(LEGACY_DOCS_DIR / "assumptions.md"),
            "teaching_notes": str(LEGACY_DOCS_DIR / "teaching_notes.md"),
            "examples": str(LEGACY_DOCS_DIR / "examples.md"),
            "slides_outline": str(LEGACY_DOCS_DIR / "slides_outline.md"),
            "visualization": visualization_artifacts,
        },
        "strict_mapping": strict_mapping_meta(),
        "hypothesis": hypothesis.to_dict(),
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run_reference_pipeline()
