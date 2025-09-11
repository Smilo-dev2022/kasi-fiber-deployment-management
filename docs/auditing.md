# Auditing

- Log every deploy with git SHA, actor, and image digest
- Log artifact downloads/pulls from the registry (GHCR/ECR)
- Enable GitHub audit log and review weekly

## GitHub Actions Job Summary
- Jobs should emit the SHA, image tags, and actor to the summary

## Registry Logs
- GHCR: enable packages visibility and review downloads
- ECR: use CloudTrail/CloudWatch metrics and alerts on unusual pulls