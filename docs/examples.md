# 示例判定

## 有效结构示例

### V1

- canonical_key: `SHELF|L0:(0,1,0,1)|L1:(0,2,0,2)`

- panel_count: 2

- target_efficiency: 32.734375

- 结论: True

### V2

- canonical_key: `SHELF|L0:(0,1,0,1)|L1:(0,1,0,2)|L1:(1,2,0,2)`

- panel_count: 3

- target_efficiency: 32.734375

- 结论: True

### V3

- canonical_key: `SHELF|L0:(0,1,0,1)|L1:(0,1,0,2)|L1:(1,2,0,1)|L1:(1,2,1,2)`

- panel_count: 4

- target_efficiency: 32.734375

- 结论: True

## 无效结构示例

### I1

- case: 边界非法

- 结论: False

- 原因: ['layers_n must be > 0', 'payload_p_per_layer must be > 0', 'family-specific verification path: SHELF (R3/R4/R5/R6)']

### I2

- case: 效率未超过 baseline

- 结论: False

- 原因: ['target_efficiency must be > baseline_efficiency', 'family-specific verification path: SHELF (R3/R4/R5/R6)']

### I3

- case: {C,P} 组合被 R5 几何可实现性淘汰

- 结论: False

- 原因: ['combo is not in valid combinations']

