# Contributing to Shelf

Shelf 只接受一套主架构语言：

`Framework -> Config -> Code -> Evidence`

`projects/*/generated/canonical.json` 是唯一机器真相源。

## Read This First

- [docs/four-layer-architecture.md](./docs/four-layer-architecture.md)
- [specs/规范总纲与树形结构.md](./specs/规范总纲与树形结构.md)
- [specs/框架设计核心标准.md](./specs/框架设计核心标准.md)
- [AGENTS.md](./AGENTS.md)

## Environment

使用 `uv` 管理依赖与执行：

```bash
uv sync
bash scripts/install_git_hooks.sh
```

## Required Checks

影响 framework、project config、runtime、validation 或 generated evidence 的改动，提交前至少执行：

```bash
uv run mypy
uv run python scripts/materialize_project.py
uv run python scripts/validate_canonical.py
```

## Source-Of-Truth Rules

- 不要手改 `projects/<project_id>/generated/*`
- 行为变化先改 `framework/*.md` 或 `projects/<project_id>/project.toml`
- `project.toml` 只保留：
  - `framework`
  - `communication`
  - `exact`

## Framework Authoring Rules

Framework 模块必须显式写出：

- capability
- boundary
- minimum viable bases
- combination rules
- verification

仓库保留 `@framework` 模板和 Shelf AI 插入命令作为默认作者入口。

## Project Authoring Rules

`projects/<project_id>/project.toml` 是唯一项目配置入口。

保持注释清晰并明确分层：

- `[framework]`
  只声明项目装配哪些 framework 模块
- `[communication]`
  只写人与 AI 协作的结构化沟通要求
- `[exact]`
  只写 Code 层可精确消费的字段、参数、路径与策略

尽量保留中文注释，不要让 prose 变成机器真相。

## Pull Request Notes

PR 里需要说明：

- 改动属于哪一层
- 为什么落在这一层
- 跑了哪些校验
- 是否影响 `generated/canonical.json` 或其派生产物
