"""Task runner — orchestrates the full repo/topic analysis pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

from github_radar.models.repo import RepoRef
from github_radar.models.config import Settings
from github_radar.models.task import TaskPhase, TaskStatus, PHASE_ORDER
from github_radar.storage.paths import RepoPaths
from github_radar.memory.checkpoint import (
    create_task_state,
    load_task_state,
    update_task_phase,
    mark_phase_done,
    get_next_pending_phase,
    mark_failed,
)
from github_radar.ingest.repo_metadata import fetch_metadata
from github_radar.ingest.repo_readme import fetch_readme
from github_radar.ingest.repo_tree import fetch_tree
from github_radar.ingest.content_select import select_files
from github_radar.analyze.llm_client import build_client
from github_radar.analyze.snapshot import run_snapshot
from github_radar.analyze.structure_pass import run_structure_pass
from github_radar.analyze.synthesis import run_synthesis
from github_radar.obsidian.writer import write_repo_note


def _build_paths(ref: RepoRef, settings: Settings) -> RepoPaths:
    return RepoPaths(settings.artifacts_dir, ref)


def run_repo_analysis(
    raw: str,
    settings: Settings | None = None,
    force: bool = False,
) -> str:
    """Run full repo analysis pipeline.

    Args:
        raw: owner/repo string or GitHub URL.
        settings: Optional config override.
        force: Skip cache, re-run all phases.

    Returns the task_id.
    """
    if settings is None:
        settings = Settings()

    ref = RepoRef.parse(raw)
    paths = _build_paths(ref, settings)
    llm = build_client(settings.llm_base_url, settings.llm_model)

    # Check for existing state
    existing = load_task_state(paths)
    if existing and existing.status == TaskStatus.completed and not force:
        print(f"[cached] {ref.full_name} already analyzed. Use --force to re-run.")
        return existing.task_id

    # Create or resume
    if existing:
        state = existing
        print(f"[resume] {state.task_id} from phase {state.phase.value}")
    else:
        state = create_task_state(paths, repo=ref.full_name)
        print(f"[start] {state.task_id} → {ref.full_name}")

    token = settings.github_token

    # Determine starting phase (use PHASE_ORDER index, not string compare)
    start_phase = get_next_pending_phase(paths)
    phases_to_run = [
        p for p in PHASE_ORDER
        if PHASE_ORDER.index(p) >= PHASE_ORDER.index(start_phase) and p != TaskPhase.completed
    ]

    for phase in phases_to_run:
        try:
            print(f"  [{phase.value}] ...", end=" ", flush=True)
            _run_phase(phase, ref, paths, llm, token, settings, force)
            mark_phase_done(paths, phase)
            print("done")
        except Exception as e:
            print(f"FAILED: {e}")
            mark_failed(paths, str(e))
            raise

    # Mark completed
    update_task_phase(paths, TaskPhase.completed, TaskStatus.completed)
    print(f"[completed] {state.task_id}")
    return state.task_id


def _run_phase(
    phase: TaskPhase,
    ref: RepoRef,
    paths: RepoPaths,
    llm,
    token: str | None,
    settings: Settings,
    force: bool,
) -> None:
    """Execute a single pipeline phase."""
    if phase == TaskPhase.init:
        pass  # Already done
    elif phase == TaskPhase.metadata:
        fetch_metadata(ref, paths, token=token, force=force)
    elif phase == TaskPhase.readme:
        fetch_readme(ref, paths, token=token, force=force, max_chars=settings.max_readme_chars)
    elif phase == TaskPhase.tree:
        fetch_tree(ref, paths, token=token, force=force)
    elif phase == TaskPhase.content_select:
        select_files(ref, paths, force=force, max_file_chars=settings.max_file_chars)
    elif phase == TaskPhase.snapshot:
        result = run_snapshot(ref, paths, llm, force=force)
        if not result.worth_deep_reading:
            print("(skip deep — not worth it)", end=" ")
            # Skip remaining phases, go straight to obsidian write
            for skip_p in [TaskPhase.structure, TaskPhase.synthesis]:
                mark_phase_done(paths, skip_p)
    elif phase == TaskPhase.structure:
        run_structure_pass(ref, paths, llm, force=force)
    elif phase == TaskPhase.synthesis:
        run_synthesis(ref, paths, llm, force=force)
    elif phase == TaskPhase.obsidian_write:
        note_path = write_repo_note(ref, paths)
        print(f"(→ {note_path})", end=" ")


def resume_analysis(task_id: str, settings: Settings | None = None) -> str:
    """Resume a previously interrupted task by task_id."""
    if settings is None:
        settings = Settings()

    # Find the task state by scanning artifacts
    import json
    repos_dir = settings.artifacts_dir / "repos"
    for safe_dir in repos_dir.iterdir():
        if not safe_dir.is_dir():
            continue
        state_file = safe_dir / "checkpoints" / "task_state.json"
        if not state_file.exists():
            continue
        state_data = json.loads(state_file.read_text())
        if state_data.get("task_id") == task_id:
            ref = RepoRef.parse(state_data["repo"])
            return run_repo_analysis(ref.full_name, settings=settings)

    raise ValueError(f"Task not found: {task_id}")
