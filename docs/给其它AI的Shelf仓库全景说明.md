# 给其它 AI 的 Shelf 仓库全景说明

## 1. 这是什么仓库

`shelf` 现在最准确的定义是：

> 一个以“结构”为第一性对象、以 Framework Markdown 为作者源、以五层收敛链为主架构的编译型仓库。

当前默认主线不是 legacy 置物架样本，而是：

> `Framework -> Product -> Implementation -> Code -> Evidence`

## 2. 仓库最核心的判断

这个仓库背后的方法论不是“先写代码，再补说明”，而是：

1. 结构比功能更基础
2. Framework 不是模板，而是人和 AI 的共同结构语言
3. Product 真相和 Implementation 细化必须分开
4. Code 不能成为上游真相源
5. Evidence 不是日志补丁，而是第五主层

## 3. 当前真实主链

### 3.1 Framework

位置：

- `framework/*/*.md`

解析后形成正式结构对象：

- `FrameworkModule`
- `FrameworkBase`
- `FrameworkRule`

### 3.2 Product

位置：

- `projects/<project_id>/product_spec.toml`
- `projects/<project_id>/product_spec/*.toml`

它表达产品真相，不表达技术细化。

### 3.3 Implementation

位置：

- `projects/<project_id>/implementation_config.toml`

它只表达实现路径，不回改产品真相。

### 3.4 Code

位置：

- `src/project_runtime/knowledge_base.py`
- `src/knowledge_base_runtime/`
- `src/frontend_kernel/`
- `src/knowledge_base_framework/`

代码主线只消费编译出来的 Code module export。

### 3.5 Evidence

位置：

- `projects/<project_id>/generated/`

当前唯一机器真相源：

- `generated/canonical_graph.json`

其它生成文件全部视为派生视图。

## 4. 机器真相源长什么样

`canonical_graph.json` 当前按五层组织：

- `layers.framework`
- `layers.product`
- `layers.implementation`
- `layers.code`
- `layers.evidence`

它保留：

- framework 文件与模块来源
- product / implementation 的 source file
- code layer 的 contract / spec / route / behavior 导出
- evidence layer 对派生视图的声明

GUI、追溯、治理和报告都应围绕它展开。

## 5. 当前知识库主链怎么落地

默认样例项目：

- `projects/knowledge_base_basic/`

它现在已经能把三份 framework markdown、两份项目 TOML 和运行时代码串成一条完整链：

- Framework 输入：前端 / 知识库工作台 / 后端接口模块
- Product：页面、路由、视觉、交互、知识对象、文档种子
- Implementation：renderer / transport / retrieval / evidence / artifacts
- Code：`frontend_contract`、`workbench_contract`、`ui_spec`、`backend_spec`
- Evidence：canonical graph、治理清单、治理树、strict zone、coverage

## 6. 当前已成立的关键原则

### 6.1 Markdown-first authoring

Framework 的作者源仍然是 Markdown，不是 schema 或 config。

### 6.2 Base / Rule first-class

`B*` 和 `R*` 不再只是注释条目，而是正式结构对象。

### 6.3 Composition first

框架装配关系默认用组合表达，不用继承树表达。

### 6.4 配置即功能

`implementation_config.toml` 里的字段必须真正进入下游行为，而不是只停留在配置文件或 bundle 抄写。

### 6.5 逐结构覆盖

仓库追求的是关键结构对象可反查，不是每一行代码逐行上框架。

## 7. 你如果要帮这个仓库出主意，最值得看的问题

### 7.1 五层边界是否还能更纯

尤其关注：

- Code 是否仍偷偷读取上游内部细节
- Evidence 是否仍然夹带平行真相源

### 7.2 canonical graph 是否已经足够支撑 GUI

重点看：

- 是否能从 framework 文件一路跳到 code / evidence
- 是否能从 code symbol 一路反查回 framework

### 7.3 治理与 strict checking 是否还有重复表达

重点看：

- 哪些派生视图其实可以再收敛
- 哪些治理对象还带着旧时代命名或旧总对象依赖

### 7.4 当前分层是否还有可继续压缩的旧抽象

例如：

- 过大的总对象接口
- 只是历史兼容残留的命名
- 旧 bundle 叙事还残留在文档或脚本里

## 8. 现在不要误解这个仓库的地方

- 它不是普通前端项目
- 它不是单纯知识库 demo
- 它不是 Markdown 模板生成器
- 它不是“写一堆 manifest”的仓库

它真正要证明的是：

> 框架文档能否成为人和 AI 共享的结构语言，并稳定收敛到产品、实现、代码和证据。

## 9. 最短总结

如果你只记一句话，就记这个：

> `shelf` 的主线已经固定为 `Framework -> Product -> Implementation -> Code -> Evidence`，并且当前知识库项目以 `canonical_graph.json` 作为唯一机器真相源，其它生成物都应被理解为派生视图。
