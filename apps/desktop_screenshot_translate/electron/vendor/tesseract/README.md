当前目录用于承载随应用分发的 Tesseract 运行时。

目标路径约定：

- 开发态优先查找 `electron/vendor/tesseract/tesseract.exe`
- 也兼容 `electron/vendor/tesseract/bin/tesseract.exe`
- 打包态优先查找 `process.resourcesPath/tesseract/tesseract.exe`
- 打包态若存在 `tessdata`，会自动传入 `--tessdata-dir`

当前仓库不直接提交第三方二进制。
在正式接入 bundling 前，开发联调仍可通过 `AITRANS_TESSERACT_PATH` 指向外部可执行文件。

Windows 可发布安装包至少应包含：

- `vendor/tesseract/tesseract.exe` 或 `vendor/tesseract/bin/tesseract.exe`
- `vendor/tesseract/*.dll`
- `vendor/tesseract/tessdata/eng.traineddata`
- `vendor/tesseract/tessdata/chi_sim.traineddata`
- `vendor/tesseract/tessdata/jpn.traineddata`
