# Python Candidate Scanner 规则说明

## 1. 目标

Python candidate scanner 的职责不是扫描所有函数，而是扫描会承载项目结构对象的高置信结构候选，然后把它们交给 `governed / attached / internal` 消解链。

当前实现位置：

- [project_governance.py](../src/project_runtime/project_governance.py)

当前测试位置：

- [test_python_candidate_scanner.py](../tests/test_python_candidate_scanner.py)
- [test_governance_counterexamples.py](../tests/test_governance_counterexamples.py)

## 2. 扫描范围

第一版只扫描：

- `src/**/*.py`
- `scripts/**/*.py`

扫描器本身是语言无关设计的第一步，但当前只实现了 Python AST。

## 3. 会命中的 AST 形态

### 3.1 route decorator / route handler

命中条件：

- `FunctionDef` / `AsyncFunctionDef`
- decorator 链路末尾是：
  - `.get`
  - `.post`
  - `.put`
  - `.delete`
  - `.patch`

命中结果：

- `candidate.kind = python_route_handler`
- 默认高置信

### 3.2 route builder / router carrier

命中条件：

- 函数名以这些前缀开头：
  - `build_`
  - `_build_`
  - `compile_`
  - `resolve_`
  - `create_`
  - `materialize_`
  - `_expected_`
  - `_actual_`
- 同时函数体出现：
  - `APIRouter(...)`
  - `FastAPI(...)`
  - `add_api_route(...)`
  - `include_router(...)`

命中结果：

- `candidate.kind = python_route_builder`

### 3.3 schema / contract carrier

命中条件：

- `ClassDef`
- base 或 decorator 命中：
  - `BaseModel`
  - `TypedDict`
  - `Enum`
  - `@dataclass`

命中结果：

- `candidate.kind = python_schema_carrier`

### 3.4 builder / compiler / resolver / materializer

命中条件：

- 函数名前缀命中：
  - `build_`
  - `_build_`
  - `compile_`
  - `resolve_`
  - `create_`
  - `materialize_`
  - `_expected_`
  - `_actual_`

附加信号：

- 若函数体出现 manifest / governance / tree / artifact write 语义：
  - 提升为 `python_evidence_builder`
- 若函数体出现 `implementation / ui_spec / backend_spec / generated_artifacts` sink 信号：
  - 提升为 `python_config_sink`
- 否则保留为 `python_builder`

### 3.5 behavior orchestrator / policy chooser

命中条件：

- 函数名包含这些 token：
  - `answer`
  - `retrieval`
  - `citation`
  - `merge`
  - `context`
  - `return`

命中结果：

- `candidate.kind = python_behavior_orchestrator`

### 3.6 manifest / tree / evidence builder

命中条件：

- builder 类函数
- 且函数体出现：
  - `write_text`
  - `write_bytes`
  - `dump`
  - `dumps`
  - 常量字符串包含 `manifest / tree / governance`

命中结果：

- `candidate.kind = python_evidence_builder`

## 4. 什么会被提升为高置信

第一版没有引入复杂打分模型，而是用“命中规则 + 职责信号”组合成置信度。

高置信候选主要来自：

- route handler
- route builder
- schema carrier
- behavior orchestrator
- evidence builder
- config sink

提升依据包括：

- 位于 `src/` 或 `scripts/` 主链目录
- 被 route decorator / router construction 命中
- 消费 `framework/product/implementation/code export`
- 返回或构造 contract/spec/schema/manifest
- 影响用户可见行为或 evidence

## 5. governed / attached / internal 的判定规则

### 5.1 governed

满足任一 `RequiredRole`：

- kind 匹配
- locator pattern 匹配
- file hint 匹配

结果：

- 直接绑定到某个结构对象的 role

### 5.2 attached

不直接承担 role，但：

- 位于已经承载 governed object 的 strict zone carrier file
- 且本身是高置信候选

当前常见 attached：

- API request/response schema carrier
- compiler/evidence builder helper
- 与 governed object 同文件的辅助 carrier

### 5.3 internal

满足以下条件：

- 是 scanner 命中的候选
- 但不承担任何 required role
- 也不附着在已治理文件的对象角色上

当前 internal 允许存在，但必须显式落成 `internal`，不能“扫描到了但无人解释”。

## 6. 哪些候选必须显式绑定

当前这几类候选不允许以内隐方式漂移：

- `python_route_handler`
- `python_route_builder`
- `python_behavior_orchestrator`

如果它们进入治理范围但没有成为 `governed / attached` 的合法角色承载，校验会报：

- `MISSING_BINDING`

高风险 route 的额外硬规则：

- 在知识库 runtime / backend router builder 里新增 route handler
- 若缺少 `@governed_symbol`
- 会被 AST 级高风险检查直接抓住

## 7. 当前已知盲区与保守边界

第一版明确保守，不做这些：

- 不做深层控制流语义归因
- 不做多文件 alias/dataflow 追踪
- 不做 decorator factory 的复杂展开
- 不做 JS/TS/Go/Rust
- 不自动把所有 attached 提升成 governed object

当前主要盲区：

- 复杂 metaprogramming 生成的 route/schema
- runtime 动态拼接、scanner 无法静态看到的 candidate
- 纯间接 helper 链的职责归因

## 8. 当前测试覆盖

已有自动测试覆盖：

- 应命中：
  - route handler
  - route builder
  - schema carrier
  - behavior orchestrator
  - evidence builder
- 不应命中：
  - 普通 helper
- 应判：
  - governed
  - attached
  - internal
- 应失败：
  - 新增未绑定高风险 route

对应测试文件：

- [test_python_candidate_scanner.py](../tests/test_python_candidate_scanner.py)
- [test_governance_counterexamples.py](../tests/test_governance_counterexamples.py)
