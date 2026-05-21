# GitHub Radar Container Deployment

This is the recommended "open on a new machine" distribution path.

The container image includes:

- Node.js runtime for `server.mjs`
- Python runtime
- Python dependencies from `pyproject.toml`
- GitHub Radar app code and Web UI

It does **not** include secrets or user data:

- `.env`
- `.ui-settings.json`
- analyzed `artifacts/`
- personal Obsidian vault content

User data lives in `./data` on the host and is mounted to `/data` in the container.

## Run from source folder

Linux/macOS/WSL with Docker integration:

```bash
./scripts/docker-start.sh
```

Windows:

```bat
scripts\docker-start-windows.bat
```

Then open:

```text
http://localhost:4420
```

## Build and export an offline image

Linux:

```bash
./scripts/docker-build-save.sh
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\docker-build-save.ps1
```

Outputs:

```text
dist/github-radar-0.1.0-container-linux-amd64.tar
dist/github-radar-0.1.0-container-windows-docker.tar
```

Note: these are Docker image archives. They run as Linux containers on both Linux and Windows Docker Desktop.

## Install on a new machine from image tar

1. Install Docker Desktop / Docker Engine.
2. Copy the project folder or at least:
   - `docker-compose.yml`
   - `data/` if you already have user data
   - exported image tar
3. Load image:

```bash
docker load -i github-radar-0.1.0-container-linux-amd64.tar
```

4. Start:

```bash
docker compose up -d
```

5. Open:

```text
http://localhost:4420
```

## Data layout

Host:

```text
data/
├── .env
├── .ui-settings.json
├── artifacts/
└── vaults/
    └── AI-Vault/
```

Container:

```text
/data/.env
/data/.ui-settings.json
/data/artifacts/
/data/vaults/AI-Vault/
```

## LLM endpoint notes

Inside a container, `localhost` means the container itself, not the host machine.

If your LLM server runs on the host, use:

```text
http://host.docker.internal:5000/v1
```

The compose file already sets:

```yaml
LLM_BASE_URL: http://host.docker.internal:5000/v1
extra_hosts:
  - "host.docker.internal:host-gateway"
```

## Obsidian notes

By default the container reads Obsidian-style project notes from:

```text
/data/vaults/AI-Vault/Projects/GitHub Radar/Repos/*.md
```

To use a real host vault, mount it into the container and set `OBSIDIAN_VAULT_PATH`.

Example:

```yaml
volumes:
  - ./data:/data
  - /path/to/AI-Vault:/vaults/AI-Vault:ro
environment:
  OBSIDIAN_VAULT_PATH: /vaults/AI-Vault
```
