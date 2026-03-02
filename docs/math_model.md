# 数学模型（双族）

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

## 7. 效率函数
SHELF：
`eta_shelf(S) = (1/A) * sum_k(A_usable_k * h_clear_k * alpha_access_k)`

FRAME：
`eta_frame(S) = (1/A) * sum_b(volume(bay_b) * access_coeff(bay_b))`

说明：若不引入 `eta_frame` 分支，纯骨架结构会因无 panel usable area 导致效率恒为 0。

## 8. 有限与无限边界
连续尺寸空间通常是无限问题。
本项目通过有界离散网格把问题转为有限可穷举问题，完备性仅在离散边界内成立。
