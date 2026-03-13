# 项目发现审计

- 审计版本：`project-discovery-audit/v1`
- 扫描目录：`projects`
- 识别为框架驱动项目：`1`
- 排除项目：`0`

| 项目目录 | 结果 | 分类 | 模板 | 原因 |
| --- | --- | --- | --- | --- |
| projects/knowledge_base_basic | 识别 | `recognized` | `knowledge_base_workbench` | product_spec.toml and implementation_config.toml both exist<br>registered template resolved: knowledge_base_workbench<br>project loads through the registered framework-driven materialization chain<br>framework selections resolve to concrete framework modules<br>implementation config exposes generated artifact contract |
