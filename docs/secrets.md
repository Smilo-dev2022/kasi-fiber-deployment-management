# Secrets Reference

## Staging Secret Names
- SECRET_STAGING_JWT
- SECRET_STAGING_JWT_ROTATE_NEXT
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
- SECRET_PROD_JWT_ROTATE_NEXT
- SECRET_PROD_HMAC_LIBRENMS
- SECRET_PROD_HMAC_ZABBIX
- SECRET_PROD_S3_ACCESS_KEY
- SECRET_PROD_S3_SECRET_KEY
- SECRET_PROD_NMS_ALLOW_IPS
- SECRET_PROD_CONFIGS_ALLOW_IPS
- SECRET_PROD_REDIS_URL
- SECRET_PROD_CORS_ALLOWED_ORIGINS
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

### JWT rotation
1. Store the next JWT secret in `*_JWT_ROTATE_NEXT`.
2. Update API to accept both current and next for a grace period.
3. Rotate clients to use tokens signed with the next secret.
4. Promote `*_JWT_ROTATE_NEXT` to `*_JWT` and clear the old.

### Helpful commands
- Generate hex secret: `openssl rand -hex 32`
- Validate HMAC locally: see `scripts/test_webhooks.sh`