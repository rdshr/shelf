# Shelf AI (VSCode Extension)

## What It Does

- Opens the framework tree and workspace governance tree from the sidebar.
- Treats the repository mainline as:
  `Framework Markdown -> Package Registry -> Project Config -> Code -> Evidence`.
- Treats `projects/*/generated/canonical_graph.json` as the only machine truth.
- Treats `generation_manifest.json` / `governance_manifest.json` / `governance_tree.json` / reports as canonical-derived views.
- Supports framework-markdown navigation for `B/C/R/V`, boundaries, module refs, and rule refs.
- Maps framework boundaries back to `projects/*/project.toml` sections such as `[truth.chat]` and `[truth.surface]`.
- Auto-materializes affected projects when `framework/*.md` or `projects/*/project.toml` changes.
- Guards `projects/*/generated/*` and workspace tree artifacts from direct edits.
- Runs strict validation and optionally `mypy` from the extension.
- Supports publishing the active `framework_drafts/...` file into the formal `framework/...` tree.

## Install (Local)

1. Package and install the current source version:
   `bash tools/vscode/shelf-ai/install_local.sh`
2. If your VSCode CLI is not `code`, set it explicitly:
   `CODE_BIN=code-insiders bash tools/vscode/shelf-ai/install_local.sh`

## Commands

- `Shelf: Insert Framework Module Template`
- `Shelf: Install Git Hooks`
- `Shelf: Validate Registry Chain Now`
- `Shelf: Run Codegen Preflight`
- `Shelf: Publish Current Framework Draft`
- `Shelf: Show Validation Issues`
- `Shelf: Open Framework Tree`
- `Shelf: Refresh Framework Tree`
- `Shelf: Open Governance Tree`
- `Shelf: Refresh Governance Tree`

## Configuration

- `shelf.frameworkTreeJsonPath`
- `shelf.governanceTreeJsonPath`
- `shelf.guardMode = strict`

## Validation

Default commands:

- `uv run python scripts/validate_strict_mapping.py --check-changes --json`
- `uv run python scripts/validate_strict_mapping.py --json`
- `uv run python scripts/materialize_project.py`
- `uv run mypy`

`Shelf: Run Codegen Preflight` materializes all discovered `projects/*/project.toml` files, then runs full validation.

The `@framework` template entry is a repository-side hard authoring contract and must not be removed without an equally direct replacement.

## Tree Views

- Framework tree:
  `docs/hierarchy/shelf_framework_tree.json`
  `docs/hierarchy/shelf_framework_tree.html`
- Governance tree:
  `docs/hierarchy/shelf_governance_tree.json`
  `docs/hierarchy/shelf_governance_tree.html`

The framework tree is the authoring view.
The governance tree is the canonical-derived workspace evidence view.

## Project Config Navigation

Boundary jumps now target unified project config sections, for example:

- `[truth.surface]`
- `[truth.surface.copy]`
- `[truth.chat]`
- `[truth.chat.copy]`
- `[truth.library]`
- `[truth.preview]`
- `[truth.return]`

The extension no longer treats the removed dual-track config files as live authoring entrypoints.

## Release Notes

Public release notes live at:

- `tools/vscode/shelf-ai/CHANGELOG.md`
- `tools/vscode/shelf-ai/release-notes/0.0.48.md`
