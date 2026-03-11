# Windows 联调清单

本清单只服务于 `desktop_screenshot_translate` 的 Windows MVP 端到端联调。

它不改写框架层，也不替代：

- `projects/desktop_screenshot_translate/product_spec.toml`
- `projects/desktop_screenshot_translate/implementation_config.toml`

## 1. 你当前需要知道的边界

- 我可以在仓库里继续补代码、补脚本、补日志和修主链问题。
- 我不能在当前 WSL Linux 会话里替你真实触发 Windows 托盘、全局快捷键、桌面截图或悬浮窗。
- 因此端到端跑通必须由你在 Windows 原生环境执行，我根据你回传的现象继续修。

## 2. 我已经替你准备好的东西

- 纯 Electron Windows MVP 主链：
  - [main.js](/home/zx/shelf/apps/desktop_screenshot_translate/electron/main.js)
  - [translation-adapters.js](/home/zx/shelf/apps/desktop_screenshot_translate/electron/lib/translation-adapters.js)
  - [ocr-adapters.js](/home/zx/shelf/apps/desktop_screenshot_translate/electron/lib/ocr-adapters.js)
- Vue 结果面板：
  - [App.vue](/home/zx/shelf/apps/desktop_screenshot_translate/electron/renderer/panel-src/src/App.vue)
- Windows 运行前预检：
  - [doctor.js](/home/zx/shelf/apps/desktop_screenshot_translate/electron/scripts/doctor.js)

## 3. 你在 Windows 侧需要准备什么

1. Node.js 20+
2. 开发联调可用的 `tesseract`，或已接入内置 OCR 运行时的应用包
3. `openai_translation` 所需凭据，或可访问的局域网兼容端点
4. 能从 Windows 访问当前仓库目录

建议不要直接在 `\\\\wsl$\\...` 路径里跑 Electron 联调。
更稳妥的方式是把仓库放到 Windows 本地盘，或用 Windows 工具链稳定访问当前代码目录。

## 4. 先在 WSL 里做一次物化

在仓库根目录执行：

```bash
uv run python scripts/materialize_project.py --project projects/desktop_screenshot_translate/product_spec.toml
uv run python scripts/validate_strict_mapping.py --check-changes
uv run mypy
```

这一步我已经在当前代码状态上跑通过了。

## 5. 在 Windows PowerShell 里执行

进入：

```powershell
cd <repo>\apps\desktop_screenshot_translate\electron
```

首次安装依赖：

```powershell
npm install
```

设置翻译端点所需环境变量：

```powershell
$env:OPENAI_API_KEY="你的key"
```

如果你要切到局域网里的 OpenAI 兼容端点，再补：

```powershell
$env:AITRANS_OPENAI_BASE_URL="http://<lan-host>:<port>/v1"
```

如果当前开发联调仍走外部 `tesseract`，再补：

```powershell
$env:AITRANS_TESSERACT_PATH="C:\Program Files\Tesseract-OCR\tesseract.exe"
```

先跑预检：

```powershell
npm run doctor
```

预检通过后启动：

```powershell
npm run dev
```

如果你希望预检通过后自动启动：

```powershell
npm run dev:doctor
```

## 6. 端到端验证步骤

启动后按这个顺序验证：

1. 看系统托盘里是否出现应用图标
2. 右键托盘菜单，点击“开始截图翻译”
3. 或直接按快捷键 `Ctrl+Shift+1`
4. 在桌面拖选一块有文字的区域
5. 观察面板状态是否按顺序变化：
   - `capturing`
   - `ocr_processing`
   - `translation_processing`
   - `translation_ready`
6. 检查面板中是否出现：
   - 截图预览
   - OCR 原文
   - OpenAI 返回的译文
   - `OCR: ... / TRANS: ...` provider 信息
7. 点击“复制译文”
8. 粘贴到任意编辑器，验证内容
9. 点击“重新截图”，确认主链可复用
10. 点击“关闭”，确认面板能隐藏且下次还能再次拉起

## 7. 成功标准

以下条件同时成立，才算当前 MVP 主链跑通：

- 托盘正常
- 快捷键正常
- 截图遮罩正常
- 选区不偏移
- OCR 运行时能识别出原文
- `openai_translation` 目标端点能返回译文
- 面板能复制 / 关闭 / 重截图

## 8. 如果失败，先看哪一类

### 8.1 `npm run doctor` 失败

优先把这三个问题先修掉：

- generated 文件缺失
- 开发联调所需 OCR 运行时不可执行
- `openai_translation` 所需凭据未设置，且局域网兼容端点不可用

### 8.2 应用能启动，但截图后失败

先记录面板里的：

- `当前状态`
- `错误来源`
- provider 信息

再把 PowerShell 终端输出一并给我。

### 8.3 有 OCR 原文，但翻译失败

大概率是：

- `OPENAI_API_KEY` 无效
- 局域网兼容端点不可达
- 目标翻译端点返回错误

这时把面板里的 `错误来源` 和终端输出发给我。

### 8.4 选区偏移或截图不对

这通常是 Windows 多屏 / DPI 坐标问题。
把你的显示器数量、缩放比例、主副屏排列方式告诉我，我会继续修 `desktopCapturer + screen` 的坐标补偿。

## 9. 你回传给我什么最有用

联调后请优先回这几项：

1. `npm run doctor` 的输出
2. `npm run dev` 启动后的终端输出
3. 面板里的 `当前状态`
4. 面板里的 `错误来源`
5. 是否出现截图预览
6. 是否出现 OCR 原文
7. 是否出现真实译文
8. 你的 Windows 版本、显示器数量、缩放比例

## 10. 我接下来还能继续做什么

只要你把 Windows 侧现象发回来，我可以继续直接改：

- OCR / 翻译失败回退逻辑
- OpenAI 请求结构
- 截图多屏坐标补偿
- 面板状态与错误展示
- 日志输出和诊断脚本
- 打包前的 Windows 运行时收敛
