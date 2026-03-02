# 架构说明

## 项目结构
- `src/domain/`: 核心实体与数据模型
- `src/rules/`: 组合规则与结构规则判定
- `src/geometry/`: 网格与几何诱导构造
- `src/enumeration/`: 有界离散分型穷举与 canonical 去重
- `src/metrics/`: 效率与简化载荷
- `src/verification/`: 统一验证报告
- `src/visualization/`: 3D 渲染（Plotly + OBJ fallback）
- `src/main.py`: 流水线入口，输出证据与文档

## 数据流
自然语言规则 -> 形式化对象 -> 枚举候选 -> 规则判定 -> 计算效率 -> baseline 比较 -> 输出证据

## 规则流
- R1/R2：模块种类组合过滤（FRAME/SHELF 通用）
- R3：对所有结构适用
- R4/R5/R6：仅对 SHELF 适用；FRAME 视为 not applicable/pass
- FRAME 特有规则：connected、ground_contact、minimal_under_deletability、可选 forbid_dangling_rods
- Verification：边界有效 + 组合有效 + 效率提升

## 可追溯性
核心类名与规则函数保持与 L2 -> L3 映射一致，且输出 `docs/logic_record.json` 保存证据链。
