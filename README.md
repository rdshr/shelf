# Shelf

本仓库提供“通用框架标准 + 置物架领域标准”的双层规范，以及对应 Python 参考实现。

## 文件结构

- `framework_design_standard.md`：通用抽象标准（仓库最高规范）
- `shelf_framework_standard.md`：置物架领域标准（基于通用标准派生）
- `shelf_framework.py`：核心模型（Goal/Boundary/Rule/Hypothesis/Verification/LogicRecord）
- `main.py`：示例运行入口
- `docs/logic_record.json`：示例运行导出的逻辑记录
- `pyproject.toml`：`uv` 管理入口（Python 版本与依赖管理）

## 仓库规范

- `framework_design_standard.md` 是本仓库的最高设计规范与评审基线。
- `shelf_framework_standard.md` 是置物架领域的具体标准，必须遵循通用标准。
- Python 环境与依赖管理统一使用 `uv`。
- 运行命令统一使用 `uv run`。

## 快速运行

```bash
uv sync
uv run python main.py
```

运行后会：
1. 在控制台输出框架快照与验证结果
2. 生成或更新 `docs/logic_record.json`
