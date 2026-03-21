const fs = require("fs");
const path = require("path");

const MARKDOWN_SNIPPETS_FILE = path.join(__dirname, "snippets", "markdown.code-snippets");
const FRAMEWORK_TEMPLATE_SNIPPET_NAME = "@framework Module Template";
const FRAMEWORK_SECTION_HEADINGS = Object.freeze({
  capability: "## 1. 能力声明（Capability Statement）",
  parameter: "## 2. 边界定义（Boundary / Parameter 参数）",
  base: "## 3. 最小结构基（Minimal Structural Bases）",
  rule: "## 4. 基组合原则（Base Combination Principles）",
  verification: "## 5. 验证（Verification）",
});

function splitLines(text) {
  return String(text || "").split(/\r?\n/);
}

function loadMarkdownSnippets() {
  return JSON.parse(fs.readFileSync(MARKDOWN_SNIPPETS_FILE, "utf8"));
}

function getFrameworkTemplateSnippetBody() {
  const snippets = loadMarkdownSnippets();
  const snippet = snippets[FRAMEWORK_TEMPLATE_SNIPPET_NAME];
  if (!snippet || !Array.isArray(snippet.body) || snippet.body.length === 0) {
    throw new Error(`missing snippet body for ${FRAMEWORK_TEMPLATE_SNIPPET_NAME}`);
  }
  return snippet.body.slice();
}

function getFrameworkTemplateSnippetText() {
  return getFrameworkTemplateSnippetBody().join("\n");
}

function detectSectionIdFromHeading(trimmedHeading) {
  const heading = String(trimmedHeading || "").trim();
  if (heading === FRAMEWORK_SECTION_HEADINGS.capability) {
    return "capability";
  }
  if (heading === FRAMEWORK_SECTION_HEADINGS.parameter) {
    return "parameter";
  }
  if (heading === FRAMEWORK_SECTION_HEADINGS.base) {
    return "base";
  }
  if (heading === FRAMEWORK_SECTION_HEADINGS.rule) {
    return "rule";
  }
  if (heading === FRAMEWORK_SECTION_HEADINGS.verification) {
    return "verification";
  }
  return "";
}

function detectFrameworkAuthoringState(documentText, lineNumber = 0) {
  const lines = splitLines(documentText);
  const safeLineNumber = Math.max(0, Math.min(Number(lineNumber || 0), Math.max(0, lines.length - 1)));
  let sectionId = "";
  let inNonResponsibility = false;

  for (let index = 0; index <= safeLineNumber; index += 1) {
    const trimmed = lines[index].trim();
    if (trimmed.startsWith("## ")) {
      sectionId = detectSectionIdFromHeading(trimmed);
      inNonResponsibility = false;
      continue;
    }
    if (trimmed.startsWith("### ")) {
      const lower = trimmed.toLowerCase();
      inNonResponsibility = sectionId === "capability" && lower.includes("非职责声明");
    }
  }

  return {
    sectionId,
    inNonResponsibility,
    lineCount: lines.length,
  };
}

function collectNextSymbolNumbers(documentText) {
  const text = String(documentText || "");
  const maxima = {
    C: 0,
    P: 0,
    B: 0,
    R: 0,
    V: 0,
    N: 0,
  };
  const symbolPattern = /`([CPBRVN])(\d+)(?:\.\d+)?`/g;
  for (const match of text.matchAll(symbolPattern)) {
    const symbol = String(match[1] || "");
    const number = Number(match[2] || 0);
    if (!Number.isInteger(number) || number <= 0 || !Object.prototype.hasOwnProperty.call(maxima, symbol)) {
      continue;
    }
    if (number > maxima[symbol]) {
      maxima[symbol] = number;
    }
  }
  return {
    C: maxima.C + 1,
    P: maxima.P + 1,
    B: maxima.B + 1,
    R: maxima.R + 1,
    V: maxima.V + 1,
    N: maxima.N + 1,
  };
}

function findNearestRuleNumber(documentText, lineNumber = 0) {
  const lines = splitLines(documentText);
  const safeLineNumber = Math.max(0, Math.min(Number(lineNumber || 0), Math.max(0, lines.length - 1)));
  for (let index = safeLineNumber; index >= 0; index -= 1) {
    const trimmed = lines[index].trim();
    if (index !== safeLineNumber && trimmed.startsWith("## ")) {
      break;
    }
    const ruleMatch = /^-\s+`R(\d+)`\s+/.exec(trimmed);
    if (ruleMatch) {
      return Number(ruleMatch[1]);
    }
  }
  return null;
}

function createCompletionDefinitions(dynamic = {}) {
  const next = {
    C: Number(dynamic.nextNumbers?.C || 1),
    P: Number(dynamic.nextNumbers?.P || 1),
    B: Number(dynamic.nextNumbers?.B || 1),
    R: Number(dynamic.nextNumbers?.R || 1),
    V: Number(dynamic.nextNumbers?.V || 1),
    N: Number(dynamic.nextNumbers?.N || 1),
  };
  const nearestRuleNumber = Number(dynamic.nearestRuleNumber || 0) || next.R;
  return [
    {
      id: "framework-title",
      label: "# 中文模块名:EnglishName",
      detail: "插入框架模块双语标题",
      documentation: "框架标题必须遵守 `中文名:EnglishName` 格式。",
      insertText: "# ${1:中文模块名}:${2:EnglishName}",
      contexts: ["hash", "framework-file-empty"],
    },
    {
      id: "framework-module-template",
      label: "@framework 标准模块模板",
      detail: "插入完整框架标准模板",
      documentation: "覆盖标题、@framework、能力声明、参数、最小结构基、组合原则与验证。",
      insertText: getFrameworkTemplateSnippetText(),
      contexts: ["at", "framework-file-empty"],
    },
    {
      id: "framework-directive",
      label: "@framework",
      detail: "插入 plain @framework 指令",
      documentation: "框架文件必须使用无参数的 plain `@framework` 指令。",
      insertText: "@framework",
      contexts: ["at", "framework-file-empty"],
    },
    {
      id: "section-capability",
      label: "## 1. 能力声明（Capability Statement）",
      detail: "插入能力声明主章节",
      documentation: "固定框架章节：能力声明。",
      insertText: "## 1. 能力声明（Capability Statement）",
      contexts: ["hash", "framework-file-empty", "section"],
    },
    {
      id: "section-boundary",
      label: "## 2. 边界定义（Boundary / Parameter 参数）",
      detail: "插入边界定义主章节",
      documentation: "固定框架章节：边界定义（代码层消费为参数）。",
      insertText: "## 2. 边界定义（Boundary / Parameter 参数）",
      contexts: ["hash", "framework-file-empty", "section"],
    },
    {
      id: "section-base",
      label: "## 3. 最小结构基（Minimal Structural Bases）",
      detail: "插入最小结构基主章节",
      documentation: "固定框架章节：最小结构基。",
      insertText: "## 3. 最小结构基（Minimal Structural Bases）",
      contexts: ["hash", "framework-file-empty", "section"],
    },
    {
      id: "section-rule",
      label: "## 4. 基组合原则（Base Combination Principles）",
      detail: "插入基组合原则主章节",
      documentation: "固定框架章节：基组合原则。",
      insertText: "## 4. 基组合原则（Base Combination Principles）",
      contexts: ["hash", "framework-file-empty", "section"],
    },
    {
      id: "section-verification",
      label: "## 5. 验证（Verification）",
      detail: "插入验证主章节",
      documentation: "固定框架章节：验证。",
      insertText: "## 5. 验证（Verification）",
      contexts: ["hash", "framework-file-empty", "section"],
    },
    {
      id: "capability-item",
      label: "C 条目",
      detail: "插入能力声明条目",
      documentation: "用于 `C*` 能力声明。",
      insertText: `- \`C\${1:${next.C}}\` \${2:能力名}：\${3:待补充结构能力说明}。`,
      contexts: ["list", "capability-symbol", "framework-file-empty", "section-capability"],
    },
    {
      id: "non-responsibility-item",
      label: "N 条目",
      detail: "插入非职责声明条目",
      documentation: "用于 `N*` 非职责声明。",
      insertText: `- \`N\${1:${next.N}}\` \${2:非职责声明}：\${3:待补充非职责范围}。`,
      contexts: [
        "list",
        "non-responsibility-symbol",
        "framework-file-empty",
        "section-capability",
        "section-non-responsibility",
      ],
    },
    {
      id: "boundary-item",
      label: "参数条目",
      detail: "插入边界定义条目",
      documentation: "用于边界定义；可替换 `P1` 为 `SURFACE`、`CHAT` 等稳定参数名。",
      insertText: `- \`\${1:P${next.P}}\` \${2:参数名}：\${3:待定义参数约束}。来源：\`\${4:C1}\`。`,
      contexts: ["list", "boundary-symbol", "framework-file-empty", "section-parameter"],
    },
    {
      id: "base-item",
      label: "B 条目",
      detail: "插入最小结构基条目",
      documentation: "用于 `B*` 结构基定义。",
      insertText: `- \`B\${1:${next.B}}\` \${2:结构基名}：\${3:L0.M0[R1] 或 frontend.L1.M0[R1,R2]}。来源：\`\${4:C1 + P1}\`。`,
      contexts: ["list", "base-symbol", "framework-file-empty", "section-base"],
    },
    {
      id: "rule-block",
      label: "R 规则块",
      detail: "插入完整组合规则块",
      documentation: "用于 `R*` 主规则及 `R*.1~R*.4` 子项。",
      insertText: [
        `- \`R\${1:${next.R}}\` \${2:规则名}`,
        "  - `R${1}.1` 参与基：`${3:B1 + B2}`。",
        "  - `R${1}.2` 组合方式：${4:待补充}。",
        "  - `R${1}.3` 输出能力：`${5:C1}`。",
        "  - `R${1}.4` 参数绑定：`${6:P1/P2}`。",
      ].join("\n"),
      contexts: ["list", "rule-symbol", "framework-file-empty", "section-rule"],
    },
    {
      id: "rule-participants",
      label: "R*.1 参与基",
      detail: "插入组合规则参与基子项",
      documentation: "固定子项：参与基。",
      insertText: `  - \`R\${1:${nearestRuleNumber}}.1\` 参与基：\`\${2:B1 + B2}\`。`,
      contexts: ["rule-child", "rule-symbol", "section-rule"],
    },
    {
      id: "rule-composition",
      label: "R*.2 组合方式",
      detail: "插入组合方式子项",
      documentation: "固定子项：组合方式。",
      insertText: `  - \`R\${1:${nearestRuleNumber}}.2\` 组合方式：\${2:待补充}。`,
      contexts: ["rule-child", "rule-symbol", "section-rule"],
    },
    {
      id: "rule-output",
      label: "R*.3 输出能力",
      detail: "插入输出能力子项",
      documentation: "固定子项：输出能力。",
      insertText: `  - \`R\${1:${nearestRuleNumber}}.3\` 输出能力：\`\${2:C1}\`。`,
      contexts: ["rule-child", "rule-symbol", "section-rule"],
    },
    {
      id: "rule-boundary",
      label: "R*.4 参数绑定",
      detail: "插入参数绑定子项",
      documentation: "固定子项：参数绑定。",
      insertText: `  - \`R\${1:${nearestRuleNumber}}.4\` 参数绑定：\`\${2:P1/P2}\`。`,
      contexts: ["rule-child", "rule-symbol", "section-rule"],
    },
    {
      id: "verification-item",
      label: "V 条目",
      detail: "插入验证条目",
      documentation: "用于 `V*` 验证结论或验证约束。",
      insertText: `- \`V\${1:${next.V}}\` \${2:验证名}：\${3:待补充验证要求}。`,
      contexts: ["list", "verification-symbol", "framework-file-empty", "section-verification"],
    },
  ];
}

function detectFrameworkCompletionContexts(linePrefix, wordPrefix, isFrameworkFile, authoringState = {}) {
  const normalizedLine = linePrefix || "";
  const trimmed = normalizedLine.trimStart();
  const compact = trimmed.replace(/[`。\s]/g, "");
  const upperWord = String(wordPrefix || "").toUpperCase();
  const contexts = new Set();
  const sectionId = String(authoringState.sectionId || "").trim();

  if (isFrameworkFile && trimmed === "") {
    contexts.add("framework-file-empty");
  }
  if (trimmed.startsWith("@")) {
    contexts.add("at");
  }
  if (trimmed.startsWith("#")) {
    contexts.add("hash");
  }
  if (trimmed.startsWith("##")) {
    contexts.add("section");
  }
  if (trimmed.startsWith("-") || trimmed.startsWith("`")) {
    contexts.add("list");
  }
  if (/^C\d*$/.test(upperWord) || compact.startsWith("-C") || compact.startsWith("C")) {
    contexts.add("capability-symbol");
  }
  if (
    /^(P\d*|[A-Z_]{2,})$/.test(upperWord) ||
    compact.startsWith("-P") ||
    compact.startsWith("P") ||
    compact.startsWith("-SURFACE") ||
    compact.startsWith("SURFACE")
  ) {
    contexts.add("boundary-symbol");
  }
  if (/^B\d*$/.test(upperWord) || compact.startsWith("-B") || compact.startsWith("B")) {
    contexts.add("base-symbol");
  }
  if (/^R\d*$/.test(upperWord) || compact.startsWith("-R") || compact.startsWith("R")) {
    contexts.add("rule-symbol");
  }
  if (/^R\d+\.\d*$/.test(upperWord) || compact.startsWith("R1.") || compact.startsWith("-R1.")) {
    contexts.add("rule-child");
  }
  if (/^V\d*$/.test(upperWord) || compact.startsWith("-V") || compact.startsWith("V")) {
    contexts.add("verification-symbol");
  }
  if (/^N\d*$/.test(upperWord) || compact.startsWith("-N") || compact.startsWith("N")) {
    contexts.add("non-responsibility-symbol");
  }
  if (sectionId) {
    contexts.add(`section-${sectionId}`);
  }
  if (authoringState.inNonResponsibility) {
    contexts.add("section-non-responsibility");
  }

  return contexts;
}

function getFrameworkCompletionEntries(linePrefix, wordPrefix, isFrameworkFile, options = {}) {
  const documentText = String(options.documentText || "");
  const lineNumber = Number(options.lineNumber || 0);
  const authoringState = detectFrameworkAuthoringState(documentText, lineNumber);
  const nextNumbers = collectNextSymbolNumbers(documentText);
  const nearestRuleNumber = findNearestRuleNumber(documentText, lineNumber);
  const contexts = detectFrameworkCompletionContexts(linePrefix, wordPrefix, isFrameworkFile, authoringState);
  if (contexts.size === 0) {
    return [];
  }
  const activeSectionContext = [...contexts].find((item) => item.startsWith("section-") && item !== "section-non-responsibility")
    || "";
  const symbolContexts = new Set(
    [...contexts].filter((item) =>
      item.endsWith("-symbol") || item === "rule-child"
    )
  );
  const allDefinitions = createCompletionDefinitions({
    nextNumbers,
    nearestRuleNumber,
  });

  return allDefinitions.filter((entry) => {
    const hasDirectContext = entry.contexts.some((context) => contexts.has(context));
    if (!hasDirectContext) {
      return false;
    }
    if (!activeSectionContext || contexts.has("framework-file-empty")) {
      return true;
    }
    if (entry.contexts.includes(activeSectionContext)) {
      return true;
    }
    if (symbolContexts.size > 0 && entry.contexts.some((context) => symbolContexts.has(context))) {
      return true;
    }
    if (entry.contexts.includes("at") || entry.contexts.includes("hash") || entry.contexts.includes("section")) {
      return true;
    }
    return false;
  });
}

function getFrameworkDashAutoExpansion(linePrefix, isFrameworkFile, options = {}) {
  if (!isFrameworkFile) {
    return null;
  }
  const normalizedLinePrefix = String(linePrefix || "");
  if (!/^\s*-\s*$/.test(normalizedLinePrefix)) {
    return null;
  }
  const documentText = String(options.documentText || "");
  const lineNumber = Number(options.lineNumber || 0);
  const authoringState = detectFrameworkAuthoringState(documentText, lineNumber);
  if (authoringState.sectionId !== "parameter") {
    return null;
  }
  const entries = getFrameworkCompletionEntries(
    normalizedLinePrefix,
    "",
    true,
    {
      documentText,
      lineNumber,
    }
  );
  const boundaryEntry = entries.find((entry) => entry.id === "boundary-item");
  if (!boundaryEntry || typeof boundaryEntry.insertText !== "string" || !boundaryEntry.insertText.startsWith("-")) {
    return null;
  }
  return {
    entryId: boundaryEntry.id,
    insertText: boundaryEntry.insertText.slice(1),
  };
}

module.exports = {
  FRAMEWORK_TEMPLATE_SNIPPET_NAME,
  FRAMEWORK_SECTION_HEADINGS,
  detectFrameworkAuthoringState,
  detectFrameworkCompletionContexts,
  getFrameworkDashAutoExpansion,
  getFrameworkCompletionEntries,
  getFrameworkTemplateSnippetBody,
  getFrameworkTemplateSnippetText,
};
