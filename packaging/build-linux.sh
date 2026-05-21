#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="$(grep -m1 '^version[[:space:]]*=' "$ROOT/pyproject.toml" | sed -E 's/.*"([^"]+)".*/\1/')"
NAME="github-radar-${VERSION}-linux-x64"
BUILD="$ROOT/dist/$NAME"
rm -rf "$BUILD"
mkdir -p "$BUILD"

copy() { rsync -a --delete "$1" "$2"; }

# Core app — deliberately exclude secrets, caches, generated dist.
# Core app — deliberately exclude secrets, caches, generated dist.
rsync -a \
  --exclude '.env' \
  --exclude '.ui-settings.json' \
  --exclude '.pytest_cache' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude 'dist' \
  --exclude 'artifacts' \
  "$ROOT/" "$BUILD/"

mkdir -p "$BUILD/artifacts"
cp "$ROOT/.env.example" "$BUILD/.env.example"

cat > "$BUILD/GitHub-Radar.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PORT="${PORT:-4420}"
cd "$APP_DIR"
if ! command -v node >/dev/null 2>&1; then
  echo "[GitHub Radar] Node.js is required. Please install Node.js 20+." >&2
  exit 1
fi
xdg-open "http://localhost:${PORT}" >/dev/null 2>&1 || true
exec node "$APP_DIR/server.mjs"
SH
chmod +x "$BUILD/GitHub-Radar.sh"

cat > "$BUILD/github-radar-cli.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"
if ! command -v python3 >/dev/null 2>&1; then
  echo "[GitHub Radar] Python 3.10+ is required." >&2
  exit 1
fi
export PYTHONPATH="$APP_DIR"
exec python3 -c 'from app.cli import main; main()' "$@"
SH
chmod +x "$BUILD/github-radar-cli.sh"

cat > "$BUILD/README-FIRST.md" <<'MD'
# GitHub Radar Linux Portable

## Requirements
- Node.js 20+
- Python 3.10+ for analysis CLI (`python -m app.cli ...`)
- Optional: Obsidian CLI if you want vault writeback

## Run UI
```bash
./scripts/github-radar-linux.sh
```
Then open: http://localhost:4420

## Install as user service
```bash
./scripts/install-linux-service.sh
```

## Configure
Copy `.env.example` to `.env` and fill in:
- `GITHUB_TOKEN`
- `LLM_BASE_URL`
- `LLM_MODEL`
- `OBSIDIAN_VAULT`

Secrets are intentionally not bundled.
MD

chmod +x "$BUILD/scripts/"*.sh
(cd "$ROOT/dist" && tar -czf "$NAME.tar.gz" "$NAME")
echo "$ROOT/dist/$NAME.tar.gz"
