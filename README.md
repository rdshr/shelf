# Shelf

Shelf 是一个面向 AI 编程的结构优先仓库。

当前仓库的唯一主路径已经切到下面这条链：

```text
framework/*.md
  -> framework parser / module tree
    -> framework package registry
      -> package entry classes
        -> projects/<project_id>/project.toml
          -> config slicing + package compile
            -> runtime assembly
              -> generated/canonical_graph.json
                -> derived governance / tree / report views
```

## 当前架构

- `framework/*.md` 仍是作者源。
- 每个 framework 文件对应一个代码 package。
- 每个 package 只有一个入口 class，并注册到统一 registry。
- `projects/<project_id>/project.toml` 是唯一项目配置入口。
- `generated/canonical_graph.json` 是唯一机器真相源。
- 其他 manifest / governance / tree / report 都只是 canonical 的派生视图。

## 当前默认项目

- [projects/knowledge_base_basic/project.toml](./projects/knowledge_base_basic/project.toml)

它编译出一个知识库工作台示例：

- 聊天主界面
- 引用抽屉
- 知识库列表与详情页
- 文档详情页
- canonical 派生治理视图

## 快速开始

```bash
uv sync
bash scripts/install_git_hooks.sh
uv run mypy
uv run python scripts/materialize_project.py
uv run python scripts/validate_strict_mapping.py
uv run python src/main.py
```

默认入口：

- App: `http://127.0.0.1:8000/knowledge-base`
- Project Config API: `http://127.0.0.1:8000/api/knowledge/project-config`

## 关键文件

- Framework 解析：
  - [src/framework_ir/parser.py](./src/framework_ir/parser.py)
- Framework package contract / registry：
  - [src/framework_packages/contract.py](./src/framework_packages/contract.py)
  - [src/framework_packages/registry.py](./src/framework_packages/registry.py)
  - [src/framework_packages/builtin_registry.py](./src/framework_packages/builtin_registry.py)
- 编译器：
  - [src/project_runtime/knowledge_base.py](./src/project_runtime/knowledge_base.py)
- 运行时：
  - [src/knowledge_base_runtime/app.py](./src/knowledge_base_runtime/app.py)
- 派生治理：
  - [src/project_runtime/governance.py](./src/project_runtime/governance.py)
- 物化与校验：
  - [scripts/materialize_project.py](./scripts/materialize_project.py)
  - [scripts/validate_strict_mapping.py](./scripts/validate_strict_mapping.py)

## 进一步阅读

- [docs/框架到代码映射与反查覆盖说明.md](./docs/框架到代码映射与反查覆盖说明.md)
- [docs/全链实现框架与跳转逻辑详解.md](./docs/全链实现框架与跳转逻辑详解.md)
- [docs/architecture.md](./docs/architecture.md)
