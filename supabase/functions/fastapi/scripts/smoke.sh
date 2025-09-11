#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
ORG_ID="${ORG_ID:-}"
ROLE="${ROLE:-ADMIN}"

hdr_org=( )
if [[ -n "$ORG_ID" ]]; then
  hdr_org=(-H "X-Org-Id: $ORG_ID")
fi

hdrs=(-H "X-Role: $ROLE" -H "Content-Type: application/json" "${hdr_org[@]}")

echo "Smoke: healthz" && curl -fsS "$BASE_URL/healthz" | cat

echo "Smoke: readyz" && curl -fsS "$BASE_URL/readyz" | cat

echo "Smoke: list work-queue" && curl -fsS "${BASE_URL}/work-queue" "${hdrs[@]}" | cat || true

# Placeholder: add more endpoint checks as needed

echo "OK"

