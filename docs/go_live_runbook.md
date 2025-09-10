## Go Live Steps

1. Tag release `v0.1.0`
2. Deploy to staging; run `/healthz`, `/readyz`, `/ops/readiness` and smoke tests
3. Approve change; deploy to production
4. Configure NMS (LibreNMS/Zabbix) to production endpoints `/webhooks/*`
5. Start pilot in one ward for two weeks
6. Daily fixes and redeploys as needed

Post-pilot:
- Review KPIs and breaches
- Enable white-label tenants
- Add SSO if required
- Plan month 2 features

