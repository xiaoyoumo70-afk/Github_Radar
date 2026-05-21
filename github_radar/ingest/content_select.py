"""Select files worth deep-reading based on tree structure."""

from __future__ import annotations

from ..models.repo import RepoRef
from ..storage.artifacts import read_json, write_json
from ..storage.cache import is_cached
from ..storage.paths import RepoPaths


def select_files(
    ref: RepoRef,
    paths: RepoPaths,
    max_file_chars: int = 20_000,
    force: bool = False,
) -> dict:
    """Select files for focused reading based on tree analysis."""
    if not force and is_cached(paths.selected_files):
        return read_json(paths.selected_files)

    tree = read_json(paths.tree_file)

    selected: list[dict] = []

    # Priority 1: README + docs entry points
    selected.append({
        "path": "README.md",
        "reason": "project overview",
        "priority": 1,
        "estimated_chars": 15000,
    })

    for dp in tree.get("doc_paths", [])[:5]:
        # Prefer index/getting-started/architecture
        if any(k in dp.lower() for k in ("index", "getting", "quick", "arch")):
            selected.append({
                "path": dp,
                "reason": "documentation entry point",
                "priority": 1,
                "estimated_chars": 8000,
            })

    # Priority 2: config files
    for cf in tree.get("config_files", [])[:3]:
        selected.append({
            "path": cf,
            "reason": "project configuration",
            "priority": 2,
            "estimated_chars": 5000,
        })

    # Priority 2: entrypoints
    for ep in tree.get("entrypoint_paths", [])[:5]:
        if ep not in {s["path"] for s in selected}:
            selected.append({
                "path": ep,
                "reason": "code entrypoint",
                "priority": 2,
                "estimated_chars": 8000,
            })

    total_est = sum(s["estimated_chars"] for s in selected)
    result = {
        "repo": ref.full_name,
        "selected": selected,
        "total_estimated_chars": total_est,
        "selected_count": len(selected),
    }

    paths.ensure()
    write_json(paths.selected_files, result)
    return result
