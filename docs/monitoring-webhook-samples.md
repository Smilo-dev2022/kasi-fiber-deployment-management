### Monitoring Webhook cURL Samples

Use these examples to test inbound webhooks from LibreNMS and Zabbix against your service.

- Replace placeholders: <STAGING_URL>, <PROD_URL>, <LIBRENMS_SECRET>, <ZABBIX_SECRET>.
- Header used for shared secret: `X-Webhook-Secret`.
- Content type: `application/json`.

### LibreNMS → Service Webhook

Example endpoint:
- Staging: <STAGING_URL>/webhooks/librenms
- Production: <PROD_URL>/webhooks/librenms

Example cURL (staging):
```bash
curl -X POST \
  -H 'Content-Type: application/json' \
  -H 'X-Webhook-Secret: <LIBRENMS_SECRET>' \
  '<STAGING_URL>/webhooks/librenms' \
  -d '{
    "id": 12345,
    "rule_id": 23,
    "hostname": "core-sw1.example.com",
    "sysName": "core-sw1",
    "device_id": 12,
    "severity": "critical",
    "state": "raised",
    "title": "Interface down: core-sw1 Gi0/1",
    "timestamp": 1731260400,
    "rule": "Port status down",
    "links": {
      "device": "https://librenms.example.com/device/device=12",
      "alert": "https://librenms.example.com/alert/12345"
    },
    "faults": [
      {
        "port_id": 104,
        "ifName": "Gi0/1",
        "ifDescr": "Gi0/1",
        "ifAlias": "Uplink to edge",
        "msg": "ifOperStatus down"
      }
    ],
    "tags": [
      {"tag": "service", "value": "network"},
      {"tag": "env", "value": "staging"}
    ]
  }'
```

Notes:
- Payload shape may vary based on your LibreNMS alert template/macros; adjust as needed.

### Zabbix → Service Webhook

Example endpoint:
- Staging: <STAGING_URL>/webhooks/zabbix
- Production: <PROD_URL>/webhooks/zabbix

Example cURL (staging):
```bash
curl -X POST \
  -H 'Content-Type: application/json' \
  -H 'X-Webhook-Secret: <ZABBIX_SECRET>' \
  '<STAGING_URL>/webhooks/zabbix' \
  -d '{
    "event_id": "67890",
    "event_value": "1",
    "severity": "High",
    "datetime": "2025-09-10T12:34:56Z",
    "host": {
      "name": "app-01",
      "ip": "10.0.0.12",
      "groups": ["Linux servers"],
      "tags": [{"tag": "env", "value": "staging"}, {"tag": "service", "value": "web"}]
    },
    "trigger": {
      "id": "20045",
      "name": "Free disk space is less than 10% on {HOST.NAME}",
      "status": "PROBLEM"
    },
    "items": [
      {
        "itemid": "30001",
        "name": "Free disk space on /",
        "key": "vfs.fs.size[/,free]",
        "value": "1024",
        "units": "MB"
      }
    ]
  }'
```

Notes:
- Zabbix webhook payloads are customizable via Media types; adapt keys/fields to your template.

### Headers and Secrets

- Provide the shared secret via header `X-Webhook-Secret`.
- Match the value with your environment variables:
  - Staging: `LIBRENMS_WEBHOOK_SHARED_SECRET`, `ZABBIX_WEBHOOK_SHARED_SECRET`
  - Production: `LIBRENMS_WEBHOOK_SHARED_SECRET`, `ZABBIX_WEBHOOK_SHARED_SECRET`

