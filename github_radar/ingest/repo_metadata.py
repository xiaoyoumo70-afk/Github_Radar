"""GitHub API — repo metadata fetcher."""

from __future__ import annotations

import time

import requests

from ..models.repo import RepoRef, RepoMetadata
from ..storage.artifacts import read_json, write_json
from ..storage.cache import is_cached
from ..storage.paths import RepoPaths

GITHUB_API = "https://api.github.com"
HEADERS_TEMPLATE = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def fetch_metadata(
    ref: RepoRef,
    paths: RepoPaths,
    token: str | None = None,
    force: bool = False,
) -> RepoMetadata:
    """Fetch repo metadata, using cache when available."""
    if not force and is_cached(paths.metadata_file):
        return RepoMetadata.model_validate(read_json(paths.metadata_file))

    headers = dict(HEADERS_TEMPLATE)
    if token:
        headers["Authorization"] = f"Bearer {token}"

    resp = requests.get(
        f"{GITHUB_API}/repos/{ref.full_name}",
        headers=headers,
        timeout=30,
    )

    if resp.status_code == 404:
        raise ValueError(f"Repo not found: {ref.full_name}")
    if resp.status_code == 403 and "rate limit" in resp.text.lower():
        raise RuntimeError("GitHub API rate limit exceeded. Set GITHUB_TOKEN.")
    resp.raise_for_status()

    data = resp.json()
    meta = RepoMetadata(
        repo=ref.full_name,
        url=data.get("html_url", f"https://github.com/{ref.full_name}"),
        description=data.get("description"),
        language=data.get("language"),
        topics=data.get("topics", []),
        stars=data.get("stargazers_count"),
        forks=data.get("forks_count"),
        open_issues=data.get("open_issues_count"),
        default_branch=data.get("default_branch", "main"),
        license=data.get("license", {}).get("spdx_id") if data.get("license") else None,
        pushed_at=data.get("pushed_at"),
        fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )
    paths.ensure()
    write_json(paths.metadata_file, meta.model_dump())
    return meta
