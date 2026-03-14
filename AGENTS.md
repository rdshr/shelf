# AGENTS

## 仓库认知前提（强制）
- 框架不是某个项目的模板，而是 AI 编程时代的人和 AI 之间的共同结构语言。
- 仓库主分层应保持 `Framework Markdown -> Package Registry -> Project Config -> Code -> Evidence` 的单向收敛。
- `projects/<project_id>/project.toml` 是项目配置唯一入口；配置物理上统一，逻辑上必须明确区分 `selection / truth / refinement / narrative`。
- `project.toml` 默认应使用中文注释，作为人与 AI 协作讨论的主入口。
- 上述 TOML 文件在篇幅可控时，应优先提供详细注释而不是极简标签；至少在文件头和每个主 section 前说明职责边界、讨论重点与与相邻层的分界。
- `selection` 负责模块树选择；`truth` 负责产品真相；`refinement` 负责实现细化；`narrative` 只负责解释，不得替代机器判定字段。
- 面向 `framework/*.md` 的标准模板起手能力属于仓库基本作者入口，不得移除。当前保底入口为 Shelf AI 的 `@framework` 模板与显式插入命令；若未来重构，必须提供同等直接、默认可用、可测试的替代能力。

## 核心规则
1. `framework/*.md` 是作者源。不要把 framework 真相源改成 schema、config 或生成物。
2. 一个 framework 文件对应一个 code package。一个 package 只允许有一个入口 class。
3. 每个入口 class 都必须实现统一的 `Framework Package Contract`，并注册到显式 `registry`。
4. `registry` 是 framework 文件与代码实现的一一绑定真相。未注册的是悬空包；未绑定实现的 framework 文件是未实现模块；冲突注册必须报错。
5. 架构关系只允许用组合，不允许用继承。上层通过 import 子 package、分发配置、调用 `compile / export` 来装配下层。
6. 项目由三部分决定：framework tree、统一 project config、registered packages。不要把项目做成手写特化分支。
7. `product truth` 和 `implementation refinement` 属于统一 project config，但逻辑上必须分区。配置必须按模块树逐层切片分发；package 只能消费自己声明的配置。
8. 自然语言说明只能做补充；机器判定必须依赖结构化字段。不要让 narrative 变成可执行真相。
9. `generated/canonical_graph.json` 是唯一机器真相源。其他 manifest、tree、report、governance view 都只能是它的派生视图。
10. 不要恢复旧的核心架构。不要保留并行真相源，不要保留旧的 project-wide aggregate core model，不要把旧系统换个名字继续跑。

## 默认工作顺序
1. 读相关 `framework/*.md`
2. 找对应 package
3. 校验 entry class 与 `registry`
4. 校验 `config contract`
5. 修改 package composition 或 package internals
6. 更新 `generated/canonical_graph.json`
7. 更新所有 derived views 和 validation outputs
8. 始终保持架构单一，不要创建 side channel

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
- 项目行为变更必须先改 `framework/*.md` 或 `projects/<project_id>/project.toml`，再执行 `uv run python scripts/materialize_project.py` 生成产物；禁止直接手改 `projects/<project_id>/generated/*`。
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

### 4.1 按语言读取标准（强制）
- 修改 `.py` 文件前，必须阅读 `specs/code/Python实现质量标准.md`。
- 修改 `.ts` 文件前，必须阅读 `specs/code/TypeScript实现质量标准.md`。
- 修改 `.tsx` 文件前，必须同时阅读 `specs/code/TypeScript实现质量标准.md` 与 `specs/code/HTML与模板实现质量标准.md`。
- 修改 `.js/.mjs/.cjs` 文件前，必须阅读 `specs/code/JavaScript实现质量标准.md`。
- 修改 `.jsx` 文件前，必须同时阅读 `specs/code/JavaScript实现质量标准.md` 与 `specs/code/HTML与模板实现质量标准.md`。
- 修改 `.html` 文件前，必须阅读 `specs/code/HTML与模板实现质量标准.md`。
- 修改 `.css/.scss/.less` 文件前，必须阅读 `specs/code/前端样式实现质量标准.md`。
- 多语言或混合语法文件必须同时满足对应标准；冲突时按更严格者执行。
- 语言到标准的机器可读索引为 `specs/code/代码语言标准索引.toml`；新增语言或文件类型时，必须先更新该索引与本节，再允许 AI 或人工按新语言写代码。
