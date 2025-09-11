#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/set_github_secrets.sh <owner/repo> <SUPABASE_ACCESS_TOKEN> <SUPABASE_PROJECT_REF>
# Requires: gh CLI authenticated (gh auth login)

REPO="${1:-}"
SUPA_TOKEN="${2:-}"
SUPA_REF="${3:-}"

if [[ -z "$REPO" || -z "$SUPA_TOKEN" || -z "$SUPA_REF" ]]; then
  echo "Usage: $0 <owner/repo> <SUPABASE_ACCESS_TOKEN> <SUPABASE_PROJECT_REF>"
  exit 1
fi

# Set secrets
gh secret set SUPABASE_ACCESS_TOKEN -R "$REPO" -b"$SUPA_TOKEN"
gh secret set SUPABASE_PROJECT_REF -R "$REPO" -b"$SUPA_REF"

echo "✅ GitHub secrets set on $REPO: SUPABASE_ACCESS_TOKEN, SUPABASE_PROJECT_REF"