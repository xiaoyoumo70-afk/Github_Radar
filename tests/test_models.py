"""Tests for core models."""

import pytest
from github_radar.models.repo import RepoRef


class TestRepoRef:
    def test_parse_owner_repo(self):
        ref = RepoRef.parse("vllm-project/vllm")
        assert ref.owner == "vllm-project"
        assert ref.name == "vllm"

    def test_parse_github_url(self):
        ref = RepoRef.parse("https://github.com/vllm-project/vllm")
        assert ref.owner == "vllm-project"
        assert ref.name == "vllm"

    def test_parse_trailing_slash(self):
        ref = RepoRef.parse("https://github.com/vllm-project/vllm/")
        assert ref.owner == "vllm-project"
        assert ref.name == "vllm"

    def test_parse_dot_git(self):
        ref = RepoRef.parse("https://github.com/vllm-project/vllm.git")
        assert ref.owner == "vllm-project"
        assert ref.name == "vllm"

    def test_parse_invalid(self):
        with pytest.raises(ValueError):
            RepoRef.parse("not-a-valid-ref")

    def test_full_name(self):
        ref = RepoRef(owner="a", name="b")
        assert ref.full_name == "a/b"

    def test_safe_name(self):
        ref = RepoRef(owner="a", name="b")
        assert ref.safe_name == "a__b"
