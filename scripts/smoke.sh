#!/usr/bin/env bash
set -euo pipefail

BASE=${1:-http://localhost:8000}
echo "Health: $(curl -fsS "$BASE/healthz")"
echo "Ready: $(curl -fsS "$BASE/readyz")"
echo "Jobs: $(curl -fsS -H "Authorization: Bearer ${JWT_TOKEN:-}" "$BASE/jobs" || true)"

