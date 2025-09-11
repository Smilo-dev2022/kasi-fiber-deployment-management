#!/usr/bin/env bash
set -euo pipefail

# Harden a GitHub repository using gh CLI and REST API.
# Usage: OWNER=my-org REPO=my-repo BRANCH=main bash scripts/harden_repo.sh

: "${OWNER:?Set OWNER}"
: "${REPO:?Set REPO}"
: "${BRANCH:=main}"

api() {
	# Wrapper for gh api with sane defaults
	gh api -H "Accept: application/vnd.github+json" "$@"
}

echo "Hardening $OWNER/$REPO on branch ${BRANCH}..."

# 1) Disable forking and Pages; enable delete branch on merge
api -X PATCH "/repos/$OWNER/$REPO" \
	-f allow_forking=false \
	-f delete_branch_on_merge=true \
	-F security_and_analysis={\
		\"advanced_security\":{\"status\":\"enabled\"},\
		\"secret_scanning\":{\"status\":\"enabled\"},\
		\"secret_scanning_push_protection\":{\"status\":\"enabled\"}\
	}

# Disable GitHub Pages (ignore errors if not enabled)
set +e
api -X DELETE "/repos/$OWNER/$REPO/pages" 2>/dev/null || true
set -e

# 2) Branch protection
api -X PUT "/repos/$OWNER/$REPO/branches/${BRANCH}/protection" \
	-F required_status_checks={\
		\"strict\":true,\
		\"contexts\":[\"build-and-push\"]\
	} \
	-F enforce_admins=true \
	-F required_pull_request_reviews={\
		\"required_approving_review_count\":1,\
		\"dismiss_stale_reviews\":true,\
		\"require_code_owner_reviews\":true\
	} \
	-F restrictions= \
	-F allow_force_pushes=false \
	-F allow_deletions=false

# Require signed commits on the branch
api -X POST "/repos/$OWNER/$REPO/branches/${BRANCH}/protection/required_signatures" >/dev/null

echo "✔ Repo hardened. Note: Enforce SSO/2FA at the ORG level manually."

