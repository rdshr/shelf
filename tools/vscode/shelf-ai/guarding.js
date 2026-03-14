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
const WORKSPACE_EVIDENCE_ARTIFACTS = new Set([
  "docs/hierarchy/shelf_evidence_tree.json",
  "docs/hierarchy/shelf_evidence_tree.html",
]);
const WORKSPACE_FRAMEWORK_ARTIFACTS = new Set([
  "docs/hierarchy/shelf_framework_tree.json",
  "docs/hierarchy/shelf_framework_tree.html",
]);
const WORKSPACE_TREE_ARTIFACTS = new Set([
  ...WORKSPACE_EVIDENCE_ARTIFACTS,
  ...WORKSPACE_FRAMEWORK_ARTIFACTS,
]);

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
  return GENERATED_PATTERN.test(normalized) || WORKSPACE_TREE_ARTIFACTS.has(normalized);
}

function isWorkspaceEvidenceArtifact(relPath) {
  return WORKSPACE_EVIDENCE_ARTIFACTS.has(normalizeRelPath(relPath));
}

function isWorkspaceFrameworkArtifact(relPath) {
  return WORKSPACE_FRAMEWORK_ARTIFACTS.has(normalizeRelPath(relPath));
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
  const protectedWorkspaceArtifacts = [];
  const protectedEvidenceArtifacts = [];
  const protectedFrameworkArtifacts = [];
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
      if (WORKSPACE_TREE_ARTIFACTS.has(relPath)) {
        protectedWorkspaceArtifacts.push(relPath);
      }
      if (WORKSPACE_EVIDENCE_ARTIFACTS.has(relPath)) {
        protectedEvidenceArtifacts.push(relPath);
      }
      if (WORKSPACE_FRAMEWORK_ARTIFACTS.has(relPath)) {
        protectedFrameworkArtifacts.push(relPath);
      }
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
    protectedWorkspaceArtifacts,
    protectedEvidenceArtifacts,
    protectedFrameworkArtifacts,
    protectedProjectFiles: [...protectedProjectFiles].sort(),
  };
}

module.exports = {
  WATCH_FILES,
  WATCH_PREFIXES,
  anyWatchedUris,
  classifyWorkspaceChanges,
  discoverProjectFiles,
  inferConfiguredFrameworks,
  isProtectedGeneratedPath,
  isWorkspaceFrameworkArtifact,
  isWorkspaceEvidenceArtifact,
  isWatchedPath,
  isWatchedUri,
  normalizeRelPath,
  resolveProjectFilePath,
  shouldRunMypyForRelPath,
};
