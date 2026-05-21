"""Task state models for checkpoint and resume."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class TaskStatus(str, Enum):
    queued = "queued"
    running = "running"
    failed = "failed"
    completed = "completed"


class TaskPhase(str, Enum):
    init = "init"
    metadata = "metadata"
    readme = "readme"
    tree = "tree"
    content_select = "content_select"
    snapshot = "snapshot"
    structure = "structure"
    synthesis = "synthesis"
    obsidian_write = "obsidian_write"
    completed = "completed"


class TaskState(BaseModel):
    """Persistent task state writable to checkpoint."""

    task_id: str
    mode: str = "repo"  # "repo" | "topic"
    status: TaskStatus = TaskStatus.queued
    phase: TaskPhase = TaskPhase.init
    repo: str | None = None
    query: str | None = None
    created_at: str = ""
    updated_at: str = ""
    error: str | None = None


# Ordered phases for sequential execution
PHASE_ORDER: list[TaskPhase] = [
    TaskPhase.init,
    TaskPhase.metadata,
    TaskPhase.readme,
    TaskPhase.tree,
    TaskPhase.content_select,
    TaskPhase.snapshot,
    TaskPhase.structure,
    TaskPhase.synthesis,
    TaskPhase.obsidian_write,
    TaskPhase.completed,
]
