const fs = require("fs");
const path = require("path");

const WATCH_PREFIXES = [
  "framework/",
  "specs/",
  "src/",
  "projects/",
  "scripts/",
  "docs/",
  "tests/",
  "tools/",
  ".githooks/",
];

const WATCH_FILES = new Set([
  "AGENTS.md",
  "CONTRIBUTING.md",
  "README.md",
  "pyproject.toml",
  "uv.lock",
]);

const PROJECT_FILE_PATTERN = /^projects\/([^/]+)\/project\.toml$/;
const GENERATED_PATTERN = /^projects\/([^/]+)\/generated(?:\/(.+))?$/;

function normalizeRelPath(relPath) {
  if (typeof relPath !== "string") {
    return "";
  }
  return relPath.replace(/\\/g, "/").replace(/^\/+/, "");
}

function isWatchedPath(relPath) {
  const normalized = normalizeRelPath(relPath);
  if (!normalized || normalized.startsWith("..")) {
    return false;
  }
  if (WATCH_FILES.has(normalized)) {
    return true;
  }
  return WATCH_PREFIXES.some((prefix) => normalized.startsWith(prefix));
}

function isWatchedUri(uri, workspaceRoot) {
  if (!uri || !workspaceRoot) {
    return false;
  }
  return isWatchedPath(path.relative(workspaceRoot, uri.fsPath));
}

function anyWatchedUris(uris, workspaceRoot) {
  return uris.some((uri) => isWatchedUri(uri, workspaceRoot));
}

function discoverProjectFiles(repoRoot) {
  const projectsDir = path.join(repoRoot, "projects");
  if (!fs.existsSync(projectsDir) || !fs.statSync(projectsDir).isDirectory()) {
    return [];
  }

  const files = [];
  for (const entry of fs.readdirSync(projectsDir)) {
    const projectFile = path.join(projectsDir, entry, "project.toml");
    if (fs.existsSync(projectFile) && fs.statSync(projectFile).isFile()) {
      files.push(projectFile);
    }
  }
  return files.sort();
}

function inferConfiguredFrameworks(projectConfigText) {
  const frameworks = new Set();
  const lines = String(projectConfigText).split(/\r?\n/);
  for (const lineText of lines) {
    const valueMatch = /^\s*framework_file\s*=\s*"framework\/([^/]+)\//.exec(lineText);
    if (valueMatch) {
      frameworks.add(valueMatch[1]);
    }
  }
  return frameworks;
}

function inferConfiguredFrameworkFiles(projectConfigText) {
  const frameworkFiles = new Set();
  const lines = String(projectConfigText).split(/\r?\n/);
  for (const lineText of lines) {
    const valueMatch = /^\s*framework_file\s*=\s*"([^"]+)"/.exec(lineText);
    if (valueMatch) {
      frameworkFiles.add(normalizeRelPath(valueMatch[1]));
    }
  }
  return frameworkFiles;
}

function canonicalPathForProjectFile(projectFilePath) {
  return path.join(path.dirname(projectFilePath), "generated", "canonical.json");
}

function safeReadCanonical(canonicalPath) {
  try {
    const raw = JSON.parse(fs.readFileSync(canonicalPath, "utf8"));
    return raw && typeof raw === "object"
      ? { ok: true, canonical: raw }
      : { ok: false, reason: "canonical.json must decode into an object" };
  } catch (error) {
    return {
      ok: false,
      reason: error instanceof Error ? error.message : String(error),
    };
  }
}

function addSourceRefPaths(target, items) {
  for (const item of Array.isArray(items) ? items : []) {
    const relPath = normalizeRelPath(String(item?.source_ref?.file_path || ""));
    if (relPath) {
      target.add(relPath);
    }
  }
}

function collectCanonicalSourceRelPaths(repoRoot, projectFilePath, projectConfigText, canonical) {
  const relPaths = new Set([
    normalizeRelPath(path.relative(repoRoot, projectFilePath)),
  ]);

  for (const frameworkFile of inferConfiguredFrameworkFiles(projectConfigText)) {
    relPaths.add(frameworkFile);
  }

  for (const frameworkModule of Array.isArray(canonical?.framework?.modules) ? canonical.framework.modules : []) {
    const relPath = normalizeRelPath(String(frameworkModule?.framework_file || ""));
    if (relPath) {
      relPaths.add(relPath);
    }
  }

  addSourceRefPaths(relPaths, canonical?.config?.modules);
  addSourceRefPaths(relPaths, canonical?.code?.modules);
  addSourceRefPaths(relPaths, canonical?.evidence?.modules);

  return [...relPaths].sort();
}

function getProjectCanonicalFreshness(repoRoot, projectFilePath) {
  const resolvedProjectFile = path.resolve(projectFilePath);
  const projectId = path.basename(path.dirname(resolvedProjectFile));
  const canonicalPath = canonicalPathForProjectFile(resolvedProjectFile);
  const canonicalRelPath = normalizeRelPath(path.relative(repoRoot, canonicalPath));
  let projectConfigText = "";

  try {
    projectConfigText = fs.readFileSync(resolvedProjectFile, "utf8");
  } catch (error) {
    return {
      projectId,
      projectFilePath: resolvedProjectFile,
      canonicalPath,
      canonicalRelPath,
      status: "invalid",
      reason: error instanceof Error ? error.message : String(error),
      authoritativeSourceRelPaths: [],
      newerSourceRelPaths: [],
      missingSourceRelPaths: [],
    };
  }

  if (!fs.existsSync(canonicalPath) || !fs.statSync(canonicalPath).isFile()) {
    return {
      projectId,
      projectFilePath: resolvedProjectFile,
      canonicalPath,
      canonicalRelPath,
      status: "missing",
      reason: "canonical.json is missing",
      authoritativeSourceRelPaths: collectCanonicalSourceRelPaths(repoRoot, resolvedProjectFile, projectConfigText, {}),
      newerSourceRelPaths: [],
      missingSourceRelPaths: [],
    };
  }

  const canonicalRead = safeReadCanonical(canonicalPath);
  if (!canonicalRead.ok) {
    return {
      projectId,
      projectFilePath: resolvedProjectFile,
      canonicalPath,
      canonicalRelPath,
      status: "invalid",
      reason: canonicalRead.reason,
      authoritativeSourceRelPaths: collectCanonicalSourceRelPaths(repoRoot, resolvedProjectFile, projectConfigText, {}),
      newerSourceRelPaths: [],
      missingSourceRelPaths: [],
    };
  }

  const canonicalStat = fs.statSync(canonicalPath);
  const authoritativeSourceRelPaths = collectCanonicalSourceRelPaths(
    repoRoot,
    resolvedProjectFile,
    projectConfigText,
    canonicalRead.canonical
  );
  const newerSourceRelPaths = [];
  const missingSourceRelPaths = [];

  for (const relPath of authoritativeSourceRelPaths) {
    const absPath = path.join(repoRoot, relPath);
    if (!fs.existsSync(absPath) || !fs.statSync(absPath).isFile()) {
      missingSourceRelPaths.push(relPath);
      continue;
    }
    const sourceStat = fs.statSync(absPath);
    if (sourceStat.mtimeMs > canonicalStat.mtimeMs) {
      newerSourceRelPaths.push(relPath);
    }
  }

  const status = newerSourceRelPaths.length || missingSourceRelPaths.length
    ? "stale"
    : "fresh";

  return {
    projectId,
    projectFilePath: resolvedProjectFile,
    canonicalPath,
    canonicalRelPath,
    status,
    reason: status === "fresh" ? "" : "canonical.json is older than its authoritative sources",
    authoritativeSourceRelPaths,
    newerSourceRelPaths,
    missingSourceRelPaths,
  };
}

function summarizeCanonicalFreshness(repoRoot) {
  const projects = discoverProjectFiles(repoRoot).map((projectFile) =>
    getProjectCanonicalFreshness(repoRoot, projectFile)
  );
  const blockingProjects = projects.filter((project) => project.status !== "fresh");
  return {
    projects,
    blockingProjects,
    hasBlockingProjects: blockingProjects.length > 0,
  };
}

function resolveProjectFilePath(repoRoot, relPath) {
  const normalized = normalizeRelPath(relPath);
  let match = normalized.match(PROJECT_FILE_PATTERN);
  if (match) {
    return path.join(repoRoot, "projects", match[1], "project.toml");
  }

  match = normalized.match(GENERATED_PATTERN);
  if (match) {
    return path.join(repoRoot, "projects", match[1], "project.toml");
  }

  return null;
}

function isProtectedGeneratedPath(relPath) {
  const normalized = normalizeRelPath(relPath);
  return GENERATED_PATTERN.test(normalized);
}

function shouldRunMypyForRelPath(relPath) {
  const normalized = normalizeRelPath(relPath);
  if (!normalized.endsWith(".py")) {
    return false;
  }
  return (
    normalized.startsWith("src/") ||
    normalized.startsWith("scripts/") ||
    normalized.startsWith("tests/")
  );
}

function classifyWorkspaceChanges(repoRoot, relPaths) {
  const uniqueRelPaths = [...new Set((relPaths || []).map(normalizeRelPath).filter(Boolean))];
  const watchedRelPaths = uniqueRelPaths.filter(isWatchedPath);
  const materializeProjects = new Set();
  const protectedGeneratedPaths = [];
  const protectedProjectFiles = new Set();
  let shouldRunMypy = false;
  let discoveredProjectFiles = null;

  const getProjectFiles = () => {
    if (!discoveredProjectFiles) {
      discoveredProjectFiles = discoverProjectFiles(repoRoot);
    }
    return discoveredProjectFiles;
  };

  for (const relPath of watchedRelPaths) {
    if (shouldRunMypyForRelPath(relPath)) {
      shouldRunMypy = true;
    }

    if (isProtectedGeneratedPath(relPath)) {
      protectedGeneratedPaths.push(relPath);
      const protectedProjectFile = resolveProjectFilePath(repoRoot, relPath);
      if (protectedProjectFile) {
        protectedProjectFiles.add(protectedProjectFile);
      }
      continue;
    }

    if (PROJECT_FILE_PATTERN.test(relPath)) {
      const projectFile = resolveProjectFilePath(repoRoot, relPath);
      if (projectFile) {
        materializeProjects.add(projectFile);
      }
      continue;
    }

    if (relPath.startsWith("framework/")) {
      const frameworkName = relPath.split("/")[1];
      if (!frameworkName) {
        for (const projectFile of getProjectFiles()) {
          materializeProjects.add(projectFile);
        }
        continue;
      }

      for (const projectFile of getProjectFiles()) {
        try {
          const projectText = fs.readFileSync(projectFile, "utf8");
          const configuredFrameworks = inferConfiguredFrameworks(projectText);
          if (configuredFrameworks.has(frameworkName)) {
            materializeProjects.add(projectFile);
          }
        } catch {
          materializeProjects.add(projectFile);
        }
      }
    }
  }

  return {
    relPaths: watchedRelPaths,
    shouldRunMypy,
    shouldMaterialize: materializeProjects.size > 0,
    materializeProjects: [...materializeProjects].sort(),
    protectedGeneratedPaths,
    protectedProjectFiles: [...protectedProjectFiles].sort(),
  };
}

module.exports = {
  canonicalPathForProjectFile,
  WATCH_FILES,
  WATCH_PREFIXES,
  anyWatchedUris,
  classifyWorkspaceChanges,
  getProjectCanonicalFreshness,
  discoverProjectFiles,
  inferConfiguredFrameworkFiles,
  inferConfiguredFrameworks,
  isProtectedGeneratedPath,
  isWatchedPath,
  isWatchedUri,
  normalizeRelPath,
  resolveProjectFilePath,
  shouldRunMypyForRelPath,
  summarizeCanonicalFreshness,
};
