# 架构说明

## 当前主线

`shelf` 当前的默认主线已经固定为一条五层收敛链：

> `Framework -> Product -> Implementation -> Code -> Evidence`

这不是概念口号，而是当前知识库主链的真实工程结构。

如果你要看完整的文件级落地路径、逐层跳转方式和 code 反查逻辑，直接看：

- [全链实现框架与跳转逻辑详解.md](./全链实现框架与跳转逻辑详解.md)

- `Framework`
  - 人类作者源，位于 `framework/*/*.md`
  - 先写 Markdown，再编译为模块对象
- `Product`
  - 产品真相，位于 `projects/<project_id>/product_spec.toml`
- `Implementation`
  - 实现细化，位于 `projects/<project_id>/implementation_config.toml`
- `Code`
  - 只消费实现层导出，绑定到 contract / spec / runtime symbol
- `Evidence`
  - 只消费代码层导出，生成 canonical 图和其派生视图

## 机器真相源

知识库主链当前唯一机器真相源是：

- `projects/<project_id>/generated/canonical_graph.json`

它明确分成五层：

- `layers.framework`
- `layers.product`
- `layers.implementation`
- `layers.code`
- `layers.evidence`

其它生成文件都只是派生视图，例如：

- `framework_ir.json`
- `product_spec.json`
- `implementation_bundle.py`
- `generation_manifest.json`
- `governance_manifest.json`
- `governance_tree.json`
- `strict_zone_report.json`
- `object_coverage_report.json`

这些文件仍然保留，是为了 GUI、治理、调试和审查方便；但它们不再被叙述为平行真相源。

## 主要代码入口

- `src/framework_ir/`
  - 把 `framework/*.md` 解析成 `FrameworkModule`、`FrameworkBase`、`FrameworkRule`
- `src/project_runtime/knowledge_base.py`
  - 把 Framework / Product / Implementation 编译成分层模块与 canonical graph
- `src/knowledge_base_runtime/`
  - 只消费 Code 层导出，承载当前知识库主链的运行时代码
- `src/project_runtime/governance.py`
  - 从编译结果构造治理闭包和治理派生视图
- `scripts/validate_strict_mapping.py`
  - 对框架、项目配置、生成物和治理派生视图做严格校验

## 当前默认项目

当前默认项目是：

- `projects/knowledge_base_basic/`

它展示的是：

- Framework Markdown 如何变成 Framework module
- Product / Implementation 如何逐层收敛
- Code 如何只消费 Implementation 的稳定导出
- Evidence 如何把整条链固化成 canonical graph 与治理视图

## Legacy 样本

历史上的置物架样本仍保留，但它已经不是仓库默认主线。

位置：

- `src/examples/legacy_shelf/`
- `docs/legacy_shelf/`

它现在只是方法论样本，不再承担当前仓库的默认架构叙事。
