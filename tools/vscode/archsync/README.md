# ArchSync (VSCode Extension)

## What It Does
- Adds an Activity Bar icon entry (`ArchSync`) for direct plugin access from the sidebar.
- Sidebar home view provides one-click actions: open tree, refresh tree, run validation, show issues.
- Opens framework tree structure HTML in Webview (`docs/hierarchy/shelf_framework_tree.html`).
- Refreshes framework tree artifacts by running the generator script.
- Supports node-to-source jump: click a node, then use `打开源文件` in detail panel to jump to the mapped markdown line.
- Supports `Go to Definition` / `Ctrl/Cmd+Click` inside framework markdown for `B/C/R/V`, boundary ids, `Lx.My`, `framework.Lx.My`, and bracketed module-rule refs like `frontend.L1.M4[R1,R3]`.
- Module refs such as `frontend.L1.M4` are treated as one hover/click target, jump straight to the target module's first `B*`, and show capability/base/rule summaries on hover.
- Hover also works for bracketed module rules such as `frontend.L1.M4[R1,R3]` and local `B/C/R/V` plus boundary symbols, showing the resolved definition content directly in place.
- Runs strict mapping validation automatically on startup.
- Runs strict mapping validation on save/create/rename/delete for relevant files.
- Runs strict mapping validation when watched files change outside VSCode and when window regains focus.
- Auto-disables validation for repositories that do not contain `specs/规范总纲与树形结构.md`.
- Shows validation issues in VSCode Problems panel.
- Status bar (`ArchSync issues`) is clickable and opens an issue picker for direct file/line jump.
- Disabled status text no longer shows `n/a`.
- Auto-fail notification provides buttons: `Open Problems` / `Open Log`.
- Provides manual commands for validation and framework tree viewing.

## Install (Local)
1. Install latest packaged VSIX:
   `bash tools/vscode/archsync/install_local.sh`
2. Reload VSCode window if the sidebar icon does not appear immediately.

## Public Distribution
- GitHub Packages is not a VSCode extension gallery, so VSCode cannot install this extension from a GitHub package registry entry.
- Public install channels for this extension are:
  - GitHub Releases: download the `.vsix` and use `Extensions: Install from VSIX...`
  - Open VSX: publish `rdshr.archsync` for VSCodium / compatible clients
  - Visual Studio Marketplace: publish `rdshr.archsync` for standard VSCode installs
- Release automation lives in `.github/workflows/publish-archsync.yml`.
- Tagging `archsync-vX.Y.Z` packages the current source, creates a GitHub Release, and attaches the generated `.vsix`.
- If repository secrets are configured, the same tag also publishes to:
  - `OPEN_VSX_TOKEN`
  - `VS_MARKETPLACE_TOKEN`
- One-time prerequisites outside this repo:
  - create publisher / namespace `rdshr`
  - create the corresponding publish tokens for each registry

## Install (Dev)
1. Open `tools/vscode/archsync` in VSCode.
2. Press `F5` to launch Extension Development Host.
3. Open the repository in the launched host window.

## Sidebar Icon
- Activity Bar icon uses custom product icon glyph `$(archsync-logo)` from `media/archsync-icons.woff2`.
- Current source mark lives in `media/archsync.svg`.
- Explicit rollback snapshot for the previous tomoe build is `media/archsync-backup-0.0.11-tomoe-triad.svg`.

## Commands
- `ArchSync: Open Framework Tree`
- `ArchSync: Refresh Framework Tree`
- `ArchSync: Validate Mapping Now`
- `ArchSync: Show Mapping Issues`

## Markdown Snippets
- `@framework`: insert neutral module template only.
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
- `FW024`: non-`L0` `B*` must inline adjacent lower-layer module refs in the main clause.
- `FW025`: local inline module refs must point to real adjacent lower-layer module files in the same framework directory.
- `FW026`: `L0` `B*` cannot reference local upstream modules inside the same framework.
- `FW027`: external foundation refs may only target another framework's `L0/L1` base modules.
- `FW028`: external foundation refs must point to real framework modules.
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
- Source defaults to framework files: `framework/<module>/Lx-Mn-*.md`.
- Legacy `Lx-*.md` (without `-Mn`) files are ignored.
- Preferred derivation: file-level module mode (`Lx-Mn-*.md` -> node `Lx.Mn`).
- In file-level mode, growth edges are parsed from base lines that directly reference upstream modules, for example:
  - ``- `B3` ...：L0.M0[R2,R3] + L0.M1[R2,R3]。来源：`...`。``
- Domain `L0` modules may also declare explicit external foundation refs, for example:
  - ``- `B1` ...：frontend.L1.M0[R1,R2]。来源：`...`。``
- Growth edges only allow adjacent layers (`Lx-1 -> Lx`).
- External foundation edges are limited to another framework's `L0/L1` modules and are intended only for structure carry-over, not for skipping the current framework's own layer growth.
- Strict validator rejects missing or invalid inline upstream refs for non-`L0` modules; standalone tree generation now aborts on warnings instead of silently skipping invalid growth edges.
- Module nodes jump to the module header; growth edges keep their source `B*` line for precise trace-back.
- Each node and growth edge carries `source_file` and `source_line` metadata for line-level jump.
