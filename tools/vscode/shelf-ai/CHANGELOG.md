# Changelog

## 0.1.20 - 2026-03-20

- Switched Shelf AI Problems diagnostics to Chinese by default instead of leaking English validation text from generated-artifact guards and correspondence summaries.
- Added correspondence-side reason localization so common audit drift messages land in Chinese even when the underlying runtime emits English reason strings.
- Repacked and reinstalled the local VSIX after the diagnostics localization fix so the shipped release matches the current validated workspace.

## 0.1.19 - 2026-03-20

- Removed fixed default-project assumptions in runtime and scripts: project resolution now supports discovery from `projects/*/project.toml` or explicit input instead of `projects/project.toml` fallback.
- Hardened no-project handling in CLI/validation/materialization paths with explicit messages and bootstrap-aware checks.
- Synced repository docs and guards to the current `message_queue_basic` baseline and canonical path conventions.

## 0.1.18 - 2026-03-20

- Replaced hard-coded per-module `if module_id == ...` export assignment branches in runtime/evidence layers with mapping-driven export injection.
- Removed fixed `frontend/knowledge_base/backend` overlay branching in framework projection and switched to framework-name-driven overlay path generation.
- Added repository-level hardcode regression guard (`tests/test_no_hardcode_guard.py`) and enforced anti-hardcode execution requirements in `AGENTS.md`.

## 0.1.17 - 2026-03-20

- Removed hard-coded root-role coupling checks in `project_runtime.code_layer` and switched consistency validation to framework-upstream-derived dependencies plus explicit config overrides.
- Added configurable root-role dependency overrides at `exact.evidence.root_role_dependencies`, so projects can declare extra root coupling without patching runtime code.
- Enabled queue-only project materialization/validation flow (`message_queue` roots without mandatory frontend/knowledge_base/backend triple), while keeping per-module export injection strict to selected roots only.

## 0.1.16 - 2026-03-20

- Removed hard dependency on `projects/knowledge_base_basic/project.toml` as the extension fallback project file and switched to generic `projects/*/project.toml` discovery.
- Updated issue reveal fallback behavior so Shelf can still open a valid workspace file (project file first, then standards doc) when no canonical issue file is available.
- Synced framework/correspondence navigation default project preference to the generic workspace fallback path.

## 0.1.15 - 2026-03-20

- Updated framework design standards to remove the mandatory base-to-capability direct mapping constraint and keep capability derivation at the rule-combination layer.
- Added correspondence guard enforcement that every base must declare at least one boundary and that declared base boundaries must belong to the owner module.
- Synced Shelf AI framework lint hint `FW022` wording with the new base-boundary constraint semantics.

## 0.1.14 - 2026-03-19

- Removed extension-side normalization that silently stripped stale `--json` from validation commands; Shelf now executes the configured validation command as-is.
- Hardened tree webview HTML escaping for both text nodes and attribute values (`"`, `'`, `<`, `>`, `&`) and added regression tests for attribute-injection payloads.
- Added `check:webview-types` and extension test execution to the `Publish Shelf AI` workflow before VSIX packaging.

## 0.1.13 - 2026-03-19

- Renamed the framework authoring term from `Boundary` to `Parameter` across current framework docs, Shelf AI snippets, completion entries, and author-facing plugin documentation.
- Kept parser and navigation compatibility for legacy framework files by accepting both the new `参数定义 / 参数绑定` syntax and the previous `边界定义 / 边界绑定` wording during the transition.
- Revalidated the repository, reran plugin tests, and repackaged the local VSIX so the shipped extension matches the current validated workspace and terminology baseline.

## 0.1.12 - 2026-03-17

- Refined the dedicated monochrome Activity Bar duck glyph so the icon now fills the sidebar slot more decisively while keeping thinner, cleaner inner lines.
- Kept the colorful README / Marketplace artwork unchanged; this patch only tunes the VS Code sidebar-specific icon adaptation.
- Repackaged and reinstalled the local VSIX after the icon tweak so the shipped asset matches the current validated workspace.

## 0.1.11 - 2026-03-17

- Refreshed Shelf AI branding with a new duck icon set: the extension now ships a colorful README/Marketplace icon together with a dedicated monochrome Activity Bar glyph tuned for VS Code's sidebar constraints.
- Added the icon working assets under `tools/vscode/shelf-ai/design/` so the final shipped icon remains traceable to its design iterations.
- Repackaged and reinstalled the local VSIX after the icon refresh so the published asset matches the validated workspace.

## 0.1.10 - 2026-03-17

- Kept framework tree module edges visible even when canonical is `stale`, so the authoring graph no longer drops arrows just because correspondence freshness is temporarily unavailable.
- Added branch-scoped git-hook enforcement in repository hooks and install flow, with default protected branches set to `framework` and `main` (other branches now skip hook blocking by default).
- Added explicit ignore coverage for `projects/knowledge_base_basic/generated/canonical.json`, keeping local canonical regeneration out of tracked diffs in fresh plugin/repo setups.

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
