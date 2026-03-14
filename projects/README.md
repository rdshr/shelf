# 项目层

`projects/` 用于承载“同一框架下的不同具体产品”。

定位：
- `framework/` 定义共同结构语言、边界、基、规则与验证
- `projects/<project_id>/product_spec.toml` 固定该产品最终是什么
- `projects/<project_id>/implementation_config.toml` 固定该产品如何落到某种实现路径
- `src/` 承载生成器内核、运行时模板与校验器，不承载项目层手写业务真相

约束：
- `projects/` 不属于 L0-L3 框架标准树
- 项目层不能替代标准源文档
- 只有边界内允许变化的值才能下放到 `product_spec.toml`
- `product_spec.toml` 顶层 section 必须对应框架大类边界；校验器会拒绝未知顶层 section 与越界嵌套 section
- `implementation_config.toml` 只负责技术细化，不得改写 `product_spec.toml` 已确定的产品真相
- 项目行为必须通过 `framework/*.md + product_spec.toml + implementation_config.toml -> generated/*` 物化；禁止直接手改 `projects/<project_id>/generated/*`

约定：
- 每个项目放在 `projects/<project_id>/`
- 主产品文件命名为 `product_spec.toml`
- 实现配置文件命名为 `implementation_config.toml`
- 编译产物输出到 `projects/<project_id>/generated/`
- 项目运行时通过 `SHELF_PRODUCT_SPEC_FILE` 选择要加载的 `product_spec.toml`
- 重新物化命令：`uv run python scripts/materialize_project.py --project projects/<project_id>/product_spec.toml`

`product_spec.toml` 至少包含：
- `project`：产品元信息与模板类型
- `framework`：引用的前端/领域/后端框架与 preset
- `surface`：对应前端 `SURFACE` 大类边界
- `visual`：对应前端 `VISUAL` 大类边界
- `route`：对应前端 `ROUTE` 大类边界
- `a11y`：对应前端 `A11Y` 大类边界
- `library / preview / chat / context / return`：对应知识库大类边界
- `[[documents]]`：知识库产品内容

`implementation_config.toml` 至少包含：
- `frontend`：前端实现剖面与运行时 profile
- `backend`：后端实现剖面、传输协议与检索策略
- `evidence`：对外暴露的产品规格证据路径
- `artifacts`：编译产物命名

当前样板：
- `knowledge_base_basic`
  - Product Spec：[product_spec.toml](./knowledge_base_basic/product_spec.toml)
  - Implementation Config：[implementation_config.toml](./knowledge_base_basic/implementation_config.toml)
  - 严格映射基线：[框架严格映射基线.md](./knowledge_base_basic/框架严格映射基线.md)
  - 机器真相源：
    - `generated/canonical_graph.json`
  - 派生视图：
    - `generated/framework_ir.json`
    - `generated/product_spec.json`
    - `generated/implementation_bundle.py`
    - `generated/generation_manifest.json`
    - `generated/governance_manifest.json`
    - `generated/governance_tree.json`
    - `generated/strict_zone_report.json`
    - `generated/object_coverage_report.json`
