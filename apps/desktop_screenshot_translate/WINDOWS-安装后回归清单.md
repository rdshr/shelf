# Windows 安装后回归清单

本清单用于 `AiTrans` Windows 发布后的最小人工回归。

它不替代：

- [WINDOWS-打包发布清单.md](/home/zx/shelf/apps/desktop_screenshot_translate/WINDOWS-%E6%89%93%E5%8C%85%E5%8F%91%E5%B8%83%E6%B8%85%E5%8D%95.md)
- [WINDOWS-联调清单.md](/home/zx/shelf/apps/desktop_screenshot_translate/WINDOWS-%E8%81%94%E8%B0%83%E6%B8%85%E5%8D%95.md)

## 1. 安装与启动

1. 双击 `NSIS` 安装包可直接启动，不要求管理员权限
2. 安装完成后可正常启动应用
3. 启动后托盘图标可见
4. 首次启动会生成 `%APPDATA%\\AiTrans\\runtime-overrides.json`

## 2. 首次配置

1. 未配置翻译端点时会自动弹出首次配置窗口
2. 用户可在界面中直接保存：
   - `base_url`
   - `api_key`
   - `capture_shortcut`
3. 保存后不要求用户手工编辑 JSON

## 3. 截图主链

1. 托盘入口可触发截图
2. 全局快捷键可触发截图
3. `Esc` 和右键可取消截图
4. `Enter` 和双击可触发当前显示器整屏截图
5. 首次配置完成后的第一次截图即可直接进入 OCR 与翻译

## 4. 结果面板

1. 结果面板可显示：
   - 原文
   - 译文
   - `source_language`
   - 状态与错误来源
2. 可执行：
   - 复制译文
   - 重试翻译
   - 重新截图
   - 关闭面板

## 5. 焦点与降级

1. 从外部应用触发截图时，截图完成后焦点应优先回到原前台应用
2. 结果面板在外部应用前台恢复场景下可见但不应强抢焦点
3. 若全局快捷键注册失败，应用仍可通过托盘进入
4. 若翻译端点未配置，应用应自动回到配置引导

## 6. OCR 与翻译

1. 安装版可调用 bundled Tesseract
2. `chi_sim / eng / jpn / osd` 语言包完整可用
3. 提供可达的兼容端点时，真实翻译主链可工作
4. 未提供端点或凭据时，应用行为可解释，不应静默失败

## 7. 发布产物

1. `dist/` 下存在安装版与便携版
2. 发布目录内存在对应 `.blockmap`
3. 发布目录内存在 `release-manifest-<version>.json`
4. 项目版本说明存在且与当前版本一致
