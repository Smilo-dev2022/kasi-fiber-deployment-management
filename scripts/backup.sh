#!/usr/bin/env bash
set -euo pipefail

# Usage: PGURL=postgresql://user:pass@host:5432/db ./scripts/backup.sh /backups

DEST_DIR=${1:-/backups}
mkdir -p "$DEST_DIR"
TS=$(date +%Y%m%d_%H%M%S)
OUT="$DEST_DIR/pg_backup_$TS.sql.gz"

pg_dump --no-owner --no-privileges --format=plain "$PGURL" | gzip -9 > "$OUT"
echo "Backup written to $OUT"

