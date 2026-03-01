# 示例判定

## 有效结构示例

### V1

- canonical_key: `SHELF|L0:(0,1,0,1)`

- panel_count: 1

- target_efficiency: 6.546875

- 结论: True

### V2

- canonical_key: `SHELF|L0:(0,1,0,2)`

- panel_count: 1

- target_efficiency: 13.093750

- 结论: True

### V3

- canonical_key: `SHELF|L0:(0,1,0,1)|L0:(0,1,1,2)`

- panel_count: 2

- target_efficiency: 13.093750

- 结论: True

## 无效结构示例

### I1

- case: 边界非法

- 结论: False

- 原因: ['layers_n must be > 0', 'payload_p_per_layer must be > 0', 'family-specific verification path: SHELF (R3/R4/R5)']

### I2

- case: 效率未超过 baseline

- 结论: False

- 原因: ['target_efficiency must be > baseline_efficiency', 'family-specific verification path: SHELF (R3/R4/R5)']

### I3

- case: {C,P} 组合被 R5 几何可实现性淘汰

- 结论: False

- 原因: ['combo is not in valid combinations']

