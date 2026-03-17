---
name: Bug report
about: Report a runtime, validation, materialization, or tooling issue
title: "[Bug] "
labels: bug
assignees: ""
---

## Summary

Describe the problem in one or two sentences.

## Layer

Which layer does this affect?

- Framework
- Config
- Code
- Evidence
- Shelf AI

## Reproduction

Steps to reproduce:

1.
2.
3.

## Expected behavior

What should happen instead?

## Actual behavior

What happened?

## Files involved

List the main files or paths involved.

## Validation status

Paste relevant command output if available:

```bash
uv run mypy
uv run python scripts/materialize_project.py
uv run python scripts/validate_canonical.py
uv run python scripts/validate_canonical.py --check-changes
```

## Additional context

Anything else that helps explain the issue.
