#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
IMAGE="${IMAGE:-github-radar:0.1.0}"

docker build -t "$IMAGE" .
mkdir -p dist
docker save "$IMAGE" -o dist/github-radar-0.1.0-container-linux-amd64.tar

echo "Built image: $IMAGE"
echo "Exported: dist/github-radar-0.1.0-container-linux-amd64.tar"
