#!/usr/bin/env sh
set -eu

mkdir -p /data/artifacts /data/vaults/AI-Vault

if [ ! -f /data/.env ]; then
  cp /app/.env.example /data/.env
fi

export PATH="/opt/github-radar-venv/bin:$PATH"
export PYTHONPATH="/app"

exec "$@"
