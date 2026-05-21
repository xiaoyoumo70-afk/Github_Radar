"""Normalize user input into RepoRef."""

from __future__ import annotations

from ..models.repo import RepoRef


def parse_repo(raw: str) -> RepoRef:
    """Parse owner/repo string or GitHub URL into RepoRef.

    Raises ValueError for unparseable input.
    """
    return RepoRef.parse(raw)


def normalize_url(raw: str) -> str:
    """Normalize a GitHub URL to canonical form."""
    ref = RepoRef.parse(raw)
    return f"https://github.com/{ref.full_name}"


def try_parse_repo(raw: str) -> RepoRef | None:
    """Attempt to parse; return None on failure instead of raising."""
    try:
        return RepoRef.parse(raw)
    except ValueError:
        return None
