# Frontend L1 模块速查表

本文档不是 `framework/*.md` 真相源，而是面向 `framework/frontend/L1-*` 的快速阅读索引。
它服务于两个目标：
- 在查看文件树时，快速理解每个 `L1` 原子的主关系。
- 在新增模块或阅读相邻模块时，快速判断“它不是什么”。

命名约定补充：
- `frontend/L1` 文件名采用 `L1-编号-族类-职责-原子模块.md`。
- 其中“族类”用于目录树中的第一眼分组，例如 `输入 / 承载 / 浏览 / 导航 / 提示`。
- `L1` 的文件名目标不是替代模块标题，而是降低扫目录时的辨识成本。

## 1. 速查表

| 模块 | 模块短标签 | 典型落地对象 | 不包括 |
| --- | --- | --- | --- |
| `L1-M0` 输入-文本输入-原子模块 | 连续文本编辑 | `input` / `textarea` / inline text editor | 日期时间输入、离散选择控件、集合浏览、页面流程编排 |
| `L1-M1` 输入-离散值选择-原子模块 | 值选择 | `radio group` / `checkbox group` / `switch` / `slider` / `stepper` / `rating` | 纯动作触发、临时展开选择面、互斥视图切换、日期时间输入、结构化字段工作面 |
| `L1-M2` 输入-日期时间输入-原子模块 | 时间值输入 | `date picker` / `time picker` / `range picker` / datetime input | 普通连续文本编辑、任意候选选择面、领域调度规则 |
| `L1-M3` 输入-文件摄取-原子模块 | 文件接纳 | upload input / `dropzone` / intake queue | 纯触发入口、文件库管理、后端上传处理流程 |
| `L1-M4` 动作-触发-原子模块 | 动作入口 | `button` / `icon action` / `submit trigger` / `confirm trigger` | 临时展开选择面、锚点附着提示、文件摄取、集合浏览、离散值选择 |
| `L1-M5` 选择-临时展开选择面-原子模块 | 选择闭合面 | `dropdown` / `menu` / `select panel` / temporary option surface | 纯动作入口、锚点附着提示、长期驻留导航区、离散值选择 |
| `L1-M6` 切换-互斥视图切换-原子模块 | 互斥切换 | `tabs` / segmented control / view switcher | 页面级路由跳转、展开披露、一般集合浏览、离散值选择 |
| `L1-M7` 披露-展开披露-原子模块 | 展开披露 | `accordion` / disclosure / collapsible section | 互斥视图切换、临时展开选择面、页面级导航 |
| `L1-M8` 提示-锚点附着提示-原子模块 | 附着提示 | `tooltip` / popover hint / annotation bubble | 临时展开选择面、纯动作入口、页面级通知流 |
| `L1-M9` 承载-展示与容器-原子模块 | 展示承载 | `panel` / `drawer shell` / content surface / reading viewport | 局部任务接管、媒体预览、临时展开选择面 |
| `L1-M10` 承载-局部任务接管容器-原子模块 | 任务接管 | `dialog` / `modal` / `side sheet` / confirm surface | 普通展示容器、媒体预览、页面级路由流程 |
| `L1-M11` 承载-媒体预览-原子模块 | 媒体预览 | image preview / video preview / audio preview / document page preview | 普通展示容器、局部任务接管、媒体编辑器、资源库管理 |
| `L1-M12` 浏览-集合浏览-原子模块 | 集合内浏览 | `list` / `tree` / item browser / side collection | 页序列导航、路径链导航、临时展开选择面 |
| `L1-M13` 导航-路径链导航-原子模块 | 路径回溯 | `breadcrumb` / path chain / hierarchical backtrack | 一般集合浏览、页序列导航、互斥视图切换 |
| `L1-M14` 导航-页序列导航-原子模块 | 页窗导航 | `pagination` / page window / page jumper | 一般集合浏览、路径链导航、互斥视图切换 |
| `L1-M15` 反馈-标记与反馈-原子模块 | 附着反馈 | `badge` / `tag` / inline status / empty hint / alert bubble | 锚点附着提示、输入内反馈闭环、文件摄取反馈闭环、媒体预览反馈闭环 |

## 2. 快速阅读顺序

如果你是第一次阅读 `frontend/L1`，推荐按下面顺序理解：

1. 先看输入族
   - `L1-M0 / L1-M1 / L1-M2 / L1-M3`
2. 再看最容易混淆的三组
   - `L1-M4 / L1-M5 / L1-M8`
   - `L1-M9 / L1-M10 / L1-M11`
   - `L1-M12 / L1-M13 / L1-M14`
3. 最后看 `L1-M15`
   - 它是“附着反馈”，不是所有反馈的总出口

## 3. 使用建议

- 看文件树时，先用本表确定“主关系”，再进入具体模块。
- 若两个模块看起来都像在描述同一对象，优先比较“不包括”列，而不是比较例子。
- 若一个新对象无法稳定落进某个 `L1` 的“主关系 + 不包括”组合，优先怀疑它属于 `L2`，而不是马上新增 `L1`。

