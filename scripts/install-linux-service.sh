#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT_DIR="$HOME/.config/systemd/user"
mkdir -p "$UNIT_DIR"
cat > "$UNIT_DIR/github-radar-ui.service" <<UNIT
[Unit]
Description=GitHub Radar Web UI
After=network.target

[Service]
Type=simple
WorkingDirectory=$APP_DIR
Environment=PORT=4420
ExecStart=/usr/bin/env node $APP_DIR/server.mjs
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
UNIT
systemctl --user daemon-reload
systemctl --user enable github-radar-ui
systemctl --user restart github-radar-ui
echo "GitHub Radar UI installed and running at http://localhost:4420"
