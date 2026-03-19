# 四层主架构重建说明

## 1. 唯一主链

仓库主链固定为：

`Framework -> Config -> Code -> Evidence`

这四层之外，不再存在额外的独立主层。

## 2. 各层职责

### Framework

- 人类作者源只允许是 `framework/*.md`
- 每个 framework markdown 文件必须对应一个独立 `FrameworkModule` class
- 每个 `B*` 必须对应一个独立 `Base` class
- 每个 `R*` 必须对应一个独立 `Rule` class
- Framework 只定义结构空间、参数、基、规则、能力与验证，不落地项目实例值

### Config

- `projects/<project_id>/project.toml` 是唯一配置入口
- Config 只允许分成两块：
  - `communication`
  - `exact`
- `communication` 用于人与 AI 的结构化沟通要求
- `exact` 用于 Code 层精确消费的字段、参数、路径和策略
- `ConfigModule` 只能消费对应 `FrameworkModule` export，并导出：
  - `communication_export`
  - `exact_export`
  - `compiled_config_export`

### Code

- `CodeModule` 只能消费对应 `ConfigModule.exact_export`
- Code 层是第一次真正落地到实现的层
- 代码绑定、运行时装配、页面/API/数据结构导出都在本层发生
- Code 不允许直接读取 framework markdown，也不允许直接读取 `communication`

### Evidence

- `EvidenceModule` 只能消费对应 `CodeModule` export
- Evidence 负责验证结果、运行观察、快照、追溯材料和 GUI 材料
- Evidence 不允许回头拼多层内部状态形成新的平行真相源

## 3. 唯一机器真相

- 全仓库唯一机器真相源为 `generated/canonical.json`
- 该 JSON 必须天然分层表达：
  - `framework`
  - `config`
  - `code`
  - `evidence`
  - 相邻层连接关系
- 导航、验证、报告、追溯、GUI 数据源都必须消费这个 canonical JSON
- 其他视图只能是 canonical 的派生物，不能再承担独立真相职责

## 4. 组合原则

- 只允许组合，不允许用继承表达框架语义
- 模块关系通过显式装配表达：
  - `FrameworkModule -> ConfigModule -> CodeModule -> EvidenceModule`
- 若某个功能需要代码绑定，必须在 canonical JSON 中留下正式绑定：
  - 模块绑定
  - 参数绑定
  - 基绑定

## 5. 当前仓库落地要求

- 重写 `project.toml`，只保留 `communication / exact`
- 重建知识库项目的四层模块链
- 重建验证逻辑，使其从 canonical JSON 或 Code/Evidence export 收敛
- 重写 VS Code 扩展的默认命令与导航数据源，使其不再调用旧脚本

## 6. 完成判断

只有以下同时成立，才视为完成：

- 仓库只讲一种架构语言
- 不再存在旧核心文件承担真实主职责
- 每个 framework markdown 都能解析成正式 `FrameworkModule / Base / Rule` class
- `project.toml` 只保留 Config 层语义
- Code 层承担第一次真实实现落点
- Evidence 层承担验证、快照和追溯职责
- 全部主流程收敛到 `generated/canonical.json`
