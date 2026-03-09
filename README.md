# Shelf

**AI coding framework for executable architecture, strict mapping, and project materialization.**

Shelf 是一个面向 **AI 编程 / AI-assisted software engineering** 的框架仓库。它把框架文档、边界定义、项目配置、生成产物、严格校验、VSCode 导航放进同一条链路，让 AI 写代码时不是只靠 prompt，而是基于可执行规范、可追溯关系和可验证结果协作。

In short: **Shelf helps teams turn framework docs into a real engineering system**. You define the structure in Markdown, validate it with code, materialize project artifacts, and inspect the whole graph in VSCode.

## Why Shelf

很多 AI 编程项目都卡在同一个问题上：

- 文档、配置、代码、生成产物彼此脱节
- AI 能快速生成代码，但很难持续遵守边界和结构约束
- 项目越大，越难回答“这个模块为什么存在、来源是什么、改动会影响哪里”

Shelf 的目标不是做一个“会写代码的聊天界面”，而是提供一套 **AI-native engineering workflow**：

- 用 `framework/*.md` 作为框架级事实来源
- 用 `projects/<project_id>/instance.toml` 固化实例级边界
- 用脚本把规范物化为项目产物
- 用严格映射验证保证结构一致性
- 用 VSCode 插件把模块树、跳转、问题定位接到日常开发里

## Core Capabilities

- **Executable framework specs**
  - 在 `framework/<module>/Lx-Mn-*.md` 中定义能力、边界、基、规则与验证。
- **Strict mapping validation**
  - 通过 `scripts/validate_strict_mapping.py` 检查规范、代码、配置和产物是否一致。
- **Project materialization**
  - 通过 `scripts/materialize_project.py` 从框架和实例配置生成项目产物。
- **AI-friendly traceability**
  - 模块、规则、边界、实例 section、生成产物都能被追踪和跳转。
- **ArchSync VSCode extension**
  - 在 VSCode 里直接查看框架树、运行校验、定位问题、跳转文档。
- **Runnable reference app**
  - 仓库内置一个知识库 demo，可直接启动验证整条链路。

## Who This Is For

- 想做 **spec-driven AI coding** 的团队
- 想把“AI 生成代码”升级成“AI 在结构约束下协作开发”的工程团队
- 想做知识库、内部工作台、框架化前后端产品的人
- 想把文档、配置、生成器、运行时放进一个可维护系统的人

## Quick Start

### 1. Install dependencies

```bash
uv sync
```

### 2. Enable the required git hook

```bash
bash scripts/install_git_hooks.sh
```

### 3. Run the core validations

```bash
uv run mypy
uv run python scripts/validate_strict_mapping.py
uv run python scripts/validate_strict_mapping.py --check-changes
```

### 4. Materialize project artifacts

```bash
uv run python scripts/materialize_project.py
```

### 5. Start the demo app

```bash
uv run uvicorn --app-dir src project_runtime.app_factory:app --reload
```

默认入口：

- Page: `http://127.0.0.1:8000/knowledge-base`
- Workbench spec: `http://127.0.0.1:8000/api/knowledge/workbench-spec`
- API: `http://127.0.0.1:8000/api/knowledge/documents`

## How The Workflow Fits Together

1. **Define the framework**
   - 在 `framework/` 里写模块标准，例如能力声明、边界定义、最小可行基、组合规则。
2. **Configure a project instance**
   - 在 `projects/<project_id>/instance.toml` 里填写实例边界和数据。
3. **Materialize the project**
   - 由框架和实例配置生成 `projects/<project_id>/generated/*`。
4. **Validate changes**
   - 校验规范、代码和配置是否仍然满足严格映射。
5. **Inspect and navigate**
   - 在 ArchSync 中查看模块结构图、节点关系和问题定位。

## Repository Map

- `specs/`
  - 规范总纲、框架设计核心标准、代码规范目录
- `framework/`
  - 框架级模块定义，按领域拆分
- `projects/`
  - 项目实例配置与物化产物
- `mapping/`
  - 映射注册表与结构关系
- `scripts/`
  - 生成、物化、校验、发布辅助脚本
- `src/`
  - 运行时模板、生成器内核、参考实现
- `tools/vscode/archsync/`
  - VSCode 插件源码

## Important Entry Points

### Specs and standards

- 规范总纲：`specs/规范总纲与树形结构.md`
- 框架设计核心标准：`specs/框架设计核心标准.md`
- 代码规范目录：`specs/code/`
- 工程执行规范：`AGENTS.md`

### Frameworks

- 置物架领域：`framework/shelf/Lx-M0-*.md`
- 前端通用框架：`framework/frontend/Lx-Mn-*.md`
- 知识库领域框架：`framework/knowledge_base/Lx-Mn-*.md`
- 知识库接口：`framework/backend/Lx-M0-*.md`

### Project instances

- 实例层说明：`projects/README.md`
- 当前样板：`projects/knowledge_base_basic/instance.toml`

## ArchSync VSCode Extension

ArchSync 是这个仓库配套的 VSCode 插件，目标不是做一个泛用聊天助手，而是做一个 **framework-aware AI coding companion**。

它提供：

- 侧边栏主页：一键打开框架树、刷新树图、运行映射校验、查看问题列表
- 结构图 Webview：模块树、层级关系、节点详情、缩放、拖拽、侧栏收起
- 文档导航：从模块引用、边界引用、规则引用直接跳到对应 Markdown 或实例配置
- 保存即校验：相关文件变更后自动运行严格映射验证，并同步到 Problems 面板

本地安装：

```bash
bash tools/vscode/archsync/install_local.sh
```

公开安装：

- GitHub Releases: https://github.com/xueyu888/framework/releases
- 插件源码说明：`tools/vscode/archsync/README.md`

主要命令：

- `ArchSync: Open Framework Tree`
- `ArchSync: Refresh Framework Tree`
- `ArchSync: Validate Mapping Now`
- `ArchSync: Show Mapping Issues`

## Knowledge Base Demo

仓库内置了一个“项目实例配置驱动”的知识库 demo，用来演示：

- 前端框架 + 领域框架 + 后端接口如何组合
- `framework/*.md + instance.toml -> generated/*` 的物化链路
- 运行时模板如何从实例配置构建出真实应用

相关入口：

- 项目配置：`projects/knowledge_base_basic/instance.toml`
- 运行时模板：`src/knowledge_base_demo/`
- 物化产物：`projects/knowledge_base_basic/generated/`

手动物化：

```bash
uv run python scripts/materialize_project.py --project projects/knowledge_base_basic/instance.toml
```

## Framework Tree and Visual Outputs

框架树总入口：

- `docs/hierarchy/shelf_framework_tree.html`

重新生成框架树：

```bash
uv run python scripts/generate_framework_tree_hierarchy.py \
  --source framework \
  --framework-dir framework \
  --output-json docs/hierarchy/shelf_framework_tree.json \
  --output-html docs/hierarchy/shelf_framework_tree.html
```

其他可视化示例：

- 双族分型子页面：`docs/examples/type_subpages_valid_2x2x2_dualfamily/index.html`
- 旧版单族分型子页面：`docs/examples/type_subpages_valid_2x2x2/index.html`
- 3D 分型总览墙：`docs/examples/type_gallery_3d_valid_2x2x2.html`

## Engineering Rules

这个仓库有几条铁律：

- 必须使用 `uv` 管理 Python 环境和依赖
- 不直接修改 `projects/<project_id>/generated/*`
- 项目行为变更先改 `framework/*.md` 或 `projects/<project_id>/instance.toml`
- 推送前必须通过严格映射验证
- 公开发布必须遵守 `specs/code/发布与版本说明标准.md`

对应守卫：

- 本地 `pre-push` hook：`.githooks/pre-push`
- GitHub 工作流：`.github/workflows/strict-mapping-gate.yml`

## Search-Friendly Summary

如果你是在找这些方向，这个仓库就是相关的：

- AI coding framework
- AI programming workflow
- AI-native software architecture
- executable specification
- spec-driven development
- strict mapping validation
- Markdown-driven architecture
- VSCode extension for framework navigation
- knowledge base app scaffold
- traceable project generation

## Project Status

当前仓库更接近 **active framework repository + executable reference implementation**，适合继续扩展为：

- 更完整的 AI-native app framework
- 更强的生成器与验证器
- 更成熟的 VSCode / Marketplace 体验
- 更标准的对外模板与公开示例

如果你希望在 AI 编程里得到的不只是“更快写代码”，而是“让结构、文档、配置、生成产物和运行时保持一致”，Shelf 的重点就在这里。
