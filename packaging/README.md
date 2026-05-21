# GitHub Radar Packaging

This packaging layer creates portable and runtime-bundled Linux/Windows distributions without bundling private secrets.

## Package types

### 1. Portable code package

Smaller package. Requires user machine to already have Node.js and Python.

```bash
npm run package:linux
bash packaging/build-windows.sh
```

Outputs:

- `dist/github-radar-<version>-linux-x64.tar.gz`
- `dist/github-radar-<version>-windows-x64.zip`

### 2. Bundled runtime package

Larger package. Includes runtime environment.

Linux bundled build, from Linux/WSL:

```bash
npm run package:linux:bundled
# output: dist/github-radar-<version>-linux-x64-bundled.tar.gz
```

Windows bundled build, run on Windows PowerShell:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File packaging/build-windows-bundled.ps1
# output: dist/github-radar-<version>-windows-x64-bundled.zip
```

The Windows bundled builder downloads:

- Node.js Windows x64 portable ZIP
- Python embeddable Windows x64 ZIP
- Python runtime dependencies into embedded `Lib/site-packages`

## Runtime contents

Linux bundled package includes:

- `runtime/node/bin/node`
- `runtime/node/lib/*` shared libs copied from host
- `runtime/python/bin/python`
- `runtime/python/lib/pythonX.Y/*` stdlib
- `runtime/python/lib/pythonX.Y/site-packages/*` required runtime packages

Windows bundled package includes:

- `runtime/node/node.exe`
- `runtime/python/python.exe`
- `runtime/python/Lib/site-packages/*`

## Entrypoints

Linux bundled:

```bash
./GitHub-Radar.sh
./github-radar-cli.sh --help
```

Windows bundled:

```bat
GitHub-Radar.bat
github-radar-cli.bat --help
```

## Design

Current package type: **local desktop-like web app**.

- UI: `public/index.html`
- API server: `server.mjs` (Node.js built-ins only)
- Analysis CLI: Python package under `github_radar/` and `app/`
- User data: `artifacts/`
- Secrets: `.env` is excluded; use `.env.example`

## Security

The packagers intentionally exclude:

- `.env`
- `.ui-settings.json`
- analyzed `artifacts/`
- caches and bytecode

## Next upgrade path

For a true no-browser desktop UX:

1. Electron wrapper + electron-builder around this bundled runtime, or
2. Tauri wrapper if smaller package size matters, or
3. PyInstaller/PySide6 if UI is later rewritten around Python.

Recommendation: keep bundled runtime package as v0.1, then add Electron shell as v0.2.
