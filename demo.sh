#!/bin/bash
set -euo pipefail

echo "=== Multi-tenant Demo Seed ==="

API_BASE=${API_BASE:-http://localhost:8000}

create_tenant() {
  local NAME=$1
  local CODE=$2
  local DOMAIN=$3
  curl -sS -X POST "$API_BASE/tenants" \
    -H "Content-Type: application/json" \
    -H "X-Role: ADMIN" \
    -d "{\"name\":\"$NAME\",\"code\":\"$CODE\",\"primary_domain\":\"$DOMAIN\"}"
}

echo "Seeding tenants..."
create_tenant "PilotCo" "pilot" "pilot.local"
create_tenant "StandardCo" "standard" "standard.local"
create_tenant "EnterpriseCo" "enterprise" "enterprise.local"
echo "Done"