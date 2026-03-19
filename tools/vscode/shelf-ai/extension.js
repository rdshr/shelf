const fs = require("fs");
const path = require("path");
const vscode = require("vscode");
const frameworkNavigation = require("./framework_navigation");
const configNavigation = require("./config_navigation");
const frameworkCompletion = require("./framework_completion");
const evidenceTree = require("./evidence_tree");
const correspondenceRuntime = require("./correspondence_runtime");
const workspaceGuard = require("./guarding");
const validationRuntime = require("./validation_runtime");
const intentGate = require("./intent_gate");
const treeRuntimeModels = require("./tree_runtime_models");
const treeWebviewBridge = require("./tree_webview_bridge");
const localSettings = require("./local_settings");

const STANDARDS_TREE_FILE = path.join("specs", "规范总纲与树形结构.md");
const DEFAULT_VALIDATION_FALLBACK_FILE = path.join("projects", "knowledge_base_basic", "project.toml");
const SIDEBAR_VIEW_ID = "shelf.sidebarHome";
const DEFAULT_MATERIALIZE_COMMAND = "uv run python scripts/materialize_project.py";
const DEFAULT_PUBLISH_FRAMEWORK_DRAFT_COMMAND = "uv run python scripts/publish_framework_draft.py";
const DEFAULT_TYPE_CHECK_COMMAND = "uv run mypy";
const DEFAULT_INSTALL_GIT_HOOKS_COMMAND = "bash scripts/install_git_hooks.sh";
const DEFAULT_CHANGE_VALIDATION_COMMAND = "uv run python scripts/validate_canonical.py --check-changes";
const DEFAULT_INTENT_GATE_TTL_MINUTES = 120;
const DEFAULT_INTENT_GATE_MINIMUM_SCORE = 4;
const DEFAULT_INTENT_GATE_MAX_MATCHES = 8;
const INTENT_GATE_GUARD_ALL_TOKEN = "*";
const DEFAULT_INTENT_GATE_GUARDED_PREFIXES = [
  "framework/",
  "framework_drafts/",
  "projects/",
  "src/project_runtime/",
  "scripts/",
  "tools/vscode/shelf-ai/",
];
const DEFAULT_INTENT_GATE_IGNORED_PREFIXES = [
  ".git/",
  ".github/",
  ".venv/",
  "node_modules/",
  "dist/",
  "build/",
  "out/",
  ".pytest_cache/",
  ".mypy_cache/",
  "__pycache__/",
];
const FRAMEWORK_RULE_HINTS = {
  FW002: "@framework 必须无参数",
  FW003: "标题必须为 中文名:EnglishName",
  FW010: "当前框架文件内编号必须唯一",
  FW011: "C/B/R/V 编号格式必须合法",
  FW020: "B* 必须包含来源",
  FW021: "B* 来源表达式与引用必须合法",
  FW022: "B* 来源中的能力归属与参数约束必须合法",
  FW023: "B* 禁止使用“上游模块：...”，必须内联写模块引用",
  FW024: "非根层模块的 B* 必须在主句中内联写本框架上游模块引用",
  FW025: "B* 的本地内联模块引用必须指向当前框架中真实存在的更低本地层模块",
  FW026: "当前框架最低本地层的 B* 不能引用本框架内部其他模块",
  FW027: "外部内联模块引用的合法性以显式依赖方向为准，Lx 标签只作参考",
  FW028: "外部内联模块引用必须指向真实存在的框架模块",
  FW029: "框架内联模块引用图必须无环",
  FW030: "边界参数必须包含来源",
  FW031: "边界来源必须引用 C* 且引用合法",
  FW040: "R*/R*.* 编号必须合法并可追溯",
  FW041: "每个 R* 必须包含参与基/组合方式/输出能力/参数绑定",
  FW050: "R*.输出能力必须引用已定义 C*",
  FW060: "新符号必须通过输出结构声明后才可在规则中使用"
};

function resetStatusToIdle(status) {
  status.text = "$(check) Shelf idle";
  status.tooltip = "Shelf";
  status.backgroundColor = undefined;
  status.color = undefined;
}

function createStatusController({
  status,
  getValidationTriggerMode,
  getMappingValidationActive,
  getLastRepoRoot,
  getLastRunIssues,
  getDirtyWatchedFileCount,
  getLastValidationPassed,
}) {
  const setOk = () => {
    status.text = "$(check) Shelf OK";
    status.tooltip = "Shelf: no guard issues";
    status.backgroundColor = undefined;
    status.color = undefined;
  };

  const setError = (errors) => {
    status.text = "$(close) Shelf failed";
    status.tooltip = buildTooltip(errors);
    status.backgroundColor = new vscode.ThemeColor("statusBarItem.errorBackground");
    status.color = new vscode.ThemeColor("statusBarItem.errorForeground");
  };

  const setPendingSave = () => {
    const dirtyCount = getDirtyWatchedFileCount();
    const triggerMode = getValidationTriggerMode();
    const revalidateHint = triggerMode === "manual"
      ? "Run validation when you are ready."
      : "Save to revalidate.";
    status.text = "$(close) Shelf pending";
    status.tooltip = dirtyCount > 0
      ? `Shelf: ${dirtyCount} watched file(s) changed. ${revalidateHint}`
      : `Shelf: watched files changed. ${revalidateHint}`;
    status.backgroundColor = new vscode.ThemeColor("statusBarItem.warningBackground");
    status.color = new vscode.ThemeColor("statusBarItem.warningForeground");
  };

  const refresh = () => {
    if (!getMappingValidationActive()) {
      const repoRoot = getLastRepoRoot();
      if (repoRoot) {
        setStatusDisabled(status, repoRoot);
      }
      return;
    }
    const lastRunIssues = getLastRunIssues();
    if (lastRunIssues.length) {
      setError(lastRunIssues);
      return;
    }
    if (getDirtyWatchedFileCount()) {
      setPendingSave();
      return;
    }
    if (getLastValidationPassed() === true) {
      setOk();
      return;
    }
    resetStatusToIdle(status);
  };

  return {
    setOk,
    setError,
    setPendingSave,
    refresh,
  };
}

function toWatchedTriggerUris(repoRoot, uris, isSuppressedGeneratedPath) {
  return (uris || []).filter((uri) => {
    const relPath = workspaceGuard.normalizeRelPath(path.relative(repoRoot, uri.fsPath));
    return workspaceGuard.isWatchedPath(relPath) && !isSuppressedGeneratedPath(relPath);
  });
}

function flattenRenameEventUris(items) {
  const uris = [];
  for (const item of items || []) {
    uris.push(item.oldUri, item.newUri);
  }
  return uris;
}

function scheduleWatchedChangeValidation({
  repoRoot,
  uris,
  scheduleValidation,
  isSuppressedGeneratedPath,
  source = "auto",
}) {
  const triggerUris = toWatchedTriggerUris(repoRoot, uris, isSuppressedGeneratedPath);
  if (!triggerUris.length) {
    return false;
  }
  scheduleValidation({ mode: "change", triggerUris, notifyOnFail: false, source });
  return true;
}

function createWorkspaceValidationWatchers({
  watcherFolder,
  shouldRunValidationTrigger,
  scheduleValidation,
  isSuppressedGeneratedPath,
}) {
  const watcherPatterns = [
    ...workspaceGuard.WATCH_PREFIXES.map((prefix) => `${prefix}**`),
    ...workspaceGuard.WATCH_FILES,
  ];
  const watcherDisposables = [];

  for (const pattern of watcherPatterns) {
    const watcher = vscode.workspace.createFileSystemWatcher(
      new vscode.RelativePattern(watcherFolder, pattern)
    );

    const triggerIfWatched = (uri) => {
      if (!shouldRunValidationTrigger("workspace")) {
        return;
      }
      scheduleWatchedChangeValidation({
        repoRoot: watcherFolder.uri.fsPath,
        uris: [uri],
        scheduleValidation,
        isSuppressedGeneratedPath,
      });
    };

    watcher.onDidChange(triggerIfWatched);
    watcher.onDidCreate(triggerIfWatched);
    watcher.onDidDelete(triggerIfWatched);
    watcherDisposables.push(watcher);
  }

  return watcherDisposables;
}

function activate(context) {
  const output = vscode.window.createOutputChannel("Shelf");
  const diagnostics = vscode.languages.createDiagnosticCollection("shelf-validation");
  const status = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
  resetStatusToIdle(status);
  status.command = "shelf.showIssues";
  status.show();

  context.subscriptions.push(output, diagnostics, status);

  let running = false;
  let pending = null;
  let timer = null;
  let lastFailureSignature = "";
  let lastRunIssues = [];
  let lastRepoRoot = "";
  let validationActive = true;
  let treePanel = null;
  let treePanelKind = "framework";
  let treePanelRepoRoot = "";
  let frameworkSidebarView = null;
  let lastValidationAt = "";
  let lastValidationMode = "change";
  let lastValidationPassed = null;
  let lastChangeContext = null;
  let lastChangeSummary = null;
  let gitHooksReady = null;
  let gitHooksDetail = "Not checked in this session";
  let gitHooksPrompted = false;
  let intentGateSession = null;
  let localShelfSettingValues = {};
  let localShelfSettingsError = "";
  const suppressedGeneratedDirectories = new Map();
  const dirtyWatchedFiles = new Set();
  const guardedBaselineByPath = new Map();
  const restoringGuardedFiles = new Set();
  const activeValidationCommand = validationRuntime.createActiveCommandTracker();
  const VALIDATION_SOURCE_PRIORITY = {
    auto: 1,
    save: 2,
    manual: 3
  };
  const TREE_WEBVIEW_SETTING_KEYS = [
    "shelf.frameworkTreeNodeHorizontalGap",
    "shelf.frameworkTreeLevelVerticalGap",
    "shelf.treeZoomMinScale",
    "shelf.treeZoomMaxScale",
    "shelf.treeWheelSensitivity",
    "shelf.treeInspectorWidth",
    "shelf.treeInspectorRailWidth",
  ];
  const INTENT_GATE_SETTING_KEYS = [
    "shelf.intentGateEnabled",
    "shelf.intentGateEnforcementMode",
    "shelf.intentGateRequireMappingEcho",
    "shelf.intentGateRunChangeValidationBeforeGrant",
    "shelf.intentGateAutoOpenOutput",
    "shelf.intentGateMinimumScore",
    "shelf.intentGateMaxMatches",
    "shelf.intentGateSessionTtlMinutes",
    "shelf.intentGateGuardedPathPrefixes",
    "shelf.intentGateIgnoredPathPrefixes",
    "shelf.intentGateTemporaryBypasses",
  ];

  const clampInt = (value, minimum, maximum, fallback) => {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) {
      return fallback;
    }
    return Math.min(maximum, Math.max(minimum, Math.round(parsed)));
  };

  const clampNumber = (value, minimum, maximum, fallback) => {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) {
      return fallback;
    }
    return Math.min(maximum, Math.max(minimum, parsed));
  };

  const getShelfConfig = () => {
    const config = vscode.workspace.getConfiguration("shelf");
    return {
      get(settingKey, fallback) {
        return localSettings.getShelfSetting(config, localShelfSettingValues, settingKey, fallback);
      }
    };
  };

  const reloadLocalShelfSettings = (repoRoot, { notifyOnError = false } = {}) => {
    const snapshot = localSettings.readLocalShelfSettings(repoRoot);
    localShelfSettingValues = snapshot.values;
    const nextError = snapshot.error || "";
    if (nextError) {
      if (nextError !== localShelfSettingsError) {
        output.appendLine(`[settings] ${nextError}`);
      }
      if (notifyOnError) {
        void vscode.window.showWarningMessage(
          `Shelf ignored ${localSettings.LOCAL_SETTINGS_REL_PATH}: ${nextError}`
        );
      }
    } else if (localShelfSettingsError) {
      output.appendLine(`[settings] local shelf settings recovered: ${localSettings.LOCAL_SETTINGS_REL_PATH}`);
    }
    localShelfSettingsError = nextError;
    return snapshot;
  };

  const readTreeLayoutSettings = () => {
    const config = getShelfConfig();
    return {
      frameworkNodeHorizontalGap: clampInt(config.get("frameworkTreeNodeHorizontalGap"), 0, 40, 8),
      frameworkLevelVerticalGap: clampInt(config.get("frameworkTreeLevelVerticalGap"), 48, 180, 80),
    };
  };

  const readTreeViewSettings = () => {
    const config = getShelfConfig();
    const zoomMinScale = clampNumber(config.get("treeZoomMinScale"), 0.2, 3, 0.68);
    const zoomMaxScale = clampNumber(config.get("treeZoomMaxScale"), zoomMinScale, 5, 1.55);
    return {
      zoomMinScale,
      zoomMaxScale,
      wheelSensitivity: clampNumber(config.get("treeWheelSensitivity"), 0.25, 3, 1),
      inspectorWidth: clampInt(config.get("treeInspectorWidth"), 240, 520, 338),
      inspectorRailWidth: clampInt(config.get("treeInspectorRailWidth"), 32, 72, 42),
    };
  };

  const readValidationTimingSettings = () => {
    const config = getShelfConfig();
    return {
      validationCommandTimeoutMs: clampInt(config.get("validationCommandTimeoutMs"), 1_000, 1_800_000, 120_000),
      generatedEventSuppressionMs: clampInt(config.get("generatedEventSuppressionMs"), 0, 30_000, 2_500),
      manualValidationRestartThresholdMs: clampInt(
        config.get("manualValidationRestartThresholdMs"),
        1_000,
        300_000,
        15_000
      ),
      validationDebounceMs: clampInt(config.get("validationDebounceMs"), 0, 5_000, 250),
    };
  };

  const getValidationTriggerMode = () => {
    const config = getShelfConfig();
    const value = String(config.get("validationTriggerMode") || "all");
    return ["manual", "save", "all"].includes(value) ? value : "all";
  };

  const shouldRunValidationTrigger = (triggerKind) => {
    const mode = getValidationTriggerMode();
    if (mode === "all") {
      return true;
    }
    if (mode === "manual") {
      return false;
    }
    return triggerKind === "save";
  };

  const normalizePrefixList = (value, fallback) => {
    const source = Array.isArray(value) ? value : fallback;
    const normalized = [];
    const seen = new Set();
    for (const item of source) {
      const rawText = String(item || "").trim();
      if (!rawText) {
        continue;
      }
      if (rawText === INTENT_GATE_GUARD_ALL_TOKEN) {
        return [INTENT_GATE_GUARD_ALL_TOKEN];
      }
      const text = workspaceGuard.normalizeRelPath(rawText);
      if (!text || seen.has(text)) {
        continue;
      }
      seen.add(text);
      normalized.push(text.endsWith("/") ? text : `${text}/`);
    }
    return normalized.length ? normalized : fallback;
  };

  const readIntentGateSettings = () => {
    const config = getShelfConfig();
    const rawMode = String(config.get("intentGateEnforcementMode") || "block").trim().toLowerCase();
    const mode = rawMode === "warn" ? "warn" : "block";
    return {
      enabled: Boolean(config.get("intentGateEnabled")),
      mode,
      requireMappingEcho: Boolean(config.get("intentGateRequireMappingEcho")),
      runValidationBeforeGrant: Boolean(config.get("intentGateRunChangeValidationBeforeGrant")),
      autoOpenOutput: Boolean(config.get("intentGateAutoOpenOutput")),
      minimumScore: clampInt(
        config.get("intentGateMinimumScore"),
        1,
        20,
        DEFAULT_INTENT_GATE_MINIMUM_SCORE
      ),
      maxMatches: clampInt(
        config.get("intentGateMaxMatches"),
        1,
        20,
        DEFAULT_INTENT_GATE_MAX_MATCHES
      ),
      ttlMinutes: clampInt(
        config.get("intentGateSessionTtlMinutes"),
        1,
        1_440,
        DEFAULT_INTENT_GATE_TTL_MINUTES
      ),
      guardedPrefixes: normalizePrefixList(
        config.get("intentGateGuardedPathPrefixes"),
        DEFAULT_INTENT_GATE_GUARDED_PREFIXES
      ),
      ignoredPrefixes: normalizePrefixList(
        config.get("intentGateIgnoredPathPrefixes"),
        DEFAULT_INTENT_GATE_IGNORED_PREFIXES
      ),
      temporaryBypasses: intentGate.normalizeTemporaryBypassScopes(
        config.get("intentGateTemporaryBypasses")
      ),
    };
  };

  const isIntentGateTemporaryBypassEnabled = (settings, scope) => (
    intentGate.isTemporaryBypassScopeEnabled(settings?.temporaryBypasses, scope)
  );

  const clearIntentGateSession = (reason = "") => {
    if (intentGateSession && reason) {
      output.appendLine(`[intent-gate] session cleared: ${reason}`);
    }
    intentGateSession = null;
  };

  const pathMatchesPrefix = (relPath, prefix) => (
    prefix === INTENT_GATE_GUARD_ALL_TOKEN || relPath === prefix || relPath.startsWith(prefix)
  );

  const isIntentGateGuardedPath = (repoRoot, fsPath, settings) => {
    if (!repoRoot || !fsPath || !settings.enabled) {
      return false;
    }
    const relPath = workspaceGuard.normalizeRelPath(path.relative(repoRoot, fsPath));
    if (!relPath || relPath.startsWith("..")) {
      return false;
    }
    if (settings.ignoredPrefixes.some((prefix) => pathMatchesPrefix(relPath, prefix))) {
      return false;
    }
    return settings.guardedPrefixes.some((prefix) => pathMatchesPrefix(relPath, prefix));
  };

  const isIntentGateSessionExpired = (session, settings) => {
    if (!session || !session.createdAt) {
      return true;
    }
    const createdMs = new Date(session.createdAt).getTime();
    if (!Number.isFinite(createdMs)) {
      return true;
    }
    const ttlMs = settings.ttlMinutes * 60 * 1000;
    return (Date.now() - createdMs) > ttlMs;
  };

  const ensureIntentGateSession = (settings) => {
    if (!settings.enabled) {
      return null;
    }
    if (!intentGateSession) {
      return null;
    }
    if (isIntentGateSessionExpired(intentGateSession, settings)) {
      clearIntentGateSession("session ttl exceeded");
      return null;
    }
    return intentGateSession;
  };

  const handleRuntimeSettingSourcesChanged = async ({
    reason = "settings changed",
    refreshTree = false,
  } = {}) => {
    const settings = readIntentGateSettings();
    if (!settings.enabled) {
      clearIntentGateSession(`intent gate disabled by ${reason}`);
    } else {
      ensureIntentGateSession(settings);
    }
    refreshSidebarHome();
    if (refreshTree && treePanel) {
      await openTreeView(treePanelKind);
    }
  };

  const statusController = createStatusController({
    status,
    getValidationTriggerMode,
    getMappingValidationActive: () => validationActive,
    getLastRepoRoot: () => lastRepoRoot,
    getLastRunIssues: () => lastRunIssues,
    getDirtyWatchedFileCount: () => dirtyWatchedFiles.size,
    getLastValidationPassed: () => lastValidationPassed,
  });
  const refreshStatusFromCurrentState = () => statusController.refresh();

  const getCanonicalFreshnessState = (repoRoot) => {
    const summary = workspaceGuard.summarizeCanonicalFreshness(repoRoot);
    const authoritativeSources = new Set();
    for (const projectFreshness of summary.projects) {
      for (const relPath of projectFreshness.authoritativeSourceRelPaths || []) {
        authoritativeSources.add(relPath);
      }
    }
    const dirtySourceRelPaths = [...dirtyWatchedFiles]
      .map((fsPath) => workspaceGuard.normalizeRelPath(path.relative(repoRoot, fsPath)))
      .filter((relPath) => authoritativeSources.has(relPath))
      .sort();
    return {
      projects: summary.projects,
      blockingProjects: summary.blockingProjects,
      dirtySourceRelPaths,
      hasBlocking: summary.hasBlockingProjects || dirtySourceRelPaths.length > 0,
    };
  };

  const describeProjectFreshness = (projectFreshness) => {
    const projectLabel = projectFreshness.projectId || path.basename(path.dirname(projectFreshness.projectFilePath || ""));
    if (projectFreshness.status === "missing") {
      return `${projectLabel}: missing ${projectFreshness.canonicalRelPath || "generated/canonical.json"}`;
    }
    if (projectFreshness.status === "invalid") {
      return `${projectLabel}: invalid canonical.json`;
    }
    const staleSources = [
      ...(projectFreshness.newerSourceRelPaths || []),
      ...(projectFreshness.missingSourceRelPaths || []),
    ];
    if (!staleSources.length) {
      return `${projectLabel}: stale canonical`;
    }
    return `${projectLabel}: stale via ${staleSources.slice(0, 2).join(", ")}`;
  };

  const describeCanonicalFreshness = (freshnessState) => {
    const parts = [];
    if (freshnessState.dirtySourceRelPaths.length) {
      parts.push(`dirty authoring sources: ${freshnessState.dirtySourceRelPaths.slice(0, 2).join(", ")}`);
    }
    if (freshnessState.blockingProjects.length) {
      parts.push(
        freshnessState.blockingProjects
          .slice(0, 2)
          .map(describeProjectFreshness)
          .join(" | ")
      );
    }
    return parts.join(" | ");
  };

  const normalizeTriggerUris = (options = {}) => {
    const inputs = [];
    if (options.triggerUri) {
      inputs.push(options.triggerUri);
    }
    if (Array.isArray(options.triggerUris)) {
      inputs.push(...options.triggerUris);
    }

    const seen = new Set();
    const normalized = [];
    for (const uri of inputs) {
      if (!uri || !uri.fsPath) {
        continue;
      }
      if (seen.has(uri.fsPath)) {
        continue;
      }
      seen.add(uri.fsPath);
      normalized.push(uri);
    }
    return normalized;
  };

  const normalizeValidationOptions = (options = {}) => ({
    mode: options.mode === "full" ? "full" : "change",
    triggerUris: normalizeTriggerUris(options),
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
      triggerUris: normalizeTriggerUris({
        triggerUris: [...current.triggerUris, ...incoming.triggerUris]
      }),
      notifyOnFail: current.notifyOnFail || incoming.notifyOnFail,
      source
    };
  };

  const pruneSuppressedGeneratedDirectories = () => {
    const now = Date.now();
    for (const [generatedDir, expiresAt] of suppressedGeneratedDirectories.entries()) {
      if (expiresAt <= now) {
        suppressedGeneratedDirectories.delete(generatedDir);
      }
    }
  };

  const isSuppressedGeneratedPath = (relPath) => {
    pruneSuppressedGeneratedDirectories();
    const normalized = workspaceGuard.normalizeRelPath(relPath);
    for (const [generatedDir] of suppressedGeneratedDirectories.entries()) {
      if (normalized === generatedDir || normalized.startsWith(`${generatedDir}/`)) {
        return true;
      }
    }
    return false;
  };

  const suppressGeneratedEventsForProjects = (repoRoot, projectFiles) => {
    const expiresAt = Date.now() + readValidationTimingSettings().generatedEventSuppressionMs;
    for (const projectFile of projectFiles) {
      const generatedDir = path.join(path.dirname(projectFile), "generated");
      const generatedRel = workspaceGuard.normalizeRelPath(path.relative(repoRoot, generatedDir));
      if (generatedRel) {
        suppressedGeneratedDirectories.set(generatedRel, expiresAt);
      }
    }
  };

  const runParsedCommand = async (label, command, repoRoot, parseFn) => {
    output.appendLine(`[${label}] ${command}`);
    const timingSettings = readValidationTimingSettings();
    const execResult = await validationRuntime.execCommand(command, repoRoot, {
      timeoutMs: timingSettings.validationCommandTimeoutMs,
      onSpawn: (child) => activeValidationCommand.trackChild(label, child),
      onExit: (child) => activeValidationCommand.clearChild(child),
    });
    output.appendLine(execResult.stdout || "");
    output.appendLine(execResult.stderr || "");
    if (execResult.timedOut) {
      return parseStageFailure(
        `SHELF_${String(label).replace(/[^A-Za-z0-9]+/g, "_").toUpperCase()}_TIMEOUT`,
        `Shelf ${label} command timed out after ${Math.round(execResult.timeoutMs / 1000)}s.`,
        execResult.stdout,
        execResult.stderr,
        execResult.code
      );
    }
    return parseFn(execResult.stdout, execResult.stderr, execResult.code);
  };

  const appendIntentGateAnalysisLog = (analysis, settings) => {
    output.appendLine("[intent-gate] mapping summary");
    output.appendLine(`- intent: ${analysis.intentText}`);
    output.appendLine(`- query tokens: ${analysis.queryTokens.join(", ")}`);
    output.appendLine(`- mappings: ${analysis.mappings.length}`);
    output.appendLine(`- minimum score: ${settings.minimumScore}`);
    output.appendLine(`- guarded prefixes: ${settings.guardedPrefixes.join(", ")}`);
    output.appendLine(`- ignored prefixes: ${settings.ignoredPrefixes.join(", ")}`);
    output.appendLine(
      `- temporary bypasses: ${settings.temporaryBypasses.length ? settings.temporaryBypasses.join(", ") : "none"}`
    );
    output.appendLine(intentGate.formatIntentMappingSummary(analysis));
    if (analysis.errors.length) {
      output.appendLine(`- canonical read warnings: ${analysis.errors.join(" | ")}`);
    }
  };

  const runIntentGateGrantValidation = async (repoRoot, settings) => {
    if (isIntentGateTemporaryBypassEnabled(settings, "grant_pre_validation")) {
      output.appendLine("[intent-gate] temporary bypass active: skip grant pre-validation.");
      return { passed: true, errors: [] };
    }
    if (!settings.runValidationBeforeGrant) {
      return { passed: true, errors: [] };
    }
    const config = getShelfConfig();
    const changeValidationCommand = validationRuntime.normalizeValidationCommand(
      String(config.get("changeValidationCommand") || DEFAULT_CHANGE_VALIDATION_COMMAND)
    );
    return runParsedCommand(
      "intent-gate-validate",
      changeValidationCommand,
      repoRoot,
      parseResult
    );
  };

  const grantIntentGateSession = async ({ repoRoot, intentText }) => {
    const settings = readIntentGateSettings();
    const normalizedIntent = String(intentText || "").trim();
    if (!settings.enabled) {
      return { passed: false, message: "Shelf intent gate is disabled in settings." };
    }
    if (!normalizedIntent) {
      return { passed: false, message: "Intent text is empty." };
    }

    const preValidation = await runIntentGateGrantValidation(repoRoot, settings);
    if (!preValidation.passed) {
      const firstMessage = preValidation.errors[0]?.message || "validate_canonical --check-changes failed.";
      return {
        passed: false,
        message: `intent gate blocked before mapping: ${firstMessage}`,
      };
    }

    const analysis = intentGate.analyzeIntentMapping({
      repoRoot,
      intentText: normalizedIntent,
      minimumScore: settings.minimumScore,
      maxResults: settings.maxMatches,
      allowNonOneToOneMapping: isIntentGateTemporaryBypassEnabled(settings, "one_to_one_check"),
    });
    if (isIntentGateTemporaryBypassEnabled(settings, "one_to_one_check")) {
      output.appendLine("[intent-gate] temporary bypass active: allow non one-to-one boundary mapping.");
    }
    appendIntentGateAnalysisLog(analysis, settings);
    if (settings.autoOpenOutput) {
      output.show(true);
    }

    if (!analysis.passed) {
      clearIntentGateSession("mapping not found");
      const reason = String(analysis.reason || "").trim();
      return {
        passed: false,
        analysis,
        message: reason || "No framework mapping reached threshold. Ask a human to update framework first.",
      };
    }

    const requireMappingEcho = settings.requireMappingEcho
      && !isIntentGateTemporaryBypassEnabled(settings, "mapping_echo");
    if (settings.requireMappingEcho && !requireMappingEcho) {
      output.appendLine("[intent-gate] temporary bypass active: skip mapping echo confirmation.");
    }
    if (requireMappingEcho) {
      const picks = analysis.mappings.slice(0, 6).map((item) => ({
        label: `${item.moduleId} / ${item.boundaryId}`,
        description: item.exactPaths.join(", "),
        detail: `score=${item.score} · ${item.note || "projection from canonical"}`,
      }));
      const selected = await vscode.window.showQuickPick(
        [
          {
            label: "Confirm Mapping (Recommended)",
            description: "Grant this governed task session.",
            detail: "Use the top canonical-backed mappings and unlock guarded saves.",
            keepOpen: true,
          },
          ...picks,
        ],
        {
          title: "Shelf Governed Task Mapping",
          canPickMany: false,
          placeHolder: "Confirm mapping, or cancel to keep implementation edits blocked.",
        }
      );
      if (!selected || !selected.keepOpen) {
        return {
          passed: false,
          analysis,
          message: "Mapping confirmation was cancelled.",
        };
      }
    }

    intentGateSession = {
      id: `intent-${Date.now()}`,
      createdAt: new Date().toISOString(),
      repoRoot,
      intentText: normalizedIntent,
      analysis,
      allowedExactPaths: analysis.allowedExactPaths,
      allowedCommunicationPaths: analysis.allowedCommunicationPaths,
      matchedModuleIds: analysis.matchedModuleIds,
      lastTouchedAt: new Date().toISOString(),
    };
    refreshSidebarHome();
    return { passed: true, analysis, message: "Governed task session granted." };
  };

  const restoreGuardedDocumentFromBaseline = async (doc, baselineText) => {
    if (!doc || typeof baselineText !== "string") {
      return false;
    }
    const targetPath = doc.uri?.fsPath || "";
    if (!targetPath) {
      return false;
    }
    restoringGuardedFiles.add(targetPath);
    try {
      const fullRange = new vscode.Range(
        doc.positionAt(0),
        doc.positionAt(doc.getText().length)
      );
      const edit = new vscode.WorkspaceEdit();
      edit.replace(doc.uri, fullRange, baselineText);
      const applied = await vscode.workspace.applyEdit(edit);
      if (!applied) {
        return false;
      }
      await doc.save();
      return true;
    } finally {
      restoringGuardedFiles.delete(targetPath);
    }
  };

  const enforceIntentGateOnSave = async (doc) => {
    const settings = readIntentGateSettings();
    if (!settings.enabled) {
      return { allow: true };
    }
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder || !doc?.uri?.fsPath) {
      return { allow: true };
    }
    const repoRoot = folder.uri.fsPath;
    const docPath = doc.uri.fsPath;

    if (isIntentGateTemporaryBypassEnabled(settings, "save_guard")) {
      guardedBaselineByPath.delete(docPath);
      return { allow: true };
    }

    if (restoringGuardedFiles.has(docPath)) {
      guardedBaselineByPath.delete(docPath);
      return { allow: true };
    }

    if (!isIntentGateGuardedPath(repoRoot, docPath, settings)) {
      guardedBaselineByPath.delete(docPath);
      return { allow: true };
    }

    const session = ensureIntentGateSession(settings);
    if (session && session.repoRoot === repoRoot) {
      guardedBaselineByPath.delete(docPath);
      session.lastTouchedAt = new Date().toISOString();
      return { allow: true };
    }

    const relPath = workspaceGuard.normalizeRelPath(path.relative(repoRoot, docPath));
    const blockedMessage = session && session.repoRoot !== repoRoot
      ? "guarded save blocked: active intent session belongs to a different workspace."
      : "guarded save blocked: start a governed task and confirm framework mapping first.";

    if (settings.mode === "warn") {
      vscode.window.showWarningMessage(`Shelf intent gate warning (${relPath}): ${blockedMessage}`);
      return { allow: true };
    }

    const baselineText = guardedBaselineByPath.get(docPath);
    if (typeof baselineText !== "string") {
      vscode.window.showErrorMessage(
        `Shelf intent gate blocked save for ${relPath}, but no baseline snapshot was available to restore.`
      );
      return { allow: false };
    }

    const restored = await restoreGuardedDocumentFromBaseline(doc, baselineText);
    if (restored) {
      vscode.window.showErrorMessage(
        `Shelf intent gate blocked and reverted ${relPath}. Run "Shelf: Start Governed Task" first.`
      );
    } else {
      vscode.window.showErrorMessage(
        `Shelf intent gate blocked ${relPath}, but automatic restore failed.`
      );
    }
    return { allow: false };
  };

  const requestManualValidation = () => {
    if (running) {
      const restarted = activeValidationCommand.restartIfStale(
        readValidationTimingSettings().manualValidationRestartThresholdMs
      );
      if (restarted.restarted) {
        output.appendLine(
          `[validate] restarted stale ${restarted.label} command after ${Math.round(restarted.elapsedMs / 1000)}s`
        );
      }
    }
    scheduleValidation({ mode: "full", triggerUris: [], notifyOnFail: true, source: "manual" });
  };

  const activeFrameworkDraftFile = () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor?.document?.uri?.fsPath) {
      return null;
    }
    const folder = vscode.workspace.getWorkspaceFolder(editor.document.uri);
    if (!folder) {
      return null;
    }
    const repoRoot = folder.uri.fsPath;
    const relPath = workspaceGuard.normalizeRelPath(path.relative(repoRoot, editor.document.uri.fsPath));
    if (!/^framework_drafts\/[^/]+\/L\d+-M\d+-[^/]+\.md$/.test(relPath)) {
      return null;
    }
    return {
      repoRoot,
      relPath,
      absPath: editor.document.uri.fsPath,
      publishedRelPath: relPath.replace(/^framework_drafts\//, "framework/"),
      publishedAbsPath: path.join(repoRoot, relPath.replace(/^framework_drafts\//, "framework/")),
    };
  };

  const buildPublishFrameworkDraftCommand = (draftRelPath) => (
    `${DEFAULT_PUBLISH_FRAMEWORK_DRAFT_COMMAND} --draft ${shellQuote(draftRelPath)}`
  );

  const refreshGitHookStatus = async ({ promptIfMissing = false } = {}) => {
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      gitHooksReady = null;
      gitHooksDetail = "No workspace";
      refreshSidebarHome();
      return;
    }

    const repoRoot = folder.uri.fsPath;
    const result = await execCommand("git config --get core.hooksPath", repoRoot);
    const configured = (result.stdout || "").trim();
    const expected = path.resolve(repoRoot, ".githooks");
    const resolved = configured
      ? path.resolve(repoRoot, configured)
      : "";
    gitHooksReady = Boolean(configured) && resolved === expected;
    gitHooksDetail = gitHooksReady
      ? configured
      : (configured || "core.hooksPath is not set to .githooks");
    refreshSidebarHome();

    const config = getShelfConfig();
    if (!promptIfMissing || gitHooksReady || !config.get("promptInstallGitHooks") || gitHooksPrompted) {
      return;
    }

    gitHooksPrompted = true;
    const action = await vscode.window.showInformationMessage(
      "Shelf recommends enabling the repository git hooks so pre-push checks cannot be skipped.",
      "Install Hooks",
      "Later"
    );
    if (action === "Install Hooks") {
      await vscode.commands.executeCommand("shelf.installGitHooks");
    }
  };

  const runCodegenPreflight = async () => {
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      vscode.window.showWarningMessage("Shelf: no workspace is open.");
      return;
    }
    const repoRoot = folder.uri.fsPath;
    const config = getShelfConfig();
    const projectFiles = workspaceGuard.discoverProjectFiles(repoRoot);
    const materializeCommand = buildMaterializeCommand(
      String(config.get("materializeCommand") || DEFAULT_MATERIALIZE_COMMAND),
      projectFiles
    );

    output.clear();
    status.text = "$(sync~spin) Shelf preflight";
    status.backgroundColor = new vscode.ThemeColor("statusBarItem.warningBackground");
    status.color = new vscode.ThemeColor("statusBarItem.warningForeground");

    const materializeResult = await runParsedCommand(
      "codegen-preflight-materialize",
      materializeCommand,
      repoRoot,
      (stdout, stderr, code) => parseStageFailure(
        "SHELF_CODEGEN_PREFLIGHT_MATERIALIZE",
        "Shelf codegen preflight failed during materialization.",
        stdout,
        stderr,
        code
      )
    );
    if (!materializeResult.passed) {
      lastRunIssues = materializeResult.errors;
      lastRepoRoot = repoRoot;
      lastValidationAt = new Date().toISOString();
      lastValidationMode = "full";
      lastValidationPassed = false;
      applyDiagnostics({ passed: false, errors: materializeResult.errors }, diagnostics, repoRoot, null);
      statusController.refresh();
      refreshSidebarHome();
      const action = await vscode.window.showErrorMessage(
        "Shelf codegen preflight failed during materialization.",
        "Open Problems",
        "Open Log"
      );
      if (action === "Open Problems") {
        await vscode.commands.executeCommand("workbench.actions.view.problems");
      } else if (action === "Open Log") {
        output.show(true);
      }
      return;
    }

    if (projectFiles.length) {
      suppressGeneratedEventsForProjects(repoRoot, projectFiles);
    }
    await runValidation({ mode: "full", triggerUris: [], notifyOnFail: true, source: "manual" });
    if (lastValidationPassed) {
      vscode.window.showInformationMessage(
        "Shelf codegen preflight passed. Framework -> Config -> Code -> Evidence chain is consistent."
      );
    }
  };

  const loadEvidenceChangePlan = async ({
    repoRoot,
    relPaths,
  }) => {
    const issues = [];
    let evidencePayload = null;
    let changePlan = workspaceGuard.classifyWorkspaceChanges(repoRoot, relPaths);
    try {
      evidencePayload = evidenceTree.readEvidenceTree(repoRoot, "");
      changePlan = evidenceTree.classifyWorkspaceChanges(repoRoot, relPaths, evidencePayload);
    } catch (error) {
      issues.push(normalizeIssue({
        message: `Shelf could not load evidence tree: ${String(error)}`,
        file: "projects/*/generated/canonical.json",
        line: 1,
        column: 1,
        code: "SHELF_EVIDENCE_TREE",
      }));
    }

    let changeSummary = null;
    if (changePlan.changeContext && evidencePayload) {
      changeSummary = evidenceTree.summarizeChangeContext(evidencePayload, changePlan.changeContext, 4);
    } else if (changePlan.changeContext) {
      changeSummary = {
        touchedCount: Array.isArray(changePlan.changeContext.touchedNodes) ? changePlan.changeContext.touchedNodes.length : 0,
        affectedCount: Array.isArray(changePlan.changeContext.affectedNodes) ? changePlan.changeContext.affectedNodes.length : 0,
        touched: (changePlan.changeContext.touchedNodes || []).slice(0, 4).map((nodeId) => ({
          id: String(nodeId),
          label: String(nodeId),
          layer: "",
          file: "",
        })),
        affected: (changePlan.changeContext.affectedNodes || []).slice(0, 4).map((nodeId) => ({
          id: String(nodeId),
          label: String(nodeId),
          layer: "",
          file: "",
        })),
      };
    }

    return {
      issues,
      evidencePayload,
      changePlan,
      changeSummary,
    };
  };

  const protectGeneratedArtifacts = async ({
    repoRoot,
    config,
    changePlan,
  }) => {
    const issues = [];
    const materializedProjects = new Set();
    if (!config.get("protectGeneratedFiles") || !changePlan.protectedGeneratedPaths.length) {
      return { issues, materializedProjects };
    }

    const guardMode = config.get("guardMode") === "strict" ? "strict" : "normal";

    if (guardMode === "strict") {
      if (changePlan.protectedProjectFiles.length) {
        const restoreCommand = buildMaterializeCommand(
          String(config.get("materializeCommand") || DEFAULT_MATERIALIZE_COMMAND),
          changePlan.protectedProjectFiles
        );
        const restoreResult = await runParsedCommand(
          "materialize",
          restoreCommand,
          repoRoot,
          (stdout, stderr, code) => parseStageFailure(
            "SHELF_GENERATED_PROTECT",
            "Generated artifacts were edited directly and Shelf could not restore them.",
            stdout,
            stderr,
            code
          )
        );
        if (restoreResult.passed) {
          for (const projectFile of changePlan.protectedProjectFiles) {
            materializedProjects.add(projectFile);
          }
          suppressGeneratedEventsForProjects(repoRoot, changePlan.protectedProjectFiles);
        } else {
          issues.push(...restoreResult.errors);
        }
      }
      const unresolvedProtectedPaths = changePlan.protectedGeneratedPaths.filter(
        (relPath) => !workspaceGuard.resolveProjectFilePath(repoRoot, relPath)
      );
      for (const relPath of unresolvedProtectedPaths) {
        issues.push(normalizeIssue({
          message: "Generated artifacts were edited directly and Shelf could not determine how to restore them.",
          file: relPath,
          line: 1,
          column: 1,
          code: "SHELF_GENERATED_PROTECT",
        }));
      }
      return { issues, materializedProjects };
    }

    for (const relPath of changePlan.protectedGeneratedPaths) {
      issues.push(normalizeIssue({
        message: "Direct edits under projects/*/generated/* are forbidden. Change framework markdown or project.toml and re-materialize instead.",
        file: relPath,
        line: 1,
        column: 1,
        code: "SHELF_GENERATED_EDIT",
      }));
    }
    return { issues, materializedProjects };
  };

  const autoMaterializePendingProjects = async ({
    repoRoot,
    config,
    changePlan,
    materializedProjects,
  }) => {
    const issues = [];
    const pendingMaterializeProjects = changePlan.materializeProjects
      .filter((projectFile) => !materializedProjects.has(projectFile));

    if (!config.get("autoMaterialize") || !pendingMaterializeProjects.length) {
      return { issues, materializedProjects };
    }

    const materializeCommand = buildMaterializeCommand(
      String(config.get("materializeCommand") || DEFAULT_MATERIALIZE_COMMAND),
      pendingMaterializeProjects
    );
    const materializeResult = await runParsedCommand(
      "materialize",
      materializeCommand,
      repoRoot,
      (stdout, stderr, code) => parseStageFailure(
        "SHELF_MATERIALIZE",
        "Shelf auto-materialization failed.",
        stdout,
        stderr,
        code
      )
    );
    if (materializeResult.passed) {
      for (const projectFile of pendingMaterializeProjects) {
        materializedProjects.add(projectFile);
      }
      suppressGeneratedEventsForProjects(repoRoot, pendingMaterializeProjects);
    } else {
      issues.push(...materializeResult.errors);
    }
    return { issues, materializedProjects };
  };

  const readCorrespondenceIssues = (repoRoot) => {
    try {
      const snapshot = correspondenceRuntime.loadCorrespondenceSnapshot(repoRoot);
      if (!snapshot) {
        return [];
      }
      return correspondenceRuntime.buildValidationIssues(
        snapshot.payload.validation_summary,
        snapshot.payload.object_index || {}
      );
    } catch (error) {
      return [normalizeIssue({
        message: `Shelf could not load correspondence summary: ${String(error)}`,
        file: "projects/*/generated/canonical.json",
        line: 1,
        column: 1,
        code: "SHELF_CORRESPONDENCE",
      })];
    }
  };

  const runValidation = async (options = { mode: "change", triggerUris: [], notifyOnFail: false, source: "auto" }) => {
    const task = normalizeValidationOptions(options);
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      return;
    }
    const repoRoot = folder.uri.fsPath;

    if (!hasStandardsTree(repoRoot)) {
      validationActive = false;
      lastRepoRoot = repoRoot;
      lastRunIssues = [];
      lastFailureSignature = "";
      lastValidationAt = "";
      lastValidationPassed = null;
      lastChangeSummary = null;
      diagnostics.clear();
      setStatusDisabled(status, repoRoot);
      refreshSidebarHome();
      return;
    }
    validationActive = true;

    const config = getShelfConfig();
    const command = task.mode === "full"
      ? config.get("fullValidationCommand")
      : config.get("changeValidationCommand");

    if (!command || typeof command !== "string") {
      return;
    }
    const normalizedValidationCommand = validationRuntime.normalizeValidationCommand(command);
    if (normalizedValidationCommand !== String(command).trim()) {
      output.appendLine(
        `[validate] removed unsupported --json flag from canonical validation command: ${normalizedValidationCommand}`
      );
    }

    const showProgressStatus = task.source === "manual";
    if (showProgressStatus) {
      status.text = "$(sync~spin) Shelf validating";
      status.backgroundColor = new vscode.ThemeColor("statusBarItem.warningBackground");
      status.color = new vscode.ThemeColor("statusBarItem.warningForeground");
    }
    output.clear();
    pruneSuppressedGeneratedDirectories();

    const relPaths = task.triggerUris
      .map((uri) => workspaceGuard.normalizeRelPath(path.relative(repoRoot, uri.fsPath)))
      .filter(Boolean)
      .filter((relPath) => !isSuppressedGeneratedPath(relPath));

    const combinedIssues = [];
    const evidencePlan = await loadEvidenceChangePlan({
      repoRoot,
      relPaths,
    });
    combinedIssues.push(...evidencePlan.issues);
    const evidencePayload = evidencePlan.evidencePayload;
    const changePlan = evidencePlan.changePlan;
    const changeSummary = evidencePlan.changeSummary;

    const protectionResult = await protectGeneratedArtifacts({
      repoRoot,
      config,
      changePlan,
    });
    combinedIssues.push(...protectionResult.issues);

    const materializeResult = await autoMaterializePendingProjects({
      repoRoot,
      config,
      changePlan,
      materializedProjects: protectionResult.materializedProjects,
    });
    combinedIssues.push(...materializeResult.issues);

    if (config.get("runMypyOnPythonChanges") && changePlan.shouldRunMypy) {
      const mypyCommand = String(config.get("typeCheckCommand") || DEFAULT_TYPE_CHECK_COMMAND);
      const mypyResult = await runParsedCommand("mypy", mypyCommand, repoRoot, parseMypyResult);
      combinedIssues.push(...mypyResult.errors);
    }

    const parsed = await runParsedCommand("validate", normalizedValidationCommand, repoRoot, parseResult);
    combinedIssues.push(...parsed.errors);
    const correspondenceIssues = readCorrespondenceIssues(repoRoot);

    const combined = {
      passed: parsed.passed && combinedIssues.length === 0 && correspondenceIssues.length === 0,
      errors: correspondenceRuntime.mergeIssueLists(correspondenceIssues, combinedIssues)
    };

    lastRunIssues = combined.errors;
    lastRepoRoot = repoRoot;
    lastValidationAt = new Date().toISOString();
    lastValidationMode = task.mode;
    lastValidationPassed = combined.passed;
    lastChangeContext = changePlan.changeContext || null;
    lastChangeSummary = changeSummary;
    applyDiagnostics(combined, diagnostics, repoRoot, task.triggerUris[0] || null);
    output.appendLine(`[result] passed=${combined.passed} errors=${combined.errors.length}`);
    if (lastChangeContext && lastChangeContext.touchedNodes?.length) {
      output.appendLine(`[evidence] touched=${lastChangeContext.touchedNodes.join(", ")}`);
      output.appendLine(`[evidence] affected=${(lastChangeContext.affectedNodes || []).join(", ")}`);
    }

    if (combined.passed) {
      lastFailureSignature = "";
      statusController.refresh();
    } else {
      statusController.refresh();
      const shouldNotify = task.notifyOnFail || config.get("notifyOnAutoFail");
      if (shouldNotify && shouldNotifyFailure(combined.errors, lastFailureSignature)) {
        lastFailureSignature = signature(combined.errors);
        const action = await vscode.window.showErrorMessage(
          `Shelf guard failed (${combined.errors.length} issue(s)).`,
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
    }, readValidationTimingSettings().validationDebounceMs);
  };

  const openFrameworkTreeSource = async (repoRoot, relFile, line) => {
    if (!repoRoot || !relFile || typeof relFile !== "string") {
      return;
    }

    const normalizedRel = relFile.replace(/\\/g, "/").replace(/^\/+/, "");
    const absPath = path.resolve(repoRoot, normalizedRel);
    if (!fs.existsSync(absPath)) {
      vscode.window.showWarningMessage(`Shelf: source file not found: ${normalizedRel}`);
      return;
    }

    const lineNumber = Number.isFinite(Number(line)) ? Math.max(1, Number(line)) : 1;
    const doc = await vscode.workspace.openTextDocument(vscode.Uri.file(absPath));
    const editor = await vscode.window.showTextDocument(doc, { preview: false });
    const pos = new vscode.Position(lineNumber - 1, 0);
    editor.selection = new vscode.Selection(pos, pos);
    editor.revealRange(new vscode.Range(pos, pos), vscode.TextEditorRevealType.InCenter);
  };

  const treeTitleForKind = (kind) => kind === "evidence"
    ? "Shelf · Evidence Tree"
    : "Shelf · Framework Tree";

  const ensureTreePanel = (kind) => {
    if (!treePanel) {
      treePanel = vscode.window.createWebviewPanel(
        "shelfTreeView",
        treeTitleForKind(kind),
        vscode.ViewColumn.Active,
        {
          enableScripts: true,
          retainContextWhenHidden: true,
          localResourceRoots: [vscode.Uri.joinPath(context.extensionUri, "media")],
        }
      );
      treePanel.onDidDispose(() => {
        treePanel = null;
        treePanelKind = "framework";
        treePanelRepoRoot = "";
      });
      treePanel.webview.onDidReceiveMessage(async (message) => {
        if (!message || message.type !== "shelf.openSource") {
          return;
        }
        await openFrameworkTreeSource(
          treePanelRepoRoot || vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || "",
          String(message.file || ""),
          Number(message.line || 1)
        );
      });
    } else {
      treePanel.reveal(vscode.ViewColumn.Active, true);
    }
    treePanelKind = kind;
    treePanel.title = treeTitleForKind(kind);
    return treePanel;
  };

  const openTreeView = async (kind) => {
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      vscode.window.showWarningMessage("Shelf: no workspace is open.");
      return;
    }

    const repoRoot = folder.uri.fsPath;
    treePanelRepoRoot = repoRoot;
    const freshnessState = getCanonicalFreshnessState(repoRoot);

    if (kind === "evidence" && freshnessState.hasBlocking) {
      const freshnessDetail = describeCanonicalFreshness(freshnessState);
      const panel = ensureTreePanel(kind);
      panel.webview.html = buildTreeFallbackHtml(
        freshnessDetail
          ? `Evidence tree unavailable until canonical is fresh. ${freshnessDetail}`
          : "Evidence tree unavailable until canonical is fresh.",
        "Shelf: Run Codegen Preflight",
        treeTitleForKind(kind)
      );
      vscode.window.showWarningMessage(
        freshnessDetail
          ? `Shelf: evidence tree is unavailable until canonical is fresh. ${freshnessDetail}`
          : "Shelf: evidence tree is unavailable until canonical is fresh."
      );
      return;
    }

    const panel = ensureTreePanel(kind);
    try {
      const scriptPath = path.join(context.extensionPath, "media", "tree_view_bundle.js");
      const stylePath = path.join(context.extensionPath, "media", "tree_view.css");
      if (!fs.existsSync(scriptPath)) {
        panel.webview.html = buildTreeFallbackHtml(
          "Tree webview bundle is missing: media/tree_view_bundle.js",
          "npm run build:webview",
          treeTitleForKind(kind)
        );
        return;
      }
      if (!fs.existsSync(stylePath)) {
        panel.webview.html = buildTreeFallbackHtml(
          "Tree webview stylesheet is missing: media/tree_view.css",
          "Shelf: Run Codegen Preflight",
          treeTitleForKind(kind)
        );
        return;
      }

      const model = treeRuntimeModels.buildRuntimeTreeModel(repoRoot, kind);
      const scriptUri = panel.webview.asWebviewUri(vscode.Uri.file(scriptPath)).toString();
      const styleUri = panel.webview.asWebviewUri(vscode.Uri.file(stylePath)).toString();
      panel.webview.html = treeWebviewBridge.buildRuntimeTreeHtml({
        kind,
        model,
        layoutSettings: readTreeLayoutSettings(),
        viewSettings: readTreeViewSettings(),
        scriptUri,
        styleUri,
        cspSource: panel.webview.cspSource,
      });
    } catch (error) {
      panel.webview.html = buildTreeFallbackHtml(
        `Failed to render ${kind === "evidence" ? "evidence" : "framework"} tree runtime projection: ${String(error)}`,
        "Shelf: Run Codegen Preflight",
        treeTitleForKind(kind)
      );
    }
  };

  const openFrameworkTree = async () => {
    await openTreeView("framework");
  };

  const openEvidenceTree = async () => {
    await openTreeView("evidence");
  };

  const clearShelfDiagnosticsForUri = (uri) => {
    if (!uri || !uri.fsPath) {
      return;
    }
    diagnostics.delete(uri);
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      return;
    }
    const repoRoot = folder.uri.fsPath;
    const relPath = workspaceGuard.normalizeRelPath(path.relative(repoRoot, uri.fsPath));
    if (!relPath) {
      return;
    }
    lastRunIssues = lastRunIssues.filter(
      (issue) => workspaceGuard.normalizeRelPath(issue.file || "") !== relPath
    );
    if (!lastRunIssues.length && dirtyWatchedFiles.size) {
      lastValidationPassed = null;
    }
    refreshStatusFromCurrentState();
    refreshSidebarHome();
  };

  const renderSidebarHome = () => {
    const defaultActionItems = [
      {
        action: "startGovernedTask",
        label: "启动受控任务会话",
        description: "先做需求到 framework 的显式映射，通过后再改实现层代码。",
        tone: "primary"
      },
      {
        action: "showGovernedTaskSession",
        label: "查看当前门禁会话",
        description: "查看当前会话的 module/boundary/exact 映射结果。",
        tone: "ghost"
      },
      {
        action: "clearGovernedTaskSession",
        label: "清空门禁会话",
        description: "清空当前授权会话，恢复到默认阻断状态。",
        tone: "ghost"
      },
      {
        action: "openTree",
        label: "打开框架树",
        description: "默认查看框架文档树，不把代码节点混进主视图。",
        tone: "primary"
      },
      {
        action: "refreshTree",
        label: "刷新框架树视图",
        description: "重新计算并渲染当前框架树运行时投影。",
        tone: "ghost"
      },
      {
        action: "openEvidenceTree",
        label: "打开证据树",
        description: "需要排障或看受影响闭包时，再打开工作区证据树。",
        tone: "ghost"
      },
      {
        action: "refreshEvidenceTree",
        label: "刷新证据树视图",
        description: "重新计算并渲染当前证据树运行时投影。",
        tone: "ghost"
      },
      {
        action: "validate",
        label: "执行 canonical 校验",
        description: "运行完整 canonical validation。",
        tone: "ghost"
      },
      {
        action: "codegenPreflight",
        label: "生成前预检",
        description: "先物化再跑完整校验，确认框架链路闭合后再继续生成代码。",
        tone: "ghost"
      },
      {
        action: "publishDraft",
        label: "发布当前框架草稿",
        description: "把 framework_drafts 下的当前草稿提升到正式 framework 树。",
        tone: "ghost"
      },
      {
        action: "showIssues",
        label: "查看问题列表",
        description: "打开 Problems 或快速跳转到问题位置。",
        tone: "ghost"
      },
      {
        action: "openLog",
        label: "打开运行日志",
        description: "查看最近一次命令输出与错误详情。",
        tone: "ghost"
      }
    ];

    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      return buildSidebarHomeHtml({
        workspace: "No workspace",
        heroTone: "unknown",
        heroStatus: "等待工作区",
        heroSummary: "打开仓库后，这里会优先显示框架树入口，同时保留证据树守卫和问题跳转。",
        treePath: "runtime projection (in-memory)",
        validationStatus: "Unavailable",
        issueSummary: "No workspace",
        treeStatus: "Unknown",
        standardsStatus: "Unknown",
        lastValidation: "Not available",
        actionItems: defaultActionItems,
        healthItems: [
          {
            label: "规范总纲",
            value: "未知",
            tone: "unknown",
            note: STANDARDS_TREE_FILE
          },
          {
        label: "框架树视图",
            value: "未知",
            tone: "unknown",
            note: "运行时投影（不持久化）"
          },
          {
        label: "证据树视图",
            value: "未知",
            tone: "unknown",
            note: "运行时投影（不持久化）"
          },
          {
            label: "守卫模式",
            value: "未知",
            tone: "unknown",
            note: "打开工作区后读取 shelf.guardMode。"
          },
          {
            label: "Git Hooks",
            value: "未知",
            tone: "unknown",
            note: "打开工作区后检查 .githooks 是否已启用。"
          },
          {
            label: "会话门禁",
            value: "未知",
            tone: "unknown",
            note: "打开工作区后读取 shelf.intentGate* 设置并展示会话状态。"
          },
          {
            label: "严格校验",
            value: "等待工作区",
            tone: "unknown",
            note: "打开仓库后自动判断是否启用。"
          },
          {
            label: "最近结果",
            value: "未运行",
            tone: "unknown",
            note: "本会话尚未启动校验。"
          }
        ],
        issueItems: [],
        issueEmptyText: "打开工作区后，这里会显示校验问题预览和快速跳转入口。",
        issueOverflow: 0,
        changeItems: [],
        changeEmptyText: "打开工作区后，这里会显示最近一次变更命中的证据树节点闭包。",
        changeOverflow: 0,
        calloutTone: "unknown",
        calloutTitle: "从工作区开始",
        calloutBody: "Shelf 侧边栏不是占位区。打开仓库后，它会变成树图入口、校验面板和问题导航工作台。"
      });
    }

    const repoRoot = folder.uri.fsPath;
    const config = getShelfConfig();
    const intentGateSettings = readIntentGateSettings();
    const activeIntentSession = ensureIntentGateSession(intentGateSettings);
    const validationTriggerMode = getValidationTriggerMode();
    const standardsExists = hasStandardsTree(repoRoot);
    const validationEnabled = standardsExists && validationActive;
    const freshnessState = getCanonicalFreshnessState(repoRoot);
    const freshnessDetail = describeCanonicalFreshness(freshnessState);
    const frameworkTreeReady = fs.existsSync(path.join(repoRoot, "framework"));
    const evidenceTreeReady = !freshnessState.hasBlocking;
    const guardMode = config.get("guardMode") === "strict" ? "strict" : "normal";
    const hasIntentGateTemporaryBypass = intentGateSettings.temporaryBypasses.length > 0;
    const isSaveGuardBypassed = isIntentGateTemporaryBypassEnabled(intentGateSettings, "save_guard");
    const intentGateStatus = !intentGateSettings.enabled
      ? "Disabled"
      : (hasIntentGateTemporaryBypass ? "Bypass" : (activeIntentSession ? "Granted" : "Required"));
    const intentGateTone = !intentGateSettings.enabled
      ? "unknown"
      : (hasIntentGateTemporaryBypass ? "unknown" : (activeIntentSession ? "ok" : "error"));
    const intentGateNote = !intentGateSettings.enabled
      ? "shelf.intentGateEnabled = false"
      : (
        hasIntentGateTemporaryBypass
          ? `temporary bypass: ${intentGateSettings.temporaryBypasses.join(", ")}`
          : (
            activeIntentSession
              ? `${activeIntentSession.analysis.mappings.length} mappings · ${new Date(activeIntentSession.createdAt).toLocaleString()}`
              : "先执行 “Shelf: Start Governed Task”，确认映射后再改实现层文件。"
          )
      );
    const issueCount = lastRunIssues.length;
    const issueSummary = validationEnabled
      ? (lastValidationPassed === null ? "Not run yet" : (issueCount ? `${issueCount} issue(s)` : "No issues"))
      : "Validation disabled";
    const lastValidation = lastValidationAt
      ? `${lastValidationMode === "full" ? "Full" : "Change"} · ${new Date(lastValidationAt).toLocaleString()}`
      : "Not run in this session";
    const issueItems = lastRunIssues.slice(0, 3).map((issue, index) => {
      const recognizedCode = normalizeFrameworkRuleCode(issue.code);
      return {
        index,
        code: recognizedCode || String(issue.code || "ARCHSYNC"),
        hint: recognizedCode ? frameworkRuleHint(recognizedCode) : "",
        message: issue.message || "Shelf validation issue",
        location: issue.file
          ? `${issue.file}:${Number(issue.line || 1)}`
          : `line ${Number(issue.line || 1)}`
      };
    });
    const touchedChangeItems = (lastChangeSummary?.touched || []).map((item) => ({
      kind: "Touched",
      label: item.label || item.id,
      detail: item.layer || "",
      location: item.file || item.id || "",
    }));
    const affectedChangeItems = (lastChangeSummary?.affected || []).map((item) => ({
      kind: "Affected",
      label: item.label || item.id,
      detail: item.layer || "",
      location: item.file || item.id || "",
    }));
    const changeItems = [...touchedChangeItems, ...affectedChangeItems].slice(0, 6);
    const changeOverflow = Math.max(
      0,
      (lastChangeSummary?.touchedCount || 0) + (lastChangeSummary?.affectedCount || 0) - changeItems.length
    );
    const changeSummary = lastChangeSummary
      ? `${lastChangeSummary.touchedCount || 0} touched / ${lastChangeSummary.affectedCount || 0} affected`
      : "No recent node closure";

    let heroTone = "unknown";
    let heroStatus = "等待首次校验";
    let heroSummary = "先执行一次完整校验，把树图状态和问题列表都热起来。";
    let calloutTone = "unknown";
    let calloutTitle = "建议先跑一次完整校验";
    let calloutBody = "这样能立即得到最新问题摘要，并确认 canonical 守卫是否正常工作。";
    let calloutAction = {
      action: "validate",
      label: "现在执行校验"
    };

    if (!standardsExists) {
      heroTone = "error";
      heroStatus = "严格守卫未启用";
      heroSummary = `当前工作区缺少 ${STANDARDS_TREE_FILE}，Shelf 会停用证据树守卫，但仍可打开框架树。`;
      calloutTone = "error";
      calloutTitle = "先补齐规范入口";
      calloutBody = "没有规范总纲时，侧边栏仍可作为框架树入口，但 canonical 校验问题不会自动汇总。";
      calloutAction = {
        action: "openStandards",
        label: "打开规范总纲路径"
      };
    } else if (freshnessState.hasBlocking) {
      heroTone = "error";
      heroStatus = "canonical 已过期";
      heroSummary = "正式跨层导航和证据树入口已收紧。先物化并重新校验，再继续信任当前主链结果。";
      calloutTone = "error";
      calloutTitle = "先刷新 canonical";
      calloutBody = freshnessDetail
        ? `${freshnessDetail}。先执行物化与完整校验，再继续打开证据树或使用正式跨层跳转。`
        : "当前 canonical 不是 fresh 状态。先执行物化与完整校验，再继续打开证据树或使用正式跨层跳转。";
      calloutAction = {
        action: "codegenPreflight",
        label: "先物化并校验"
      };
    } else if (lastValidationPassed === false) {
      heroTone = "error";
      heroStatus = `${issueCount} 个问题待处理`;
      heroSummary = "侧边栏现在会直接预览问题，并支持点进具体文件和行号。";
      calloutTone = "error";
      calloutTitle = "先处理校验问题";
      calloutBody = "修复这些问题前，不适合继续推送或发布。可以先点下面的问题卡片，或打开完整问题列表。";
      calloutAction = {
        action: "showIssues",
        label: "打开完整问题列表"
      };
    } else if (lastValidationPassed === true) {
      heroTone = "ok";
      heroStatus = "工作区状态正常";
      heroSummary = "框架树入口和证据树守卫都已接通，侧边栏现在就是你的快速入口。";
      calloutTone = "ok";
      calloutTitle = "继续查看框架树";
      calloutBody = "一般先打开框架文档树；只有需要追踪代码影响闭包时，再切到证据树。";
      calloutAction = {
        action: "openTree",
        label: "打开框架树"
      };
    }

    if (gitHooksReady === false) {
      calloutTone = "error";
      calloutTitle = "补齐 Git Hooks";
      calloutBody = "当前仓库还没有启用 .githooks，pre-push 严格校验可以被绕开。先安装 hooks，再继续协作。";
      calloutAction = {
        action: "installHooks",
        label: "安装 Git Hooks"
      };
    } else if (intentGateSettings.enabled && !isSaveGuardBypassed && !activeIntentSession) {
      calloutTone = "error";
      calloutTitle = "先开启受控任务会话";
      calloutBody = "实现层修改前，先执行需求到 framework 映射门禁。未授权会话下，受保护路径保存会被阻断或回滚。";
      calloutAction = {
        action: "startGovernedTask",
        label: "启动受控任务会话"
      };
    }

    const healthItems = [
      {
        label: "规范总纲",
        value: standardsExists ? "已检测" : "缺失",
        tone: standardsExists ? "ok" : "error",
        note: STANDARDS_TREE_FILE
      },
      {
        label: "框架树视图",
        value: frameworkTreeReady ? "就绪" : "缺失",
        tone: frameworkTreeReady ? "ok" : "error",
        note: frameworkTreeReady
          ? "运行时投影（基于 framework 作者源，不持久化）。"
          : "缺少 framework/ 目录，无法构建作者视图。"
      },
      {
        label: "证据树视图",
        value: evidenceTreeReady ? "就绪" : "受阻",
        tone: evidenceTreeReady ? "ok" : "error",
        note: evidenceTreeReady
          ? "运行时投影（基于 canonical，不持久化）。"
          : "canonical 不是 fresh 状态，正式证据树已收紧。"
      },
      {
        label: "Canonical Freshness",
        value: freshnessState.hasBlocking ? "Stale" : "Fresh",
        tone: freshnessState.hasBlocking ? "error" : "ok",
        note: freshnessState.hasBlocking
          ? (freshnessDetail || "先 materialize / validate，再继续信任正式跨层结果。")
          : "当前正式跨层跳转与证据树可继续信任 canonical。"
      },
      {
        label: "守卫模式",
        value: guardMode === "strict" ? "Strict" : "Normal",
        tone: guardMode === "strict" ? "ok" : "unknown",
        note: guardMode === "strict"
          ? "发现 generated 直改时会自动回滚并重物化。"
          : "发现 generated 直改时会报告问题，但不会强制回滚。"
      },
      {
        label: "Git Hooks",
        value: gitHooksReady === null ? "未检查" : (gitHooksReady ? "就绪" : "缺失"),
        tone: gitHooksReady === null ? "unknown" : (gitHooksReady ? "ok" : "error"),
        note: gitHooksReady
          ? gitHooksDetail
          : `需要指向 .githooks。当前状态：${gitHooksDetail}`
      },
      {
        label: "会话门禁",
        value: intentGateStatus,
        tone: intentGateTone,
        note: intentGateNote
      },
      {
        label: "严格校验",
        value: validationEnabled ? "启用" : "停用",
        tone: validationEnabled ? "ok" : "error",
        note: validationEnabled
          ? (
            validationTriggerMode === "manual"
              ? "当前为手动模式，只在显式命令时检查。"
              : (
                validationTriggerMode === "save"
                  ? "当前为保存模式，只在保存 watched 文件时检查。"
                  : "当前为全自动模式，保存、命令和工作区事件都会参与检查。"
              )
          )
          : "补齐规范总纲后会自动恢复。"
      },
      {
        label: "最近结果",
        value: lastValidationPassed === null
          ? "未运行"
          : (lastValidationPassed ? "通过" : `${issueCount} 个问题`),
        tone: lastValidationPassed === null
          ? "unknown"
          : (lastValidationPassed ? "ok" : "error"),
        note: lastValidation
      }
    ];

    const actionItems = [...defaultActionItems];
    if (!standardsExists) {
      actionItems.unshift({
        action: "openStandards",
        label: "打开规范总纲路径",
        description: "检查缺失的规范入口，恢复严格校验。",
        tone: "ghost"
      });
    }
    if (gitHooksReady === false) {
      actionItems.unshift({
        action: "installHooks",
        label: "安装 Git Hooks",
        description: "启用 .githooks，确保 pre-push 校验不能被跳过。",
        tone: "primary"
      });
    }

    let issueEmptyText = "当前没有可展示的问题。";
    if (!validationEnabled) {
      issueEmptyText = "当前工作区的 canonical 守卫已停用，所以这里不会自动汇总问题。";
    } else if (lastValidationPassed === null) {
      issueEmptyText = "本会话尚未执行校验。先跑一次完整校验，侧边栏才能显示最新问题摘要。";
    } else if (lastValidationPassed === true) {
      issueEmptyText = "当前没有可展示的问题，Shelf canonical 守卫状态正常。";
    }

    return buildSidebarHomeHtml({
      workspace: path.basename(repoRoot),
      heroTone,
      heroStatus,
      heroSummary,
      treePath: "runtime projection (in-memory)",
      validationStatus: validationEnabled ? "Enabled" : "Disabled",
      issueSummary,
      treeStatus: frameworkTreeReady ? "Ready (runtime)" : "Missing framework source",
      standardsStatus: standardsExists ? "Ready" : "Missing",
      lastValidation,
      actionItems,
      healthItems,
      issueItems,
      issueEmptyText,
      issueOverflow: Math.max(0, lastRunIssues.length - issueItems.length),
      changeItems,
      changeEmptyText: "本会话还没有可展示的节点闭包。执行一次校验后，这里会显示最近变更命中的证据树节点。",
      changeOverflow,
      changeSummary,
      calloutTone,
      calloutTitle,
      calloutBody,
      calloutAction,
      lastValidationTone: lastValidationPassed === null
        ? "unknown"
        : (lastValidationPassed ? "ok" : "error")
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

        if (message.type === "shelf.sidebar.openTree") {
          await openFrameworkTree();
          return;
        }
        if (message.type === "shelf.sidebar.startGovernedTask") {
          await vscode.commands.executeCommand("shelf.startGovernedTask");
          return;
        }
        if (message.type === "shelf.sidebar.showGovernedTaskSession") {
          await vscode.commands.executeCommand("shelf.showGovernedTaskSession");
          return;
        }
        if (message.type === "shelf.sidebar.clearGovernedTaskSession") {
          await vscode.commands.executeCommand("shelf.clearGovernedTaskSession");
          return;
        }
        if (message.type === "shelf.sidebar.refreshTree") {
          await vscode.commands.executeCommand("shelf.refreshFrameworkTree");
          return;
        }
        if (message.type === "shelf.sidebar.openEvidenceTree") {
          await openEvidenceTree();
          return;
        }
        if (message.type === "shelf.sidebar.refreshEvidenceTree") {
          await vscode.commands.executeCommand("shelf.refreshEvidenceTree");
          return;
        }
        if (message.type === "shelf.sidebar.validate") {
          requestManualValidation();
          return;
        }
        if (message.type === "shelf.sidebar.codegenPreflight") {
          await vscode.commands.executeCommand("shelf.codegenPreflight");
          return;
        }
        if (message.type === "shelf.sidebar.publishDraft") {
          await vscode.commands.executeCommand("shelf.publishFrameworkDraft");
          return;
        }
        if (message.type === "shelf.sidebar.showIssues") {
          await vscode.commands.executeCommand("shelf.showIssues");
          return;
        }
        if (message.type === "shelf.sidebar.openLog") {
          output.show(true);
          return;
        }
        if (message.type === "shelf.sidebar.openStandards") {
          const repoRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
          if (repoRoot) {
            await openFrameworkTreeSource(repoRoot, STANDARDS_TREE_FILE, 1);
          }
          return;
        }
        if (message.type === "shelf.sidebar.installHooks") {
          await vscode.commands.executeCommand("shelf.installGitHooks");
          return;
        }
        if (message.type === "shelf.sidebar.openIssue") {
          const index = Number(message.index);
          if (Number.isInteger(index) && index >= 0 && index < lastRunIssues.length && lastRepoRoot) {
            await revealIssue(lastRunIssues[index], lastRepoRoot);
          }
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

  const frameworkDefinitionDisposable = vscode.languages.registerDefinitionProvider(
    { language: "markdown", scheme: "file" },
    {
      provideDefinition(document, position) {
        const folder = vscode.workspace.getWorkspaceFolder(document.uri);
        if (!folder) {
          return null;
        }

        const repoRoot = folder.uri.fsPath;
        if (!frameworkNavigation.isFrameworkMarkdownFile(document.uri.fsPath, repoRoot)) {
          return null;
        }

        const allowCanonicalProjection = getCanonicalFreshnessState(repoRoot).dirtySourceRelPaths.length === 0;
        const target = frameworkNavigation.resolveDefinitionTarget({
          repoRoot,
          filePath: document.uri.fsPath,
          text: document.getText(),
          line: position.line,
          character: position.character,
          allowCanonicalProjection,
        });
        if (!target) {
          return null;
        }

        const targetUri = vscode.Uri.file(target.filePath);
        const start = new vscode.Position(target.line, target.character);
        const end = new vscode.Position(target.line, target.character + Math.max(1, target.length || 1));
        return new vscode.Location(targetUri, new vscode.Range(start, end));
      }
    }
  );

  const configToCodeDefinitionDisposable = vscode.languages.registerDefinitionProvider(
    { language: "toml", scheme: "file" },
    {
      provideDefinition(document, position) {
        const folder = vscode.workspace.getWorkspaceFolder(document.uri);
        if (!folder) {
          return null;
        }
        const repoRoot = folder.uri.fsPath;
        const target = configNavigation.resolveConfigToCodeTarget({
          repoRoot,
          filePath: document.uri.fsPath,
          text: document.getText(),
          line: position.line,
          character: position.character,
        });
        if (!target) {
          return null;
        }
        const targetUri = vscode.Uri.file(target.filePath);
        const start = new vscode.Position(target.line, target.character);
        const end = new vscode.Position(target.line, target.character + Math.max(1, target.length || 1));
        return new vscode.Location(targetUri, new vscode.Range(start, end));
      }
    }
  );

  const frameworkHoverDisposable = vscode.languages.registerHoverProvider(
    { language: "markdown", scheme: "file" },
    {
      provideHover(document, position) {
        const folder = vscode.workspace.getWorkspaceFolder(document.uri);
        if (!folder) {
          return null;
        }

        const repoRoot = folder.uri.fsPath;
        if (!frameworkNavigation.isFrameworkMarkdownFile(document.uri.fsPath, repoRoot)) {
          return null;
        }

        const allowCanonicalProjection = getCanonicalFreshnessState(repoRoot).dirtySourceRelPaths.length === 0;
        const target = frameworkNavigation.resolveHoverTarget({
          repoRoot,
          filePath: document.uri.fsPath,
          text: document.getText(),
          line: position.line,
          character: position.character,
          allowCanonicalProjection,
        });
        if (!target) {
          return null;
        }

        const start = new vscode.Position(position.line, target.start);
        const end = new vscode.Position(position.line, target.end);
        return new vscode.Hover(new vscode.MarkdownString(target.markdown), new vscode.Range(start, end));
      }
    }
  );

  const frameworkReferenceDisposable = vscode.languages.registerReferenceProvider(
    { language: "markdown", scheme: "file" },
    {
      provideReferences(document, position) {
        const folder = vscode.workspace.getWorkspaceFolder(document.uri);
        if (!folder) {
          return [];
        }

        const repoRoot = folder.uri.fsPath;
        if (!frameworkNavigation.isFrameworkMarkdownFile(document.uri.fsPath, repoRoot)) {
          return [];
        }

        const allowCanonicalProjection = getCanonicalFreshnessState(repoRoot).dirtySourceRelPaths.length === 0;
        const targets = frameworkNavigation.resolveReferenceTargets({
          repoRoot,
          filePath: document.uri.fsPath,
          text: document.getText(),
          line: position.line,
          character: position.character,
          allowCanonicalProjection,
        });
        return targets.map((target) => {
          const targetUri = vscode.Uri.file(target.filePath);
          const start = new vscode.Position(target.line, target.character);
          const end = new vscode.Position(target.line, target.character + Math.max(1, target.length || 1));
          return new vscode.Location(targetUri, new vscode.Range(start, end));
        });
      }
    }
  );

  const frameworkCompletionDisposable = vscode.languages.registerCompletionItemProvider(
    { language: "markdown", scheme: "file" },
    {
      provideCompletionItems(document, position) {
        const folder = vscode.workspace.getWorkspaceFolder(document.uri);
        const repoRoot = folder?.uri.fsPath || "";
        const isFrameworkFile = repoRoot
          ? frameworkNavigation.isFrameworkMarkdownFile(document.uri.fsPath, repoRoot)
          : false;
        const lineText = document.lineAt(position.line).text;
        const linePrefix = lineText.slice(0, position.character);
        const wordRange = document.getWordRangeAtPosition(position, /[@A-Za-z_][A-Za-z0-9_.-]*/);
        const wordPrefix = wordRange
          ? document.getText(new vscode.Range(wordRange.start, position))
          : "";

        const entries = frameworkCompletion.getFrameworkCompletionEntries(
          linePrefix,
          wordPrefix,
          isFrameworkFile
        );
        if (!entries.length) {
          return undefined;
        }

        return entries.map((entry, index) => {
          const item = new vscode.CompletionItem(
            entry.label,
            vscode.CompletionItemKind.Snippet
          );
          item.detail = entry.detail;
          item.documentation = new vscode.MarkdownString(entry.documentation);
          item.insertText = new vscode.SnippetString(entry.insertText);
          item.insertTextFormat = vscode.InsertTextFormat.Snippet;
          item.sortText = String(index).padStart(3, "0");
          item.filterText = entry.label;
          return item;
        });
      }
    },
    "@",
    "#",
    "-",
    "`",
    "."
  );

  const startGovernedTaskDisposable = vscode.commands.registerCommand(
    "shelf.startGovernedTask",
    async () => {
      const folder = vscode.workspace.workspaceFolders?.[0];
      if (!folder) {
        vscode.window.showWarningMessage("Shelf: no workspace is open.");
        return;
      }

      const settings = readIntentGateSettings();
      if (!settings.enabled) {
        vscode.window.showWarningMessage("Shelf: intent gate is disabled. Enable `shelf.intentGateEnabled` first.");
        return;
      }

      const intentText = await vscode.window.showInputBox({
        title: "Shelf Governed Task",
        prompt: "Describe the requested change. Shelf will map it to framework paths before code edits.",
        placeHolder: "例如：给知识库聊天页增加 @ 文档引用，并新增动态图展示页",
        ignoreFocusOut: true,
      });
      if (!intentText) {
        return;
      }

      const result = await grantIntentGateSession({
        repoRoot: folder.uri.fsPath,
        intentText,
      });
      if (!result.passed) {
        vscode.window.showErrorMessage(`Shelf intent gate denied: ${result.message}`);
        return;
      }

      const preview = result.analysis.mappings.slice(0, 2)
        .map((item) => `${item.moduleId}/${item.boundaryId}`)
        .join(" | ");
      vscode.window.showInformationMessage(
        `Shelf governed task granted (${result.analysis.mappings.length} mappings): ${preview}`
      );
    }
  );

  const showGovernedTaskSessionDisposable = vscode.commands.registerCommand(
    "shelf.showGovernedTaskSession",
    async () => {
      const settings = readIntentGateSettings();
      const session = ensureIntentGateSession(settings);
      if (!session) {
        vscode.window.showInformationMessage("Shelf: no active governed task session.");
        return;
      }
      output.appendLine("[intent-gate] active session");
      output.appendLine(`- id: ${session.id}`);
      output.appendLine(`- createdAt: ${session.createdAt}`);
      output.appendLine(`- intent: ${session.intentText}`);
      output.appendLine(
        `- temporary bypasses: ${settings.temporaryBypasses.length ? settings.temporaryBypasses.join(", ") : "none"}`
      );
      output.appendLine(intentGate.formatIntentMappingSummary(session.analysis));
      output.show(true);
    }
  );

  const clearGovernedTaskSessionDisposable = vscode.commands.registerCommand(
    "shelf.clearGovernedTaskSession",
    async () => {
      clearIntentGateSession("manual clear");
      refreshSidebarHome();
      vscode.window.showInformationMessage("Shelf: governed task session cleared.");
    }
  );

  const validateNowDisposable = vscode.commands.registerCommand("shelf.validateNow", async () => {
    requestManualValidation();
  });

  const codegenPreflightDisposable = vscode.commands.registerCommand("shelf.codegenPreflight", async () => {
    await runCodegenPreflight();
  });

  const publishFrameworkDraftDisposable = vscode.commands.registerCommand(
    "shelf.publishFrameworkDraft",
    async () => {
      const activeDraft = activeFrameworkDraftFile();
      if (!activeDraft) {
        vscode.window.showWarningMessage(
          "Shelf: open a markdown file under framework_drafts/<framework>/ before publishing."
        );
        return;
      }

      const result = await runParsedCommand(
        "publish-framework-draft",
        buildPublishFrameworkDraftCommand(activeDraft.relPath),
        activeDraft.repoRoot,
        (stdout, stderr, code) => parseStageFailure(
          "SHELF_PUBLISH_FRAMEWORK_DRAFT",
          "Shelf failed to publish the current framework draft.",
          stdout,
          stderr,
          code
        )
      );
      if (!result.passed) {
        const action = await vscode.window.showErrorMessage(
          "Shelf: failed to publish the current framework draft.",
          "Open Log"
        );
        if (action === "Open Log") {
          output.show(true);
        }
        return;
      }

      const doc = await vscode.workspace.openTextDocument(vscode.Uri.file(activeDraft.publishedAbsPath));
      await vscode.window.showTextDocument(doc, { preview: false });
      scheduleValidation({
        mode: "full",
        triggerUris: [vscode.Uri.file(activeDraft.publishedAbsPath)],
        notifyOnFail: true,
        source: "manual"
      });
      vscode.window.showInformationMessage(
        `Shelf: published ${workspaceGuard.normalizeRelPath(activeDraft.publishedRelPath)}`
      );
    }
  );

  const installGitHooksDisposable = vscode.commands.registerCommand("shelf.installGitHooks", async () => {
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      vscode.window.showWarningMessage("Shelf: no workspace is open.");
      return;
    }

    const repoRoot = folder.uri.fsPath;
    const result = await runParsedCommand(
      "git-hooks",
      DEFAULT_INSTALL_GIT_HOOKS_COMMAND,
      repoRoot,
      (stdout, stderr, code) => parseStageFailure(
        "SHELF_GIT_HOOKS",
        "Shelf failed to install the repository git hooks.",
        stdout,
        stderr,
        code
      )
    );

    if (result.passed) {
      vscode.window.showInformationMessage("Shelf: repository git hooks installed.");
    } else {
      const action = await vscode.window.showErrorMessage(
        "Shelf: failed to install repository git hooks.",
        "Open Log"
      );
      if (action === "Open Log") {
        output.show(true);
      }
    }
    await refreshGitHookStatus({ promptIfMissing: false });
  });

  const insertFrameworkTemplateDisposable = vscode.commands.registerCommand(
    "shelf.insertFrameworkModuleTemplate",
    async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        vscode.window.showWarningMessage("Shelf: no active editor for framework template insertion.");
        return;
      }

      if (editor.document.languageId !== "markdown") {
        vscode.window.showWarningMessage("Shelf: framework module template can only be inserted into Markdown files.");
        return;
      }

      let snippetText = "";
      try {
        snippetText = frameworkCompletion.getFrameworkTemplateSnippetText();
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        output.appendLine(`[template] ${message}`);
        vscode.window.showErrorMessage("Shelf: failed to load the @framework module template.");
        return;
      }

      const inserted = await editor.insertSnippet(
        new vscode.SnippetString(snippetText),
        editor.selections
      );
      if (!inserted) {
        vscode.window.showWarningMessage("Shelf: framework module template insertion was cancelled.");
      }
    }
  );

  const showIssuesDisposable = vscode.commands.registerCommand("shelf.showIssues", async () => {
    if (!validationActive && lastRepoRoot) {
      vscode.window.showInformationMessage(
        `Shelf validation guard is disabled: missing ${STANDARDS_TREE_FILE} in this workspace.`
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
      title: `Shelf Mapping Issues (${lastRunIssues.length})`,
      placeHolder: "Select an issue to jump to its location"
    });

    if (selected && lastRepoRoot) {
      await revealIssue(selected.issue, lastRepoRoot);
    }
  });

  const openFrameworkTreeDisposable = vscode.commands.registerCommand("shelf.openFrameworkTree", async () => {
    await openFrameworkTree();
  });

  const refreshFrameworkTreeDisposable = vscode.commands.registerCommand("shelf.refreshFrameworkTree", async () => {
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      vscode.window.showWarningMessage("Shelf: no workspace is open.");
      return;
    }
    await openFrameworkTree();
    vscode.window.showInformationMessage("Shelf: framework tree runtime projection refreshed.");
  });

  const openEvidenceTreeDisposable = vscode.commands.registerCommand("shelf.openEvidenceTree", async () => {
    await openEvidenceTree();
  });

  const refreshEvidenceTreeDisposable = vscode.commands.registerCommand("shelf.refreshEvidenceTree", async () => {
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      vscode.window.showWarningMessage("Shelf: no workspace is open.");
      return;
    }

    const repoRoot = folder.uri.fsPath;
    const freshnessState = getCanonicalFreshnessState(repoRoot);

    if (freshnessState.hasBlocking) {
      const freshnessDetail = describeCanonicalFreshness(freshnessState);
      const panel = ensureTreePanel("evidence");
      panel.webview.html = buildTreeFallbackHtml(
        freshnessDetail
          ? `Evidence tree unavailable until canonical is fresh. ${freshnessDetail}`
          : "Evidence tree unavailable until canonical is fresh.",
        "Shelf: Run Codegen Preflight",
        treeTitleForKind("evidence")
      );
      vscode.window.showWarningMessage(
        freshnessDetail
          ? `Shelf: refresh evidence tree is blocked until canonical is fresh. ${freshnessDetail}`
          : "Shelf: refresh evidence tree is blocked until canonical is fresh."
      );
      return;
    }

    await openEvidenceTree();
    vscode.window.showInformationMessage("Shelf: evidence tree runtime projection refreshed.");
  });

  const configurationDisposable = vscode.workspace.onDidChangeConfiguration(async (event) => {
    const affectsIntentGate = INTENT_GATE_SETTING_KEYS.some((key) => event.affectsConfiguration(key));
    const affectsTreeView = TREE_WEBVIEW_SETTING_KEYS.some((key) => event.affectsConfiguration(key));
    if (!affectsIntentGate && !affectsTreeView) {
      return;
    }
    await handleRuntimeSettingSourcesChanged({
      reason: "VSCode shelf settings update",
      refreshTree: affectsTreeView
    });
  });

  const saveDisposable = vscode.workspace.onDidSaveTextDocument(async (doc) => {
    const gateDecision = await enforceIntentGateOnSave(doc);
    if (!gateDecision.allow) {
      return;
    }
    const config = getShelfConfig();
    if (!config.get("enableOnSave") || !shouldRunValidationTrigger("save")) {
      return;
    }

    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      return;
    }

    const rel = workspaceGuard.normalizeRelPath(path.relative(folder.uri.fsPath, doc.uri.fsPath));
    if (!workspaceGuard.isWatchedPath(rel) || isSuppressedGeneratedPath(rel)) {
      return;
    }

    dirtyWatchedFiles.delete(doc.uri.fsPath);
    scheduleValidation({ mode: "change", triggerUris: [doc.uri], notifyOnFail: false, source: "save" });
  });

  const changeDisposable = vscode.workspace.onDidChangeTextDocument((event) => {
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder || !event.document?.uri?.fsPath) {
      return;
    }
    const relPath = workspaceGuard.normalizeRelPath(path.relative(folder.uri.fsPath, event.document.uri.fsPath));
    if (!workspaceGuard.isWatchedPath(relPath) || isSuppressedGeneratedPath(relPath)) {
      return;
    }

    const intentSettings = readIntentGateSettings();
    if (
      intentSettings.enabled
      && !isIntentGateTemporaryBypassEnabled(intentSettings, "save_guard")
      && isIntentGateGuardedPath(folder.uri.fsPath, event.document.uri.fsPath, intentSettings)
    ) {
      const fsPath = event.document.uri.fsPath;
      if (event.document.isDirty && !guardedBaselineByPath.has(fsPath) && !restoringGuardedFiles.has(fsPath)) {
        try {
          guardedBaselineByPath.set(fsPath, fs.readFileSync(fsPath, "utf8"));
        } catch (error) {
          output.appendLine(`[intent-gate] baseline snapshot failed for ${relPath}: ${String(error)}`);
        }
      }
      if (!event.document.isDirty) {
        guardedBaselineByPath.delete(fsPath);
      }
    }

    if (event.document.isDirty) {
      dirtyWatchedFiles.add(event.document.uri.fsPath);
      clearShelfDiagnosticsForUri(event.document.uri);
      return;
    }

    dirtyWatchedFiles.delete(event.document.uri.fsPath);
    refreshStatusFromCurrentState();
    refreshSidebarHome();
  });

  const createDisposable = vscode.workspace.onDidCreateFiles(async (event) => {
    if (!shouldRunValidationTrigger("workspace")) {
      return;
    }
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      return;
    }
    scheduleWatchedChangeValidation({
      repoRoot: folder.uri.fsPath,
      uris: event.files,
      scheduleValidation,
      isSuppressedGeneratedPath,
    });
  });

  const deleteDisposable = vscode.workspace.onDidDeleteFiles(async (event) => {
    if (!shouldRunValidationTrigger("workspace")) {
      return;
    }
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      return;
    }
    scheduleWatchedChangeValidation({
      repoRoot: folder.uri.fsPath,
      uris: event.files,
      scheduleValidation,
      isSuppressedGeneratedPath,
    });
  });

  const renameDisposable = vscode.workspace.onDidRenameFiles(async (event) => {
    if (!shouldRunValidationTrigger("workspace")) {
      return;
    }
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      return;
    }
    scheduleWatchedChangeValidation({
      repoRoot: folder.uri.fsPath,
      uris: flattenRenameEventUris(event.files),
      scheduleValidation,
      isSuppressedGeneratedPath,
    });
  });

  const focusDisposable = vscode.window.onDidChangeWindowState(async (state) => {
    if (!state.focused || !shouldRunValidationTrigger("workspace")) {
      return;
    }
    scheduleValidation({ mode: "change", triggerUris: [], notifyOnFail: false, source: "auto" });
  });

  const fileWatcherDisposables = [];
  const watcherFolder = vscode.workspace.workspaceFolders?.[0];
  if (watcherFolder) {
    reloadLocalShelfSettings(watcherFolder.uri.fsPath, { notifyOnError: false });
    fileWatcherDisposables.push(
      ...createWorkspaceValidationWatchers({
        watcherFolder,
        shouldRunValidationTrigger,
        scheduleValidation,
        isSuppressedGeneratedPath,
      })
    );

    const localSettingsWatcher = vscode.workspace.createFileSystemWatcher(
      new vscode.RelativePattern(watcherFolder, localSettings.LOCAL_SETTINGS_REL_PATH)
    );
    const refreshFromLocalSettingsFile = async () => {
      const snapshot = reloadLocalShelfSettings(watcherFolder.uri.fsPath, { notifyOnError: true });
      if (!snapshot.error) {
        output.appendLine(`[settings] reloaded ${localSettings.LOCAL_SETTINGS_REL_PATH}`);
      }
      await handleRuntimeSettingSourcesChanged({
        reason: `${localSettings.LOCAL_SETTINGS_REL_PATH} update`,
        refreshTree: true
      });
    };
    localSettingsWatcher.onDidChange(refreshFromLocalSettingsFile);
    localSettingsWatcher.onDidCreate(refreshFromLocalSettingsFile);
    localSettingsWatcher.onDidDelete(refreshFromLocalSettingsFile);
    fileWatcherDisposables.push(localSettingsWatcher);
  }

  context.subscriptions.push(
    sidebarViewDisposable,
    frameworkDefinitionDisposable,
    configToCodeDefinitionDisposable,
    frameworkHoverDisposable,
    frameworkReferenceDisposable,
    frameworkCompletionDisposable,
    insertFrameworkTemplateDisposable,
    startGovernedTaskDisposable,
    showGovernedTaskSessionDisposable,
    clearGovernedTaskSessionDisposable,
    validateNowDisposable,
    codegenPreflightDisposable,
    publishFrameworkDraftDisposable,
    installGitHooksDisposable,
    showIssuesDisposable,
    openFrameworkTreeDisposable,
    refreshFrameworkTreeDisposable,
    openEvidenceTreeDisposable,
    refreshEvidenceTreeDisposable,
    configurationDisposable,
    changeDisposable,
    saveDisposable,
    createDisposable,
    deleteDisposable,
    renameDisposable,
    focusDisposable,
    ...fileWatcherDisposables
  );

  if (shouldRunValidationTrigger("workspace")) {
    scheduleValidation({ mode: "change", triggerUris: [], notifyOnFail: false, source: "auto" });
  }
  void refreshGitHookStatus({ promptIfMissing: true });
}

function deactivate() {}

const execCommand = validationRuntime.execCommand;

function shellQuote(value) {
  const text = String(value ?? "");
  if (!text) {
    return "''";
  }
  if (/^[A-Za-z0-9_./:-]+$/.test(text)) {
    return text;
  }
  return `'${text.replace(/'/g, `'\"'\"'`)}'`;
}

function buildMaterializeCommand(baseCommand, projectFiles) {
  const files = [...new Set((projectFiles || []).filter(Boolean))];
  if (!files.length) {
    return String(baseCommand || DEFAULT_MATERIALIZE_COMMAND);
  }
  const projectArgs = files
    .map((projectFile) => `--project-file ${shellQuote(projectFile)}`)
    .join(" ");
  return `${String(baseCommand || DEFAULT_MATERIALIZE_COMMAND)} ${projectArgs}`.trim();
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

function parseStageFailure(code, message, stdout, stderr, exitCode) {
  const parsed = parseResult(stdout, stderr, exitCode);
  if (parsed.passed) {
    return parsed;
  }

  if (parsed.errors.length) {
    return {
      passed: false,
      errors: parsed.errors.map((issue) => normalizeIssue({
        ...issue,
        code,
      }))
    };
  }

  const detail = [stdout, stderr]
    .filter(Boolean)
    .map((value) => String(value).trim())
    .filter(Boolean)
    .join("\n")
    .trim();

  return {
    passed: false,
    errors: [normalizeIssue({
      message: detail ? `${message}\n${detail}` : message,
      file: null,
      line: 1,
      column: 1,
      code,
    })]
  };
}

function parseMypyResult(stdout, stderr, code) {
  const text = [stdout, stderr].filter(Boolean).join("\n");
  const errors = [];
  const seen = new Set();
  const linePattern = /^(.*):(\d+)(?::(\d+))?:\s*(error|note):\s*(.+)$/;

  for (const rawLine of text.split("\n")) {
    const line = rawLine.trim();
    if (!line) {
      continue;
    }
    const match = line.match(linePattern);
    if (!match || match[4] !== "error") {
      continue;
    }

    const issue = normalizeIssue({
      message: match[5],
      file: workspaceGuard.normalizeRelPath(match[1]),
      line: Number(match[2] || 1),
      column: Number(match[3] || 1),
      code: "SHELF_MYPY",
    });
    const key = `${issue.file}:${issue.line}:${issue.column}:${issue.message}`;
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    errors.push(issue);
  }

  if (!errors.length && code !== 0) {
    const fallback = [stdout, stderr]
      .filter(Boolean)
      .map((value) => String(value).trim())
      .filter(Boolean)
      .join("\n")
      .trim();
    errors.push(normalizeIssue({
      message: fallback || "mypy failed.",
      file: null,
      line: 1,
      column: 1,
      code: "SHELF_MYPY",
    }));
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
        : path.join(repoRoot, DEFAULT_VALIDATION_FALLBACK_FILE));

    if (!grouped.has(target)) {
      grouped.set(target, []);
    }

    const startLine = Math.max(0, Number(issue.line || 1) - 1);
    const startCol = Math.max(0, Number(issue.column || 1) - 1);
    const range = new vscode.Range(startLine, startCol, startLine, startCol + 1);
    const ruleCode = normalizeFrameworkRuleCode(issue.code);
    const ruleHint = frameworkRuleHint(ruleCode);
    const message = ruleCode
      ? `✖ [shelf ${ruleCode}] ${ruleHint} | ${issue.message}`
      : `✖ [shelf] ${issue.message}`;
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

function toWorkspaceRelative(filePath, repoRoot) {
  const rel = path.relative(repoRoot, filePath).replace(/\\/g, "/");
  return rel.startsWith("..") ? filePath : rel;
}

function buildTreeFallbackHtml(message, refreshCommandLabel, title) {
  const escaped = String(message)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
  const commandLabel = escapeHtml(refreshCommandLabel || "Shelf: Refresh Framework Tree");
  const pageTitle = escapeHtml(title || "Shelf · Framework Tree");

  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>${pageTitle}</title>
  <style>
    :root {
      color-scheme: light dark;
      --bg: var(--vscode-editor-background, #1e1e1e);
      --surface: var(--vscode-editorWidget-background, rgba(37, 37, 38, 0.96));
      --border: var(--vscode-panel-border, rgba(128, 128, 128, 0.3));
      --text: var(--vscode-editor-foreground, var(--vscode-foreground, #cccccc));
      --muted: var(--vscode-descriptionForeground, #9da1a6);
      --accent: var(--vscode-textLink-foreground, var(--vscode-button-background, #0e639c));
      --code-bg: rgba(127, 127, 127, 0.12);
    }

    body.vscode-light {
      --surface: var(--vscode-editorWidget-background, #f8f8f8);
      --border: var(--vscode-panel-border, rgba(0, 0, 0, 0.12));
      --code-bg: rgba(0, 0, 0, 0.05);
    }

    body.vscode-high-contrast {
      --border: var(--vscode-contrastBorder, #ffffff);
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      padding: 16px;
      color: var(--text);
      background: var(--bg);
      font-family: var(--vscode-font-family, "Segoe WPC", "Segoe UI", sans-serif);
    }

    .card {
      max-width: 760px;
      margin: 0 auto;
      padding: 16px;
      border: 1px solid var(--border);
      border-radius: 10px;
      background: var(--surface);
    }

    h1 {
      margin: 0 0 10px;
      font-size: 14px;
      font-weight: 600;
      letter-spacing: 0.01em;
    }

    p {
      margin: 0;
      font-size: 12px;
      line-height: 1.6;
      color: var(--muted);
    }

    .message {
      margin-bottom: 12px;
      color: var(--text);
    }

    .next-step {
      padding: 10px 12px;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--code-bg);
    }

    code {
      padding: 2px 6px;
      border-radius: 6px;
      color: var(--accent);
      background: var(--code-bg);
      font-family: var(--vscode-editor-font-family, "Cascadia Code", monospace);
    }
  </style>
</head>
<body>
  <div class="card">
    <h1>Shelf</h1>
    <p class="message">${escaped}</p>
    <p class="next-step">使用 <code>${commandLabel}</code> 重新计算运行时投影。</p>
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
  const heroTone = escapeHtml(model.heroTone || "unknown");
  const heroStatus = escapeHtml(model.heroStatus || "Waiting");
  const heroSummary = escapeHtml(model.heroSummary || "");
  const treePath = escapeHtml(model.treePath);
  const validationStatus = escapeHtml(model.validationStatus);
  const issueSummary = escapeHtml(model.issueSummary);
  const treeStatus = escapeHtml(model.treeStatus || "Unknown");
  const standardsStatus = escapeHtml(model.standardsStatus || "Unknown");
  const lastValidation = escapeHtml(model.lastValidation || "Not available");
  const issueOverflow = Number(model.issueOverflow || 0);
  const lastValidationTone = escapeHtml(model.lastValidationTone || "unknown");
  const issueItems = Array.isArray(model.issueItems) ? model.issueItems : [];
  const issueEmptyText = escapeHtml(model.issueEmptyText || "当前没有可展示的问题。");
  const changeItems = Array.isArray(model.changeItems) ? model.changeItems : [];
  const changeEmptyText = escapeHtml(model.changeEmptyText || "当前没有可展示的节点闭包。");
  const changeOverflow = Number(model.changeOverflow || 0);
  const changeSummary = escapeHtml(model.changeSummary || "No recent node closure");
  const actionItems = Array.isArray(model.actionItems) ? model.actionItems : [];
  const healthItems = Array.isArray(model.healthItems) ? model.healthItems : [];
  const calloutTone = escapeHtml(model.calloutTone || "unknown");
  const calloutTitle = escapeHtml(model.calloutTitle || "Next Step");
  const calloutBody = escapeHtml(model.calloutBody || "");
  const calloutAction = model.calloutAction && typeof model.calloutAction === "object"
    ? {
      action: escapeHtml(model.calloutAction.action || ""),
      label: escapeHtml(model.calloutAction.label || "")
    }
    : null;
  const summaryTiles = [
    { label: "规范总纲", value: standardsStatus },
    { label: "框架树", value: treeStatus },
    { label: "严格校验", value: validationStatus },
    { label: "问题", value: issueSummary }
  ];
  const summaryTilesHtml = summaryTiles.map((item) => `
        <div class="overview-tile">
          <span class="overview-label">${escapeHtml(item.label)}</span>
          <span class="overview-value">${escapeHtml(item.value)}</span>
        </div>`).join("");
  const metaRows = [
    { label: "Workspace", value: workspace },
    { label: "Tree Path", value: treePath },
    { label: "Last Validation", value: lastValidation }
  ];
  const metaRowsHtml = metaRows.map((item) => `
        <div class="meta-row">
          <span class="meta-key">${escapeHtml(item.label)}</span>
          <span class="meta-value">${escapeHtml(item.value)}</span>
        </div>`).join("");
  const actionItemsHtml = actionItems.length
    ? actionItems.map((item) => {
      const label = escapeHtml(item.label);
      const description = escapeHtml(item.description);
      const action = escapeHtml(item.action);
      const tone = escapeHtml(item.tone || "ghost");
      return `
        <button type="button" class="action-card ${tone}" data-action="${action}">
          <span class="action-label">${label}</span>
          <span class="action-description">${description}</span>
        </button>`;
    }).join("")
    : `<div class="empty-state">当前没有可执行的快捷操作。</div>`;
  const healthItemsHtml = healthItems.length
    ? healthItems.map((item) => {
      const label = escapeHtml(item.label);
      const value = escapeHtml(item.value);
      const tone = escapeHtml(item.tone || "unknown");
      const note = escapeHtml(item.note || "");
      return `
        <div class="health-item">
          <div class="item-head">
            <span class="item-title">${label}</span>
            <span class="badge ${tone}">${value}</span>
          </div>
          <p class="item-note">${note}</p>
        </div>`;
    }).join("")
    : `<div class="empty-state">当前没有可展示的工作区信号。</div>`;
  const issuesHtml = issueItems.length
    ? issueItems.map((item) => {
      const code = escapeHtml(item.code);
      const hint = escapeHtml(item.hint || "");
      const message = escapeHtml(item.message);
      const location = escapeHtml(item.location);
      return `
        <button type="button" class="issue-item" data-action="openIssue" data-index="${item.index}">
          <div class="issue-head">
            <span class="issue-code">${code}</span>
            ${hint ? `<span class="issue-hint">${hint}</span>` : ""}
          </div>
          <span class="issue-message">${message}</span>
          <span class="issue-location">${location}</span>
        </button>`;
    }).join("")
    : `<div class="empty-state">${issueEmptyText}</div>`;
  const overflowHtml = issueOverflow > 0
    ? `<p class="section-note">还有 ${issueOverflow} 个问题，点击“查看问题”打开完整列表。</p>`
    : "";
  const changeItemsHtml = changeItems.length
    ? changeItems.map((item) => `
        <div class="change-item">
          <div class="issue-head">
            <span class="issue-code">${escapeHtml(item.kind || "Node")}</span>
            ${item.detail ? `<span class="issue-hint">${escapeHtml(item.detail)}</span>` : ""}
          </div>
          <span class="issue-message">${escapeHtml(item.label || "")}</span>
          <span class="issue-location">${escapeHtml(item.location || "")}</span>
        </div>`).join("")
    : `<div class="empty-state">${changeEmptyText}</div>`;
  const changeOverflowHtml = changeOverflow > 0
    ? `<p class="section-note">还有 ${changeOverflow} 个节点未展开，打开证据树可查看完整闭包。</p>`
    : "";
  const calloutActionHtml = calloutAction && calloutAction.action && calloutAction.label
    ? `<button type="button" class="note-action" data-action="${calloutAction.action}">${calloutAction.label}</button>`
    : "";

  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    :root {
      color-scheme: light dark;
      --bg: var(--vscode-sideBar-background, #1e1e1e);
      --surface: rgba(255, 255, 255, 0.04);
      --surface-elevated: rgba(255, 255, 255, 0.03);
      --surface-hover: var(--vscode-list-hoverBackground, rgba(255, 255, 255, 0.06));
      --surface-tint: rgba(55, 148, 255, 0.10);
      --border: var(--vscode-sideBar-border, var(--vscode-panel-border, rgba(128, 128, 128, 0.3)));
      --text: var(--vscode-sideBar-foreground, var(--vscode-foreground, #cccccc));
      --muted: var(--vscode-descriptionForeground, #9da1a6);
      --accent: var(--vscode-textLink-foreground, var(--vscode-button-background, #0e639c));
      --accent-strong: var(--vscode-focusBorder, var(--vscode-textLink-foreground, #3794ff));
      --button-bg: var(--vscode-button-background, #0e639c);
      --button-fg: var(--vscode-button-foreground, #ffffff);
      --button-hover: var(--vscode-button-hoverBackground, #1177bb);
      --secondary-bg: var(--vscode-button-secondaryBackground, rgba(255, 255, 255, 0.08));
      --secondary-fg: var(--vscode-button-secondaryForeground, var(--text));
      --secondary-hover: var(--vscode-button-secondaryHoverBackground, rgba(255, 255, 255, 0.12));
      --badge-bg: var(--vscode-badge-background, rgba(90, 93, 94, 0.35));
      --badge-fg: var(--vscode-badge-foreground, var(--text));
      --selection: var(--vscode-list-activeSelectionBackground, rgba(55, 148, 255, 0.16));
      --ok: var(--vscode-testing-iconPassed, #89d185);
      --error: var(--vscode-testing-iconFailed, var(--vscode-errorForeground, #f48771));
      --unknown: var(--vscode-descriptionForeground, #9da1a6);
      --ok-bg: rgba(137, 209, 133, 0.12);
      --error-bg: rgba(244, 135, 113, 0.12);
      --unknown-bg: rgba(157, 161, 166, 0.12);
      --shadow: rgba(0, 0, 0, 0.24);
    }

    body.vscode-light {
      --surface: rgba(0, 0, 0, 0.035);
      --surface-elevated: rgba(0, 0, 0, 0.02);
      --surface-hover: rgba(0, 0, 0, 0.06);
      --surface-tint: rgba(0, 122, 204, 0.08);
      --border: var(--vscode-sideBar-border, var(--vscode-panel-border, rgba(0, 0, 0, 0.12)));
      --secondary-bg: rgba(0, 0, 0, 0.04);
      --secondary-hover: rgba(0, 0, 0, 0.08);
      --selection: rgba(0, 122, 204, 0.10);
      --ok-bg: rgba(30, 122, 58, 0.08);
      --error-bg: rgba(196, 43, 28, 0.08);
      --unknown-bg: rgba(90, 93, 94, 0.10);
      --shadow: rgba(15, 23, 42, 0.10);
    }

    body.vscode-high-contrast,
    body.vscode-high-contrast-light {
      --border: var(--vscode-contrastBorder, #ffffff);
      --surface: transparent;
      --surface-elevated: transparent;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      padding: 10px;
      background: var(--bg);
      color: var(--text);
      font-family: var(--vscode-font-family, "Segoe WPC", "Segoe UI", sans-serif);
    }

    .shell {
      display: grid;
      gap: 10px;
    }

    .panel {
      border: 1px solid var(--border);
      border-radius: 12px;
      background: var(--surface-elevated);
      overflow: hidden;
      box-shadow: 0 14px 28px -24px var(--shadow);
    }

    .hero-panel {
      padding: 14px;
      background:
        linear-gradient(180deg, var(--surface-tint), transparent 58%),
        var(--surface-elevated);
    }

    .hero-header {
      display: grid;
      gap: 14px;
    }

    .panel-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      padding: 10px 12px;
      border-bottom: 1px solid var(--border);
    }

    .panel-title {
      margin: 0;
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.06em;
      color: var(--muted);
      text-transform: uppercase;
    }

    .title {
      margin: 0;
      font-size: 15px;
      font-weight: 600;
      letter-spacing: 0.01em;
    }

    .title-row {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 10px;
    }

    .title-stack {
      display: grid;
      gap: 6px;
      min-width: 0;
    }

    .summary {
      margin: 0;
      font-size: 12px;
      line-height: 1.55;
      color: var(--muted);
    }

    .overview-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
    }

    .overview-tile {
      display: grid;
      gap: 6px;
      padding: 10px;
      border: 1px solid var(--border);
      border-radius: 10px;
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.03), transparent), var(--surface);
    }

    body.vscode-light .overview-tile {
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.72));
    }

    .overview-label,
    .meta-key,
    .fact-label {
      font-size: 11px;
      line-height: 1.45;
      letter-spacing: 0.06em;
      color: var(--muted);
      text-transform: uppercase;
    }

    .overview-value {
      min-width: 0;
      font-size: 13px;
      font-weight: 600;
      line-height: 1.45;
      color: var(--text);
      overflow-wrap: anywhere;
    }

    .meta-list {
      border-top: 1px solid var(--border);
    }

    .meta-row {
      display: grid;
      grid-template-columns: 98px minmax(0, 1fr);
      gap: 8px;
      padding: 9px 0;
      border-bottom: 1px solid var(--border);
    }

    .meta-row:last-child {
      border-bottom: 0;
      padding-bottom: 0;
    }

    .meta-value,
    .fact-value {
      min-width: 0;
      font-size: 12px;
      line-height: 1.5;
      color: var(--text);
      overflow-wrap: anywhere;
    }

    .section-meta,
    .item-note,
    .issue-message,
    .issue-location,
    .empty-state,
    .section-note,
    .note-copy {
      margin: 0;
      font-size: 11px;
      line-height: 1.5;
      color: var(--muted);
      overflow-wrap: anywhere;
    }

    .stack {
      display: grid;
      gap: 6px;
      padding: 10px 12px 12px;
    }

    .badge,
    .status-badge {
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 2px 8px;
      font-size: 10px;
      font-weight: 600;
      line-height: 1.5;
      white-space: nowrap;
      background: var(--badge-bg);
      color: var(--badge-fg);
    }

    .badge.ok,
    .status-badge.ok {
      color: var(--ok);
      background: var(--ok-bg);
    }

    .badge.error,
    .status-badge.error {
      color: var(--error);
      background: var(--error-bg);
    }

    .badge.unknown,
    .status-badge.unknown {
      color: var(--unknown);
      background: var(--unknown-bg);
    }

    button {
      width: 100%;
      border: 0;
      border-radius: 10px;
      padding: 10px;
      text-align: left;
      font: inherit;
      cursor: pointer;
      transition: background 120ms ease, border-color 120ms ease, transform 120ms ease;
    }

    button:focus-visible {
      outline: 1px solid var(--accent-strong);
      outline-offset: -1px;
    }

    .action-card {
      display: grid;
      gap: 4px;
      border: 1px solid var(--border);
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.03), transparent), transparent;
      color: var(--text);
    }

    .action-card.primary {
      background: linear-gradient(180deg, rgba(55, 148, 255, 0.18), rgba(55, 148, 255, 0.08));
      border-color: var(--accent-strong);
    }

    .action-card.primary:hover {
      background: linear-gradient(180deg, rgba(55, 148, 255, 0.24), rgba(55, 148, 255, 0.12));
    }

    .action-card.ghost {
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.03), transparent), var(--secondary-bg);
      color: var(--secondary-fg);
    }

    .action-card.ghost:hover {
      background: var(--secondary-hover);
    }

    .action-card:hover,
    .issue-item:hover {
      transform: translateY(-1px);
      border-color: var(--accent-strong);
    }

    .action-label {
      font-size: 12px;
      font-weight: 600;
      line-height: 1.45;
    }

    .action-description {
      font-size: 11px;
      line-height: 1.55;
      color: var(--muted);
    }

    .health-item {
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 10px;
      display: grid;
      gap: 6px;
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.025), transparent), transparent;
    }

    .item-head,
    .issue-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 8px;
    }

    .item-title {
      font-size: 12px;
      font-weight: 600;
      line-height: 1.45;
    }

    .issue-item {
      display: grid;
      gap: 6px;
      padding: 10px;
      border: 1px solid var(--border);
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.025), transparent), transparent;
      color: var(--text);
    }

    .change-item {
      display: grid;
      gap: 6px;
      padding: 10px;
      border: 1px solid var(--border);
      border-radius: 10px;
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.025), transparent), transparent;
      color: var(--text);
    }

    .issue-item:hover {
      background: var(--surface-hover);
    }

    .issue-code {
      font-size: 10px;
      font-weight: 600;
      line-height: 1.5;
      color: var(--accent);
    }

    .issue-hint {
      font-size: 10px;
      line-height: 1.45;
      color: var(--muted);
      text-align: right;
    }

    .note-panel {
      padding: 10px 12px 12px;
      border-left: 2px solid var(--accent-strong);
      background:
        linear-gradient(180deg, rgba(55, 148, 255, 0.10), transparent 72%),
        var(--surface-elevated);
    }

    .note-panel.ok {
      border-left-color: var(--ok);
    }

    .note-panel.error {
      border-left-color: var(--error);
    }

    .note-panel.unknown {
      border-left-color: var(--unknown);
    }

    .note-copy {
      margin-top: 0;
    }

    .note-action {
      margin-top: 12px;
      text-align: center;
      color: var(--button-fg);
      background: var(--button-bg);
    }

    .note-action:hover {
      background: var(--button-hover);
    }
  </style>
</head>
<body>
  <div class="shell">
    <section class="panel hero-panel">
      <div class="hero-header">
        <div class="title-row">
          <div class="title-stack">
            <h1 class="title">Shelf</h1>
            <p class="summary">${heroSummary}</p>
          </div>
        <span class="status-badge ${heroTone}">${heroStatus}</span>
        </div>
        <div class="overview-grid">
          ${summaryTilesHtml}
        </div>
        <div class="meta-list">
          ${metaRowsHtml}
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="panel-header">
        <h2 class="panel-title">快速操作</h2>
        <span class="section-meta">${issueSummary}</span>
      </div>
      <div class="stack">
        ${actionItemsHtml}
      </div>
    </section>

    <section class="panel">
      <div class="panel-header">
        <h2 class="panel-title">工作区信号</h2>
        <span class="badge ${lastValidationTone}">最近校验</span>
      </div>
      <div class="stack">
        ${healthItemsHtml}
      </div>
    </section>

    <section class="panel">
      <div class="panel-header">
        <h2 class="panel-title">节点闭包</h2>
        <span class="section-meta">${changeSummary}</span>
      </div>
      <div class="stack">
        ${changeItemsHtml}
        ${changeOverflowHtml}
      </div>
    </section>

    <section class="panel">
      <div class="panel-header">
        <h2 class="panel-title">问题预览</h2>
        <span class="section-meta">${issueSummary}</span>
      </div>
      <div class="stack">
        ${issuesHtml}
        ${overflowHtml}
      </div>
    </section>

    <section class="panel note-panel ${calloutTone}">
      <div class="panel-header">
        <h2 class="panel-title">${calloutTitle}</h2>
      </div>
      <div class="stack">
        <p class="note-copy">${calloutBody}</p>
        ${calloutActionHtml}
      </div>
    </section>
  </div>

  <script>
    const vscode = typeof acquireVsCodeApi === "function" ? acquireVsCodeApi() : null;
    for (const button of document.querySelectorAll("button[data-action]")) {
      button.addEventListener("click", () => {
        if (!vscode) return;
        const action = button.getAttribute("data-action");
        if (!action) return;
        const index = button.getAttribute("data-index");
        const message = { type: "shelf.sidebar." + action };
        if (index !== null) {
          message.index = Number(index);
        }
        vscode.postMessage(message);
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
    : path.join(repoRoot, DEFAULT_VALIDATION_FALLBACK_FILE);
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
    message: String(item.message || "Shelf validation issue"),
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
    return "Shelf 规则";
  }
  return FRAMEWORK_RULE_HINTS[ruleCode] || "Shelf 规则";
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
    return "Shelf";
  }
  const preview = errors.slice(0, 3).map((e) => `• ${e.message}`).join("\n");
  const more = errors.length > 3 ? `\n... +${errors.length - 3} more` : "";
  return `Shelf\n${preview}${more}\n(click to open Problems)`;
}

function hasStandardsTree(repoRoot) {
  return fs.existsSync(path.join(repoRoot, STANDARDS_TREE_FILE));
}

function setStatusDisabled(status, repoRoot) {
  status.text = "$(circle-slash) Shelf";
  status.tooltip = `Shelf validation guard disabled: ${toWorkspaceRelative(
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
