"""Tests for Phase 3 — handoff packets and memory index."""

import tempfile
from pathlib import Path
from github_radar.memory.handoff import (
    create_handoff,
    HandoffPacket,
    save_handoff,
    load_handoff,
)
from github_radar.memory.index import MemoryIndex
from github_radar.models.repo import RepoRef


class TestHandoff:
    def test_create_and_summary(self):
        packet = create_handoff(
            task_id="test-001",
            repo="test/repo",
            current_phase="focused_reading",
            completed_phases=["discover", "snapshot", "structure"],
            core_findings=["Finding A", "Finding B"],
            open_questions=["Q1?"],
            next_actions=["Read docs/", "Final synthesis"],
            artifact_refs=["artifacts/repos/test__repo/snapshot.json"],
        )
        assert packet.task_id == "test-001"
        assert "Finding A" in packet.summary()
        assert "test/repo" in packet.summary()

    def test_roundtrip(self):
        packet = create_handoff(
            task_id="test-002",
            repo="a/b",
            current_phase="synthesis",
            completed_phases=["snapshot", "structure"],
            core_findings=["X"],
            open_questions=[],
            next_actions=["Done"],
            artifact_refs=["f.json"],
        )
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "handoff.json"
            save_handoff(packet, p)
            loaded = load_handoff(p)
            assert loaded.task_id == "test-002"
            assert loaded.repo == "a/b"


class TestMemoryIndex:
    def test_index_and_search(self):
        with tempfile.TemporaryDirectory() as tmp:
            idx = MemoryIndex(Path(tmp))
            ref = RepoRef(owner="test", name="repo")
            idx.index_repo(ref, topics=["llm", "inference"], language="Python", stars=1000)
            results = idx.search_by_topic("llm")
            assert "test/repo" in results

    def test_stats(self):
        with tempfile.TemporaryDirectory() as tmp:
            idx = MemoryIndex(Path(tmp))
            ref = RepoRef(owner="a", name="b")
            idx.index_repo(ref, topics=["quantization"])
            stats = idx.stats()
            assert stats["repo_count"] == 1
            assert stats["topic_count"] == 1
