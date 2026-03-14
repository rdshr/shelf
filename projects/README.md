# 项目层

`projects/` 承载在同一套 framework 下的具体项目实例。

当前仓库已经不再使用旧双轨配置主模型。  
每个项目统一使用：

- `projects/<project_id>/project.toml`

这份配置在逻辑上分成四块：

- `selection`
  - 选择本项目装配的 framework 根模块
- `truth`
  - 固定产品真相
- `refinement`
  - 固定实现细化与生成物命名
- `narrative`
  - 保留人与 AI 协作说明

约束：

- `framework/*.md` 是上游作者源
- `project.toml` 只能在 framework 边界内做选择和细化
- `generated/canonical_graph.json` 是唯一机器真相源
- 其它生成物都只是 canonical 的派生视图
- 禁止直接手改 `projects/<project_id>/generated/*`

当前样板：

- [projects/knowledge_base_basic/project.toml](./knowledge_base_basic/project.toml)

说明：

- `knowledge_base_basic` 是用于验证 Shelf AI 编译链、治理链和运行时效果的样例项目
- 它保留在仓库里参与物化与测试，但不是公开发布对象

重新物化：

```bash
uv run python scripts/materialize_project.py --project projects/knowledge_base_basic/project.toml
```
