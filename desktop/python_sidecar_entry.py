"""PyInstaller sidecar entry for GitHub Radar Desktop.

This file intentionally calls app.cli.main() directly instead of relying on
`python -m app.cli`, because app/cli.py defines `main()` but does not execute it
when imported as a module.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _bootstrap_paths() -> None:
    """Make source-layout imports robust in dev and frozen builds."""
    if getattr(sys, "frozen", False):
        # PyInstaller onefile extracts bundled files to _MEIPASS.
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    else:
        base = Path(__file__).resolve().parents[1]

    candidates = [base, base / "github_radar", base / "app"]
    for p in candidates:
        s = str(p)
        if p.exists() and s not in sys.path:
            sys.path.insert(0, s)


def _normalize_env() -> None:
    """Map desktop/container data envs onto Python Settings env names."""
    data_dir = os.environ.get("GITHUB_RADAR_DATA_DIR")
    if data_dir:
        os.environ.setdefault("ARTIFACTS_DIR", str(Path(data_dir) / "artifacts"))


def main() -> None:
    _bootstrap_paths()
    _normalize_env()
    from app.cli import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()
