# Shelf

本仓库采用“多级严格映射”规范。

## 规范入口
- 规范总纲（树形）：`standards/L0/规范总纲与树形结构.md`
- 框架设计核心标准：`standards/L1/框架设计核心标准.md`
- 领域标准（置物架）：`standards/L2/置物架框架标准.md`
- 工程执行规范：`AGENTS.md`

## 映射与验证
- 映射注册：`standards/L3/mapping_registry.json`
- 验证命令：
```bash
uv run python scripts/validate_strict_mapping.py
uv run python scripts/validate_strict_mapping.py --check-changes
```

## 推送守卫（Git Hook）
- 安装命令：
```bash
bash scripts/install_git_hooks.sh
```
- Hook：`.githooks/pre-push`
- 作用：推送前强制执行严格映射验证；若失败则阻止 `git push`

## 远端守卫（GitHub）
- 工作流：`.github/workflows/strict-mapping-gate.yml`
- 作用：远端 `push/pull_request` 到 `main` 时强制执行映射校验
- 启用远端“禁止不通过校验推送”：
```bash
export GITHUB_TOKEN=<repo_admin_token>
bash scripts/configure_branch_protection.sh rdshr/shelf main
```
- 该分支保护会将 `Strict Mapping Gate / strict-mapping` 设为必需检查，并强制 PR 审核与线性历史

## VSCode 插件雏形
- 位置：`tools/vscode/strict-mapping-guard`
- 作用：保存文件后自动运行严格映射校验，并在 Problems 面板报警
- 手动命令：`Strict Mapping: Validate Now`

## 运行
```bash
uv sync
uv run python src/main.py
```

## 看图（总入口）
- 双族分型子页面入口：
  - `docs/examples/type_subpages_valid_2x2x2_dualfamily/index.html`
- 旧版单族分型子页面入口：
  - `docs/examples/type_subpages_valid_2x2x2/index.html`
- 3D 分型总览墙：
  - `docs/examples/type_gallery_3d_valid_2x2x2.html`

## 打开方式（Linux / WSL）
### 方式 1：本地 HTTP 服务（推荐）
```bash
cd /home/xue/code/shelf
uv run python -m http.server 8765
```
浏览器访问：
- `http://localhost:8765/docs/examples/type_subpages_valid_2x2x2_dualfamily/index.html`
- `http://localhost:8765/docs/examples/type_gallery_3d_valid_2x2x2.html`

### 方式 2：WSL 直接调用 Windows 浏览器
```bash
explorer.exe "$(wslpath -w /home/xue/code/shelf/docs/examples/type_subpages_valid_2x2x2_dualfamily/index.html)"
explorer.exe "$(wslpath -w /home/xue/code/shelf/docs/examples/type_gallery_3d_valid_2x2x2.html)"
```

### 方式 3：Linux 桌面环境
```bash
xdg-open /home/xue/code/shelf/docs/examples/type_subpages_valid_2x2x2_dualfamily/index.html
```
如果报 `Couldn't find a suitable web browser`，请用“方式 1”或“方式 2”。

## 我要自己调界面，怎么做
### A. 弹窗交互查看器（非 HTML）
WSL 下建议优先用系统 Python（通常可直接弹窗）：
```bash
PYTHONPATH=src python3 src/interactive_viewer.py
```

`uv` 方式（如果你的 `uv` Python 已支持 Tk/Qt）：
```bash
uv run python src/interactive_viewer.py
```
若看到 `FigureCanvasAgg is non-interactive`，说明当前解释器无 GUI 后端，请切回上面的 `python3` 命令，或执行：
```bash
uv python install --reinstall 3.12
```
界面控件：
- `x_cells / y_cells / layers`：离散空间大小
- `cell_w / cell_d / layer_h`：几何尺寸
- `allow_empty`：是否允许空层
- `valid / invalid / all`：筛选分型
- `Prev / Next`：切换分型
- `Recompute`：按当前参数重新枚举

### B. 重新生成网页分型墙（批量）
生成“每个类型组一个子页面（含组内 3D）”：
```bash
uv run python src/generate_type_subpages.py \
  --x-cells 2 --y-cells 2 --layers 2 \
  --filter valid \
  --output-dir docs/examples/type_subpages_valid_2x2x2_dualfamily \
  --group-3d-columns 8
```

生成单页 3D 总览墙：
```bash
uv run python src/generate_type_gallery_3d.py \
  --x-cells 2 --y-cells 2 --layers 2 \
  --filter valid \
  --output-html docs/examples/type_gallery_3d_valid_2x2x2.html \
  --columns 16
```

常用可调参数：
- `--x-cells --y-cells --layers`：离散边界
- `--filter valid|invalid|all`：筛选范围
- `--columns`：3D 墙局部排布密度
- `--group-3d-columns`：子页面内组级 3D 排布密度
