# Frontend L1 模块速查表

本文档不是 `framework/*.md` 真相源，而是面向 `framework/frontend/L1-*` 的快速阅读索引。
它服务于两个目标：
- 在查看文件树时，快速理解每个 `L1` 原子的主关系。
- 在新增模块或阅读相邻模块时，快速判断“它不是什么”。

## 1. 速查表

| 模块 | 模块短标签 | 典型落地对象 | 不包括 |
| --- | --- | --- | --- |
| `L1-M0` 触发原子 | 动作入口 | `button` / `icon action` / `submit trigger` / `toggle trigger` | 临时展开选择面、锚点附着提示、文件摄取、集合浏览 |
| `L1-M1` 文本输入原子 | 连续文本编辑 | `input` / `textarea` / inline text editor | 日期时间输入、离散选择控件、集合浏览、页面流程编排 |
| `L1-M2` 展示与容器原子 | 展示承载 | `panel` / `drawer shell` / content surface / reading viewport | 局部任务接管、媒体预览、临时展开选择面 |
| `L1-M3` 集合浏览原子 | 集合内浏览 | `list` / `tree` / item browser / side collection | 页序列导航、路径链导航、临时展开选择面 |
| `L1-M4` 标记与反馈原子 | 附着反馈 | `badge` / `tag` / inline status / empty hint / alert bubble | 锚点附着提示、输入内反馈闭环、文件摄取反馈闭环、媒体预览反馈闭环 |
| `L1-M5` 局部任务接管容器原子 | 任务接管 | `dialog` / `modal` / `side sheet` / confirm surface | 普通展示容器、媒体预览、页面级路由流程 |
| `L1-M6` 互斥视图切换原子 | 互斥切换 | `tabs` / segmented control / view switcher | 页面级路由跳转、展开披露、一般集合浏览 |
| `L1-M7` 临时展开选择面原子 | 选择闭合面 | `dropdown` / `menu` / `select panel` / temporary option surface | 纯动作入口、锚点附着提示、长期驻留导航区 |
| `L1-M8` 锚点附着提示原子 | 附着提示 | `tooltip` / popover hint / annotation bubble | 临时展开选择面、纯动作入口、页面级通知流 |
| `L1-M9` 展开披露原子 | 展开披露 | `accordion` / disclosure / collapsible section | 互斥视图切换、临时展开选择面、页面级导航 |
| `L1-M10` 页序列导航原子 | 页窗导航 | `pagination` / page window / page jumper | 一般集合浏览、路径链导航、互斥视图切换 |
| `L1-M11` 路径链导航原子 | 路径回溯 | `breadcrumb` / path chain / hierarchical backtrack | 一般集合浏览、页序列导航、互斥视图切换 |
| `L1-M12` 文件摄取原子 | 文件接纳 | upload input / `dropzone` / intake queue | 纯触发入口、文件库管理、后端上传处理流程 |
| `L1-M13` 日期时间输入原子 | 时间值输入 | `date picker` / `time picker` / `range picker` / datetime input | 普通连续文本编辑、任意候选选择面、领域调度规则 |
| `L1-M14` 媒体预览原子 | 媒体预览 | image preview / video preview / audio preview / document page preview | 普通展示容器、局部任务接管、媒体编辑器、资源库管理 |

## 2. 快速阅读顺序

如果你是第一次阅读 `frontend/L1`，推荐按下面顺序理解：

1. 先看“最容易混淆的三组”
   - `L1-M0 / L1-M7 / L1-M8`
   - `L1-M2 / L1-M5 / L1-M14`
   - `L1-M3 / L1-M10 / L1-M11`
2. 再看输入族
   - `L1-M1 / L1-M13`
3. 最后看 `L1-M4`
   - 它是“附着反馈”，不是所有反馈的总出口

## 3. 使用建议

- 看文件树时，先用本表确定“主关系”，再进入具体模块。
- 若两个模块看起来都像在描述同一对象，优先比较“不包括”列，而不是比较例子。
- 若一个新对象无法稳定落进某个 `L1` 的“主关系 + 不包括”组合，优先怀疑它属于 `L2`，而不是马上新增 `L1`。
