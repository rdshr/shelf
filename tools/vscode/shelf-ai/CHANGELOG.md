# Changelog

## 0.0.48 - 2026-03-14

- Rebased Shelf AI on the rewritten repository architecture:
  `Framework Markdown -> Package Registry -> Project Config -> Code -> Evidence`.
- Switched project navigation from the removed dual-track config path to unified `projects/*/project.toml`.
- Switched generated-artifact guarding and auto-materialization to discovered `project.toml` files.
- Dropped extension-side dependence on the removed legacy mapping list and old scaffold-project commands.
- Clarified that `projects/*/generated/canonical_graph.json` is the sole machine truth and all governance views are derived from it.
