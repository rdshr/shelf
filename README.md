# Shelf

Shelf 是一个面向 AI 编程的结构优先仓库。

仓库现在只保留一条主链：

```text
Framework -> Config -> Code -> Evidence
```

- `framework/*.md` 是唯一 Framework 作者源
- `projects/<project_id>/project.toml` 是唯一 Config 入口
- `Code` 层第一次落地到真实实现
- `Evidence` 层负责验证、快照、追溯和 GUI 材料
- `projects/*/generated/canonical.json` 是唯一机器真相源

## 样例项目

- [projects/message_queue_basic/project.toml](./projects/message_queue_basic/project.toml)

该项目用于验证 message_queue 场景的四层主链物化与校验流程。

## 快速开始

```bash
uv sync
bash scripts/install_git_hooks.sh
uv run mypy
uv run python scripts/materialize_project.py
uv run python scripts/validate_canonical.py
uv run python src/main.py
```

默认入口：

- App: `http://127.0.0.1:8000/`
- Project Config API: `http://127.0.0.1:8000/project/config`
- Correspondence API: `http://127.0.0.1:8000/correspondence`

## 关键文件

- Framework 解析：
  - [src/framework_ir/parser.py](./src/framework_ir/parser.py)
- 四层编译器：
  - [src/project_runtime/compiler.py](./src/project_runtime/compiler.py)
  - [src/project_runtime/framework_layer.py](./src/project_runtime/framework_layer.py)
  - [src/project_runtime/config_layer.py](./src/project_runtime/config_layer.py)
  - [src/project_runtime/code_layer.py](./src/project_runtime/code_layer.py)
  - [src/project_runtime/evidence_layer.py](./src/project_runtime/evidence_layer.py)
- 运行时：
  - [src/project_runtime/runtime_app.py](./src/project_runtime/runtime_app.py)
- 物化与校验：
  - [scripts/materialize_project.py](./scripts/materialize_project.py)
  - [scripts/validate_canonical.py](./scripts/validate_canonical.py)

## 进一步阅读

- [docs/four-layer-architecture.md](./docs/four-layer-architecture.md)
