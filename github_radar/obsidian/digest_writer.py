"""Daily digest note writer for Obsidian."""

from __future__ import annotations

import subprocess
import time
from typing import Any

DIGEST_TEMPLATE = """---
type: github-digest
date: {date}
repo_count: {repo_count}
high_priority_count: {p1_count}
tags:
  - github-radar
  - daily-digest
---

# GitHub Daily Digest — {date}

## 今日结论
{today_summary}

## P1 重点推荐
{p1_list}

## P2 浏览列表
{p2_list}

## 今日趋势
{trends}

## 后续建议
{follow_up}
"""


def _obsidian_cli(*args: str) -> None:
    cmd = ["obsidian", *args]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"obsidian CLI failed: {result.stderr.strip()}")


def write_daily_digest(
    date_str: str,
    repos: list[dict],
    summary: str = "",
    trends: str = "",
) -> str:
    """Write a daily GitHub digest note to Obsidian.

    Args:
        date_str: Date string (YYYY-MM-DD).
        repos: List of repo dicts with keys: full_name, score, priority.
        summary: Overall day summary.
        trends: Trend observations.

    Returns vault-relative note path.
    """
    p1 = [r for r in repos if r.get("priority") == "P1"]
    p2 = [r for r in repos if r.get("priority") == "P2"]

    p1_list = "\n".join(
        f"1. [[{r['full_name'].replace('/', '__')}]] — {r.get('reason', '')}"
        for r in p1[:10]
    ) or "无"

    p2_list = "\n".join(
        f"- {r['full_name']} {r.get('reason', '') if r.get('reason') else ''}"
        for r in p2[:20]
    ) or "无"

    content = DIGEST_TEMPLATE.format(
        date=date_str,
        repo_count=len(repos),
        p1_count=len(p1),
        today_summary=summary or "今日无结论总结。",
        p1_list=p1_list,
        p2_list=p2_list,
        trends=trends or "无趋势数据。",
        follow_up=f"建议深读 {len(p1)} 个 P1 项目。" if p1 else "今日无需深读项目。",
    )

    note_path = f"Projects/GitHub Radar/Digests/{date_str} GitHub Digest"
    _obsidian_cli("create", f"path={note_path}", f"content={content}", "overwrite")
    return note_path
