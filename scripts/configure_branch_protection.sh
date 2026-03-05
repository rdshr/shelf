#!/usr/bin/env bash
set -euo pipefail

REPO_SLUG="${1:-rdshr/shelf}"
BRANCH="${2:-main}"
REQUIRED_CONTEXT="${3:-Strict Mapping Gate / strict-mapping}"
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
