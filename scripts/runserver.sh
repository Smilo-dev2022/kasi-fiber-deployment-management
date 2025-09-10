#!/usr/bin/env bash
set -euo pipefail

ENVFILE="${1:-.env.staging}"
if [[ -f "$ENVFILE" ]]; then
  set -a
  source "$ENVFILE"
  set +a
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000

