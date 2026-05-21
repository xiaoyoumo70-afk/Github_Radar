# GitHub Radar container image
# Build:
#   docker build -t github-radar:0.1.0 .
# Run:
#   docker compose up -d

FROM node:22-bookworm-slim AS runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=4420 \
    GITHUB_RADAR_DATA_DIR=/data \
    ARTIFACTS_DIR=/data/artifacts \
    OBSIDIAN_VAULT_PATH=/data/vaults/AI-Vault

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      python3 \
      python3-pip \
      python3-venv \
      ca-certificates \
      curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./
COPY github_radar ./github_radar
COPY app ./app
COPY public ./public
COPY server.mjs ./server.mjs
COPY .env.example ./.env.example

RUN python3 -m venv /opt/github-radar-venv \
 && /opt/github-radar-venv/bin/pip install --no-cache-dir --upgrade pip \
 && /opt/github-radar-venv/bin/pip install --no-cache-dir -e .

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh \
 && mkdir -p /data/artifacts /data/vaults/AI-Vault

EXPOSE 4420
VOLUME ["/data"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD node -e "fetch('http://127.0.0.1:'+(process.env.PORT||4420)+'/api/settings').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

ENTRYPOINT ["/entrypoint.sh"]
CMD ["node", "/app/server.mjs"]
