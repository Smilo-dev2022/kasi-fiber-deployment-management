#!/usr/bin/env bash
set -euo pipefail

# GitHub policy checker/enforcer
# Requires: jq

OWNER_REPO="${GITHUB_REPOSITORY:-}"
DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"
GH_TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
ENFORCE="${ENFORCE:-false}"

if [[ -z "$OWNER_REPO" ]]; then
  echo "GITHUB_REPOSITORY not set (owner/repo)." >&2
  exit 1
fi
if [[ -z "$GH_TOKEN" ]]; then
  echo "Set GH_TOKEN or provide GITHUB_TOKEN in CI." >&2
  exit 1
fi

OWNER="${OWNER_REPO%%/*}"
REPO="${OWNER_REPO#*/}"

api() {
  local method="$1"; shift
  local path="$1"; shift
  local data="${1:-}"
  local url="https://api.github.com/repos/${OWNER}/${REPO}${path}"
  if [[ -n "$data" ]]; then
    curl -sS -X "$method" \
      -H "Authorization: Bearer ${GH_TOKEN}" \
      -H "Accept: application/vnd.github+json" \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      -d "$data" "$url"
  else
    curl -sS -X "$method" \
      -H "Authorization: Bearer ${GH_TOKEN}" \
      -H "Accept: application/vnd.github+json" \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      "$url"
  fi
}

CHECK_FAILED=0

echo "Checking repo privacy and forking..."
repo_json="$(api GET "")"
private_val="$(echo "$repo_json" | jq -r '.private')"
allow_forking_val="$(echo "$repo_json" | jq -r '.allow_forking')"
if [[ "$private_val" != "true" ]]; then echo "FAIL: repo not private"; CHECK_FAILED=1; fi
if [[ "$allow_forking_val" != "false" ]]; then echo "FAIL: forking not disabled"; CHECK_FAILED=1; fi
if [[ "$ENFORCE" == "true" ]]; then
  api PATCH "" "$(jq -n --argjson private true --argjson allow_forking false '{private:$private,allow_forking:$allow_forking}')" >/dev/null || true
fi

echo "Checking GitHub Pages..."
pages_status=$(curl -sS -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${GH_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/${OWNER}/${REPO}/pages")
if [[ "$pages_status" != "404" ]]; then
  echo "FAIL: GitHub Pages is enabled"
  CHECK_FAILED=1
  if [[ "$ENFORCE" == "true" ]]; then
    curl -sS -X DELETE \
      -H "Authorization: Bearer ${GH_TOKEN}" \
      -H "Accept: application/vnd.github+json" \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      "https://api.github.com/repos/${OWNER}/${REPO}/pages" || true
  fi
fi

echo "Enabling security & analysis features (best-effort)..."
if [[ "$ENFORCE" == "true" ]]; then
  # Dependabot alerts (vulnerability alerts)
  curl -sS -X PUT \
    -H "Authorization: Bearer ${GH_TOKEN}" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com/repos/${OWNER}/${REPO}/vulnerability-alerts" || true
  # Secret scanning and push protection
  api PATCH "" '{"security_and_analysis":{"secret_scanning":{"status":"enabled"},"secret_scanning_push_protection":{"status":"enabled"}}}' >/dev/null || true
fi

echo "Checking branch protection on ${DEFAULT_BRANCH}..."
prot_json=$(api GET "/branches/${DEFAULT_BRANCH}/protection" || true)
if [[ -z "$prot_json" || "$prot_json" == *"Not Found"* ]]; then
  echo "FAIL: no branch protection on ${DEFAULT_BRANCH}"
  CHECK_FAILED=1
  if [[ "$ENFORCE" == "true" ]]; then
    api PUT "/branches/${DEFAULT_BRANCH}/protection" '{"required_status_checks":{"strict":true,"contexts":["build"]},"enforce_admins":true,"required_pull_request_reviews":{"required_approving_review_count":1,"dismiss_stale_reviews":true,"require_code_owner_reviews":true},"restrictions":null,"required_linear_history":true,"allow_force_pushes":false,"allow_deletions":false,"required_conversation_resolution":true}' >/dev/null || true
  fi
else
  strict="$(echo "$prot_json" | jq -r '.required_status_checks.strict')"
  contexts="$(echo "$prot_json" | jq -r '.required_status_checks.contexts[]?')"
  require_code_owner="$(echo "$prot_json" | jq -r '.required_pull_request_reviews.require_code_owner_reviews')"
  admins="$(echo "$prot_json" | jq -r '.enforce_admins.enabled')"
  linear="$(echo "$prot_json" | jq -r '.required_linear_history.enabled')"
  conv="$(echo "$prot_json" | jq -r '.required_conversation_resolution.enabled')"
  if [[ "$strict" != "true" ]]; then echo "FAIL: status checks not strict"; CHECK_FAILED=1; fi
  if ! grep -q "^build$" <<< "$contexts"; then echo "FAIL: 'build' status check not required"; CHECK_FAILED=1; fi
  if [[ "$require_code_owner" != "true" ]]; then echo "FAIL: code owner reviews not required"; CHECK_FAILED=1; fi
  if [[ "$admins" != "true" ]]; then echo "FAIL: admin enforcement disabled"; CHECK_FAILED=1; fi
  if [[ "$linear" != "true" ]]; then echo "FAIL: linear history not required"; CHECK_FAILED=1; fi
  if [[ "$conv" != "true" ]]; then echo "FAIL: conversation resolution not required"; CHECK_FAILED=1; fi
fi

echo "Checking required signed commits..."
sig_status=$(curl -sS -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${GH_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/${OWNER}/${REPO}/branches/${DEFAULT_BRANCH}/protection/required_signatures")
if [[ "$sig_status" != "204" ]]; then
  echo "FAIL: signed commits not required"
  CHECK_FAILED=1
  if [[ "$ENFORCE" == "true" ]]; then
    curl -sS -X POST \
      -H "Authorization: Bearer ${GH_TOKEN}" \
      -H "Accept: application/vnd.github+json" \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      "https://api.github.com/repos/${OWNER}/${REPO}/branches/${DEFAULT_BRANCH}/protection/required_signatures" >/dev/null || true
  fi
fi

if [[ "$CHECK_FAILED" -ne 0 ]]; then
  echo "Policy check failed." >&2
  exit 1
fi
echo "All policy checks passed."

