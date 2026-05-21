"""GitHub API — README fetcher with content truncation."""

from __future__ import annotations

import requests

from ..models.repo import RepoRef
from ..storage.artifacts import read_text, write_text
from ..storage.cache import is_cached
from ..storage.paths import RepoPaths

GITHUB_API = "https://api.github.com"
HEADERS_TEMPLATE = {
    "Accept": "application/vnd.github.raw+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def fetch_readme(
    ref: RepoRef,
    paths: RepoPaths,
    branch: str = "main",
    max_chars: int = 30_000,
    token: str | None = None,
    force: bool = False,
) -> str:
    """Fetch README content, caching and truncating as needed."""
    if not force and is_cached(paths.readme_file):
        return read_text(paths.readme_file)

    headers = dict(HEADERS_TEMPLATE)
    if token:
        headers["Authorization"] = f"Bearer {token}"

    resp = requests.get(
        f"{GITHUB_API}/repos/{ref.full_name}/readme",
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()

    # With Accept: application/vnd.github.raw+json, response is raw content directly
    text = resp.text

    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n...[truncated]"

    paths.ensure()
    write_text(paths.readme_file, text)
    return text
