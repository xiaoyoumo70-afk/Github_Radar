#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${PORT:-4420}"
cd "$APP_DIR"
export PORT
if ! command -v node >/dev/null 2>&1; then
  echo "[GitHub Radar] Node.js is required. Please install Node.js 20+." >&2
  exit 1
fi
xdg-open "http://localhost:${PORT}" >/dev/null 2>&1 || true
exec node server.mjs
