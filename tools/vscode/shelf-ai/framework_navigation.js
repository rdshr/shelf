const fs = require("fs");
const path = require("path");
const correspondenceRuntime = require("./correspondence_runtime");
const workspaceGuard = require("./guarding");

const FRAMEWORK_FILE_PATH_PATTERN = /^(framework|framework_drafts)\/([^/]+)\/L(\d+)-M(\d+)-[^/]+\.md$/;
const MODULE_REF_WITH_RULES_PATTERN =
  /(?:(?<framework>[A-Za-z][A-Za-z0-9_-]*)\.)?L(?<level>\d+)\.M(?<module>\d+)\[(?<rules>[^\]]+)\]/g;
const MODULE_REF_PATTERN = /(?:(?<framework>[A-Za-z][A-Za-z0-9_-]*)\.)?L(?<level>\d+)\.M(?<module>\d+)/g;
const RULE_TOKEN_PATTERN = /R\d+(?:\.\d+)?/g;
const CORE_TOKEN_PATTERN = /R\d+\.\d+|R\d+|B\d+|C\d+|V\d+/g;
const UPPER_SYMBOL_PATTERN = /[A-Z][A-Z0-9_]+/g;
const BACKTICK_SEGMENT_PATTERN = /`([^`]+)`/g;
const SYMBOL_TOKEN_PATTERN = /[A-Za-z][A-Za-z0-9_]*/g;
const TOML_SECTION_PATTERN = /^\s*\[([A-Za-z0-9_.-]+)\]\s*$/;
const DEFAULT_PROJECT_FILE = path.join("projects", "knowledge_base_basic", "project.toml");

const SECTION_PREFIXES = [
  ["## 1. 能力声明", "capability"],
  ["## 2. 参数定义", "boundary"],
  ["## 2. 边界定义", "boundary"],
  ["## 3. 最小可行基", "base"],
  ["## 4. 基组合原则", "rule"],
  ["## 5. 验证", "verification"],
];

function uniqueSections(sections) {
  const ordered = [];
  const seen = new Set();
  for (const section of sections) {
    if (!section || seen.has(section)) {
      continue;
    }
    seen.add(section);
    ordered.push(section);
  }
  return ordered;
}

function normalizeConfigSection(section) {
  if (!section) {
    return "";
  }
  if (section.startsWith("exact.") || section.startsWith("communication.") || section.startsWith("framework.")) {
    return section;
  }
  return section;
}

function createBoundaryConfigMapping(primarySection, relatedSections = [primarySection], options = {}) {
  const normalizedPrimarySection = normalizeConfigSection(primarySection);
  return {
    primarySection: normalizedPrimarySection,
    relatedSections: uniqueSections([normalizedPrimarySection, ...relatedSections.map(normalizeConfigSection)]),
    mappingMode: options.mappingMode || "direct",
    note: options.note || "",
  };
}

function normalizePathSlashes(value) {
  return value.replace(/\\/g, "/");
}

function getFrameworkDocumentInfo(filePath, repoRoot) {
  const relativePath = normalizePathSlashes(path.relative(repoRoot, filePath));
  const match = FRAMEWORK_FILE_PATH_PATTERN.exec(relativePath);
  if (!match) {
    return null;
  }
  return {
    relativePath,
    treeRoot: match[1],
    frameworkName: match[2],
    level: `L${match[3]}`,
    moduleId: `M${match[4]}`,
  };
}

function isFrameworkMarkdownFile(filePath, repoRoot) {
  return getFrameworkDocumentInfo(filePath, repoRoot) !== null;
}

function detectSection(lineText) {
  for (const [prefix, section] of SECTION_PREFIXES) {
    if (lineText.startsWith(prefix)) {
      return section;
    }
  }
  return "";
}

function registerSymbol(symbols, token, line, character) {
  if (!token || symbols.has(token)) {
    return;
  }
  symbols.set(token, {
    line,
    character,
    length: token.length,
  });
}

function createAnchor(lineText, line) {
  const trimmed = lineText.trim();
  return {
    line,
    character: Math.max(0, lineText.indexOf(trimmed)),
    length: Math.max(1, trimmed.length),
  };
}

function trimListMarker(lineText) {
  return lineText.trim().replace(/^[-*]\s*/, "");
}

function extractAfterColon(text) {
  const match = /[:：]\s*(.+)$/.exec(text.trim());
  return match ? match[1].trim() : "";
}

function buildDefinitionIndex(text) {
  const symbols = new Map();
  const boundaryIds = new Set();
  const sectionHeaders = {};
  const capabilities = [];
  const boundaries = [];
  const bases = [];
  const verifications = [];
  const rules = [];
  const itemByToken = new Map();
  const ruleByToken = new Map();
  const lines = text.split(/\r?\n/);
  let section = "";
  let header = null;
  let headerText = "";
  let currentRule = null;

  for (let lineIndex = 0; lineIndex < lines.length; lineIndex += 1) {
    const lineText = lines[lineIndex];
    const trimmed = lineText.trim();
    const sectionName = detectSection(trimmed);
    if (sectionName) {
      section = sectionName;
      if (!sectionHeaders[sectionName]) {
        sectionHeaders[sectionName] = createAnchor(lineText, lineIndex);
      }
    } else if (trimmed.startsWith("## ")) {
      section = "";
    }

    if (!header) {
      const headingMatch = /^\s*#\s+/.exec(lineText);
      if (headingMatch) {
        header = {
          line: lineIndex,
          character: headingMatch[0].length,
          length: Math.max(1, lineText.trim().length - 2),
        };
        headerText = lineText.replace(/^\s*#\s+/, "").trim();
      }
    }

    if (section === "capability") {
      const match = /^\s*[-*]\s*`(C\d+)`/.exec(lineText);
      if (match) {
        const token = match[1];
        const character = match.index + match[0].indexOf(token);
        const item = {
          kind: "capability",
          token,
          text: trimListMarker(lineText),
          line: lineIndex,
          character,
          length: token.length,
        };
        registerSymbol(symbols, token, lineIndex, character);
        capabilities.push(item);
        itemByToken.set(token, item);
      }
      continue;
    }

    if (section === "boundary") {
      const match = /^\s*[-*]\s*`([A-Za-z][A-Za-z0-9_]*)`/.exec(lineText);
      if (match) {
        const token = match[1];
        const character = match.index + match[0].indexOf(token);
        const item = {
          kind: "boundary",
          token,
          text: trimListMarker(lineText),
          line: lineIndex,
          character,
          length: token.length,
        };
        boundaryIds.add(token);
        registerSymbol(symbols, token, lineIndex, character);
        boundaries.push(item);
        itemByToken.set(token, item);
      }
      continue;
    }

    if (section === "base") {
      const match = /^\s*[-*]\s*`(B\d+)`/.exec(lineText);
      if (match) {
        const token = match[1];
        const character = match.index + match[0].indexOf(token);
        const item = {
          kind: "base",
          token,
          text: trimListMarker(lineText),
          line: lineIndex,
          character,
          length: token.length,
        };
        registerSymbol(symbols, token, lineIndex, character);
        bases.push(item);
        itemByToken.set(token, item);
      }
      continue;
    }

    if (section === "rule") {
      const topMatch = /^\s*[-*]\s*`(R\d+)`\s*/.exec(lineText);
      if (topMatch) {
        const token = topMatch[1];
        const character = topMatch.index + topMatch[0].indexOf(token);
        const textValue = trimListMarker(lineText);
        const item = {
          kind: "rule",
          token,
          text: textValue,
          title: textValue.replace(/^`R\d+`\s*/, "").trim(),
          line: lineIndex,
          character,
          length: token.length,
          participatingBases: "",
          combination: "",
          output: "",
          boundary: "",
          children: [],
        };
        registerSymbol(symbols, token, lineIndex, character);
        rules.push(item);
        ruleByToken.set(token, item);
        itemByToken.set(token, item);
        currentRule = item;
        continue;
      }

      const childMatch = /^\s*[-*]\s*`(R\d+\.\d+)`\s*/.exec(lineText);
      if (childMatch) {
        const token = childMatch[1];
        const character = childMatch.index + childMatch[0].indexOf(token);
        const textValue = trimListMarker(lineText);
        const parentToken = token.split(".", 1)[0];
        const item = {
          kind: "ruleChild",
          token,
          text: textValue,
          line: lineIndex,
          character,
          length: token.length,
          parentToken,
        };
        registerSymbol(symbols, token, lineIndex, character);
        itemByToken.set(token, item);
        const parentRule = ruleByToken.get(parentToken) || currentRule;
        if (parentRule) {
          parentRule.children.push(item);
          if (token.endsWith(".1")) {
            parentRule.participatingBases = extractAfterColon(textValue);
          } else if (token.endsWith(".2")) {
            parentRule.combination = extractAfterColon(textValue);
          } else if (token.endsWith(".3")) {
            parentRule.output = extractAfterColon(textValue);
          } else if (token.endsWith(".4")) {
            parentRule.boundary = extractAfterColon(textValue);
          }
        }
        if (lineText.includes("输出结构")) {
          for (const segmentMatch of lineText.matchAll(BACKTICK_SEGMENT_PATTERN)) {
            const segment = segmentMatch[1];
            const segmentOffset = (segmentMatch.index || 0) + 1;
            for (const tokenMatch of segment.matchAll(SYMBOL_TOKEN_PATTERN)) {
              const token = tokenMatch[0];
              if (
                /^C\d+$/.test(token) ||
                /^B\d+$/.test(token) ||
                /^V\d+$/.test(token) ||
                /^R\d+(?:\.\d+)?$/.test(token) ||
                boundaryIds.has(token)
              ) {
                continue;
              }
              registerSymbol(symbols, token, lineIndex, segmentOffset + (tokenMatch.index || 0));
              itemByToken.set(token, {
                kind: "derivedSymbol",
                token,
                text: textValue,
                line: lineIndex,
                character: segmentOffset + (tokenMatch.index || 0),
                length: token.length,
                parentToken,
              });
            }
          }
        }
      }
      continue;
    }

    if (section === "verification") {
      const match = /^\s*[-*]\s*`(V\d+)`/.exec(lineText);
      if (match) {
        const token = match[1];
        const character = match.index + match[0].indexOf(token);
        const item = {
          kind: "verification",
          token,
          text: trimListMarker(lineText),
          line: lineIndex,
          character,
          length: token.length,
        };
        registerSymbol(symbols, token, lineIndex, character);
        verifications.push(item);
        itemByToken.set(token, item);
      }
    }
  }

  return {
    header,
    headerText,
    sectionHeaders,
    symbols,
    capabilities,
    boundaries,
    bases,
    verifications,
    rules,
    itemByToken,
  };
}

function containsPosition(start, end, character) {
  return character >= start && character < end;
}

function findTokenContext(lineText, character) {
  for (const match of lineText.matchAll(MODULE_REF_WITH_RULES_PATTERN)) {
    const moduleRefText = match[0].slice(0, match[0].indexOf("["));
    const start = match.index || 0;
    const ruleBlockStart = start + moduleRefText.length + 1;
    const rulesText = match.groups?.rules || "";
    for (const ruleMatch of rulesText.matchAll(RULE_TOKEN_PATTERN)) {
      const ruleStart = ruleBlockStart + (ruleMatch.index || 0);
      const ruleEnd = ruleStart + ruleMatch[0].length;
      if (!containsPosition(ruleStart, ruleEnd, character)) {
        continue;
      }
      return {
        kind: "moduleRule",
        token: ruleMatch[0],
        start: ruleStart,
        end: ruleEnd,
        frameworkName: match.groups?.framework || null,
        level: `L${match.groups?.level || ""}`,
        moduleId: `M${match.groups?.module || ""}`,
      };
    }
  }

  for (const match of lineText.matchAll(MODULE_REF_PATTERN)) {
    const start = match.index || 0;
    const end = start + match[0].length;
    if (!containsPosition(start, end, character)) {
      continue;
    }
    return {
      kind: "moduleRef",
      token: match[0],
      start,
      end,
      frameworkName: match.groups?.framework || null,
      level: `L${match.groups?.level || ""}`,
      moduleId: `M${match.groups?.module || ""}`,
    };
  }

  for (const match of lineText.matchAll(CORE_TOKEN_PATTERN)) {
    const start = match.index || 0;
    const end = start + match[0].length;
    if (!containsPosition(start, end, character)) {
      continue;
    }
    return {
      kind: "localSymbol",
      token: match[0],
      start,
      end,
    };
  }

  for (const match of lineText.matchAll(UPPER_SYMBOL_PATTERN)) {
    const start = match.index || 0;
    const end = start + match[0].length;
    if (!containsPosition(start, end, character)) {
      continue;
    }
    return {
      kind: "localSymbol",
      token: match[0],
      start,
      end,
    };
  }

  return null;
}

function resolveModuleFile(repoRoot, currentFrameworkName, refFrameworkName, level, moduleId, preferredTreeRoot = "framework") {
  const frameworkName = refFrameworkName || currentFrameworkName;
  if (!frameworkName || !level || !moduleId) {
    return null;
  }

  const prefix = `${level}-${moduleId}-`;
  const searchRoots = [];
  if (preferredTreeRoot) {
    searchRoots.push(preferredTreeRoot);
  }
  for (const candidateRoot of ["framework", "framework_drafts"]) {
    if (!searchRoots.includes(candidateRoot)) {
      searchRoots.push(candidateRoot);
    }
  }

  for (const treeRoot of searchRoots) {
    const moduleDir = path.join(repoRoot, treeRoot, frameworkName);
    if (!fs.existsSync(moduleDir) || !fs.statSync(moduleDir).isDirectory()) {
      continue;
    }
    for (const entry of fs.readdirSync(moduleDir)) {
      if (!entry.endsWith(".md")) {
        continue;
      }
      if (entry.startsWith(prefix)) {
        return path.join(moduleDir, entry);
      }
    }
  }
  return null;
}

function buildTomlSectionIndex(text) {
  const sections = new Map();
  const lines = text.split(/\r?\n/);
  for (let lineIndex = 0; lineIndex < lines.length; lineIndex += 1) {
    const lineText = lines[lineIndex];
    const match = TOML_SECTION_PATTERN.exec(lineText);
    if (!match) {
      continue;
    }
    const sectionName = match[1];
    sections.set(sectionName, {
      line: lineIndex,
      character: lineText.indexOf("["),
      length: lineText.trim().length,
    });
  }
  return sections;
}

function resolveTomlSectionTarget(projectFilePath, sectionNames) {
  const wantedSections = [...new Set((sectionNames || []).filter(Boolean))];
  const targetText = fs.readFileSync(projectFilePath, "utf8");
  const sectionIndex = buildTomlSectionIndex(targetText);
  for (const sectionName of wantedSections) {
    const sectionTarget = sectionIndex.get(sectionName);
    if (!sectionTarget) {
      continue;
    }
    return {
      filePath: projectFilePath,
      line: sectionTarget.line,
      character: sectionTarget.character,
      length: sectionTarget.length,
      targetSection: sectionName,
    };
  }
  return null;
}

function readProjectCanonical(projectFilePath) {
  const canonicalPath = path.join(path.dirname(projectFilePath), "generated", "canonical.json");
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

function readCanonicalBoundaryProjection(canonical, moduleId, token) {
  const frameworkModules = Array.isArray(canonical?.framework?.modules) ? canonical.framework.modules : [];
  const frameworkModule = frameworkModules.find(
    (item) => item && typeof item === "object" && String(item.module_id || "") === moduleId
  );
  if (!frameworkModule) {
    return null;
  }
  const boundaries = Array.isArray(frameworkModule.boundaries) ? frameworkModule.boundaries : [];
  const boundary = boundaries.find(
    (item) => item && typeof item === "object" && String(item.boundary_id || "") === token
  );
  if (!boundary || typeof boundary.config_projection !== "object" || !boundary.config_projection) {
    return null;
  }
  return boundary.config_projection;
}

function readCorrespondenceBoundaryObject(repoRoot, projectFilePath, moduleId, token) {
  const canonical = readProjectCanonical(projectFilePath);
  if (!canonical) {
    return null;
  }
  const correspondence = correspondenceRuntime.readCorrespondenceApi(
    repoRoot,
    correspondenceRuntime.resolveCorrespondenceApiPaths(canonical).root,
    { projectFilePath }
  );
  if (!correspondence || typeof correspondence !== "object" || !correspondence.object_index) {
    return null;
  }
  return correspondence.object_index[`${moduleId}::boundary::${token}`] || null;
}

function canonicalBoundaryConfigMapping(repoRoot, frameworkName, moduleId, token) {
  const projectFilePath = resolvePreferredProjectFile(repoRoot, frameworkName);
  if (!projectFilePath || !moduleId) {
    return null;
  }
  const freshness = workspaceGuard.getProjectCanonicalFreshness(repoRoot, projectFilePath);
  if (freshness.status !== "fresh") {
    return null;
  }
  const canonical = readProjectCanonical(projectFilePath);
  if (!canonical) {
    return null;
  }
  const boundaryObject = readCorrespondenceBoundaryObject(repoRoot, projectFilePath, moduleId, token);
  if (boundaryObject) {
    const configTarget = correspondenceRuntime.resolveTargetByKind(boundaryObject, "config_source")
      || correspondenceRuntime.resolvePrimaryNavigationTarget(boundaryObject);
    if (configTarget && configTarget.target_kind === "config_source") {
      const primarySection = normalizeConfigSection(String(configTarget.symbol || ""));
      const projection = readCanonicalBoundaryProjection(canonical, moduleId, token);
      const relatedSections = Array.isArray(projection?.related_exact_paths)
        ? projection.related_exact_paths.map((item) => normalizeConfigSection(String(item || ""))).filter(Boolean)
        : [primarySection];
      return {
        projectFilePath,
        mapping: createBoundaryConfigMapping(primarySection, relatedSections, {
          mappingMode: String(projection?.mapping_mode || "direct"),
          note: String(projection?.note || ""),
        }),
        objectId: String(boundaryObject.object_id || ""),
      };
    }
  }
  const projection = readCanonicalBoundaryProjection(canonical, moduleId, token);
  if (!projection) {
    return null;
  }
  const primarySection = normalizeConfigSection(String(projection.primary_exact_path || ""));
  const relatedSections = Array.isArray(projection.related_exact_paths)
    ? projection.related_exact_paths.map((item) => normalizeConfigSection(String(item || ""))).filter(Boolean)
    : [primarySection];
  return {
    projectFilePath,
    mapping: createBoundaryConfigMapping(primarySection, relatedSections, {
      mappingMode: String(projection.mapping_mode || "direct"),
      note: String(projection.note || ""),
    }),
    objectId: "",
  };
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

function inferConfiguredFrameworks(projectText) {
  const frameworks = new Set();
  const lines = String(projectText).split(/\r?\n/);
  for (const lineText of lines) {
    const valueMatch = /^\s*framework_file\s*=\s*"framework\/([^/]+)\//.exec(lineText);
    if (valueMatch) {
      frameworks.add(valueMatch[1]);
    }
  }
  return frameworks;
}

function resolvePreferredProjectFile(repoRoot, frameworkName) {
  const candidates = discoverProjectFiles(repoRoot);
  const preferredDefault = path.join(repoRoot, DEFAULT_PROJECT_FILE);
  let bestFile = null;
  let bestScore = -1;
  for (const filePath of candidates) {
    let score = filePath === preferredDefault ? 1 : 0;
    try {
      const frameworks = inferConfiguredFrameworks(fs.readFileSync(filePath, "utf8"));
      if (frameworks.has(frameworkName)) {
        score += 10;
      }
    } catch {
      // Ignore broken product spec files here; main parser/validator handles them elsewhere.
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

function resolveBoundaryConfigTarget(repoRoot, frameworkName, moduleId, token) {
  const mappingResult = canonicalBoundaryConfigMapping(repoRoot, frameworkName, moduleId, token);
  if (!mappingResult || !mappingResult.mapping) {
    return null;
  }
  const mapping = mappingResult.mapping;
  const projectFilePath = mappingResult.projectFilePath;
  if (!projectFilePath || !fs.existsSync(projectFilePath)) {
    return null;
  }
  const orderedSections = [mapping.primarySection, ...mapping.relatedSections];
  const sectionTarget = resolveTomlSectionTarget(projectFilePath, orderedSections);
  if (!sectionTarget) {
    return null;
  }
  return {
    filePath: sectionTarget.filePath,
    line: sectionTarget.line,
    character: sectionTarget.character,
    length: sectionTarget.length,
    primarySection: mapping.primarySection,
    targetSection: sectionTarget.targetSection,
    relatedSections: mapping.relatedSections,
    mappingMode: mapping.mappingMode,
    note: mapping.note,
    objectId: String(mappingResult.objectId || ""),
  };
}

function resolveLocalSymbol(index, token) {
  const direct = index.symbols.get(token);
  if (direct) {
    return direct;
  }
  if (/^R\d+\.\d+$/.test(token)) {
    return index.symbols.get(token.split(".", 1)[0]) || null;
  }
  return null;
}

function resolveModuleTarget(index) {
  if (index.bases.length > 0) {
    const firstBase = index.bases[0];
    return {
      line: firstBase.line,
      character: firstBase.character,
      length: firstBase.length,
    };
  }

  if (index.sectionHeaders.base) {
    return index.sectionHeaders.base;
  }

  return index.header;
}

function buildModuleLabel(moduleInfo) {
  return moduleInfo
    ? `${moduleInfo.frameworkName}.${moduleInfo.level}.${moduleInfo.moduleId}`
    : "module";
}

function canonicalModuleId(moduleInfo) {
  return moduleInfo ? `${moduleInfo.frameworkName}.${moduleInfo.level}.${moduleInfo.moduleId}` : "";
}

function pushItemSection(parts, title, items) {
  if (!items || items.length === 0) {
    return;
  }
  parts.push("", title);
  for (const item of items) {
    parts.push(`- ${item.text}`);
  }
}

function pushRuleSummary(parts, rule) {
  const title = rule.title ? ` ${rule.title}` : "";
  parts.push(`- \`${rule.token}\`${title}`);
  if (rule.participatingBases) {
    parts.push(`  参与基：${rule.participatingBases}`);
  }
  if (rule.combination) {
    parts.push(`  组合方式：${rule.combination}`);
  }
  if (rule.output) {
    parts.push(`  输出能力：${rule.output}`);
  }
  if (rule.boundary) {
    parts.push(`  参数绑定：${rule.boundary}`);
  }
}

function buildModuleHoverMarkdown(moduleInfo, index) {
  const label = buildModuleLabel(moduleInfo);
  const parts = [`**${label}**`];

  if (index.headerText) {
    parts.push(index.headerText);
  }

  pushItemSection(parts, "能力声明", index.capabilities);
  pushItemSection(parts, "最小可行基", index.bases);

  if (index.rules.length > 0) {
    parts.push("", "基组合原则");
    for (const rule of index.rules) {
      pushRuleSummary(parts, rule);
    }
  }

  return parts.join("\n");
}

function getItemForToken(index, token) {
  const direct = index.itemByToken.get(token);
  if (direct) {
    return direct;
  }
  if (/^R\d+\.\d+$/.test(token)) {
    return index.itemByToken.get(token.split(".", 1)[0]) || null;
  }
  return null;
}

function buildRuleHoverMarkdown(moduleInfo, rule) {
  const parts = [`**${buildModuleLabel(moduleInfo)} · \`${rule.token}\`**`];

  if (rule.title) {
    parts.push(rule.title);
  }
  if (rule.participatingBases) {
    parts.push("", `参与基：${rule.participatingBases}`);
  }
  if (rule.combination) {
    parts.push(`组合方式：${rule.combination}`);
  }
  if (rule.output) {
    parts.push(`输出能力：${rule.output}`);
  }
  if (rule.boundary) {
    parts.push(`参数绑定：${rule.boundary}`);
  }

  return parts.join("\n");
}

function appendBoundaryConfigHover(parts, repoRoot, frameworkName, moduleId, token, allowCanonicalProjection) {
  if (!allowCanonicalProjection) {
    return;
  }
  const boundaryTarget = resolveBoundaryConfigTarget(repoRoot, frameworkName, moduleId, token);
  if (!boundaryTarget) {
    return;
  }
  const relFile = normalizePathSlashes(path.relative(repoRoot, boundaryTarget.filePath));
  parts.push("", "Project Config");
  parts.push(`- 文件：\`${relFile}\``);
  parts.push(`- 主归属 section：\`[${boundaryTarget.primarySection}]\``);
  if (boundaryTarget.targetSection && boundaryTarget.targetSection !== boundaryTarget.primarySection) {
    parts.push(`- 当前跳转 section：\`[${boundaryTarget.targetSection}]\``);
  }
  if (boundaryTarget.relatedSections.length > 1) {
    parts.push(
      `- 相关 section：${boundaryTarget.relatedSections.map((section) => `\`[${section}]\``).join("、")}`
    );
  }
  if (boundaryTarget.mappingMode === "derived" && boundaryTarget.note) {
    parts.push(`- 归属说明：${boundaryTarget.note}`);
  }
}

function buildSymbolHoverMarkdown(moduleInfo, index, token, repoRoot, allowCanonicalProjection = true) {
  const item = getItemForToken(index, token);
  if (!item) {
    return null;
  }

  if (item.kind === "rule") {
    return buildRuleHoverMarkdown(moduleInfo, item);
  }

  if (item.kind === "ruleChild") {
    const parentRule = getItemForToken(index, item.parentToken);
    const parts = [`**${buildModuleLabel(moduleInfo)} · \`${item.token}\`**`, item.text];
    if (parentRule && parentRule.kind === "rule") {
      parts.push("", `所属规则：\`${parentRule.token}\` ${parentRule.title}`);
    }
    return parts.join("\n");
  }

  if (item.kind === "derivedSymbol") {
    const parts = [`**${buildModuleLabel(moduleInfo)} · \`${item.token}\`**`, item.text];
    if (item.parentToken) {
      parts.push("", `来源规则：\`${item.parentToken}\``);
    }
    return parts.join("\n");
  }

  const parts = [`**${buildModuleLabel(moduleInfo)} · \`${item.token}\`**`, item.text];
  if (item.kind === "boundary" && repoRoot && moduleInfo?.frameworkName) {
    appendBoundaryConfigHover(
      parts,
      repoRoot,
      moduleInfo.frameworkName,
      canonicalModuleId(moduleInfo),
      item.token,
      allowCanonicalProjection
    );
  }
  return parts.join("\n");
}

function resolveDefinitionTarget({ repoRoot, filePath, text, line, character, allowCanonicalProjection = true }) {
  const documentInfo = getFrameworkDocumentInfo(filePath, repoRoot);
  if (!documentInfo) {
    return null;
  }

  const lines = text.split(/\r?\n/);
  const lineText = lines[line] || "";
  const tokenContext = findTokenContext(lineText, character);
  if (!tokenContext) {
    return null;
  }

  if (tokenContext.kind === "moduleRef" || tokenContext.kind === "moduleRule") {
    const targetFilePath = resolveModuleFile(
      repoRoot,
      documentInfo.frameworkName,
      tokenContext.frameworkName,
      tokenContext.level,
      tokenContext.moduleId,
      documentInfo.treeRoot
    );
    if (!targetFilePath || !fs.existsSync(targetFilePath)) {
      return null;
    }
    const targetText = fs.readFileSync(targetFilePath, "utf8");
    const targetIndex = buildDefinitionIndex(targetText);
    if (tokenContext.kind === "moduleRef") {
      const moduleTarget = resolveModuleTarget(targetIndex);
      if (!moduleTarget) {
        return null;
      }
      return {
        filePath: targetFilePath,
        line: moduleTarget.line,
        character: moduleTarget.character,
        length: moduleTarget.length,
      };
    }
    const resolvedSymbol = resolveLocalSymbol(targetIndex, tokenContext.token);
    if (!resolvedSymbol) {
      return null;
    }
    return {
      filePath: targetFilePath,
      line: resolvedSymbol.line,
      character: resolvedSymbol.character,
      length: resolvedSymbol.length,
    };
  }

  const index = buildDefinitionIndex(text);
  const resolvedLocal = resolveLocalSymbol(index, tokenContext.token);
  if (!resolvedLocal) {
    return null;
  }
  const localItem = getItemForToken(index, tokenContext.token);
  if (
    allowCanonicalProjection &&
    localItem &&
    localItem.kind === "boundary" &&
    localItem.line !== line &&
    documentInfo.frameworkName
  ) {
    const boundaryTarget = resolveBoundaryConfigTarget(
      repoRoot,
      documentInfo.frameworkName,
      canonicalModuleId(documentInfo),
      tokenContext.token
    );
    if (boundaryTarget) {
      return boundaryTarget;
    }
  }
  return {
    filePath,
    line: resolvedLocal.line,
    character: resolvedLocal.character,
    length: resolvedLocal.length,
  };
}

function resolveHoverTarget({ repoRoot, filePath, text, line, character, allowCanonicalProjection = true }) {
  const documentInfo = getFrameworkDocumentInfo(filePath, repoRoot);
  if (!documentInfo) {
    return null;
  }
  const lines = text.split(/\r?\n/);
  const lineText = lines[line] || "";
  const tokenContext = findTokenContext(lineText, character);
  if (!tokenContext) {
    return null;
  }

  if (tokenContext.kind === "moduleRef" || tokenContext.kind === "moduleRule") {
    const targetFilePath = resolveModuleFile(
      repoRoot,
      documentInfo.frameworkName,
      tokenContext.frameworkName,
      tokenContext.level,
      tokenContext.moduleId,
      documentInfo.treeRoot
    );
    if (!targetFilePath || !fs.existsSync(targetFilePath)) {
      return null;
    }

    const targetText = fs.readFileSync(targetFilePath, "utf8");
    const targetIndex = buildDefinitionIndex(targetText);
    const targetInfo = getFrameworkDocumentInfo(targetFilePath, repoRoot);
    const markdown = tokenContext.kind === "moduleRef"
      ? buildModuleHoverMarkdown(targetInfo, targetIndex)
      : buildSymbolHoverMarkdown(targetInfo, targetIndex, tokenContext.token, repoRoot, allowCanonicalProjection);
    if (!markdown) {
      return null;
    }

    return {
      start: tokenContext.start,
      end: tokenContext.end,
      markdown,
    };
  }

  const currentIndex = buildDefinitionIndex(text);
  const markdown = buildSymbolHoverMarkdown(
    documentInfo,
    currentIndex,
    tokenContext.token,
    repoRoot,
    allowCanonicalProjection
  );
  if (!markdown) {
    return null;
  }

  return {
    start: tokenContext.start,
    end: tokenContext.end,
    markdown,
  };
}

function dedupeTargets(targets) {
  const seen = new Set();
  const deduped = [];
  for (const target of targets) {
    if (!target || !target.filePath) {
      continue;
    }
    const key = `${target.filePath}:${target.line}:${target.character}:${target.length || 0}`;
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    deduped.push(target);
  }
  return deduped;
}

function resolveReferenceTargets({ repoRoot, filePath, text, line, character, allowCanonicalProjection = true }) {
  const documentInfo = getFrameworkDocumentInfo(filePath, repoRoot);
  if (!documentInfo) {
    return [];
  }
  const lines = text.split(/\r?\n/);
  const lineText = lines[line] || "";
  const tokenContext = findTokenContext(lineText, character);
  if (!tokenContext) {
    return [];
  }

  const targets = [
    {
      filePath,
      line,
      character: tokenContext.start,
      length: Math.max(1, tokenContext.end - tokenContext.start),
    },
  ];

  if (tokenContext.kind === "moduleRef" || tokenContext.kind === "moduleRule") {
    const definitionTarget = resolveDefinitionTarget({ repoRoot, filePath, text, line, character });
    if (definitionTarget) {
      targets.push(definitionTarget);
    }
    return dedupeTargets(targets);
  }

  const index = buildDefinitionIndex(text);
  const resolvedLocal = resolveLocalSymbol(index, tokenContext.token);
  if (resolvedLocal) {
    targets.push({
      filePath,
      line: resolvedLocal.line,
      character: resolvedLocal.character,
      length: resolvedLocal.length,
    });
  }

  const localItem = getItemForToken(index, tokenContext.token);
  if (
    allowCanonicalProjection &&
    localItem &&
    localItem.kind === "boundary" &&
    documentInfo.frameworkName
  ) {
    const boundaryTarget = resolveBoundaryConfigTarget(
      repoRoot,
      documentInfo.frameworkName,
      canonicalModuleId(documentInfo),
      tokenContext.token
    );
    if (boundaryTarget) {
      targets.push(boundaryTarget);
    }
  }

  return dedupeTargets(targets);
}

module.exports = {
  buildDefinitionIndex,
  findTokenContext,
  getFrameworkDocumentInfo,
  isFrameworkMarkdownFile,
  resolveDefinitionTarget,
  resolveReferenceTargets,
  resolveHoverTarget,
};
