### LibreNMS sample payload and curl

Copy the JSON below into a file named `librenms_payload.json`, then run the curl command.

```bash
curl -sS -X POST "https://your-endpoint.example.com/webhooks/librenms" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  --data @librenms_payload.json | cat
```

```json
{
  "alert": {
    "state": "alert",
    "severity": "critical",
    "rule": "High CPU usage > 90%",
    "id": 12345,
    "name": "High CPU on host"
  },
  "device": {
    "hostname": "router-01.example.com",
    "sysName": "router-01",
    "device_id": 678,
    "os": "ios",
    "hardware": "ISR 4331"
  },
  "event": {
    "timestamp": "2025-09-10T12:34:56Z",
    "duration_sec": 300
  },
  "links": {
    "alert": "https://librenms.example.com/alerts/12345",
    "device": "https://librenms.example.com/device/device=678"
  },
  "notes": "Sample payload for testing"
}
```

---

### Zabbix sample payload and curl

Copy the JSON below into a file named `zabbix_payload.json`, then run the curl command.

```bash
curl -sS -X POST "https://your-endpoint.example.com/webhooks/zabbix" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  --data @zabbix_payload.json | cat
```

```json
{
  "eventid": "34567",
  "event_time": "2025-09-10T12:34:56Z",
  "event_severity": "High",
  "trigger": {
    "id": "2890",
    "name": "CPU usage is too high on {HOST.NAME}",
    "status": "PROBLEM"
  },
  "host": {
    "host": "db-01",
    "hostid": "10105",
    "ip": "10.0.0.10",
    "group": "Databases"
  },
  "item": {
    "key": "system.cpu.util[,idle]",
    "value": "5.2",
    "units": "%"
  },
  "links": {
    "event": "https://zabbix.example.com/tr_events.php?eventid=34567",
    "host": "https://zabbix.example.com/hosts.php?form=update&hostid=10105"
  },
  "notes": "Sample payload for testing"
}
```

