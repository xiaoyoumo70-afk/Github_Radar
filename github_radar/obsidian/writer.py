"""Obsidian writer — generate and persist repo/topic notes via obsidian CLI."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any

from ..models.repo import RepoRef, RepoMetadata
from ..models.analysis import FinalSynthesis
from ..storage.artifacts import read_json, write_json, write_text
from ..storage.paths import RepoPaths

REPO_NOTE_TEMPLATE = """---
type: repo
repo: {repo_name}
url: {url}
language: {language}
topics:
{topics_yaml}
stars_total: {stars}
last_analyzed_at: {analyzed_at}
tags:
{tags_yaml}
---

# {repo_name}

## 一句话判断
{one_sentence_takeaway}

## 为什么值得关注
{why_interesting}

## 核心定位
{repo_positioning}

## 主要用途
{use_cases}

## 技术栈
{tech_stack}

## 架构理解
{architecture_summary}

## 关键模块
{key_modules}

## 关键创新
{innovations}

## 局限与风险
{limitations}

## 相关项目
{related}

## 值得跟进的问题
{follow_up}

## 行动建议
{recommended_action}
"""


def _render_repo_note(
    ref: RepoRef,
    metadata: RepoMetadata,
    synthesis: FinalSynthesis,
    snapshot: dict[str, Any],
    structure: dict[str, Any],
) -> str:
    """Render a repo note from analysis outputs."""
    return REPO_NOTE_TEMPLATE.format(
        repo_name=ref.full_name,
        url=metadata.url,
        language=metadata.language or "unknown",
        topics_yaml="\n".join(f"  - {t}" for t in metadata.topics),
        stars=metadata.stars or 0,
        analyzed_at=time.strftime("%Y-%m-%d"),
        tags_yaml="\n".join(f"  - {t}" for t in synthesis.obsidian_tags),
        one_sentence_takeaway=synthesis.one_sentence_takeaway,
        why_interesting="\n".join(f"- {item}" for item in snapshot.get("why_interesting", [])),
        repo_positioning=synthesis.detailed_summary,
        use_cases="\n".join(f"- {item}" for item in snapshot.get("primary_use_cases", [])),
        tech_stack=", ".join(snapshot.get("tech_stack", [])),
        architecture_summary=structure.get("architecture_summary", ""),
        key_modules="\n".join(f"- {m}" for m in structure.get("major_modules", [])),
        innovations="\n".join(f"- {item}" for item in synthesis.key_innovations),
        limitations="\n".join(f"- {item}" for item in synthesis.limitations),
        related="\n".join(f"- [[{p.replace('/', '__')}]]" for p in synthesis.related_projects),
        follow_up="\n".join(f"- {q}" for q in synthesis.follow_up_questions),
        recommended_action=synthesis.recommended_action,
    )


def _obsidian_cli(*args: str) -> None:
    """Run an obsidian CLI command."""
    cmd = ["obsidian", *args]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"obsidian CLI failed: {result.stderr.strip()}")


def write_repo_note(
    ref: RepoRef,
    paths: RepoPaths,
) -> str:
    """Write a repo analysis note to Obsidian vault.

    Returns the vault-relative path of the created note.
    """
    metadata = RepoMetadata.model_validate(read_json(paths.metadata_file))
    synthesis = FinalSynthesis.model_validate(read_json(paths.synthesis_file))
    snapshot = read_json(paths.snapshot_file)
    structure = read_json(paths.structure_file)

    content = _render_repo_note(ref, metadata, synthesis, snapshot, structure)
    note_path = f"Projects/GitHub Radar/Repos/{ref.safe_name}"

    # Write to Obsidian — create with content
    _obsidian_cli("create", f'path={note_path}', f"content={content}", "overwrite")

    # Record path for later reference
    paths.ensure()
    write_text(paths.note_path_file, note_path)
    write_json(paths.last_write_file, {
        "note_path": note_path,
        "written_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "repo": ref.full_name,
    })

    return note_path
