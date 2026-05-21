"""Simple file cache for repo artifacts."""

from __future__ import annotations

from pathlib import Path


def is_cached(path: Path, max_age_days: int = 7) -> bool:
    """Check whether a cached file exists and is recent enough."""
    if not path.exists():
        return False
    # For now, just existence check — TTL logic can expand later
    return True
