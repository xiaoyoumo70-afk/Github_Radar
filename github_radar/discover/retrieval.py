"""Retrieval layer — search and browse the indexed knowledge base."""

from __future__ import annotations

from pathlib import Path

from ..memory.index import MemoryIndex
from ..models.repo import RepoRef
from ..models.config import Settings


class KnowledgeBase:
    """High-level interface for querying the accumulated knowledge base."""

    def __init__(self, settings: Settings | None = None):
        if settings is None:
            settings = Settings()
        self.settings = settings
        self.index = MemoryIndex(settings.artifacts_dir)
        # Auto-index from existing artifacts
        self._sync_from_artifacts()

    def _sync_from_artifacts(self) -> None:
        """Scan artifacts dir and index any repo not yet in the index."""
        from ..storage.artifacts import read_json

        repos_dir = self.settings.artifacts_dir / "repos"
        if not repos_dir.exists():
            return

        for d in repos_dir.iterdir():
            if not d.is_dir():
                continue
            full_name = d.name.replace("__", "/", 1)
            if self.index.get_repo(full_name):
                continue  # Already indexed

            # Try to derive from metadata
            meta_file = d / "metadata.json"
            synth_file = d / "analyses" / "final_synthesis.json"
            if meta_file.exists():
                try:
                    meta = read_json(meta_file)
                    topics = meta.get("topics", [])
                    synthesis = {}
                    if synth_file.exists():
                        synthesis = read_json(synth_file)

                    self.index.index_repo(
                        ref=RepoRef.parse(full_name),
                        topics=topics,
                        language=meta.get("language"),
                        stars=meta.get("stars"),
                        summary_path=str(synth_file) if synth_file.exists() else None,
                        obsidian_note=f"Projects/GitHub Radar/Repos/{d.name}",
                    )
                except Exception:
                    continue

    def search(self, topic: str) -> list[dict]:
        """Search indexed repos by topic."""
        names = self.index.search_by_topic(topic)
        return [self.index.get_repo(n) for n in names if self.index.get_repo(n)]

    def list_repos(self) -> list[dict]:
        """List all indexed repos."""
        return list(self.index._data.get("repos", {}).values())

    def get_repo_detail(self, full_name: str) -> dict | None:
        """Get full repo entry from index."""
        return self.index.get_repo(full_name)

    def list_topics(self) -> list[str]:
        """List all known topics."""
        return sorted(self.index.list_topics())

    def stats(self) -> dict:
        """Return knowledge base statistics."""
        base = self.index.stats()
        # Count actual artifact dirs
        repos_dir = self.settings.artifacts_dir / "repos"
        if repos_dir.exists():
            base["artifact_dirs"] = sum(1 for d in repos_dir.iterdir() if d.is_dir())
        return base
