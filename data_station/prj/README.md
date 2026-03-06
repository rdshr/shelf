# Data Station PRJ

`data_station/prj` 是基于 `framework/` 模块标准落地的本地参考工程。

当前实现重点：

- 邮箱 + 密码登录
- 注册申请 + `root` 审批
- `root` 用户后台调整普通用户角色、职责、启停状态、密码
- 用户记录落盘到 `runtime/users/` 目录
- 密码仅保存 PBKDF2-SHA256 哈希，不保存明文
- 会话化访问控制
- 左上角抽屉式文件树
- 默认 `未分类 / 已分类` 目录
- 用户自建文件夹
- 文件上传后默认进入 `未分类`
- 文件右键菜单占位：`移动 / 清洗 / 删除 / 审核 / 提交`

## 1. 运行

在仓库根目录执行：

```bash
uv run python data_station/prj/main.py
```

访问地址：

```text
http://127.0.0.1:8010
```

## 2. 初始 root 账号

仅用于本地演示：

- 邮箱：`root@root.com`
- 密码：`123`

说明：

- 首次启动时，如果 `runtime/users/` 下不存在该账号，系统会自动写入 `root` 用户文件。
- 这是本地种子账号，不适合直接用于生产环境。
- 密码不会明文保存，实际落盘内容是哈希、盐值和迭代次数。

## 3. 注册与审批流程

1. 新用户在登录页切换到“注册”模式提交邮箱、密码、用户名、职责
2. 系统创建 `pending` 状态用户，默认角色为最低权限 `viewer`
3. `root` 登录后，可在管理面板查看待审批用户
4. `root` 可执行批准，并调整用户的角色、职责、启停状态、密码
5. 用户获批后才能正常登录

## 4. 用户数据位置

运行后，用户文件默认写入：

```text
data_station/prj/runtime/users/
```

每个用户单独一个 `.json` 文件，包含：

- `user_id`
- `email`
- `username`
- `role`
- `duties`
- `status`
- `active`
- `password_hash`
- `password_salt`
- `password_iterations`
- `approved_at`
- `approved_by`
- `last_login_at`
- `created_at`
- `updated_at`

## 5. 功能结构

- 认证与会话
  - [authentication.py](/home/wuyz/Ability_Enhance/frame/shelf/data_station/prj/app/modules/authentication.py)
- 文件树目录
  - [folders.py](/home/wuyz/Ability_Enhance/frame/shelf/data_station/prj/app/modules/folders.py)
- 上传链路
  - [upload.py](/home/wuyz/Ability_Enhance/frame/shelf/data_station/prj/app/modules/upload.py)
- 状态管理
  - [state.py](/home/wuyz/Ability_Enhance/frame/shelf/data_station/prj/app/modules/state.py)
- 追溯管理
  - [trace.py](/home/wuyz/Ability_Enhance/frame/shelf/data_station/prj/app/modules/trace.py)
- 权限治理
  - [authorization.py](/home/wuyz/Ability_Enhance/frame/shelf/data_station/prj/app/modules/authorization.py)
- 处理审核
  - [processing_review.py](/home/wuyz/Ability_Enhance/frame/shelf/data_station/prj/app/modules/processing_review.py)
- 展示导出
  - [display.py](/home/wuyz/Ability_Enhance/frame/shelf/data_station/prj/app/modules/display.py)
- 组合服务
  - [service.py](/home/wuyz/Ability_Enhance/frame/shelf/data_station/prj/app/service.py)
- HTTP 入口
  - [http_server.py](/home/wuyz/Ability_Enhance/frame/shelf/data_station/prj/app/http_server.py)
- 前端页面
  - [index.html](/home/wuyz/Ability_Enhance/frame/shelf/data_station/prj/web/index.html)
  - [app.js](/home/wuyz/Ability_Enhance/frame/shelf/data_station/prj/web/app.js)
  - [style.css](/home/wuyz/Ability_Enhance/frame/shelf/data_station/prj/web/style.css)

## 6. 目录说明

```text
prj/
  app/
  config/
  docs/
  runtime/
  web/
  main.py
```

运行后，数据默认写入 `runtime/`：

- `documents.json`
- `folders.json`
- `sessions.json`
- `traces.jsonl`
- `users/`
- `uploads/`
- `exports/`

## 7. 相关文档

- [配置说明](docs/configuration.md)
- [运行维护说明](docs/operations.md)
