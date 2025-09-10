### One-page pilot checklist

- **Objectives defined**: success criteria, scope, in/out of scope, owners.
- **Environments ready**: `staging` and `production` exist; URLs documented.
- **Config templated**: `.env.staging.example` and `.env.production.example` filled with secret names.
- **Secrets provisioned**: entries created in secret manager; least-privilege IAM; rotation plan.
- **Networking**: firewall rules, ingress allowlists, egress needs, outbound proxies if any.
- **TLS and domains**: certificates valid (auto-renew), root/intermediate chains tested.
- **AuthN/AuthZ**: tokens/keys created, scopes set, service accounts mapped.
- **Monitoring**: logs, metrics, traces wired; dashboards created; alerting thresholds set.
- **Webhooks tested**: LibreNMS and Zabbix sample curls succeed (2xx) and are processed end-to-end.
- **Data handling**: PII review done; retention, redaction, and backups documented.
- **SLOs and runbooks**: SLOs published; on-call runbook covers alerts, rollback, and mitigation steps.
- **Chaos/dry run**: simulate failures (network, auth, 5xx) and validate alerts/rollback.
- **Rollout plan**: pilot tenant list, timeline, comms plan, and opt-out path.
- **Rollback plan**: clear steps, data implications, and ownership.
- **Sign-off**: security, compliance, and stakeholder approvals recorded.

