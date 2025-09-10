# Runbook: Setup, Deploy, Operate

## Setup (Local)
- Start infra: `docker compose -f infra/docker-compose.yml up -d`
- Install deps: `pip install -r requirements.txt`
- Migrate: `alembic upgrade head`
- Seed: `psql "$DATABASE_URL" -f db/init/001_seed.sql`

## Deploy (Staging/Prod)
- Build image and push (CI/CD)
- Set env vars: `DATABASE_URL`, `CORS_ALLOW_ORIGINS`, `JWT_SECRET`, `NMS_ALLOW_IPS`, `NMS_HMAC_SECRET`, `S3_*`, `LOG_LEVEL`
- Run DB migrations: `alembic upgrade head`
- Smoke test: `./scripts/smoke.sh`

## Backups
- Nightly cron: `PGURL=... ./scripts/backup.sh /var/backups/app`
- Restore test: `PGURL=... ./scripts/restore.sh /var/backups/app/pg_backup_<ts>.sql.gz`

## S3 Lifecycle
- Apply `scripts/s3_lifecycle.json` via AWS CLI or MinIO console

## Scheduler Jobs
- Check: `GET /jobs`
- Logs: search for `job_*` entries

## Webhooks
- Restrict IPs via `NMS_ALLOW_IPS`
- Rotate `NMS_HMAC_SECRET` per environment

## Security
- Rotate `JWT_SECRET` per environment
- Minimum rate limits in place; adjust via code if needed