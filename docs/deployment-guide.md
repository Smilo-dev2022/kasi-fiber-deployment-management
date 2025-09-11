# Deployment Guide

## Requirements
- Access to private registry (GHCR/ECR)
- Environment variables provided via secrets manager
- Database, Redis, object storage provisioned

## Environment Variables
- See `README.md` and `docs/secrets.md`
- Use `.env.staging` and `.env.prod` templates (not committed)

## Pull Images
```bash
docker pull ghcr.io/<org>/<repo>:<tag>
```

## Run Migrations
```bash
alembic upgrade head
# or supabase db push (if used)
```

## Deploy
- Use your orchestrator (Kubernetes, ECS, Nomad) to deploy images by tag
- Inject env vars and secrets
- Use environment-scoped deploy keys/roles (no shared keys)

## Audit
- Record git SHA, image tag, and operator identity per deploy
- Store logs centrally