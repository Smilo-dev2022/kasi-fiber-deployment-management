# Distribution Model (Images Only)

- Deliverables: Docker images only (no source)
- Registries: private `ghcr.io` and/or AWS ECR
- Access: grant image pull to environment-scoped identities (deploy keys, IRSA, workload identity)
- Versioning: semver tags on releases, plus immutable `sha-<gitsha>` tags
- Configuration: environment variables only; never distribute service keys or source
- Integration assets (separate repo): OpenAPI JSON, SDKs, config templates, Postman collection

## Environment Variables
- Provide `.env` templates per environment (staging/prod)
- Avoid embedding secrets in images; inject via secrets manager at deploy time

## Pulling Images
```bash
# GHCR (requires packages:read)
docker login ghcr.io -u <user> -p <token>
docker pull ghcr.io/<org>/<repo>:v1.2.3

# ECR (AWS credentials or OIDC)
aws ecr get-login-password --region <REGION> | docker login --username AWS --password-stdin <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com
docker pull <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/<name>:v1.2.3
```