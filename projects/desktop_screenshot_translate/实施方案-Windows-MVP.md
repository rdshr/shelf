# desktop_screenshot_translate Windows MVP 实施方案

## 1. 文档定位

本文件不是新的框架文档，也不改写 `framework/aitrans/*.md` 的共同结构语言。

它只负责回答一件事：

在已经确定的 `Framework -> Product Spec -> Implementation Config` 前提下，
这个具体项目如何优先落地 `Windows MVP`。

因此它属于项目层实施文档，服务于：

- 下一阶段开发排序
- 目录与模块映射
- Windows / WSL 双环境分工
- 里程碑与验收口径

## 2. 当前前提

已固定的上游输入：

- Framework：
  - `framework/aitrans/L3-M0-桌面截图翻译框架.md`
  - `framework/frontend/L2-M0-前端框架标准模块.md`
  - `framework/runtime_env/L0-M0-运行环境识别模块.md`
- Product Spec：
  - `projects/desktop_screenshot_translate/product_spec.toml`
- Implementation Config：
  - `projects/desktop_screenshot_translate/implementation_config.toml`

当前不再继续压框架，除非真实落地时发现现有框架无法表达新的跨实例稳定共同结构。

## 3. MVP 目标

Windows MVP 的交付目标只定义最小闭环，不追求一次做完最终产品。

必须交付：

1. 用户可以通过托盘或全局快捷键进入截图。
2. 用户可以在 Windows 桌面上拖选一个区域完成截图。
3. 截图结果可以进入 OCR 与翻译主链。
4. 译文可以在悬浮结果面板中展示。
5. 结果面板至少支持：
   - 复制译文
   - 关闭面板
   - 重新截图
6. 主链关键事件可以被记录并追踪问题。

暂不作为 MVP 必须项：

- 自动更新完整闭环
- macOS 实机对齐
- 复杂排版还原
- 术语表、历史记录、多任务列表
- 本地离线高质量翻译模型

## 4. 环境分工

当前开发环境是 `Windows + WSL`。

这意味着职责必须拆开：

### 4.1 WSL 负责

- 仓库文档、框架、项目配置维护
- Python 生成器与校验器
- 纯逻辑代码与单元测试
- `uv` 环境、严格映射、物化、类型检查

### 4.2 Windows 原生环境负责

- Electron 主进程运行
- 托盘、全局快捷键、窗口、浮层
- Windows 截图链联调
- 原生 OCR / 剪贴板 / 凭据管理接线
- Windows 安装包生成与实际验证

### 4.3 结论

WSL 是“规范与生成链开发环境”，不是最终的 Windows 桌面运行环境。

因此 Windows MVP 的真实联调、截图、快捷键、悬浮窗和打包，必须在 Windows 侧完成。

## 5. 实现路线

当前建议路线：

- 桌面宿主：`Electron`
- MVP 主链：`纯 Electron`
- Python sidecar：保留为后续可选扩展点
- renderer 策略：
  - `overlay`：原生 HTML / JS
  - `panel`：`Vue 3 + Vite + .vue SFC`

原因：

- 当前仓库已经有 `uv`、Python 生成链、项目运行时和校验器
- Electron 更适合先打通 Windows 托盘、全局快捷键、悬浮窗和截图主链
- 纯 Electron 可以减少 MVP 阶段的多进程、打包和联调复杂度
- Python 继续承担生成器、校验器与可选扩展运行时，不再作为 MVP 首批主链前置依赖
- 结果面板比遮罩页更容易继续增长状态与交互复杂度，因此优先在 `panel renderer` 集成 `Vue 3 + Vite + .vue SFC`，而不把整个 Electron 壳都框架化

这里的关键约束是：

- Electron 不能绕开 `projects/desktop_screenshot_translate/*`
- 桌面应用行为必须仍由 `framework + product_spec + implementation_config` 驱动
- 不能把真实产品真相偷偷移回代码硬编码

## 6. 目录建议

建议新增真实实现目录：

- `apps/desktop_screenshot_translate/`

建议分层：

- `apps/desktop_screenshot_translate/electron/`
  - `main/`：托盘、快捷键、窗口、IPC 注册
  - `preload/`：受限桥接
  - `renderer/overlay/`：原生截图遮罩页
  - `renderer/panel-src/`：Vite + Vue SFC 源码
  - `renderer/panel-dist/`：Vite 构建产物，由构建命令生成，不手改
- `apps/desktop_screenshot_translate/python_sidecar/`
  - `service/`：可选项目加载与扩展编排
  - `adapters/`：后续 provider 扩展适配
  - `contracts/`：后续 Electron <-> Python 请求响应契约

说明：

- `projects/*` 继续放产品真相与实现细化
- `generated/*` 继续放编译产物
- `apps/*` 才是接下来的真实实现代码落点

## 7. 框架到实现的映射

### 7.1 L2-M0 桌面宿主层

落地到：

- Electron tray
- globalShortcut
- BrowserWindow 生命周期
- 权限检测与引导

### 7.2 L2-M1 截图交互层

落地到：

- 全屏透明遮罩窗口
- 鼠标拖选区域
- 多屏坐标换算
- 截图位图裁剪与标准化

### 7.3 L2-M2 识别翻译层

落地到：

- Electron 本地 OCR provider 适配
- translation provider 适配
- timeout / retry / fallback

当前 Windows MVP 说明：

- OCR 正式发布路径默认采用“应用内置 Tesseract 运行时”，不把用户手工安装 `tesseract` 作为标准交付方式
- 当前开发联调阶段仍允许通过环境变量覆盖 OCR 可执行路径，避免在 bundling 尚未落地前阻塞主链
- `windows_ocr_api` 仍保留为后续 packaged / package-identity 形态下的能力升级入口
- 翻译主链仍只保留 `openai_translation`，但它面向 OpenAI 兼容端点，可指向 OpenAI 官方或局域网内兼容端点
- 当前默认本地模型选择为 `qwen3-30b-a3b-instruct-2507`，并在端点不可用时回退到本地 stub
- 翻译端点与密钥的普通用户入口应是首次配置窗口 / 设置界面，而不是要求用户手工编辑 `%APPDATA%` 下的 JSON
- 这不是框架变化，而是当前实现路径对官方 Windows API 约束的回应

### 7.4 L2-M3 结果展示层

落地到：

- 悬浮结果面板
- 原文 / 译文 / 状态展示
- copy / close / recapture
- panel renderer 的状态驱动视图由 `Vue 3 + Vite + .vue SFC` 承接

### 7.5 L2-M4 运行治理层

落地到：

- IPC 白名单
- 配置装配
- 审计与观测
- Windows 手动发布链
- 后续 auto-update 预留接入点

## 8. 分阶段计划

### 阶段 1：Windows 桌面壳可运行

目标：

- Electron 应用可在 Windows 上启动
- 托盘可见
- 全局快捷键可注册
- 可以打开截图遮罩窗口和结果面板 stub

验收：

- 按快捷键能拉起截图遮罩
- 点击托盘菜单也能触发同一路径
- 面板能显示假数据

### 阶段 2：截图链打通

目标：

- 在 Windows 上完成真实区域截图
- 输出标准位图对象
- 完成多屏与 DPI 校正

验收：

- 单屏与双屏都能正确选区
- 高分屏下裁剪区域不偏移
- 取消截图不会留下脏窗口

### 阶段 3：OCR + 翻译主链打通

目标：

- 截图结果继续停留在纯 Electron 主链
- 先完成真实本地 OCR
- 再接真实翻译 provider
- 失败时显示状态和错误来源

验收：

- 正常图片能得到原文与译文
- OCR / 翻译失败时有确定性结果
- 超时后能回退或报错
- OpenAI 官方凭据缺失或本地兼容端点不可用时可回退到本地 stub
- 首次配置完成后的第一次截图必须可直接完成 OCR 与翻译，不得要求用户“再试一次”

### 阶段 4：结果交付面稳定

目标：

- 悬浮面板展示原文 / 译文 / 状态
- 复制、关闭、重新截图动作稳定

验收：

- 复制动作成功率稳定
- 关闭不影响下一次截图
- 重新截图可以复用主链

### 阶段 5：治理与发布

目标：

- 审计与观测事件补齐
- 配置与 secrets 接入稳定
- Windows 安装包可生成

验收：

- 关键事件有记录
- secrets 不直接暴露在 renderer
- 能产出 Windows 安装包

## 9. 第一批必须落的代码

优先实现：

1. `apps/desktop_screenshot_translate/electron/main/`
   - 托盘入口
   - 全局快捷键
   - 窗口管理器
   - 本地截图 / stub OCR / stub 翻译管线
2. `apps/desktop_screenshot_translate/electron/renderer/overlay`
   - 截图遮罩页
   - 拖选交互
3. `apps/desktop_screenshot_translate/electron/renderer/panel`
   - Vite + Vue SFC 结果面板页
   - 本地截图结果渲染
4. `apps/desktop_screenshot_translate/python_sidecar/service`
   - 保留为后续扩展入口，不再作为 MVP 首批依赖

## 10. 当前技术决定

本阶段默认采用：

- 宿主：`Electron`
- Windows 截图链：`desktopCapturer + overlay selection`
- Windows OCR 主路：`bundled_tesseract`
- OCR 升级入口：`windows_ocr_api`
- 翻译首选：`openai_translation`
- 翻译端点：`OpenAI-compatible official or LAN endpoint`
- 默认本地模型：`qwen3-30b-a3b-instruct-2507`
- 结果面板：`frameless_transparent_always_on_top`
- 密钥来源：`setup_ui_managed_runtime_store_or_env`
- 发布产物：`NSIS + portable`
- 更新策略：当前关闭应用内自动更新，先走稳定手动发布

这些决定已经同步到了 `implementation_config.toml`，但仍属于可替换的实现路径，不是框架定义。

## 11. 风险与注意项

### 11.1 WSL 与 Windows 路径切换

- 代码可以在 WSL 编辑
- 但 Electron 真正运行时必须在 Windows 工具链中验证
- 不应把 GUI 联调完全押在 WSL 上

### 11.2 截图与 DPI

Windows 多屏与 DPI 是 MVP 的高风险点，必须尽早验证，不要拖到 OCR 后再处理。

### 11.3 Provider 不可用

OCR 与翻译 provider 必须允许 stub / fallback，否则主链联调会被外部依赖卡死。

### 11.4 首次配置后的首帧截图

Windows 下首次配置窗口刚关闭后，第一帧截图容易受窗口合成时序影响。

因此实现层必须满足：

- 截图前先隐藏 setup / panel 等辅助窗口
- 在遮罩隐藏后留出短暂稳定时间，再读取桌面帧
- 对首帧 `tesseract returned empty OCR text` 视为可恢复场景，允许自动重试一次

这个问题已经在真实联调中出现过，因此不再视为“可选优化”。

### 11.5 打包 OCR runtime 的完整性

Windows 安装包中的 OCR 运行时不能只携带 `tesseract.exe`。

必须同时带上：

- `tesseract.exe`
- 同目录运行依赖的 `*.dll`
- `tessdata/eng.traineddata`
- `tessdata/chi_sim.traineddata`
- `tessdata/jpn.traineddata`
- `tessdata/osd.traineddata`

否则会出现“开发态可识别、安装包内 OCR 子进程失败”的问题。

### 11.6 安装器权限模型

Windows 安装器默认应走当前用户安装路径。

这意味着：

- 安装器不应依赖管理员权限才能启动
- `NSIS` 配置应默认关闭提权帮助路径
- “必须右键管理员运行安装器”不应作为对外分发前提

### 11.7 发布与更新边界

当前阶段的真实承诺是“可重复构建、可人工分发”的 Windows 发布链，而不是自动更新。

这意味着：

- 需要稳定产出 `NSIS` 安装包与 `portable` 便携版
- 版本更新当前通过重新分发安装包或便携版完成
- `auto_update` 在未接入更新源、元数据与应用内状态机前必须保持关闭
- 不能因为 `implementation_config` 里写了更新语义，就假定代码已经具备自动更新能力

## 12. 下一步动作

下一会话如果继续实现，建议直接开始：

1. 新建 `apps/desktop_screenshot_translate/` 目录骨架
2. 先完成 Electron Windows 壳
3. 再完成截图遮罩与 stub 结果面板

## 13. 已踩坑后的固定验收项

下面这些项在后续迭代中应视为回归检查，不再只是临时联调观察：

1. 首次启动能自动生成 `%APPDATA%\AiTrans\runtime-overrides.json`
2. 翻译端点未配置时会自动弹出首次配置窗口
3. 用户可直接在首次配置窗口中保存 `base_url / api_key`，不需要手工编辑 JSON
4. 完成首次配置后，第一次截图即可成功，不依赖第二次重试
5. `win-unpacked` 与 `NSIS` 安装版都能完成真实 OCR
6. `NSIS` 安装器可直接启动，不要求管理员权限
7. 安装后应用可从打包资源目录读取 `project-generated`
8. `release:win` 一键发布命令可重复生成 `NSIS + portable` 两类产物
4. 然后接入内置 OCR 运行时与真实翻译链
