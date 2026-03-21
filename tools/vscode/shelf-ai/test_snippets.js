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
  assert(
    (packageJson.files || []).includes("guarding.js"),
    "package.json must package guarding.js"
  );
  assert(
    (packageJson.files || []).includes("local_settings.js"),
    "package.json must package local_settings.js"
  );

  const commandContribution = (packageJson.contributes?.commands || []).find(
    (item) => item.command === "shelf.insertFrameworkModuleTemplate"
  );
  assert(commandContribution, "package.json must contribute the framework template insert command");
  const installHooksCommand = (packageJson.contributes?.commands || []).find(
    (item) => item.command === "shelf.installGitHooks"
  );
  assert(installHooksCommand, "package.json must contribute the git hooks install command");
  const openFrameworkTreeCommand = (packageJson.contributes?.commands || []).find(
    (item) => item.command === "shelf.openFrameworkTree"
  );
  assert(openFrameworkTreeCommand, "package.json must contribute the framework tree open command");
  const openEvidenceTreeCommand = (packageJson.contributes?.commands || []).find(
    (item) => item.command === "shelf.openEvidenceTree"
  );
  assert(openEvidenceTreeCommand, "package.json must contribute the evidence tree open command");

  assert(
    (packageJson.activationEvents || []).includes("onCommand:shelf.insertFrameworkModuleTemplate"),
    "package.json must activate on the framework template insert command"
  );
  assert(
    (packageJson.activationEvents || []).includes("onCommand:shelf.installGitHooks"),
    "package.json must activate on the git hooks install command"
  );
  assert(
    (packageJson.activationEvents || []).includes("onCommand:shelf.openFrameworkTree"),
    "package.json must activate on the framework tree open command"
  );
  assert(
    (packageJson.activationEvents || []).includes("onCommand:shelf.openEvidenceTree"),
    "package.json must activate on the evidence tree open command"
  );

  const configuration = packageJson.contributes?.configuration?.properties || {};
  for (const key of [
    "shelf.guardMode",
    "shelf.autoMaterialize",
    "shelf.runMypyOnPythonChanges",
    "shelf.protectGeneratedFiles",
    "shelf.promptInstallGitHooks",
    "shelf.materializeCommand",
    "shelf.typeCheckCommand",
  ]) {
    assert(Object.prototype.hasOwnProperty.call(configuration, key), `package.json must expose ${key}`);
  }
  assert.strictEqual(
    configuration["shelf.changeValidationCommand"]?.default,
    "uv run python scripts/validate_canonical.py --check-changes",
    "package.json must default shelf.changeValidationCommand to the supported canonical validation command"
  );
  assert.strictEqual(
    configuration["shelf.fullValidationCommand"]?.default,
    "uv run python scripts/validate_canonical.py",
    "package.json must default shelf.fullValidationCommand to the supported canonical validation command"
  );
  assert(
    configuration["shelf.frameworkLintEnabled"]?.default === true,
    "package.json must enable framework realtime lint by default"
  );
  assert(
    configuration["shelf.frameworkLintOnType"]?.default === true,
    "package.json must run framework realtime lint while typing by default"
  );
  assert(
    configuration["shelf.frameworkLintDebounceMs"]?.default === 300,
    "package.json must expose framework lint debounce configuration"
  );
  assert(
    configuration["shelf.frameworkAutoCompleteEnabled"]?.default === true,
    "package.json must enable framework auto completion by default"
  );
  assert(
    configuration["shelf.frameworkAutoTriggerSuggest"]?.default === true,
    "package.json must auto trigger framework completion by default"
  );
  assert(
    configuration["shelf.frameworkQuickFixEnabled"]?.default === true,
    "package.json must enable framework lint quick fixes by default"
  );
  assert(
    !Object.prototype.hasOwnProperty.call(configuration, "shelf.intentGateEnforcementMode"),
    "package.json should not expose save-time intent gate enforcement mode"
  );
  assert(
    !Object.prototype.hasOwnProperty.call(configuration, "shelf.intentGateGuardedPathPrefixes"),
    "package.json should not expose save-time guarded path prefixes"
  );
  assert(
    !Object.prototype.hasOwnProperty.call(configuration, "shelf.intentGateIgnoredPathPrefixes"),
    "package.json should not expose save-time ignored path prefixes"
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
    frameworkSnippet.body.includes("## 2. 边界定义（Boundary / Parameter 参数）"),
    "@framework snippet must include boundary/parameter section"
  );
  assert(
    frameworkSnippet.body.includes("## 3. 最小结构基（Minimal Structural Bases）"),
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
    /registerCommand\s*\(\s*"shelf\.insertFrameworkModuleTemplate"/.test(extensionSource),
    "extension.js must register the framework template insert command"
  );
  assert(
    /registerCommand\s*\(\s*"shelf\.installGitHooks"/.test(extensionSource),
    "extension.js must register the git hooks install command"
  );
  assert(
    /registerCommand\s*\(\s*"shelf\.openFrameworkTree"/.test(extensionSource),
    "extension.js must register the framework tree open command"
  );
  assert(
    /registerCommand\s*\(\s*"shelf\.openEvidenceTree"/.test(extensionSource),
    "extension.js must register the evidence tree open command"
  );
  assert(
    /registerCompletionItemProvider\s*\(/.test(extensionSource),
    "extension.js must register a markdown completion provider"
  );
  assert(
    /registerCodeActionsProvider\s*\(/.test(extensionSource),
    "extension.js must register framework markdown quick-fix provider"
  );
  assert(
    extensionSource.includes("editor.action.triggerSuggest"),
    "extension.js must trigger framework suggestion popup while typing"
  );
  assert(
    /onDidChangeTextDocument\s*\(/.test(extensionSource),
    "extension.js must clear stale shelf diagnostics when watched documents are edited"
  );
  assert(
    extensionSource.includes('$(close) Shelf 失败'),
    "extension.js must expose a visible cross icon for failing Shelf status"
  );
  assert(
    readme.includes("Shelf: Insert Framework Module Template"),
    "README must document the framework template insert command"
  );
  assert(
    readme.includes("Shelf: Install Git Hooks"),
    "README must document the git hooks install command"
  );
  assert(
    readme.includes("Shelf: Open Framework Tree"),
    "README must document the framework tree open command"
  );
  assert(
    readme.includes("Shelf: Refresh Framework Tree"),
    "README must document the framework tree refresh command"
  );
  assert(
    readme.includes("Shelf: Open Evidence Tree"),
    "README must document the evidence tree open command"
  );
  assert(
    readme.includes("The `@framework` template entry is a repository-side hard authoring contract"),
    "README must document the non-removable @framework authoring contract"
  );
  assert(
    readme.includes("shelf.guardMode = strict"),
    "README must document strict guard mode"
  );
  assert(
    readme.includes(".shelf/settings.jsonc"),
    "README must document the local .shelf settings entrypoint"
  );
  assert(
    readme.includes("VSCode `shelf.*` setting has highest priority"),
    "README must document local settings precedence"
  );
  assert(
    readme.includes("uv run python scripts/validate_canonical.py --check-changes"),
    "README must document the supported save-triggered canonical validation command"
  );
  assert(
    readme.includes("uv run python scripts/validate_canonical.py"),
    "README must document the supported full canonical validation command"
  );
  assert(
    !readme.includes("validate_canonical.py --json"),
    "README must not document the optional --json canonical flag as the default command"
  );
  assert(
    readme.includes("Treats stale / missing / invalid canonical as non-authoritative"),
    "README must document strict canonical freshness behavior"
  );
  assert(
    readme.includes("Shelf blocks the formal evidence tree until you materialize again"),
    "README must explain how the evidence tree behaves when canonical is stale"
  );
  assert(
    readme.includes("No persisted tree artifact"),
    "README must state tree views are runtime projections without persisted artifacts"
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
    sectionEntries.some((entry) => entry.label.includes("最小结构基")),
    "section completion must include the Minimal Structural Bases heading"
  );

  const authoringSample = [
    "# 模块:Module",
    "",
    "@framework",
    "",
    "## 1. 能力声明（Capability Statement）",
    "",
    "- `C1` 现有能力：描述。",
    "- `N1` 非职责声明：描述。",
    "",
    "## 4. 基组合原则（Base Combination Principles）",
    "",
    "- `R7` 现有规则",
    "  - `R7.1` 参与基：`B1 + B2`。",
  ].join("\n");

  const capabilityEntries = frameworkCompletion.getFrameworkCompletionEntries(
    "- ",
    "",
    true,
    {
      documentText: authoringSample,
      lineNumber: 6,
    }
  );
  assert(
    capabilityEntries.some((entry) => entry.label === "C 条目"),
    "capability section completion must include C entry"
  );
  assert(
    !capabilityEntries.some((entry) => entry.label === "参数条目"),
    "capability section completion should not prioritize parameter entry"
  );
  const cEntry = capabilityEntries.find((entry) => entry.label === "C 条目");
  assert(cEntry?.insertText.includes("C${1:2}"), "C completion should infer next index from current document");
  assert(
    capabilityEntries.some((entry) => entry.label === "N 条目"),
    "capability section completion must include non-responsibility entry"
  );

  const baseEntries = frameworkCompletion.getFrameworkCompletionEntries("- `B", "B", true, {
    documentText: authoringSample,
    lineNumber: 6,
  });
  assert(
    baseEntries.some((entry) => entry.label === "B 条目"),
    "base completion must include the B entry template"
  );

  const ruleChildEntries = frameworkCompletion.getFrameworkCompletionEntries("  - `R7.", "R7.", true, {
    documentText: authoringSample,
    lineNumber: 12,
  });
  assert(
    ruleChildEntries.some((entry) => entry.label === "R*.1 参与基"),
    "rule child completion must include R*.1"
  );
  assert(
    ruleChildEntries.some((entry) => entry.label === "R*.4 参数绑定"),
    "rule child completion must include R*.4"
  );
  const ruleChildEntry = ruleChildEntries.find((entry) => entry.label === "R*.1 参与基");
  assert(
    ruleChildEntry?.insertText.includes("R${1:7}.1"),
    "rule child completion should infer nearest rule number"
  );

  const parameterAuthoringSample = [
    "# 模块:Module",
    "",
    "@framework",
    "",
    "## 1. 能力声明（Capability Statement）",
    "",
    "- `C1` 现有能力：描述。",
    "",
    "## 2. 边界定义（Boundary / Parameter 参数）",
    "",
    "- `P1` 现有参数：描述。来源：`C1`。",
    "",
  ].join("\n");
  const parameterDashAutoExpansion = frameworkCompletion.getFrameworkDashAutoExpansion(
    "-",
    true,
    {
      documentText: parameterAuthoringSample,
      lineNumber: 11,
    }
  );
  assert(
    typeof parameterDashAutoExpansion?.insertText === "string",
    "parameter section dash should auto-expand to parameter entry"
  );
  assert(
    parameterDashAutoExpansion.insertText.includes("${1:P2}"),
    "parameter dash auto-expansion should infer the next P index"
  );
  const nonParameterDashAutoExpansion = frameworkCompletion.getFrameworkDashAutoExpansion(
    "-",
    true,
    {
      documentText: authoringSample,
      lineNumber: 6,
    }
  );
  assert.strictEqual(
    nonParameterDashAutoExpansion,
    null,
    "dash auto-expansion should only apply inside the parameter section"
  );
}

main();
