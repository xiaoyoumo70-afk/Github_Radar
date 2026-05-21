"""GitHub Search API wrapper."""

from __future__ import annotations

import requests

from ..models.repo import RepoRef

GITHUB_API = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def search_repos(
    query: str,
    token: str | None = None,
    sort: str = "stars",
    per_page: int = 20,
    language: str | None = None,
) -> list[dict]:
    """Search GitHub repositories.

    Args:
        query: Search keywords or topic.
        token: GitHub API token.
        sort: Sort field — stars, forks, updated.
        per_page: Results per page (max 100).
        language: Optional language filter.

    Returns list of raw repo dicts from GitHub API.
    """
    headers = dict(HEADERS)
    if token:
        headers["Authorization"] = f"Bearer {token}"

    q = query
    if language:
        q += f" language:{language}"

    params = {
        "q": q,
        "sort": sort,
        "order": "desc",
        "per_page": min(per_page, 100),
    }

    resp = requests.get(
        f"{GITHUB_API}/search/repositories",
        headers=headers,
        params=params,
        timeout=30,
    )

    if resp.status_code == 403 and "rate limit" in resp.text.lower():
        raise RuntimeError("GitHub API rate limit exceeded")
    resp.raise_for_status()

    return resp.json().get("items", [])


def search_to_refs(
    query: str,
    token: str | None = None,
    limit: int = 20,
) -> list[RepoRef]:
    """Search and return normalized RepoRef list."""
    items = search_repos(query, token=token, per_page=limit)
    refs = []
    for item in items:
        try:
            refs.append(RepoRef(owner=item["owner"]["login"], name=item["name"]))
        except (KeyError, TypeError):
            continue
    return refs
