#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PY="${PYTHON:-$(command -v python3.11 || command -v python3)}"
PY_VER="$($PY - <<'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
PY
)"

if [[ "$PY_VER" < "3.11" ]]; then
  echo "[WARN] Building sidecar with Python $PY_VER, but pyproject.toml declares >=3.11." >&2
  echo "[WARN] This is acceptable for local smoke tests only; release builds should use Python 3.11+." >&2
fi

if ! "$PY" -m PyInstaller --version >/dev/null 2>&1; then
  echo "[ERROR] PyInstaller is not installed for $PY." >&2
  echo "Install it first, preferably in a clean build venv:" >&2
  echo "  $PY -m pip install pyinstaller" >&2
  exit 2
fi

OUT="$ROOT/dist-sidecar/linux"
rm -rf "$OUT" "$ROOT/build/github-radar-cli" "$ROOT/github-radar-cli.spec"
mkdir -p "$OUT"

"$PY" -m PyInstaller \
  --clean \
  --onefile \
  --name github-radar-cli \
  --distpath "$OUT" \
  --workpath "$ROOT/build" \
  --paths "$ROOT" \
  --paths "$ROOT/github_radar/analyze" \
  --collect-submodules github_radar \
  --collect-submodules app \
  --hidden-import pydantic \
  --hidden-import pydantic_settings \
  --hidden-import dotenv \
  --hidden-import rich \
  --hidden-import typer \
  "$ROOT/desktop/python_sidecar_entry.py"

chmod +x "$OUT/github-radar-cli"
"$OUT/github-radar-cli" version

echo "$OUT/github-radar-cli"
