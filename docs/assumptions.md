# 默认假设

以下假设全部显式参数化，可替换。

## A1

- 假设：连续尺寸先离散化到有限网格，先解可计算穷举，再讨论连续优化。

- 配置位置：`DiscreteGrid(x_cells, y_cells, layers_n)`

## A2

- 假设：默认支持同层多块矩形板分割（占用模式与分割方式分离计数）。

- 配置位置：`partition_into_rectangles`

## A3

- 假设：冗余杆件/连接件不枚举，采用板诱导的最小必需支撑构造。

- 配置位置：`build_geometry(topology, grid)`

## A4

- 假设：默认重力沿 -Z，层板法向沿 +Z（水平层板语义）。

- 配置位置：`check_r4_board_parallel`

## A5

- 假设：opening_o 映射为 access_factor（宽高比均值，裁剪到 [0,1]）。

- 配置位置：`metrics.efficiency::_access_factor`

## A6

- 假设：baseline_efficiency 默认由实验输入给定，可替换为任意基准结构。

- 配置位置：`baseline_efficiency`

## A7

- 假设：未提供材料/截面/连接强度时，不声称完成真实工程安全验证，仅给简化载荷检查接口。

- 配置位置：`simplified_load_check`

## A8

- 假设：FRAME 结构采用 V1“腔体诱导骨架”：枚举 6-邻接连通单元子集 U，并诱导最小外边界骨架。

- 配置位置：`enumerate_connected_non_empty_cell_subsets + derive_boundary_skeleton_edges`

## A9

- 假设：FRAME 的 R4/R5/R6 视为 not applicable/pass；新增 connected、ground_contact、minimal_under_deletability 规则。

- 配置位置：`evaluate_structural_rules(frame path)`

