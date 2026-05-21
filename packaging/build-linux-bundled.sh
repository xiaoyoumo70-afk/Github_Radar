#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="$(grep -m1 '^version[[:space:]]*=' "$ROOT/pyproject.toml" | sed -E 's/.*"([^"]+)".*/\1/')"
NAME="github-radar-${VERSION}-linux-x64-bundled"
BUILD="$ROOT/dist/$NAME"
RUNTIME="$BUILD/runtime"
rm -rf "$BUILD"
mkdir -p "$BUILD" "$RUNTIME"

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

# ── Bundle Node.js runtime ───────────────────────────────────────────
NODE_BIN="$(command -v node)"
mkdir -p "$RUNTIME/node/bin" "$RUNTIME/node/lib"
cp "$NODE_BIN" "$RUNTIME/node/bin/node"
chmod +x "$RUNTIME/node/bin/node"
ldd "$NODE_BIN" | awk '/=> \/|^\// {for(i=1;i<=NF;i++) if ($i ~ /^\//) print $i}' | sort -u | while read -r lib; do
  cp -L "$lib" "$RUNTIME/node/lib/" 2>/dev/null || true
done

# ── Bundle Python runtime from current host ──────────────────────────
PY_BIN="$(command -v python3.11 || command -v python3)"
PY_VER="$($PY_BIN - <<'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
PY
)"
PY_BASE="$RUNTIME/python"
mkdir -p "$PY_BASE/bin" "$PY_BASE/lib/python${PY_VER}/site-packages"
cp "$PY_BIN" "$PY_BASE/bin/python"
chmod +x "$PY_BASE/bin/python"

STD_LIB="$($PY_BIN - <<'PY'
import sysconfig
print(sysconfig.get_path('stdlib'))
PY
)"
mkdir -p "$PY_BASE/lib/python${PY_VER}"
rsync -a --exclude '__pycache__' --exclude 'test' --exclude 'tests' --exclude 'idlelib' --exclude 'tkinter' "$STD_LIB/" "$PY_BASE/lib/python${PY_VER}/"

ldd "$PY_BIN" | awk '/=> \/|^\// {for(i=1;i<=NF;i++) if ($i ~ /^\//) print $i}' | sort -u | while read -r lib; do
  cp -L "$lib" "$PY_BASE/lib/" 2>/dev/null || true
done

# Copy only runtime packages required by pyproject and their deps.
$PY_BIN - <<PY
from pathlib import Path
import importlib, shutil, sys
out = Path('$PY_BASE/lib/python${PY_VER}/site-packages')
mods = [
  'pydantic','pydantic_core','pydantic_settings','dotenv','typer','rich','requests',
  'click','shellingham','typing_extensions','annotated_types','annotated_doc',
  'typing_inspection','certifi','charset_normalizer','idna','urllib3','markdown_it',
  'pygments','mdurl'
]
for m in mods:
    try:
        mod = importlib.import_module(m)
    except Exception as e:
        print(f'[WARN] missing {m}: {e}', file=sys.stderr); continue
    src = Path(mod.__file__).resolve()
    if src.name == '__init__.py':
        src = src.parent
        dst = out / src.name
        if dst.exists(): shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__','*.pyc','tests','test'))
    else:
        shutil.copy2(src, out / src.name)
    # Copy dist-info if available for package metadata.
    top = src.name if src.is_dir() else src.stem
    site = src.parent if src.is_file() else src.parent
    candidates = [p for p in site.glob('*.dist-info') if p.name.lower().replace('-','_').startswith(top.lower().replace('-','_').split('.')[0])]
    for di in candidates:
        dd = out / di.name
        if not dd.exists(): shutil.copytree(di, dd, ignore=shutil.ignore_patterns('RECORD'))
print('python runtime packages copied')
PY

cat > "$BUILD/GitHub-Radar.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PORT="${PORT:-4420}"
export PY_VER="$(ls "$APP_DIR/runtime/python/lib" | grep '^python' | head -1 | sed 's/python//')"
export PYTHONHOME="$APP_DIR/runtime/python"
export PYTHONPATH="$APP_DIR:$APP_DIR/runtime/python/lib/python${PY_VER}/site-packages"
export LD_LIBRARY_PATH="$APP_DIR/runtime/node/lib:$APP_DIR/runtime/python/lib:${LD_LIBRARY_PATH:-}"
export PATH="$APP_DIR/runtime/node/bin:$APP_DIR/runtime/python/bin:$PATH"
cd "$APP_DIR"
xdg-open "http://localhost:${PORT}" >/dev/null 2>&1 || true
exec "$APP_DIR/runtime/node/bin/node" "$APP_DIR/server.mjs"
SH
chmod +x "$BUILD/GitHub-Radar.sh"

cat > "$BUILD/github-radar-cli.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PY_VER="$(ls "$APP_DIR/runtime/python/lib" | grep '^python' | head -1 | sed 's/python//')"
export PYTHONHOME="$APP_DIR/runtime/python"
export PYTHONPATH="$APP_DIR:$APP_DIR/runtime/python/lib/python${PY_VER}/site-packages"
export LD_LIBRARY_PATH="$APP_DIR/runtime/python/lib:${LD_LIBRARY_PATH:-}"
export PATH="$APP_DIR/runtime/python/bin:$PATH"
cd "$APP_DIR"
exec "$APP_DIR/runtime/python/bin/python" -c 'from app.cli import main; main()' "$@"
SH
chmod +x "$BUILD/github-radar-cli.sh"

cat > "$BUILD/README-FIRST.md" <<'MD'
# GitHub Radar Linux Bundled

This build bundles the runtime environment:

- Node.js runtime for the UI/API server
- Python interpreter + standard library
- Python dependencies used by GitHub Radar

## Run UI

```bash
./GitHub-Radar.sh
```

Open: http://localhost:4420

## Run CLI

```bash
./github-radar-cli.sh --help
```

## Configure

Copy `.env.example` to `.env` and fill in `GITHUB_TOKEN`, `LLM_BASE_URL`, `LLM_MODEL`, `OBSIDIAN_VAULT`.

Secrets and analyzed artifacts are intentionally not bundled.

## Compatibility note

Linux x64 glibc bundle built from the current host runtime. For maximum portability, build on the oldest Linux distribution you intend to support.
MD

(cd "$ROOT/dist" && tar -czf "$NAME.tar.gz" "$NAME")
echo "$ROOT/dist/$NAME.tar.gz"
