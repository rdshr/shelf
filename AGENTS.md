# AGENTS

## 仓库认知前提（强制）
- 框架不是某个项目的模板，而是 AI 编程时代的人和 AI 之间的共同结构语言。
- 仓库主分层应保持 `Framework -> Config -> Code -> Evidence` 的单向收敛。
- `projects/<project_id>/project.toml` 是项目配置唯一入口；配置物理上统一，逻辑上必须明确区分 `framework / communication / exact`。
- `project.toml` 默认应使用中文注释，作为人与 AI 协作讨论的主入口。
- 上述 TOML 文件在篇幅可控时，应优先提供详细注释而不是极简标签；至少在文件头和每个主 section 前说明职责边界、讨论重点与与相邻层的分界。
- `framework` 负责声明项目装配哪些 framework 模块；`communication` 负责人与 AI 的结构化沟通要求；`exact` 负责 Code 层精确消费字段。
- 面向 `framework/*.md` 的标准模板起手能力属于仓库基本作者入口，不得移除。当前保底入口为 Shelf AI 的 `@framework` 模板与显式插入命令；若未来重构，必须提供同等直接、默认可用、可测试的替代能力。

## 核心规则
1. `framework/*.md` 是作者源。不要把 framework 真相源改成 schema、config 或生成物。
2. 每个 framework 文件必须解析成一个独立 `FrameworkModule` class。
3. 每个 `B*` 必须是一等 `Base` class；每个 `R*` 必须是一等 `Rule` class。
4. `ConfigModule` 只消费对应 `FrameworkModule` export；`CodeModule` 只消费对应 `ConfigModule.exact_export`；`EvidenceModule` 只消费对应 `CodeModule` export。
5. 架构关系只允许用组合，不允许用继承。
6. 项目由三部分决定：framework markdown、统一 project config、真实 code 实现。不要把项目做成手写特化分支。
7. `communication` 只能承载结构化沟通要求；`exact` 只能承载 Code 层精确消费字段。
8. 自然语言说明只能做补充；机器判定必须依赖结构化字段。
9. `generated/canonical.json` 是唯一机器真相源。其他 tree、report、evidence view 都只能是它的派生视图。
10. 不要恢复旧的核心架构。不要保留并行真相源，不要把旧系统换个名字继续跑。
11. 写任何代码前，先评估是否存在更简洁的等效实现；若存在必须优先采用。只有在正确性、性能、兼容性或可测试性明确需要时，才允许增加实现复杂度。
12. 禁止硬编码门禁/依赖/项目路径。涉及模块选择、跨层依赖、root 关系、项目定位时，必须基于 framework upstream、project 配置或运行时发现，不得写死 `frontend/knowledge_base/backend` 固定分支或 `projects/project.toml` 固定回退。
13. 防回退要求：提交前必须通过 `tests/test_no_hardcode_guard.py`，若出现命中项必须先改为配置化/结构化来源再继续。

## 默认工作顺序
1. 读相关 `framework/*.md`
2. 找对应 `FrameworkModule / ConfigModule / CodeModule / EvidenceModule`
3. 校验 `communication / exact`
4. 修改 code composition 或 code internals
5. 更新 `generated/canonical.json`
7. 更新所有 derived views 和 validation outputs
8. 始终保持架构单一，不要创建 side channel

## 对话触发守卫（强制）
- AGENTS 只认最终生效的 `shelf.*` 值作为门禁配置语义入口，不再维护独立目录常量；不再在 AGENTS 里区分配置来自哪个文件承载。
- 门禁范围只看：`shelf.intentGateGuardedPathPrefixes` 与 `shelf.intentGateIgnoredPathPrefixes`。若未显式覆盖，插件默认受检目录为：`framework/`、`framework_drafts/`、`projects/`、`src/project_runtime/`、`scripts/`。
- 检查开关只看：`shelf.intentGateEnabled`、`shelf.intentGateRunChangeValidationBeforeGrant`、`shelf.intentGateTemporaryBypasses`。当 `intentGateEnabled = false`，或 `intentGateRunChangeValidationBeforeGrant = false`，或 `intentGateTemporaryBypasses` 包含 `grant_pre_validation` / `*` 时，可临时关闭“改前 check-changes 检查”。
- 只要用户在 AI 对话中提出“改代码/改配置/改脚本/改模块”诉求（无论中文或英文），且目标修改路径命中“门禁作用范围”且未命中上述关闭条件，AI 在开始任何文件修改前，必须先执行：`uv run python scripts/validate_canonical.py --check-changes`。
- bootstrap 例外：若 `--check-changes` 失败原因为“当前仓库不存在任何 `projects/*/project.toml`”，可进入 bootstrap 模式继续生成首个 `project.toml` 与对应代码/产物；生成后必须立刻恢复常规门禁并重新执行 `--check-changes`。
- 若上述命令失败，或输出包含 `FRAMEWORK_VIOLATION`，AI 必须拒绝继续修改命中门禁范围的文件，并明确提示“先由人修改 framework，再继续实现层变更”。
- AI 完成命中门禁范围的修改后，提交前必须再次执行：`uv run python scripts/validate_canonical.py --check-changes`，除非命中上述临时关闭条件；未关闭时必须确保未引入新的 framework 语义越权。
- 该守卫属于“对话级自动触发”，不得要求用户手工复制临时 `project.toml` 才触发。
- 当用户把 `intentGateGuardedPathPrefixes` 配置为仅 `framework/` 时，门禁只对 `framework/**` 生效。

### 对话意图到框架映射门禁（强制）
- 用户提出“新增/调整功能”时，AI 必须先完成“需求 -> framework 显式映射”再动实现层文件。
- 映射结果至少应包含：`module_id`、对应 `boundary_id`（或明确的 Rule/Base 约束）、以及落点 `exact.*` 路径。
- 若 AI 不能给出上述映射，或映射结果无法在当前 framework 中找到对应约束，AI 必须拒绝修改命中门禁范围的实现文件，并提示“该需求尚未进入 framework，请先由人修改 framework”。
- 在“映射失败”场景中，AI 不得通过“直接改 config 或 code”规避框架前置；不得创建平行真相路径。
- `framework/**` 是人类作者源；AI 对 framework 默认只读。需要新增框架能力时，AI 只能给出修改建议，不得直接落盘 framework 文件。

## 工程执行规范（强制）

### 1. 环境与依赖
- 必须使用 `uv` 管理 Python 环境与依赖。
- 新增依赖必须使用 `uv add <package>`。
- 必须提交 `pyproject.toml` 与 `uv.lock`。

### 2. 运行与验证命令
- 运行主程序：`uv run python src/main.py`
- 静态类型检查：`uv run mypy`
- 硬编码守卫：`uv run pytest -q tests/test_no_hardcode_guard.py`
- 项目生成产物物化：`uv run python scripts/materialize_project.py`
- canonical 验证：`uv run python scripts/validate_canonical.py`
- 变更传导验证：`uv run python scripts/validate_canonical.py --check-changes`
- 公开发布与版本说明标准：`specs/code/发布与版本说明标准.md`

### 3. 变更执行要求
- 修改标准或代码后，必须执行对应验证命令。
- Python 代码变更后，必须通过静态类型检查（`uv run mypy`）。
- 触及 `src/project_runtime/**`、`src/frontend_kernel/**`、`tools/vscode/shelf-ai/**` 或 `scripts/**` 时，必须执行硬编码守卫测试（`uv run pytest -q tests/test_no_hardcode_guard.py`）。
- 项目行为变更必须先改 `framework/*.md` 或 `projects/<project_id>/project.toml`，再执行 `uv run python scripts/materialize_project.py` 生成产物；禁止直接手改 `projects/<project_id>/generated/*`。
- 禁止在仓库规范文档中引入 `pip install` 作为标准流程。
- 必须启用仓库 `pre-push` hook：`bash scripts/install_git_hooks.sh`。
- 若 canonical 验证不通过，禁止推送。
- 公开发布时，必须提供符合规范的双语版本说明与正式安装产物。
- 公开发布版本说明必须按“上一版本 tag -> 当前版本 tag”的完整提交区间汇总；禁止只按单次会话/单次对话编写发布说明（示例：`shelf-ai-v0.1.20..shelf-ai-v0.1.21`）。

### 4. 规范优先级
- 规范总纲：`specs/规范总纲与树形结构.md`
- 框架设计标准：`specs/框架设计核心标准.md`
- 领域标准：按项目选中的 framework 根模块（示例：`framework/message_queue/L1-M0-消息队列标准模块.md`）
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

### 4.2 Shelf AI 契约与技术方案同步（强制）
- 只要任务涉及 `tools/vscode/shelf-ai/**`，无论是代码、配置、README、release notes、tree 视图脚本，还是与插件直接耦合的导航 / evidence / validation 路径，都必须先阅读 `tools/vscode/shelf-ai/插件设计与实现契约.md`。
- Shelf AI 插件的后续设计与实现，默认以 `tools/vscode/shelf-ai/插件设计与实现契约.md` 作为一线约束；README、零散注释、临时讨论或历史实现都不得覆盖该文档。
- 凡是插件相关实现发生变化，必须同步审查该契约文档是否需要更新；若实现语义已变而契约文档未更新，则该实现视为未完成。
- 修改以下文件时，默认应同时检查该契约文档是否需要更新：
  - `tools/vscode/shelf-ai/extension.js`
  - `tools/vscode/shelf-ai/guarding.js`
  - `tools/vscode/shelf-ai/framework_navigation.js`
  - `tools/vscode/shelf-ai/framework_completion.js`
  - `tools/vscode/shelf-ai/evidence_tree.js`
  - `tools/vscode/shelf-ai/validation_runtime.js`
  - `tools/vscode/shelf-ai/package.json`
  - `tools/vscode/shelf-ai/README.md`
  - `tools/vscode/shelf-ai/release-notes/*`
  - 与插件直接耦合的 tree / validation / materialize 脚本
- `tools/vscode/shelf-ai/插件设计与实现契约.md` 第 13 章《仓库技术方案（当前讨论基线）》是本仓库技术方案讨论与落地的固定入口。
- 以后凡是修改本仓库代码（不限语言、不限目录），提交前都必须审查第 13 章是否需要更新。
- 若实现语义、模块边界、交互行为、依赖策略、验证门槛任一发生变化，必须同步更新第 13 章；未更新视为任务未完成。
- 若本次代码变更不影响第 13 章，也必须在提交说明或评审说明中显式声明“技术方案章节无变更”。
