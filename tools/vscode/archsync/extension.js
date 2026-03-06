const cp = require("child_process");
const fs = require("fs");
const path = require("path");
const vscode = require("vscode");

const WATCH_PREFIXES = ["framework/", "specs/", "mapping/", "src/", "docs/"];
const WATCH_FILES = new Set([
  "AGENTS.md",
  "README.md",
  "scripts/validate_strict_mapping.py",
  "scripts/generate_framework_tree_hierarchy.py"
]);

const STANDARDS_TREE_FILE = path.join("specs", "规范总纲与树形结构.md");
const REGISTRY_FILE = path.join("mapping", "mapping_registry.json");
const DEFAULT_FRAMEWORK_TREE_HTML = path.join("docs", "hierarchy", "shelf_framework_tree.html");
const SIDEBAR_VIEW_ID = "archSync.sidebarHome";
const DEFAULT_FRAMEWORK_TREE_GENERATE_COMMAND =
  "uv run python scripts/generate_framework_tree_hierarchy.py --source framework --framework-dir framework --output-json docs/hierarchy/shelf_framework_tree.json --output-html docs/hierarchy/shelf_framework_tree.html";
const FRAMEWORK_RULE_HINTS = {
  FW002: "@framework 必须无参数",
  FW003: "标题必须为 中文名:EnglishName",
  FW010: "当前框架文件内编号必须唯一",
  FW011: "C/B/R/V 编号格式必须合法",
  FW020: "B* 必须包含来源",
  FW021: "B* 来源表达式与引用必须合法",
  FW022: "B* 来源必须包含 C* 与参数",
  FW023: "B* 禁止使用“上游模块：...”，必须内联写模块引用",
  FW024: "非 L0 的 B* 必须在主句中内联写相邻下层模块引用",
  FW025: "B* 的内联模块引用必须指向当前目录中真实存在的相邻下层模块文件",
  FW026: "L0 的 B* 不能再引用其他模块，必须保持自足",
  FW030: "边界参数必须包含来源",
  FW031: "边界来源必须引用 C* 且引用合法",
  FW040: "R*/R*.* 编号必须合法并可追溯",
  FW041: "每个 R* 必须包含参与基/组合方式/输出能力/边界绑定",
  FW050: "R*.输出能力必须引用已定义 C*",
  FW060: "新符号必须通过输出结构声明后才可在规则中使用"
};

function activate(context) {
  const output = vscode.window.createOutputChannel("ArchSync");
  const diagnostics = vscode.languages.createDiagnosticCollection("archsync-mapping");
  const status = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
  status.text = "$(check) ArchSync idle";
  status.tooltip = "ArchSync";
  status.command = "archSync.showIssues";
  status.backgroundColor = undefined;
  status.color = undefined;
  status.show();

  context.subscriptions.push(output, diagnostics, status);

  let running = false;
  let pending = null;
  let timer = null;
  let lastFailureSignature = "";
  let lastRunIssues = [];
  let lastRepoRoot = "";
  let mappingValidationActive = true;
  let frameworkTreePanel = null;
  let frameworkTreeRepoRoot = "";
  let frameworkSidebarView = null;
  const VALIDATION_SOURCE_PRIORITY = {
    auto: 1,
    save: 2,
    manual: 3
  };

  const normalizeValidationOptions = (options = {}) => ({
    mode: options.mode === "full" ? "full" : "change",
    triggerUri: options.triggerUri || null,
    notifyOnFail: Boolean(options.notifyOnFail),
    source: options.source || "auto"
  });

  const mergeValidationOptions = (left, right) => {
    const current = normalizeValidationOptions(left);
    const incoming = normalizeValidationOptions(right);
    const sourcePriority = Math.max(
      VALIDATION_SOURCE_PRIORITY[current.source] || 0,
      VALIDATION_SOURCE_PRIORITY[incoming.source] || 0
    );
    const source = Object.keys(VALIDATION_SOURCE_PRIORITY)
      .find((key) => VALIDATION_SOURCE_PRIORITY[key] === sourcePriority) || "auto";

    return {
      mode: current.mode === "full" || incoming.mode === "full" ? "full" : "change",
      triggerUri: incoming.triggerUri || current.triggerUri,
      notifyOnFail: current.notifyOnFail || incoming.notifyOnFail,
      source
    };
  };

  const runValidation = async (options = { mode: "change", triggerUri: null, notifyOnFail: false, source: "auto" }) => {
    const task = normalizeValidationOptions(options);
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      return;
    }
    const repoRoot = folder.uri.fsPath;

    if (!hasStandardsTree(repoRoot)) {
      mappingValidationActive = false;
      lastRepoRoot = repoRoot;
      lastRunIssues = [];
      lastFailureSignature = "";
      diagnostics.clear();
      setStatusDisabled(status, repoRoot);
      refreshSidebarHome();
      return;
    }
    mappingValidationActive = true;

    const config = vscode.workspace.getConfiguration("archSync");
    const command = task.mode === "full"
      ? config.get("fullValidationCommand")
      : config.get("changeValidationCommand");

    if (!command || typeof command !== "string") {
      return;
    }

    const showProgressStatus = task.source === "manual";
    const shouldSetErrorStatus = task.source === "save" || task.source === "manual";
    if (showProgressStatus) {
      status.text = "$(sync~spin) ArchSync validating";
      status.backgroundColor = new vscode.ThemeColor("statusBarItem.warningBackground");
      status.color = new vscode.ThemeColor("statusBarItem.warningForeground");
    }
    output.clear();
    output.appendLine(`[run] ${command}`);

    const execResult = await execCommand(command, repoRoot);
    output.appendLine(execResult.stdout || "");
    output.appendLine(execResult.stderr || "");

    const parsed = parseResult(execResult.stdout, execResult.stderr, execResult.code);
    lastRunIssues = parsed.errors;
    lastRepoRoot = repoRoot;
    applyDiagnostics(parsed, diagnostics, repoRoot, task.triggerUri);
    output.appendLine(`[result] passed=${parsed.passed} errors=${parsed.errors.length}`);

    if (parsed.passed) {
      status.text = "$(check) ArchSync OK";
      status.tooltip = "ArchSync: no mapping issues";
      status.backgroundColor = undefined;
      status.color = undefined;
      lastFailureSignature = "";
    } else {
      if (shouldSetErrorStatus) {
        status.text = "$(error) ArchSync issues";
        status.tooltip = buildTooltip(parsed.errors);
        status.backgroundColor = new vscode.ThemeColor("statusBarItem.errorBackground");
        status.color = new vscode.ThemeColor("statusBarItem.errorForeground");
      }

      const shouldNotify = task.notifyOnFail || config.get("notifyOnAutoFail");
      if (shouldNotify && shouldNotifyFailure(parsed.errors, lastFailureSignature)) {
        lastFailureSignature = signature(parsed.errors);
        const action = await vscode.window.showErrorMessage(
          `ArchSync mapping validation failed (${parsed.errors.length} issue(s)).`,
          "Open Problems",
          "Open Log"
        );
        if (action === "Open Problems") {
          await vscode.commands.executeCommand("workbench.actions.view.problems");
        } else if (action === "Open Log") {
          output.show(true);
        }
      }
    }
    refreshSidebarHome();
  };

  const scheduleValidation = (options) => {
    const normalized = normalizeValidationOptions(options);
    if (pending) {
      pending = mergeValidationOptions(pending, normalized);
    } else {
      pending = normalized;
    }

    if (timer) {
      clearTimeout(timer);
    }

    timer = setTimeout(async () => {
      if (running || !pending) {
        return;
      }
      running = true;
      const task = pending;
      pending = null;
      try {
        await runValidation(task);
      } finally {
        running = false;
        if (pending) {
          scheduleValidation(pending);
        }
      }
    }, 250);
  };

  const openFrameworkTreeSource = async (repoRoot, relFile, line) => {
    if (!repoRoot || !relFile || typeof relFile !== "string") {
      return;
    }

    const normalizedRel = relFile.replace(/\\/g, "/").replace(/^\/+/, "");
    const absPath = path.resolve(repoRoot, normalizedRel);
    if (!fs.existsSync(absPath)) {
      vscode.window.showWarningMessage(`ArchSync: source file not found: ${normalizedRel}`);
      return;
    }

    const lineNumber = Number.isFinite(Number(line)) ? Math.max(1, Number(line)) : 1;
    const doc = await vscode.workspace.openTextDocument(vscode.Uri.file(absPath));
    const editor = await vscode.window.showTextDocument(doc, { preview: false });
    const pos = new vscode.Position(lineNumber - 1, 0);
    editor.selection = new vscode.Selection(pos, pos);
    editor.revealRange(new vscode.Range(pos, pos), vscode.TextEditorRevealType.InCenter);
  };

  const ensureFrameworkTreePanel = () => {
    if (!frameworkTreePanel) {
      frameworkTreePanel = vscode.window.createWebviewPanel(
        "archSyncFrameworkTree",
        "ArchSync · Framework Tree",
        vscode.ViewColumn.Active,
        {
          enableScripts: true,
          retainContextWhenHidden: true
        }
      );
      frameworkTreePanel.onDidDispose(() => {
        frameworkTreePanel = null;
        frameworkTreeRepoRoot = "";
      });
      frameworkTreePanel.webview.onDidReceiveMessage(async (message) => {
        if (!message || message.type !== "archSync.openSource") {
          return;
        }
        await openFrameworkTreeSource(
          frameworkTreeRepoRoot || vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || "",
          String(message.file || ""),
          Number(message.line || 1)
        );
      });
    } else {
      frameworkTreePanel.reveal(vscode.ViewColumn.Active, true);
    }
    return frameworkTreePanel;
  };

  const openFrameworkTree = async (options = { regenerateIfMissing: false }) => {
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      vscode.window.showWarningMessage("ArchSync: no workspace is open.");
      return;
    }

    const repoRoot = folder.uri.fsPath;
    frameworkTreeRepoRoot = repoRoot;
    const config = vscode.workspace.getConfiguration("archSync");
    const htmlPath = resolveFrameworkTreeHtmlPath(repoRoot, config.get("frameworkTreeHtmlPath"));

    if (options.regenerateIfMissing && !fs.existsSync(htmlPath)) {
      const generateCommand = config.get("frameworkTreeGenerateCommand") || DEFAULT_FRAMEWORK_TREE_GENERATE_COMMAND;
      await generateFrameworkTree(repoRoot, String(generateCommand), output);
    }

    const panel = ensureFrameworkTreePanel();
    panel.webview.html = buildFrameworkTreeFallbackHtml(
      `Loading ${toWorkspaceRelative(htmlPath, repoRoot)} ...`
    );

    if (!fs.existsSync(htmlPath)) {
      panel.webview.html = buildFrameworkTreeFallbackHtml(
        `Framework tree HTML not found: ${toWorkspaceRelative(htmlPath, repoRoot)}`
      );
      return;
    }

    try {
      panel.webview.html = fs.readFileSync(htmlPath, "utf8");
    } catch (error) {
      panel.webview.html = buildFrameworkTreeFallbackHtml(
        `Failed to read framework tree HTML: ${String(error)}`
      );
    }
  };

  const renderSidebarHome = () => {
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      return buildSidebarHomeHtml({
        workspace: "No workspace",
        treePath: DEFAULT_FRAMEWORK_TREE_HTML,
        mappingStatus: "Unavailable",
        issueSummary: "No workspace",
      });
    }

    const repoRoot = folder.uri.fsPath;
    const config = vscode.workspace.getConfiguration("archSync");
    const treePath = resolveFrameworkTreeHtmlPath(repoRoot, config.get("frameworkTreeHtmlPath"));
    const issueSummary = mappingValidationActive
      ? (lastRunIssues.length ? `${lastRunIssues.length} issue(s)` : "No issues")
      : "Validation disabled";

    return buildSidebarHomeHtml({
      workspace: path.basename(repoRoot),
      treePath: toWorkspaceRelative(treePath, repoRoot),
      mappingStatus: mappingValidationActive ? "Enabled" : "Disabled",
      issueSummary,
    });
  };

  const refreshSidebarHome = () => {
    if (!frameworkSidebarView) {
      return;
    }
    frameworkSidebarView.webview.html = renderSidebarHome();
  };

  const sidebarViewProvider = {
    resolveWebviewView(webviewView) {
      frameworkSidebarView = webviewView;
      webviewView.webview.options = {
        enableScripts: true
      };
      refreshSidebarHome();

      webviewView.onDidDispose(() => {
        if (frameworkSidebarView === webviewView) {
          frameworkSidebarView = null;
        }
      });

      webviewView.webview.onDidReceiveMessage(async (message) => {
        if (!message || typeof message.type !== "string") {
          return;
        }

        if (message.type === "archSync.sidebar.openTree") {
          await openFrameworkTree({ regenerateIfMissing: true });
          return;
        }
        if (message.type === "archSync.sidebar.refreshTree") {
          await vscode.commands.executeCommand("archSync.refreshFrameworkTree");
          return;
        }
        if (message.type === "archSync.sidebar.validate") {
          scheduleValidation({ mode: "full", triggerUri: null, notifyOnFail: true, source: "manual" });
          return;
        }
        if (message.type === "archSync.sidebar.showIssues") {
          await vscode.commands.executeCommand("archSync.showIssues");
        }
      });
    }
  };

  const sidebarViewDisposable = vscode.window.registerWebviewViewProvider(
    SIDEBAR_VIEW_ID,
    sidebarViewProvider,
    {
      webviewOptions: {
        retainContextWhenHidden: true
      }
    }
  );

  const validateNowDisposable = vscode.commands.registerCommand("archSync.validateNow", async () => {
    scheduleValidation({ mode: "full", triggerUri: null, notifyOnFail: true, source: "manual" });
  });

  const showIssuesDisposable = vscode.commands.registerCommand("archSync.showIssues", async () => {
    if (!mappingValidationActive && lastRepoRoot) {
      vscode.window.showInformationMessage(
        `ArchSync mapping guard is disabled: missing ${STANDARDS_TREE_FILE} in this workspace.`
      );
      return;
    }

    if (!lastRunIssues.length) {
      await vscode.commands.executeCommand("workbench.actions.view.problems");
      return;
    }

    if (lastRunIssues.length === 1 && lastRepoRoot) {
      await revealIssue(lastRunIssues[0], lastRepoRoot);
      return;
    }

    const picks = lastRunIssues.map((issue) => {
      const resolved = resolveIssueFile(issue.file, lastRepoRoot);
      const displayPath = resolved ? toWorkspaceRelative(resolved, lastRepoRoot) : "unknown";
      const ruleCode = normalizeFrameworkRuleCode(issue.code);
      const ruleHint = frameworkRuleHint(ruleCode);
      return {
        label: issue.message,
        description: `${displayPath}:${Number(issue.line || 1)}`,
        detail: ruleCode ? `[${ruleCode}] ${ruleHint}` : (issue.code ? `[${issue.code}]` : ""),
        issue
      };
    });

    const selected = await vscode.window.showQuickPick(picks, {
      title: `ArchSync Mapping Issues (${lastRunIssues.length})`,
      placeHolder: "Select an issue to jump to its location"
    });

    if (selected && lastRepoRoot) {
      await revealIssue(selected.issue, lastRepoRoot);
    }
  });

  const openFrameworkTreeDisposable = vscode.commands.registerCommand("archSync.openFrameworkTree", async () => {
    await openFrameworkTree({ regenerateIfMissing: true });
  });

  const refreshFrameworkTreeDisposable = vscode.commands.registerCommand("archSync.refreshFrameworkTree", async () => {
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      vscode.window.showWarningMessage("ArchSync: no workspace is open.");
      return;
    }

    const repoRoot = folder.uri.fsPath;
    const config = vscode.workspace.getConfiguration("archSync");
    const generateCommand = String(
      config.get("frameworkTreeGenerateCommand") || DEFAULT_FRAMEWORK_TREE_GENERATE_COMMAND
    );

    const ok = await generateFrameworkTree(repoRoot, generateCommand, output);
    if (!ok) {
      await vscode.window.showErrorMessage("ArchSync: failed to refresh framework tree.", "Open Log").then((action) => {
        if (action === "Open Log") {
          output.show(true);
        }
      });
      return;
    }

    await openFrameworkTree({ regenerateIfMissing: false });
  });

  const saveDisposable = vscode.workspace.onDidSaveTextDocument(async (doc) => {
    const config = vscode.workspace.getConfiguration("archSync");
    if (!config.get("enableOnSave")) {
      return;
    }

    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      return;
    }

    const rel = path.relative(folder.uri.fsPath, doc.uri.fsPath).replace(/\\/g, "/");
    if (!isWatchedPath(rel)) {
      return;
    }

    scheduleValidation({ mode: "change", triggerUri: doc.uri, notifyOnFail: false, source: "save" });
  });

  const createDisposable = vscode.workspace.onDidCreateFiles(async (event) => {
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      return;
    }
    if (anyWatchedUris(event.files, folder.uri.fsPath)) {
      scheduleValidation({ mode: "change", triggerUri: null, notifyOnFail: false, source: "auto" });
    }
  });

  const deleteDisposable = vscode.workspace.onDidDeleteFiles(async (event) => {
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      return;
    }
    if (anyWatchedUris(event.files, folder.uri.fsPath)) {
      scheduleValidation({ mode: "change", triggerUri: null, notifyOnFail: false, source: "auto" });
    }
  });

  const renameDisposable = vscode.workspace.onDidRenameFiles(async (event) => {
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      return;
    }
    const uris = [];
    for (const item of event.files) {
      uris.push(item.oldUri, item.newUri);
    }
    if (anyWatchedUris(uris, folder.uri.fsPath)) {
      scheduleValidation({ mode: "change", triggerUri: null, notifyOnFail: false, source: "auto" });
    }
  });

  const focusDisposable = vscode.window.onDidChangeWindowState(async (state) => {
    if (!state.focused) {
      return;
    }
    scheduleValidation({ mode: "change", triggerUri: null, notifyOnFail: false, source: "auto" });
  });

  const fileWatcherDisposables = [];
  const watcherFolder = vscode.workspace.workspaceFolders?.[0];
  if (watcherFolder) {
    const watcherPatterns = [
      "framework/**",
      "specs/**",
      "mapping/**",
      "src/**",
      "docs/**",
      "AGENTS.md",
      "README.md",
      "scripts/validate_strict_mapping.py",
      "scripts/generate_framework_tree_hierarchy.py"
    ];

    for (const pattern of watcherPatterns) {
      const watcher = vscode.workspace.createFileSystemWatcher(
        new vscode.RelativePattern(watcherFolder, pattern)
      );

      const triggerIfWatched = (uri) => {
        if (isWatchedUri(uri, watcherFolder.uri.fsPath)) {
          scheduleValidation({ mode: "change", triggerUri: uri, notifyOnFail: false, source: "auto" });
        }
      };

      watcher.onDidChange(triggerIfWatched);
      watcher.onDidCreate(triggerIfWatched);
      watcher.onDidDelete(triggerIfWatched);
      fileWatcherDisposables.push(watcher);
    }
  }

  context.subscriptions.push(
    sidebarViewDisposable,
    validateNowDisposable,
    showIssuesDisposable,
    openFrameworkTreeDisposable,
    refreshFrameworkTreeDisposable,
    saveDisposable,
    createDisposable,
    deleteDisposable,
    renameDisposable,
    focusDisposable,
    ...fileWatcherDisposables
  );

  scheduleValidation({ mode: "change", triggerUri: null, notifyOnFail: false, source: "auto" });
}

function deactivate() {}

function isWatchedPath(relPath) {
  if (!relPath || relPath.startsWith("..")) {
    return false;
  }

  if (WATCH_FILES.has(relPath)) {
    return true;
  }

  return WATCH_PREFIXES.some((prefix) => relPath.startsWith(prefix));
}

function anyWatchedUris(uris, workspaceRoot) {
  for (const uri of uris) {
    if (isWatchedUri(uri, workspaceRoot)) {
      return true;
    }
  }
  return false;
}

function isWatchedUri(uri, workspaceRoot) {
  const rel = path.relative(workspaceRoot, uri.fsPath).replace(/\\/g, "/");
  return isWatchedPath(rel);
}

function execCommand(command, cwd) {
  return new Promise((resolve) => {
    cp.exec(command, { cwd, maxBuffer: 1024 * 1024 }, (error, stdout, stderr) => {
      resolve({
        code: error ? error.code ?? 1 : 0,
        stdout: stdout || "",
        stderr: stderr || ""
      });
    });
  });
}

async function generateFrameworkTree(repoRoot, command, output) {
  output.appendLine(`[framework-tree] ${command}`);
  const result = await execCommand(command, repoRoot);
  output.appendLine(result.stdout || "");
  output.appendLine(result.stderr || "");
  output.appendLine(`[framework-tree] exit=${result.code}`);
  return result.code === 0;
}

function parseResult(stdout, stderr, code) {
  const text = [stdout, stderr].filter(Boolean).join("\n").trim();

  try {
    const data = JSON.parse(stdout || stderr || "{}");
    if (typeof data.passed === "boolean" && Array.isArray(data.errors)) {
      return {
        passed: data.passed,
        errors: data.errors.map(normalizeIssue)
      };
    }
  } catch (_) {
    // Fallback to text parsing below.
  }

  const errors = [];
  for (const line of text.split("\n")) {
    const trimmed = line.trim();
    if (trimmed.startsWith("- ")) {
      errors.push(normalizeIssue(trimmed.slice(2)));
    }
  }

  if (!errors.length && code !== 0 && text) {
    errors.push(normalizeIssue(text));
  }

  return {
    passed: code === 0 && errors.length === 0,
    errors
  };
}

function applyDiagnostics(parsed, collection, repoRoot, triggerUri) {
  collection.clear();
  if (parsed.passed) {
    return;
  }

  const grouped = new Map();

  for (const issue of parsed.errors) {
    const candidateTarget = resolveIssueFile(issue.file, repoRoot);
    const target = (candidateTarget && fs.existsSync(candidateTarget))
      ? candidateTarget
      : (triggerUri
        ? triggerUri.fsPath
        : path.join(repoRoot, REGISTRY_FILE));

    if (!grouped.has(target)) {
      grouped.set(target, []);
    }

    const startLine = Math.max(0, Number(issue.line || 1) - 1);
    const startCol = Math.max(0, Number(issue.column || 1) - 1);
    const range = new vscode.Range(startLine, startCol, startLine, startCol + 1);
    const ruleCode = normalizeFrameworkRuleCode(issue.code);
    const ruleHint = frameworkRuleHint(ruleCode);
    const message = ruleCode
      ? `[archsync ${ruleCode}] ${ruleHint} | ${issue.message}`
      : `[archsync] ${issue.message}`;
    const diag = new vscode.Diagnostic(
      range,
      message,
      vscode.DiagnosticSeverity.Error
    );

    if (ruleCode) {
      diag.code = ruleCode;
    } else if (issue.code) {
      diag.code = issue.code;
    }

    if (Array.isArray(issue.related) && issue.related.length) {
      const relatedInfo = [];
      for (const rel of issue.related) {
        const relFile = resolveIssueFile(rel.file, repoRoot);
        if (!relFile) {
          continue;
        }
        const relLine = Math.max(0, Number(rel.line || 1) - 1);
        const relCol = Math.max(0, Number(rel.column || 1) - 1);
        const relRange = new vscode.Range(relLine, relCol, relLine, relCol + 1);
        const relMessage = rel.message || "Related location";
        relatedInfo.push(
          new vscode.DiagnosticRelatedInformation(
            new vscode.Location(vscode.Uri.file(relFile), relRange),
            relMessage
          )
        );
      }
      if (relatedInfo.length) {
        diag.relatedInformation = relatedInfo;
      }
    }

    grouped.get(target).push(diag);
  }

  for (const [filePath, diagnostics] of grouped.entries()) {
    collection.set(vscode.Uri.file(filePath), diagnostics);
  }
}

function resolveIssueFile(file, repoRoot) {
  if (!file || typeof file !== "string") {
    return null;
  }
  if (path.isAbsolute(file)) {
    return file;
  }
  return path.join(repoRoot, file);
}

function resolveFrameworkTreeHtmlPath(repoRoot, configuredPath) {
  if (typeof configuredPath !== "string" || !configuredPath.trim()) {
    return path.join(repoRoot, DEFAULT_FRAMEWORK_TREE_HTML);
  }
  if (path.isAbsolute(configuredPath)) {
    return configuredPath;
  }
  return path.join(repoRoot, configuredPath);
}

function toWorkspaceRelative(filePath, repoRoot) {
  const rel = path.relative(repoRoot, filePath).replace(/\\/g, "/");
  return rel.startsWith("..") ? filePath : rel;
}

function buildFrameworkTreeFallbackHtml(message) {
  const escaped = String(message)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");

  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>ArchSync · Framework Tree</title>
  <style>
    body { font-family: sans-serif; margin: 0; padding: 20px; color: #183249; background: #f2f7fb; }
    .card { max-width: 900px; margin: 0 auto; background: #fff; border: 1px solid #d6e2ec; border-radius: 12px; padding: 18px; }
    h1 { margin: 0 0 10px; font-size: 22px; }
    p { margin: 0; line-height: 1.6; }
    code { background: #edf5fb; padding: 2px 6px; border-radius: 6px; }
  </style>
</head>
<body>
  <div class="card">
    <h1>ArchSync · Framework Tree</h1>
    <p>${escaped}</p>
    <p style="margin-top:10px;">Try command <code>ArchSync: Refresh Framework Tree</code>.</p>
  </div>
</body>
</html>`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function buildSidebarHomeHtml(model) {
  const workspace = escapeHtml(model.workspace);
  const treePath = escapeHtml(model.treePath);
  const mappingStatus = escapeHtml(model.mappingStatus);
  const issueSummary = escapeHtml(model.issueSummary);

  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    :root {
      --bg: #f3f7fb;
      --panel: #ffffff;
      --text: #1f3246;
      --muted: #4f6479;
      --line: #d7e3ee;
      --primary: #0b74de;
      --primary-hover: #095fb3;
      --ghost: #edf4fb;
      --ghost-hover: #e2edf8;
    }

    body {
      margin: 0;
      padding: 12px;
      background: linear-gradient(180deg, #f7fbff 0%, var(--bg) 100%);
      color: var(--text);
      font-family: "Noto Sans SC", "PingFang SC", sans-serif;
    }

    .card {
      border: 1px solid var(--line);
      border-radius: 12px;
      background: var(--panel);
      padding: 12px;
      box-shadow: 0 6px 16px rgba(22, 47, 74, 0.08);
    }

    .title {
      margin: 0 0 6px;
      font-size: 16px;
      font-weight: 700;
    }

    .meta {
      margin: 0;
      font-size: 12px;
      color: var(--muted);
      line-height: 1.55;
      word-break: break-all;
    }

    .meta + .meta {
      margin-top: 4px;
    }

    .actions {
      margin-top: 12px;
      display: grid;
      gap: 8px;
    }

    button {
      border: 0;
      border-radius: 9px;
      padding: 8px 10px;
      text-align: left;
      font-size: 12px;
      cursor: pointer;
      transition: background 120ms ease;
    }

    button.primary {
      color: #ffffff;
      background: var(--primary);
    }

    button.primary:hover {
      background: var(--primary-hover);
    }

    button.ghost {
      color: #234563;
      background: var(--ghost);
    }

    button.ghost:hover {
      background: var(--ghost-hover);
    }
  </style>
</head>
<body>
  <div class="card">
    <h1 class="title">ArchSync</h1>
    <p class="meta">Workspace: ${workspace}</p>
    <p class="meta">Framework tree: ${treePath}</p>
    <p class="meta">Mapping validation: ${mappingStatus}</p>
    <p class="meta">Issues: ${issueSummary}</p>

    <div class="actions">
      <button class="primary" data-action="openTree">打开树图</button>
      <button class="ghost" data-action="refreshTree">刷新树图</button>
      <button class="ghost" data-action="validate">执行校验</button>
      <button class="ghost" data-action="showIssues">查看问题</button>
    </div>
  </div>

  <script>
    const vscode = typeof acquireVsCodeApi === "function" ? acquireVsCodeApi() : null;
    for (const button of document.querySelectorAll("button[data-action]")) {
      button.addEventListener("click", () => {
        if (!vscode) return;
        const action = button.getAttribute("data-action");
        if (!action) return;
        vscode.postMessage({ type: "archSync.sidebar." + action });
      });
    }
  </script>
</body>
</html>`;
}

async function revealIssue(issue, repoRoot) {
  const candidate = resolveIssueFile(issue.file, repoRoot);
  const target = (candidate && fs.existsSync(candidate))
    ? candidate
    : path.join(repoRoot, REGISTRY_FILE);
  const uri = vscode.Uri.file(target);
  const doc = await vscode.workspace.openTextDocument(uri);
  const line = Math.max(0, Number(issue.line || 1) - 1);
  const col = Math.max(0, Number(issue.column || 1) - 1);
  const safeLine = Math.min(line, Math.max(doc.lineCount - 1, 0));
  const lineText = doc.lineAt(safeLine).text;
  const safeCol = Math.min(col, lineText.length);
  const pos = new vscode.Position(safeLine, safeCol);
  const editor = await vscode.window.showTextDocument(doc, { preview: false });
  editor.selection = new vscode.Selection(pos, pos);
  editor.revealRange(new vscode.Range(pos, pos), vscode.TextEditorRevealType.InCenter);
}

function normalizeIssue(item) {
  if (typeof item === "string") {
    return {
      message: item,
      file: null,
      line: 1,
      column: 1,
      code: "ARCHSYNC_MAPPING",
      related: []
    };
  }

  if (!item || typeof item !== "object") {
    return {
      message: String(item),
      file: null,
      line: 1,
      column: 1,
      code: "ARCHSYNC_MAPPING",
      related: []
    };
  }

  return {
    message: String(item.message || "ArchSync mapping issue"),
    file: item.file || null,
    line: Number(item.line || 1),
    column: Number(item.column || 1),
    code: item.code || "ARCHSYNC_MAPPING",
    related: Array.isArray(item.related) ? item.related : []
  };
}

function normalizeFrameworkRuleCode(rawCode) {
  const code = String(rawCode || "").trim();
  if (!code) {
    return "";
  }
  if (Object.prototype.hasOwnProperty.call(FRAMEWORK_RULE_HINTS, code)) {
    return code;
  }
  return "";
}

function frameworkRuleHint(ruleCode) {
  if (!ruleCode) {
    return "ArchSync 规则";
  }
  return FRAMEWORK_RULE_HINTS[ruleCode] || "ArchSync 规则";
}

function signature(errors) {
  return [...errors]
    .map((e) => `${e.file || ""}:${e.line || 1}:${e.message}`)
    .sort()
    .join("||");
}

function shouldNotifyFailure(errors, prevSignature) {
  return signature(errors) !== prevSignature;
}

function buildTooltip(errors) {
  if (!errors.length) {
    return "ArchSync";
  }
  const preview = errors.slice(0, 3).map((e) => `• ${e.message}`).join("\n");
  const more = errors.length > 3 ? `\n... +${errors.length - 3} more` : "";
  return `ArchSync\n${preview}${more}\n(click to open Problems)`;
}

function hasStandardsTree(repoRoot) {
  return fs.existsSync(path.join(repoRoot, STANDARDS_TREE_FILE));
}

function setStatusDisabled(status, repoRoot) {
  status.text = "$(circle-slash) ArchSync";
  status.tooltip = `ArchSync mapping guard disabled: ${toWorkspaceRelative(
    path.join(repoRoot, STANDARDS_TREE_FILE),
    repoRoot
  )} not found`;
  status.backgroundColor = undefined;
  status.color = undefined;
}

module.exports = {
  activate,
  deactivate
};
