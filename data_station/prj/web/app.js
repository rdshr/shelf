const state = {
  bootstrap: null,
  currentUser: null,
  tree: [],
  selectedFolderId: null,
  selectedDocumentId: null,
  detailDocument: null,
  contextTarget: null,
  authMode: "login",
  adminUsers: []
};

const elements = {
  loginScreen: document.getElementById("loginScreen"),
  showLoginMode: document.getElementById("showLoginMode"),
  showRegisterMode: document.getElementById("showRegisterMode"),
  loginForm: document.getElementById("loginForm"),
  registerForm: document.getElementById("registerForm"),
  loginTitle: document.getElementById("loginTitle"),
  loginEmail: document.getElementById("loginEmail"),
  loginPassword: document.getElementById("loginPassword"),
  loginMessage: document.getElementById("loginMessage"),
  registerUsername: document.getElementById("registerUsername"),
  registerEmail: document.getElementById("registerEmail"),
  registerPassword: document.getElementById("registerPassword"),
  registerDuties: document.getElementById("registerDuties"),
  registerMessage: document.getElementById("registerMessage"),
  workspaceShell: document.getElementById("workspaceShell"),
  drawerToggle: document.getElementById("drawerToggle"),
  drawerClose: document.getElementById("drawerClose"),
  treeDrawer: document.getElementById("treeDrawer"),
  treeRoot: document.getElementById("treeRoot"),
  folderForm: document.getElementById("folderForm"),
  folderName: document.getElementById("folderName"),
  documentType: document.getElementById("documentType"),
  source: document.getElementById("source"),
  fileInput: document.getElementById("fileInput"),
  fileLabel: document.getElementById("fileLabel"),
  uploadButton: document.getElementById("uploadButton"),
  uploadResult: document.getElementById("uploadResult"),
  detailTitle: document.getElementById("detailTitle"),
  detailMeta: document.getElementById("detailMeta"),
  detailResult: document.getElementById("detailResult"),
  userName: document.getElementById("userName"),
  userMeta: document.getElementById("userMeta"),
  logoutButton: document.getElementById("logoutButton"),
  statusText: document.getElementById("statusText"),
  contextMenu: document.getElementById("contextMenu"),
  adminPanel: document.getElementById("adminPanel"),
  adminUsers: document.getElementById("adminUsers")
};

function setStatus(message) {
  elements.statusText.textContent = message;
}

function formatTime(value) {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("zh-CN", { hour12: false });
}

function renderJson(target, payload) {
  target.textContent = JSON.stringify(payload, null, 2);
}

function parseDuties(value) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    credentials: "same-origin",
    ...options
  });
  const contentType = response.headers.get("Content-Type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : {};
  if (!response.ok) {
    if (response.status === 401) {
      showLogin();
    }
    throw new Error(payload.message || `Request failed: ${response.status}`);
  }
  return payload;
}

function switchAuthMode(mode) {
  state.authMode = mode;
  const loginMode = mode === "login";
  elements.showLoginMode.classList.toggle("active", loginMode);
  elements.showRegisterMode.classList.toggle("active", !loginMode);
  elements.loginForm.classList.toggle("hidden", !loginMode);
  elements.registerForm.classList.toggle("hidden", loginMode);
  elements.loginMessage.textContent = "";
  elements.registerMessage.textContent = "";
}

async function loadBootstrap() {
  state.bootstrap = await requestJson("/api/bootstrap");
  elements.loginTitle.textContent = state.bootstrap.auth.loginTitle || "Data Station";
}

async function restoreSession() {
  try {
    const payload = await requestJson("/api/auth/session");
    state.currentUser = payload.user;
    state.bootstrap = payload.bootstrap;
    showWorkspace();
    await afterAuthenticated();
    setStatus("ready");
  } catch (_error) {
    showLogin();
  }
}

function showLogin() {
  state.currentUser = null;
  state.tree = [];
  state.adminUsers = [];
  state.selectedFolderId = null;
  state.selectedDocumentId = null;
  state.detailDocument = null;
  elements.workspaceShell.classList.add("hidden");
  elements.loginScreen.classList.remove("hidden");
  elements.loginPassword.value = "";
  elements.registerPassword.value = "";
  elements.adminPanel.classList.add("hidden");
  closeContextMenu();
  switchAuthMode(state.authMode || "login");
}

function showWorkspace() {
  elements.loginScreen.classList.add("hidden");
  elements.workspaceShell.classList.remove("hidden");
  updateUserChip();
  const collapsed = state.bootstrap?.folders?.collapsedByDefault ?? true;
  elements.treeDrawer.classList.toggle("collapsed", collapsed);
}

function updateUserChip() {
  if (!state.currentUser) {
    elements.userName.textContent = "-";
    elements.userMeta.textContent = "-";
    return;
  }
  elements.userName.textContent = state.currentUser.username;
  const duties = Array.isArray(state.currentUser.duties) ? state.currentUser.duties.join(" / ") : "";
  elements.userMeta.textContent = `${state.currentUser.email} · ${duties || state.currentUser.role}`;
}

async function afterAuthenticated() {
  await loadTree();
  if (state.currentUser?.role === "root") {
    elements.adminPanel.classList.remove("hidden");
    await loadAdminUsers();
  } else {
    elements.adminPanel.classList.add("hidden");
  }
}

async function handleLogin(event) {
  event.preventDefault();
  elements.loginMessage.textContent = "";
  try {
    const payload = await requestJson("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: elements.loginEmail.value.trim(),
        password: elements.loginPassword.value
      })
    });
    state.currentUser = payload.user;
    state.bootstrap = payload.bootstrap;
    showWorkspace();
    await afterAuthenticated();
    elements.loginPassword.value = "";
    setStatus(`hello, ${payload.user.username}`);
  } catch (error) {
    elements.loginMessage.textContent = error.message;
  }
}

async function handleRegister(event) {
  event.preventDefault();
  elements.registerMessage.textContent = "";
  try {
    const payload = await requestJson("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: elements.registerUsername.value.trim(),
        email: elements.registerEmail.value.trim(),
        password: elements.registerPassword.value,
        duties: parseDuties(elements.registerDuties.value)
      })
    });
    elements.registerForm.reset();
    elements.registerMessage.textContent = payload.message;
    switchAuthMode("login");
    elements.loginEmail.value = payload.user.email;
  } catch (error) {
    elements.registerMessage.textContent = error.message;
  }
}

async function handleLogout() {
  try {
    await requestJson("/api/auth/logout", { method: "POST" });
  } catch (_error) {
    // Ignore logout errors and force local reset.
  }
  showLogin();
}

async function loadTree(preferredDocumentId = null) {
  const payload = await requestJson("/api/tree");
  state.tree = payload.folders;
  if (!state.selectedFolderId) {
    state.selectedFolderId = payload.selected_folder_id;
  }
  renderTree();
  if (preferredDocumentId) {
    await openDocument(preferredDocumentId);
  }
}

function renderTree() {
  elements.treeRoot.innerHTML = "";
  for (const folder of state.tree) {
    elements.treeRoot.appendChild(renderFolderNode(folder));
  }
}

function renderFolderNode(folder) {
  const wrapper = document.createElement("div");
  wrapper.className = "folder-node";

  const button = document.createElement("button");
  button.type = "button";
  button.className = "folder-label";
  if (folder.folder_id === state.selectedFolderId) {
    button.classList.add("active");
  }
  button.innerHTML = `
    <span class="folder-icon">▣</span>
    <span>${folder.name}</span>
  `;
  button.addEventListener("click", () => {
    state.selectedFolderId = folder.folder_id;
    clearDocumentSelection();
    renderTree();
    setStatus(`目录: ${folder.name}`);
  });
  wrapper.appendChild(button);

  const children = document.createElement("ul");
  for (const documentItem of folder.documents || []) {
    children.appendChild(renderFileNode(documentItem));
  }
  for (const child of folder.children || []) {
    const item = document.createElement("li");
    item.appendChild(renderFolderNode(child));
    children.appendChild(item);
  }
  wrapper.appendChild(children);
  return wrapper;
}

function renderFileNode(documentItem) {
  const item = document.createElement("li");
  item.className = "file-node";

  const button = document.createElement("button");
  button.type = "button";
  button.className = "file-label";
  if (documentItem.document_id === state.selectedDocumentId) {
    button.classList.add("active");
  }
  button.innerHTML = `
    <span class="file-icon">●</span>
    <span>
      <span>${documentItem.filename}</span>
      <span class="file-subtle">${formatTime(documentItem.uploaded_at)}</span>
    </span>
  `;
  button.addEventListener("click", () => {
    openDocument(documentItem.document_id).catch((error) => setStatus(error.message));
  });
  button.addEventListener("contextmenu", (event) => {
    event.preventDefault();
    state.contextTarget = documentItem;
    showContextMenu(event.clientX, event.clientY);
  });

  item.appendChild(button);
  return item;
}

function showContextMenu(x, y) {
  const actions = state.bootstrap?.folders?.menuActions || [];
  elements.contextMenu.innerHTML = "";
  for (const action of actions) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = action;
    button.addEventListener("click", () => {
      setStatus(`${action}：功能预留`);
      closeContextMenu();
    });
    elements.contextMenu.appendChild(button);
  }
  elements.contextMenu.style.left = `${Math.min(x, window.innerWidth - 180)}px`;
  elements.contextMenu.style.top = `${Math.min(y, window.innerHeight - 220)}px`;
  elements.contextMenu.classList.remove("hidden");
}

function closeContextMenu() {
  elements.contextMenu.classList.add("hidden");
  elements.contextMenu.innerHTML = "";
}

function clearDocumentSelection() {
  state.selectedDocumentId = null;
  state.detailDocument = null;
  elements.detailTitle.textContent = "未选中文件";
  elements.detailMeta.innerHTML = "";
  elements.detailResult.textContent = "选择左侧目录中的文件。";
}

async function openDocument(documentId) {
  const payload = await requestJson(`/api/documents/${documentId}`);
  state.selectedDocumentId = documentId;
  state.selectedFolderId = payload.document.folder_id;
  state.detailDocument = payload.document;
  renderTree();
  renderDocumentDetail(payload.document);
  setStatus(payload.document.original_filename || payload.document.document_id);
}

function renderDocumentDetail(documentItem) {
  elements.detailTitle.textContent = documentItem.original_filename;
  const meta = [
    ["目录", documentItem.folder_name || documentItem.folder_id],
    ["状态", documentItem.state],
    ["上传者", documentItem.metadata?.uploaded_by || "-"],
    ["邮箱", documentItem.metadata?.uploaded_by_email || "-"],
    ["日期", formatTime(documentItem.created_at)],
    ["大小", `${documentItem.size_bytes} bytes`]
  ];
  elements.detailMeta.innerHTML = meta
    .map(
      ([label, value]) => `
        <div class="meta-item">
          <div class="meta-label">${label}</div>
          <div class="meta-value">${value}</div>
        </div>
      `
    )
    .join("");
  renderJson(elements.detailResult, documentItem);
}

async function handleCreateFolder(event) {
  event.preventDefault();
  const name = elements.folderName.value.trim();
  if (!name) {
    return;
  }
  try {
    const payload = await requestJson("/api/folders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, parent_id: state.selectedFolderId })
    });
    elements.folderName.value = "";
    await loadTree();
    state.selectedFolderId = payload.folder.folder_id;
    renderTree();
    setStatus(`已创建目录 ${payload.folder.name}`);
  } catch (error) {
    setStatus(error.message);
  }
}

async function handleUpload() {
  const file = elements.fileInput.files[0];
  if (!file) {
    setStatus("请先选择文件");
    return;
  }
  const maxSize = state.bootstrap?.upload?.maxUploadSizeBytes || 0;
  if (maxSize && file.size > maxSize) {
    renderJson(elements.uploadResult, { ok: false, message: `文件超过限制 ${maxSize} bytes` });
    return;
  }
  setStatus(`上传 ${file.name}`);
  const response = await fetch(state.bootstrap.upload.uploadPath, {
    method: "POST",
    credentials: "same-origin",
    headers: {
      "Content-Type": file.type || "application/octet-stream",
      "X-Filename": encodeURIComponent(file.name),
      "X-Document-Type": elements.documentType.value.trim() || "manual_document",
      "X-Source": elements.source.value.trim() || "web_manual",
      "X-Request-Id": generateRequestId()
    },
    body: file
  });
  const payload = await response.json();
  renderJson(elements.uploadResult, payload);
  if (!response.ok) {
    if (response.status === 401) {
      showLogin();
    }
    setStatus(payload.message || `上传失败 ${response.status}`);
    return;
  }
  elements.fileInput.value = "";
  elements.fileLabel.textContent = "选择文件";
  await loadTree(payload.document?.document_id || null);
  setStatus(`${file.name} 已进入未分类`);
}

async function loadAdminUsers() {
  const payload = await requestJson("/api/admin/users");
  state.adminUsers = payload.users;
  renderAdminUsers();
}

function renderAdminUsers() {
  elements.adminUsers.innerHTML = "";
  for (const user of state.adminUsers) {
    const card = document.createElement("article");
    card.className = "user-card";
    const pending = user.status === "pending";
    const duties = Array.isArray(user.duties) ? user.duties.join(", ") : "";
    const minimumPasswordLength = state.bootstrap?.auth?.minimumPasswordLength || 8;
    const roleOptions = (state.bootstrap?.auth?.assignableRoles || []).map((role) => `
      <option value="${role}" ${role === user.role ? "selected" : ""}>${role}</option>
    `).join("");
    card.innerHTML = `
      <div class="user-top">
        <div>
          <div class="user-title">${user.username}</div>
          <div class="user-subtle">${user.email}</div>
        </div>
        <span class="status-pill ${pending ? "pending" : ""}">${user.status}</span>
      </div>
      <div class="user-grid">
        <input data-field="username" value="${user.username}" />
        <div class="user-grid two">
          <select data-field="role">${roleOptions}</select>
          <label class="inline-check">
            <input data-field="active" type="checkbox" ${user.active ? "checked" : ""} />
            <span>active</span>
          </label>
        </div>
        <input data-field="duties" value="${duties}" placeholder="职责，逗号分隔" />
        <input data-field="password" type="password" placeholder="新密码，留空表示不改" minlength="${minimumPasswordLength}" />
        <div class="user-actions">
          ${pending ? '<button type="button" class="accent-button approve-button">通过</button>' : ""}
          <button type="button" class="ghost-light save-button">保存</button>
        </div>
      </div>
    `;

    const approveButton = card.querySelector(".approve-button");
    if (approveButton) {
      approveButton.addEventListener("click", () => {
        approveAdminUser(user.user_id).catch((error) => setStatus(error.message));
      });
    }

    card.querySelector(".save-button").addEventListener("click", () => {
      const password = card.querySelector('[data-field="password"]').value;
      const payload = {
        username: card.querySelector('[data-field="username"]').value.trim(),
        role: card.querySelector('[data-field="role"]').value,
        duties: parseDuties(card.querySelector('[data-field="duties"]').value),
        active: card.querySelector('[data-field="active"]').checked
      };
      if (password) {
        payload.password = password;
      }
      updateAdminUser(user.user_id, payload).catch((error) => setStatus(error.message));
    });

    elements.adminUsers.appendChild(card);
  }
  if (!state.adminUsers.length) {
    elements.adminUsers.innerHTML = '<div class="user-subtle">没有用户数据。</div>';
  }
}

async function approveAdminUser(userId) {
  const payload = await requestJson(`/api/admin/users/${userId}/approve`, { method: "POST" });
  setStatus(`已通过 ${payload.user.email}`);
  await loadAdminUsers();
}

async function updateAdminUser(userId, payload) {
  const result = await requestJson(`/api/admin/users/${userId}/update`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  setStatus(`已更新 ${result.user.email}`);
  await loadAdminUsers();
}

function generateRequestId() {
  if (window.crypto && window.crypto.randomUUID) {
    return window.crypto.randomUUID();
  }
  return `req-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function bindEvents() {
  elements.showLoginMode.addEventListener("click", () => switchAuthMode("login"));
  elements.showRegisterMode.addEventListener("click", () => switchAuthMode("register"));
  elements.loginForm.addEventListener("submit", handleLogin);
  elements.registerForm.addEventListener("submit", handleRegister);
  elements.logoutButton.addEventListener("click", () => {
    handleLogout().catch((error) => setStatus(error.message));
  });
  elements.drawerToggle.addEventListener("click", () => {
    elements.treeDrawer.classList.remove("collapsed");
  });
  elements.drawerClose.addEventListener("click", () => {
    elements.treeDrawer.classList.add("collapsed");
  });
  elements.folderForm.addEventListener("submit", handleCreateFolder);
  elements.uploadButton.addEventListener("click", () => {
    handleUpload().catch((error) => setStatus(error.message));
  });
  elements.fileInput.addEventListener("change", () => {
    const file = elements.fileInput.files[0];
    elements.fileLabel.textContent = file ? file.name : "选择文件";
  });
  document.addEventListener("click", (event) => {
    if (!elements.contextMenu.contains(event.target)) {
      closeContextMenu();
    }
  });
  window.addEventListener("resize", closeContextMenu);
}

async function bootstrap() {
  bindEvents();
  switchAuthMode("login");
  await loadBootstrap();
  await restoreSession();
}

bootstrap().catch((error) => {
  showLogin();
  elements.loginMessage.textContent = error.message;
});
