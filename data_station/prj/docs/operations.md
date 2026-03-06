# 运行维护说明

## 1. 启动与停止

启动：

```bash
uv run python data_station/prj/main.py
```

停止：

- 前台运行时按 `Ctrl+C`

## 2. 本地访问

页面：

```text
http://127.0.0.1:8010
```

健康检查：

```bash
curl --noproxy '*' http://127.0.0.1:8010/api/health
```

## 3. 首次使用流程

1. 启动服务
2. 使用 `root@root.com / 123` 登录
3. 普通用户在登录页切换到注册模式提交申请
4. root 在页面下方的用户管理区域批准申请
5. root 按需要修改普通用户角色、职责、启停状态
6. 如有需要，root 可在同一区域为用户重置新密码
7. 获批用户重新登录后再使用目录树、上传和检索功能

## 4. 用户与权限管理

### root 种子账号

- root 首次启动时由配置自动注入
- 若 `runtime/users/` 已存在 root 文件，则沿用现有文件
- root 账号当前仅用于本地演示，建议在长期使用前改密码哈希

### 注册用户默认行为

- 新注册用户默认 `status = pending`
- 新注册用户默认角色为最低权限 `viewer`
- 待审批用户不能登录

### root 可执行的后台动作

- 查看用户列表
- 批准注册申请
- 修改普通用户 `username`
- 修改普通用户 `duties`
- 修改普通用户 `role`
- 修改普通用户 `active`
- 为用户设置新密码

说明：

- 当前页面已接入这些后台动作
- 管理端不会展示旧密码，只允许 root 直接写入新密码并重新生成哈希

## 5. 运行期文件

默认目录：`data_station/prj/runtime/`

- `documents.json`：文档主数据
- `folders.json`：目录树数据
- `sessions.json`：登录会话
- `traces.jsonl`：追溯记录
- `users/`：用户目录，每个用户一个 `.json` 文件
- `uploads/`：上传文件
- `exports/`：导出文件

## 6. 常见维护动作

### 清空本地数据

```bash
rm -rf data_station/prj/runtime
```

下次启动会自动重建运行目录和空数据文件，并重新写入 root 种子账号。

### 查看用户文件

```bash
ls data_station/prj/runtime/users
cat data_station/prj/runtime/users/root.local.json
```

### 查看目录树数据

```bash
cat data_station/prj/runtime/folders.json
```

### 查看会话数据

```bash
cat data_station/prj/runtime/sessions.json
```

### 查看最近追溯记录

```bash
tail -n 20 data_station/prj/runtime/traces.jsonl
```

### 手动修改用户密码

先生成新的哈希、盐值和迭代次数，再写回对应用户文件：

```bash
uv run python - <<'PY'
import hashlib
import secrets

password = "ReplaceMe123!"
salt = secrets.token_hex(16)
iterations = 200000
password_hash = hashlib.pbkdf2_hmac(
    "sha256",
    password.encode("utf-8"),
    salt.encode("utf-8"),
    iterations,
).hex()
print("password_salt =", salt)
print("password_iterations =", iterations)
print("password_hash =", password_hash)
PY
```

修改后重启服务。

## 7. 常见问题

### 登录失败

检查：

- 该用户文件是否存在于 `runtime/users/`
- 用户是否为 `active: true`
- 用户状态是否为 `approved`
- `password_hash` / `password_salt` / `password_iterations` 是否匹配

### 注册后无法登录

检查：

- 该用户是否仍为 `pending`
- root 是否已经批准该用户
- root 是否将该用户设置为 `active: true`

### 登录后接口返回 401

检查：

- 浏览器 cookie 是否被清掉
- `session_ttl_hours` 是否太短
- `sessions.json` 是否被手动删除

### 不能创建目录

检查：

- 当前角色是否具备 `folder.create`
- 当前目录深度是否超出 `max_folder_depth`
- 文件夹名是否超出 `max_name_length`

### 上传失败

检查：

- 当前角色是否具备 `upload.create`
- 后缀是否在 `allowed_extensions` 中
- 文件大小是否超过 `max_upload_size_bytes`
- 是否已经登录且已审批

## 8. 改动建议

1. 改界面：优先改 `web/index.html`、`web/style.css`、`web/app.js`
2. 改业务：优先改 `app/modules/`，再改 `app/service.py`
3. 改接口：最后改 `app/http_server.py`
4. 每次改完至少验证注册、root 审批、登录、目录树、新建目录、上传六条链路
