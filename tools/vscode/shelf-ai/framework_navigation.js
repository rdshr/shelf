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
const DEFAULT_PRODUCT_SPEC_FILE = path.join("projects", "knowledge_base_basic", "product_spec.toml");
const GOVERNANCE_MANIFEST_RELATIVE_PATH = path.join("generated", "governance_manifest.json");

const SECTION_PREFIXES = [
  ["## 1. 能力声明", "capability"],
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

function createBoundaryConfigMapping(primarySection, relatedSections = [primarySection], options = {}) {
  return {
    primarySection,
    relatedSections: uniqueSections([primarySection, ...relatedSections]),
    mappingMode: options.mappingMode || "direct",
    note: options.note || "",
  };
}

function directConfigMapping(primarySection, relatedSections = [primarySection]) {
  return createBoundaryConfigMapping(primarySection, relatedSections, { mappingMode: "direct" });
}

function derivedConfigMapping(primarySection, relatedSections = [primarySection], note = "") {
  return createBoundaryConfigMapping(primarySection, relatedSections, {
    mappingMode: "derived",
    note,
  });
}

const FRAMEWORK_BOUNDARY_SECTION_MAP = {
  frontend: {
    SURFACE: directConfigMapping("surface", ["surface.copy"]),
    VISUAL: directConfigMapping("visual"),
    ROUTE: directConfigMapping("route"),
    A11Y: directConfigMapping("a11y"),
  },
  knowledge_base: {
    SURFACE: directConfigMapping("surface", ["surface.copy"]),
    LIBRARY: directConfigMapping("library", ["library.copy"]),
    PREVIEW: directConfigMapping("preview"),
    CHAT: directConfigMapping("chat", ["chat.copy"]),
    CONTEXT: directConfigMapping("context"),
    RETURN: directConfigMapping("return"),
    A11Y: derivedConfigMapping("a11y", ["a11y"], "该边界由工作台实例的可访问配置承接。"),
    FILESET: derivedConfigMapping("library", ["library", "library.copy"], "该边界由知识库实例 section 承接。"),
    INGEST: derivedConfigMapping("library", ["library", "library.copy"], "该边界由知识库实例 section 承接。"),
    CLASSIFY: derivedConfigMapping("library", ["library"], "该边界由知识库实例 section 承接。"),
    LIMIT: derivedConfigMapping("library", ["library"], "该边界由知识库实例 section 承接。"),
    VISIBILITY: derivedConfigMapping(
      "library",
      ["library", "preview"],
      "该边界由知识库入口与来源预览配置共同承接。"
    ),
    ENTRY: derivedConfigMapping(
      "library",
      ["library", "route"],
      "该边界由知识库入口配置与工作台路由共同承接。"
    ),
    DOCVIEW: derivedConfigMapping("preview", ["preview"], "该边界由来源预览配置承接。"),
    TOC: derivedConfigMapping("preview", ["preview"], "该边界由来源预览配置承接。"),
    META: derivedConfigMapping("preview", ["preview"], "该边界由来源预览配置承接。"),
    FOCUS: derivedConfigMapping(
      "preview",
      ["preview", "a11y"],
      "该边界由来源预览与可访问配置共同承接。"
    ),
    ANCHOR: derivedConfigMapping(
      "preview",
      ["preview", "return"],
      "该边界由来源锚点与返回路径配置共同承接。"
    ),
    TURN: derivedConfigMapping("chat", ["chat", "chat.copy"], "该边界由对话产品规格承接。"),
    INPUT: derivedConfigMapping("chat", ["chat", "chat.copy"], "该边界由对话产品规格承接。"),
    STATUS: derivedConfigMapping(
      "chat",
      ["chat", "chat.copy", "preview"],
      "该边界由对话输出与来源状态配置共同承接。"
    ),
    CITATION: derivedConfigMapping(
      "chat",
      ["chat", "chat.copy", "context", "return", "preview"],
      "该边界由对话、上下文、返回与来源预览配置共同承接。"
    ),
    SCOPE: derivedConfigMapping(
      "context",
      ["context", "preview"],
      "该边界由上下文选择与来源预览配置共同承接。"
    ),
    TURNLINK: derivedConfigMapping(
      "return",
      ["return", "chat", "context"],
      "该边界由回合返回链路与上下文配置共同承接。"
    ),
    TRACE: derivedConfigMapping(
      "context",
      ["context", "preview", "return"],
      "该边界由上下文、来源追踪与返回链路配置共同承接。"
    ),
    EMPTY: derivedConfigMapping(
      "chat",
      ["chat", "chat.copy", "preview", "library"],
      "该边界由聊天、预览与知识库空态配置共同承接。"
    ),
    REGION: derivedConfigMapping(
      "surface",
      ["surface", "surface.copy"],
      "该边界由工作台界面承载配置承接。"
    ),
    RESPONSIVE: derivedConfigMapping(
      "surface",
      ["surface", "visual"],
      "该边界由界面承载与视觉配置共同承接。"
    ),
  },
  backend: {
    LIBRARY: derivedConfigMapping("library", ["library", "library.copy"], "该边界由知识库实例 section 承接。"),
    LIBAPI: derivedConfigMapping("library", ["library", "library.copy"], "该边界由知识库实例 section 承接。"),
    FILE: derivedConfigMapping("library", ["library", "library.copy"], "该边界由知识库实例 section 承接。"),
    PREVIEW: derivedConfigMapping("preview", ["preview"], "该边界由来源预览配置承接。"),
    PREVIEWAPI: derivedConfigMapping("preview", ["preview"], "该边界由来源预览配置承接。"),
    CHAT: derivedConfigMapping("chat", ["chat", "chat.copy"], "该边界由对话产品规格承接。"),
    CHATAPI: derivedConfigMapping("chat", ["chat", "chat.copy"], "该边界由对话产品规格承接。"),
    CITATION: derivedConfigMapping(
      "chat",
      ["chat", "chat.copy", "context", "return", "preview"],
      "该边界由对话、返回与来源预览配置共同承接。"
    ),
    TRACE: derivedConfigMapping(
      "context",
      ["context", "return"],
      "该边界由上下文与返回链路配置共同承接。"
    ),
    RESULT: derivedConfigMapping(
      "return",
      ["return", "chat", "library", "preview"],
      "该边界由返回链路与统一结果结构配置共同承接。"
    ),
    AUTH: derivedConfigMapping(
      "return",
      ["return", "chat"],
      "该边界由接口返回治理与对话入口配置共同承接。"
    ),
    ERROR: derivedConfigMapping(
      "return",
      ["return", "chat", "preview"],
      "该边界由错误返回链路与界面反馈配置共同承接。"
    ),
    VALID: derivedConfigMapping(
      "return",
      ["return", "chat"],
      "该边界由返回链路与交互约束配置共同承接。"
    ),
    CONSIST: derivedConfigMapping(
      "return",
      ["return", "chat", "library", "preview"],
      "该边界由统一返回与多接口一致性配置共同承接。"
    ),
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
  if (mapping && mapping[token]) {
    return mapping[token];
  }
  return inferBoundaryConfigMapping(frameworkName, token);
}

function inferFrontendBoundaryConfigMapping(token) {
  const upper = String(token || "").toUpperCase();
  if (!upper) {
    return null;
  }

  if (
    upper === "A11Y" ||
    upper.endsWith("A11Y") ||
    new Set(["READ", "ORDER", "FOCUS"]).has(upper)
  ) {
    return derivedConfigMapping("a11y", ["a11y"], "该边界按可访问与阅读路径归属到实例可访问配置。");
  }

  if (new Set(["ROUTE", "NAV", "ENTRY", "RETURN", "PAGESET", "SCENE", "STEP", "REF"]).has(upper)) {
    return derivedConfigMapping("route", ["route"], "该边界按导航与返回路径归属到实例路由配置。");
  }

  if (
    new Set([
      "VISUAL",
      "TOKEN",
      "THEME",
      "DENSITY",
      "ALERT",
      "TAG",
      "BUBBLE",
      "TEXTTONE",
      "TEXTTYPO",
      "BTNCHROME",
      "PANELTONE",
      "FEEDBACK",
    ]).has(upper) ||
    upper.includes("TONE") ||
    upper.includes("TYPO") ||
    upper.includes("CHROME")
  ) {
    return derivedConfigMapping("visual", ["visual"], "该边界按视觉与主题语义归属到实例视觉配置。");
  }

  return derivedConfigMapping(
    "surface",
    ["surface", "surface.copy"],
    "该边界按界面承载与组件装配归属到实例界面配置。"
  );
}

function inferKnowledgeBaseBoundaryConfigMapping(token) {
  const upper = String(token || "").toUpperCase();
  if (!upper) {
    return null;
  }

  if (upper === "A11Y" || upper.endsWith("A11Y")) {
    return derivedConfigMapping("a11y", ["a11y"], "该边界由工作台实例的可访问配置承接。");
  }
  if (new Set(["RETURN", "TURNLINK"]).has(upper)) {
    return derivedConfigMapping(
      "return",
      ["return", "chat", "context"],
      "该边界由回合返回链路与上下文配置共同承接。"
    );
  }
  if (new Set(["CHAT", "TURN", "INPUT", "STATUS"]).has(upper)) {
    return derivedConfigMapping("chat", ["chat", "chat.copy"], "该边界由对话产品规格承接。");
  }
  if (upper === "CITATION") {
    return derivedConfigMapping(
      "chat",
      ["chat", "chat.copy", "context", "return", "preview"],
      "该边界由对话、上下文、返回与来源预览配置共同承接。"
    );
  }
  if (new Set(["CONTEXT", "SCOPE", "TRACE"]).has(upper)) {
    return derivedConfigMapping(
      "context",
      ["context", "preview", "return"],
      "该边界由上下文、来源追踪与返回链路配置共同承接。"
    );
  }
  if (new Set(["PREVIEW", "DOCVIEW", "TOC", "ANCHOR", "META", "FOCUS", "EMPTY"]).has(upper)) {
    return derivedConfigMapping(
      "preview",
      ["preview", "return"],
      "该边界由来源预览与锚点返回配置共同承接。"
    );
  }
  if (new Set(["LIBRARY", "ENTRY", "FILESET", "INGEST", "LIMIT", "CLASSIFY", "VISIBILITY"]).has(upper)) {
    return derivedConfigMapping(
      "library",
      ["library", "library.copy", "preview"],
      "该边界由知识库入口与来源预览配置共同承接。"
    );
  }
  if (new Set(["SURFACE", "REGION", "RESPONSIVE"]).has(upper)) {
    return derivedConfigMapping(
      "surface",
      ["surface", "surface.copy", "visual"],
      "该边界由工作台界面承载与视觉配置共同承接。"
    );
  }

  return null;
}

function inferBackendBoundaryConfigMapping(token) {
  const upper = String(token || "").toUpperCase();
  if (!upper) {
    return null;
  }

  if (upper.startsWith("LIB") || upper === "FILE" || upper === "LIBRARY") {
    return derivedConfigMapping("library", ["library", "library.copy"], "该边界由知识库实例 section 承接。");
  }
  if (upper.startsWith("PREVIEW") || upper === "PREVIEW") {
    return derivedConfigMapping("preview", ["preview"], "该边界由来源预览配置承接。");
  }
  if (upper.startsWith("CHAT") || upper === "CITATION") {
    return derivedConfigMapping(
      "chat",
      ["chat", "chat.copy", "context", "return", "preview"],
      "该边界由对话、返回与来源预览配置共同承接。"
    );
  }
  if (upper === "TRACE") {
    return derivedConfigMapping(
      "context",
      ["context", "return"],
      "该边界由上下文与返回链路配置共同承接。"
    );
  }
  if (new Set(["RESULT", "AUTH", "ERROR", "VALID", "CONSIST"]).has(upper)) {
    return derivedConfigMapping(
      "return",
      ["return", "chat", "library", "preview"],
      "该边界由统一返回结构与跨接口约束配置共同承接。"
    );
  }

  return null;
}

function inferBoundaryConfigMapping(frameworkName, token) {
  if (frameworkName === "frontend") {
    return inferFrontendBoundaryConfigMapping(token);
  }
  if (frameworkName === "knowledge_base") {
    return inferKnowledgeBaseBoundaryConfigMapping(token);
  }
  if (frameworkName === "backend") {
    return inferBackendBoundaryConfigMapping(token);
  }
  return null;
}

function discoverGovernanceManifestFiles(repoRoot) {
  const projectsDir = path.join(repoRoot, "projects");
  if (!fs.existsSync(projectsDir) || !fs.statSync(projectsDir).isDirectory()) {
    return [];
  }
  const files = [];
  for (const entry of fs.readdirSync(projectsDir)) {
    const manifestPath = path.join(projectsDir, entry, GOVERNANCE_MANIFEST_RELATIVE_PATH);
    if (fs.existsSync(manifestPath) && fs.statSync(manifestPath).isFile()) {
      files.push(manifestPath);
    }
  }
  return files.sort();
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
    const sectionMatch = TOML_SECTION_PATTERN.exec(lineText);
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

function resolvePreferredProductSpecFile(repoRoot, frameworkName) {
  const candidates = discoverProductSpecFiles(repoRoot);
  const preferredDefault = path.join(repoRoot, DEFAULT_PRODUCT_SPEC_FILE);
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

function collectDerivedFromEntries(node, results = []) {
  if (Array.isArray(node)) {
    for (const value of node) {
      collectDerivedFromEntries(value, results);
    }
    return results;
  }
  if (!node || typeof node !== "object") {
    return results;
  }
  if (node.derived_from && typeof node.derived_from === "object") {
    results.push(node.derived_from);
  }
  for (const value of Object.values(node)) {
    collectDerivedFromEntries(value, results);
  }
  return results;
}

function resolveGovernanceBoundaryTargets(repoRoot, frameworkName, token) {
  const manifests = discoverGovernanceManifestFiles(repoRoot);
  if (!manifests.length) {
    return [];
  }

  const preferredProductSpec = resolvePreferredProductSpecFile(repoRoot, frameworkName);
  const candidates = [];
  const seen = new Set();

  for (const manifestPath of manifests) {
    let manifest = null;
    try {
      manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
    } catch {
      continue;
    }
    if (!manifest || typeof manifest !== "object") {
      continue;
    }

    const relProductSpec = normalizePathSlashes(String(manifest.product_spec_file || ""));
    if (!relProductSpec) {
      continue;
    }
    const productSpecFilePath = path.resolve(repoRoot, relProductSpec);
    if (!fs.existsSync(productSpecFilePath)) {
      continue;
    }

    const productSpecText = fs.readFileSync(productSpecFilePath, "utf8");
    const sectionIndex = buildTomlSectionIndex(productSpecText);
    for (const derivedFrom of collectDerivedFromEntries(manifest)) {
      const frameworkModules = derivedFrom && typeof derivedFrom.framework_modules === "object"
        ? derivedFrom.framework_modules
        : null;
      const boundarySections = derivedFrom && typeof derivedFrom.boundary_sections === "object"
        ? derivedFrom.boundary_sections
        : null;
      if (!frameworkModules || !boundarySections) {
        continue;
      }
      const mappedSection = boundarySections[token];
      if (typeof mappedSection !== "string" || !mappedSection.trim()) {
        continue;
      }
      const sectionTarget = sectionIndex.get(mappedSection);
      if (!sectionTarget) {
        continue;
      }

      const frameworkNames = new Set();
      for (const moduleId of Object.values(frameworkModules)) {
        if (typeof moduleId !== "string" || !moduleId.includes(".")) {
          continue;
        }
        frameworkNames.add(moduleId.split(".", 1)[0]);
      }
      if (!frameworkNames.has(frameworkName)) {
        continue;
      }

      const dedupeKey = `${productSpecFilePath}:${mappedSection}:${frameworkName}:${token}`;
      if (seen.has(dedupeKey)) {
        continue;
      }
      seen.add(dedupeKey);
      candidates.push({
        filePath: productSpecFilePath,
        line: sectionTarget.line,
        character: sectionTarget.character,
        length: sectionTarget.length,
        primarySection: mappedSection,
        targetSection: mappedSection,
        relatedSections: [mappedSection],
        mappingMode: "governance",
        note: "该映射来自已物化项目的治理清单。",
        preferred: preferredProductSpec === productSpecFilePath,
      });
    }
  }

  return candidates.sort((left, right) => {
    if (left.preferred !== right.preferred) {
      return left.preferred ? -1 : 1;
    }
    return left.filePath.localeCompare(right.filePath);
  });
}

function resolveBoundaryConfigTarget(repoRoot, frameworkName, token) {
  const governanceTargets = resolveGovernanceBoundaryTargets(repoRoot, frameworkName, token);
  if (governanceTargets.length) {
    return governanceTargets[0];
  }
  const mapping = getBoundaryConfigMapping(frameworkName, token);
  if (!mapping) {
    return null;
  }
  const productSpecFilePath = resolvePreferredProductSpecFile(repoRoot, frameworkName);
  if (!productSpecFilePath || !fs.existsSync(productSpecFilePath)) {
    return null;
  }
  const productSpecText = fs.readFileSync(productSpecFilePath, "utf8");
  const sectionIndex = buildTomlSectionIndex(productSpecText);
  let targetSectionName = mapping.primarySection;
  let sectionTarget = sectionIndex.get(targetSectionName);
  if (!sectionTarget) {
    for (const relatedSection of mapping.relatedSections) {
      const candidate = sectionIndex.get(relatedSection);
      if (candidate) {
        targetSectionName = relatedSection;
        sectionTarget = candidate;
        break;
      }
    }
  }
  if (!sectionTarget) {
    return null;
  }
  return {
    filePath: productSpecFilePath,
    line: sectionTarget.line,
    character: sectionTarget.character,
    length: sectionTarget.length,
    primarySection: mapping.primarySection,
    targetSection: targetSectionName,
    relatedSections: mapping.relatedSections,
    mappingMode: mapping.mappingMode,
    note: mapping.note,
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
  parts.push("", "Product Spec");
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

function resolveReferenceTargets({ repoRoot, filePath, text, line, character }) {
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
  if (localItem && localItem.kind === "boundary" && documentInfo.frameworkName) {
    const boundaryTarget = resolveBoundaryConfigTarget(repoRoot, documentInfo.frameworkName, tokenContext.token);
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
