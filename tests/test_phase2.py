"""Tests for Phase 2 — deduplication and digest rendering."""

import tempfile
from pathlib import Path
from github_radar.models.repo import RepoRef
from github_radar.discover.deduplicate import deduplicate


class TestDeduplicate:
    def test_no_seen_repos(self):
        refs = [
            RepoRef(owner="a", name="x"),
            RepoRef(owner="b", name="y"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            result = deduplicate(refs, Path(tmp))
            assert len(result) == 2
            assert result[0].full_name == "a/x"

    def test_some_seen(self):
        refs = [
            RepoRef(owner="a", name="x"),
            RepoRef(owner="b", name="y"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            # Create artifact dir for a__x
            (Path(tmp) / "repos" / "a__x").mkdir(parents=True)
            result = deduplicate(refs, Path(tmp))
            assert len(result) == 1
            assert result[0].full_name == "b/y"
