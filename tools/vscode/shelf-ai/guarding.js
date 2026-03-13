const fs = require("fs");
const path = require("path");

const WATCH_PREFIXES = [
  "framework/",
  "specs/",
  "mapping/",
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
  "README.md",
  "pyproject.toml",
  "uv.lock",
]);

const PRODUCT_SPEC_PATTERN = /^projects\/([^/]+)\/product_spec\.toml$/;
const PRODUCT_SPEC_SECTION_PATTERN = /^projects\/([^/]+)\/product_spec\/[^/]+\.toml$/;
const IMPLEMENTATION_CONFIG_PATTERN = /^projects\/([^/]+)\/implementation_config\.toml$/;
const GENERATED_PATTERN = /^projects\/([^/]+)\/generated(?:\/(.+))?$/;
const WORKSPACE_GOVERNANCE_ARTIFACTS = new Set([
  "docs/hierarchy/shelf_governance_tree.json",
  "docs/hierarchy/shelf_governance_tree.html",
]);
const WORKSPACE_FRAMEWORK_ARTIFACTS = new Set([
  "docs/hierarchy/shelf_framework_tree.json",
  "docs/hierarchy/shelf_framework_tree.html",
]);
const WORKSPACE_TREE_ARTIFACTS = new Set([
  ...WORKSPACE_GOVERNANCE_ARTIFACTS,
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
  const relPath = path.relative(workspaceRoot, uri.fsPath);
  return isWatchedPath(relPath);
}

function anyWatchedUris(uris, workspaceRoot) {
  return uris.some((uri) => isWatchedUri(uri, workspaceRoot));
}

function discoverProductSpecFiles(repoRoot) {
  const projectsDir = path.join(repoRoot, "projects");
  if (!fs.existsSync(projectsDir) || !fs.statSync(projectsDir).isDirectory()) {
    return [];
  }

  const files = [];
  for (const entry of fs.readdirSync(projectsDir)) {
    const productSpecFile = path.join(projectsDir, entry, "product_spec.toml");
    if (fs.existsSync(productSpecFile) && fs.statSync(productSpecFile).isFile()) {
      files.push(productSpecFile);
    }
  }
  return files.sort();
}

function inferConfiguredFrameworks(productSpecText) {
  const frameworks = new Set();
  const lines = String(productSpecText).split(/\r?\n/);
  let inFrameworkSection = false;
  for (const lineText of lines) {
    const sectionMatch = /^\s*\[([A-Za-z0-9_.-]+)\]\s*$/.exec(lineText);
    if (sectionMatch) {
      inFrameworkSection = sectionMatch[1] === "framework";
      continue;
    }
    if (!inFrameworkSection) {
      continue;
    }
    const valueMatch = /^\s*[A-Za-z0-9_-]+\s*=\s*"framework\/([^/]+)\//.exec(lineText);
    if (valueMatch) {
      frameworks.add(valueMatch[1]);
    }
  }
  return frameworks;
}

function resolveProjectProductSpecPath(repoRoot, relPath) {
  const normalized = normalizeRelPath(relPath);
  let match = normalized.match(PRODUCT_SPEC_PATTERN);
  if (match) {
    return path.join(repoRoot, "projects", match[1], "product_spec.toml");
  }

  match = normalized.match(IMPLEMENTATION_CONFIG_PATTERN);
  if (match) {
    return path.join(repoRoot, "projects", match[1], "product_spec.toml");
  }

  match = normalized.match(PRODUCT_SPEC_SECTION_PATTERN);
  if (match) {
    return path.join(repoRoot, "projects", match[1], "product_spec.toml");
  }

  match = normalized.match(GENERATED_PATTERN);
  if (match) {
    return path.join(repoRoot, "projects", match[1], "product_spec.toml");
  }

  return null;
}

function isProtectedGeneratedPath(relPath) {
  const normalized = normalizeRelPath(relPath);
  return GENERATED_PATTERN.test(normalized) || WORKSPACE_TREE_ARTIFACTS.has(normalized);
}

function isWorkspaceGovernanceArtifact(relPath) {
  return WORKSPACE_GOVERNANCE_ARTIFACTS.has(normalizeRelPath(relPath));
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
  const protectedProjectSpecs = new Set();
  const protectedWorkspaceArtifacts = [];
  const protectedGovernanceArtifacts = [];
  const protectedFrameworkArtifacts = [];
  let shouldRunMypy = false;
  let discoveredProductSpecFiles = null;

  const getProductSpecFiles = () => {
    if (!discoveredProductSpecFiles) {
      discoveredProductSpecFiles = discoverProductSpecFiles(repoRoot);
    }
    return discoveredProductSpecFiles;
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
      if (WORKSPACE_GOVERNANCE_ARTIFACTS.has(relPath)) {
        protectedGovernanceArtifacts.push(relPath);
      }
      if (WORKSPACE_FRAMEWORK_ARTIFACTS.has(relPath)) {
        protectedFrameworkArtifacts.push(relPath);
      }
      const protectedSpec = resolveProjectProductSpecPath(repoRoot, relPath);
      if (protectedSpec) {
        protectedProjectSpecs.add(protectedSpec);
      }
      continue;
    }

    if (
      PRODUCT_SPEC_PATTERN.test(relPath) ||
      PRODUCT_SPEC_SECTION_PATTERN.test(relPath) ||
      IMPLEMENTATION_CONFIG_PATTERN.test(relPath)
    ) {
      const productSpecFile = resolveProjectProductSpecPath(repoRoot, relPath);
      if (productSpecFile) {
        materializeProjects.add(productSpecFile);
      }
      continue;
    }

    if (relPath.startsWith("framework/")) {
      const frameworkName = relPath.split("/")[1];
      if (!frameworkName) {
        for (const productSpecFile of getProductSpecFiles()) {
          materializeProjects.add(productSpecFile);
        }
        continue;
      }

      for (const productSpecFile of getProductSpecFiles()) {
        try {
          const productSpecText = fs.readFileSync(productSpecFile, "utf8");
          const configuredFrameworks = inferConfiguredFrameworks(productSpecText);
          if (configuredFrameworks.has(frameworkName)) {
            materializeProjects.add(productSpecFile);
          }
        } catch {
          materializeProjects.add(productSpecFile);
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
    protectedGovernanceArtifacts,
    protectedFrameworkArtifacts,
    protectedProjectSpecs: [...protectedProjectSpecs].sort(),
  };
}

module.exports = {
  WATCH_FILES,
  WATCH_PREFIXES,
  anyWatchedUris,
  classifyWorkspaceChanges,
  discoverProductSpecFiles,
  inferConfiguredFrameworks,
  isProtectedGeneratedPath,
  isWorkspaceFrameworkArtifact,
  isWorkspaceGovernanceArtifact,
  isWatchedPath,
  isWatchedUri,
  normalizeRelPath,
  resolveProjectProductSpecPath,
  shouldRunMypyForRelPath,
};
