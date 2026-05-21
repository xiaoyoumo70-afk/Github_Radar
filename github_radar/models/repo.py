"""Core domain models for repo and task state."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RepoRef(BaseModel):
    """Normalized GitHub repository reference."""

    owner: str
    name: str

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"

    @property
    def safe_name(self) -> str:
        return f"{self.owner}__{self.name}"

    @classmethod
    def parse(cls, raw: str) -> "RepoRef":
        """Parse owner/repo or GitHub URL into RepoRef.

        Supported forms:
            owner/repo
            https://github.com/owner/repo
            https://github.com/owner/repo/
            https://github.com/owner/repo.git
        """
        import re

        raw = raw.strip().rstrip("/").rstrip(".git")
        # GitHub URL
        m = re.match(r"^https?://github\.com/([^/]+)/([^/]+)/?$", raw)
        if m:
            return cls(owner=m.group(1), name=m.group(2))
        # owner/repo
        m = re.match(r"^([^/]+)/([^/]+)$", raw)
        if m:
            return cls(owner=m.group(1), name=m.group(2))
        raise ValueError(f"Cannot parse repo ref from: {raw!r}")


class RepoMetadata(BaseModel):
    """Cached GitHub repo metadata."""

    repo: str
    url: str
    description: str | None = None
    language: str | None = None
    topics: list[str] = Field(default_factory=list)
    stars: int | None = None
    forks: int | None = None
    open_issues: int | None = None
    default_branch: str = "main"
    license: str | None = None
    pushed_at: str | None = None
    fetched_at: str = ""
