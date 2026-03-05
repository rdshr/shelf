# ArchSync (VSCode Extension)

## What It Does
- Opens framework tree structure HTML in Webview (`docs/hierarchy/shelf_framework_tree.html`).
- Refreshes framework tree artifacts by running the generator script.
- Generates framework layer scaffold markdown via command palette.
- Auto-expands `@framework` directive on save for `framework/**` markdown files.
- Runs strict mapping validation automatically on startup.
- Runs strict mapping validation on save/create/rename/delete for relevant files.
- Runs strict mapping validation when watched files change outside VSCode and when window regains focus.
- Auto-disables validation for repositories that do not contain `specs/规范总纲与树形结构.md`.
- Shows validation issues in VSCode Problems panel.
- Status bar (`ArchSync issues`) is clickable and opens an issue picker for direct file/line jump.
- Auto-fail notification provides buttons: `Open Problems` / `Open Log`.
- Provides manual commands for validation and framework tree viewing.

## Install (Local)
1. Open `tools/vscode/archsync` in VSCode.
2. Press `F5` to launch Extension Development Host.
3. Open the repository in the launched host window.

## Commands
- `ArchSync: Open Framework Tree`
- `ArchSync: Refresh Framework Tree`
- `ArchSync: Validate Mapping Now`
- `ArchSync: Show Mapping Issues`
- `ArchSync: Generate Framework Scaffold`

## Markdown Snippets
- `@framework`: insert empty framework scaffold format only.
- `B`: insert one `B*` line format only.
- `R`: insert one `R*` + `R*.*` nested rule block format only.

## Auto Expand `@framework`
- Default enabled: `archSync.autoExpandFrameworkDirective = true`
- Scope: markdown files under `framework/**`
- Behavior: if file contains a line `@framework`, save will replace full file content with scaffold format.
- Directive format:
  - `@framework`
  - Any extra parameters are invalid.

## Framework Rule Codes
- `FW002`: `@framework` must be plain directive without arguments.
- `FW003`: title must be bilingual `中文名:EnglishName`.
- `FW010`: identifiers in one framework file must be unique.
- `FW011`: capability/base/rule/verification ids must match required numbering patterns.
- `FW020`: every `B*` must include source expression.
- `FW021`: `B*` source expression must be parseable and references must exist.
- `FW022`: `B*` source must include at least one `C*` and one parameter id.
- `FW030`: every boundary parameter item (for example `N/P/S/O/A/T/SF`) must include source.
- `FW031`: boundary source must reference at least one `C*`, and all references must exist.
- `FW040`: `R*` / `R*.*` numbering must be valid.
- `FW041`: each `R*` must include required fields (`参与基` / `组合方式` / `输出能力` / `边界绑定`).
- `FW050`: each `输出能力` line must reference at least one defined `C*`.
- `FW060`: any new symbol in rules must be declared via `输出结构` in same/upstream rule.

## Configuration
- `archSync.enableOnSave`
- `archSync.notifyOnAutoFail`
- `archSync.changeValidationCommand`
- `archSync.fullValidationCommand`
- `archSync.frameworkTreeHtmlPath`
- `archSync.frameworkTreeGenerateCommand`

Default commands use the repository validator:
- `uv run python scripts/validate_strict_mapping.py --check-changes --json`
- `uv run python scripts/validate_strict_mapping.py --json`

Default framework tree generation command:
- `uv run python scripts/generate_framework_tree_hierarchy.py --source framework --framework-dir framework --output-json docs/hierarchy/shelf_framework_tree.json --output-html docs/hierarchy/shelf_framework_tree.html`

Tree generation behavior:
- Source defaults to framework files: `framework/<module>/Lx-*.md`.
- Only adjacent-level edges are generated: `Lx -> L(x+1)`.
- Cross-level jump edges are never generated.
