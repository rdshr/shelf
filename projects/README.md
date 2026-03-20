# 项目层

`projects/` 承载 Config 层的具体项目实例。

每个项目统一使用：

- `projects/<project_id>/project.toml`

这份配置现在只表达四层主链中的 Config 语义，结构固定为：

- `[project]`
  - 项目元信息
- `[framework]` 与 `[[framework.modules]]`
  - 选择本项目启用的 framework 根模块
- `[communication.*]`
  - 面向人与 AI 的结构化沟通要求
- `[exact.*]`
  - 面向 Code 层精确消费的字段、参数、路径与策略

约束：

- `framework/*.md` 是上游作者源
- `project.toml` 只能在 framework 边界内具体化配置
- `generated/canonical.json` 是唯一机器真相源
- 其它生成物都只是 canonical 的派生视图
- 禁止直接手改 `projects/<project_id>/generated/*`

当前样板：

- `message_queue_basic`
  - 项目配置：`projects/message_queue_basic/project.toml`
  - 产物目录：`projects/message_queue_basic/generated/`
