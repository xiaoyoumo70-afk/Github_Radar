"""Tests for Phase 4 — retrieval and relations."""

import tempfile
from pathlib import Path
from github_radar.memory.index import MemoryIndex
from github_radar.memory.relations import RelationGraph
from github_radar.models.repo import RepoRef


class TestRelationGraph:
    def test_find_clusters(self):
        with tempfile.TemporaryDirectory() as tmp:
            idx = MemoryIndex(Path(tmp))
            idx.index_repo(RepoRef(owner="a", name="x"), topics=["llm", "inference"])
            idx.index_repo(RepoRef(owner="b", name="y"), topics=["llm", "serving"])
            idx.index_repo(RepoRef(owner="c", name="z"), topics=["rust"])

            rg = RelationGraph(idx)
            clusters = rg.find_clusters()
            # llm cluster should have 2 repos
            llm_cluster = next((c for c in clusters if c["topic"] == "llm"), None)
            assert llm_cluster is not None
            assert llm_cluster["size"] == 2

    def test_get_graph(self):
        with tempfile.TemporaryDirectory() as tmp:
            idx = MemoryIndex(Path(tmp))
            idx.index_repo(RepoRef(owner="a", name="x"), topics=["llm"])
            idx.index_repo(RepoRef(owner="b", name="y"), topics=["llm"])
            idx.add_relation("a/x", "b/y", "related", "both llm")

            rg = RelationGraph(idx)
            g = rg.get_graph()
            assert len(g["nodes"]) == 2
            assert len(g["edges"]) == 1
            assert g["edges"][0]["source"] == "a/x"


class TestKnowledgeBase:
    def test_sync_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            from github_radar.discover.retrieval import KnowledgeBase
            from github_radar.models.config import Settings
            s = Settings(artifacts_dir=Path(tmp))
            kb = KnowledgeBase(s)
            assert kb.stats()["repo_count"] == 0
