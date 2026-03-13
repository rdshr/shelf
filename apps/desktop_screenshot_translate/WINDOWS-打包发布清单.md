# Windows 打包发布清单

本清单只服务于 `desktop_screenshot_translate` 的 Windows 安装产物构建。

它不替代：

- [product_spec.toml](/home/zx/shelf/projects/desktop_screenshot_translate/product_spec.toml)
- [implementation_config.toml](/home/zx/shelf/projects/desktop_screenshot_translate/implementation_config.toml)
- [WINDOWS-联调清单.md](/home/zx/shelf/apps/desktop_screenshot_translate/WINDOWS-联调清单.md)
- [WINDOWS-安装后回归清单.md](/home/zx/shelf/apps/desktop_screenshot_translate/WINDOWS-%E5%AE%89%E8%A3%85%E5%90%8E%E5%9B%9E%E5%BD%92%E6%B8%85%E5%8D%95.md)

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
- `electron/vendor/tesseract/tessdata/osd.traineddata`

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

如果你要一次性产出正式分发所需的两类 Windows 产物：

```powershell
npm run release:win
```

这个命令会额外生成：

- `release-manifest-<version>.json`
- 若自动更新已启用，还应生成与更新通道对应的元数据文件：
  - `latest.yml` 或
  - `<channel>.yml`，例如 `stable.yml`

## 4. 产物位置

构建输出目录：

- `apps/desktop_screenshot_translate/electron/dist/`

预期会看到：

- `desktop-screenshot-translate-<version>-x64.exe`
- `desktop-screenshot-translate-<version>-x64-portable.exe`
- 对应的 `.blockmap`
- `release-manifest-<version>.json`
- 若自动更新已启用，还应看到与更新通道对应的元数据文件，例如 `stable.yml`

## 5. 给其他人的运行方式

OCR 运行时已随安装包分发，不应再要求用户手工安装 `tesseract`。

翻译运行时默认不应把密钥硬编码进安装包。推荐方式：

1. 首次启动时会自动生成：
   - `%APPDATA%\\AiTrans\\runtime-overrides.json`
2. 用户主路径应是首次配置窗口，直接在界面中填写并保存：
   - `translation.base_url`
   - `translation.api_key`
3. 如需手工重建模板或高级排障，可参考：
   - [runtime-overrides.example.json](/home/zx/shelf/apps/desktop_screenshot_translate/electron/config/runtime-overrides.example.json)

如果目标机器走官方 OpenAI，也可以继续使用环境变量：

- `OPENAI_API_KEY`
- `AITRANS_OPENAI_API_KEY`
- `AITRANS_OPENAI_BASE_URL`

## 6. 已踩坑后的强制检查项

在准备对外分发前，至少要再检查一遍：

1. `NSIS` 安装器能直接双击启动，不要求“以管理员身份运行”
2. 安装完成后的首次启动会自动生成 `%APPDATA%\\AiTrans\\runtime-overrides.json`
3. 未配置翻译端点时会自动弹出首次配置窗口
4. 用户可在首次配置窗口中直接保存 `base_url / api_key`，不需要手工编辑 JSON
5. 配好 `base_url / api_key` 后，第一次截图即可完成 OCR 与翻译
6. `win-unpacked` 与安装版都能正常调用 bundled Tesseract
7. 首次截图若命中空 OCR，不应直接报错给用户，而应由应用内部吸收短时重试

## 7. 自动更新发布要求

当前 Windows 自动更新只针对：

- `NSIS` 安装版

不覆盖：

- `portable` 便携版

若要让安装版自动更新真正可用，更新源目录至少需要提供：

- 与更新通道对应的元数据文件，例如 `stable.yml`
- `desktop-screenshot-translate-<version>-x64.exe`
- `desktop-screenshot-translate-<version>-x64.exe.blockmap`

应用运行时可通过以下入口获得更新源：

- `AITRANS_UPDATE_BASE_URL`
- `%APPDATA%\\AiTrans\\runtime-overrides.json` 中的 `release.update_base_url`

说明：

- `electron-builder` 中的 `publish.generic.url` 仅用于生成 `latest.yml` 等更新元数据
- 应用运行时真正访问的更新地址，仍以上面的环境变量或运行时覆盖配置为准

## 8. 当前边界

- 当前已能构建 Windows `NSIS` 安装包与 `portable` 产物
- `NSIS` 目标默认走当前用户安装路径，不应要求管理员权限
- 当前未完成代码签名
- 当前自动更新仅在更新源真实配置后才会生效
- 未配置更新源时，版本升级仍通过重新分发安装包或便携版完成
- 若不提供可达的翻译端点与凭据，应用会退回本地 stub 翻译

## 9. 发布说明要求

每次对外发布前，必须同时准备：

- `projects/desktop_screenshot_translate/release-notes/<version>.md`
- 双语版本说明
- 正式安装产物

当前 `release:check` 已会校验版本说明文件是否存在，并检查：

- `## 中文说明`
- `## English Notes`
