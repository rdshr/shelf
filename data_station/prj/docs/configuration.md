# 可配置内容说明

配置文件：`data_station/prj/config/default.json`

加载优先级：

1. `--config <path>`
2. 环境变量 `DATA_STATION_PRJ_CONFIG`
3. 默认文件 `data_station/prj/config/default.json`

## 1. 服务与路径

### `server`

- `host`：监听地址
- `port`：监听端口
- `public_origin`：前端展示地址

### `paths`

- `runtime_dir`：运行期目录
- `uploads_dir`：上传文件目录
- `exports_dir`：导出目录
- `document_store_file`：文档记录文件
- `trace_store_file`：追溯文件
- `folder_store_file`：文件夹记录文件
- `session_store_file`：会话记录文件
- `users_dir`：用户文件目录
- `web_dir`：静态页面目录

## 2. 登录、注册与用户

### `l1_authentication`

- `session_cookie_name`：会话 cookie 名称
- `login_title`：登录卡片标题

### `l2_authentication_bootstrap`

用于首启时自动注入 root 种子账号：

- `root_user_id`
- `root_email`
- `root_username`
- `root_duties`
- `root_password_salt`
- `root_password_iterations`
- `root_password_hash`

说明：

- 这里只保存 root 的种子哈希，不保存明文密码。
- 若 `runtime/users/` 已存在同邮箱 root 账号，系统不会重复覆盖。

### `l2_registration_policy`

- `enabled`：是否允许注册
- `minimum_password_length`：最小密码长度
- `default_password_iterations`：新注册用户默认密码哈希迭代次数
- `default_role`：新注册用户默认角色，当前默认 `viewer`
- `assignable_roles`：root 可调整到的角色范围

### `l2_session_management`

- `session_ttl_hours`：会话时长
- `cookie_path`：cookie 路径
- `http_only`：是否仅 HTTP 可读
- `same_site`：SameSite 策略

### 用户文件结构

用户数据不再写在配置文件里，而是按用户单文件存放在 `runtime/users/`。

每个用户文件支持这些字段：

- `user_id`
- `email`
- `username`
- `role`
- `duties`
- `status`：`pending` 或 `approved`
- `active`
- `password_hash`
- `password_salt`
- `password_iterations`
- `approved_at`
- `approved_by`
- `last_login_at`
- `created_at`
- `updated_at`

## 3. 文件树目录

### `l1_folder_tree`

- `collapsed_by_default`：目录抽屉是否默认收起
- `context_menu_actions`：文件右键菜单项

### `l2_folder_defaults`

- `folders`：默认系统目录定义

当前默认目录：

- `uncategorized / 未分类`
- `categorized / 已分类`

### `l2_folder_creation`

- `max_name_length`：文件夹名长度上限
- `max_folder_depth`：用户自建目录深度上限

## 4. 上传链路

### `l2_frontend_upload`

- `max_upload_size_bytes`
- `refresh_after_upload`
- `default_actor_role`

### `l2_upload_contract`

- `upload_path`
- `allowed_methods`
- `max_upload_size_bytes`
- `allowed_extensions`
- `required_headers`
- `success_message`
- `duplicate_message`

### `l3_admission_interface`

- `sanitize_filename`
- `require_content_length`
- `max_header_bytes`

### `l3_payload_handling`

- `allow_empty_file`
- `sha256_enabled`

### `l3_file_persistence`

- `filename_pattern`
- `timestamp_format`

### `l3_result_output`

- `success_status`
- `duplicate_status`

## 5. 状态、追溯、权限

### `l1_state_management` / `l2_state_registration` / `l2_state_transition_control` / `l2_version_idempotency`

控制初始状态、可流转状态、版本号和幂等策略。

### `l1_trace_management` / `l2_trace_event_intake` / `l2_trace_field_normalization` / `l2_trace_record_output`

控制追溯是否开启、必填字段和输出方式。

### `l1_authorization_governance` / `l2_authorization_input_parsing` / `l2_authorization_decision_generation` / `l2_authorization_scope_governance`

控制动作到角色的映射、资源作用域和默认作用域。

当前包含的后台用户管理动作：

- `admin.user.view`
- `admin.user.approve`
- `admin.user.update`

当前包含的资源范围：

- `folder_tree`
- `user_directory`
- `manual_document`
- `document_collection`

## 6. 处理审核与展示

### `l1_processing_review`

- `processing_target_state`
- `review_approved_state`
- `review_rejected_state`

### `l2_processing_input_preparation`

- `allowed_source_states`

### `l2_structured_processing_service`

- `preview_bytes`
- `keyword_limit`
- `text_decode_charset`

### `l2_review_writeback`

- `allowed_review_results`
- `default_review_comment`

### `l1_display_retrieval`

- `default_page_size`
- `max_page_size`

### `l2_list_retrieval`

- `default_sort`

### `l2_detail_display`

- `include_internal_paths`

### `l2_reuse_export`

- `export_format`
- `export_filename_pattern`

## 7. 密码维护

当前密码使用 `PBKDF2-HMAC-SHA256`，并为每个用户单独保存：

- `password_salt`
- `password_iterations`
- `password_hash`

如果需要手动改某个用户密码，应先生成新的哈希，再写回对应用户文件。例如：

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

不要把明文密码直接写入任何 JSON 文件。

## 8. 调整建议

1. 优先改配置，不要先改代码
2. 角色、目录默认项、状态流转这类关键项改完后，重启服务再验证
3. 修改用户体系后，至少检查注册、root 审批、登录、目录树、上传五条链路
