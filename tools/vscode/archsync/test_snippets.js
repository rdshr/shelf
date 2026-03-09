const assert = require("assert");
const fs = require("fs");
const path = require("path");
const frameworkCompletion = require("./framework_completion");

const extensionRoot = __dirname;

function readJson(relativePath) {
  return JSON.parse(fs.readFileSync(path.join(extensionRoot, relativePath), "utf8"));
}

function readText(relativePath) {
  return fs.readFileSync(path.join(extensionRoot, relativePath), "utf8");
}

function main() {
  const packageJson = readJson("package.json");
  const snippetJson = readJson(path.join("snippets", "markdown.code-snippets"));
  const extensionSource = readText("extension.js");
  const readme = readText("README.md");

  const snippetContribution = (packageJson.contributes?.snippets || []).find(
    (item) => item.language === "markdown" && item.path === "./snippets/markdown.code-snippets"
  );
  assert(snippetContribution, "package.json must contribute markdown snippets");
  assert(
    (packageJson.files || []).includes("framework_completion.js"),
    "package.json must package framework_completion.js"
  );

  const commandContribution = (packageJson.contributes?.commands || []).find(
    (item) => item.command === "archSync.insertFrameworkModuleTemplate"
  );
  assert(commandContribution, "package.json must contribute the framework template insert command");

  assert(
    (packageJson.activationEvents || []).includes("onCommand:archSync.insertFrameworkModuleTemplate"),
    "package.json must activate on the framework template insert command"
  );

  const frameworkSnippet = snippetJson["@framework Module Template"];
  assert(frameworkSnippet, "markdown snippets must keep the @framework module template");
  assert.strictEqual(frameworkSnippet.prefix, "@framework");
  assert(Array.isArray(frameworkSnippet.body), "@framework snippet must have a body array");
  assert(frameworkSnippet.body.includes("@framework"), "@framework snippet body must include the directive line");
  assert(
    frameworkSnippet.body.includes("## 1. 能力声明（Capability Statement）"),
    "@framework snippet must include capability statement section"
  );
  assert(
    frameworkSnippet.body.includes("## 2. 边界定义（Boundary / 参数）"),
    "@framework snippet must include boundary section"
  );
  assert(
    frameworkSnippet.body.includes("## 3. 最小可行基（Minimum Viable Bases）"),
    "@framework snippet must include base section"
  );
  assert(
    frameworkSnippet.body.includes("## 4. 基组合原则（Base Combination Principles）"),
    "@framework snippet must include rule section"
  );
  assert(
    frameworkSnippet.body.includes("## 5. 验证（Verification）"),
    "@framework snippet must include verification section"
  );

  assert(
    /registerCommand\s*\(\s*"archSync\.insertFrameworkModuleTemplate"/.test(extensionSource),
    "extension.js must register the framework template insert command"
  );
  assert(
    /registerCompletionItemProvider\s*\(/.test(extensionSource),
    "extension.js must register a markdown completion provider"
  );
  assert(
    readme.includes("ArchSync: Insert Framework Module Template"),
    "README must document the framework template insert command"
  );
  assert(
    readme.includes("The `@framework` template entry is a repository-side hard authoring contract"),
    "README must document the non-removable @framework authoring contract"
  );

  const atEntries = frameworkCompletion.getFrameworkCompletionEntries("@", "@", false);
  assert(
    atEntries.some((entry) => entry.label === "@framework 标准模块模板"),
    "@ completion must include the full framework template"
  );
  assert(
    atEntries.some((entry) => entry.label === "@framework"),
    "@ completion must include the plain @framework directive"
  );

  const sectionEntries = frameworkCompletion.getFrameworkCompletionEntries("## ", "", true);
  assert(
    sectionEntries.some((entry) => entry.label.includes("最小可行基")),
    "section completion must include the Minimum Viable Bases heading"
  );

  const baseEntries = frameworkCompletion.getFrameworkCompletionEntries("- `B", "B", true);
  assert(
    baseEntries.some((entry) => entry.label === "B 条目"),
    "base completion must include the B entry template"
  );

  const ruleChildEntries = frameworkCompletion.getFrameworkCompletionEntries("  - `R1.", "R1.", true);
  assert(
    ruleChildEntries.some((entry) => entry.label === "R*.1 参与基"),
    "rule child completion must include R*.1"
  );
  assert(
    ruleChildEntries.some((entry) => entry.label === "R*.4 边界绑定"),
    "rule child completion must include R*.4"
  );
}

main();
