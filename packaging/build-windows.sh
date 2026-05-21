#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="$(grep -m1 '^version[[:space:]]*=' "$ROOT/pyproject.toml" | sed -E 's/.*"([^"]+)".*/\1/')"
NAME="github-radar-${VERSION}-windows-x64"
BUILD="$ROOT/dist/$NAME"
rm -rf "$BUILD"
mkdir -p "$BUILD"

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

cat > "$BUILD/README-FIRST.md" <<'MD'
# GitHub Radar Windows Portable

## Requirements
- Node.js 20+
- Python 3.10+ for analysis CLI (`python -m app.cli ...`)
- Optional: Obsidian CLI if you want vault writeback

## Run UI
Double-click:

```bat
scripts\github-radar-windows.bat
```

Or run PowerShell:

```powershell
scripts\github-radar-windows.ps1
```

Then open: http://localhost:4420

## Configure
Copy `.env.example` to `.env` and fill in:
- `GITHUB_TOKEN`
- `LLM_BASE_URL`
- `LLM_MODEL`
- `OBSIDIAN_VAULT`

Secrets are intentionally not bundled.
MD

python3 - <<PY
from pathlib import Path
import zipfile, os
root = Path('$ROOT/dist')
build = root / '$NAME'
zip_path = root / '$NAME.zip'
if zip_path.exists(): zip_path.unlink()
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
    for p in sorted(build.rglob('*')):
        if p.is_symlink():
            target = os.readlink(p)
            if not p.exists():
                continue  # skip broken symlinks (common in node_modules/.bin)
        if '.bin' in p.parts:
            continue  # skip node_modules/.bin — symlinks not portable to Windows
        if p.is_file():
            z.write(p, p.relative_to(root))
print(zip_path)
PY
