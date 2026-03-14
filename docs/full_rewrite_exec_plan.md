# 全仓 destructive rewrite 执行账本与二次复核

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

## 1.1 二次复核说明（2026-03-14）

本文件最初在重构推进阶段被当作执行账本使用，但此前把全部条目都标成了完成。  
2026-03-14 的二次复核结论是：这个“全部完成”判断过度乐观，和仓库当前真实主路径并不完全一致。

本次复核后，本文件的勾选状态改为按“当前真实实现”计，不再按“预期目标”计。  
复核结论分成两部分：

- 已经真实落地：
  - `framework/*.md -> framework IR -> framework package registry -> package compile -> canonical_graph.json`
  - 每个 framework 文件都有对应 package 注册，当前是 `29 / 29`
  - `project.toml` 已经替代旧 `product_spec.toml + implementation_config.toml`
  - `generated/canonical_graph.json` 已经成为唯一机器真相源
  - 其他 manifest / tree / report 已经降级为 canonical 派生视图
- 仍未完全满足提示词：
  - `KnowledgeBaseProject` 仍然存在，并且仍是运行时与运行时投影的核心聚合对象
  - `src/project_runtime/knowledge_base.py` 仍然是知识库场景的大编排器
  - runtime projection 仍通过 `build_frontend_contract / build_workbench_contract / _build_ui_spec / _build_backend_spec` 手工汇总，而不是仅由 package export 自然收敛
  - `RootModuleSelection` 仍把根模块固定成 `frontend / knowledge_base / backend`
  - `PackageConfigContract` 仍只有 `required_paths / optional_paths / allow_extra_paths`，契约粒度偏粗
  - 部分文档和测试仍在直接书写 `KnowledgeBaseProject / ui_spec / backend_spec`

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
- [ ] 删除旧 `KnowledgeBaseProject`
- [x] 删除 `CanonicalLayeredProjectGraph`

### 3.3 旧编译与物化主路径

- [ ] 删除 `src/project_runtime/knowledge_base.py` 的旧大编排器主路径
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
- [ ] 建立新的 runtime assembly
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
- 当前状态：`部分完成`

### Step 6. 重写 runtime assembly

- 完成判据：
  - 运行时从新的 compiled runtime projection 装配
  - 旧 `KnowledgeBaseCodeModule` 依赖被移除
- 当前状态：`部分完成`

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
- 当前状态：`部分完成`

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
- Step 5：`部分完成`
- Step 6：`部分完成`
- Step 7：`已完成`
- Step 8：`已完成`
- Step 9：`已完成`
- Step 10：`部分完成`
- Step 11：`已完成`

## 7.1 当前仍存在的核心差异

下面这些差异会直接影响“这次 rewrite 是否真的已经完成”的判断：

1. 旧的大聚合对象仍在主路径内
   - [src/project_runtime/knowledge_base.py](../src/project_runtime/knowledge_base.py) 里仍存在 `KnowledgeBaseProject`，且运行时、运行时 bundle、验证器与前后端投影都直接消费它。
2. 编译核心仍然是场景化大编排器
   - `_compile_project(...)` 虽然已经接入 registry 和 package compile，但仍在同一个文件里完成 root module 解析、project 聚合、runtime projection 构建、validation 汇总与 canonical 收束。
3. 运行时投影没有完全由 package export 收敛
   - `frontend_contract`、`workbench_contract`、`ui_spec`、`backend_spec` 仍由 [contracts.py](../src/frontend_kernel/contracts.py)、[workbench.py](../src/knowledge_base_framework/workbench.py) 和 [knowledge_base.py](../src/project_runtime/knowledge_base.py) 的专门 builder 直接从 `KnowledgeBaseProject` 手工构建。
4. 根模块选择仍然是固定三槽位
   - `RootModuleSelection` 仍显式固定为 `frontend / knowledge_base / backend`，而不是完全由更一般化的模块树选择表达。
5. package config contract 还不够强
   - [contract.py](../src/framework_packages/contract.py) 目前只声明 dotted path 级别的 `required_paths / optional_paths / allow_extra_paths`，还没有把字段默认值、禁用字段和更强的结构验证显式化。
6. “每个 package 只有一个入口类”目前主要靠结构约定，不是显式验证器
   - registry 能检测重复注册，但还没有一个单独校验器去证明“每个 package 目录只能有一个正式入口类”。
7. 文档和测试仍残留旧聚合语言
   - [docs/全链实现框架与跳转逻辑详解.md](./全链实现框架与跳转逻辑详解.md) 与 [tests/test_project_runtime.py](../tests/test_project_runtime.py) 仍直接围绕 `KnowledgeBaseProject / ui_spec / backend_spec` 叙述和断言。

## 7. 最终验收清单

- [x] Framework Markdown 仍是作者源
- [x] 每个 framework 文件对应一个 package
- [x] 每个 package 只有一个唯一入口 class
- [x] 每个入口 class 实现统一 Framework Package Contract
- [x] 每个入口 class 已注册到统一 registry
- [x] registry 成为 framework 与代码的一一绑定真相
- [x] 统一项目配置体系已取代旧 `product_spec / implementation_config` 双轨核心
- [ ] 配置已按模块树逐层切片分发
- [ ] 编译核心已切换为 `module tree + registry + config slicing + package compile`
- [x] `generated/canonical_graph.json` 已成为唯一机器真相源
- [x] 其他 manifest/tree/report 已降级为 canonical 派生视图
- [x] Evidence 已纳入 canonical 主层
- [ ] 旧架构核心实现已删除、替换或彻底降级
- [ ] 文档、脚本、治理、验证、运行时装配、测试全部切换到新架构语言和对象模型
- [ ] 本文档全部条目已完成

## 8. 结论

截至 2026-03-14，本仓库已经完成了大部分结构切换，但**还不能诚实地称为“完全满足提示词的最终形态”**。  
真正完成的部分，是：

- Markdown-first framework authoring
- framework file 与 package 的一一注册
- unified `project.toml`
- canonical single truth
- canonical-derived governance / report / workspace views

尚未完全切净的部分，是：

- `KnowledgeBaseProject` 仍是主聚合对象
- scene-specific `knowledge_base.py` 仍是核心大编排器
- runtime assembly 仍然手工汇总
- package contract 粒度仍偏粗
- 部分文档和测试仍围绕旧聚合对象叙事

因此，本执行账本现在必须被解释为：

- 主骨架已落地
- 但 destructive rewrite 还没有达到提示词要求的“完全收口态”

## 附录 A. 原始执行提示词

```text
你现在就在这个仓库里工作。你的任务不是补丁、兼容、过渡，也不是在旧方案外面再包一层新壳，而是对当前架构做一次彻底、完整、不可回退的重构：把仓库从旧实现完整迁移到新实现，并且删除旧实现的核心机制，不允许留下旧架构残留作为主路径或并行路径。

这是一次完整重构，不接受以下做法：

- 先保留旧架构，再在旁边追加新架构
- 做兼容层、适配层、过渡层长期保留
- 做 MVP、第一版、临时版
- 先改一半，留 TODO 等以后再收口
- 保留旧的核心 manifest/tree/report 作为并行真相源
- 保留旧的项目级大编排器作为架构核心，只是改名
- 用文档叙事伪装已经重构，实际上核心实现还是旧的

你必须直接把仓库重构到最终形态：结构统一、概念统一、生成链统一、验证链统一、文档统一。只有当仓库已经完整进入新架构，并且旧架构不再作为核心存在时，才算完成。

====================
一、最终目标
====================

把当前仓库重构成下面这套架构：

1. Framework Markdown 仍然是作者源（Markdown-first authoring）。
2. 每个 framework 文件对应一个代码包（package）。
3. 每个 package 必须有且只有一个唯一入口 class。
4. 这个入口 class 必须实现统一的 Framework Package Contract。
5. 每个入口 class 必须注册到统一 registry 中，并明确声明自己对应哪份 framework 文件。
6. registry 构成 framework 与代码包的一一绑定真相。
7. Product 与 Implementation 不再作为两套独立的大对象体系存在，而是合并成一个统一的项目配置体系；但逻辑上仍需区分“产品选择/产品真相”和“实现细化/实现偏好”。
8. 项目本质上由三部分决定：
   - framework 树/模块树选择
   - 项目配置内容
   - 代码包注册与装配结果
9. 上层组合下层的方式是 import package + 分发配置 + 调用统一 contract 编译，不允许用继承表达框架装配关系。
10. 最终机器真相源只能有一个：canonical JSON。
11. canonical JSON 必须分层记录：
    - framework
    - config
    - code
    - evidence
    同时清晰记录模块树、注册绑定、配置分发、编译结果和证据结果。
12. 旧架构的核心概念、旧的多份平行真相文件、旧的项目级聚合模块体系、旧的治理主路径，都必须被删除、替换或降级为 canonical JSON 的派生视图，不允许继续作为主实现存在。

====================
二、你必须遵守的架构原则
====================

1. Markdown-first
   - framework/*.md 是 framework 层的人类作者源。
   - 不允许把 framework 的真相源改成 schema/config 再反向生成 markdown。
   - 先有 markdown，再有 parser/loader，再有代码包注册与装配。

2. One framework file -> one package
   - 每个 framework 文件必须对应一个独立代码包。
   - 每个代码包必须自成体系、可拆卸、可独立理解、可独立测试。
   - 允许一个 package 内有多个内部文件，但必须只有一个唯一入口 class。
   - 不要强行要求一个 framework 文件只对应一个代码文件；正确粒度是“一个 framework 文件对应一个 package”。

3. One package -> one entry class
   - 每个 package 必须有唯一入口 class。
   - 只有入口 class 可以注册到 framework registry。
   - package 内的 helper/schema/adapter/internal builder 都不能直接注册到主链。

4. Unified contract
   - 每个入口 class 必须实现统一的 Framework Package Contract。
   - contract 必须统一表达以下事情：
     - 对应哪份 framework 文件
     - 模块身份
     - 需要什么配置切片
     - 允许组合哪些子模块/子包
     - 如何编译
     - 如何导出 export
   - 系统只承认实现了 contract 且成功注册的 package。

5. Explicit registry
   - 必须有统一 registry。
   - registry 的作用是建立：
     - framework 文件 <-> package 入口 class
   - registry 是正式绑定真相。
   - 装饰器可以作为语法糖，但 registry 才是真相源。
   - 未注册的实现视为悬空。
   - framework 文件没有对应注册实现，视为未实现。
   - 一个 framework 文件被多个 package 冲突注册，必须报错。
   - 一个 package 试图对应多个 framework 文件，必须报错，除非你在真实仓库上下文中能证明这是有意识且被契约允许的特殊机制；否则默认禁止。

6. Composition only
   - 上层使用下层的方式必须是组合，不是继承。
   - package 之间的装配方式是：
     - import 子 package
     - 按 contract 分发配置切片
     - 调用 compile / export
   - 严禁用继承树表达 framework/module 关系。

7. Config-driven projects
   - 项目不是靠手写特化代码定义的，而是由：
     - framework 树选择
     - 配置文件内容
     - registry 中可用 package
     三者共同决定。
   - 不同项目的差异，主要表现为：
     - framework 树不同
     - 选中的 package 不同
     - 配置内容不同
   - 如果项目差异已经无法用现有 framework 模块表达，正确做法是扩展 framework 模块，而不是把配置文件变成隐形第二框架。

8. Config merge but logical partition
   - Product 与 Implementation 可以物理合并到一个统一配置体系里。
   - 但逻辑上必须仍然可区分：
     - selection / product truth
     - refinement / implementation detail
   - 不能把配置做成一坨没有分区的大字典。
   - 配置里允许有自然语言说明，但自然语言只能作为解释/补充，不得替代机器判定所依赖的结构字段。

9. Strict config slicing
   - 配置必须按模块树逐层分发。
   - 每个 package 必须显式声明自己的 config contract。
   - 上层只能把对应切片分发给子包。
   - 子包不得偷偷消费未声明字段。
   - 不允许全局配置字典任意透传。

10. Single canonical JSON
   - 最终机器真相源只能有一个 canonical JSON。
   - GUI、validator、change propagation、coverage、report generation 必须以它为唯一机器基础。
   - 其他 manifest/tree/report 如果仍有价值，只能是 canonical JSON 的派生视图。
   - 不允许再存在多个平行 JSON 分别承担不同部分真相。

====================
三、最终目标架构
====================

重构后的架构应当呈现下面这种关系：

Framework markdown
  -> framework parser / loader
    -> framework tree / module tree
      -> registry lookup
        -> package entry classes
          -> config slicing / package compile
            -> package exports
              -> assembled code runtime
                -> evidence generation
                  -> canonical JSON
                    -> derived governance/tree/report/views

这里最重要的结构是：

1. Framework layer
   - framework/*.md 继续是作者源。
   - 每个 framework 文件对应一个模块语义单元。
   - parser/loader 负责把 framework markdown 解析成可装配的模块语义，但不要把 framework 真相源迁移成别的东西。

2. Package layer
   - 每个 framework 模块对应一个代码 package。
   - package 内唯一入口 class 实现 Framework Package Contract。
   - package 内部可以有 helper/schema/internal files，但对外只有入口 class 的 contract 有正式地位。

3. Config layer
   - 项目配置统一到一套配置体系里。
   - 物理上可以是一个文件体系，但逻辑上必须至少分清：
     - 模块/树选择
     - 产品真相
     - 实现细化
     - 配置说明/narrative
   - 配置必须能被逐层切片分发给 package。

4. Compile/assembly layer
   - 编译器不再以“项目级大聚合模块”作为核心抽象。
   - 编译器的核心职责应当是：
     - 读取 framework 树
     - 读取项目配置
     - 从 registry 找到对应 package
     - 校验 config contract
     - 装配 child packages
     - 调用 compile / export
     - 汇总为 canonical JSON
   - 不要继续保留旧的项目级大编排器作为核心架构主角。

5. Evidence layer
   - Evidence 是正式主层，不是附属品。
   - Evidence 负责生成：
     - 编译证据
     - 运行证据
     - 结构证明
     - 审计与治理视图
   - 但 Evidence 不是新的平行真相源；它的正式机器落点仍然应回到 canonical JSON，并由其派生其他视图。

====================
四、Framework Package Contract 必须具备的能力
====================

不要机械套用我下面的方法名，但语义上必须完整承载这些能力：

1. framework 对齐能力
   - 明确回答：这个 package 对应哪份 framework 文件。
   - 这是 framework 与代码一一对应的锚点。

2. 模块身份能力
   - 明确回答：这个 package 的模块 id 是什么。
   - 不能只靠 framework 路径作为内部身份。

3. 配置契约能力
   - 明确回答：这个 package 需要哪些配置字段、哪些是必填、哪些是可选、默认值如何、哪些字段不允许出现。
   - 编译器必须根据这个 contract 进行配置切片和验证。

4. 子模块槽位能力
   - 明确回答：这个 package 可以组合哪些 child packages，child 的角色是什么，哪些是必需的，哪些是可选的。
   - 上层 package 组合下层 package，本质上就是通过 child slot 完成。

5. 编译能力
   - 明确回答：给定本 package 的配置切片和子包编译结果后，如何收敛出本 package 的编译结果。

6. 导出能力
   - 明确回答：本 package 向上层暴露什么 export。
   - export 是模块对外契约，不是随意 dump 内部对象。

7. 证据能力（如果适合）
   - 明确回答：本 package 如何产出自己的 evidence 或 evidence contribution。
   - 即使不是每个 package 都单独生成完整 evidence，也必须能把证据贡献纳入统一 evidence 汇总链。

====================
五、Registry 必须承担的职责
====================

必须实现统一 registry，并把它变成 framework 与代码的正式绑定枢纽。Registry 至少要承担：

1. framework 文件 -> entry class 的绑定
2. module id -> entry class 的绑定
3. package 冲突检测
4. framework 未实现检测
5. 悬空 package 检测
6. 供编译器按模块树查询 package
7. 供 validator 检查 package / framework 一一对应关系
8. 供 canonical JSON 记录正式绑定关系

Registry 必须是第一公民。不要靠扫描代码目录猜谁是模块入口。

====================
六、Config 体系必须如何重构
====================

当前旧方案中的 Product Spec 和 Implementation Config 需要彻底重构成新的项目配置体系。要求：

1. 合并旧的 product/implementation 主叙事，不再让它们作为两套平行大体系继续存在。
2. 但逻辑上保留明确分区，至少区分：
   - 模块树/模块选择
   - 产品真相
   - 实现细化
   - 说明文字
3. 配置必须支持逐层切片分发。
4. 每个 package 的 config contract 必须可用于自动校验。
5. 不允许“谁想读什么字段就去读”。
6. 不允许 package 跳过自己的配置切片直接偷读全局配置。
7. 不允许自然语言说明成为机器唯一判定依据。

如果仓库当前已经有多个项目或项目发现机制，你需要把它们全部切到新配置体系，不要只改一个示例项目。

====================
七、Canonical JSON 必须记录什么
====================

最终只能有一个 canonical JSON 作为唯一机器真相源。它至少要稳定记录以下内容：

1. Framework tree / module tree
   - 当前项目选中了哪些 framework 文件
   - 它们的层次关系和装配关系是什么

2. Registry binding
   - 每个 framework 文件对应哪个 package
   - 对应哪个 entry class
   - module id 是什么

3. Config projection
   - 当前项目对每个模块/package 分发了哪些配置切片
   - 哪些配置来自 selection / truth / refinement

4. Compile result
   - 每个 package 的编译结果
   - 每个 package 的 export
   - 包之间的 child 组合关系

5. Code/runtime projection
   - 实际装配出的代码模块/运行时面
   - 如果有运行时路由、契约、行为 surface，也应以新架构的方式纳入

6. Evidence
   - 编译证据
   - 运行证据
   - 结构证据
   - 审计视图来源

7. Derived view metadata
   - 其他 tree / governance / report / coverage 之类的派生视图，必须清楚声明自己 derived from canonical JSON

不要再让多个 manifest 分别扮演不同部分的“真相”。

====================
八、旧实现必须删除或降级的内容
====================

你必须主动搜索整个仓库，把旧架构中与新架构冲突的核心机制全部删除、替换或降级。包括但不限于：

1. 旧的项目级大聚合模块体系
   - 任何把整个项目收敛成单个大 ProductModule / ImplementationModule / CodeModule 再作为核心主抽象的机制，如果与新 package-contract + registry 架构冲突，必须删除或彻底降级。
   - 不允许旧的大聚合模块继续作为主编译核心存在。

2. 旧的平行真相文件
   - 旧的 framework_ir.json / generation_manifest.json / governance_manifest.json / governance_tree.json / strict_zone_report.json / object_coverage_report.json 等，如果继续承载机器真相，必须取消。
   - 如果仍保留，必须降级为 canonical JSON 的派生视图。

3. 旧的治理主路径
   - 如果旧的 governance/mapping/strict mapping/change propagation 是围绕旧对象模型构建的，必须切换到新的 canonical JSON + registry + package contract。
   - 不允许旧治理模型继续充当主路径，只在外面披一层新名词。

4. 旧的绑定方式
   - 任何旧的 symbol 注释、旧的 governed_symbol、旧的映射注解，如果不符合新的一一对应 package/entry class 模式，必须删除、迁移或降级。

5. 旧的文档叙事
   - 所有介绍架构、主链、编译顺序、治理方式的文档，必须改成新架构语言。
   - 不允许新旧两套语言并存。

====================
九、实现方式要求
====================

1. 先充分阅读仓库，基于真实上下文理解当前模板、模块、运行链、生成链、校验链。
2. 不要把提示词里的抽象概念生硬硬编码进代码；要从仓库现有真实领域中提取合理命名和模块边界。
3. 允许你重命名、搬移、删除、合并文件与目录，只要最终架构更统一、更优雅、更简洁。
4. 可以保留对外功能行为，但内部结构必须彻底切换到新架构。
5. 不要为了少改动而保留旧架构核心。
6. 不要为了快而牺牲“每个 framework 文件 -> 一个 package -> 一个入口 class -> registry 注册 -> contract 装配”这条主骨架。

====================
十、完成标准
====================

只有当下面全部成立时，才算完成：

1. Framework Markdown 仍是作者源。
2. 每个 framework 文件已经对应一个代码 package。
3. 每个 package 有且只有一个唯一入口 class。
4. 每个入口 class 已实现统一 Framework Package Contract。
5. 每个入口 class 已成功注册到统一 registry。
6. registry 已成为 framework 与代码的一一绑定真相。
7. Product 与 Implementation 已经被重构成新的统一项目配置体系，不再保留旧的两套主对象模型作为核心。
8. 配置分发已经按模块树逐层切片，package 只消费自己 contract 声明的配置。
9. 编译器的核心已经从“项目级大聚合模块”转为“模块树 + registry + config + package compile”。
10. canonical JSON 已经成为唯一机器真相源。
11. 其他 manifest/tree/report 若存在，已经明确降级为 derived views。
12. Evidence 已经作为正式主层纳入新架构，但不形成新的平行真相源。
13. 旧架构的核心实现已经被删除、替换或彻底降级，不再作为主路径存在。
14. 文档、生成物、验证脚本、治理脚本、运行时装配脚本都已经使用新架构语言和新架构对象。
15. 仓库里不再存在“实际上还是旧方案，只是换了名字”的情况。

现在开始，直接在仓库里完成这次重构。不要停在中途，不要输出 MVP，不要留下过渡态，不要保留旧核心残留。只有当仓库已经彻底完成这次架构切换，并且旧方案不再作为核心存在时，才算结束。
```
