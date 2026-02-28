# AGENTS

## 工程执行规范（强制）

### 1. 环境与依赖
- 必须使用 `uv` 管理 Python 环境与依赖。
- 新增依赖必须使用 `uv add <package>`。
- 必须提交 `pyproject.toml` 与 `uv.lock`。

### 2. 运行与验证命令
- 运行主程序：`uv run python src/main.py`
- 严格映射验证：`uv run python scripts/validate_strict_mapping.py`
- 变更传导验证：`uv run python scripts/validate_strict_mapping.py --check-changes`

### 3. 变更执行要求
- 修改标准或代码后，必须执行对应验证命令。
- 禁止在仓库规范文档中引入 `pip install` 作为标准流程。
- 必须启用仓库 `pre-push` hook：`bash scripts/install_git_hooks.sh`。
- 若严格映射验证不通过，禁止推送。

### 4. 规范优先级
- 规范总纲：`standards/L0/规范总纲与树形结构.md`
- 框架设计标准：`standards/L1/框架设计核心标准.md`
- 领域标准：`standards/L2/置物架框架标准.md`
