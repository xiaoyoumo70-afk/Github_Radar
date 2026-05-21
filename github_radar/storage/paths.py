"""Unified path management for repo artifacts.

Every artifact path is derived from RepoRef.safe_name — no string
splices scattered across modules.
"""

from __future__ import annotations

from pathlib import Path

from ..models.repo import RepoRef


class RepoPaths:
    """Standardized path layout for a single repo's cached artifacts."""

    def __init__(self, root: Path, ref: RepoRef):
        self.root = root
        self.ref = ref
        self._dir: Path | None = None

    @property
    def dir(self) -> Path:
        if self._dir is None:
            self._dir = self.root / self.ref.safe_name
        return self._dir

    def ensure(self) -> None:
        """Create all standard subdirectories."""
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / "analyses").mkdir(exist_ok=True)
        (self.dir / "checkpoints").mkdir(exist_ok=True)
        (self.dir / "obsidian").mkdir(exist_ok=True)

    # -- source data --
    @property
    def metadata_file(self) -> Path:
        return self.dir / "metadata.json"

    @property
    def readme_file(self) -> Path:
        return self.dir / "readme.md"

    @property
    def tree_file(self) -> Path:
        return self.dir / "tree.json"

    @property
    def selected_files(self) -> Path:
        return self.dir / "selected_files.json"

    # -- analyses --
    @property
    def snapshot_file(self) -> Path:
        return self.dir / "analyses" / "snapshot.json"

    @property
    def structure_file(self) -> Path:
        return self.dir / "analyses" / "structure.json"

    @property
    def synthesis_file(self) -> Path:
        return self.dir / "analyses" / "final_synthesis.json"

    # -- checkpoints --
    @property
    def task_state_file(self) -> Path:
        return self.dir / "checkpoints" / "task_state.json"

    def phase_checkpoint(self, phase: str) -> Path:
        return self.dir / "checkpoints" / f"{phase}.done.json"

    # -- obsidian --
    @property
    def note_path_file(self) -> Path:
        return self.dir / "obsidian" / "note_path.txt"

    @property
    def last_write_file(self) -> Path:
        return self.dir / "obsidian" / "last_write.json"
