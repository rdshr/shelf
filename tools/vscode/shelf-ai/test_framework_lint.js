const assert = require("assert");
const path = require("path");

const { lintFrameworkMarkdown } = require("./framework_lint");

const repoRoot = path.resolve(__dirname, "..", "..", "..");

const VALID_FRAMEWORK_TEXT = [
  "# 知识库文本单元模块:KnowledgeBaseTextUnitModule",
  "",
  "@framework",
  "",
  "## 1. 能力声明（Capability Statement）",
  "",
  "- `C1` 单元定位能力：支持通过定位键唯一定位文本单元。",
  "### 非职责声明（Non-Responsibility Statement）",
  "- `N1` 非职责声明：不负责复杂语义检索。",
  "",
  "## 2. 边界定义（Boundary / Parameter 参数）",
  "",
  "- `P1` 文档标识参数：用于限定文本单元所属文档。来源：`C1`。",
  "",
  "## 3. 最小结构基（Minimal Structural Bases）",
  "",
  "- `B1` 文本索引基：L0.M0[R1]。来源：`C1 + P1`。",
  "",
  "## 4. 基组合原则（Base Combination Principles）",
  "",
  "- `R1` 文本定位组合",
  "  - `R1.1` 参与基：`B1`。",
  "  - `R1.2` 组合方式：按索引优先，再做局部过滤。",
  "  - `R1.3` 输出能力：`C1`。",
  "  - `R1.4` 参数绑定：`P1`。",
  "",
  "## 5. 验证（Verification）",
  "",
  "- `V1` 定位验证：给定定位键时必须返回唯一文本单元。",
].join("\n");

function runLint(text) {
  return lintFrameworkMarkdown({
    repoRoot,
    filePath: path.join(repoRoot, "framework", "backend", "L0-M0-测试模块.md"),
    text,
  });
}

function main() {
  const validIssues = runLint(VALID_FRAMEWORK_TEXT);
  assert.strictEqual(validIssues.length, 0, "valid framework text should not produce lint issues");

  const starText = VALID_FRAMEWORK_TEXT.replace(
    "- `C1` 单元定位能力：支持通过定位键唯一定位文本单元。",
    "* `C1` 单元定位能力：支持通过定位键唯一定位文本单元。"
  );
  const starIssues = runLint(starText);
  assert(starIssues.some((issue) => issue.code === "FWL004"), "star list marker should be rejected");

  const missingSectionText = VALID_FRAMEWORK_TEXT.replace(
    "## 5. 验证（Verification）\n\n- `V1` 定位验证：给定定位键时必须返回唯一文本单元。",
    ""
  );
  const missingIssues = runLint(missingSectionText);
  assert(
    missingIssues.some((issue) => issue.code === "FWL003"),
    "missing required section should be reported"
  );
}

main();
