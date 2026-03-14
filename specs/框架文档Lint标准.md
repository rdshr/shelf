# 框架文档Lint标准

## 0. 定位

本文件定义 framework Markdown 的表达协议，以及它与 package registry、project config、canonical evidence 的对齐约束。

## 1. 适用范围

- `specs/*.md`
- `framework/<domain>/Lx-Mn-*.md`
- `framework_drafts/<domain>/Lx-Mn-*.md`
- `projects/*/generated/*` 的派生一致性校验

## 2. Framework Markdown 规则

- 每个正式 framework 文件必须使用 `framework/<domain>/Lx-Mn-*.md` 命名。
- 每个文件必须保留 plain `@framework` 起手入口。
- 每个文件必须包含以下主 section：
  - `## 1. 能力声明`
  - `## 2. 边界定义`
  - `## 3. 最小可行基`
  - `## 4. 基组合原则`
  - `## 5. 验证`
- `C* / N* / B* / R* / V*` 编号必须稳定、唯一、可解析。
- `B*` 的上游模块引用必须写在主句中，不得使用 `上游模块：...`。
- framework 模块正文不得直接写入 `project.toml` 路径、已删除的双轨配置文件名、已删除的旧映射清单名或旧配置 section 语法。

## 3. 项目配置边界

- framework 文档只能描述结构语义，不得直接写入项目实例值。
- 项目配置唯一入口是 `projects/<project_id>/project.toml`。
- 边界跳转或实例落点必须回到 `project.toml` 的显式 section，例如：
  - `[selection.root_modules]`
  - `[truth.surface]`
  - `[truth.chat]`
  - `[refinement.backend]`
- `project.toml` 必须可解析，并能被编译器按 contract 切片分发。

## 4. Registry 与 Contract 对齐

- 每个 framework 文件都必须能在 registry 中找到唯一 package 入口类。
- package 入口类必须实现统一 contract。
- 未注册实现视为悬空 package。
- framework 文件没有注册实现视为未实现。
- 一个 framework 文件被多个 package 冲突注册时，lint 必须失败。

## 5. Canonical 与派生视图

- `projects/*/generated/canonical_graph.json` 是唯一机器真相源。
- `generation_manifest.json`、`governance_manifest.json`、`governance_tree.json`、`strict_zone_report.json`、`object_coverage_report.json` 必须明确是 canonical 派生视图。
- 直接编辑 `projects/*/generated/*` 必须被视为违规。

## 6. 自动检查必须覆盖的内容

- framework Markdown 结构完整性
- registry 一一绑定关系
- `project.toml` 可解析性
- contract 切片与 compile 结果一致性
- canonical 可重新物化
- derived views 明确回指 canonical
- `--check-changes` 下的变更传导闭包

## 7. 与执行器关系

`scripts/validate_strict_mapping.py` 是当前主要自动执行器，但脚本不是第一性事实来源；若 lint 合同要变，必须先改本文，再同步执行器。
