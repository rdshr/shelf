# review_workbench_backend 领域总览

本文档是 `framework/review_workbench_backend` 的领域级总览入口。它用于承接原先散落在 `review_workbench` 中、但语义上属于后端契约请求 / 返回 / 回流的 framework 真相源。

`review_workbench_backend` 不是 `review_workbench` 的实现代码目录，也不是某个具体后端项目；它表达的是统一审查平台在后端契约侧需要稳定成立的契约结构。`review_workbench` 继续负责平台壳层、工作面、列表、反馈、编排与场景主线；`review_workbench_backend` 负责这些前端场景稳定消费的后端契约真相。

## 1. 当前分层

### `L0` 后端契约原子层
`L0` 负责定义跨多个前端场景复用的后端契约原子。它回答的是：
- 请求最少要带哪些上下文
- 返回最少要说明哪些状态
- 某类后端契约交互怎样稳定表达

当前模块包括：
- `L0-M0` 统一审查平台后端契约总纲原子模块
- `L0-M1` 查询与结果集后端契约原子模块
- `L0-M2` 工作面打开与查看后端契约原子模块
- `L0-M3` 范围结构变更与查询失效后端契约原子模块
- `L0-M4` 对象动作与结果回流后端契约原子模块
- `L0-M5` 历史序列与差异后端契约原子模块

## 2. 与 `review_workbench` 的关系

- `review_workbench` 是统一审查平台的前端主领域入口。
- `review_workbench_backend` 是其外部后端契约邻域。
- `review_workbench/L1*`、`review_workbench/L2*` 等前端模块可以复用 `review_workbench_backend/L0*`，但不得在前端模块中重写同一份后端契约真相。
- `review_workbench_backend` 不负责平台壳层、导航、工作面布局、范围树展示、反馈区承载等前端结构。

### 当前消费关系
- `L0-M1` 主要被 `review_workbench/L1-M3`、`L1-M4`、`L1-M5` 复用，用于列表查询与结果集返回。
- `L0-M2` 主要被 `review_workbench/L1-M1`、`L1-M4`、`L1-M5` 复用，用于工作面打开、来源查看、节点打开与查看承接。
- `L0-M3` 主要被 `review_workbench/L1-M2` 复用，用于范围结构改动与查询失效回流。
- `L0-M4` 主要被 `review_workbench/L1-M1`、`L1-M4` 复用，用于块级动作、审核动作及结果回流。
- `L0-M5` 主要被 `review_workbench/L1-M5` 复用，用于历史请求、历史节点与差异返回。

## 3. 默认扩展规则

- 若新增的是前端壳层、列表、工作面、场景编排或用户路径，优先修改 `review_workbench`。
- 若新增的是请求、返回、动作回流、查询失效、历史差异等后端契约语义，优先修改 `review_workbench_backend`。
- 只有出现多个前端场景稳定共享的后端契约语义时，才允许继续新增 `review_workbench_backend/L0*`。
