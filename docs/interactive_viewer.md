# 本地窗口交互查看器

## 目标
不通过 html，直接打开本地窗口进行 3D 动态查看与参数调整。

## 启动命令
WSL 下优先（推荐）：
```bash
PYTHONPATH=src python3 src/interactive_viewer.py
```

`uv` 方式：
```bash
uv run python src/interactive_viewer.py
```

若报 `FigureCanvasAgg is non-interactive`，表示当前解释器没有可用 GUI 后端，请改用系统 Python，或先执行：
```bash
uv python install --reinstall 3.12
```

## 交互说明
- `x_cells / y_cells / layers`：离散网格尺寸（为保证实时性，x/y 限制在 1~2）
- `cell_w / cell_d / layer_h`：几何尺寸缩放
- `allow_empty`：是否允许空层
- `valid / invalid / all`：结构筛选
- `Prev / Next`：切换当前展示结构
- `Recompute`：按当前离散参数重新枚举

## 备注
- 这是本地 GUI 窗口，依赖图形环境。
- 若在纯无头环境（无 X11/Wayland）运行，窗口无法弹出。
- 当前环境里 `uv` 管理的 Python 缺少 Tk/Qt 所需系统库（例如 `libEGL.so.1`），因此 `uv run` 可能无法弹窗。
