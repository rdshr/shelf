# AGENTS

## 工程执行规范（强制）

### 1. 环境与依赖
- 必须使用 `uv` 管理 Python 环境与依赖。
- 新增依赖必须使用 `uv add <package>`。
- 必须提交 `pyproject.toml` 与 `uv.lock`。

### 2. 运行与验证命令
- 运行主程序：`uv run python src/main.py`
- 静态类型检查：`uv run mypy`
- 项目生成产物物化：`uv run python scripts/materialize_project.py`
- 严格映射验证：`uv run python scripts/validate_strict_mapping.py`
- 变更传导验证：`uv run python scripts/validate_strict_mapping.py --check-changes`
- 公开发布与版本说明标准：`specs/code/发布与版本说明标准.md`

### 3. 变更执行要求
- 修改标准或代码后，必须执行对应验证命令。
- Python 代码变更后，必须通过静态类型检查（`uv run mypy`）。
- 项目实例行为变更必须先改 `framework/*.md` 或 `projects/<project_id>/instance.toml`，再执行 `uv run python scripts/materialize_project.py` 生成产物；禁止直接手改 `projects/<project_id>/generated/*`。
- 禁止在仓库规范文档中引入 `pip install` 作为标准流程。
- 必须启用仓库 `pre-push` hook：`bash scripts/install_git_hooks.sh`。
- 若严格映射验证不通过，禁止推送。
- 公开发布时，必须提供符合规范的双语版本说明与正式安装产物。

### 4. 规范优先级
- 规范总纲：`specs/规范总纲与树形结构.md`
- 框架设计标准：`specs/框架设计核心标准.md`
- 领域标准：`framework/shelf/L2-M0-置物架框架标准模块.md`
- 代码规范目录：`specs/code/`
- Python 实现质量（静态类型）：`specs/code/Python实现质量标准.md`
