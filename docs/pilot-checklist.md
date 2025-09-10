### Pilot Rollout Checklist (One Page)

This checklist guides a limited-scope pilot to validate functionality, operability, and support readiness before general availability.

### 1) Scope & Stakeholders
- **Define pilot goals**: success metrics, must-pass tests, and no-go criteria
- **Select pilot users/systems**: size, environments, any exclusions
- **Assign DRI/contacts**: engineering, SRE, security, support, product owner

### 2) Environment & Configuration
- **Provision staging**: endpoints reachable from pilot systems
- **Secrets set**: `JWT_SECRET`, `SESSION_SECRET`, `ENCRYPTION_KEY_BASE64`, webhook secrets
- **Connectivity**: firewall rules, DNS, TLS certs valid during pilot window
- **Observability**: logs, metrics, traces wired (Sentry/OTel), alert routing

### 3) Data Stores & Dependencies
- **Database**: schema migrated, backups enabled, access least-privileged
- **Cache/Queue**: Redis configured, auth required, eviction policy set
- **Email/Notifications**: SMTP or provider creds validated; from addresses confirmed

### 4) Integrations (Monitoring Systems)
- **LibreNMS webhook**: test with sample cURL; verify auth and parsing
  - Endpoint: `/webhooks/librenms`, header `X-Webhook-Secret`
  - Validate alert create/update/resolve flow, deduping, and idempotency
  - Confirm device/port metadata mapping
- **Zabbix webhook**: test with sample cURL; verify auth and parsing
  - Endpoint: `/webhooks/zabbix`, header `X-Webhook-Secret`
  - Validate PROBLEM → OK lifecycle and severity mapping

### 5) Functional Test Plan
- **Happy paths**: create, update, resolve alerts; verify notifications
- **Edge cases**: duplicate events, missing fields, large payloads, time skew
- **Security**: reject bad secrets, invalid signatures, oversized payloads
- **Performance**: baseline latency and throughput under expected load

### 6) Ops Runbook
- **On-call guide**: how to identify, mitigate, escalate
- **Dashboards**: links to logs/metrics/traces
- **SLOs/Alerts**: thresholds, paging policy, runbooks linked from alerts

### 7) Rollout Plan
- **Change window**: start/end, maintenance policies
- **Feature flag/rollback**: toggles, safe defaults, rollback script
- **Comms plan**: notify pilot users before/after, support channels

### 8) Exit Criteria & Handover
- **Success metrics met**: error budget, functional pass, user sign-off
- **Docs updated**: architecture, README, env templates, runbook
- **Postmortem**: capture findings, decide GA/iterate/stop

