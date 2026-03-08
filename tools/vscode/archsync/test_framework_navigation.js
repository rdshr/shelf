const assert = require("assert");
const fs = require("fs");
const path = require("path");

const {
  resolveDefinitionTarget,
  resolveReferenceTargets,
  resolveHoverTarget,
} = require("./framework_navigation");

const repoRoot = path.resolve(__dirname, "..", "..", "..");

function loadFrameworkFile(relativePath) {
  const filePath = path.join(repoRoot, relativePath);
  return {
    filePath,
    text: fs.readFileSync(filePath, "utf8"),
  };
}

function locate(text, needle) {
  const index = text.indexOf(needle);
  assert.notStrictEqual(index, -1, `missing needle: ${needle}`);
  const before = text.slice(0, index);
  const line = before.split(/\r?\n/).length - 1;
  const lineStart = before.lastIndexOf("\n") + 1;
  return {
    line,
    character: index - lineStart,
  };
}

function targetLineText(result) {
  const text = fs.readFileSync(result.filePath, "utf8");
  return text.split(/\r?\n/)[result.line] || "";
}

function main() {
  const curtainL2 = loadFrameworkFile("framework/curtain/L2-M0-窗帘框架标准模块.md");
  const capRef = locate(curtainL2.text, "C1 + SPAN");
  const capResult = resolveDefinitionTarget({
    repoRoot,
    filePath: curtainL2.filePath,
    text: curtainL2.text,
    line: capRef.line,
    character: capRef.character,
  });
  assert(capResult, "capability ref should resolve");
  assert(capResult.filePath.endsWith("framework/curtain/L2-M0-窗帘框架标准模块.md"));
  assert(targetLineText(capResult).includes("`C1`"));

  const boundaryRef = locate(curtainL2.text, "SPAN + LOAD");
  const boundaryResult = resolveDefinitionTarget({
    repoRoot,
    filePath: curtainL2.filePath,
    text: curtainL2.text,
    line: boundaryRef.line,
    character: boundaryRef.character,
  });
  assert(boundaryResult, "boundary ref should resolve");
  assert(targetLineText(boundaryResult).includes("`SPAN`"));

  const baseRef = locate(curtainL2.text, "`B1 + B2`");
  const baseResult = resolveDefinitionTarget({
    repoRoot,
    filePath: curtainL2.filePath,
    text: curtainL2.text,
    line: baseRef.line,
    character: baseRef.character + 1,
  });
  assert(baseResult, "base ref should resolve");
  assert(targetLineText(baseResult).includes("`B1`"));

  const verifyRef = locate(curtainL2.text, "`R1` 必须满足");
  const verifyResult = resolveDefinitionTarget({
    repoRoot,
    filePath: curtainL2.filePath,
    text: curtainL2.text,
    line: verifyRef.line,
    character: verifyRef.character + 1,
  });
  assert(verifyResult, "verification rule ref should resolve");
  assert(targetLineText(verifyResult).includes("`R1`"));

  const moduleRef = locate(curtainL2.text, "L1.M0[R1]");
  const moduleResult = resolveDefinitionTarget({
    repoRoot,
    filePath: curtainL2.filePath,
    text: curtainL2.text,
    line: moduleRef.line,
    character: moduleRef.character + 1,
  });
  assert(moduleResult, "module ref should resolve");
  assert(moduleResult.filePath.endsWith("framework/curtain/L1-M0-安装与控制编排模块.md"));
  assert(targetLineText(moduleResult).includes("`B1`"));

  const knowledgeBaseL0 = loadFrameworkFile("framework/knowledge_base/L0-M0-文件库与摄取原子模块.md");
  const externalRuleRef = locate(knowledgeBaseL0.text, "frontend.L1.M3[R1,R2]");
  const externalRuleResult = resolveDefinitionTarget({
    repoRoot,
    filePath: knowledgeBaseL0.filePath,
    text: knowledgeBaseL0.text,
    line: externalRuleRef.line,
    character: externalRuleRef.character + "frontend.L1.M3[".length + 3,
  });
  assert(externalRuleResult, "external rule ref should resolve");
  assert(externalRuleResult.filePath.endsWith("framework/frontend/L1-M3-集合与导航原子模块.md"));
  assert(targetLineText(externalRuleResult).includes("`R2`"));

  const knowledgeBaseL2 = loadFrameworkFile("framework/knowledge_base/L0-M2-对话与引用原子模块.md");
  const moduleHoverRef = locate(knowledgeBaseL2.text, "frontend.L1.M2[R1,R2]");
  const hoverResult = resolveHoverTarget({
    repoRoot,
    filePath: knowledgeBaseL2.filePath,
    text: knowledgeBaseL2.text,
    line: moduleHoverRef.line,
    character: moduleHoverRef.character + "frontend.L1.M2".length - 1,
  });
  assert(hoverResult, "module hover should resolve");
  assert.strictEqual(hoverResult.end - hoverResult.start, "frontend.L1.M2".length);
  assert(hoverResult.markdown.includes("**frontend.L1.M2**"));
  assert(hoverResult.markdown.includes("能力声明"));
  assert(hoverResult.markdown.includes("- `C1` 文本展示能力"));
  assert(hoverResult.markdown.includes("最小可行基"));
  assert(hoverResult.markdown.includes("- `B1` 文本展示结构基"));
  assert(hoverResult.markdown.includes("基组合原则"));
  assert(hoverResult.markdown.includes("参与基：`B1`"));
  assert(hoverResult.markdown.includes("组合方式：先固定标题、正文、说明与元信息的阅读顺序"));

  const moduleRuleHoverResult = resolveHoverTarget({
    repoRoot,
    filePath: knowledgeBaseL2.filePath,
    text: knowledgeBaseL2.text,
    line: moduleHoverRef.line,
    character: moduleHoverRef.character + "frontend.L1.M2[".length + 1,
  });
  assert(moduleRuleHoverResult, "module rule hover should resolve");
  assert(moduleRuleHoverResult.markdown.includes("**frontend.L1.M2 · `R1`**"));
  assert(moduleRuleHoverResult.markdown.includes("参与基：`B1`"));
  assert(moduleRuleHoverResult.markdown.includes("输出能力：`C1`"));

  const localBaseHoverRef = locate(knowledgeBaseL2.text, "`B1` 对话舞台结构基");
  const localBaseHoverResult = resolveHoverTarget({
    repoRoot,
    filePath: knowledgeBaseL2.filePath,
    text: knowledgeBaseL2.text,
    line: localBaseHoverRef.line,
    character: localBaseHoverRef.character + 1,
  });
  assert(localBaseHoverResult, "local base hover should resolve");
  assert(localBaseHoverResult.markdown.includes("**knowledge_base.L0.M2 · `B1`**"));
  assert(localBaseHoverResult.markdown.includes("`B1` 对话舞台结构基"));

  const localBoundaryHoverRef = locate(knowledgeBaseL2.text, "`TURN` 回合边界");
  const localBoundaryHoverResult = resolveHoverTarget({
    repoRoot,
    filePath: knowledgeBaseL2.filePath,
    text: knowledgeBaseL2.text,
    line: localBoundaryHoverRef.line,
    character: localBoundaryHoverRef.character + 1,
  });
  assert(localBoundaryHoverResult, "local boundary hover should resolve");
  assert(localBoundaryHoverResult.markdown.includes("**knowledge_base.L0.M2 · `TURN`**"));
  assert(localBoundaryHoverResult.markdown.includes("`TURN` 回合边界"));

  const localCapabilityHoverRef = locate(knowledgeBaseL2.text, "`C1` 对话舞台承载能力");
  const localCapabilityHoverResult = resolveHoverTarget({
    repoRoot,
    filePath: knowledgeBaseL2.filePath,
    text: knowledgeBaseL2.text,
    line: localCapabilityHoverRef.line,
    character: localCapabilityHoverRef.character + 1,
  });
  assert(localCapabilityHoverResult, "local capability hover should resolve");
  assert(localCapabilityHoverResult.markdown.includes("**knowledge_base.L0.M2 · `C1`**"));

  const localRuleHoverRef = locate(knowledgeBaseL2.text, "`R1` 对话舞台先行");
  const localRuleHoverResult = resolveHoverTarget({
    repoRoot,
    filePath: knowledgeBaseL2.filePath,
    text: knowledgeBaseL2.text,
    line: localRuleHoverRef.line,
    character: localRuleHoverRef.character + 1,
  });
  assert(localRuleHoverResult, "local rule hover should resolve");
  assert(localRuleHoverResult.markdown.includes("**knowledge_base.L0.M2 · `R1`**"));
  assert(localRuleHoverResult.markdown.includes("参与基：`B1 + B2`"));
  assert(localRuleHoverResult.markdown.includes("边界绑定：`TURN/INPUT/STATUS/A11Y`"));

  const localVerificationHoverRef = locate(knowledgeBaseL2.text, "`V1` 回合完整性");
  const localVerificationHoverResult = resolveHoverTarget({
    repoRoot,
    filePath: knowledgeBaseL2.filePath,
    text: knowledgeBaseL2.text,
    line: localVerificationHoverRef.line,
    character: localVerificationHoverRef.character + 1,
  });
  assert(localVerificationHoverResult, "local verification hover should resolve");
  assert(localVerificationHoverResult.markdown.includes("**knowledge_base.L0.M2 · `V1`**"));

  const workbenchL2 = loadFrameworkFile("framework/knowledge_base/L2-M0-知识库工作台场景模块.md");
  const boundaryConfigRef = locate(workbenchL2.text, "CHAT + CONTEXT + RETURN");
  const boundaryConfigResult = resolveDefinitionTarget({
    repoRoot,
    filePath: workbenchL2.filePath,
    text: workbenchL2.text,
    line: boundaryConfigRef.line,
    character: boundaryConfigRef.character,
  });
  assert(boundaryConfigResult, "instance boundary ref should resolve");
  assert(boundaryConfigResult.filePath.endsWith("projects/knowledge_base_basic/instance.toml"));
  assert.strictEqual(targetLineText(boundaryConfigResult).trim(), "[chat]");

  const boundaryDefinitionRef = locate(workbenchL2.text, "`CHAT` 对话边界");
  const boundaryDefinitionResult = resolveDefinitionTarget({
    repoRoot,
    filePath: workbenchL2.filePath,
    text: workbenchL2.text,
    line: boundaryDefinitionRef.line,
    character: boundaryDefinitionRef.character + 1,
  });
  assert(boundaryDefinitionResult, "boundary definition should still resolve locally");
  assert(boundaryDefinitionResult.filePath.endsWith("framework/knowledge_base/L2-M0-知识库工作台场景模块.md"));
  assert(targetLineText(boundaryDefinitionResult).includes("`CHAT` 对话边界"));

  const boundaryConfigHoverResult = resolveHoverTarget({
    repoRoot,
    filePath: workbenchL2.filePath,
    text: workbenchL2.text,
    line: boundaryConfigRef.line,
    character: boundaryConfigRef.character,
  });
  assert(boundaryConfigHoverResult, "boundary config hover should resolve");
  assert(boundaryConfigHoverResult.markdown.includes("实例配置"));
  assert(boundaryConfigHoverResult.markdown.includes("projects/knowledge_base_basic/instance.toml"));
  assert(boundaryConfigHoverResult.markdown.includes("`[chat]`"));

  const citationConfigRef = locate(knowledgeBaseL2.text, "CITATION + SCOPE");
  const citationConfigResult = resolveDefinitionTarget({
    repoRoot,
    filePath: knowledgeBaseL2.filePath,
    text: knowledgeBaseL2.text,
    line: citationConfigRef.line,
    character: citationConfigRef.character,
  });
  assert(citationConfigResult, "derived citation boundary ref should resolve");
  assert(citationConfigResult.filePath.endsWith("projects/knowledge_base_basic/instance.toml"));
  assert.strictEqual(targetLineText(citationConfigResult).trim(), "[chat]");

  const citationConfigHoverResult = resolveHoverTarget({
    repoRoot,
    filePath: knowledgeBaseL2.filePath,
    text: knowledgeBaseL2.text,
    line: citationConfigRef.line,
    character: citationConfigRef.character,
  });
  assert(citationConfigHoverResult, "derived citation boundary hover should resolve");
  assert(citationConfigHoverResult.markdown.includes("`[chat]`"));
  assert(citationConfigHoverResult.markdown.includes("`[context]`"));
  assert(citationConfigHoverResult.markdown.includes("`[return]`"));
  assert(citationConfigHoverResult.markdown.includes("归属说明"));

  const citationReferences = resolveReferenceTargets({
    repoRoot,
    filePath: knowledgeBaseL2.filePath,
    text: knowledgeBaseL2.text,
    line: citationConfigRef.line,
    character: citationConfigRef.character,
  });
  assert(citationReferences.length >= 3, "citation references should include usage, definition, and config");
  assert(citationReferences.some((item) => item.filePath.endsWith("framework/knowledge_base/L0-M2-对话与引用原子模块.md")));
  assert(citationReferences.some((item) => item.filePath.endsWith("projects/knowledge_base_basic/instance.toml")));

  const a11yConfigRef = locate(knowledgeBaseL2.text, "STATUS + A11Y");
  const a11yConfigResult = resolveDefinitionTarget({
    repoRoot,
    filePath: knowledgeBaseL2.filePath,
    text: knowledgeBaseL2.text,
    line: a11yConfigRef.line,
    character: a11yConfigRef.character + "STATUS + ".length,
  });
  assert(a11yConfigResult, "knowledge base A11Y boundary ref should resolve");
  assert(a11yConfigResult.filePath.endsWith("projects/knowledge_base_basic/instance.toml"));
  assert.strictEqual(targetLineText(a11yConfigResult).trim(), "[a11y]");

  const frontendTokenL0 = loadFrameworkFile("framework/frontend/L0-M2-视觉语义原子模块.md");
  const tokenConfigRef = locate(frontendTokenL0.text, "TOKEN + DENSITY");
  const tokenConfigResult = resolveDefinitionTarget({
    repoRoot,
    filePath: frontendTokenL0.filePath,
    text: frontendTokenL0.text,
    line: tokenConfigRef.line,
    character: tokenConfigRef.character,
  });
  assert(tokenConfigResult, "frontend TOKEN boundary ref should resolve");
  assert(tokenConfigResult.filePath.endsWith("projects/knowledge_base_basic/instance.toml"));
  assert.strictEqual(targetLineText(tokenConfigResult).trim(), "[visual]");

  const frontendEntryL1 = loadFrameworkFile("framework/frontend/L1-M0-触发与选择原子模块.md");
  const entryA11yRef = locate(frontendEntryL1.text, "PICK + OPTION + ACTION + A11Y");
  const entryA11yResult = resolveDefinitionTarget({
    repoRoot,
    filePath: frontendEntryL1.filePath,
    text: frontendEntryL1.text,
    line: entryA11yRef.line,
    character: entryA11yRef.character + "PICK + OPTION + ACTION + ".length,
  });
  assert(entryA11yResult, "frontend A11Y boundary ref should resolve");
  assert(entryA11yResult.filePath.endsWith("projects/knowledge_base_basic/instance.toml"));
  assert.strictEqual(targetLineText(entryA11yResult).trim(), "[a11y]");

  const backendL2 = loadFrameworkFile("framework/backend/L2-M0-知识库接口框架标准模块.md");
  const backendResultRef = locate(backendL2.text, "CHAT + RESULT + TRACE");
  const backendResult = resolveDefinitionTarget({
    repoRoot,
    filePath: backendL2.filePath,
    text: backendL2.text,
    line: backendResultRef.line,
    character: backendResultRef.character + "CHAT + ".length,
  });
  assert(backendResult, "backend RESULT boundary ref should resolve");
  assert(backendResult.filePath.endsWith("projects/knowledge_base_basic/instance.toml"));
  assert.strictEqual(targetLineText(backendResult).trim(), "[return]");
}

main();
