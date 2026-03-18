const fs = require("fs");
const path = require("path");
const workspaceGuard = require("./guarding");

const DEFAULT_PROJECT_FILE = path.join("projects", "knowledge_base_basic", "project.toml");
const SUPPORTED_CORRESPONDENCE_SCHEMA_VERSION = 1;
const DEFAULT_API_PREFIX = "/api/knowledge";

/**
 * @typedef {Object} CorrespondenceNavigationTarget
 * @property {string} target_kind
 * @property {string} layer
 * @property {string} file_path
 * @property {number} start_line
 * @property {number} end_line
 * @property {string} symbol
 * @property {string} label
 * @property {boolean} is_primary
 * @property {boolean} is_editable
 * @property {boolean} is_deprecated_alias
 */

/**
 * @typedef {Object} CorrespondenceObject
 * @property {string} object_kind
 * @property {string} object_id
 * @property {string} owner_module_id
 * @property {string} display_name
 * @property {string} materialization_kind
 * @property {string} primary_nav_target_kind
 * @property {string} primary_edit_target_kind
 * @property {CorrespondenceNavigationTarget} correspondence_anchor
 * @property {CorrespondenceNavigationTarget} implementation_anchor
 * @property {CorrespondenceNavigationTarget[]} navigation_targets
 */

/**
 * @typedef {Object} CorrespondenceValidationIssue
 * @property {string} issue_kind
 * @property {string} level
 * @property {string} reason
 * @property {string[]} object_ids
 * @property {string} primary_object_id
 */

/**
 * @typedef {Object} CorrespondenceValidationSummary
 * @property {boolean} passed
 * @property {number} rule_count
 * @property {number} error_count
 * @property {CorrespondenceValidationIssue[]} issues
 * @property {Record<string, number>} issue_count_by_object
 */

/**
 * @typedef {Object} CorrespondencePayload
 * @property {number} correspondence_schema_version
 * @property {CorrespondenceObject[]} objects
 * @property {Record<string, CorrespondenceObject>} object_index
 * @property {Record<string, unknown>[]} tree
 * @property {CorrespondenceValidationSummary} validation_summary
 */

/**
 * @typedef {Object} CorrespondenceSnapshot
 * @property {string} projectFilePath
 * @property {string} canonicalPath
 * @property {ReturnType<typeof resolveCorrespondenceApiPaths>} endpoints
 * @property {CorrespondencePayload} payload
 * @property {Record<string, unknown>} canonical
 * @property {ReturnType<typeof workspaceGuard.getProjectCanonicalFreshness>} freshness
 */

function asText(value) {
  return String(value ?? "").trim();
}

function asPositiveInt(value, fallback) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed < 1) {
    return fallback;
  }
  return Math.max(1, Math.floor(parsed));
}

function normalizeApiPath(value) {
  const text = asText(value);
  if (!text) {
    return "";
  }
  return text.startsWith("/") ? text : `/${text}`;
}

/**
 * @param {string} projectFilePath
 * @returns {Record<string, unknown> | null}
 */
function readProjectCanonical(projectFilePath) {
  const canonicalPath = workspaceGuard.canonicalPathForProjectFile(projectFilePath);
  if (!fs.existsSync(canonicalPath) || !fs.statSync(canonicalPath).isFile()) {
    return null;
  }
  try {
    const raw = JSON.parse(fs.readFileSync(canonicalPath, "utf8"));
    return raw && typeof raw === "object" ? raw : null;
  } catch {
    return null;
  }
}

/**
 * @param {string} repoRoot
 * @param {string} frameworkName
 * @returns {string | null}
 */
function resolvePreferredProjectFile(repoRoot, frameworkName = "") {
  const candidates = workspaceGuard.discoverProjectFiles(repoRoot);
  const preferredDefault = path.join(repoRoot, DEFAULT_PROJECT_FILE);
  let bestFile = null;
  let bestScore = -1;
  for (const filePath of candidates) {
    let score = filePath === preferredDefault ? 1 : 0;
    if (frameworkName) {
      try {
        const frameworks = workspaceGuard.inferConfiguredFrameworks(fs.readFileSync(filePath, "utf8"));
        if (frameworks.has(frameworkName)) {
          score += 10;
        }
      } catch {
        score += 0;
      }
    }
    if (score > bestScore) {
      bestScore = score;
      bestFile = filePath;
    }
  }
  if (bestFile) {
    return bestFile;
  }
  if (fs.existsSync(preferredDefault) && fs.statSync(preferredDefault).isFile()) {
    return preferredDefault;
  }
  return null;
}

/**
 * @param {Record<string, unknown>} canonical
 * @returns {{ root: string, tree: string, objectBase: string }}
 */
function resolveCorrespondenceApiPaths(canonical) {
  const transport = canonical?.code
    && typeof canonical.code === "object"
    && canonical.code.runtime_exports
    && typeof canonical.code.runtime_exports === "object"
    && canonical.code.runtime_exports.backend_service_spec
    && typeof canonical.code.runtime_exports.backend_service_spec === "object"
    && canonical.code.runtime_exports.backend_service_spec.transport
    && typeof canonical.code.runtime_exports.backend_service_spec.transport === "object"
      ? canonical.code.runtime_exports.backend_service_spec.transport
      : null;
  const apiPrefix = transport && typeof transport.api_prefix === "string" && transport.api_prefix.startsWith("/")
    ? transport.api_prefix
    : DEFAULT_API_PREFIX;
  const root = `${apiPrefix}/correspondence`;
  return {
    root,
    tree: `${root}/tree`,
    objectBase: `${root}/object/`,
  };
}

/**
 * @param {unknown} candidate
 * @returns {CorrespondenceNavigationTarget}
 */
function normalizeNavigationTarget(candidate) {
  if (!candidate || typeof candidate !== "object") {
    throw new Error("invalid correspondence target: expected object");
  }
  return {
    target_kind: asText(candidate.target_kind),
    layer: asText(candidate.layer),
    file_path: asText(candidate.file_path),
    start_line: asPositiveInt(candidate.start_line, 1),
    end_line: asPositiveInt(candidate.end_line, asPositiveInt(candidate.start_line, 1)),
    symbol: asText(candidate.symbol),
    label: asText(candidate.label),
    is_primary: candidate.is_primary === true,
    is_editable: candidate.is_editable === true,
    is_deprecated_alias: candidate.is_deprecated_alias === true,
  };
}

/**
 * @param {unknown} candidate
 * @returns {CorrespondenceObject}
 */
function normalizeCorrespondenceObject(candidate) {
  if (!candidate || typeof candidate !== "object") {
    throw new Error("invalid correspondence object: expected object");
  }
  const objectId = asText(candidate.object_id);
  if (!objectId) {
    throw new Error("invalid correspondence object: missing object_id");
  }
  const navigationTargets = Array.isArray(candidate.navigation_targets)
    ? candidate.navigation_targets.map(normalizeNavigationTarget)
    : [];
  const objectValue = {
    object_kind: asText(candidate.object_kind),
    object_id: objectId,
    owner_module_id: asText(candidate.owner_module_id),
    display_name: asText(candidate.display_name),
    materialization_kind: asText(candidate.materialization_kind),
    primary_nav_target_kind: asText(candidate.primary_nav_target_kind),
    primary_edit_target_kind: asText(candidate.primary_edit_target_kind),
    correspondence_anchor: normalizeNavigationTarget(candidate.correspondence_anchor),
    implementation_anchor: normalizeNavigationTarget(candidate.implementation_anchor),
    navigation_targets: navigationTargets,
  };
  const primaryTargetKinds = new Set(
    navigationTargets
      .filter((target) => target.is_primary)
      .map((target) => target.target_kind)
  );
  if (!navigationTargets.some((target) => target.target_kind === objectValue.primary_nav_target_kind)) {
    throw new Error(`invalid correspondence object ${objectId}: missing primary_nav_target_kind target`);
  }
  if (!navigationTargets.some((target) => target.target_kind === objectValue.primary_edit_target_kind)) {
    throw new Error(`invalid correspondence object ${objectId}: missing primary_edit_target_kind target`);
  }
  if (objectValue.materialization_kind === "runtime_dynamic_type") {
    const hasFallback = navigationTargets.some((target) =>
      target.target_kind === "framework_definition"
      || target.target_kind === "config_source"
      || target.target_kind === "code_correspondence"
    );
    if (!hasFallback) {
      throw new Error(`invalid correspondence object ${objectId}: runtime_dynamic_type requires a fallback target`);
    }
  }
  if (navigationTargets.some((target) => target.target_kind === "deprecated_alias" && target.is_primary)) {
    throw new Error(`invalid correspondence object ${objectId}: deprecated_alias cannot be primary`);
  }
  if (!primaryTargetKinds.has(objectValue.primary_nav_target_kind)) {
    throw new Error(`invalid correspondence object ${objectId}: primary nav target is not marked primary`);
  }
  return objectValue;
}

/**
 * @param {unknown} candidate
 * @returns {CorrespondenceValidationSummary}
 */
function normalizeValidationSummary(candidate) {
  if (!candidate || typeof candidate !== "object") {
    return {
      passed: false,
      rule_count: 0,
      error_count: 0,
      issues: [],
      issue_count_by_object: {},
    };
  }
  const issues = Array.isArray(candidate.issues)
    ? candidate.issues
      .filter((item) => item && typeof item === "object")
      .map((item) => ({
        issue_kind: asText(item.issue_kind),
        level: asText(item.level) || "error",
        reason: asText(item.reason),
        object_ids: Array.isArray(item.object_ids) ? item.object_ids.map((entry) => asText(entry)).filter(Boolean) : [],
        primary_object_id: asText(item.primary_object_id),
      }))
    : [];
  const issueCountByObject = {};
  const rawIssueCounts = candidate.issue_count_by_object;
  if (rawIssueCounts && typeof rawIssueCounts === "object") {
    for (const [objectId, count] of Object.entries(rawIssueCounts)) {
      issueCountByObject[asText(objectId)] = Math.max(0, Math.floor(Number(count) || 0));
    }
  }
  return {
    passed: candidate.passed === true,
    rule_count: Math.max(0, Math.floor(Number(candidate.rule_count) || 0)),
    error_count: Math.max(0, Math.floor(Number(candidate.error_count) || issues.length)),
    issues,
    issue_count_by_object: issueCountByObject,
  };
}

/**
 * @param {unknown} candidate
 * @returns {CorrespondencePayload}
 */
function normalizeCorrespondencePayload(candidate) {
  if (!candidate || typeof candidate !== "object") {
    throw new Error("invalid correspondence payload: expected object");
  }
  const schemaVersion = Number(candidate.correspondence_schema_version || 0);
  if (schemaVersion !== SUPPORTED_CORRESPONDENCE_SCHEMA_VERSION) {
    throw new Error(
      `unsupported correspondence schema version: ${schemaVersion} (expected ${SUPPORTED_CORRESPONDENCE_SCHEMA_VERSION})`
    );
  }
  const objects = Array.isArray(candidate.objects)
    ? candidate.objects.map(normalizeCorrespondenceObject)
    : [];
  const objectIndex = {};
  for (const objectValue of objects) {
    objectIndex[objectValue.object_id] = objectValue;
  }
  const rawObjectIndex = candidate.object_index;
  if (rawObjectIndex && typeof rawObjectIndex === "object") {
    for (const [objectId, objectValue] of Object.entries(rawObjectIndex)) {
      const normalized = normalizeCorrespondenceObject(objectValue);
      if (normalized.object_id !== objectId) {
        throw new Error(`invalid correspondence object index entry: ${objectId}`);
      }
      objectIndex[objectId] = normalized;
    }
  }
  return {
    correspondence_schema_version: schemaVersion,
    objects,
    object_index: objectIndex,
    tree: Array.isArray(candidate.tree) ? candidate.tree.filter((item) => item && typeof item === "object") : [],
    validation_summary: normalizeValidationSummary(candidate.validation_summary),
  };
}

/**
 * @param {string} repoRoot
 * @param {{ projectFilePath?: string, frameworkName?: string, requireFresh?: boolean }} [options]
 * @returns {CorrespondenceSnapshot | null}
 */
function loadCorrespondenceSnapshot(repoRoot, options = {}) {
  const projectFilePath = options.projectFilePath
    ? path.resolve(options.projectFilePath)
    : resolvePreferredProjectFile(repoRoot, asText(options.frameworkName));
  if (!projectFilePath) {
    return null;
  }
  const freshness = workspaceGuard.getProjectCanonicalFreshness(repoRoot, projectFilePath);
  if (options.requireFresh !== false && freshness.status !== "fresh") {
    return null;
  }
  const canonical = readProjectCanonical(projectFilePath);
  if (!canonical) {
    return null;
  }
  const payload = normalizeCorrespondencePayload(canonical.correspondence);
  return {
    projectFilePath,
    canonicalPath: workspaceGuard.canonicalPathForProjectFile(projectFilePath),
    endpoints: resolveCorrespondenceApiPaths(canonical),
    payload,
    canonical,
    freshness,
  };
}

/**
 * @param {string} repoRoot
 * @param {string} apiPath
 * @param {{ projectFilePath?: string, frameworkName?: string, requireFresh?: boolean }} [options]
 * @returns {CorrespondencePayload | { correspondence_schema_version: number, tree: Record<string, unknown>[], validation_summary: CorrespondenceValidationSummary } | CorrespondenceObject | null}
 */
function readCorrespondenceApi(repoRoot, apiPath, options = {}) {
  const snapshot = loadCorrespondenceSnapshot(repoRoot, options);
  if (!snapshot) {
    return null;
  }
  const requested = normalizeApiPath(apiPath);
  const rootPath = normalizeApiPath(snapshot.endpoints.root);
  const treePath = normalizeApiPath(snapshot.endpoints.tree);
  if (requested === rootPath) {
    return snapshot.payload;
  }
  if (requested === treePath) {
    return {
      correspondence_schema_version: snapshot.payload.correspondence_schema_version,
      tree: snapshot.payload.tree,
      validation_summary: snapshot.payload.validation_summary,
    };
  }
  const objectPrefix = normalizeApiPath(snapshot.endpoints.objectBase);
  if (requested.startsWith(objectPrefix)) {
    const objectId = decodeURIComponent(requested.slice(objectPrefix.length));
    return snapshot.payload.object_index[objectId] || null;
  }
  return null;
}

/**
 * @param {CorrespondenceObject | null | undefined} objectValue
 * @param {string} targetKind
 * @returns {CorrespondenceNavigationTarget | null}
 */
function resolveTargetByKind(objectValue, targetKind) {
  if (!objectValue || !Array.isArray(objectValue.navigation_targets)) {
    return null;
  }
  return objectValue.navigation_targets.find((target) => target.target_kind === targetKind) || null;
}

/**
 * @param {CorrespondenceObject | null | undefined} objectValue
 * @returns {CorrespondenceNavigationTarget | null}
 */
function resolvePrimaryNavigationTarget(objectValue) {
  if (!objectValue) {
    return null;
  }
  return resolveTargetByKind(objectValue, objectValue.primary_nav_target_kind)
    || objectValue.navigation_targets.find((target) => target.is_primary)
    || null;
}

/**
 * @param {CorrespondenceObject | null | undefined} objectValue
 * @returns {CorrespondenceNavigationTarget | null}
 */
function resolvePrimaryEditTarget(objectValue) {
  if (!objectValue) {
    return null;
  }
  return resolveTargetByKind(objectValue, objectValue.primary_edit_target_kind)
    || null;
}

/**
 * @param {CorrespondenceObject | null | undefined} objectValue
 * @returns {CorrespondenceNavigationTarget[]}
 */
function resolveSecondaryTargets(objectValue) {
  if (!objectValue) {
    return [];
  }
  const primaryNav = resolvePrimaryNavigationTarget(objectValue);
  const primaryEdit = resolvePrimaryEditTarget(objectValue);
  const excluded = new Set(
    [primaryNav, primaryEdit, objectValue.correspondence_anchor, objectValue.implementation_anchor]
      .filter(Boolean)
      .map((target) => `${target.target_kind}:${target.file_path}:${target.start_line}:${target.symbol}`)
  );
  return objectValue.navigation_targets.filter((target) =>
    !excluded.has(`${target.target_kind}:${target.file_path}:${target.start_line}:${target.symbol}`)
  );
}

/**
 * @param {CorrespondenceValidationSummary | null | undefined} summary
 * @param {Record<string, CorrespondenceObject>} objectIndex
 * @returns {{ message: string, file: string, line: number, column: number, code: string, objectId: string, targetKind: string }[]}
 */
function buildValidationIssues(summary, objectIndex) {
  if (!summary || !Array.isArray(summary.issues) || !summary.issues.length) {
    return [];
  }
  return summary.issues.map((issue) => {
    const primaryObjectId = asText(issue.primary_object_id)
      || (Array.isArray(issue.object_ids) ? asText(issue.object_ids[0]) : "");
    const objectValue = primaryObjectId ? objectIndex[primaryObjectId] : null;
    const primaryTarget = resolvePrimaryNavigationTarget(objectValue)
      || objectValue?.correspondence_anchor
      || objectValue?.implementation_anchor
      || null;
    return {
      message: primaryObjectId
        ? `[${primaryObjectId}] ${asText(issue.reason) || "Correspondence validation issue"}`
        : (asText(issue.reason) || "Correspondence validation issue"),
      file: primaryTarget ? primaryTarget.file_path : "projects/*/generated/canonical.json",
      line: primaryTarget ? primaryTarget.start_line : 1,
      column: 1,
      code: "SHELF_CORRESPONDENCE",
      objectId: primaryObjectId,
      targetKind: primaryTarget ? primaryTarget.target_kind : "",
    };
  });
}

/**
 * @param {{ message: string, file: string, line: number, column: number, code: string }[]} primaryIssues
 * @param {{ message: string, file: string, line: number, column: number, code: string }[]} fallbackIssues
 * @returns {{ message: string, file: string, line: number, column: number, code: string }[]}
 */
function mergeIssueLists(primaryIssues, fallbackIssues) {
  const merged = [];
  const seen = new Set();
  for (const issue of [...(primaryIssues || []), ...(fallbackIssues || [])]) {
    const signature = [
      asText(issue.code),
      asText(issue.file),
      asPositiveInt(issue.line, 1),
      asText(issue.message),
    ].join("|");
    if (seen.has(signature)) {
      continue;
    }
    seen.add(signature);
    merged.push(issue);
  }
  return merged;
}

module.exports = {
  DEFAULT_API_PREFIX,
  SUPPORTED_CORRESPONDENCE_SCHEMA_VERSION,
  buildValidationIssues,
  loadCorrespondenceSnapshot,
  mergeIssueLists,
  normalizeCorrespondencePayload,
  readCorrespondenceApi,
  readProjectCanonical,
  resolveCorrespondenceApiPaths,
  resolvePrimaryEditTarget,
  resolvePrimaryNavigationTarget,
  resolvePreferredProjectFile,
  resolveSecondaryTargets,
  resolveTargetByKind,
};
