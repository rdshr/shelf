# Shelf AI (VSCode Extension)

## What It Does

- Opens the framework tree and workspace evidence tree from the sidebar.
- Treats the repository mainline as:
  `Framework -> Config -> Code -> Evidence`.
- Treats `projects/*/generated/canonical.json` as the only machine truth.
- Treats framework tree and evidence tree as canonical-derived views.
- Supports framework-markdown navigation for `B/C/R/V`, boundaries, module refs, and rule refs.
- Maps framework boundaries back to `projects/*/project.toml` sections such as `[exact.knowledge_base.chat]` and `[exact.frontend.surface]`.
- Auto-materializes affected projects when `framework/*.md` or `projects/*/project.toml` changes.
- Guards `projects/*/generated/*` from direct edits.
- Treats stale / missing / invalid canonical as non-authoritative: formal config jumps and the evidence tree wait for fresh canonical.
- Runs canonical validation and optionally `mypy` from the extension.
- Supports publishing the active `framework_drafts/...` file into the formal `framework/...` tree.

## Contract

- 插件后续设计与实现的正式契约文档：
  `tools/vscode/shelf-ai/插件设计与实现契约.md`
- 后续凡是插件相关代码变更，都应同步检查并在需要时更新该文档。

## Install (Local)

1. Package and install the current source version:
   `bash tools/vscode/shelf-ai/install_local.sh`
2. If your VSCode CLI is not `code`, set it explicitly:
   `CODE_BIN=code-insiders bash tools/vscode/shelf-ai/install_local.sh`

## Commands

- `Shelf: Insert Framework Module Template`
- `Shelf: Install Git Hooks`
- `Shelf: Validate Canonical Now`
- `Shelf: Run Codegen Preflight`
- `Shelf: Publish Current Framework Draft`
- `Shelf: Show Validation Issues`
- `Shelf: Open Framework Tree`
- `Shelf: Refresh Framework Tree`
- `Shelf: Open Evidence Tree`
- `Shelf: Refresh Evidence Tree`

## Configuration

- `shelf.guardMode = strict`

## Validation

Default commands:

- `uv run python scripts/validate_canonical.py --check-changes`
- `uv run python scripts/validate_canonical.py`
- `uv run python scripts/materialize_project.py`
- `uv run mypy`

`Shelf: Run Codegen Preflight` materializes all discovered `projects/*/project.toml` files, then runs full validation.

The `@framework` template entry is a repository-side hard authoring contract and must not be removed without an equally direct replacement.

## Tree Views

The framework tree is the authoring view.
The evidence tree is the canonical-derived workspace evidence view.
No persisted tree artifact is used for these views; both trees are runtime projections.
When canonical is stale, missing, or invalid, Shelf blocks the formal evidence tree until you materialize again.

## Project Config Navigation

Boundary jumps now target unified project config sections, for example:

- `[exact.frontend.surface]`
- `[exact.frontend.visual]`
- `[exact.knowledge_base.chat]`
- `[exact.knowledge_base.library]`
- `[exact.knowledge_base.preview]`
- `[exact.knowledge_base.return]`

The extension no longer treats the removed dual-track config files as live authoring entrypoints.

## Release Notes

Public release notes live at:

- `tools/vscode/shelf-ai/CHANGELOG.md`
- `tools/vscode/shelf-ai/release-notes/0.1.5.md`
