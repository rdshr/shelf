# Shelf

本仓库采用“多级严格映射”规范。

## 规范入口
- 规范总纲（树形）：`standards/standards_tree.md`
- 框架设计核心标准：`standards/framework_design_standard.md`
- 领域标准（置物架）：`standards/shelf_framework_standard.md`
- 工程执行规范：`AGENTS.md`

## 映射与验证
- 映射注册：`standards/mapping_registry.json`
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

## VSCode 插件雏形
- 位置：`tools/vscode/strict-mapping-guard`
- 作用：保存文件后自动运行严格映射校验，并在 Problems 面板报警
- 手动命令：`Strict Mapping: Validate Now`

## 运行
```bash
uv sync
uv run python src/main.py
```
