# Changelog

## Unreleased

## 0.0.47 - 2026-03-13
- Added a structure-first authoring workflow for framework drafts and product truth. Shelf AI now supports `framework_drafts/` navigation plus one-click draft publishing, can scaffold a framework-driven project from the extension, and lets `product_spec.toml` stay as the root entry while splitting concrete product sections into `product_spec/*.toml`.
- Reworked boundary and authoring flows to remove hardwired single-file assumptions. Boundary jumps now prefer real split section files, repository governance resolves section source files through the composed product-spec loader, and generated governance evidence keeps pointing back to the actual section file instead of only the root `product_spec.toml`.
- Added manual workflow controls to the extension: validation trigger mode can now be `manual`, `save`, or `all`, and Shelf AI exposes an explicit codegen preflight command so framework / product / implementation checks can be run before asking AI to generate code.
- Formalized the positive-vs-negative framework protocol. `C*` now stays positive-only, `N*` carries non-responsibility declarations, negative rules use `失效结论` instead of faking `输出能力`, and the framework corpus, snippet templates, parser, strict validator, and regression tests were migrated together.

## 0.0.46 - 2026-03-13
- Fixed the long-lived validation deadlock path in Shelf AI. Validation commands now run with timeout protection, and a manual `Shelf: Validate Mapping Now` request can restart a stale in-flight validation instead of leaving the extension apparently unresponsive until `Reload Window`.
- Changed boundary-to-product-spec navigation to prefer materialized governance manifests when available. This removes the hardcoded knowledge-base bias and lets custom frameworks such as `document_chunking` resolve to the correct `projects/*/product_spec.toml` section after project materialization.
- Added regression coverage for both fixes: plugin-side runtime tests now guard command-timeout / stale-restart behavior, and framework-navigation tests now cover a custom framework that resolves boundary navigation through generated governance metadata.

## 0.0.45 - 2026-03-13
- Formalized the `B / R / C+` relation model in the repository standards and strict validation chain. Positive capabilities now map to exactly one base-level source expression, while combination principles still legitimately span multiple bases and produce multiple capabilities.
- Rewrote the affected framework modules to follow the tightened base-source rule, then synced the lint / validation behavior so capability-to-base ownership is no longer inferred loosely from mixed dependency context.
- Fixed Shelf AI's stale-diagnostics behavior for edited watched documents. The extension now clears outdated Shelf diagnostics while files are being edited, prefixes visible failures with a cross marker, and turns the status bar into an explicit failing state instead of leaving a misleading `Shelf OK` during auto-triggered errors.

## 0.0.44 - 2026-03-13
- Restored the framework tree as Shelf AI's default visual entry. The sidebar and primary command now open `docs/hierarchy/shelf_framework_tree.html`, while the workspace governance tree stays available as a separate secondary view for closure tracing and guard debugging.
- Split framework-tree and governance-tree commands, packaged settings, and generated-artifact protection. Both derived tree artifacts are now regenerated and guarded independently instead of being treated as one mixed default view.
- Fixed the framework-tree canvas viewport model so left-drag now pans a real workspace surface instead of a content-stretched pseudo-viewport. The generated graph keeps extra workspace padding, recenters after fit/reset, and behaves closer to Visio-style canvas navigation.
- Registered repository-level code governance more explicitly by adding a Chinese-first Git commit-message standard alongside the existing release-note standard under `specs/code/`.

## 0.0.43 - 2026-03-11
- Clarified the current governance-tree scope in the packaged Shelf AI docs: the mainline now explicitly means the path that carries `Framework -> Product Spec -> Implementation Config -> Code -> Evidence` convergence plus the reverse-check chain back to upstream structure.
- Documented the current coverage boundary more precisely: Shelf AI strongly governs the structural mainline carriers, while lower-level rendering and presentation details remain only partially governed instead of being overstated as fully closed.
- Synced this release with the repository-side second-round audit so packaged guidance, GitHub release notes, and the current governance posture no longer drift apart.

## 0.0.40 - 2026-03-10
- Switched Shelf AI from a framework-tree-only view to a workspace governance-tree flow. The extension now reads the workspace governance tree, opens the governance-tree view directly, and surfaces the recent touched / affected node closure inside the sidebar.
- Moved strict validation to the same workspace-governance source used by the extension. Validation now resolves affected projects and checks through governance-tree closure instead of relying on framework-tree-only path heuristics.
- Added governance-tree regression coverage and updated the packaged docs so the published extension explains the current single-tree workflow more accurately.

## 0.0.39 - 2026-03-10
- Turned Shelf AI into a background workspace guard instead of a validation-only companion. Relevant saves, file operations, external file changes, and focus returns are now classified before validation, so the extension can decide when to materialize affected projects, when to run Python type checks, and when to surface guard failures.
- Added generated-artifact protection plus `normal` / `strict` guard modes. Direct edits under `projects/*/generated/*` are now always detected, with strict mode attempting automatic restore through project materialization.
- Added git-hook awareness and one-click installation from the extension UI so repository `pre-push` enforcement is easier to keep enabled across contributor machines.
- Added packaged configuration for guard behavior (`guardMode`, `autoMaterialize`, generated protection, mypy-on-change, hook prompt, materialize command, type-check command) and updated the packaged docs / regression tests accordingly.
- Added a repository-side architecture presentation generator script for explaining the current Shelf AI structure, capabilities, and Codex-facing guard model without checking the binary presentation into git.

## 0.0.38 - 2026-03-10
- Synced Shelf AI packaged metadata to the renamed `xueyu888/shelf` repository, so release, issue, and homepage links now resolve to the live public repo.
- Refreshed the repository-facing presentation so Shelf emphasizes logically self-consistent design rather than intuition-led structure, keeping the public positioning aligned with the framework philosophy.
- This release is a packaging and public-entry consistency update; extension functionality is unchanged.

## 0.0.37 - 2026-03-10
- Renamed the VS Code companion to Shelf AI across package metadata, command labels, view ids, media assets, and release automation.
- Updated current documentation, install flows, and knowledge-base reference branding so Shelf becomes the single public name across the repository and extension.
- Switched extension packaging and tag-based publishing to the new `shelf-ai-v*` release path with a `shelf-ai-<version>.vsix` artifact.

## 0.0.36 - 2026-03-10
- Updated Shelf AI packaged metadata and public links so repository, issues, and homepage targets stay aligned with the current public GitHub location.
- Added explicit WSL-aware local install guidance to the packaged README, clarifying how to install and verify Shelf AI from a WSL workspace attached through VS Code.
- This release is mainly a packaging, distribution, and onboarding sync for the current public-facing workflow.

## 0.0.35 - 2026-03-09
- Added framework-markdown fixed-shape completions in Shelf AI. `@framework`, the five standard section headings, `C/P/B/R/V` entries, and `R*.1~R*.4` child lines now have direct completion support instead of relying on snippet discovery alone.
- Added an explicit `Shelf: Insert Framework Module Template` fallback command and regression coverage so the `@framework` standard-template entry remains a non-removable authoring contract.
- Synced repository standards with this requirement: the plain `@framework` template entry is now treated as a hard framework-authoring constraint, not an optional editor convenience.

## 0.0.34 - 2026-03-09
- Published a packaging / documentation sync release so the versioned Shelf AI metadata tracks the current repository-side framework-tree interaction updates and the new Chinese-first product-spec authoring guidance.
- This release does not add new extension-side commands; the main visible changes come from the refreshed workspace framework-tree generator/artifacts and the updated spec-writing conventions in the repository.
- After upgrading, regenerate or refresh the framework tree if you want the tighter layout / arrow / pan behavior from the current repository sources.

## 0.0.33 - 2026-03-09
- Switched Shelf AI boundary-to-project navigation from the legacy `instance.toml` convention to the new `product_spec.toml` convention, so boundary jumps and hover cards now point to the product-truth file that the repository actually uses.
- Updated the packaged extension guidance and repository-facing tests to match the new layering model (`Framework -> Product Spec -> Implementation Config -> Code -> Evidence`), keeping navigation and validation language aligned with the runtime/compiler changes.
- This release is mainly a repository-structure and navigation terminology update; after upgrading, reopen or refresh the framework tree if you had an older navigation result cached.

## 0.0.32 - 2026-03-09
- Hardened the framework-tree interaction contract in the repository-side HTML generator and tests: background drag pans the graph, node / edge click selection stays intact, `Ctrl/⌘ + click` source jumps stay intact, and framework-group controls remain isolated from canvas pan.
- Improved default framework-tree edge readability by making relationship lines and arrowheads more visible without overpowering the graph.

## 0.0.31 - 2026-03-08
- Added framework-group box controls to the generated framework-tree page. Each framework panel can now be collapsed or expanded from its header, dragged as one unit inside the graph, and restored to the default compact layout with `恢复布局`.
- Fixed the framework-group interaction layer so dragging no longer depends on fragile transparent title hit zones. The generated graph now uses explicit framework drag handles and preserves node hover / click behavior while groups move.
- Documented the new framework-group interaction model in the packaged Shelf AI README so the published extension guidance matches the current tree UX.

## 0.0.30 - 2026-03-08
- Reworked the framework-tree layout for framework sources from one global `L0/L1/L2` swimlane into per-framework grouped columns. Each `framework/<module>/` now renders as its own column group, and group ordering follows the cross-framework reference graph.
- Shifted strict framework validation to a references-first model: local inline refs must point downward within the same framework, external refs must resolve to real modules, and the full inline-ref graph is now checked for cycles via `FW029`.
- Compressed and rebuilt the frontend framework stack to reduce over-splitting, then regenerated the framework tree and mapping registry against the new structure plan.

## 0.0.29 - 2026-03-08
- Fixed framework-tree interaction regressions in the generated graph page: node hover no longer flickers around the hit zone, node click selection works again, and `Ctrl/⌘ + click` jump-to-document is restored.
- Fixed the framework-tree right sidebar toggle so the statistics / detail panel can actually be hidden and shown again, instead of leaving the layout visually stuck open.
- This release is primarily a repository-side framework-tree generator / HTML interaction fix; users should refresh or regenerate `docs/hierarchy/shelf_framework_tree.html` after updating.

## 0.0.28 - 2026-03-08
- Expanded boundary-to-instance navigation from explicit top-level sections to full boundary traceability across framework markdown. Derived boundaries such as `CITATION`, `TURN`, `INPUT`, `SCOPE`, and `STATUS` now jump to their owning or related `instance.toml` sections instead of stopping at local definitions only.
- Boundary hover cards now distinguish primary owning sections from additional related sections and include an ownership note when the mapping is inferred rather than directly declared.
- Added framework-markdown reference results for navigable symbols, so `Find All References` / `Shift+F12` can return the current usage, framework definition, and mapped instance configuration target for boundary tokens.

## 0.0.27 - 2026-03-08
- Refined the Shelf AI sidebar into a denser dark VS Code-style home view with clearer overview, actions, workspace signals, and issue preview sections.
- Reworked the framework tree page into a more GitLens / Git Graph-like layout with a scrollable full-size graph surface, stronger right-side inspect panels, and improved node detail grouping.
- Added graph zoom controls (`+`, `-`, `100%`, `适配`) plus `Ctrl/⌘ + 滚轮` zooming so large framework graphs remain readable without shrinking everything to fit.

## 0.0.25 - 2026-03-08
- Added boundary-to-instance navigation for instance-exposed framework boundaries such as `SURFACE`, `LIBRARY`, `CHAT`, and `RETURN`, jumping directly to the owning `instance.toml` section.
- Boundary hover cards now show the mapped project config file and primary related section when that boundary is instantiated as configuration.

## 0.0.24 - 2026-03-07
- Enforced versioned bilingual release notes for Shelf AI public releases.
- Updated the publish workflow to fail when release notes or the `.vsix` asset are missing, and to use the curated notes file as the GitHub release body.

## 0.0.23 - 2026-03-07
- Fixed the GitHub release workflow so the packaged VSIX is uploaded from the correct path during tag-based publishing.

## 0.0.22 - 2026-03-07
- Expanded framework-markdown hover coverage for module refs, module rule refs, and local `B/C/R/V` plus boundary symbols.
- Module hover cards now include combination-principle details, especially participating bases, combination method, output abilities, and boundary bindings.

## 0.0.21 - 2026-03-07
- Changed module-ref navigation so `Lx.My` / `framework.Lx.My` jumps straight to the target module's first `B*` base instead of its title.
- Added module hover cards for whole module refs such as `frontend.L1.M4`, showing the target module's capability declarations and minimum viable bases.

## 0.0.20 - 2026-03-07
- Added framework-markdown `Go to Definition` navigation for local `B/C/R/V` ids, boundary ids, module refs such as `L1.M0` / `frontend.L1.M4`, and rule refs inside module brackets like `frontend.L1.M4[R1,R3]`.

## 0.0.19 - 2026-03-07
- Updated packaged guidance and snippets for the deeper frontend common-structure split: frontend `L0` now represents common structure atoms, while domain `L0` examples point to concrete frontend `L1` component atoms such as `frontend.L1.M0[...]`.
- Synced the published docs with the new structure chain: frontend common structures -> frontend component atoms -> frontend standard -> domain atoms.

## 0.0.18 - 2026-03-07
- Updated Shelf AI packaged docs and Markdown snippets to reflect the new frontend primitive sink: domain `L0` examples now point to concrete frontend `L0` atoms such as `frontend.L0.M0[...]`, instead of the older coarse `frontend.L1.M0[...]` component-family reference.
- Updated examples again for the deeper frontend common-structure split: domain `L0` examples now point to concrete frontend `L1` component atoms such as `frontend.L1.M0[...]`, while frontend `L0` is reserved for lower-level common structures.
- Aligned the published guidance with the current structure-first layering: frontend primitive atoms -> generic component assembly -> domain atoms -> domain scenes.

## 0.0.17 - 2026-03-07
- Synced Shelf AI rule hints with the new cross-framework foundation ref syntax (`frontend.L1.M0[...]`) and the added validator rules `FW027` / `FW028`.
- Updated the packaged docs and snippets to reflect the current structure-first stack: generic frontend structures, domain knowledge-base structures, and project-instantiated generation.

## 0.0.16 - 2026-03-07
- Made GitHub Release creation non-blocking in the publish workflow so registry publication can continue even if the repository token cannot create releases.

## 0.0.15 - 2026-03-07
- Fixed the GitHub Actions release workflow by moving registry-token checks into shell steps; GitHub rejected `secrets.*` inside those step-level `if` expressions.

## 0.0.14 - 2026-03-07
- Replaced third-party GitHub release/publish actions with CLI-based publishing steps so the release workflow can run under stricter GitHub Actions policies.

## 0.0.13 - 2026-03-07
- Switched the public extension identity from the old local-only package id to the registry-ready `rdshr` publisher path.
- Added release automation for GitHub Releases plus optional Open VSX / VS Marketplace publishing on version tags.
- Updated package metadata for public distribution links and explicit custom license reference.

## 0.0.12 - 2026-03-07
- Added an experimental rainbow-arch Activity Bar icon direction and kept the previous tomoe glyph as an explicit rollback snapshot.

## 0.0.11 - 2026-03-07
- Reduced the outer ring thickness again while keeping the enlarged custom glyph pipeline unchanged.

## 0.0.10 - 2026-03-07
- Thinned the Shelf AI glyph geometry while keeping the larger GitLens-style product icon pipeline, reducing the heavy ring and inner tomoe weight.

## 0.0.9 - 2026-03-07
- Switched the Activity Bar icon from raw SVG path loading to a custom product icon glyph, matching GitLens-style rendering behavior more closely.
- Bumped the packaged extension version to force icon cache refresh on reinstall.

## 0.0.8 - 2026-03-06
- Refined the Activity Bar icon to a cleaner infinity-loop silhouette closer to the intended ribbon form.
- Changed module-node source jumps to open module headers, while growth edges keep precise `B*` source lines.
- Framework tree generation now aborts on warnings instead of emitting partial-success graphs.
- Documented remote type-check parity with local validation expectations.

## 0.0.7 - 2026-03-06
- Removed the last validator-side legacy `@layer/@base/@compose` compatibility path; framework docs now validate against one rule set only.
- Added packaged `LICENSE.txt` so VSIX publishing no longer depends on an implicit repository license.
- Refined install and usage docs around the packaged VSIX flow and sidebar entry.

## 0.0.6 - 2026-03-06
- Removed legacy scaffold command and auto-expand flow; the extension now stays focused on validation and tree viewing.
- Added validator rules `FW024` / `FW025` / `FW026` to harden inline module-growth constraints.
- Rewrote markdown snippets to neutral structure-first templates aligned with the current framework rule set.
- Aligned generic hierarchy HTML generator defaults to the current framework tree artifacts.

## 0.0.5 - 2026-03-06
- Enforced inline upstream module refs in `B*` lines; removed legacy `上游模块：...` style.
- Added validator rule `FW023` for the new `B*` format constraint.
- Updated framework tree parsing to rely on inline upstream refs only.

## 0.0.4 - 2026-03-06
- Removed legacy tree compatibility; framework tree generation now only accepts `framework/<module>/Lx-Mn-*.md`.
- Aligned scaffold default output path to `Lx-Mn-*` naming.
- Added module-level source jump metadata consistency for generated framework tree.
- Updated framework docs to explicit upstream module references for growth edges.
- Kept Activity Bar Möbius icon + sidebar tree entry flow.

## 0.0.3 - 2026-03-06
- Added Activity Bar icon + sidebar home view for Shelf AI.
- Sidebar supports one-click actions: open tree, refresh tree, validate, show issues.
- Removed `n/a` text from disabled status bar state.
- Updated sidebar icon to Möbius ring style.

## 0.0.2 - 2026-03-06
- Framework tree generation defaults to `framework/<module>/Lx-*.md` source.
- Tree edges are restricted to adjacent levels only (`Lx -> Lx+1`).
- Added node-level source metadata (`source_file`, `source_line`) in generated graph payload.
- Added graph detail action `打开源文件` to jump from node to markdown source line in VSCode.
- Updated Shelf AI default tree generate command and README.

## 0.0.1
- Initial local release.
