const fs = require("fs");
const path = require("path");

const FRAMEWORK_FILE_PATH_PATTERN = /^framework\/([^/]+)\/L(\d+)-M(\d+)-[^/]+\.md$/;
const MODULE_REF_WITH_RULES_PATTERN =
  /(?:(?<framework>[A-Za-z][A-Za-z0-9_-]*)\.)?L(?<level>\d+)\.M(?<module>\d+)\[(?<rules>[^\]]+)\]/g;
const MODULE_REF_PATTERN = /(?:(?<framework>[A-Za-z][A-Za-z0-9_-]*)\.)?L(?<level>\d+)\.M(?<module>\d+)/g;
const RULE_TOKEN_PATTERN = /R\d+(?:\.\d+)?/g;
const CORE_TOKEN_PATTERN = /R\d+\.\d+|R\d+|B\d+|C\d+|V\d+/g;
const UPPER_SYMBOL_PATTERN = /[A-Z][A-Z0-9_]+/g;
const BACKTICK_SEGMENT_PATTERN = /`([^`]+)`/g;
const SYMBOL_TOKEN_PATTERN = /[A-Za-z][A-Za-z0-9_]*/g;
const TOML_SECTION_PATTERN = /^\s*\[([A-Za-z0-9_.-]+)\]\s*$/;
const DEFAULT_INSTANCE_FILE = path.join("projects", "knowledge_base_basic", "instance.toml");

const SECTION_PREFIXES = [
  ["## 1. 能力声明", "capability"],
  ["## 2. 边界定义", "boundary"],
  ["## 3. 最小可行基", "base"],
  ["## 4. 基组合原则", "rule"],
  ["## 5. 验证", "verification"],
];

const FRAMEWORK_BOUNDARY_SECTION_MAP = {
  frontend: {
    SURFACE: {
      primarySection: "surface",
      relatedSections: ["surface", "surface.copy"],
    },
    VISUAL: {
      primarySection: "visual",
      relatedSections: ["visual"],
    },
    ROUTE: {
      primarySection: "route",
      relatedSections: ["route"],
    },
    A11Y: {
      primarySection: "a11y",
      relatedSections: ["a11y"],
    },
  },
  knowledge_base: {
    SURFACE: {
      primarySection: "surface",
      relatedSections: ["surface", "surface.copy"],
    },
    LIBRARY: {
      primarySection: "library",
      relatedSections: ["library", "library.copy"],
    },
    PREVIEW: {
      primarySection: "preview",
      relatedSections: ["preview"],
    },
    CHAT: {
      primarySection: "chat",
      relatedSections: ["chat", "chat.copy"],
    },
    CONTEXT: {
      primarySection: "context",
      relatedSections: ["context"],
    },
    RETURN: {
      primarySection: "return",
      relatedSections: ["return"],
    },
  },
};

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
    frameworkName: match[1],
    level: `L${match[2]}`,
    moduleId: `M${match[3]}`,
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

function resolveModuleFile(repoRoot, currentFrameworkName, refFrameworkName, level, moduleId) {
  const frameworkName = refFrameworkName || currentFrameworkName;
  if (!frameworkName || !level || !moduleId) {
    return null;
  }

  const moduleDir = path.join(repoRoot, "framework", frameworkName);
  if (!fs.existsSync(moduleDir) || !fs.statSync(moduleDir).isDirectory()) {
    return null;
  }

  const prefix = `${level}-${moduleId}-`;
  for (const entry of fs.readdirSync(moduleDir)) {
    if (!entry.endsWith(".md")) {
      continue;
    }
    if (entry.startsWith(prefix)) {
      return path.join(moduleDir, entry);
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

function getBoundaryConfigMapping(frameworkName, token) {
  const mapping = FRAMEWORK_BOUNDARY_SECTION_MAP[frameworkName];
  if (!mapping) {
    return null;
  }
  return mapping[token] || null;
}

function discoverInstanceFiles(repoRoot) {
  const projectsDir = path.join(repoRoot, "projects");
  if (!fs.existsSync(projectsDir) || !fs.statSync(projectsDir).isDirectory()) {
    return [];
  }
  const files = [];
  for (const entry of fs.readdirSync(projectsDir)) {
    const instanceFile = path.join(projectsDir, entry, "instance.toml");
    if (fs.existsSync(instanceFile) && fs.statSync(instanceFile).isFile()) {
      files.push(instanceFile);
    }
  }
  return files.sort();
}

function inferConfiguredFrameworks(instanceText) {
  const frameworks = new Set();
  for (const match of instanceText.matchAll(/^\s*(frontend|domain|backend)\s*=\s*"framework\/([^/]+)\//gm)) {
    frameworks.add(match[2]);
  }
  return frameworks;
}

function resolvePreferredInstanceFile(repoRoot, frameworkName) {
  const preferredDefault = path.join(repoRoot, DEFAULT_INSTANCE_FILE);
  if (fs.existsSync(preferredDefault) && fs.statSync(preferredDefault).isFile()) {
    return preferredDefault;
  }

  const candidates = discoverInstanceFiles(repoRoot);
  let bestFile = null;
  let bestScore = -1;
  for (const filePath of candidates) {
    let score = 0;
    try {
      const frameworks = inferConfiguredFrameworks(fs.readFileSync(filePath, "utf8"));
      if (frameworks.has(frameworkName)) {
        score += 10;
      }
    } catch {
      // Ignore broken instance files here; main parser/validator handles them elsewhere.
    }
    if (score > bestScore) {
      bestScore = score;
      bestFile = filePath;
    }
  }
  return bestFile;
}

function resolveBoundaryConfigTarget(repoRoot, frameworkName, token) {
  const mapping = getBoundaryConfigMapping(frameworkName, token);
  if (!mapping) {
    return null;
  }
  const instanceFilePath = resolvePreferredInstanceFile(repoRoot, frameworkName);
  if (!instanceFilePath || !fs.existsSync(instanceFilePath)) {
    return null;
  }
  const instanceText = fs.readFileSync(instanceFilePath, "utf8");
  const sectionIndex = buildTomlSectionIndex(instanceText);
  const sectionTarget = sectionIndex.get(mapping.primarySection);
  if (!sectionTarget) {
    return null;
  }
  return {
    filePath: instanceFilePath,
    line: sectionTarget.line,
    character: sectionTarget.character,
    length: sectionTarget.length,
    relatedSections: mapping.relatedSections,
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
    parts.push(`  边界绑定：${rule.boundary}`);
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
    parts.push(`边界绑定：${rule.boundary}`);
  }

  return parts.join("\n");
}

function appendBoundaryConfigHover(parts, repoRoot, frameworkName, token) {
  const boundaryTarget = resolveBoundaryConfigTarget(repoRoot, frameworkName, token);
  if (!boundaryTarget) {
    return;
  }
  const relFile = normalizePathSlashes(path.relative(repoRoot, boundaryTarget.filePath));
  parts.push("", "实例配置");
  parts.push(`- 文件：\`${relFile}\``);
  parts.push(`- 主 section：\`[${boundaryTarget.relatedSections[0]}]\``);
  if (boundaryTarget.relatedSections.length > 1) {
    parts.push(
      `- 相关 section：${boundaryTarget.relatedSections.map((section) => `\`[${section}]\``).join("、")}`
    );
  }
}

function buildSymbolHoverMarkdown(moduleInfo, index, token, repoRoot) {
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
    appendBoundaryConfigHover(parts, repoRoot, moduleInfo.frameworkName, item.token);
  }
  return parts.join("\n");
}

function resolveDefinitionTarget({ repoRoot, filePath, text, line, character }) {
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
      tokenContext.moduleId
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
    localItem &&
    localItem.kind === "boundary" &&
    localItem.line !== line &&
    documentInfo.frameworkName
  ) {
    const boundaryTarget = resolveBoundaryConfigTarget(
      repoRoot,
      documentInfo.frameworkName,
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

function resolveHoverTarget({ repoRoot, filePath, text, line, character }) {
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
      tokenContext.moduleId
    );
    if (!targetFilePath || !fs.existsSync(targetFilePath)) {
      return null;
    }

    const targetText = fs.readFileSync(targetFilePath, "utf8");
    const targetIndex = buildDefinitionIndex(targetText);
    const targetInfo = getFrameworkDocumentInfo(targetFilePath, repoRoot);
    const markdown = tokenContext.kind === "moduleRef"
      ? buildModuleHoverMarkdown(targetInfo, targetIndex)
      : buildSymbolHoverMarkdown(targetInfo, targetIndex, tokenContext.token, repoRoot);
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
  const markdown = buildSymbolHoverMarkdown(documentInfo, currentIndex, tokenContext.token, repoRoot);
  if (!markdown) {
    return null;
  }

  return {
    start: tokenContext.start,
    end: tokenContext.end,
    markdown,
  };
}

module.exports = {
  buildDefinitionIndex,
  findTokenContext,
  getFrameworkDocumentInfo,
  isFrameworkMarkdownFile,
  resolveDefinitionTarget,
  resolveHoverTarget,
};
