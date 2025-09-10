#!/usr/bin/env bash
set -euo pipefail

# Usage: PGURL=postgresql://user:pass@host:5432/db ./scripts/restore.sh /backups/pg_backup_YYYYMMDD_HHMMSS.sql.gz

SRC=${1:?specify backup file}
gunzip -c "$SRC" | psql "$PGURL"
echo "Restore complete from $SRC"

