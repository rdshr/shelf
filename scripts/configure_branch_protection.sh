#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKFLOW_FILE="${REPO_ROOT}/.github/workflows/strict-mapping-gate.yml"

discover_repo_slug() {
  local remote_url
  remote_url="$(git -C "${REPO_ROOT}" config --get remote.origin.url 2>/dev/null || true)"
  if [[ -z "${remote_url}" ]]; then
    echo "xueyu888/shelf"
    return
  fi
  case "${remote_url}" in
    https://github.com/*)
      remote_url="${remote_url#https://github.com/}"
      remote_url="${remote_url%.git}"
      echo "${remote_url}"
      ;;
    git@github.com:*)
      remote_url="${remote_url#git@github.com:}"
      remote_url="${remote_url%.git}"
      echo "${remote_url}"
      ;;
    *)
      echo "${remote_url}" | sed -E 's#.*github.com[:/]([^ ]+?)(\.git)?$#\1#'
      ;;
  esac
}

discover_default_branch() {
  local remote_head current_branch
  remote_head="$(git -C "${REPO_ROOT}" symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null || true)"
  if [[ -n "${remote_head}" ]]; then
    echo "${remote_head#origin/}"
    return
  fi
  current_branch="$(git -C "${REPO_ROOT}" branch --show-current 2>/dev/null || true)"
  if [[ -n "${current_branch}" ]]; then
    echo "${current_branch}"
    return
  fi
  echo "main"
}

discover_required_context() {
  local workflow_name job_id
  if [[ -f "${WORKFLOW_FILE}" ]]; then
    workflow_name="$(sed -n 's/^name:[[:space:]]*//p' "${WORKFLOW_FILE}" | head -n 1)"
    job_id="$(
      awk '
        /^jobs:/ { in_jobs=1; next }
        in_jobs && /^[[:space:]]{2}[A-Za-z0-9_-]+:/ {
          gsub(":", "", $1)
          print $1
          exit
        }
      ' "${WORKFLOW_FILE}"
    )"
    if [[ -n "${workflow_name}" && -n "${job_id}" ]]; then
      echo "${workflow_name} / ${job_id}"
      return
    fi
  fi
  echo "Strict Mapping Gate / strict-mapping"
}

REPO_SLUG="${1:-$(discover_repo_slug)}"
BRANCH="${2:-$(discover_default_branch)}"
REQUIRED_CONTEXT="${3:-$(discover_required_context)}"
TOKEN="${GITHUB_TOKEN:-${GH_TOKEN:-}}"

if [[ -z "$TOKEN" ]]; then
  echo "Missing token. Set GITHUB_TOKEN or GH_TOKEN with repo admin permission." >&2
  exit 1
fi

api_url="https://api.github.com/repos/${REPO_SLUG}/branches/${BRANCH}/protection"
payload="$(cat <<JSON
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["${REQUIRED_CONTEXT}"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON
)"

echo "Configuring branch protection for ${REPO_SLUG}:${BRANCH} ..."
http_code="$(
  curl -sS -o /tmp/branch_protection_response.json -w "%{http_code}" \
    -X PUT "${api_url}" \
    -H "Accept: application/vnd.github+json" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    -d "${payload}"
)"

if [[ "${http_code}" != "200" ]]; then
  echo "Failed to configure branch protection (HTTP ${http_code})." >&2
  cat /tmp/branch_protection_response.json >&2
  exit 1
fi

echo "Branch protection configured successfully."
