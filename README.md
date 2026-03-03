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

## 快速启动
### 1) 环境准备
- Python 3.11+
- `uv`（本项目唯一依赖管理工具）

可先确认：
```bash
python --version
uv --version
```

### 2) 安装依赖
在仓库根目录执行：
```bash
uv sync
```

### 3) 生成数据与验证结果
```bash
uv run python src/main.py
```
该命令会生成/更新：
- `docs/frontend_snapshot.json`
- `docs/frontend_snapshot.js`
- `docs/logic_record.json`

### 4) 查看前端最终效果
直接打开：
- `docs/shelf_dashboard.html`

### 5) 执行严格映射验证（建议每次改动后执行）
```bash
uv run python scripts/validate_strict_mapping.py
uv run python scripts/validate_strict_mapping.py --check-changes
```

### 6)（可选）安装 Git 推送前校验 Hook
```bash
bash scripts/install_git_hooks.sh
```

## 前端可视化看板（1单位面积内4置物架验证 + 3D 拖拽旋转）
1. 先生成最新快照数据：
```bash
uv run python src/main.py
```
2. 打开页面查看最终效果：
- 页面：`docs/shelf_dashboard.html`
- 数据：`docs/frontend_snapshot.json`、`docs/frontend_snapshot.js`

看板包含：
- 全部置物架组合可能性（含有效/无效、R1/R2/R3 判定）
- 最小结构数量验证：`vertical_rod >= 4`、`connector >= 4*layers_n`、`horizontal_rod >= 4*layers_n`、`panel >= layers_n`
- 固定验证维度：1 个单位占地面积内放置 4 个置物架（2x2 槽位）
- 层数约束：`1 <= layers_n < 4`（允许 1/2/3 层）
- 目标一致性规则：至少一个置物架满足 `layers_n >= 2`
- 单单位内 4 置物架组合可能性统计（总布局数、有效布局数、按无效置物架数分布）
- 每种组合的 3D 可视模型（鼠标/触控拖拽旋转）
- 2x2 布局验证器（每个置物架槽位选择“组合+层数”变体，实时判定通过/失败）
