#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <envfile>" >&2
  exit 1
fi

ENVFILE="$1"

if [[ ! -f "$ENVFILE" ]]; then
  echo "Env file not found: $ENVFILE" >&2
  exit 1
fi

set -a
source "$ENVFILE"
set +a

alembic upgrade head