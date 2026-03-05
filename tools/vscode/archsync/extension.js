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
const DEFAULT_FRAMEWORK_TREE_GENERATE_COMMAND =
  "uv run python scripts/generate_framework_tree_hierarchy.py --source framework --framework-dir framework --output-json docs/hierarchy/shelf_framework_tree.json --output-html docs/hierarchy/shelf_framework_tree.html";
const MODULE_ID_PATTERN = /^[A-Za-z0-9_-]+$/;
const LEVEL_PATTERN = /^L\d+$/i;
const FRAMEWORK_DIRECTIVE_PREFIX = "@framework";
const FRAMEWORK_RULE_HINTS = {
  FW002: "@framework 必须无参数",
  FW003: "标题必须为 中文名:EnglishName",
  FW010: "当前框架文件内编号必须唯一",
  FW011: "C/B/R/V 编号格式必须合法",
  FW020: "B* 必须包含来源",
  FW021: "B* 来源表达式与引用必须合法",
  FW022: "B* 来源必须包含 C* 与参数",
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

  const generateFrameworkScaffoldDisposable = vscode.commands.registerCommand("archSync.generateFrameworkScaffold", async () => {
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      vscode.window.showWarningMessage("ArchSync: no workspace is open.");
      return;
    }

    const repoRoot = folder.uri.fsPath;
    const editor = vscode.window.activeTextEditor;
    const inferred = inferFrameworkDefaults(editor?.document.uri.fsPath, repoRoot);

    const moduleId = await promptScaffoldValue({
      title: "ArchSync: module id",
      prompt: "Canonical module id used in node ids (Lx.Mmodule.By)",
      value: inferred.module,
      validateInput: (value) => (MODULE_ID_PATTERN.test(value.trim()) ? null : "Use [A-Za-z0-9_-], e.g. frontend")
    });
    if (!moduleId) {
      return;
    }

    const level = await promptScaffoldValue({
      title: "ArchSync: level",
      prompt: "Layer level, e.g. L4",
      value: inferred.level,
      validateInput: (value) => (LEVEL_PATTERN.test(value.trim()) ? null : "Use L<number>, e.g. L4")
    });
    if (!level) {
      return;
    }

    const title = await promptScaffoldValue({
      title: "ArchSync: layer title",
      prompt: "Markdown file title stem (Chinese or bilingual title)",
      value: inferred.title,
      validateInput: (value) => validateScaffoldTitle(value)
    });
    if (!title) {
      return;
    }

    const targetOptions = [
      {
        label: "Write current file",
        description: "Overwrite active markdown file",
        value: "current"
      },
      {
        label: "Write default path",
        description: "framework/<module>/<level>-<title>.md",
        value: "default"
      }
    ];
    const targetPick = await vscode.window.showQuickPick(targetOptions, {
      title: "ArchSync: scaffold output",
      placeHolder: "Choose where to write scaffold"
    });
    if (!targetPick) {
      return;
    }

    if (targetPick.value === "current" && !editor) {
      vscode.window.showWarningMessage("ArchSync: no active editor for current-file output.");
      return;
    }

    const normalizedModule = moduleId.trim();
    const normalizedLevel = level.trim().toUpperCase();
    const bilingualTitle = ensureBilingualTitle(title.trim(), normalizedModule, moduleDisplayName(normalizedModule));
    const scaffold = buildFrameworkTemplate(bilingualTitle);

    let outputFilePath = null;
    if (targetPick.value === "current" && editor) {
      outputFilePath = editor.document.uri.fsPath;
      const doc = editor.document;
      const fullRange = new vscode.Range(
        doc.positionAt(0),
        doc.positionAt(doc.getText().length)
      );
      const edit = new vscode.WorkspaceEdit();
      edit.replace(doc.uri, fullRange, scaffold);
      await vscode.workspace.applyEdit(edit);
    } else {
      const defaultPath = path.join(
        repoRoot,
        "framework",
        normalizedModule,
        `${normalizedLevel}-${title.trim()}.md`
      );
      fs.mkdirSync(path.dirname(defaultPath), { recursive: true });
      if (fs.existsSync(defaultPath)) {
        const action = await vscode.window.showWarningMessage(
          `ArchSync: ${toWorkspaceRelative(defaultPath, repoRoot)} already exists.`,
          "Overwrite",
          "Cancel"
        );
        if (action !== "Overwrite") {
          return;
        }
      }
      fs.writeFileSync(defaultPath, scaffold, "utf8");
      outputFilePath = defaultPath;
    }

    if (outputFilePath) {
      try {
        const uri = vscode.Uri.file(outputFilePath);
        const doc = await vscode.workspace.openTextDocument(uri);
        await vscode.window.showTextDocument(doc, { preview: false });
      } catch (error) {
        output.appendLine(`[framework-scaffold] open file failed: ${String(error)}`);
      }
    }

    vscode.window.showInformationMessage("ArchSync: framework scaffold generated.");
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

  const willSaveDisposable = vscode.workspace.onWillSaveTextDocument((event) => {
    const config = vscode.workspace.getConfiguration("archSync");
    if (!config.get("autoExpandFrameworkDirective")) {
      return;
    }

    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      return;
    }

    const doc = event.document;
    if (doc.languageId !== "markdown") {
      return;
    }

    const relPath = path.relative(folder.uri.fsPath, doc.uri.fsPath).replace(/\\/g, "/");
    if (!relPath.startsWith("framework/")) {
      return;
    }

    const directive = parseFrameworkDirective(doc.getText());
    if (!directive) {
      return;
    }

    event.waitUntil((async () => {
      const defaults = inferFrameworkDefaults(doc.uri.fsPath, folder.uri.fsPath);
      if (directive.error) {
        vscode.window.showErrorMessage(`ArchSync: ${directive.error}`);
        return [];
      }

      const title = ensureBilingualTitle(defaults.title, defaults.module, defaults.moduleDisplay);
      const generated = buildFrameworkTemplate(title);

      const fullRange = new vscode.Range(
        doc.positionAt(0),
        doc.positionAt(doc.getText().length)
      );
      return [vscode.TextEdit.replace(fullRange, generated)];
    })());
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
    validateNowDisposable,
    showIssuesDisposable,
    openFrameworkTreeDisposable,
    refreshFrameworkTreeDisposable,
    generateFrameworkScaffoldDisposable,
    willSaveDisposable,
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

async function promptScaffoldValue(options) {
  const value = await vscode.window.showInputBox({
    title: options.title,
    prompt: options.prompt,
    value: options.value || "",
    validateInput: options.validateInput
      ? (raw) => {
        const result = options.validateInput(raw);
        return result || undefined;
      }
      : undefined,
    ignoreFocusOut: true
  });

  if (value === undefined) {
    return null;
  }
  const cleaned = value.trim();
  return cleaned || null;
}

function validateScaffoldTitle(value) {
  const trimmed = value.trim();
  if (!trimmed) {
    return "Title cannot be empty.";
  }
  if (trimmed.includes("/") || trimmed.includes("\\")) {
    return "Title cannot contain path separators.";
  }
  return null;
}

function inferFrameworkDefaults(activeFilePath, repoRoot) {
  const defaults = {
    module: "frontend",
    moduleDisplay: "前端",
    level: "L4",
    title: "状态与数据编排层"
  };

  if (!activeFilePath) {
    return defaults;
  }

  const relPath = path.relative(repoRoot, activeFilePath).replace(/\\/g, "/");
  const match = /^framework\/([^/]+)\/(L\d+)-([^/]+)\.md$/i.exec(relPath);
  if (!match) {
    return defaults;
  }

  const moduleName = match[1];
  return {
    module: moduleName,
    moduleDisplay: moduleDisplayName(moduleName),
    level: match[2].toUpperCase(),
    title: match[3]
  };
}

function moduleDisplayName(moduleName) {
  const lower = String(moduleName || "").toLowerCase();
  if (lower === "frontend") {
    return "前端";
  }
  if (lower === "shelf") {
    return "置物架";
  }
  if (lower === "curtain") {
    return "窗帘";
  }
  return moduleName;
}

function parseFrameworkDirective(documentText) {
  const lines = String(documentText || "").split(/\r?\n/);
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed.startsWith(FRAMEWORK_DIRECTIVE_PREFIX)) {
      continue;
    }

    if (trimmed !== FRAMEWORK_DIRECTIVE_PREFIX) {
      return {
        error: "@framework must be plain directive without parameters."
      };
    }

    return { error: null };
  }

  return null;
}

function toPascalIdentifier(raw) {
  const parts = String(raw || "")
    .split(/[^A-Za-z0-9]+/)
    .filter(Boolean);
  if (!parts.length) {
    return "ModuleName";
  }
  return parts.map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join("");
}

function ensureBilingualTitle(rawTitle, moduleId, moduleDisplay) {
  const cleaned = String(rawTitle || "").trim().replace("：", ":");
  if (cleaned.includes(":")) {
    const parts = cleaned.split(":");
    const left = String(parts[0] || "").trim();
    const right = String(parts.slice(1).join(":") || "").trim();
    if (left && right) {
      return `${left}:${right}`;
    }
  }
  const zhName = cleaned || `${moduleDisplay}模块`;
  return `${zhName}:${toPascalIdentifier(moduleId)}`;
}

function buildFrameworkTemplate(bilingualTitle) {
  return `# ${bilingualTitle}

@framework

## 1. 能力声明（Capability Statement）

- \`C1\` 结构承载能力：提供可重复组装的承载结构能力。
- \`C2\` 形态生成能力：可生成目标形态并提供可用承载单元。
- \`C3\` 适配能力：在给定参数边界内可按需扩展和收缩。
- \`C4\` 非能力项：不负责电控、装饰、非承载功能件等外部职责。

## 2. 边界定义（Boundary / 参数）

- \`N\` 层数（int）：\`N >= 1\`。来源：\`C1 + C3\`。
- \`P\` 单层承重（number）：\`P > 0\`。来源：\`C1\`。
- \`S\` 单层净空（space）：宽/深/高均大于 0。来源：\`C2 + C3\`。
- \`O\` 开口尺寸（opening）：需满足可存取约束。来源：\`C2\`。
- \`A\` 占地尺寸（footprint）：需满足场地上限约束。来源：\`C2 + C3\`。
- \`T\` 连接公差（tolerance）：需满足装配稳定约束。来源：\`C1 + C3\`。
- \`SF\` 安全系数（number）：\`SF >= 1\`。来源：\`C1\`。

## 3. 最小可行基（Minimum Viable Bases）

- \`B1\` 骨架：提供主承载路径与结构稳定性。来源：\`C1 + N + P + SF\`。
- \`B2\` 连接接口：提供构件连接、定位与传力。来源：\`C1 + C3 + T\`。
- \`B3\` 承载面：提供可用放置/受力平面。来源：\`C2 + S + O + A + T\`。

## 4. 基组合原则（Base Combination Principles）

- \`R1\` 结构通路组合
  - \`R1.1\` 参与基：\`B1 + B2\`。
  - \`R1.2\` 组合方式：骨架由立向与横向构件组成；稳定单元定义为骨架连接图中存在至少一个闭合环（cycle）。
  - \`R1.3\` 输出结构：\`CP_set\`（元素：\`CP\`，每个 \`CP\` 必须绑定骨架端点或骨架交点）。
  - \`R1.4\` 输出能力：\`C1\`。
  - \`R1.5\` 边界绑定：\`N/P/T/SF\`。
- \`R2\` 承载单元组合
  - \`R2.1\` 参与基：\`B1 + B2 + B3\`。
  - \`R2.2\` 组合方式：承载面连接点必须来自 \`CP_set\`，且连接关系满足稳定受力路径约束。
  - \`R2.3\` 输出能力：\`C2\`。
  - \`R2.4\` 边界绑定：\`S/O/A/T\`。
- \`R3\` 完整功能组合
  - \`R3.1\` 参与基：\`B1 + B2 + B3\`。
  - \`R3.2\` 组合方式：先完成 \`R1\` 骨架与连接点，再执行 \`R2\` 承载面挂接，最后执行整体稳定复核。
  - \`R3.3\` 输出能力：\`C1 + C2 + C3\`。
  - \`R3.4\` 边界绑定：\`N/P/S/O/A/T/SF\`。
- \`R4\` 禁止组合
  - \`R4.1\` 参与基：\`B1 + B2 + B3\`。
  - \`R4.2\` 组合方式：缺少关键基、存在游离连接点、断裂传力路径或违反边界参数的组合均无效。
  - \`R4.3\` 输出能力：\`C4\`。
  - \`R4.4\` 边界绑定：\`N/P/S/O/A/T/SF\`。

## 5. 验证（Verification）

- \`V1\` 推导一致性：每个 \`B*\` 必须能由至少一个 \`C*\` 与一个参数项推导得到。
- \`V2\` 规则一致性：每个 \`R*\` 必须明确参与基/组合方式/输出能力/边界绑定。
- \`V3\` 目标覆盖性：\`R1~R3\` 输出能力并集必须覆盖 \`C1~C3\`。
- \`V4\` 边界符合性：所有有效组合必须满足绑定的参数边界。
- \`V5\` 最小必要性：移除任一 \`B*\` 后，\`V3\` 或 \`V4\` 至少一项失败。
- \`V6\` 结论表达：逐条输出 \`R* -> C* / 参数边界\` 的通过或失败结论。
`;
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
  status.text = "$(circle-slash) ArchSync n/a";
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
