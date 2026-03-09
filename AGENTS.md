# AGENTS

## 仓库认知前提（强制）
- 框架不是某个项目的模板，而是 AI 编程时代的人和 AI 之间的共同结构语言。
- 仓库主分层应保持 `Framework -> Product Spec -> Implementation Config -> Code -> Evidence` 的单向收敛。
- 当前若尚未把 `Product Spec` 与 `Implementation Config` 拆成独立文件，则临时合并承载文件也必须能被解释为“产品真相”与“实现细化”的组合，不得反向修改框架边界、规则与基定义。
- `projects/<project_id>/product_spec.toml` 与 `projects/<project_id>/implementation_config.toml` 默认应使用中文注释，作为人与 AI 协作讨论的主入口。
- 上述 TOML 文件在篇幅可控时，应优先提供详细注释而不是极简标签；至少在文件头和每个主 section 前说明职责边界、讨论重点与与相邻层的分界。
- `Product Spec` 注释必须解释产品真相，不得混入仅属于实现层的技巧；`Implementation Config` 注释必须解释实现细化，不得伪装成产品真相。
- 面向 `framework/*.md` 的标准模板起手能力属于仓库基本作者入口，不得移除。当前保底入口为 ArchSync 的 `@framework` 模板与显式插入命令；若未来重构，必须提供同等直接、默认可用、可测试的替代能力。

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
- 项目行为变更必须先改 `framework/*.md`、`projects/<project_id>/product_spec.toml` 或 `projects/<project_id>/implementation_config.toml`，再执行 `uv run python scripts/materialize_project.py` 生成产物；禁止直接手改 `projects/<project_id>/generated/*`。
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
