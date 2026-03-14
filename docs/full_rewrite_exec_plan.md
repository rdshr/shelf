# 全仓 rewrite 收口执行账本

审查基准文档：

- [最终架构重构验收标准.md](./最终架构重构验收标准.md)

## 当前剩余任务

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
