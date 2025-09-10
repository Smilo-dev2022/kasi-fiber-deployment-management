#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/test_webhooks.sh librenms --secret SECRET [--url URL] [--body JSON]
  scripts/test_webhooks.sh zabbix   --secret SECRET [--url URL] [--body JSON]
  scripts/test_webhooks.sh zabbix-clear --secret SECRET [--url URL] [--event-id ID]

Defaults:
  librenms URL: http://127.0.0.1:8000/webhooks/librenms
  zabbix   URL: http://127.0.0.1:8000/webhooks/zabbix

Examples:
  BODY='{"hostname":"OLT-01","severity":"critical","rule":"Device Down","alert_id":12345,"state":"alert","msg":"OLT-01 no response"}'
  scripts/test_webhooks.sh librenms --secret "$WEBHOOK_HMAC_LIBRENMS" --body "$BODY"

  BODY='{"host":"OLT-01","severity":"High","event_id":"8888","problem":true,"name":"PON1 LOS","message":"ONU flaps on PON1"}'
  scripts/test_webhooks.sh zabbix --secret "$WEBHOOK_HMAC_ZABBIX" --body "$BODY"

  scripts/test_webhooks.sh zabbix-clear --secret "$WEBHOOK_HMAC_ZABBIX" --event-id 8888
USAGE
}

if [[ $# -lt 1 ]]; then
  usage; exit 1
fi

SOURCE="$1"; shift
URL_DEFAULT_LIBRENMS="http://127.0.0.1:8000/webhooks/librenms"
URL_DEFAULT_ZABBIX="http://127.0.0.1:8000/webhooks/zabbix"

SECRET=""
URL=""
BODY=""
EVENT_ID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --secret) SECRET="$2"; shift 2;;
    --url) URL="$2"; shift 2;;
    --body) BODY="$2"; shift 2;;
    --event-id) EVENT_ID="$2"; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1"; usage; exit 1;;
  esac
done

if [[ -z "$SECRET" ]]; then
  echo "--secret is required"; exit 1
fi

case "$SOURCE" in
  librenms)
    URL="${URL:-$URL_DEFAULT_LIBRENMS}"
    BODY="${BODY:-{"hostname":"OLT-01","severity":"critical","rule":"Device Down","alert_id":12345,"state":"alert","msg":"OLT-01 no response"}}"
    ;;
  zabbix)
    URL="${URL:-$URL_DEFAULT_ZABBIX}"
    BODY="${BODY:-{"host":"OLT-01","severity":"High","event_id":"8888","problem":true,"name":"PON1 LOS","message":"ONU flaps on PON1"}}"
    ;;
  zabbix-clear)
    URL="${URL:-$URL_DEFAULT_ZABBIX}"
    ID_PART="${EVENT_ID:-8888}"
    BODY="${BODY:-{"host":"OLT-01","severity":"High","event_id":"$ID_PART","problem":false,"name":"PON1 LOS clear","message":"Recovered"}}"
    ;;
  *)
    echo "Unknown source: $SOURCE"; usage; exit 1;;
esac

# Generate HMAC signature (hex) and send
SIG=$(printf '%s' "$BODY" | openssl dgst -sha256 -hmac "$SECRET" -binary | xxd -p -c 256)
echo "POST $URL"
echo "X-Signature: sha256=$SIG"
curl -s -X POST "$URL" \
  -H "Content-Type: application/json" \
  -H "X-Signature: sha256=$SIG" \
  -d "$BODY" | cat
echo

