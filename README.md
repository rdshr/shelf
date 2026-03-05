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

## 启动前端（实时生成）
先生成页面与初始数据：
```bash
uv run python src/main.py
```

再启动前端服务（含实时 `A/N` 变体生成接口）：
```bash
uv run python src/runtime_server.py --host 127.0.0.1 --port 4173
```

浏览器打开：
```text
http://127.0.0.1:4173/groups.html
```
