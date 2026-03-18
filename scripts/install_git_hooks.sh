#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
git -C "$repo_root" config core.hooksPath .githooks
git -C "$repo_root" config --local shelf.hookProtectedBranches "framework main"
chmod +x "$repo_root/.githooks/_branch_scope.sh"
chmod +x "$repo_root/.githooks/pre-commit"
chmod +x "$repo_root/.githooks/pre-push"

echo "Installed git hooks from .githooks/"
echo "core.hooksPath=$(git -C "$repo_root" config --get core.hooksPath)"
echo "shelf.hookProtectedBranches=$(git -C "$repo_root" config --get shelf.hookProtectedBranches)"
