# Shelf AI (VSCode Extension)

## What It Does
- Adds an Activity Bar icon entry (`Shelf AI`) for direct plugin access from the sidebar.
- Sidebar home view provides one-click actions for the framework tree, governance tree, validation, and issue review.
- Treats the current governance scope as mainline-first: Shelf strongly guards the structural path that carries `Framework -> Product Spec -> Implementation Config -> Code -> Evidence` plus the reverse validation path back to upstream structure.
- Makes the current coverage boundary explicit instead of overstating it: runtime assembly, compiled contracts/specs, evidence, and governance compare are strongly covered; lower-level renderer/style/script details can still be only partially governed.
- Opens the framework tree structure HTML in Webview by default (`docs/hierarchy/shelf_framework_tree.html`).
- Keeps the workspace governance tree as a separate, secondary view for strict-guard closure and code/evidence trace inspection (`docs/hierarchy/shelf_governance_tree.html`).
- Refreshes framework-tree and governance-tree artifacts with separate generator commands.
- Supports node-to-source jump: click a node, then use `打开源文件` in detail panel to jump to the mapped markdown line.
- Supports `Go to Definition` / `Ctrl/Cmd+Click` inside framework markdown for `B/C/R/V`, boundary ids, `Lx.My`, `framework.Lx.My`, and bracketed module-rule refs like `frontend.L1.M2[R1,R2]`.
- Boundary navigation is not limited to explicitly exposed top-level sections. Direct boundaries such as `CHAT` / `SURFACE` and derived boundaries such as `CITATION` / `TURN` / `SCOPE` can jump to the owning or related `projects/*/product_spec.toml` section, and when a project uses split specs they now land directly in `projects/*/product_spec/*.toml`.
- When a project has already been materialized, boundary navigation now prefers the generated governance manifest for project-specific section ownership instead of relying on extension-side hardcoded framework guesses.
- Framework drafts under `framework_drafts/` reuse the same definition / hover / reference navigation model as published framework docs, but they stay outside strict project materialization until published.
- Module refs such as `frontend.L1.M2` are treated as one hover/click target, jump straight to the target module's first `B*`, and show capability/base/rule summaries on hover.
- Hover also works for bracketed module rules such as `frontend.L1.M2[R1,R2]` and local `B/C/R/V` plus boundary symbols, showing the resolved definition content directly in place; boundary hovers also show the mapped config file, primary owning section, related sections, and inferred ownership note when applicable.
- `Find All References` / `Shift+F12` is implemented for navigable framework symbols, so boundary tokens can return the current usage, framework definition, and mapped config target in one place.
- Validation trigger mode is configurable: `manual`, `save`, or `all`.
- Manual validation can recover from a stale in-flight guard task; if a previous validation command has been hanging for too long, `Shelf: Validate Mapping Now` restarts it instead of waiting forever.
- Adds `Shelf: Run Codegen Preflight` to materialize and fully validate the current workspace before asking AI to generate code.
- Adds `Shelf: Scaffold Framework-Driven Project` to create a formal `product_spec.toml` / `product_spec/*.toml` / `implementation_config.toml` authoring skeleton from a registered template.
- Adds `Shelf: Publish Current Framework Draft` to move the active `framework_drafts/...` file into the formal `framework/...` tree.
- Auto-materializes affected `projects/*` when `framework/*.md`, `product_spec.toml`, or `implementation_config.toml` changes.
- The validation chain includes `配置即功能` checks: effective `implementation_config.toml` fields must drive downstream compiled behavior instead of becoming dead selectors.
- Optionally runs `mypy` after relevant Python changes under `src/`, `scripts/`, or `tests/`.
- Guards `projects/*/generated/*` from direct edits; `strict` mode restores them by re-materializing the owning project.
- Checks whether repository `.githooks` are enabled and offers a one-click install command when missing.
- Auto-disables validation for repositories that do not contain `specs/规范总纲与树形结构.md`.
- Shows validation issues in VSCode Problems panel.
- Status bar (`Shelf AI issues`) is clickable and opens an issue picker for direct file/line jump.
- Disabled status text no longer shows `n/a`.
- Auto-fail notification provides buttons: `Open Problems` / `Open Log`.
- Provides manual commands for validation, framework-tree viewing, and governance-tree viewing.
- Provides a direct fallback command to insert the standard `@framework` module template even when editor snippet suggestions are not showing.
- Uses the VSCode output channel for recent command output only; it does not create persistent log files in the repository.

## Install (Local)
1. Package the current source version and install it into local VSCode:
   `bash tools/vscode/shelf-ai/install_local.sh`
2. The script reads `package.json`, rebuilds `releases/shelf-ai-<version>.vsix`, force-installs it, and verifies the installed version.
3. If your VSCode CLI is not `code`, set it explicitly:
   `CODE_BIN=code-insiders bash tools/vscode/shelf-ai/install_local.sh`
4. Reload VSCode window if the sidebar icon does not appear immediately.
5. If you are using WSL, run the script from WSL and make sure the target VS Code window is attached to the same WSL workspace.

## Public Distribution
- GitHub Packages is not a VSCode extension gallery, so VSCode cannot install this extension from a GitHub package registry entry.
- Public install channels for this extension are:
  - GitHub Releases: download the `.vsix` and use `Extensions: Install from VSIX...`
  - Open VSX: publish `rdshr.shelf-ai` for VSCodium / compatible clients
  - Visual Studio Marketplace: publish `rdshr.shelf-ai` for standard VSCode installs
- Release automation lives in `.github/workflows/publish-shelf-ai.yml`.
- Tagging `shelf-ai-vX.Y.Z` packages the current source, creates a GitHub Release, and attaches the generated `.vsix`.
- Public tag releases must include a curated bilingual notes file at `tools/vscode/shelf-ai/release-notes/<version>.md`; the workflow uses that file as the GitHub Release body.
- If repository secrets are configured, the same tag also publishes to:
  - `OPEN_VSX_TOKEN`
  - `VS_MARKETPLACE_TOKEN`
- One-time prerequisites outside this repo:
  - create publisher / namespace `rdshr`
  - create the corresponding publish tokens for each registry

## Install (Dev)
1. Open `tools/vscode/shelf-ai` in VSCode.
2. Press `F5` to launch Extension Development Host.
3. Open the repository in the launched host window.

## Sidebar Icon
- Activity Bar icon uses custom product icon glyph `$(shelf-logo)` from `media/shelf-ai-icons.woff2`.
- Current source mark lives in `media/shelf-ai.svg`.
- Explicit rollback snapshot for the previous tomoe build is `media/shelf-ai-backup-0.0.11-tomoe-triad.svg`.

## Commands
- `Shelf: Insert Framework Module Template`
- `Shelf: Install Git Hooks`
- `Shelf: Open Framework Tree`
- `Shelf: Refresh Framework Tree`
- `Shelf: Open Governance Tree`
- `Shelf: Refresh Governance Tree`
- `Shelf: Validate Mapping Now`
- `Shelf: Run Codegen Preflight`
- `Shelf: Scaffold Framework-Driven Project`
- `Shelf: Publish Current Framework Draft`
- `Shelf: Show Mapping Issues`

## Markdown Snippets
- `@framework`: insert the standard framework module template.
- The `@framework` template entry is a repository-side hard authoring contract and must not be removed without an equally direct, default-available replacement.
- If editor snippet suggestions are not cooperating, use `Shelf: Insert Framework Module Template` as the explicit fallback entry.
- Framework-markdown completion also covers the fixed skeleton directly: `@framework`、五个主章节标题、`C/P/B/R/V` 条目，以及 `R*.1~R*.4` 子项。
- `B`: insert one `B*` line format only.
- `R`: insert one `R*` + `R*.*` rule block format only.

## Framework Rule Codes
- `FW002`: `@framework` must be plain directive without arguments.
- `FW003`: title must be bilingual `中文名:EnglishName`.
- `FW010`: identifiers in one framework file must be unique.
- `FW011`: capability/base/rule/verification ids must match required numbering patterns.
- `FW020`: every `B*` must include source expression.
- `FW021`: `B*` source expression must be parseable and references must exist.
- `FW022`: `B*` source must include at least one `C*` and one parameter id.
- `FW023`: `B*` must inline upstream module refs (`Lx.My[...]` or `framework.Lx.My[...]`) before source expression; `上游模块：...` is forbidden.
- `FW024`: non-root `B*` must inline at least one local upstream module ref in the main clause.
- `FW025`: local inline module refs must point to real lower local layers in the same framework; adjacency is no longer the hard rule.
- `FW026`: the current framework root layer cannot reference local upstream modules inside the same framework.
- `FW028`: external inline module refs must point to real framework modules.
- `FW029`: framework inline module refs must remain acyclic.
- `FW030`: every boundary parameter item (for example `N/P/S/O/A/T/SF`) must include source.
- `FW031`: boundary source must reference at least one `C*`, and all references must exist.
- `FW040`: `R*` / `R*.*` numbering must be valid.
- `FW041`: each `R*` must include required fields (`参与基` / `组合方式` / `输出能力` / `边界绑定`).
- `FW050`: each `输出能力` line must reference at least one defined `C*`.
- `FW060`: any new symbol in rules must be declared via `输出结构` in same/upstream rule.

## Configuration
- `shelf.enableOnSave`
- `shelf.validationTriggerMode`
- `shelf.notifyOnAutoFail`
- `shelf.guardMode`
- `shelf.autoMaterialize`
- `shelf.runMypyOnPythonChanges`
- `shelf.protectGeneratedFiles`
- `shelf.promptInstallGitHooks`
- `shelf.changeValidationCommand`
- `shelf.fullValidationCommand`
- `shelf.frameworkTreeJsonPath`
- `shelf.frameworkTreeHtmlPath`
- `shelf.frameworkTreeGenerateCommand`
- `shelf.governanceTreeJsonPath`
- `shelf.governanceTreeHtmlPath`
- `shelf.governanceTreeGenerateCommand`
- `shelf.materializeCommand`
- `shelf.typeCheckCommand`

Default commands use the repository validator:
- `uv run python scripts/validate_strict_mapping.py --check-changes --json`
- `uv run python scripts/validate_strict_mapping.py --json`
- `uv run python scripts/materialize_project.py`
- `uv run mypy`

Guard behavior:
- `shelf.validationTriggerMode = manual`: only explicit commands run validation.
- `shelf.validationTriggerMode = save`: only saving watched files runs validation automatically.
- `shelf.validationTriggerMode = all`: save plus watched workspace events keep validation hot.
- `shelf.guardMode = normal`: report direct edits under `projects/*/generated/*`, but do not overwrite the file.
- `shelf.guardMode = strict`: re-run materialization for the owning project and treat restore failure as a hard guard issue.
- `shelf.autoMaterialize = true`: when upstream framework or project truth files change, Shelf appends `--project <product_spec.toml>` and materializes the affected projects automatically.
- `shelf.protectGeneratedFiles = true`: direct edits under generated artifacts are always surfaced; `strict` mode upgrades this to automatic restore, including both `shelf_framework_tree.*` and `shelf_governance_tree.*`.
- `shelf.runMypyOnPythonChanges = true`: Python-only checks are scoped to relevant source changes so routine Markdown work does not trigger mypy.
- `shelf.promptInstallGitHooks = true`: prompt once per session if `core.hooksPath` is not set to the repository `.githooks`.

Default framework tree generation command:
- `uv run python scripts/generate_framework_tree_hierarchy.py --output-json docs/hierarchy/shelf_framework_tree.json --output-html docs/hierarchy/shelf_framework_tree.html`

Default governance tree generation command:
- `uv run python scripts/generate_governance_tree_hierarchy.py --output-json docs/hierarchy/shelf_governance_tree.json --output-html docs/hierarchy/shelf_governance_tree.html`

Tree generation behavior:
- Framework tree is the default reading view. It focuses on `framework/*.md` and their cross-module structure without mixing in code nodes.
- Framework tree HTML is regenerated from `docs/hierarchy/shelf_framework_tree.json`.
- Workspace governance tree combines:
  - standards tree from `mapping/mapping_registry.json`
  - project governance trees derived from `Framework -> Product Spec -> Implementation Config -> Code -> Evidence`
- Governance tree HTML is regenerated from `docs/hierarchy/shelf_governance_tree.json`.
- Interaction contract for the generated framework tree and governance tree:
  - Left-drag on background scrolls / pans the whole graph canvas.
  - Clicking a node or edge must keep selection and relationship-detail inspection working.
  - `Ctrl/⌘ + click` on a node or edge must keep source-file jump working.
  - These interactions are repository-side regression constraints and are guarded by the hierarchy HTML generator tests.
- Governance tree nodes carry `source_file` and `source_line` metadata for line-level jump.
- Shelf sidebar opens the framework tree by default, while still showing the most recent touched / affected governance node closure after each validation run.
