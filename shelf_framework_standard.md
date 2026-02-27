# 置物架框架标准（领域版）

## 0. 规范关系（强制）
本文件是“置物架领域”的具体框架标准，必须遵守通用标准：
- `framework_design_standard.md`（仓库最高规范）

冲突处理：
- 若本文件与通用标准冲突，以 `framework_design_standard.md` 为准。

## 1. 目标定义（G）
定义一种可拆卸组装的开放式立体堆叠装置，用于提升单位占地面积下的存取效率。

代码映射：`Goal`

## 2. 边界定义（B）
- `N`：层数（`BoundaryDefinition.layers_n`）
- `P`：每层承重（`BoundaryDefinition.payload_p_per_layer`）
- `S`：每层空间（`BoundaryDefinition.space_s_per_layer`，`Space3D`）
- `O`：开口尺寸（`BoundaryDefinition.opening_o`，`Opening2D`）
- `A`：占地面积（`BoundaryDefinition.footprint_a`，`Footprint2D`）

有效性要求：
- 所有边界参数必须可测量、可校验（对应通用标准的 Boundary 接口）

## 3. 模块定义（M）
- `M1` 杆（`Module.ROD`）：承重支撑
- `M2` 连接接口（`Module.CONNECTOR`）：连接结构件
- `M3` 隔板（`Module.PANEL`）：承载物品

代码映射：`Module`, `MODULE_ROLE`

## 4. 规则定义（R）
- `R1`：模块不应孤立存在（组合大小至少为 2）
- `R2`：可用组合必须包含连接接口

代码映射：`Rule`, `CombinationRules.default()`

## 5. 假设与验证（H/V）

### 假设（H）
- `H1`：在边界有效且组合有效的条件下，存取效率应优于基线。

### 验证（V）
验证输入：
- 边界定义（`BoundaryDefinition`）
- 候选组合（`set[Module]`）
- 有效组合集（`valid_combinations`）
- 基线效率（`baseline_efficiency`）
- 目标效率（`target_efficiency`）

通过条件：
- 边界有效
- 组合属于有效组合集
- `target_efficiency > baseline_efficiency`

代码映射：`VerificationInput`, `VerificationResult`, `verify()`

## 6. 结论与逻辑记录（C）
逻辑链：
`G -> B1~B5 -> M1~M3 -> R1~R2 -> H1 -> V1 -> C`

自洽要求：
- `step_id` 唯一
- `depends_on` 只能引用前序步骤
- 禁止无证据结论

代码映射：`LogicStep`, `LogicRecord`, `LogicRecord.validate_self_consistency()`

## 7. 文档与代码映射
- 目标 `G` -> `Goal`
- 边界 `B` -> `BoundaryDefinition`, `Space3D`, `Opening2D`, `Footprint2D`
- 模块 `M` -> `Module`, `MODULE_ROLE`
- 规则 `R` -> `Rule`, `CombinationRules`
- 假设 `H` -> `Hypothesis`
- 验证 `V` -> `VerificationInput`, `VerificationResult`, `verify()`
- 结论/记录 `C` -> `LogicStep`, `LogicRecord`

## 8. 运行与产物
```bash
uv sync
uv run python main.py
```

产物：
- 控制台：框架快照与验证结果
- 文件：`docs/logic_record.json`

## 9. 最小验收标准（置物架）
- `N/P/S/O/A` 全部可校验且有效
- 候选组合能通过规则筛选
- 假设验证结果可解释（含失败原因）
- 逻辑记录可导出且自洽检查通过
