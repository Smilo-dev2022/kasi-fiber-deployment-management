## Readiness Gates

This document enumerates pre-flight checks for staging and production and how to verify them.

- All migrations run in staging and prod: Visit `/ops/readiness` and ensure `alembic` is `ok`.
- Seed data present: `seeded_data` shows non-zero organizations, contracts, assignments.
- Webhooks HMAC and IP allowlist active: Set `NMS_HMAC_SECRET`, `NMS_ALLOW_IPS`. `/ops/readiness` -> `webhook_security: ok`.
- APScheduler jobs visible in logs: Scheduler logs jobs on start and `/ops/scheduler/jobs` lists jobs.
- Backups: Set `BACKUP_LAST_OK_TS` after successful run. `/ops/readiness` -> `backups`.
- CORS allowlist correct: Configure `CORS_ALLOW_ORIGINS`. `/ops/readiness` -> `cors`.
- File size and type guards: Configure `PHOTO_MAX_MB`, `PHOTO_ALLOWED_TYPES`. `/ops/readiness` -> `photo_guards_configured`.
- S3 lifecycle rules: Configure lifecycle on bucket. `/ops/readiness` -> `s3_lifecycle`.
- Test coverage: CI exports `LATEST_COVERAGE` >= 80.
- Routers present: tasks, photos, assets, reports, rates, pay-sheets, NOC, civils, technical, contracts, assignments, work-queue.
- Webhooks: LibreNMS, Zabbix with signature checks under `/webhooks`.
- Routing rules: Incident `due_at` set per contract, auto-assignment by scope.
- Permission tests: Ensure no cross-tenant access; require `X-Org-Id` where appropriate.
- Operational checks: NMS alerts reach staging; incidents auto-route with `due_at`; work-queue filters by assignments; photos pass EXIF and geofence; CAC and technical tests block invoices; pay sheets match rate cards.
- Performance: Key indexes exist (`idx_tasks_sla_due_at`, `idx_incidents_severity_opened`).
- Security: JWT secret per env; admin roles limited; audit trail; rate limits; secrets in Vault/SSM.
- Docs and runbooks: README, NOC playbooks, escalation matrix, pilot checklist, on-call rota.
- Go live steps: tag `v0.1.0`, deploy to staging, smoke, approve, deploy to prod, configure NMS, pilot, daily fixes.

