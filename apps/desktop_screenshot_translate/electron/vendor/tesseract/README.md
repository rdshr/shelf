当前目录用于承载随应用分发的 Tesseract 运行时。

目标路径约定：

- 开发态优先查找 `electron/vendor/tesseract/tesseract.exe`
- 也兼容 `electron/vendor/tesseract/bin/tesseract.exe`
- 打包态优先查找 `process.resourcesPath/tesseract/tesseract.exe`

当前仓库不直接提交第三方二进制。
在正式接入 bundling 前，开发联调仍可通过 `AITRANS_TESSERACT_PATH` 指向外部可执行文件。
