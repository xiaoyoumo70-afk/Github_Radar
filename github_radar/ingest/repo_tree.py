"""GitHub API — recursive tree fetcher with structure analysis."""

from __future__ import annotations

import requests

from ..models.repo import RepoRef
from ..storage.artifacts import read_json, write_json
from ..storage.cache import is_cached
from ..storage.paths import RepoPaths

GITHUB_API = "https://api.github.com"
HEADERS_TEMPLATE = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# Patterns for classifying files
CONFIG_FILES = {
    "pyproject.toml", "setup.py", "setup.cfg", "Cargo.toml", "go.mod",
    "package.json", "tsconfig.json", "Makefile", "CMakeLists.txt",
    "Dockerfile", "docker-compose.yml", ".github/workflows",
}
DOC_DIRS = {"docs", "doc", "documentation"}
TEST_DIRS = {"tests", "test", "spec", "__tests__"}
EXAMPLE_DIRS = {"examples", "example", "demo", "samples"}


def fetch_tree(
    ref: RepoRef,
    paths: RepoPaths,
    branch: str = "main",
    token: str | None = None,
    force: bool = False,
) -> dict:
    """Fetch recursive git tree and produce a structured summary."""
    if not force and is_cached(paths.tree_file):
        return read_json(paths.tree_file)

    headers = dict(HEADERS_TEMPLATE)
    if token:
        headers["Authorization"] = f"Bearer {token}"

    resp = requests.get(
        f"{GITHUB_API}/repos/{ref.full_name}/git/trees/{branch}?recursive=1",
        headers=headers,
        timeout=45,
    )

    if resp.status_code == 404:
        # Try without recursive, then list top-level only
        resp = requests.get(
            f"{GITHUB_API}/repos/{ref.full_name}/git/trees/{branch}",
            headers=headers,
            timeout=30,
        )

    resp.raise_for_status()
    data = resp.json()
    entries = data.get("tree", [])

    # Build summary
    total_files = sum(1 for e in entries if e.get("type") == "blob")
    total_dirs = sum(1 for e in entries if e.get("type") == "tree")

    top_level_dirs: list[str] = []
    configs: list[str] = []
    doc_paths: list[str] = []
    entrypoint_paths: list[str] = []
    test_paths: list[str] = []
    example_paths: list[str] = []

    for e in entries:
        path_val = e.get("path", "")
        etype = e.get("type", "")

        if etype == "tree":
            parts = path_val.split("/")
            if len(parts) == 1:
                top_level_dirs.append(path_val)
                if parts[0].lower() in DOC_DIRS:
                    doc_paths.append(path_val)
                elif parts[0].lower() in TEST_DIRS:
                    test_paths.append(path_val)
                elif parts[0].lower() in EXAMPLE_DIRS:
                    example_paths.append(path_val)
            elif any(path_val.lower().startswith(d + "/") for d in DOC_DIRS):
                doc_paths.append(path_val)
        elif etype == "blob":
            fname = path_val.split("/")[-1]
            if fname in CONFIG_FILES or any(
                path_val.endswith(suf)
                for suf in ["/setup.py", "/setup.cfg", "CMakeLists.txt"]
            ):
                configs.append(path_val)
            # Heuristic entrypoints
            if fname in ("__init__.py", "__main__.py", "main.py", "app.py", "index.js",
                         "index.ts", "main.go", "main.rs", "server.py", "cli.py"):
                entrypoint_paths.append(path_val)

    result = {
        "repo": ref.full_name,
        "branch": branch,
        "total_files": total_files,
        "total_dirs": total_dirs,
        "top_level_dirs": top_level_dirs,
        "config_files": configs[:20],
        "doc_paths": doc_paths[:30],
        "entrypoint_paths": entrypoint_paths[:15],
        "test_paths": test_paths[:15],
        "example_paths": example_paths[:15],
        "fetched_at": __import__("time").strftime(
            "%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime()
        ),
    }

    paths.ensure()
    write_json(paths.tree_file, result)
    return result
