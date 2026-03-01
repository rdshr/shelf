# 数学公式与分型计数详解（双族）

本文解释双族模型下“分型数量怎么得到”，并明确当前 FRAME V1 的边界。

## 1. 三个计数层次
1. `raw_candidate_count`：原始候选结构数（未去重）。
2. `unique_types`：canonical 去重后的分型数。
3. `valid_types`：通过规则判定后的分型数。

## 2. 双族结构全集
- `Omega_frame`：`FRAME` 结构（`ROD + CONNECTOR`, `panels = empty`）
- `Omega_shelf`：`SHELF` 结构（`ROD + CONNECTOR + PANEL`, `panels != empty`）

`Omega = Omega_frame ⊔ Omega_shelf`

规则适用域：
- `R3`：所有结构适用。
- `R4/R5`：仅对 `SHELF` 适用。
- `FRAME`：`R4/R5` 记为 `not applicable / pass`，改用 frame-specific 规则。

## 3. 公式链条

### 3.1 SHELF 原始计数
设 `G={0..m-1}x{0..n-1}`，`tau(Q)` 为占用 `Q` 的矩形分割数，`N` 为层数。

- `T_non_empty = sum_{Q subseteq G, Q!=empty} tau(Q)`
- `T_layer = delta_empty + T_non_empty`
- `C_raw^shelf = (T_layer)^N`

说明：该式现在只代表 SHELF，不代表总式。

### 3.2 FRAME 原始计数（V1）
设 `C={0..m-1}x{0..n-1}x{0..N-1}` 为三维单元集合。

V1 不做任意杆图暴力枚举，而是：
1. 枚举非空、6-邻接连通的 `U subseteq C`
2. 诱导边界骨架 `S_frame(U)=(V_boundary(U), E_boundary(U), empty)`

因此：
`C_raw^frame = |{U subseteq C | U!=empty and connected_6(U)}|`

### 3.3 总原始计数
`C_raw^all = C_raw^frame + C_raw^shelf`

## 4. 分型计数与有效计数
- `C_type^frame = |Canon(Omega_frame)|`
- `C_type^shelf = |Canon(Omega_shelf)|`
- `C_type^all = C_type^frame + C_type^shelf`

- `C_valid^frame = |{t in Canon(Omega_frame) | t passes}|`
- `C_valid^shelf = |{t in Canon(Omega_shelf) | t passes}|`
- `C_valid^all = C_valid^frame + C_valid^shelf`

## 5. Canonical 规则（本实现）
1. key 必须包含 `family`。
2. 平移归一保留（`x/y/z` 最小值移到原点）。
3. 仅允许 `xy` 平面 D4 对称（旋转/镜像）。
4. 不允许 `z <-> x/y` 全等置换。

## 6. 2x2x2 示例（实测）
配置：`m=2, n=2, N=2, allow_empty_layer=true`

- `C_raw^shelf = 1225`
- `C_raw^frame = 167`
- `C_raw^all = 1392`

去重后：
- `C_type^shelf = 202`
- `C_type^frame = 31`
- `C_type^all = 233`

有效分型：
- `C_valid^shelf = 201`
- `C_valid^frame = 31`
- `C_valid^all = 232`

## 7. 为什么 FRAME V1 采用“腔体诱导骨架”
相比“任意杆图”暴力枚举，V1 有三个优点：
1. 与置物架语义一致：先有可用腔体，再有承载骨架。
2. 搜索空间可控：连通体子集枚举比任意图枚举更易收敛。
3. 规则解释清晰：`minimal_under_deletability` 可直接定义为“等于边界骨架”。

代价：V1 不是“任意杆图全覆盖”，而是语义受限的骨架子空间。

## 8. 复现实验命令
```bash
uv run env PYTHONPATH=src python - <<'PY'
from domain.models import DiscreteGrid, EnumerationConfig
from enumeration import enumerate_structure_types, counting_framework_summary

grid = DiscreteGrid(x_cells=2, y_cells=2, layers_n=2)
result = enumerate_structure_types(
    EnumerationConfig(
        grid=grid,
        allow_empty_layer=True,
        mirror_equivalent=True,
        axis_permutation_equivalent=True,
        include_shelf_family=True,
        include_frame_family=True,
        max_type_count=200000,
    )
)
s = counting_framework_summary(result, grid)
print("raw_all:", result.raw_candidate_count)
print("raw_shelf:", result.shelf_raw_candidate_count)
print("raw_frame:", result.frame_raw_candidate_count)
print("unique_all:", result.stats.unique_types)
print("valid_all:", len(result.valid_candidates()))
print("family_counts:", result.family_counts)
print("formula_all:", s["formula_instantiated"])
PY
```
