# Hardened App Repository Template

This repository template ships Docker images only, with strict access controls and CI/CD best practices.

Key properties:
- Private repository; forking disabled; GitHub Pages disabled
- Branch protection on `main`: required reviews, checks, signed commits
- CI builds and pushes images to `ghcr.io` (or ECR)
- Secrets scanning and Dependabot alerts enabled

## Quick start

1. Replace `Dockerfile` with your app build and runtime.
2. Configure GitHub secrets/variables as needed:
   - `AWS_OIDC_ROLE_ARN`, `AWS_REGION` (if using ECR)
   - `RELEASE_VERSION` (optional) for semver tags
3. Push to `main` to build and publish images.

## Security hardening

Run the repo hardening script to enforce settings (requires the GitHub CLI `gh` and a token with admin:repo):

```bash
make harden OWNER=<org> REPO=<repo> BRANCH=main
```

See `scripts/harden_repo.sh` for details.

## Distribution model

- Deliver Docker images only from your registry
- Share integration artifacts in a separate repository (see `../integration` template)

