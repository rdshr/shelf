const assert = require("assert");
const fs = require("fs");
const path = require("path");

const {
  resolveDefinitionTarget,
  resolveHoverTarget,
  resolveReferenceTargets,
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
  const knowledgeBaseL0 = loadFrameworkFile("framework/knowledge_base/L0-M2-对话与引用原子模块.md");
  const moduleRef = locate(knowledgeBaseL0.text, "frontend.L1.M2[R1,R2]");
  const moduleResult = resolveDefinitionTarget({
    repoRoot,
    filePath: knowledgeBaseL0.filePath,
    text: knowledgeBaseL0.text,
    line: moduleRef.line,
    character: moduleRef.character + 1,
  });
  assert(moduleResult, "module ref should resolve");
  assert(moduleResult.filePath.endsWith("framework/frontend/L1-M2-展示与容器原子模块.md"));

  const moduleHover = resolveHoverTarget({
    repoRoot,
    filePath: knowledgeBaseL0.filePath,
    text: knowledgeBaseL0.text,
    line: moduleRef.line,
    character: moduleRef.character + "frontend.L1.M2".length - 1,
  });
  assert(moduleHover, "module hover should resolve");
  assert(moduleHover.markdown.includes("**frontend.L1.M2**"));
  assert(moduleHover.markdown.includes("能力声明"));

  const workbenchL2 = loadFrameworkFile("framework/knowledge_base/L2-M0-知识库工作台场景模块.md");
  const boundaryConfigRef = locate(workbenchL2.text, "CHAT + CONTEXT + RETURN");
  const boundaryConfigResult = resolveDefinitionTarget({
    repoRoot,
    filePath: workbenchL2.filePath,
    text: workbenchL2.text,
    line: boundaryConfigRef.line,
    character: boundaryConfigRef.character,
  });
  assert(boundaryConfigResult, "boundary config ref should resolve");
  assert(boundaryConfigResult.filePath.endsWith("projects/knowledge_base_basic/project.toml"));
  assert.strictEqual(targetLineText(boundaryConfigResult).trim(), "[truth.chat]");

  const boundaryHover = resolveHoverTarget({
    repoRoot,
    filePath: workbenchL2.filePath,
    text: workbenchL2.text,
    line: boundaryConfigRef.line,
    character: boundaryConfigRef.character,
  });
  assert(boundaryHover, "boundary hover should resolve");
  assert(boundaryHover.markdown.includes("Project Config"));
  assert(boundaryHover.markdown.includes("projects/knowledge_base_basic/project.toml"));
  assert(boundaryHover.markdown.includes("`[truth.chat]`"));

  const boundaryRefs = resolveReferenceTargets({
    repoRoot,
    filePath: workbenchL2.filePath,
    text: workbenchL2.text,
    line: boundaryConfigRef.line,
    character: boundaryConfigRef.character,
  });
  assert(
    boundaryRefs.some((item) => item.filePath.endsWith("projects/knowledge_base_basic/project.toml")),
    "boundary references should include the unified project config target"
  );
}

main();
