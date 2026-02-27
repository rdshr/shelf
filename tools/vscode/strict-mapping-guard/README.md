# Strict Mapping Guard (VSCode Extension)

## What It Does
- Runs strict mapping validation automatically on startup.
- Runs strict mapping validation on save/create/rename/delete for relevant files.
- Runs strict mapping validation when watched files change outside VSCode and when window regains focus.
- Shows validation issues in VSCode Problems panel.
- Status bar (`Mapping issues`) is clickable and opens an issue picker for direct file/line jump.
- Auto-fail notification provides buttons: `Open Problems` / `Open Log`.
- Provides manual command: `Strict Mapping: Validate Now`.

## Install (Local)
1. Open `tools/vscode/strict-mapping-guard` in VSCode.
2. Press `F5` to launch Extension Development Host.
3. Open the repository in the launched host window.

## Commands
- `Strict Mapping: Validate Now`
- `Strict Mapping: Show Issues`

## Configuration
- `strictMappingGuard.enableOnSave`
- `strictMappingGuard.changeValidationCommand`
- `strictMappingGuard.fullValidationCommand`

Default commands use the repository validator:
- `uv run python scripts/validate_strict_mapping.py --check-changes --json`
- `uv run python scripts/validate_strict_mapping.py --json`
