# 全仓 destructive rewrite 执行账本

## 1. 背景与目标

当前仓库的主路径仍然建立在旧的项目级聚合对象体系上：

- `product_spec.toml + implementation_config.toml`
- `ProjectTemplateRegistration / template_registry`
- `KnowledgeBaseProductModule / KnowledgeBaseImplementationModule / KnowledgeBaseCodeModule`
- 基于旧对象模型展开的 governance / strict mapping / workspace governance

本次任务的目标不是在旧主路径外再挂一层新壳，而是把仓库完整切换到以下唯一主路径：

```text
Framework Markdown
  -> framework parser / module tree
    -> framework package registry
      -> package entry classes
        -> unified project config slicing
          -> package compile / export
            -> runtime assembly
              -> evidence aggregation
                -> generated/canonical_graph.json
                  -> derived governance/tree/report/views
```

完成标准：

- 新架构已经完整落地并成为唯一主路径。
- 旧架构核心已经被删除、替换或彻底降级，不再作为主路径存在。

## 2. 新架构总纲

### 2.1 Framework layer

- `framework/*.md` 继续作为作者源。
- 每个 framework 文件对应一个独立代码 package。
- 每个 package 有且只有一个唯一入口 class。

### 2.2 Package layer

- 每个入口 class 实现统一 `Framework Package Contract`。
- 入口 class 通过统一 registry 注册。
- registry 是 `framework file <-> package entry class <-> module id` 的正式绑定真相。

### 2.3 Config layer

- 项目配置统一到 `projects/<project_id>/project.toml`。
- 配置逻辑上分成：
  - `selection`
  - `truth`
  - `refinement`
  - `narrative`
- 编译器只允许按 package contract 切片分发配置。

### 2.4 Compile layer

- 编译核心以 `module tree + registry + config slicing + package compile` 为中心。
- 不再以旧项目级大聚合模块作为架构核心。

### 2.5 Evidence layer

- `generated/canonical_graph.json` 是唯一机器真相源。
- 其他 manifest / tree / report / governance 只能是 canonical 的派生视图。

## 3. 必删旧实现清单

### 3.1 旧项目模板与入口链

- [x] 删除 `src/project_runtime/template_registry.py` 作为主路径
- [x] 删除 `ProjectTemplateRegistration` 体系作为主路径
- [x] 删除 `src/project_runtime/app_factory.py` 的旧模板分发主路径
- [x] 删除 `src/main.py` 中 `legacy-reference-shelf` 并行入口

### 3.2 旧双轨配置与聚合对象

- [x] 删除 `product_spec.toml + implementation_config.toml` 作为核心配置体系
- [x] 删除 `src/project_runtime/project_config_source.py` 中以 `product_spec` 为中心的旧主路径
- [x] 删除 `KnowledgeBaseProductModule`
- [x] 删除 `KnowledgeBaseImplementationModule`
- [x] 删除旧 `KnowledgeBaseCodeModule` 聚合主路径
- [x] 删除旧 `KnowledgeBaseProject`
- [x] 删除 `CanonicalLayeredProjectGraph`

### 3.3 旧编译与物化主路径

- [x] 删除 `src/project_runtime/knowledge_base.py` 的旧大编排器主路径
- [x] 删除 `src/project_runtime/layered_models.py`
- [x] 删除旧 `materialize_registered_project(...)` 主路径

### 3.4 旧治理与旧严格映射主路径

- [x] 删除 `mapping/mapping_registry.json` 作为主治理真相
- [x] 删除基于旧对象模型的 strict mapping 主路径
- [x] 删除基于旧对象模型的 workspace/project governance 主路径

### 3.5 旧并行 legacy/reference 路径

- [x] 删除 `src/examples/legacy_shelf`
- [x] 删除 `src/domain`
- [x] 删除 `src/enumeration`
- [x] 删除 `src/geometry`
- [x] 删除 `src/rules`
- [x] 删除 `src/verification`
- [x] 删除 `src/visualization`
- [x] 删除与 legacy shelf 主路径绑定的脚本、文档与测试

## 4. 必建新实现清单

### 4.1 Framework Package Contract

- [x] 建立统一 contract 数据结构
- [x] 建立统一 compile input / output / evidence contribution 结构
- [x] 建立 child slot / config contract 表达能力

### 4.2 Registry

- [x] 建立统一 registry
- [x] 实现 framework file -> entry class 绑定
- [x] 实现 module id -> entry class 绑定
- [x] 实现冲突检测 / 未实现检测 / 悬空 package 检测

### 4.3 Framework packages

- [x] 为每个 `framework/*.md` 建立对应 package
- [x] 为每个 package 建立唯一入口 class
- [x] 所有入口 class 完成注册

### 4.4 Unified project config

- [x] 建立 `projects/<project_id>/project.toml`
- [x] 建立统一配置加载器与分区模型
- [x] 完成 `selection / truth / refinement / narrative` 切片分发

### 4.5 New compiler

- [x] 建立新的 module tree resolver
- [x] 建立新的 registry-driven compiler
- [x] 建立新的 runtime assembly
- [x] 建立新的 canonical graph builder

### 4.6 Derived views

- [x] governance view 改为 canonical 派生
- [x] workspace change propagation 改为 canonical 派生
- [x] strict checking 改为 registry + canonical 校验
- [x] hierarchy/tree/report 改为 canonical 派生

## 5. 迁移步骤清单

### Step 1. 建立执行账本

- 完成判据：`docs/full_rewrite_exec_plan.md` 已创建并进入版本控制上下文。
- 当前状态：`已完成`

### Step 2. 建立新 contract / registry / package 目录结构

- 完成判据：
  - 存在统一 contract
  - 存在统一 registry
  - registry 可显式加载 builtin packages
- 当前状态：`已完成`

### Step 3. 为所有 framework 文件建立 package 入口类并注册

- 完成判据：
  - 每个 framework 文件都能通过 registry 找到唯一 entry class
  - 无冲突 / 无悬空 / 无未实现
- 当前状态：`已完成`

### Step 4. 用 unified project config 替换旧双轨配置

- 完成判据：
  - `project.toml` 成为唯一项目配置入口
  - 旧 `product_spec.toml / implementation_config.toml` 不再作为主路径
- 当前状态：`已完成`

### Step 5. 用新 compiler 替换旧 project_runtime 核心

- 完成判据：
  - 编译链以 `module tree + registry + config slicing + package compile` 运转
  - 旧 `KnowledgeBase*Module` 不再是主路径
- 当前状态：`已完成`

### Step 6. 重写 runtime assembly

- 完成判据：
  - 运行时从新的 compiled runtime projection 装配
  - 旧 `KnowledgeBaseCodeModule` 依赖被移除
- 当前状态：`已完成`

### Step 7. 重写 canonical 与派生视图

- 完成判据：
  - `generated/canonical_graph.json` 成为唯一机器真相源
  - 其他视图都明确 `derived_from canonical_graph.json`
- 当前状态：`已完成`

### Step 8. 重写治理、严格校验、workspace change propagation

- 完成判据：
  - validator / governance / workspace tree 不再依赖旧对象模型
- 当前状态：`已完成`

### Step 9. 删除旧并行 legacy 路径

- 完成判据：
  - legacy shelf 并行主路径与相关测试、脚本、文档已删除
- 当前状态：`已完成`

### Step 10. 统一文档与测试

- 完成判据：
  - 架构文档、执行文档、测试全部描述新架构
  - 不再保留旧主路径叙事
- 当前状态：`已完成`

### Step 11. 全量验证

- 完成判据：
  - `uv run python scripts/materialize_project.py`
  - `uv run mypy`
  - `uv run python scripts/validate_strict_mapping.py`
  - `uv run python scripts/validate_strict_mapping.py --check-changes`
  - 运行时入口可正常工作
- 当前状态：`已完成`

## 6. 当前状态总览

- Step 1：`已完成`
- Step 2：`已完成`
- Step 3：`已完成`
- Step 4：`已完成`
- Step 5：`已完成`
- Step 6：`已完成`
- Step 7：`已完成`
- Step 8：`已完成`
- Step 9：`已完成`
- Step 10：`已完成`
- Step 11：`已完成`

## 7. 最终验收清单

- [x] Framework Markdown 仍是作者源
- [x] 每个 framework 文件对应一个 package
- [x] 每个 package 只有一个唯一入口 class
- [x] 每个入口 class 实现统一 Framework Package Contract
- [x] 每个入口 class 已注册到统一 registry
- [x] registry 成为 framework 与代码的一一绑定真相
- [x] 统一项目配置体系已取代旧 `product_spec / implementation_config` 双轨核心
- [x] 配置已按模块树逐层切片分发
- [x] 编译核心已切换为 `module tree + registry + config slicing + package compile`
- [x] `generated/canonical_graph.json` 已成为唯一机器真相源
- [x] 其他 manifest/tree/report 已降级为 canonical 派生视图
- [x] Evidence 已纳入 canonical 主层
- [x] 旧架构核心实现已删除、替换或彻底降级
- [x] 文档、脚本、治理、验证、运行时装配、测试全部切换到新架构语言和对象模型
- [x] 本文档全部条目已完成
