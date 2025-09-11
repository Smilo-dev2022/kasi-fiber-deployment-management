Use curl with HMAC
echo -n "$(cat integration/examples/webhooks/librenms.json)" | openssl dgst -sha256 -hmac "$HMAC" -binary | xxd -p -c 256 > sig.hex
SIG=$(cat sig.hex)
curl -X POST "$BASE/api/webhooks/librenms"
-H "X-Hub-Signature: sha256=$SIG"
-H "Content-Type: application/json"
--data-binary @integration/examples/webhooks/librenms.json

