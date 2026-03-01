# 本地窗口交互查看器

## 目标
不通过 html，直接打开本地窗口进行 3D 动态查看与参数调整。

## 启动命令
```bash
uv run python src/interactive_viewer.py
```

若 `uv` 环境报 `tkagg/qt` 后端错误，可使用系统 Python（已实测可进入 GUI 事件循环）：
```bash
PYTHONPATH=src python3 src/interactive_viewer.py
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
