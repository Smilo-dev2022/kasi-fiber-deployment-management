#!/usr/bin/env bash
set -euo pipefail

TAG=${1:-v0.1.0}
git tag -a "$TAG" -m "Release $TAG" && git push origin "$TAG"
echo "Tagged $TAG"

