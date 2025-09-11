# Database & Supabase Security

## Principles
- `SERVICE_ROLE` key is CI-only; never client-side
- Enforce RLS on all tables with policies
- Rotate secrets/keys regularly
- No direct DB credentials to contractors; use APIs and migrations only

## Migrations from CI
- Alembic:
```bash
alembic upgrade head
```
- Supabase (if used):
```bash
npx --yes supabase db push
```
- Store SQL changelogs; review via PR with CODEOWNERS

## CI Variables
- `DATABASE_URL` set via environment/secret store
- `SUPABASE_ACCESS_TOKEN` and `SUPABASE_PROJECT_REF` as repo secrets (optional)

## Verification
- Run `select 1` on startup (see `app/main.py`)
- Add smoke tests for critical write paths