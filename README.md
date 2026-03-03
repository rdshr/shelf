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

## 组合验证控制台（新环境启动）
以下步骤可在新环境直接启动控制台：

1. 安装并准备 `uv`（如未在 PATH）：
```bash
# 若 `uv` 命令不可用，先执行（Linux/macOS）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 让当前 shell 能找到 uv
export PATH=\"$HOME/.local/bin:$PATH\"
```

2. 同步环境依赖：
```bash
uv sync
```

3. 生成组合与验证结果（默认执行穷举分型 + 同构去重 + 三阶段验证）：
```bash
uv run python scripts/generate_shelf_combinations.py
```
说明：穷举过程为“组合原则驱动穷举”，不是先无约束穷举再筛选。

4. 启动控制台静态服务：
```bash
uv run python -m http.server 8080
```

5. 浏览器打开：
`http://127.0.0.1:8080/web/viewer/`

页面特性：
- 穷举后的分型组合列表（支持通过/失败筛选）
- Three.js 3D 交互（拖拽旋转、缩放、平移）
- 组合验证页支持配置组合原则（R1-R6 与数量上限），点击按钮后按配置组合并展示满足组合原则的全部结果
- 三阶段验证结果（组合原则 / 边界 / 目标）
- 统计图（通过率、分数分布、分型通过率）
