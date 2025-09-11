# Security and Access Controls

This repository and release process are locked down to protect IP and customer data.

## Repository and GitHub Settings
- Private repository; forking disabled (no public forks)
- GitHub Pages disabled
- Use organization teams with least-privilege; no outside users with Maintainer
- Require SSO and org-wide 2FA (org setting)
- Branch protection on `main`:
  - Require PR with at least 1 review and CODEOWNERS
  - Require status checks (build) and linear history
  - Require signed commits and conversation resolution
- Secret scanning and Dependabot alerts enabled

## Distribution Model
- Ship Docker images only; no source distribution
- Push to a private registry (GHCR and/or ECR)
- Publish integration assets in a separate `integration` repo:
  - OpenAPI spec (JSON), SDKs, config templates, Postman collection
- Expose environment variables for configuration; never share service keys or code

## Build and Deploy
- GitHub Actions builds images and artifacts on merge to `main`
- Push images to `ghcr.io` and/or `ECR` with version and SHA tags
- Deploy from registry into cloud environments using environment-scoped deploy keys

## White-labeling (No Code Access)
- Theme via tenant settings: logo, colors, domain, PDFs
- Provide a `brand.json` per tenant; pipeline bakes assets at build time
- Partners use a portal to request theme changes; no repo access required

## Database and Supabase
- Keep `SERVICE_ROLE` keys in CI only; rotate regularly
- Run migrations from CI. Share SQL changelogs; do not grant write DB access
- Enforce RLS. Never give direct DB credentials to contractors

## Webhooks and Integrations
- Share webhook URLs, HMAC secrets, and field mappings
- Provide a Postman collection and example `curl` calls
- Reject unsigned requests or traffic from unknown IPs

## Temporary Contributions (Exceptional)
- Create a throwaway fork in the org with limited history
- Strip secrets and proprietary modules
- Require PRs to a staging branch with CODEOWNERS enforcement
- Remove access after merge and delete the fork

## Auditing
- Log every deploy with Git SHA and actor
- Log artifact downloads/usage from the registry
- Enable GitHub audit log and review weekly

## Legal and Procurement
- NDAs and IP assignment in place for any external work
- Statements of Work deliver images, APIs, and SLAs — not source code