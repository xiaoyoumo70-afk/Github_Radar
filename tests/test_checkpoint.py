"""Tests for checkpoint mechanism."""

import tempfile
from pathlib import Path
from github_radar.models.repo import RepoRef
from github_radar.models.task import TaskPhase, TaskStatus
from github_radar.storage.paths import RepoPaths
from github_radar.memory.checkpoint import (
    create_task_state,
    load_task_state,
    update_task_phase,
    mark_phase_done,
    is_phase_done,
    get_next_pending_phase,
    mark_failed,
)


class TestCheckpoint:
    def _setup(self):
        ref = RepoRef(owner="test", name="check")
        tmp = tempfile.TemporaryDirectory()
        paths = RepoPaths(Path(tmp.name), ref)
        paths.ensure()
        return ref, paths, tmp

    def test_create_and_load(self):
        ref, paths, tmp = self._setup()
        state = create_task_state(paths, repo=ref.full_name)
        assert state.task_id.startswith("repo-test__check-")
        assert state.status == TaskStatus.running

        loaded = load_task_state(paths)
        assert loaded is not None
        assert loaded.task_id == state.task_id
        tmp.cleanup()

    def test_phase_checkpoint(self):
        ref, paths, tmp = self._setup()
        create_task_state(paths, repo=ref.full_name)
        assert not is_phase_done(paths, TaskPhase.metadata)

        mark_phase_done(paths, TaskPhase.metadata)
        assert is_phase_done(paths, TaskPhase.metadata)

        assert get_next_pending_phase(paths) == TaskPhase.readme
        tmp.cleanup()

    def test_failed_state(self):
        ref, paths, tmp = self._setup()
        state = create_task_state(paths, repo=ref.full_name)
        mark_failed(paths, "test error")

        loaded = load_task_state(paths)
        assert loaded is not None
        assert loaded.status == TaskStatus.failed
        assert loaded.error == "test error"
        tmp.cleanup()
