# Secrets Reference

## Staging Secret Names
- SECRET_STAGING_JWT
- SECRET_STAGING_HMAC_LIBRENMS
- SECRET_STAGING_HMAC_ZABBIX
- SECRET_STAGING_SENTRY_DSN
- SECRET_STAGING_SMTP_USER
- SECRET_STAGING_SMTP_PASS
- SECRET_STAGING_OIDC_ISSUER
- SECRET_STAGING_OIDC_CLIENT_ID
- SECRET_STAGING_OIDC_CLIENT_SECRET

## Production Secret Names
- SECRET_PROD_DATABASE_URL
- SECRET_PROD_JWT
- SECRET_PROD_HMAC_LIBRENMS
- SECRET_PROD_HMAC_ZABBIX
- SECRET_PROD_S3_ACCESS_KEY
- SECRET_PROD_S3_SECRET_KEY
- SECRET_PROD_SENTRY_DSN
- SECRET_PROD_SMTP_HOST
- SECRET_PROD_SMTP_USER
- SECRET_PROD_SMTP_PASS
- SECRET_PROD_OIDC_ISSUER
- SECRET_PROD_OIDC_CLIENT_ID
- SECRET_PROD_OIDC_CLIENT_SECRET

## Guidance
- JWT and HMAC secrets: generate strong random values (e.g., 32+ bytes hex)
- S3 access/secret keys: from your object storage/credentials system
- Sentry DSN: from your Sentry project settings
- SMTP host/user/pass: from your email provider
- OIDC issuer/client ID/client secret: from your identity provider
- Database URL (prod): full DSN, e.g., `postgresql+psycopg2://user:pass@host:5432/dbname`

## Supabase
- SUPABASE_URL: project base URL (e.g., `https://bigbujrinohnmoxuidbx.supabase.co`)
- SUPABASE_ANON_KEY: anon public key (client-side allowed)
- SUPABASE_SERVICE_ROLE_KEY: service role key (server-only; never expose)
- SUPABASE_ACCESS_TOKEN (GitHub Secret): for CLI auth in CI; do not commit

### CI usage example
Add a repository secret named `SUPABASE_ACCESS_TOKEN` (Settings → Secrets and variables → Actions). The CI will login to Supabase only if the secret is present.

```yaml
- uses: actions/setup-node@v4
  if: ${{ secrets.SUPABASE_ACCESS_TOKEN != '' }}
  with:
    node-version: '20'
- name: Supabase login (optional)
  if: ${{ secrets.SUPABASE_ACCESS_TOKEN != '' }}
  env:
    SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
  run: npx --yes supabase@latest login --token "$SUPABASE_ACCESS_TOKEN"
```

## Helpful commands
- Generate hex secret: `openssl rand -hex 32`
- Validate HMAC locally: see `scripts/test_webhooks.sh`

## Rate limit tuning

- Per-IP webhook limits (FastAPI & Express):
  - `WEBHOOK_IP_LIMIT`, `WEBHOOK_IP_WINDOW`
- Per-org heavy writes (FastAPI):
  - `HEAVY_ORG_LIMIT`, `HEAVY_ORG_WINDOW`
  - `HEAVY_ORG_BYPASS_ROLES` (default `NOC`)