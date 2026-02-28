const cp = require("child_process");
const fs = require("fs");
const path = require("path");
const vscode = require("vscode");

const WATCH_PREFIXES = ["standards/", "src/", "docs/"];
const WATCH_FILES = new Set([
  "AGENTS.md",
  "README.md",
  "scripts/validate_strict_mapping.py"
]);
const DEFAULT_REGISTRY_PATHS = [
  "standards/L3/mapping_registry.json",
  "standards/mapping_registry.json"
];
const DEFAULT_VALIDATOR_PATHS = ["scripts/validate_strict_mapping.py"];
const DEFAULT_IGNORE_PATH_PREFIXES = [
  ".git/",
  ".github/",
  ".venv/",
  "node_modules/",
  ".idea/",
  ".vscode/",
  "dist/",
  "build/",
  "coverage/",
  "__pycache__/"
];

function activate(context) {
  const output = vscode.window.createOutputChannel("Strict Mapping Guard");
  const diagnostics = vscode.languages.createDiagnosticCollection("strict-mapping");
  const status = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
  status.text = "$(check) Mapping idle";
  status.tooltip = "Strict Mapping Guard";
  status.command = "strictMapping.showIssues";
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
  let lastFallbackTarget = null;

  const applyUnsupportedState = (reason, repoRoot) => {
    lastRunIssues = [];
    diagnostics.clear();
    status.text = "$(info) Mapping N/A";
    status.tooltip = `Strict Mapping Guard: ${reason}`;
    status.backgroundColor = undefined;
    status.color = undefined;
    lastFallbackTarget = getDefaultFallbackTarget(repoRoot);
  };

  const runValidation = async (options = { mode: "change", triggerUri: null, notifyOnFail: false }) => {
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      return;
    }

    const config = vscode.workspace.getConfiguration("strictMappingGuard");
    const repoRoot = folder.uri.fsPath;
    lastRepoRoot = repoRoot;

    const support = detectRepositorySupport(repoRoot, config);
    lastFallbackTarget = support.fallbackTarget;
    if (!support.enabled) {
      applyUnsupportedState(support.reason, repoRoot);
      return;
    }

    const command = options.mode === "full"
      ? config.get("fullValidationCommand")
      : config.get("changeValidationCommand");

    if (!command || typeof command !== "string") {
      applyUnsupportedState("validation command is not configured", repoRoot);
      return;
    }

    status.text = "$(sync~spin) Mapping validating";
    status.backgroundColor = new vscode.ThemeColor("statusBarItem.warningBackground");
    status.color = new vscode.ThemeColor("statusBarItem.warningForeground");
    output.clear();
    output.appendLine(`[run] ${command}`);

    const execResult = await execCommand(command, repoRoot);
    output.appendLine(execResult.stdout || "");
    output.appendLine(execResult.stderr || "");

    const parsed = parseResult(execResult.stdout, execResult.stderr, execResult.code);
    lastRunIssues = parsed.errors;
    applyDiagnostics(parsed, diagnostics, repoRoot, options.triggerUri, lastFallbackTarget);
    output.appendLine(`[result] passed=${parsed.passed} errors=${parsed.errors.length}`);

    if (parsed.passed) {
      status.text = "$(check) Mapping OK";
      status.tooltip = "Strict Mapping Guard: no issues";
      status.backgroundColor = undefined;
      status.color = undefined;
      lastFailureSignature = "";
    } else {
      status.text = "$(error) Mapping issues";
      status.tooltip = buildTooltip(parsed.errors);
      status.backgroundColor = new vscode.ThemeColor("statusBarItem.errorBackground");
      status.color = new vscode.ThemeColor("statusBarItem.errorForeground");
      const config = vscode.workspace.getConfiguration("strictMappingGuard");
      const shouldNotify = options.notifyOnFail || config.get("notifyOnAutoFail");

      if (shouldNotify && shouldNotifyFailure(parsed.errors, lastFailureSignature)) {
        lastFailureSignature = signature(parsed.errors);
        const action = await vscode.window.showErrorMessage(
          `Strict mapping validation failed (${parsed.errors.length} issue(s)).`,
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
    if (pending) {
      pending = {
        mode: pending.mode === "full" || options.mode === "full" ? "full" : "change",
        triggerUri: options.triggerUri || pending.triggerUri,
        notifyOnFail: pending.notifyOnFail || options.notifyOnFail
      };
    } else {
      pending = options;
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

  const commandDisposable = vscode.commands.registerCommand("strictMapping.validateNow", async () => {
    scheduleValidation({ mode: "full", triggerUri: null, notifyOnFail: true });
  });
  const showIssuesDisposable = vscode.commands.registerCommand("strictMapping.showIssues", async () => {
    if (!lastRunIssues.length) {
      await vscode.commands.executeCommand("workbench.actions.view.problems");
      return;
    }

    if (lastRunIssues.length === 1 && lastRepoRoot) {
      await revealIssue(lastRunIssues[0], lastRepoRoot, lastFallbackTarget);
      return;
    }

    const picks = lastRunIssues.map((issue) => {
      const resolved = resolveIssueFile(issue.file, lastRepoRoot);
      const displayPath = resolved ? toWorkspaceRelative(resolved, lastRepoRoot) : "unknown";
      return {
        label: issue.message,
        description: `${displayPath}:${Number(issue.line || 1)}`,
        detail: issue.code ? `[${issue.code}]` : "",
        issue
      };
    });

    const selected = await vscode.window.showQuickPick(picks, {
      title: `Strict Mapping Issues (${lastRunIssues.length})`,
      placeHolder: "Select an issue to jump to its location"
    });

    if (selected && lastRepoRoot) {
      await revealIssue(selected.issue, lastRepoRoot, lastFallbackTarget);
    }
  });

  const saveDisposable = vscode.workspace.onDidSaveTextDocument(async (doc) => {
    const config = vscode.workspace.getConfiguration("strictMappingGuard");
    if (!config.get("enableOnSave")) {
      return;
    }

    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      return;
    }

    const rel = path.relative(folder.uri.fsPath, doc.uri.fsPath).replace(/\\/g, "/");
    if (!isWatchedPath(rel, config)) {
      return;
    }

    scheduleValidation({ mode: "change", triggerUri: doc.uri, notifyOnFail: false });
  });

  const createDisposable = vscode.workspace.onDidCreateFiles(async (event) => {
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      return;
    }
    const config = vscode.workspace.getConfiguration("strictMappingGuard");
    if (anyWatchedUris(event.files, folder.uri.fsPath, config)) {
      scheduleValidation({ mode: "change", triggerUri: null, notifyOnFail: false });
    }
  });

  const deleteDisposable = vscode.workspace.onDidDeleteFiles(async (event) => {
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      return;
    }
    const config = vscode.workspace.getConfiguration("strictMappingGuard");
    if (anyWatchedUris(event.files, folder.uri.fsPath, config)) {
      scheduleValidation({ mode: "change", triggerUri: null, notifyOnFail: false });
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
    const config = vscode.workspace.getConfiguration("strictMappingGuard");
    if (anyWatchedUris(uris, folder.uri.fsPath, config)) {
      scheduleValidation({ mode: "change", triggerUri: null, notifyOnFail: false });
    }
  });

  const focusDisposable = vscode.window.onDidChangeWindowState(async (state) => {
    if (!state.focused) {
      return;
    }
    scheduleValidation({ mode: "change", triggerUri: null, notifyOnFail: false });
  });

  const fileWatcherDisposables = [];
  const watcherFolder = vscode.workspace.workspaceFolders?.[0];
  if (watcherFolder) {
    const config = vscode.workspace.getConfiguration("strictMappingGuard");
    const watcherPatterns = normalizeWatchGlobs(config.get("watchGlobs"));

    for (const pattern of watcherPatterns) {
      const watcher = vscode.workspace.createFileSystemWatcher(
        new vscode.RelativePattern(watcherFolder, pattern)
      );

      const triggerIfWatched = (uri) => {
        const latestConfig = vscode.workspace.getConfiguration("strictMappingGuard");
        if (isWatchedUri(uri, watcherFolder.uri.fsPath, latestConfig)) {
          scheduleValidation({ mode: "change", triggerUri: uri, notifyOnFail: false });
        }
      };

      watcher.onDidChange(triggerIfWatched);
      watcher.onDidCreate(triggerIfWatched);
      watcher.onDidDelete(triggerIfWatched);
      fileWatcherDisposables.push(watcher);
    }
  }

  const configChangeDisposable = vscode.workspace.onDidChangeConfiguration((event) => {
    if (!event.affectsConfiguration("strictMappingGuard")) {
      return;
    }
    scheduleValidation({ mode: "change", triggerUri: null, notifyOnFail: false });
  });

  context.subscriptions.push(
    commandDisposable,
    showIssuesDisposable,
    saveDisposable,
    createDisposable,
    deleteDisposable,
    renameDisposable,
    focusDisposable,
    configChangeDisposable,
    ...fileWatcherDisposables
  );

  // Auto-run once after activation so issues surface without manual command.
  scheduleValidation({ mode: "change", triggerUri: null, notifyOnFail: false });
}

function deactivate() {}

function isWatchedPath(relPath, config) {
  if (!relPath || relPath.startsWith("..")) {
    return false;
  }

  const normalized = relPath.replace(/\\/g, "/");
  const ignorePrefixes = normalizePathPrefixes(config?.get("ignorePathPrefixes"));
  if (isIgnoredPath(normalized, ignorePrefixes)) {
    return false;
  }

  if (config?.get("watchAllFiles")) {
    return true;
  }

  if (WATCH_FILES.has(normalized)) {
    return true;
  }

  return WATCH_PREFIXES.some((prefix) => normalized.startsWith(prefix));
}

function anyWatchedUris(uris, workspaceRoot, config) {
  for (const uri of uris) {
    if (isWatchedUri(uri, workspaceRoot, config)) {
      return true;
    }
  }
  return false;
}

function isWatchedUri(uri, workspaceRoot, config) {
  const rel = path.relative(workspaceRoot, uri.fsPath).replace(/\\/g, "/");
  return isWatchedPath(rel, config);
}

function normalizeWatchGlobs(value) {
  const items = getStringArray(value);
  return items.length ? items : ["**/*"];
}

function normalizePathPrefixes(value) {
  const items = getStringArray(value);
  const source = items.length ? items : DEFAULT_IGNORE_PATH_PREFIXES;
  return source.map((item) => item.replace(/\\/g, "/")).map((item) => (
    item.endsWith("/") ? item : `${item}/`
  ));
}

function isIgnoredPath(relPath, ignorePrefixes) {
  return ignorePrefixes.some((prefix) => {
    const bare = prefix.endsWith("/") ? prefix.slice(0, -1) : prefix;
    return relPath === bare || relPath.startsWith(prefix);
  });
}

function getStringArray(value) {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .filter((item) => typeof item === "string")
    .map((item) => item.trim())
    .filter(Boolean);
}

function detectRepositorySupport(repoRoot, config) {
  const fallbackTarget = getDefaultFallbackTarget(repoRoot);
  if (!config?.get("autoDetectRepository")) {
    return {
      enabled: true,
      reason: "repository auto-detection disabled",
      fallbackTarget
    };
  }

  const registryCandidates = getStringArray(config?.get("requiredRegistryPaths"));
  const validatorCandidates = getStringArray(config?.get("requiredValidatorPaths"));
  const registryPaths = registryCandidates.length ? registryCandidates : DEFAULT_REGISTRY_PATHS;
  const validatorPaths = validatorCandidates.length ? validatorCandidates : DEFAULT_VALIDATOR_PATHS;

  const existingRegistry = firstExistingPath(repoRoot, registryPaths);
  const existingValidator = firstExistingPath(repoRoot, validatorPaths);

  if (existingRegistry && existingValidator) {
    return {
      enabled: true,
      reason: "strict mapping repository detected",
      fallbackTarget: existingRegistry
    };
  }

  const missing = [];
  if (!existingRegistry) {
    missing.push("mapping registry file");
  }
  if (!existingValidator) {
    missing.push("validator script");
  }

  return {
    enabled: false,
    reason: `skipped (${missing.join(" + ")} not found)`,
    fallbackTarget
  };
}

function firstExistingPath(repoRoot, relPaths) {
  for (const relPath of relPaths) {
    const fullPath = path.join(repoRoot, relPath);
    if (fs.existsSync(fullPath)) {
      return fullPath;
    }
  }
  return null;
}

function getDefaultFallbackTarget(repoRoot) {
  if (!repoRoot) {
    return null;
  }
  const fallbackCandidates = [...DEFAULT_REGISTRY_PATHS, ...DEFAULT_VALIDATOR_PATHS];
  const existing = firstExistingPath(repoRoot, fallbackCandidates);
  if (existing) {
    return existing;
  }
  return path.join(repoRoot, "README.md");
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

function applyDiagnostics(parsed, collection, repoRoot, triggerUri, fallbackTarget) {
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
        : fallbackTarget || getDefaultFallbackTarget(repoRoot));
    if (!grouped.has(target)) {
      grouped.set(target, []);
    }

    const startLine = Math.max(0, Number(issue.line || 1) - 1);
    const startCol = Math.max(0, Number(issue.column || 1) - 1);
    const range = new vscode.Range(startLine, startCol, startLine, startCol + 1);
    const diag = new vscode.Diagnostic(
      range,
      `[strict-mapping] ${issue.message}`,
      vscode.DiagnosticSeverity.Error
    );
    if (issue.code) {
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

function toWorkspaceRelative(filePath, repoRoot) {
  const rel = path.relative(repoRoot, filePath).replace(/\\/g, "/");
  return rel.startsWith("..") ? filePath : rel;
}

async function revealIssue(issue, repoRoot, fallbackTarget) {
  const candidate = resolveIssueFile(issue.file, repoRoot);
  const target = (candidate && fs.existsSync(candidate))
    ? candidate
    : fallbackTarget || getDefaultFallbackTarget(repoRoot);
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
      code: "STRICT_MAPPING",
      related: []
    };
  }

  if (!item || typeof item !== "object") {
    return {
      message: String(item),
      file: null,
      line: 1,
      column: 1,
      code: "STRICT_MAPPING",
      related: []
    };
  }

  return {
    message: String(item.message || "Strict mapping issue"),
    file: item.file || null,
    line: Number(item.line || 1),
    column: Number(item.column || 1),
    code: item.code || "STRICT_MAPPING",
    related: Array.isArray(item.related) ? item.related : []
  };
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
    return "Strict Mapping Guard";
  }
  const preview = errors.slice(0, 3).map((e) => `• ${e.message}`).join("\n");
  const more = errors.length > 3 ? `\n... +${errors.length - 3} more` : "";
  return `Strict Mapping Guard\n${preview}${more}\n(click to open Problems)`;
}

module.exports = {
  activate,
  deactivate
};
