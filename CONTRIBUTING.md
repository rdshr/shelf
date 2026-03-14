# Contributing to Shelf

Shelf is a structure-first repository.

The active convergence chain is:

`Framework Markdown -> Package Registry -> Project Config -> Code -> Evidence`

`projects/*/generated/canonical_graph.json` is the only machine truth.

## Read This First

- [specs/规范总纲与树形结构.md](./specs/规范总纲与树形结构.md)
- [specs/框架设计核心标准.md](./specs/框架设计核心标准.md)
- [projects/README.md](./projects/README.md)
- [AGENTS.md](./AGENTS.md)

## Environment

Use `uv` for Python dependencies and execution:

```bash
uv sync
bash scripts/install_git_hooks.sh
```

## Required Checks

Run these before pushing changes that affect standards, scripts, runtime behavior, or generated evidence:

```bash
uv run mypy
uv run python scripts/materialize_project.py
uv run python scripts/validate_strict_mapping.py
uv run python scripts/validate_strict_mapping.py --check-changes
```

## Source-Of-Truth Rules

- Do not manually edit `projects/<project_id>/generated/*`.
- If project behavior changes, update `framework/*.md` or `projects/<project_id>/project.toml` first.
- `selection` chooses framework roots.
- `truth` defines product truth.
- `refinement` defines implementation details.
- `narrative` explains author intent but does not replace structured fields.

## Framework Authoring Rules

Framework modules should remain explicit about:

- capability
- boundary
- minimal viable bases
- combination rules
- verification

The repository authoring entrypoint for framework modules is the `@framework` template and the Shelf AI insertion command.

## Project Authoring Rules

`projects/<project_id>/project.toml` is the only project config entrypoint.

Keep comments clear and layered:

- `[selection]`
  choose framework roots and module-tree shape
- `[truth]`
  explain concrete product truth
- `[refinement]`
  explain implementation refinements
- `[narrative]`
  preserve human discussion context without becoming machine truth

When practical, prefer detailed Chinese comments over minimal labels.

## Good Contribution Areas

- framework module quality
- framework package registry and contract quality
- canonical-derived governance and validation
- runtime templates
- Shelf AI navigation and validation UX
- public docs and onboarding

## Pull Request Notes

When opening a PR, explain:

- which layer changed
- why the change belongs to that layer
- which validations were run
- whether the change affects generated artifacts

Shelf is optimized for getting the structure right first and keeping the implementation aligned with the registry-bound compile chain.
