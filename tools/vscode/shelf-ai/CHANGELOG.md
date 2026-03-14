# Changelog

## 0.1.3 - 2026-03-14

- Removed the repository-side `knowledge_base_basic` release payloads so public releases stay focused on the Shelf AI extension.
- Tightened the release policy to state that `knowledge_base_basic` is only a local validation sample and must not be published as a standalone versioned deliverable.
- Repackaged and reinstalled Shelf AI `0.1.3` so the shipped VSIX matches the validated workspace and release policy.

## 0.1.2 - 2026-03-14

- Synced the extension with the final export-driven runtime rewrite so its navigation and governance assumptions match the shipped repository mainline.
- Updated release-facing documentation to use the current canonical-derived governance artifact names consistently.
- Repackaged and reinstalled the VSIX against the current workspace so the publishable asset matches the validated repository state.

## 0.1.1 - 2026-03-14

- Fixed Shelf validation defaults to use the supported `validate_strict_mapping.py` commands instead of passing the removed `--json` flag.
- Added runtime command normalization so existing user settings with the stale `--json` flag still run successfully.
- Synced the extension README and tests with the supported validation command contract to prevent the mismatch from reappearing.

## 0.1.0 - 2026-03-14

- Raised the extension version to `0.1.0` to match the repository-wide architecture rewrite instead of treating it as another `0.0.x` patch.
- Kept the extension aligned with the rewritten mainline:
  `Framework Markdown -> Package Registry -> Project Config -> Code -> Evidence`.
- Kept project navigation, auto-materialization, generated-artifact guarding, and validation centered on `projects/*/project.toml` and canonical-derived views.
- Fixed configured-framework inference for the unified `[[selection.roots]]` layout by reading `framework_file` directly instead of assuming the removed `selection.root_modules` table.
- Updated repository docs to point at the current pipeline entrypoint and mark the rewrite execution ledger as complete so extension-facing guidance matches the shipped architecture.

## 0.0.48 - 2026-03-14

- Rebased Shelf AI on the rewritten repository architecture:
  `Framework Markdown -> Package Registry -> Project Config -> Code -> Evidence`.
- Switched project navigation from the removed dual-track config path to unified `projects/*/project.toml`.
- Switched generated-artifact guarding and auto-materialization to discovered `project.toml` files.
- Dropped extension-side dependence on the removed legacy mapping list and old scaffold-project commands.
- Clarified that `projects/*/generated/canonical_graph.json` is the sole machine truth and all governance views are derived from it.
