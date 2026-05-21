# GitHub Radar Desktop Packaging

Electron desktop packaging wraps the existing Web UI and local API server in a real desktop window.

## Current phase

Phase 1 is implemented:

- `desktop/main.js` starts the API server in-process.
- Electron opens `http://127.0.0.1:<free-port>` inside a desktop window.
- Runtime data is redirected to Electron's user data directory:
  - Windows: `%APPDATA%/GitHub Radar/`
  - Linux: `~/.config/GitHub Radar/`
  - macOS: `~/Library/Application Support/GitHub Radar/`
- Menu includes:
  - open data directory
  - reload UI
  - DevTools
  - zoom controls

Phase 2 is implemented:

- `desktop/python_sidecar_entry.py` calls `app.cli.main()` safely.
- `packaging/build-python-sidecar-linux.sh` builds `dist-sidecar/linux/github-radar-cli`.
- `packaging/build-python-sidecar-windows.ps1` builds `dist-sidecar/win/github-radar-cli.exe`.
- Electron resolves sidecar path from packaged resources or local `dist-sidecar/`.
- Server exposes:
  - `GET /api/runtime`
  - `POST /api/analyze-repo`

Phase 3 still needed for final release hardening:

- Build Linux sidecar with Python 3.11+ in a clean release environment.
- Build Windows sidecar on Windows with Python 3.11+.
- Build final electron-builder outputs and test on real clean machines.

## Development run

```bash
npm install
npm run desktop:dev
```

Or:

```bash
./packaging/build-electron-dev.sh
```

## Python sidecar build

Linux:

```bash
npm run sidecar:linux
# output: dist-sidecar/linux/github-radar-cli
```

Windows PowerShell:

```powershell
npm run sidecar:windows
# output: dist-sidecar/win/github-radar-cli.exe
```

Release builds should use Python 3.11+ because `pyproject.toml` declares `requires-python = ">=3.11"`.
Local smoke builds may work on Python 3.10, but should not be treated as official release artifacts.

## Linux desktop build

```bash
./packaging/build-electron-linux.sh
```

This builds the Linux sidecar first, then runs electron-builder.

Outputs under:

```text
dist-electron/
```

Expected targets:

- AppImage
- tar.gz

## Windows desktop build

Run on Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\build-electron-windows.ps1
```

Expected targets:

- NSIS installer
- zip

## Architecture

```text
Electron main process
  ├── chooses a free localhost port
  ├── sets env vars:
  │   ├── PORT
  │   ├── HOST=127.0.0.1
  │   ├── GITHUB_RADAR_DATA_DIR=<Electron userData>
  │   ├── ARTIFACTS_DIR=<Electron userData>/artifacts
  │   └── OBSIDIAN_VAULT_PATH=<Electron userData>/vaults/AI-Vault
  ├── imports ../server.mjs
  ├── starts server via startServer()
  └── opens BrowserWindow at local server URL
```

## Runtime API

The embedded server now exposes:

```text
GET  /api/runtime
POST /api/analyze-repo
```

Analyze request example:

```bash
curl -X POST http://127.0.0.1:4420/api/analyze-repo \
  -H 'Content-Type: application/json' \
  -d '{"repo":"owner/repo","force":false,"no_llm":false}'
```

`/api/analyze-repo` requires `GITHUB_RADAR_SIDECAR_PATH` to point to the PyInstaller executable. Electron sets this automatically when the sidecar exists.

## Important implementation detail

`server.mjs` now exports:

```js
export function startServer(options = {})
```

and only auto-starts when run directly from Node:

```bash
node server.mjs
```

This keeps the old web-server mode working while allowing Electron to embed the server.
