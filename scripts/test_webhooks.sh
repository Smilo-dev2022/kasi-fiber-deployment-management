#!/usr/bin/env bash
set -euo pipefail

URL_LIBRENMS=${URL_LIBRENMS:-"http://127.0.0.1:8000/webhooks/librenms"}
URL_ZABBIX=${URL_ZABBIX:-"http://127.0.0.1:8000/webhooks/zabbix"}

SECRET_LIBRENMS=${SECRET_LIBRENMS:-"replace_with_WEBHOOK_HMAC_LIBRENMS"}
SECRET_ZABBIX=${SECRET_ZABBIX:-"replace_with_WEBHOOK_HMAC_ZABBIX"}

function hmac_sha256_hex() {
  local body="$1"
  local secret="$2"
  printf '%s' "$body" | openssl dgst -sha256 -hmac "$secret" -binary | xxd -p -c 256
}

echo "== LibreNMS alert =="
BODY_LIBRENMS='{"hostname":"OLT-01","severity":"critical","rule":"Device Down","alert_id":12345,"state":"alert","msg":"OLT-01 no response"}'
SIG=$(hmac_sha256_hex "$BODY_LIBRENMS" "$SECRET_LIBRENMS")
curl -s -X POST "$URL_LIBRENMS" \
  -H "Content-Type: application/json" \
  -H "X-Signature: sha256=$SIG" \
  -d "$BODY_LIBRENMS" | cat
echo

echo "== Zabbix alert =="
BODY_ZABBIX='{"host":"OLT-01","severity":"High","event_id":"8888","problem":true,"name":"PON1 LOS","message":"ONU flaps on PON1"}'
SIG=$(hmac_sha256_hex "$BODY_ZABBIX" "$SECRET_ZABBIX")
curl -s -X POST "$URL_ZABBIX" \
  -H "Content-Type: application/json" \
  -H "X-Signature: sha256=$SIG" \
  -d "$BODY_ZABBIX" | cat
echo

echo "== Zabbix clear =="
BODY_ZABBIX_CLEAR='{"host":"OLT-01","severity":"High","event_id":"8888","problem":false,"name":"PON1 LOS clear","message":"Recovered"}'
SIG=$(hmac_sha256_hex "$BODY_ZABBIX_CLEAR" "$SECRET_ZABBIX")
curl -s -X POST "$URL_ZABBIX" \
  -H "Content-Type: application/json" \
  -H "X-Signature: sha256=$SIG" \
  -d "$BODY_ZABBIX_CLEAR" | cat
echo

echo "Done. Override URLs or secrets via env vars: URL_LIBRENMS, URL_ZABBIX, SECRET_LIBRENMS, SECRET_ZABBIX"

