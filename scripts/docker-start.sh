#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required. Please install Docker Desktop or Docker Engine." >&2
  exit 1
fi

docker compose up -d --build

echo "GitHub Radar is starting: http://localhost:4420"
