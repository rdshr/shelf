# Changelog

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
- Updated ArchSync packaged docs and Markdown snippets to reflect the new frontend primitive sink: domain `L0` examples now point to concrete frontend `L0` atoms such as `frontend.L0.M0[...]`, instead of the older coarse `frontend.L1.M0[...]` component-family reference.
- Updated examples again for the deeper frontend common-structure split: domain `L0` examples now point to concrete frontend `L1` component atoms such as `frontend.L1.M0[...]`, while frontend `L0` is reserved for lower-level common structures.
- Aligned the published guidance with the current structure-first layering: frontend primitive atoms -> generic component assembly -> domain atoms -> domain scenes.

## 0.0.17 - 2026-03-07
- Synced ArchSync rule hints with the new cross-framework foundation ref syntax (`frontend.L1.M0[...]`) and the added validator rules `FW027` / `FW028`.
- Updated the packaged docs and snippets to reflect the current structure-first stack: generic frontend structures, domain knowledge-base structures, and project-instantiated generation.

## 0.0.16 - 2026-03-07
- Made GitHub Release creation non-blocking in the publish workflow so registry publication can continue even if the repository token cannot create releases.

## 0.0.15 - 2026-03-07
- Fixed the GitHub Actions release workflow by moving registry-token checks into shell steps; GitHub rejected `secrets.*` inside those step-level `if` expressions.

## 0.0.14 - 2026-03-07
- Replaced third-party GitHub release/publish actions with CLI-based publishing steps so the release workflow can run under stricter GitHub Actions policies.

## 0.0.13 - 2026-03-07
- Switched the public extension identity from `local.archsync` to `rdshr.archsync` for registry publishing.
- Added release automation for GitHub Releases plus optional Open VSX / VS Marketplace publishing on `archsync-v*` tags.
- Updated package metadata for public distribution links and explicit custom license reference.

## 0.0.12 - 2026-03-07
- Added an experimental rainbow-arch Activity Bar icon direction and kept the previous tomoe glyph as an explicit rollback snapshot.

## 0.0.11 - 2026-03-07
- Reduced the outer ring thickness again while keeping the enlarged custom glyph pipeline unchanged.

## 0.0.10 - 2026-03-07
- Thinned the ArchSync glyph geometry while keeping the larger GitLens-style product icon pipeline, reducing the heavy ring and inner tomoe weight.

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
- Added Activity Bar icon + sidebar home view for ArchSync.
- Sidebar supports one-click actions: open tree, refresh tree, validate, show issues.
- Removed `n/a` text from disabled status bar state.
- Updated sidebar icon to Möbius ring style.

## 0.0.2 - 2026-03-06
- Framework tree generation defaults to `framework/<module>/Lx-*.md` source.
- Tree edges are restricted to adjacent levels only (`Lx -> Lx+1`).
- Added node-level source metadata (`source_file`, `source_line`) in generated graph payload.
- Added graph detail action `打开源文件` to jump from node to markdown source line in VSCode.
- Updated ArchSync default tree generate command and README.

## 0.0.1
- Initial local release.
