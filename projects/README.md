# 项目实例层

`projects/` 用于承载“同一框架下的不同项目实例”。

定位：
- `framework/` 定义抽象结构、边界、基、规则与验证
- `projects/` 固定实例边界值与允许变化值；配置按“大类边界 -> 大类 section”组织
- `src/` 承载生成器内核、运行时模板与校验器，不承载项目实例的手写业务代码

约束：
- `projects/` 不属于 L0-L3 框架标准树
- 项目实例不能替代标准源文档
- 只有边界内允许变化的值才能下放到实例配置
- `instance.toml` 顶层 section 必须对应框架大类边界；校验器会拒绝未知顶层 section 与越界嵌套 section
- 若实例要求修改 `B*` / `R*`，必须先改框架标准，再改实例配置并重新物化生成产物
- 项目实例行为必须通过 `framework/*.md + instance.toml -> generated/*` 物化；禁止直接手改 `projects/<project_id>/generated/*`

约定：
- 每个项目放在 `projects/<project_id>/`
- 主配置文件命名为 `instance.toml`
- 编译产物输出到 `projects/<project_id>/generated/`
- 项目运行时通过 `SHELF_PROJECT_FILE` 选择实例配置
- 重新物化命令：`uv run python scripts/materialize_project.py --project projects/<project_id>/instance.toml`

`instance.toml` 至少包含：
- `project`：项目元信息与模板类型
- `framework`：引用的前端/领域/后端框架与 preset
- `surface`：对应前端 `SURFACE` 大类边界
- `visual`：对应前端 `VISUAL` 大类边界
- `route`：对应前端 `ROUTE` 大类边界
- `a11y`：对应前端 `A11Y` 大类边界
- `library / preview / chat / context / return`：对应知识库大类边界
- `[[documents]]`：知识库实例数据

当前实例：
- `knowledge_base_basic`
  - 主配置：[instance.toml](./knowledge_base_basic/instance.toml)
  - 严格映射基线：[框架严格映射基线.md](./knowledge_base_basic/框架严格映射基线.md)
  - 生成产物：
    - `generated/framework_ir.json`
    - `generated/workbench_spec.json`
    - `generated/project_bundle.py`
    - `generated/generation_manifest.json`
