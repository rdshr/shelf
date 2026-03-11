# Windows 打包发布清单

本清单只服务于 `desktop_screenshot_translate` 的 Windows 安装产物构建。

它不替代：

- [product_spec.toml](/home/zx/shelf/projects/desktop_screenshot_translate/product_spec.toml)
- [implementation_config.toml](/home/zx/shelf/projects/desktop_screenshot_translate/implementation_config.toml)
- [WINDOWS-联调清单.md](/home/zx/shelf/apps/desktop_screenshot_translate/WINDOWS-联调清单.md)

## 1. 发布前提

- 已在仓库根目录完成项目物化
- 已在 Windows 本机执行过 `npm install`
- `electron/vendor/tesseract/` 下已放入可分发的 Tesseract 运行时与 `tessdata`
- 已完成一次 `npm run doctor` 联调通过

## 2. 必备文件

Windows 可发布安装包至少要求：

- `electron/vendor/tesseract/tesseract.exe` 或 `electron/vendor/tesseract/bin/tesseract.exe`
- `electron/vendor/tesseract/*.dll`
- `electron/vendor/tesseract/tessdata/eng.traineddata`
- `electron/vendor/tesseract/tessdata/chi_sim.traineddata`
- `electron/vendor/tesseract/tessdata/jpn.traineddata`

项目生成产物也必须存在：

- `projects/desktop_screenshot_translate/generated/product_spec.json`
- `projects/desktop_screenshot_translate/generated/generation_manifest.json`
- `projects/desktop_screenshot_translate/generated/implementation_bundle.py`

## 3. 打包命令

在 Windows 终端进入：

```powershell
cd <repo>\apps\desktop_screenshot_translate\electron
```

如果本机已经安装过 Tesseract，可先把运行时复制进发布目录：

```powershell
npm run stage:tesseract
```

先跑发布前校验：

```powershell
npm run release:check
```

产出可安装 exe：

```powershell
npm run dist:win
```

如果你只想先产出免安装的便携包：

```powershell
npm run pack:win
```

## 4. 产物位置

构建输出目录：

- `apps/desktop_screenshot_translate/electron/dist/`

预期会看到：

- `desktop-screenshot-translate-<version>-x64.exe`
- 对应的 `latest*.yml` 或便携产物

## 5. 给其他人的运行方式

OCR 运行时已随安装包分发，不应再要求用户手工安装 `tesseract`。

翻译运行时默认不应把密钥硬编码进安装包。推荐方式：

1. 首次启动时会自动生成：
   - `%APPDATA%\\AiTrans\\runtime-overrides.json`
2. 如需手工重建模板，可参考：
   - [runtime-overrides.example.json](/home/zx/shelf/apps/desktop_screenshot_translate/electron/config/runtime-overrides.example.json)
3. 填入：
   - `translation.base_url`
   - `translation.api_key`

如果目标机器走官方 OpenAI，也可以继续使用环境变量：

- `OPENAI_API_KEY`
- `AITRANS_OPENAI_API_KEY`
- `AITRANS_OPENAI_BASE_URL`

## 6. 当前边界

- 当前已能构建 Windows `NSIS` 安装包与 `portable` 产物
- 当前未完成代码签名
- 当前未完成自动更新服务接入
- 若不提供可达的翻译端点与凭据，应用会退回本地 stub 翻译
