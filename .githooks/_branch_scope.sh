#!/usr/bin/env bash
set -euo pipefail

shelf_hook_branch_scope_raw() {
  if [[ -n "${SHELF_HOOK_PROTECTED_BRANCHES:-}" ]]; then
    printf '%s\n' "${SHELF_HOOK_PROTECTED_BRANCHES}"
    return 0
  fi

  local configured=""
  configured="$(git config --get shelf.hookProtectedBranches || true)"
  if [[ -n "${configured}" ]]; then
    printf '%s\n' "${configured}"
    return 0
  fi

  # Safe default: enforce hooks only on the repository's protected branches.
  printf 'framework main\n'
}

shelf_hook_branch_scope_list() {
  local raw
  raw="$(shelf_hook_branch_scope_raw)"
  printf '%s\n' "${raw}" | tr ',;' '  ' | xargs -n1
}

shelf_hook_current_branch() {
  git symbolic-ref --quiet --short HEAD 2>/dev/null || true
}

shelf_hook_branch_is_protected() {
  local branch="${1:-}"
  if [[ -z "${branch}" ]]; then
    return 1
  fi

  while IFS= read -r allowed; do
    [[ -z "${allowed}" ]] && continue
    if [[ "${allowed}" == "${branch}" ]]; then
      return 0
    fi
  done < <(shelf_hook_branch_scope_list)
  return 1
}

shelf_hook_should_run_for_current_branch() {
  local branch
  branch="$(shelf_hook_current_branch)"
  if shelf_hook_branch_is_protected "${branch}"; then
    return 0
  fi
  return 1
}

shelf_hook_scope_message() {
  local list
  list="$(shelf_hook_branch_scope_list | xargs)"
  printf 'protected branches: [%s]' "${list}"
}
