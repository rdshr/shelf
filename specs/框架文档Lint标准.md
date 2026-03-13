# 框架文档Lint标准

## 0. 定位
本文件定义框架标准文档的表达协议与 lint 合同，不定义框架设计的语义核心。

关系边界：
- `specs/框架设计核心标准.md` 负责定义“什么结构成立、什么组合合法、哪些边界允许变化”。
- 本文件负责定义这些结构在 Markdown、树注册与治理校验中必须如何表达、如何编号、如何被 lint。
- `scripts/validate_strict_mapping.py` 是本文件的主要自动执行器，但脚本不是第一性事实来源；规则本体以本文件为准。

## 1. 适用范围

- `specs/` 下承载 L0/L1 标准的 Markdown 文件。
- `framework/<module>/Lx-Mn-*.md` 下承载领域模块标准的 Markdown 文件。
- `framework_drafts/<module>/Lx-Mn-*.md` 下承载未发布的框架草稿文件；草稿沿用同一 Markdown 协议，但默认不进入正式标准树、项目物化链与严格映射闭包。
- `mapping/mapping_registry.json` 承载的标准树、映射注册与变更传导元数据。
- `projects/<project_id>/generated/` 的生成产物一致性校验。

## 2. 文档表达规则

### 2.1 路径、层级与文件命名

- `L0/L1` 标准文件必须位于 `specs/`。
- `L2` 标准文件必须位于 `framework/<module>/Lx-Mn-*.md`。
- `L3` 注册文件必须位于 `mapping/`。
- 模块是文件级单元：一个 `framework/<domain>/Lx-Mn-*.md` 文件对应一个模块。
- 当同层存在多个模块文件时，文件名必须使用 `Lx-Mn-*.md` 表示模块编号（例如 `L1-M0-...md`）。
- 模块别名（若需要）是文件级信息，不得绑定到单个 `B*`。

### 2.2 框架 Markdown 必备结构

- 面向 `framework/*.md` 的标准模块文档必须保留 plain `@framework` 指令对应的标准模板起手入口。
- `@framework` 入口属于框架作者起手约束，不得删除；若未来替换实现方式，必须提供同等直接、默认可用且可回归测试的替代入口。
- `framework_drafts/*.md` 若用于草稿编写，仍应保留 plain `@framework` 入口与同一主章节骨架；正式发布前允许不参与项目代码一致性要求。
- 框架模块文档应按顺序提供以下主 section：
  - `## 1. 能力声明`
  - `## 2. 边界定义`
  - `## 3. 最小可行基`
  - `## 4. 基组合原则`
  - `## 5. 验证`
- `## 1. 能力声明` 内若需要声明非职责范围，必须使用独立的 `N*` 编号；推荐在该 section 内追加 `### 非职责声明（Non-Responsibility Statement）` 小节承载。

### 2.3 编号与表达格式

- `C*`、`N*`、`B*`、`R*`、`V*` 必须使用稳定、连续且可解析的编号。
- 每个基必须具备 `B{n}` 标识，并可规范化映射为 `L{X}.M{m}.B{n}`。
- `B*` 行格式应为 `B* 名称：<结构定义或 Lx.My[...] 或 framework.Lx.My[...]>。来源：\`...\``。
- 若引用本框架更低层模块或外部更基础通用框架，模块引用必须直接内联写在 `B*` 主句中。
- 禁止使用 `上游模块：...` 这类追加字段表达模块依赖。
- 外部框架引用可写为 `frontend.L1.M0[R1,R2]` 这类显式形式；本地框架引用可写为 `L1.M0[R1,R2]`。
- `B*` 的 `来源` 表达式中，`C*` token 表示该基在最小可行基层直接对应的正向能力子集；非 `C* / N*` token 表示该基受哪些边界/参数约束。
- 因此，`B*` 的 `来源` 既不是自由叙述，也不是把所有相关能力都堆进去；它承担的是“基层能力归属 + 边界约束”这两个可机读语义。

## 3. 自动 Lint 与治理校验

本节是当前 lint 执行器必须对齐的规则清单。`scripts/validate_strict_mapping.py` 负责执行，但脚本不是规则本体；若要调整 lint，必须先修改本文件，再同步修改执行器使之与本文件一致。

### 3.1 路径、层级与命名 lint

- `L0/L1` 标准文件只允许落在 `specs/`。
- `L2` 标准文件只允许落在 `framework/<module>/L2-Mn-*.md`。
- `L3` 注册文件只允许落在 `mapping/`。
- `framework/<module>/` 目录下只允许直接放置 `Lx-Mn-*.md` 文件，不允许再嵌套子目录承载框架模块。
- 任意 `framework` Markdown 文件名都必须使用 `Lx-Mn-*.md` 前缀。
- 同一领域目录若声明多层文档，则最低层必须显式存在 `L0`。

### 3.2 Framework Markdown 结构 lint

- 每个 `framework/*.md` 文件必须包含 plain `@framework` 指令，且不得携带参数。
- 每个文件必须存在一级标题，标题格式必须为 `中文名:EnglishName`。
- 标题 `:` 左右都不得为空，右侧英文部分必须包含 ASCII 字母。
- `@framework` 文档必须包含并保持以下主 section：
  - `## 1. 能力声明`
  - `## 2. 边界定义`
  - `## 3. 最小可行基`
  - `## 4. 基组合原则`
  - `## 5. 验证`
- 同一文件内的 `C* / N* / B* / R* / V*` 标识必须唯一。
- `C*` 必须满足 `C<number>`。
- `N*` 必须满足 `N<number>`。
- `B*` 必须满足 `B<number>`。
- `V*` 必须满足 `V<number>`。
- `R*` 必须满足 `R<number>` 或 `R<number>.<number>`；子规则存在时，父规则必须先声明。

### 3.3 基与边界表达 lint

- `B*` 行必须符合 `B* 名称：<结构定义或 Lx.My[...] 或 framework.Lx.My[...] >。来源：\`...\`` 的主格式。
- 禁止继续使用 `上游模块：...` 这类遗留字段；上游依赖必须直接内联在 `B*` 主句里。
- 非根层模块的 `B*` 若引用本框架下层模块，必须以内联表达式显式写出，如 `L0.M0[R1] + L0.M1[R2]`。
- 非根层模块的 `B*` 内联表达式必须至少包含一个当前框架内更低层本地 ref，不能只依赖外部框架。
- 本地内联 ref 只能指向当前框架中已存在、且层级低于当前层的模块；禁止同层 ref、反向 ref、越过根层向下穿透。
- 根层 `L0` 的 `B*` 不得再引用当前框架的其它本地模块；根层基必须自足。
- 外部框架 ref 必须指向真实存在的外部模块。
- 每个 `B*` 必须显式声明 `来源：\`...\``。
- `B*` 的来源表达式不能为空，且其中引用的 `C*`、边界标识等 token 必须在当前文件中已定义。
- `B*` 的来源表达式必须至少包含一个边界/参数标识。
- `B*` 的来源表达式中若出现 `C*`，这些 `C*` 必须全部是当前文件中已声明的正向能力项；不得引用任何 `N*`。
- 一个 `B*` 可以在 `来源` 中对应多个 `C*`；若某个 `B*` 当前只承担组合支撑角色，则允许其 `来源` 中不出现 `C*`，但它仍必须进入至少一条 `R*`。
- 每个正向能力项 `C*` 必须且只能出现在一个 `B*` 的 `来源` 表达式中；也就是能力到基的基层归属必须唯一。
- `## 2. 边界定义` 中的每个边界项也必须显式声明 `来源：\`...\``。
- 边界项来源表达式中的 token 必须在当前文件中已定义，且至少包含一个 `C*`。

### 3.4 组合原则 lint

- 合法组合规则必须具备以下四类子项：
  - `参与基`
  - `组合方式`
  - `输出能力`
  - `边界绑定`
- 禁止/无效/不适用规则必须具备以下四类子项：
  - `参与基`
  - `组合方式`
  - `失效结论`
  - `边界绑定`
- `输出能力` 必须至少引用一个当前文件中已定义的 `C*`，不得引用任何 `N*`。
- `失效结论` 必须至少引用一个当前文件中已定义的 `N*`，不得引用任何 `C*`。
- 规则文本中若出现既不是 `C/B/R/V`、也不是边界标识的自定义结构符号，则必须通过当前规则或上游规则中的 `输出结构` 先行声明，才能在后续规则中继续使用。
- 组合原则只对已定义的最小可行基做选择、排序、约束与闭合，不在组合阶段发明新的基；若需要新的独立结构单元，必须回到“最小可行基”层显式定义。
- `参与基` 必须至少引用一个当前文件中已定义的 `B*`。
- `边界绑定` 必须至少引用一个当前文件中已定义的边界标识。
- 多个边界标识构成联合约束时，统一使用 ` + ` 连接；`R*.4` 的 `边界绑定` 和 `## 5. 验证` 中的多边界约束表达都不得再使用 `/`。
- 第一版“1 -> 4”弱充分性 lint 只以 `C*` 正向能力项为对象；`N*` 非职责声明不进入导出充分性检查。
- 记正向能力集合为 `C+`、最小可行基集合为 `B`、组合原则集合为 `R`。
- `B*` 到能力的基层对应关系记为 `A: B -> 𝒫(C+)`；当前 lint 以 `B*` 的 `来源` 表达式中的 `C*` token 表示 `A(b)`。
- 能力到基的归属关系记为 `g: C+ -> B`；当前 lint 要求每个正向能力项 `C*` 必须且只能出现在一个 `B*` 的 `来源` 中，因此 `g` 必须唯一。
- 组合原则到参与基集合的关系记为 `P: R -> 𝒫(B) \\ {∅}`；当前 lint 以 `R*.1` 的 `参与基` 表示 `P(r)`。
- 组合原则到导出能力集合的关系记为 `O: R -> 𝒫(C+) \\ {∅}`；当前 lint 以 `R*.3` 的 `输出能力` 表示 `O(r)`。
- 禁止/无效/不适用规则到非职责声明集合的关系记为 `F: R -> 𝒫(N) \\ {∅}`；当前 lint 以对应规则的 `失效结论` 表示 `F(r)`。
- 对每个正向能力项 `C*`，至少一个 `R*` 的 `输出能力` 必须引用它。
- 对每个正向能力项 `C*`，至少必须存在一条 `g(C*) -> R -> C*` 的导出链：
  - 唯一对应该能力的某个 `B*` 的来源表达式引用该 `C*`
  - 某个 `R*` 的 `参与基` 包含该 `B*`
  - 同一个 `R*` 的 `输出能力` 也引用该 `C*`
- 每个 `B*` 都必须至少参与一个 `R*`，不允许出现无法进入任何组合规则的“死基”。
- 每个边界标识都必须至少被一个 `B*` 的来源表达式或一个 `R*` 的 `边界绑定` 实际使用，不允许出现悬空边界。

### 3.5 引用图 lint

- 由 `B*` 内联 ref 构成的模块引用图必须无环。
- 组合依赖必须沿“更基础结构 -> 更高抽象结构”的单向方向展开。
- 当前框架内部的显式 ref 只能指向更低局部层。
- 同一下层模块允许被多个更高层模块复用，但每个组合节点必须至少由一个更低层节点组成。

### 3.6 注册树与映射 lint

- `mapping/mapping_registry.json` 必须包含合法的 `level_order` 与 `tree`。
- `tree` 必须与仓库规范标准集自动推导出的 canonical 标准树保持一致；若失配，应通过 `uv run python scripts/sync_mapping_registry.py` 同步，而不是手动局部修补。
- 树节点 `id` 必须唯一。
- 树节点 `kind` 只能是 `layer` 或 `file`。
- 树节点 `level` 必须在已声明层级中。
- 树层级跳跃不得反向，也不得一次跨越超过一层。
- `file` 节点必须提供非空 `file` 字段，且目标文件必须真实存在。
- `layer` 节点不得声明 `file` 字段。
- 每个树节点的 `children` 必须是列表。
- 同一个文件在树中只能挂载一次。
- 每个 `L0/L1/L2/L3` 层都必须在树中映射到非空文件集合。
- 所有真实存在的 `framework/*/L2-Mn-*.md` 文件都必须在树中注册，不允许出现未注册领域标准。
- `mappings` 必须是非空列表。
- 每条 mapping 必须有唯一字符串 `id`。
- 每条 mapping 必须包含：
  - `l0_file`
  - `l0_anchor`
  - `l1_file`
  - `l1_anchor`
  - `l2_file`
  - `l2_anchor`
  - `impl_symbols`
- `l0_file / l1_file / l2_file` 必须分别指向树中已声明的对应层文件。
- `impl_symbols` 必须是非空列表。
- `l0_anchor / l1_anchor / l2_anchor` 必须真实存在于对应文件中。
- `impl_symbols` 中的每个 `{file, symbol}` 引用都必须合法，且目标 symbol 必须在目标实现文件中真实存在。
- 当前实现语义附加约束：
  - `impl_symbols` 不得引用兼容 facade `src/shelf_framework.py`
  - 非 `framework/shelf/` 的 mapping 不得引用 `src/shelf_domain.py`
  - `framework/shelf/` 的边界与验证锚点 mapping 必须包含 `src/shelf_domain.py`
- 每个 `L2` 文件都必须具备到 `L1` 核心标准五个主 section 的覆盖映射：
  - `## 1. 能力声明（Capability Statement）`
  - `## 2. 边界定义（Boundary）`
  - `## 3. 最小可行基（Bases）`
  - `## 4. 组合原则（Combination Principles）`
  - `## 5. 验证（Verification）`

### 3.7 项目配置与生成产物 lint

- `projects/<project_id>/` 根目录只允许：
  - `product_spec.toml`
  - `implementation_config.toml`
  - `assets/`
  - `product_spec/`
  - `generated/`
  - 说明性 Markdown 文档
- 禁止在项目实例目录中直接手写实现代码；项目行为必须由 `framework/*.md`、`product_spec.toml`（及可选的 `product_spec/*.toml` section 文件）与 `implementation_config.toml` 驱动，再物化到 `generated/`。
- `product_spec.toml` 与 `implementation_config.toml` 必须可被解析，并满足各自模板注册的 layout 约束。
- `product_spec.toml` 允许把边界主 section 拆到同级 `product_spec/*.toml`；拆分时：
  - `product_spec.toml` 必须继续保留 `project` 与 `framework` 入口。
  - 每个拆分文件必须只承载一个顶层 section。
  - 拆分文件名必须与其承载的顶层 section 同名，例如 `chat.toml -> [chat]`、`documents.toml -> [[documents]]`。
- 当前默认模板 `knowledge_base_workbench` 的 `product_spec.toml` 顶层 section 为：
  - `project`
  - `framework`
  - `surface`
  - `visual`
  - `route`
  - `showcase_page`
  - `a11y`
  - `library`
  - `preview`
  - `chat`
  - `context`
  - `return`
  - `documents`
- 当前默认模板 `knowledge_base_workbench` 的必需嵌套 section 为：
  - `[surface.copy]`
  - `[library.copy]`
  - `[chat.copy]`
- 当前默认模板 `knowledge_base_workbench` 的 `implementation_config.toml` 顶层 section 为：
  - `frontend`
  - `backend`
  - `evidence`
  - `artifacts`
- `implementation_config.toml` 的非产物字段必须满足“配置即功能”：
  - 每个实现层字段都必须进入至少一个下游生效位。
  - 生效位必须落在编译后的 `ui_spec`、`backend_spec`、运行时路由/选择链或生成产物命名中。
  - 仅在 bundle 中重复保存 `IMPLEMENTATION_CONFIG` 本身，不构成生效位。
- 当前默认模板 `knowledge_base_workbench` 的以下字段必须可被自动追踪到下游效果，不允许成为死配置：
  - `frontend.renderer`
  - `frontend.style_profile`
  - `frontend.script_profile`
  - `backend.renderer`
  - `backend.transport`
  - `backend.retrieval_strategy`
  - `evidence.product_spec_endpoint`
- `scripts/validate_strict_mapping.py` 必须对“配置即功能”做自动检查；当 `implementation_config.toml` 字段缺少下游效果、效果路径失配或成为死配置时，lint 必须失败。
- `implementation_config.toml` 的 `[artifacts]` 必须定义且唯一命名以下产物：
  - `framework_ir_json`
  - `product_spec_json`
  - `implementation_bundle_py`
  - `generation_manifest_json`
  - `governance_manifest_json`
  - `governance_tree_json`
- 若使用 Shelf AI 插件进行作者工作流，必须支持三类正式入口：
  - 手动严格校验
  - 项目规格脚手架生成
  - 框架草稿发布到正式 `framework/`
- `generated/` 必须存在，且其中生成产物必须能由当前框架、产品配置和实现配置重新物化后完全一致。
- 项目级 `governance tree` 必须存在、可解析、闭合，且与当前项目 truth 一致。
- 工作区级治理产物 `docs/hierarchy/shelf_governance_tree.json` 与 `docs/hierarchy/shelf_governance_tree.html` 必须存在且与当前工作区状态一致。

### 3.8 变更传导 lint

- `--check-changes` 模式下，lint 会检查 `L0 -> L1 -> L2 -> L3` 的变更传导是否闭合。
- 当前规则是：
  - 若 `L0` 有变更，则 `L1/L2/L3` 都必须出现变更
  - 若 `L1` 有变更，则 `L2/L3` 都必须出现变更
  - 若 `L2` 有变更，则 `L3` 必须出现变更
- 这里的 `L3` 同时包括 `mapping/` 树注册文件和 `impl_symbols` 涉及的实现文件集合。

### 3.9 规则变更方式

- 本文件是 lint 规则的文档合同。
- 若希望通过修改文档来调整 lint，应优先改本文件对应条目，再同步修改 `scripts/validate_strict_mapping.py`。
- 当前执行器尚未做到“从 Markdown 自动解释出全部 lint 规则”；因此现在属于“文档先行、脚本跟随”的治理方式，而不是“文档一改立即自动生效”的完全解释式 lint。

## 4. 非自动审查边界

- lint 不替代 `specs/框架设计核心标准.md` 的语义判断。
- “这个基是否真的是结构”“这个边界是否真正服务能力成立”“这个组合是否导出声明能力”仍以核心标准为准。
- 当前自动执行的是“弱充分性”校验，只验证可机读的覆盖关系、导出链闭合和死基/悬空边界，不等于完成了自然语言层面的完整语义证明。
- 当表达格式合法但语义不成立时，应先按核心标准修正文档结构定义，而不是放宽 lint。

## 5. 外部关联

- `specs/规范总纲与树形结构.md`
- `specs/框架设计核心标准.md`
- `mapping/mapping_registry.json`
- `scripts/validate_strict_mapping.py`
