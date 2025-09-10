### Architecture: Multi-tenant, White-label SaaS

- Default model: single Postgres DB, shared tables with `tenant_id` + RLS
- Alternative: per-tenant schema or per-tenant DB (trade-offs below)

RLS enforcement pattern

1) Every multi-tenant table has `tenant_id uuid not null` referencing `tenants(id)`
2) Enable RLS and create policies `USING tenant_id = current_tenant_uuid()`
3) Per-request, set `SET LOCAL app.current_tenant = '<uuid>'` in the connection
4) Reject requests if Host/JWT tenant mismatch

Domain resolution

- `tenant_domains(domain)->tenant_id`; fall back to JWT `tenant_id` if no host match

JWT contract

- `{ sub, tenant_id, role }` signed with `JWT_SECRET`

Custom domains & TLS

- Use wildcard `*.yourdomain.com` for starter; for custom domains, automate DNS validation and ACM/LE issuance. See `docs/domains-tls.md`.

Data isolation choices

- Single DB + RLS: simplest ops, strongest ergonomics, requires strict tests
- Schema per tenant: better blast-radius; requires per-schema migrations
- DB per tenant: strongest isolation; cost/ops overhead

