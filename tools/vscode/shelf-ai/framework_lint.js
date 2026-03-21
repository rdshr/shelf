const path = require("path");

const TITLE_PATTERN = /^#\s+(?<cn>[^:]+):(?<en>.+)$/;
const CAPABILITY_LINE_PATTERN = /^-\s+`(?<id>C\d+)`\s+(?<name>[^：:]+)[：:]\s*(?<body>.+)$/;
const NON_RESPONSIBILITY_LINE_PATTERN = /^-\s+`(?<id>N\d+)`\s+(?<name>[^：:]+)[：:]\s*(?<body>.+)$/;
const BOUNDARY_LINE_PATTERN = /^-\s+`(?<id>[A-Z0-9_]+)`\s+(?<name>[^：:]+)[：:]\s*(?<body>.+)$/;
const BASE_LINE_PATTERN = /^-\s+`(?<id>B\d+)`\s+(?<name>[^：:]+)[：:]\s*(?<body>.+)$/;
const VERIFY_LINE_PATTERN = /^-\s+`(?<id>V\d+)`\s+(?<name>[^：:]+)[：:]\s*(?<body>.+)$/;
const RULE_TOP_PATTERN = /^-\s+`(?<id>R\d+)`\s+(?<name>.+)$/;
const RULE_CHILD_PATTERN = /^\s*-\s+`(?<id>R\d+\.\d+)`\s+(?<body>.+)$/;

const SECTION_CAPABILITY_TITLES = ["## 1. 能力声明（Capability Statement）"];
const SECTION_PARAMETER_TITLES = [
  "## 2. 边界定义（Boundary / Parameter 参数）",
];
const SECTION_BASE_TITLES = ["## 3. 最小结构基（Minimal Structural Bases）"];
const SECTION_RULE_TITLES = ["## 4. 基组合原则（Base Combination Principles）"];
const SECTION_VERIFICATION_TITLES = ["## 5. 验证（Verification）"];

function normalizeSlashes(value) {
  return String(value || "").replace(/\\/g, "/");
}

function toRelativeFilePath(filePath, repoRoot) {
  if (!filePath) {
    return null;
  }
  if (!repoRoot) {
    return normalizeSlashes(filePath);
  }
  const relative = normalizeSlashes(path.relative(repoRoot, filePath));
  if (relative.startsWith("../") || relative === "..") {
    return normalizeSlashes(filePath);
  }
  return relative;
}

function createIssue({ file, line, column, code, message, level = "error" }) {
  return {
    file,
    line: Number(line || 1),
    column: Number(column || 1),
    code,
    message,
    level,
  };
}

function splitSectionBlocks(lines) {
  const blocks = [];
  let current = null;

  for (let index = 0; index < lines.length; index += 1) {
    const raw = lines[index];
    const trimmed = raw.trim();
    if (trimmed.startsWith("## ")) {
      current = {
        title: trimmed,
        line: index + 1,
        entries: [],
      };
      blocks.push(current);
      continue;
    }
    if (!current) {
      continue;
    }
    current.entries.push({
      line: index + 1,
      text: raw,
      trimmed,
    });
  }

  return blocks;
}

function findSectionBlock(blocks, titles) {
  return blocks.find((block) => titles.includes(block.title)) || null;
}

function firstNonEmptyLine(lines) {
  for (let index = 0; index < lines.length; index += 1) {
    if (lines[index].trim()) {
      return {
        line: index + 1,
        text: lines[index].trim(),
      };
    }
  }
  return null;
}

function markerColumn(rawLine) {
  const starIndex = rawLine.indexOf("*");
  if (starIndex >= 0) {
    return starIndex + 1;
  }
  const dashIndex = rawLine.indexOf("-");
  if (dashIndex >= 0) {
    return dashIndex + 1;
  }
  const firstChar = rawLine.search(/\S/);
  return firstChar >= 0 ? firstChar + 1 : 1;
}

function lintFlatListSection({
  block,
  file,
  issues,
  validPattern,
  allowPatterns = [],
  invalidCode,
  invalidMessage,
  allowHeading = false,
}) {
  let matchCount = 0;

  for (const row of block.entries) {
    if (!row.trimmed || row.trimmed === "---") {
      continue;
    }
    if (allowHeading && row.trimmed.startsWith("### ")) {
      continue;
    }
    if (!/^[-*]\s+/.test(row.trimmed)) {
      continue;
    }
    if (/^\*\s+/.test(row.trimmed)) {
      issues.push(
        createIssue({
          file,
          line: row.line,
          column: markerColumn(row.text),
          code: "FWL004",
          message: "列表项必须使用 `-`，不要使用 `*`。",
        })
      );
      continue;
    }

    const isAllowed = validPattern.test(row.trimmed)
      || allowPatterns.some((pattern) => pattern.test(row.trimmed));
    if (isAllowed) {
      matchCount += 1;
      continue;
    }

    issues.push(
      createIssue({
        file,
        line: row.line,
        column: markerColumn(row.text),
        code: invalidCode,
        message: invalidMessage,
      })
    );
  }

  if (matchCount === 0) {
    issues.push(
      createIssue({
        file,
        line: block.line,
        column: 1,
        code: "FWL010",
        level: "warning",
        message: `章节“${block.title}”没有可解析的条目。`,
      })
    );
  }
}

function lintRuleSection({ block, file, issues }) {
  let matchCount = 0;

  for (const row of block.entries) {
    if (!row.trimmed || row.trimmed === "---") {
      continue;
    }
    if (!/^\s*[-*]\s+/.test(row.text)) {
      continue;
    }
    if (/^\s*\*\s+/.test(row.text)) {
      issues.push(
        createIssue({
          file,
          line: row.line,
          column: markerColumn(row.text),
          code: "FWL004",
          message: "列表项必须使用 `-`，不要使用 `*`。",
        })
      );
      continue;
    }

    const matchesTop = RULE_TOP_PATTERN.test(row.trimmed);
    const matchesChild = RULE_CHILD_PATTERN.test(row.text);
    if (matchesTop || matchesChild) {
      matchCount += 1;
      continue;
    }

    issues.push(
      createIssue({
        file,
        line: row.line,
        column: markerColumn(row.text),
        code: "FWL008",
        message: "规则章节条目格式错误，必须匹配 `- `R*`` 或 `- `R*.*``。",
      })
    );
  }

  if (matchCount === 0) {
    issues.push(
      createIssue({
        file,
        line: block.line,
        column: 1,
        code: "FWL010",
        level: "warning",
        message: `章节“${block.title}”没有可解析的条目。`,
      })
    );
  }
}

function lintFrameworkMarkdown({ repoRoot, filePath, text }) {
  const lines = String(text || "").split(/\r?\n/);
  const file = toRelativeFilePath(filePath, repoRoot);
  const issues = [];

  const firstLine = firstNonEmptyLine(lines);
  if (!firstLine) {
    issues.push(
      createIssue({
        file,
        line: 1,
        column: 1,
        code: "FWL001",
        message: "框架文件缺少标题行 `# 中文名:EnglishName`。",
      })
    );
    return issues;
  }

  if (!TITLE_PATTERN.test(firstLine.text)) {
    issues.push(
      createIssue({
        file,
        line: firstLine.line,
        column: 1,
        code: "FWL001",
        message: "标题格式错误，必须是 `# 中文名:EnglishName`。",
      })
    );
  }

  const directiveLines = [];
  for (let index = 0; index < lines.length; index += 1) {
    const trimmed = lines[index].trim();
    if (trimmed.startsWith("@framework")) {
      directiveLines.push({
        line: index + 1,
        text: trimmed,
      });
    }
  }

  if (directiveLines.length === 0) {
    issues.push(
      createIssue({
        file,
        line: Math.max(1, firstLine.line + 1),
        column: 1,
        code: "FWL002",
        message: "缺少 `@framework` 指令。",
      })
    );
  }
  for (const directive of directiveLines) {
    if (directive.text !== "@framework") {
      issues.push(
        createIssue({
          file,
          line: directive.line,
          column: 1,
          code: "FWL002",
          message: "`@framework` 必须为无参数单行指令。",
        })
      );
    }
  }

  const sectionBlocks = splitSectionBlocks(lines);
  const requiredSections = [
    SECTION_CAPABILITY_TITLES,
    SECTION_PARAMETER_TITLES,
    SECTION_BASE_TITLES,
    SECTION_RULE_TITLES,
    SECTION_VERIFICATION_TITLES,
  ];

  for (const titles of requiredSections) {
    if (findSectionBlock(sectionBlocks, titles)) {
      continue;
    }
    issues.push(
      createIssue({
        file,
        line: 1,
        column: 1,
        code: "FWL003",
        message: `缺少必需章节：${titles.join(" / ")}`,
      })
    );
  }

  const capabilitySection = findSectionBlock(sectionBlocks, SECTION_CAPABILITY_TITLES);
  if (capabilitySection) {
    lintFlatListSection({
      block: capabilitySection,
      file,
      issues,
      validPattern: CAPABILITY_LINE_PATTERN,
      allowPatterns: [NON_RESPONSIBILITY_LINE_PATTERN],
      invalidCode: "FWL005",
      invalidMessage: "能力章节条目格式错误，必须匹配 `- `C*` 名称：描述。`。",
      allowHeading: true,
    });
  }

  const parameterSection = findSectionBlock(sectionBlocks, SECTION_PARAMETER_TITLES);
  if (parameterSection) {
    lintFlatListSection({
      block: parameterSection,
      file,
      issues,
      validPattern: BOUNDARY_LINE_PATTERN,
      invalidCode: "FWL006",
      invalidMessage: "参数章节条目格式错误，必须匹配 `- `PARAM` 名称：描述。来源：`C*``。",
    });
  }

  const baseSection = findSectionBlock(sectionBlocks, SECTION_BASE_TITLES);
  if (baseSection) {
    lintFlatListSection({
      block: baseSection,
      file,
      issues,
      validPattern: BASE_LINE_PATTERN,
      invalidCode: "FWL007",
      invalidMessage: "最小结构基章节条目格式错误，必须匹配 `- `B*` 名称：描述。来源：`...``。",
    });
  }

  const ruleSection = findSectionBlock(sectionBlocks, SECTION_RULE_TITLES);
  if (ruleSection) {
    lintRuleSection({
      block: ruleSection,
      file,
      issues,
    });
  }

  const verificationSection = findSectionBlock(sectionBlocks, SECTION_VERIFICATION_TITLES);
  if (verificationSection) {
    lintFlatListSection({
      block: verificationSection,
      file,
      issues,
      validPattern: VERIFY_LINE_PATTERN,
      invalidCode: "FWL009",
      invalidMessage: "验证章节条目格式错误，必须匹配 `- `V*` 名称：描述。`。",
    });
  }

  return issues;
}

module.exports = {
  lintFrameworkMarkdown,
};
