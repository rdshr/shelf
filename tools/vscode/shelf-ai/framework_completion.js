const fs = require("fs");
const path = require("path");

const MARKDOWN_SNIPPETS_FILE = path.join(__dirname, "snippets", "markdown.code-snippets");
const FRAMEWORK_TEMPLATE_SNIPPET_NAME = "@framework Module Template";

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

function createCompletionDefinitions() {
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
      documentation: "覆盖标题、@framework、能力声明、参数、最小可行基、组合原则与验证。",
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
      label: "## 2. 参数定义（Parameter）",
      detail: "插入参数定义主章节",
      documentation: "固定框架章节：参数定义。",
      insertText: "## 2. 参数定义（Parameter）",
      contexts: ["hash", "framework-file-empty", "section"],
    },
    {
      id: "section-base",
      label: "## 3. 最小可行基（Minimum Viable Bases）",
      detail: "插入最小可行基主章节",
      documentation: "固定框架章节：最小可行基。",
      insertText: "## 3. 最小可行基（Minimum Viable Bases）",
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
      insertText: "- `C${1:1}` ${2:能力名}：${3:待补充结构能力说明}。",
      contexts: ["list", "capability-symbol", "framework-file-empty"],
    },
    {
      id: "boundary-item",
      label: "参数条目",
      detail: "插入参数定义条目",
      documentation: "用于参数定义；可替换 `P1` 为 `SURFACE`、`CHAT` 等稳定参数名。",
      insertText: "- `${1:P1}` ${2:参数名}：${3:待定义参数约束}。来源：`${4:C1}`。",
      contexts: ["list", "boundary-symbol", "framework-file-empty"],
    },
    {
      id: "base-item",
      label: "B 条目",
      detail: "插入最小可行基条目",
      documentation: "用于 `B*` 结构基定义。",
      insertText: "- `B${1:1}` ${2:结构基名}：${3:L0.M0[R1] 或 frontend.L1.M0[R1,R2]}。来源：`${4:C1 + P1}`。",
      contexts: ["list", "base-symbol", "framework-file-empty"],
    },
    {
      id: "rule-block",
      label: "R 规则块",
      detail: "插入完整组合规则块",
      documentation: "用于 `R*` 主规则及 `R*.1~R*.4` 子项。",
      insertText: [
        "- `R${1:1}` ${2:规则名}",
        "  - `R${1}.1` 参与基：`${3:B1 + B2}`。",
        "  - `R${1}.2` 组合方式：${4:待补充}。",
        "  - `R${1}.3` 输出能力：`${5:C1}`。",
        "  - `R${1}.4` 参数绑定：`${6:P1/P2}`。",
      ].join("\n"),
      contexts: ["list", "rule-symbol", "framework-file-empty"],
    },
    {
      id: "rule-participants",
      label: "R*.1 参与基",
      detail: "插入组合规则参与基子项",
      documentation: "固定子项：参与基。",
      insertText: "  - `R${1:1}.1` 参与基：`${2:B1 + B2}`。",
      contexts: ["rule-child", "rule-symbol"],
    },
    {
      id: "rule-composition",
      label: "R*.2 组合方式",
      detail: "插入组合方式子项",
      documentation: "固定子项：组合方式。",
      insertText: "  - `R${1:1}.2` 组合方式：${2:待补充}。",
      contexts: ["rule-child", "rule-symbol"],
    },
    {
      id: "rule-output",
      label: "R*.3 输出能力",
      detail: "插入输出能力子项",
      documentation: "固定子项：输出能力。",
      insertText: "  - `R${1:1}.3` 输出能力：`${2:C1}`。",
      contexts: ["rule-child", "rule-symbol"],
    },
    {
      id: "rule-boundary",
      label: "R*.4 参数绑定",
      detail: "插入参数绑定子项",
      documentation: "固定子项：参数绑定。",
      insertText: "  - `R${1:1}.4` 参数绑定：`${2:P1/P2}`。",
      contexts: ["rule-child", "rule-symbol"],
    },
    {
      id: "verification-item",
      label: "V 条目",
      detail: "插入验证条目",
      documentation: "用于 `V*` 验证结论或验证约束。",
      insertText: "- `V${1:1}` ${2:验证名}：${3:待补充验证要求}。",
      contexts: ["list", "verification-symbol", "framework-file-empty"],
    },
  ];
}

function detectFrameworkCompletionContexts(linePrefix, wordPrefix, isFrameworkFile) {
  const normalizedLine = linePrefix || "";
  const trimmed = normalizedLine.trimStart();
  const compact = trimmed.replace(/[`。\s]/g, "");
  const upperWord = String(wordPrefix || "").toUpperCase();
  const contexts = new Set();

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

  return contexts;
}

function getFrameworkCompletionEntries(linePrefix, wordPrefix, isFrameworkFile) {
  const contexts = detectFrameworkCompletionContexts(linePrefix, wordPrefix, isFrameworkFile);
  if (contexts.size === 0) {
    return [];
  }

  return createCompletionDefinitions().filter((entry) =>
    entry.contexts.some((context) => contexts.has(context))
  );
}

module.exports = {
  FRAMEWORK_TEMPLATE_SNIPPET_NAME,
  detectFrameworkCompletionContexts,
  getFrameworkCompletionEntries,
  getFrameworkTemplateSnippetBody,
  getFrameworkTemplateSnippetText,
};
