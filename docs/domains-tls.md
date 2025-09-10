### Custom Domains and TLS

Mapping

- Map `tenant_domains.domain` to `tenants.id`. Resolve from `Host` header.

TLS

- Wildcard: issue `*.yourdomain.com` via ACM/Let’s Encrypt
- Custom: for `client.com`, use HTTP-01/ALB integration or DNS-01 with delegated `_acme-challenge` TXT

Ingress patterns

- CNAME `app.client.com` -> `edge.yourdomain.com`
- Terminate TLS at edge; route to app with `X-Forwarded-Host`

