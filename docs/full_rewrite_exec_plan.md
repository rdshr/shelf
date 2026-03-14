# 全仓 rewrite 收口执行账本

审查基准文档：

- [最终架构重构验收标准.md](./最终架构重构验收标准.md)

## 已完成任务

- [x] 残差 0：补齐 runtime export-driven 主链并收掉旧入口
  - [x] `PackageCompileInput` 新增 `child_runtime_exports`，child runtime fragments 真正向上游传递
  - [x] 删除 `src/project_runtime/export_builders.py` 主装配角色，改为 child fragment -> root export 组合
  - [x] 删除 `src/knowledge_base_runtime/projection.py` 的知识库专属大聚合主路径
  - [x] 删除 `src/knowledge_base_runtime/app.py` 的知识库专属正式入口
  - [x] 新增 [src/project_runtime/runtime_app.py](../src/project_runtime/runtime_app.py) 作为 export-driven 通用入口

- [x] 残差 0.1：去掉旧场景名对 runtime 主链的控制
  - [x] `project.toml` 中 `runtime_scene` 降级为普通元数据值
  - [x] 删除 `knowledge_base_contract.toml` 并把稳定 runtime profile 内联到 package code
  - [x] frontend / workbench validators 不再用场景名做主链约束

- [x] 残差 0.2：清理旧命名派生产物
  - [x] runtime 快照产物统一使用 `runtime_snapshot.py`
  - [x] 治理清单产物统一使用 `derived_governance_manifest.json`
  - [x] 治理树产物统一使用 `derived_governance_tree.json`

- [x] 残差 0.3：同步 README / docs / tests 到 export-driven 主链
  - [x] README 切到通用 runtime 入口
  - [x] 运行时说明文档改写为 child fragment -> root export -> runtime assembly
  - [x] 测试改为围绕 `runtime_blueprint / runtime_documents / runtime entrypoint` 验收

- [x] 残差 1：把 config slicing 改成按模块树逐层分发
  - [x] root package 先拿到 subtree-owned config slice
  - [x] child package 只从 parent-owned sub-slice 继续切片
  - [x] `compile_package_results(...)` 不再把同一个全局 payload 直接喂给所有 package

- [x] 残差 2：把 governance / discovery / report / strict validator 全部切到 canonical-first
  - [x] `project_governance.py` 只从 canonical graph 构造治理记录
  - [x] `workspace_governance.py` 只从 canonical graph 构造 workspace 视图
  - [x] `validate_strict_mapping.py` 不再从 `project.toml` 直读业务真相

- [x] 残差 3：去掉 knowledge-base 专属 runtime scene switch 主路径
  - [x] runtime entrypoint 改成 package compile/export 驱动
  - [x] validator 链改成 package compile/export 驱动
  - [x] 移除 `runtime_scene` 手写场景分支控制

- [x] 残差 4：拆掉知识库专属大聚合 runtime bundle 主对象
  - [x] 去掉知识库专属字段伪装成通用 runtime model
  - [x] runtime aggregate 改成通用 package export graph / runtime projection
  - [x] 知识库专属 projection 下沉到 knowledge-base runtime 本地派生层

## 验证与清理

- [x] 清理旧 scene code / 旧 specialized runtime aggregate / 旧 project.toml 业务真相直读路径
- [x] `uv run python scripts/validate_strict_mapping.py`
- [x] `uv run python scripts/validate_strict_mapping.py --check-changes`
- [x] `uv run mypy`
- [x] `uv run python -m unittest`
- [x] `uv run python scripts/materialize_project.py`
- [x] 相关文档只保留最终架构叙事

当前执行账本状态：全部完成。
