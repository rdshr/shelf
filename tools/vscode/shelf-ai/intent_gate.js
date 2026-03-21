const fs = require("fs");
const path = require("path");
const workspaceGuard = require("./guarding");

const MAX_MATCH_COUNT = 8;
const NON_ONE_TO_ONE_MAPPING_PREFIX = "non one-to-one boundary mapping";
const TEMP_BYPASS_ALL_TOKEN = "*";
const TEMP_BYPASS_SCOPES = Object.freeze([
  "grant_pre_validation",
  "mapping_echo",
  "one_to_one_check",
]);
const TEMP_BYPASS_SCOPE_SET = new Set(TEMP_BYPASS_SCOPES);

/** @typedef {{
 * projectId: string,
 * projectFileRelPath: string,
 * canonicalRelPath: string,
 * canonicalPath: string,
 * freshnessStatus: string,
 * moduleId: string,
 * boundaryId: string,
 * mappingMode: string,
 * note: string,
 * primaryExactPath: string,
 * exactPaths: string[],
 * relatedExactPaths: string[],
 * primaryCommunicationPath: string,
 * communicationPaths: string[],
 * relatedCommunicationPaths: string[],
 * keywordTokens: string[]
 * }} IntentBoundaryEntry */

/** @typedef {{
 * projectId: string,
 * projectFileRelPath: string,
 * canonicalRelPath: string,
 * freshnessStatus: string,
 * moduleId: string,
 * boundaryId: string,
 * mappingMode: string,
 * note: string,
 * score: number,
 * scoreReasons: string[],
 * primaryExactPath: string,
 * exactPaths: string[],
 * relatedExactPaths: string[],
 * primaryCommunicationPath: string,
 * communicationPaths: string[],
 * relatedCommunicationPaths: string[]
 * }} IntentMappingItem */

const TOKEN_ALIAS_RULES = [
  { pattern: /@|\bmention\b|\bcite\b|\bcitation\b|\bref\b|引用|引文|提及|来源/giu, tokens: ["citation", "chat", "scope", "anchor", "return"] },
  { pattern: /文档|章节|段落|片段|document|docs?|section|snippet|source/giu, tokens: ["preview", "anchor", "docview", "toc", "meta"] },
  { pattern: /对话|聊天|问答|消息|chat|conversation|turn|input|composer/giu, tokens: ["chat", "turn", "input", "status"] },
  { pattern: /页面|路由|导航|入口|返回|page|route|navigate|navigation|entry|return/giu, tokens: ["route", "pageset", "surface", "return", "entry", "nav"] },
  { pattern: /知识库|知识|library|knowledge/giu, tokens: ["knowledge", "library", "scope", "context"] },
  { pattern: /动态|动画|炫|图|graph|visual|animation|motion|cool/giu, tokens: ["visual", "surface", "interact", "feedback", "state"] },
  { pattern: /前端|界面|ui|frontend|client|shell/giu, tokens: ["frontend", "surface", "visual", "interact", "state"] },
  { pattern: /后端|接口|api|backend|service/giu, tokens: ["backend", "result", "auth", "trace", "chatapi", "libapi", "previewapi"] },
];

function normalizeRelPath(relPath) {
  return workspaceGuard.normalizeRelPath(relPath);
}

function normalizeText(value) {
  return String(value || "").trim();
}

function tokenizeText(text) {
  const normalized = normalizeText(text).toLowerCase();
  const ascii = normalized.match(/[a-z0-9_.-]+/g) || [];
  const han = normalized.match(/[\u4e00-\u9fff]{1,6}/g) || [];
  return [...ascii, ...han];
}

function splitSymbolTokens(value) {
  return String(value || "")
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter(Boolean);
}

function parseProjectIdFromProjectFileRelPath(projectFileRelPath) {
  const match = /^projects\/([^/]+)\/project\.toml$/.exec(projectFileRelPath);
  return match ? match[1] : "";
}

function normalizePathList(values) {
  const unique = new Set();
  for (const value of Array.isArray(values) ? values : []) {
    const item = String(value || "").trim();
    if (item) {
      unique.add(item);
    }
  }
  return [...unique].sort();
}

function normalizeTemporaryBypassScopes(value) {
  const source = Array.isArray(value) ? value : [];
  const normalized = [];
  const seen = new Set();
  for (const item of source) {
    const token = String(item || "").trim().toLowerCase();
    if (!token) {
      continue;
    }
    if (token === TEMP_BYPASS_ALL_TOKEN || token === "all") {
      return [TEMP_BYPASS_ALL_TOKEN];
    }
    if (!TEMP_BYPASS_SCOPE_SET.has(token) || seen.has(token)) {
      continue;
    }
    seen.add(token);
    normalized.push(token);
  }
  return normalized.sort();
}

function isTemporaryBypassScopeEnabled(scopes, scope) {
  const normalizedScope = String(scope || "").trim().toLowerCase();
  if (!TEMP_BYPASS_SCOPE_SET.has(normalizedScope)) {
    return false;
  }
  const normalizedScopes = normalizeTemporaryBypassScopes(scopes);
  return normalizedScopes.includes(TEMP_BYPASS_ALL_TOKEN) || normalizedScopes.includes(normalizedScope);
}

function safeReadCanonical(canonicalPath) {
  try {
    const payload = JSON.parse(fs.readFileSync(canonicalPath, "utf8"));
    if (!payload || typeof payload !== "object") {
      return { ok: false, reason: "canonical payload must be an object" };
    }
    return { ok: true, canonical: payload };
  } catch (error) {
    return {
      ok: false,
      reason: error instanceof Error ? error.message : String(error),
    };
  }
}

function collectKeywordTokens({
  moduleId,
  boundaryId,
  exactPaths,
  relatedExactPaths,
  communicationPaths,
  relatedCommunicationPaths,
  note,
}) {
  const tokens = new Set();
  for (const token of splitSymbolTokens(moduleId)) {
    tokens.add(token);
  }
  for (const token of splitSymbolTokens(boundaryId)) {
    tokens.add(token);
  }
  for (const exactPath of exactPaths) {
    for (const token of splitSymbolTokens(exactPath)) {
      tokens.add(token);
    }
  }
  for (const exactPath of relatedExactPaths) {
    for (const token of splitSymbolTokens(exactPath)) {
      tokens.add(token);
    }
  }
  for (const communicationPath of communicationPaths) {
    for (const token of splitSymbolTokens(communicationPath)) {
      tokens.add(token);
    }
  }
  for (const communicationPath of relatedCommunicationPaths) {
    for (const token of splitSymbolTokens(communicationPath)) {
      tokens.add(token);
    }
  }
  for (const token of splitSymbolTokens(note)) {
    tokens.add(token);
  }
  return [...tokens].sort();
}

function readCanonicalForProject(repoRoot, projectFilePath) {
  const canonicalPath = workspaceGuard.canonicalPathForProjectFile(projectFilePath);
  const projectFileRelPath = normalizeRelPath(path.relative(repoRoot, projectFilePath));
  const canonicalRelPath = normalizeRelPath(path.relative(repoRoot, canonicalPath));
  const projectId = parseProjectIdFromProjectFileRelPath(projectFileRelPath);
  const freshness = workspaceGuard.getProjectCanonicalFreshness(repoRoot, projectFilePath);

  if (!fs.existsSync(canonicalPath) || !fs.statSync(canonicalPath).isFile()) {
    return {
      ok: false,
      projectId,
      projectFileRelPath,
      canonicalPath,
      canonicalRelPath,
      freshnessStatus: freshness.status || "missing",
      error: `canonical missing: ${canonicalRelPath}`,
    };
  }

  const readResult = safeReadCanonical(canonicalPath);
  if (!readResult.ok) {
    return {
      ok: false,
      projectId,
      projectFileRelPath,
      canonicalPath,
      canonicalRelPath,
      freshnessStatus: freshness.status || "invalid",
      error: `canonical invalid: ${canonicalRelPath} (${readResult.reason})`,
    };
  }

  return {
    ok: true,
    projectId,
    projectFileRelPath,
    canonicalPath,
    canonicalRelPath,
    freshnessStatus: freshness.status || "unknown",
    canonical: readResult.canonical,
  };
}

function collectBoundaryEntries(repoRoot, { allowNonOneToOneMapping = false } = {}) {
  const projectFiles = workspaceGuard.discoverProjectFiles(repoRoot);
  const entries = [];
  const sources = [];
  const errors = [];
  const boundaryPrimaryMap = new Map();

  for (const projectFilePath of projectFiles) {
    const canonicalResult = readCanonicalForProject(repoRoot, projectFilePath);
    if (!canonicalResult.ok) {
      errors.push(canonicalResult.error);
      continue;
    }

    const canonical = canonicalResult.canonical;
    const configModules = Array.isArray(canonical?.config?.modules) ? canonical.config.modules : [];

    sources.push({
      projectId: canonicalResult.projectId,
      projectFileRelPath: canonicalResult.projectFileRelPath,
      canonicalRelPath: canonicalResult.canonicalRelPath,
      freshnessStatus: canonicalResult.freshnessStatus,
    });

    for (const configModule of configModules) {
      const moduleId = String(configModule?.module_id || "").trim();
      if (!moduleId) {
        continue;
      }
      const boundaryBindings = Array.isArray(configModule?.compiled_config_export?.boundary_bindings)
        ? configModule.compiled_config_export.boundary_bindings
        : [];

      for (const binding of boundaryBindings) {
        const boundaryId = String(binding?.boundary_id || "").trim();
        if (!boundaryId) {
          continue;
        }
        const primaryExactPath = String(binding?.primary_exact_path || "").trim();
        const primaryCommunicationPath = String(binding?.primary_communication_path || "").trim();
        if (!primaryExactPath || !primaryCommunicationPath) {
          errors.push(
            `incomplete boundary mapping: ${canonicalResult.projectFileRelPath} ${moduleId}/${boundaryId} missing primary path`
          );
          continue;
        }
        const boundaryKey = `${canonicalResult.projectId}|${moduleId}|${boundaryId}`;
        const seenPrimary = boundaryPrimaryMap.get(boundaryKey);
        if (seenPrimary) {
          if (
            seenPrimary.primaryExactPath !== primaryExactPath
            || seenPrimary.primaryCommunicationPath !== primaryCommunicationPath
          ) {
            errors.push(
              `ambiguous primary mapping: ${canonicalResult.projectFileRelPath} ${moduleId}/${boundaryId} -> ${seenPrimary.primaryExactPath} vs ${primaryExactPath}`
            );
          }
          continue;
        }
        boundaryPrimaryMap.set(boundaryKey, {
          primaryExactPath,
          primaryCommunicationPath,
        });
        const exactPaths = [primaryExactPath];
        const communicationPaths = [primaryCommunicationPath];
        const relatedExactPaths = normalizePathList([
          primaryExactPath,
          ...(Array.isArray(binding?.related_exact_paths) ? binding.related_exact_paths : []),
        ]);
        const relatedCommunicationPaths = normalizePathList([
          primaryCommunicationPath,
          ...(Array.isArray(binding?.related_communication_paths) ? binding.related_communication_paths : []),
        ]);
        if (
          relatedExactPaths.length !== 1
          || relatedExactPaths[0] !== primaryExactPath
          || relatedCommunicationPaths.length !== 1
          || relatedCommunicationPaths[0] !== primaryCommunicationPath
        ) {
          errors.push(
            `${NON_ONE_TO_ONE_MAPPING_PREFIX}: ${canonicalResult.projectFileRelPath} `
            + `${moduleId}/${boundaryId} `
            + `primary_exact=${primaryExactPath} related_exact=[${relatedExactPaths.join(", ")}] `
            + `primary_communication=${primaryCommunicationPath} `
            + `related_communication=[${relatedCommunicationPaths.join(", ")}]`
          );
          if (!allowNonOneToOneMapping) {
            continue;
          }
        }

        const entry = {
          projectId: canonicalResult.projectId,
          projectFileRelPath: canonicalResult.projectFileRelPath,
          canonicalRelPath: canonicalResult.canonicalRelPath,
          canonicalPath: canonicalResult.canonicalPath,
          freshnessStatus: canonicalResult.freshnessStatus,
          moduleId,
          boundaryId,
          mappingMode: String(binding?.mapping_mode || "").trim() || "unknown",
          note: String(binding?.note || "").trim(),
          primaryExactPath,
          exactPaths,
          relatedExactPaths,
          primaryCommunicationPath,
          communicationPaths,
          relatedCommunicationPaths,
          keywordTokens: [],
        };
        entry.keywordTokens = collectKeywordTokens(entry);
        entries.push(entry);
      }
    }
  }

  return { entries, sources, errors };
}

function augmentIntentTokens(intentText) {
  const tokenSet = new Set(tokenizeText(intentText));
  const normalized = normalizeText(intentText).toLowerCase();
  for (const rule of TOKEN_ALIAS_RULES) {
    rule.pattern.lastIndex = 0;
    if (rule.pattern.test(normalized)) {
      for (const token of rule.tokens) {
        tokenSet.add(token);
      }
    }
  }
  return [...tokenSet].sort();
}

function scoreEntry(entry, intentText, intentTokens) {
  const reasons = [];
  let score = 0;
  const normalizedText = normalizeText(intentText).toLowerCase();
  const boundaryLower = entry.boundaryId.toLowerCase();
  const moduleLower = entry.moduleId.toLowerCase();

  if (boundaryLower && normalizedText.includes(boundaryLower)) {
    score += 10;
    reasons.push(`命中 boundary_id=${entry.boundaryId}`);
  }
  if (moduleLower && normalizedText.includes(moduleLower)) {
    score += 10;
    reasons.push(`命中 module_id=${entry.moduleId}`);
  }

  for (const exactPath of entry.exactPaths) {
    const lowerPath = exactPath.toLowerCase();
    if (normalizedText.includes(lowerPath)) {
      score += 12;
      reasons.push(`命中 exact path=${exactPath}`);
    }
  }

  const entryTokens = new Set(entry.keywordTokens);
  let overlap = 0;
  for (const token of intentTokens) {
    if (entryTokens.has(token)) {
      overlap += 1;
    }
  }
  if (overlap > 0) {
    score += overlap * 2;
    reasons.push(`关键词重合 ${overlap} 个`);
  }

  return { score, reasons };
}

function uniqueMappingItems(items) {
  const seen = new Set();
  const unique = [];
  for (const item of items) {
    const key = `${item.projectId}|${item.moduleId}|${item.boundaryId}`;
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    unique.push(item);
  }
  return unique;
}

function analyzeIntentMapping({
  repoRoot,
  intentText,
  minimumScore = 4,
  maxResults = MAX_MATCH_COUNT,
  allowNonOneToOneMapping = false,
}) {
  const text = normalizeText(intentText);
  const safeRepoRoot = String(repoRoot || "").trim();
  if (!safeRepoRoot) {
    return {
      passed: false,
      intentText: text,
      minimumScore,
      queryTokens: [],
      mappings: [],
      reason: "missing repo root",
      sources: [],
      errors: ["missing repo root"],
      allowedExactPaths: [],
      allowedCommunicationPaths: [],
      matchedModuleIds: [],
    };
  }
  if (!text) {
    return {
      passed: false,
      intentText: text,
      minimumScore,
      queryTokens: [],
      mappings: [],
      reason: "empty intent",
      sources: [],
      errors: ["intent text is empty"],
      allowedExactPaths: [],
      allowedCommunicationPaths: [],
      matchedModuleIds: [],
    };
  }

  const { entries, sources, errors } = collectBoundaryEntries(safeRepoRoot, {
    allowNonOneToOneMapping: Boolean(allowNonOneToOneMapping),
  });
  const nonOneToOneErrors = errors.filter((item) => item.startsWith(`${NON_ONE_TO_ONE_MAPPING_PREFIX}:`));
  if (nonOneToOneErrors.length && !allowNonOneToOneMapping) {
    return {
      passed: false,
      intentText: text,
      minimumScore,
      queryTokens: augmentIntentTokens(text),
      mappings: [],
      reason: "framework boundary mapping is not one-to-one; ask a human to update framework first.",
      sources,
      errors,
      allowedExactPaths: [],
      allowedCommunicationPaths: [],
      matchedModuleIds: [],
    };
  }
  if (!entries.length) {
    return {
      passed: false,
      intentText: text,
      minimumScore,
      queryTokens: augmentIntentTokens(text),
      mappings: [],
      reason: "no canonical boundary bindings available",
      sources,
      errors: errors.length ? errors : ["no canonical boundary bindings"],
      allowedExactPaths: [],
      allowedCommunicationPaths: [],
      matchedModuleIds: [],
    };
  }

  const queryTokens = augmentIntentTokens(text);
  const scored = [];
  for (const entry of entries) {
    const { score, reasons } = scoreEntry(entry, text, queryTokens);
    if (score < minimumScore) {
      continue;
    }
    scored.push({
      projectId: entry.projectId,
      projectFileRelPath: entry.projectFileRelPath,
      canonicalRelPath: entry.canonicalRelPath,
      freshnessStatus: entry.freshnessStatus,
      moduleId: entry.moduleId,
      boundaryId: entry.boundaryId,
      mappingMode: entry.mappingMode,
      note: entry.note,
      score,
      scoreReasons: reasons,
      primaryExactPath: entry.primaryExactPath,
      exactPaths: entry.exactPaths,
      relatedExactPaths: entry.relatedExactPaths,
      primaryCommunicationPath: entry.primaryCommunicationPath,
      communicationPaths: entry.communicationPaths,
      relatedCommunicationPaths: entry.relatedCommunicationPaths,
    });
  }

  const mappings = uniqueMappingItems(scored)
    .sort((left, right) => {
      if (right.score !== left.score) {
        return right.score - left.score;
      }
      if (left.moduleId !== right.moduleId) {
        return left.moduleId.localeCompare(right.moduleId);
      }
      return left.boundaryId.localeCompare(right.boundaryId);
    })
    .slice(0, Math.max(1, Number(maxResults) || MAX_MATCH_COUNT));

  const allowedExact = new Set();
  const allowedCommunication = new Set();
  const matchedModuleIds = new Set();
  for (const mapping of mappings) {
    matchedModuleIds.add(mapping.moduleId);
    for (const exactPath of mapping.exactPaths) {
      allowedExact.add(exactPath);
    }
    for (const communicationPath of mapping.communicationPaths) {
      allowedCommunication.add(communicationPath);
    }
  }

  return {
    passed: mappings.length > 0,
    intentText: text,
    minimumScore,
    queryTokens,
    mappings,
    reason: mappings.length ? "" : "no framework mapping reached threshold",
    sources,
    errors,
    allowedExactPaths: [...allowedExact].sort(),
    allowedCommunicationPaths: [...allowedCommunication].sort(),
    matchedModuleIds: [...matchedModuleIds].sort(),
  };
}

function formatIntentMappingSummary(analysisResult) {
  const mappings = Array.isArray(analysisResult?.mappings) ? analysisResult.mappings : [];
  if (!mappings.length) {
    return "(no mapping)";
  }
  return mappings.map((item, index) => {
    const relatedExactList = item.relatedExactPaths.join(", ");
    return `${index + 1}. ${item.moduleId} / ${item.boundaryId} -> ${item.primaryExactPath} (related: ${relatedExactList})`;
  }).join("\n");
}

module.exports = {
  MAX_MATCH_COUNT,
  NON_ONE_TO_ONE_MAPPING_PREFIX,
  TEMP_BYPASS_ALL_TOKEN,
  TEMP_BYPASS_SCOPES,
  TOKEN_ALIAS_RULES,
  analyzeIntentMapping,
  augmentIntentTokens,
  collectBoundaryEntries,
  formatIntentMappingSummary,
  isTemporaryBypassScopeEnabled,
  normalizeTemporaryBypassScopes,
};
