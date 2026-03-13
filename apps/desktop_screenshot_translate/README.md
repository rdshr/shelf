# desktop_screenshot_translate app skeleton

本目录承载 `desktop_screenshot_translate` 的真实实现代码，不承载产品真相本身。

上游输入仍然是：

- `framework/*.md`
- `projects/desktop_screenshot_translate/product_spec.toml`
- `projects/desktop_screenshot_translate/implementation_config.toml`
- `projects/desktop_screenshot_translate/generated/*`

目录说明：

- `electron/`：Windows MVP 的纯 Electron 主链，负责托盘、快捷键、截图、OCR、翻译 provider 和结果面板
  - `renderer/overlay/`：原生 HTML/JS
  - `renderer/panel-src/`：`Vue 3 + Vite + .vue SFC` 源码
  - `renderer/panel-dist/`：构建产物，由 Vite 生成
- `python_sidecar/`：可选扩展点，后续若 OCR / 翻译编排明显更适合 Python 时再接回主链

运行约定：

- Electron 真正联调应在 Windows 原生工具链中完成
- WSL 主要负责编辑、生成、校验与 Python sidecar 开发

建议启动顺序：

1. 先物化项目：
   - `uv run python scripts/materialize_project.py --project projects/desktop_screenshot_translate/product_spec.toml`
2. 在 Windows 侧进入 `apps/desktop_screenshot_translate/electron/` 运行：
   - `npm install`
   - 若仓库同时被 WSL 与 Windows 共用，发布脚本会自动在 Windows 下使用 `.venv-win`
3. 若要启用真实 OCR / 翻译 provider，再补运行时环境：
   - 正式发布目标是“应用内置 OCR 运行时”，不要求终端用户手工安装 `tesseract`
   - 当前开发联调阶段若 bundling 尚未接入，可临时设置 `AITRANS_TESSERACT_PATH`
   - `openai_translation` 目标端点允许是 OpenAI 官方或局域网内兼容端点
   - 官方或兼容端点都可使用 `OPENAI_API_KEY` 或 `AITRANS_OPENAI_API_KEY`
   - 若切到局域网兼容端点，可设置 `AITRANS_OPENAI_BASE_URL`
4. 在 Windows 侧做一次预检并启动：
   - `npm run doctor`
   - `npm run panel:build`
   - `npm run dev`
5. 若后续需要 Python sidecar 扩展，再额外启动：
   - `uv run python -m apps.desktop_screenshot_translate.python_sidecar.service.app`

更完整的 Windows 端到端联调步骤见：

- [WINDOWS-联调清单.md](/home/zx/shelf/apps/desktop_screenshot_translate/WINDOWS-联调清单.md)

Windows 可发布安装包路径：

1. 先把 `tesseract.exe` 与所需 `tessdata/*.traineddata` 放入：
   - `apps/desktop_screenshot_translate/electron/vendor/tesseract/`
   - 如果本机已经安装过 Tesseract，也可以直接运行：
     - `npm run stage:tesseract`
2. 再执行：
   - `npm run release:check`
   - `npm run dist:win`
   - 如果要同时生成安装包与便携版，可直接执行 `npm run release:win`
3. 生成的安装产物位于：
   - `apps/desktop_screenshot_translate/electron/dist/`
   - 发布脚本会先自动清空 `dist/`，避免旧版本产物残留

发布时还应同步准备：

- [0.1.2.md](/home/zx/shelf/projects/desktop_screenshot_translate/release-notes/0.1.2.md)
- [WINDOWS-安装后回归清单.md](/home/zx/shelf/apps/desktop_screenshot_translate/WINDOWS-%E5%AE%89%E8%A3%85%E5%90%8E%E5%9B%9E%E5%BD%92%E6%B8%85%E5%8D%95.md)

当前发布边界：

- 已支持 Windows `NSIS` 安装包与 `portable` 便携版
- `NSIS` 安装版已支持应用内自动更新接入
- `portable` 便携版仍通过重新分发新包完成升级
- 自动更新只有在提供 `AITRANS_UPDATE_BASE_URL` 或 `release.update_base_url` 后才会生效

面向目标机器的运行时配置：

- 不建议要求终端用户设置环境变量
- 首次启动时会自动弹出配置窗口，优先通过界面填写并保存翻译端点
- 应用内部仍会在配置目录生成并维护 `runtime-overrides.json`
- 默认配置文件位置：
  - `%APPDATA%\\AiTrans\\runtime-overrides.json`
- 若你想手工重建模板或做高级排障，可参考：
  - [runtime-overrides.example.json](/home/zx/shelf/apps/desktop_screenshot_translate/electron/config/runtime-overrides.example.json)
- 普通用户主路径不应是手工编辑该文件；其中当前可配置：
  - `translation.base_url`
  - `translation.api_key`
  - `ocr.tesseract_path`
  - `ocr.tessdata_dir`
