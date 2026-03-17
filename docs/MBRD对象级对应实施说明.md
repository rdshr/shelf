# MBRD 对象级对应实施说明

## 0. 文档定位

本文定义本仓库在四层主链内的 `M/B/R/D` 对象级 correspondence 方案，并作为后续实现与校验的执行契约。

四层主链不变：

```text
Framework -> Config -> Code -> Evidence
```

约束不变：

- `framework/*.md` 是作者源
- `projects/*/project.toml` 是唯一项目配置入口
- `projects/*/generated/canonical.json` 是唯一机器持久化真相源

## 1. 本阶段对象范围

本阶段只纳入以下对象：

- `M`：Module
- `B`：Base
- `R`：Rule
- `D`：Boundary（作为 `M` 的参数化边界面）

本阶段不纳入：

- `C`：Capability
- `V`：Verification object

`C/V` 保留在 framework 数据中，但不进入对应检测的正式 contract 集。

## 2. 对象对应模型

### 2.1 对应关系

- `M -> ModuleClass`
- `B -> BaseClass`
- `R -> RuleClass`
- `D -> ModuleClass` 的参数面
  - `D(static) -> StaticBoundaryParamsClass`
  - `D(runtime) -> RuntimeBoundaryParamsClass`

### 2.2 语义要求

- `M` 必须是模块装配入口，持有并装配自己的 `BaseTypes/RuleTypes`，并负责边界合成。
- `B` 必须是结构单元承载类，具备 `framework_base_id` 与 `owner_module_id`。
- `R` 必须是规则承载类，具备 `framework_rule_id`、`owner_module_id`、`base_ids`、`boundary_ids`。
- `D` 不作为独立装配对象；静态与动态参数必须通过两个参数类承接，再由 `M` 合并后下发。

## 3. Contracts（代码合同）

共享 runtime/core 层必须提供并使用以下语义合同（类名可不同，语义必须等价）：

- `ModuleContract`
- `BaseContract`
- `RuleContract`
- `StaticBoundaryParamsContract`
- `RuntimeBoundaryParamsContract`

同时需要一个 `UNSET` 哨兵用于 runtime 参数“未提供”语义：

- runtime 字段为 `UNSET`：回退到 static 值
- runtime 字段为显式值：覆盖 static 值

## 4. Config 与 Code 的边界参数模型

### 4.1 Config 层

`project.toml` 继续是实例配置来源，不直接变成 code 结构。  
保留现有 source path 投影规则（如 `exact.<framework>.<boundary_lower>`）作为来源路径。

新增 module-scoped 导出（作为 code 主锚点）：

- `exact_export.modules.<module_key>.static_params.<field_name>`
- `communication_export.modules.<module_key>.static_params.<field_name>`

兼容层：

- `exact_export.boundaries.<BOUNDARY>` 可短期保留为别名
- 但 canonical 中 primary code-facing anchor 必须切到 module static params path

### 4.2 Code 层

每个 `M` 必须同时承接：

- `StaticBoundaryParams`
- `RuntimeBoundaryParams`

并在 `M` 内完成 merged boundary context 生成。  
`B/R` 不得直接读取 config，不得绕过 `M` 获取边界值。

## 5. Canonical 扩展

在 `links` 下新增一等绑定：

- `module_class_bindings`
- `base_class_bindings`
- `rule_class_bindings`
- `boundary_param_bindings`

其中 `boundary_param_bindings` 必须包含：

- owner module
- config source path（exact/communication）
- module-scoped static export path（exact/communication）
- static/runtime params class symbol
- static/runtime field name
- merge policy（当前固定：`runtime_override_else_static`）
- 兼容别名（若仍保留旧 boundary anchor）

## 6. 必须可检测的 Invariants

对应检测器至少覆盖以下失败条件：

1. `M/B/R` 缺类或重复类
2. `D` 缺 static/runtime params class 或字段缺失
3. `R` 未声明 `owner_module_id/base_ids/boundary_ids`
4. `B/R` 未被 `M` 显式装配
5. config path -> module static param field 无法闭合
6. code 直接消费 `communication_export` 或直接读取 framework markdown
7. 仍仅依赖旧 boundary slot 而缺失 module params 主绑定

## 7. 命名与标识规则

命名必须稳定、可逆、可程序生成，不依赖人工随意命名。

- module key：`module_id` 的 `.` 替换为 `__`
  - 例：`knowledge_base.L0.M0 -> knowledge_base__L0__M0`
- 每个 class 必须带 framework id 常量（如 `framework_module_id/framework_base_id/framework_rule_id`）
- correspondence 判定不得只靠类名，必须校验类内声明 id

## 8. 迁移策略

分阶段执行，避免一次性破坏旧链路：

1. 先补对象模型与 canonical 绑定（保留旧 boundary slot）
2. 再补 static/runtime params classes 与字段映射
3. 再把 code 主锚点切到 module params
4. 再接入 correspondence validator 为必跑校验
5. 最后按兼容情况清理旧别名

## 9. 实施边界说明

以下做法禁止：

- 仅靠文件名或路径命名做 correspondence
- 用裸 `dict[str, Any]` 作为边界参数公开 contract
- 让 `R` 退化为函数集合、`B` 退化为 helper 集合
- 让 `M` 变成空壳而不持有 `B/R`

以下做法允许：

- 内部临时字典作为转换中间态
- 在 `M` 内构造 merged context 供 `B/R` 使用（不单独纳入 framework 对象模型）

## 10. 验收口径

验收必须同时满足：

- canonical 中存在 `M/B/R/D` 对应绑定
- config 仍只承载静态值，且每个 boundary 可映射到 module-scoped static params
- code 中每个 module 具备 module/static/runtime/base/rule 的 class 挂接
- correspondence validator 能对“缺失/错挂/伪挂接”给出失败结果

## 11. 当前实现落地点

- contracts：`src/project_runtime/correspondence_contracts.py`
- framework 侧对象与投影：`src/project_runtime/framework_layer.py`
- config 侧 module-scoped static params 导出：`src/project_runtime/config_layer.py`
- code 侧 module/base/rule/params class 绑定：`src/project_runtime/code_layer.py`
- correspondence 检测器：`src/project_runtime/correspondence_validator.py`
- 校验接入点：`src/project_runtime/evidence_layer.py`
- canonical links 汇总：`src/project_runtime/compiler.py`

说明：boundary field 名由 `boundary_id` 稳定派生，并对关键字/非法标识符做标准化，保证可作为 Python class 字段名与 canonical 可逆映射字段使用。

## 12. Phase 1 插件消费导航协议

在保持动态构类实现不变的前提下，新增 canonical 归一化视图 `canonical.correspondence`，作为插件稳定消费层。

顶层字段：

- `correspondence_schema_version`：当前为 `1`
- `objects`：扁平对象列表（插件详情面板 / 搜索）
- `object_index`：`object_id -> object` 映射（插件单对象查询）
- `tree`：模块树（module -> bases/rules/boundaries/static_params/runtime_params）
- `validation_summary`：`correspondence_guard` 摘要（含 object 级定位）

### 12.1 CorrespondenceNode（对象协议）

每个 `M/B/R/D/static_param/runtime_param` 都输出统一结构，最小字段：

- `object_kind`
- `object_id`
- `owner_module_id`
- `display_name`
- `materialization_kind`（`runtime_dynamic_type | source_symbol | generated_readonly`）
- `primary_nav_target_kind`
- `primary_edit_target_kind`
- `correspondence_anchor`
- `implementation_anchor`
- `navigation_targets`

### 12.2 NavigationTarget（导航协议）

每个导航目标最小字段：

- `target_kind`（`framework_definition | config_source | code_correspondence | code_implementation | evidence_report | deprecated_alias`）
- `layer`（`framework | config | code | evidence`）
- `file_path`
- `start_line`
- `end_line`
- `symbol`
- `label`
- `is_primary`
- `is_editable`
- `is_deprecated_alias`

强约束：

- 不能只有 symbol，必须有 `file_path/start_line/end_line`
- `deprecated_alias` 不能是 primary
- `runtime_dynamic_type` 对象必须至少有一个非动态 fallback target（`framework_definition/config_source/code_correspondence` 之一）

### 12.3 Anchor 语义拆分

为避免插件“看结构挂接”和“看真实实现”混淆，协议层明确拆分：

- `correspondence_anchor`：结构挂接锚点（通常落在 contract/builder/binding）
- `implementation_anchor`：实现落点锚点（通常落在 runtime implementation slot）

两者均是一等字段，且在 `navigation_targets` 中都有对应 target（`code_correspondence` / `code_implementation`）。

## 13. 运行时消费面（Phase 1B）

`runtime_app` 新增只读 endpoint（不涉及 UI）：

- `GET <api_prefix>/correspondence`
- `GET <api_prefix>/correspondence/tree`
- `GET <api_prefix>/correspondence/object/{object_id}`

其中：

- `<api_prefix>` 由 `backend_service_spec.transport.api_prefix` 决定
- `object/{object_id}` 直接返回 `object_index` 中的归一化对象详情
- 404 表示 object id 不存在（插件可直接用于诊断提示）
