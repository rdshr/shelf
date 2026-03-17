# Changelog

## 0.1.9 - 2026-03-17

- Removed redundant `boundary_id` / `mapping_mode` mirror keys from `projects/knowledge_base_basic/project.toml` so project config no longer repeats boundary identity already derived from framework and canonical.
- Stripped those mirror keys from compiled config boundary payloads to keep `communication_export` / `exact_export` free of dead projection metadata.
- Revalidated the repository, regenerated canonical output, and repackaged Shelf AI `0.1.9` so the published VSIX matches the current validated workspace.

## 0.1.8 - 2026-03-16

- Fixed the GitHub `Publish Shelf AI` workflow so the runner now installs extension dependencies before invoking `vsce package`, matching the validated local packaging environment.
- Shipped this patch release as a release-pipeline repair only: no new Shelf AI features, but the public tag/release path now produces the expected `.vsix` asset again.
- Repackaged and reinstalled the local VSIX as `0.1.8` after verifying the workflow fix and existing plugin test/build checks.

## 0.1.7 - 2026-03-16

- Rebuilt Shelf AI tree views into a dedicated runtime webview subsystem with explicit model/layout/render/bridge layering instead of a monolithic extension-side renderer.
- Restored the framework tree to the denser round-node visual baseline with layer-fixed auto layout, hover metadata, edge inspection, and collapsible inspector behavior.
- Added settings-first runtime tuning for framework tree spacing, tree zoom and inspector sizing, plus validation timeout/debounce/suppression thresholds, then repackaged and reinstalled the local VSIX.

## 0.1.6 - 2026-03-15

- Tightened framework-to-config navigation so boundary jumps now resolve from canonical-backed framework exports instead of extension-side inferred fallback tables.
- Added stable class/source identities across the four-layer canonical output and expanded base bindings beyond module ownership into owner/slot/symbol traces.
- Revalidated the repository, regenerated evidence artifacts, and rebuilt the local VSIX so the installed extension matches the current workspace.

## 0.1.5 - 2026-03-15

- Restored the interactive framework and evidence graph canvas so the generated tree views are no longer reduced to plain HTML lists.
- Reintroduced the shared hierarchy renderer and model layer that powers zoom, drag, hover, and side-panel inspection for tree outputs.
- Updated release-facing CI, repository templates, and the local `pre-push` hook to validate against the canonical pipeline instead of the removed strict-mapping commands.

## 0.1.4 - 2026-03-14

- Rebuilt the extension against the final four-layer runtime and canonical output.
- Switched release-facing validation guidance to `scripts/validate_canonical.py`.
- Revalidated the repository end-to-end and rebuilt the VSIX from the validated workspace.

## 0.1.3 - 2026-03-14

- Removed the repository-side `knowledge_base_basic` release payloads so public releases stay focused on the Shelf AI extension.
- Tightened the release policy to state that `knowledge_base_basic` is only a local validation sample and must not be published as a standalone versioned deliverable.
- Repackaged and reinstalled Shelf AI `0.1.3` so the shipped VSIX matches the validated workspace and release policy.

## 0.1.2 - 2026-03-14

- Synced the extension with the four-layer runtime and canonical-derived tree views.
- Updated release-facing documentation to use the current canonical naming consistently.
- Repackaged and reinstalled the VSIX against the current workspace so the publishable asset matches the validated repository state.

## 0.1.1 - 2026-03-14

- Fixed Shelf validation defaults to use the supported `validate_canonical.py` commands instead of passing stale arguments.
- Added runtime command normalization so existing user settings with the stale `--json` flag still run successfully.
- Synced the extension README and tests with the supported validation command contract to prevent the mismatch from reappearing.

## 0.1.0 - 2026-03-14

- Raised the extension version to `0.1.0` to match the repository-wide architecture rewrite instead of treating it as another `0.0.x` patch.
- Kept the extension aligned with the rewritten mainline:
  `Framework -> Config -> Code -> Evidence`.
- Kept project navigation, auto-materialization, generated-artifact guarding, and validation centered on `projects/*/project.toml` and canonical-derived views.
- Fixed configured-framework inference to read `[[framework.modules]]` directly from the unified config layout.
- Updated repository docs to point at the current pipeline entrypoint and mark the rewrite execution ledger as complete so extension-facing guidance matches the shipped architecture.

## 0.0.48 - 2026-03-14

- Rebased Shelf AI on the rewritten repository architecture:
  `Framework -> Config -> Code -> Evidence`.
- Switched project navigation from the removed dual-track config path to unified `projects/*/project.toml`.
- Switched generated-artifact guarding and auto-materialization to discovered `project.toml` files.
- Dropped extension-side dependence on removed legacy project scaffolding assumptions.
- Clarified that `projects/*/generated/canonical.json` is the sole machine truth and all evidence views are derived from it.
