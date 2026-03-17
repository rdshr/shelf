#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
git -C "$repo_root" config core.hooksPath .githooks
chmod +x "$repo_root/.githooks/pre-commit"
chmod +x "$repo_root/.githooks/pre-push"

echo "Installed git hooks from .githooks/"
echo "core.hooksPath=$(git -C "$repo_root" config --get core.hooksPath)"
