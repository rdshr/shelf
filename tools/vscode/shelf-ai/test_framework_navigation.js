const assert = require("assert");
const fs = require("fs");
const os = require("os");
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

function loadFrameworkFileIfExists(relativePath) {
  const filePath = path.join(repoRoot, relativePath);
  if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
    return null;
  }
  return {
    filePath,
    text: fs.readFileSync(filePath, "utf8"),
  };
}

function discoverKnowledgeProjectRelPath() {
  const projectsDir = path.join(repoRoot, "projects");
  if (!fs.existsSync(projectsDir)) {
    return null;
  }
  const entries = fs.readdirSync(projectsDir, { withFileTypes: true });
  for (const entry of entries) {
    if (!entry.isDirectory()) {
      continue;
    }
    const projectRelPath = `projects/${entry.name}/project.toml`;
    const projectAbsPath = path.join(repoRoot, projectRelPath);
    if (!fs.existsSync(projectAbsPath) || !fs.statSync(projectAbsPath).isFile()) {
      continue;
    }
    const text = fs.readFileSync(projectAbsPath, "utf8");
    if (text.includes("framework/knowledge_base/")) {
      return projectRelPath;
    }
  }
  return null;
}

function moduleIdFromFrameworkPath(relativeFrameworkPath) {
  const normalized = String(relativeFrameworkPath || "").replace(/\\/g, "/");
  const match = /^framework\/([^/]+)\/L(\d+)-M(\d+)-/.exec(normalized);
  if (!match) {
    return "";
  }
  return `${match[1]}.L${match[2]}.M${match[3]}`;
}

function fallbackWorkbenchModuleText() {
  return `
# 知识库工作台场景模块

## 1. 能力声明

- \`C1\`：最小场景能力

## 2. 边界定义（Boundary / Parameter 参数）

- \`CHAT\`：聊天参数
- \`CONTEXT\`：上下文参数
- \`RETURN\`：回跳参数

## 3. 最小结构基（Minimal Structural Bases）

- \`B1\`：最小承载基

## 4. 基组合原则

- \`R1\`：基础组合
  - 参与基：\`B1\`
  - 基组合：\`B1\`
  - 输出能力：\`C1\`
  - 参数绑定：CHAT + CONTEXT + RETURN

## 5. 验证

- \`V1\`：最小验证
`.trimStart();
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

function writeFile(filePath, text) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, text);
}

function setMtime(filePath, timeMs) {
  const time = new Date(timeMs);
  fs.utimesSync(filePath, time, time);
}

function main() {
  const knowledgeBaseL0 = loadFrameworkFileIfExists("framework/knowledge_base/L0-M2-对话与引用原子模块.md");
  if (knowledgeBaseL0) {
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
  }

  const workbenchL2 = loadFrameworkFileIfExists("framework/knowledge_base/L2-M0-知识库工作台场景模块.md");
  const workbenchText = workbenchL2 ? workbenchL2.text : fallbackWorkbenchModuleText();
  const boundaryConfigRef = locate(workbenchText, "CHAT + CONTEXT + RETURN");
  const knowledgeProjectRelPath = discoverKnowledgeProjectRelPath();

  if (workbenchL2 && knowledgeProjectRelPath) {
    const boundaryConfigResult = resolveDefinitionTarget({
      repoRoot,
      filePath: workbenchL2.filePath,
      text: workbenchL2.text,
      line: boundaryConfigRef.line,
      character: boundaryConfigRef.character,
    });
    assert(boundaryConfigResult, "boundary config ref should resolve");
    assert(boundaryConfigResult.filePath.endsWith(knowledgeProjectRelPath));
    assert.strictEqual(targetLineText(boundaryConfigResult).trim(), "[exact.knowledge_base.chat]");
    assert(boundaryConfigResult.objectId.endsWith("::boundary::CHAT"));

    const boundaryHover = resolveHoverTarget({
      repoRoot,
      filePath: workbenchL2.filePath,
      text: workbenchL2.text,
      line: boundaryConfigRef.line,
      character: boundaryConfigRef.character,
    });
    assert(boundaryHover, "boundary hover should resolve");
    assert(boundaryHover.markdown.includes("Project Config"));
    assert(boundaryHover.markdown.includes(knowledgeProjectRelPath));
    assert(boundaryHover.markdown.includes("`[exact.knowledge_base.chat]`"));

    const boundaryRefs = resolveReferenceTargets({
      repoRoot,
      filePath: workbenchL2.filePath,
      text: workbenchL2.text,
      line: boundaryConfigRef.line,
      character: boundaryConfigRef.character,
    });
    assert(
      boundaryRefs.some((item) => item.filePath.endsWith(knowledgeProjectRelPath)),
      "boundary references should include the unified project config target"
    );
  }

  const tempRepoRoot = fs.mkdtempSync(path.join(os.tmpdir(), "shelf-framework-nav-"));
  try {
    const tempFrameworkPath = path.join(
      tempRepoRoot,
      "framework",
      "knowledge_base",
      "L2-M0-知识库工作台场景模块.md"
    );
    const tempProjectPath = path.join(tempRepoRoot, "projects", "demo", "project.toml");
    writeFile(tempFrameworkPath, workbenchText);
    writeFile(
      tempProjectPath,
      `
[project]
project_id = "demo"
runtime_scene = "test"
display_name = "Demo"
description = "Demo"
version = "0.0.0"

[framework]

[[framework.modules]]
role = "knowledge_base"
framework_file = "framework/knowledge_base/L2-M0-知识库工作台场景模块.md"
`
    );

    const noCanonicalDefinition = resolveDefinitionTarget({
      repoRoot: tempRepoRoot,
      filePath: tempFrameworkPath,
      text: workbenchText,
      line: boundaryConfigRef.line,
      character: boundaryConfigRef.character,
    });
    assert(noCanonicalDefinition, "boundary definition should still resolve locally without canonical");
    assert.strictEqual(noCanonicalDefinition.filePath, tempFrameworkPath);

    const noCanonicalHover = resolveHoverTarget({
      repoRoot: tempRepoRoot,
      filePath: tempFrameworkPath,
      text: workbenchText,
      line: boundaryConfigRef.line,
      character: boundaryConfigRef.character,
    });
    assert(noCanonicalHover, "boundary hover should still resolve without canonical");
    assert(!noCanonicalHover.markdown.includes("Project Config"));

    const noCanonicalRefs = resolveReferenceTargets({
      repoRoot: tempRepoRoot,
      filePath: tempFrameworkPath,
      text: workbenchText,
      line: boundaryConfigRef.line,
      character: boundaryConfigRef.character,
    });
    assert(
      !noCanonicalRefs.some((item) => item.filePath.endsWith("project.toml")),
      "project config references should require canonical instead of inferred fallback"
    );

    const staleCanonicalPath = path.join(tempRepoRoot, "projects", "demo", "generated", "canonical.json");
    writeFile(
      staleCanonicalPath,
      JSON.stringify(
        {
          framework: {
            modules: [
              {
                module_id: moduleIdFromFrameworkPath("framework/knowledge_base/L2-M0-知识库工作台场景模块.md"),
                boundaries: [
                  {
                    boundary_id: "CHAT",
                    config_projection: {
                      primary_exact_path: "exact.demo.chat",
                      related_exact_paths: ["exact.demo.chat"],
                      mapping_mode: "direct",
                    },
                  },
                ],
              },
            ],
          },
        },
        null,
        2
      )
    );
    writeFile(
      tempProjectPath,
      `
[project]
project_id = "demo"
runtime_scene = "test"
display_name = "Demo"
description = "Demo"
version = "0.0.0"

[framework]

[[framework.modules]]
role = "knowledge_base"
framework_file = "framework/knowledge_base/L2-M0-知识库工作台场景模块.md"

[exact.demo.chat]
value = "demo"
`
    );

    const baseTime = Date.now() - 60 * 1000;
    setMtime(staleCanonicalPath, baseTime);
    setMtime(tempProjectPath, baseTime + 5_000);
    setMtime(tempFrameworkPath, baseTime + 5_000);

    const staleDefinition = resolveDefinitionTarget({
      repoRoot: tempRepoRoot,
      filePath: tempFrameworkPath,
      text: workbenchText,
      line: boundaryConfigRef.line,
      character: boundaryConfigRef.character,
    });
    assert(staleDefinition, "stale canonical should still allow local boundary navigation");
    assert.strictEqual(staleDefinition.filePath, tempFrameworkPath);

    const staleHover = resolveHoverTarget({
      repoRoot: tempRepoRoot,
      filePath: tempFrameworkPath,
      text: workbenchText,
      line: boundaryConfigRef.line,
      character: boundaryConfigRef.character,
    });
    assert(staleHover, "stale canonical should still allow local hover");
    assert(!staleHover.markdown.includes("Project Config"));

    const staleRefs = resolveReferenceTargets({
      repoRoot: tempRepoRoot,
      filePath: tempFrameworkPath,
      text: workbenchText,
      line: boundaryConfigRef.line,
      character: boundaryConfigRef.character,
    });
    assert(
      !staleRefs.some((item) => item.filePath.endsWith("project.toml")),
      "stale canonical should not keep advertising stale project config targets"
    );
  } finally {
    fs.rmSync(tempRepoRoot, { recursive: true, force: true });
  }
}

main();
