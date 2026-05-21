"""Tests for path management."""

import tempfile
from pathlib import Path
from github_radar.models.repo import RepoRef
from github_radar.storage.paths import RepoPaths


class TestRepoPaths:
    def test_dir_structure(self):
        ref = RepoRef(owner="test", name="repo")
        with tempfile.TemporaryDirectory() as tmp:
            paths = RepoPaths(Path(tmp), ref)
            paths.ensure()
            assert paths.dir.exists()
            assert (paths.dir / "analyses").exists()
            assert (paths.dir / "checkpoints").exists()
            assert (paths.dir / "obsidian").exists()

    def test_metadata_path(self):
        ref = RepoRef(owner="test", name="repo")
        paths = RepoPaths(Path("/tmp"), ref)
        assert paths.metadata_file.name == "metadata.json"
        assert "test__repo" in str(paths.metadata_file)
