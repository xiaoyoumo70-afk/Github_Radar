"""Daily scheduler — 3-round discovery + 10-project budget + 10-point scoring."""

from __future__ import annotations

import time
from pathlib import Path

from github_radar.models.config import Settings
from github_radar.models.repo import RepoRef
from github_radar.discover.trending import fetch_trending
from github_radar.discover.deduplicate import deduplicate, deduplicate_similar
from github_radar.discover.scoring import score_candidates, format_score
from github_radar.memory.budget import DailyBudget
from github_radar.obsidian.digest_writer import write_daily_digest


def run_daily(
    settings: Settings | None = None,
    max_analyze: int = 10,
    since: str = "daily",
) -> dict:
    """Run the full daily pipeline with 3-round budget + 10-point scoring.

    1. Check daily budget (3 rounds / 10 projects max)
    2. Discover trending repos
    3. Deduplicate exact matches
    4. Score on 0-10 scale
    5. Deduplicate similar projects (keep higher score)
    6. Analyze top candidates within budget
    7. Write daily digest

    Returns summary dict.
    """
    if settings is None:
        settings = Settings()

    date_str = time.strftime("%Y-%m-%d")
    budget = DailyBudget(settings.artifacts_dir / "daily_state.json")

    # Step 1: Check budget
    if not budget.can_start_round():
        print(f"[daily] Budget exhausted — {budget.summary()}")
        return {"date": date_str, "status": "budget_exhausted", **budget.state}

    round_num = budget.start_round()
    max_this_round = min(budget.projects_remaining, max_analyze)
    print(f"[daily] {date_str} — Round {round_num}/{DailyBudget.MAX_ROUNDS} "
          f"(budget: {max_this_round} projects remaining)")

    # Step 2: Discover
    print("  [discover] fetching trending ...")
    raw_repos = fetch_trending(since=since)
    print(f"  [discover] found {len(raw_repos)} trending repos")

    # Step 3: Exact deduplicate
    print("  [deduplicate] filtering already-seen repos ...")
    refs = []
    for r in raw_repos:
        try:
            refs.append(RepoRef(owner=r["owner"], name=r["name"]))
        except Exception:
            continue
    new_refs = deduplicate(refs, settings.artifacts_dir)
    print(f"  [deduplicate] {len(new_refs)} new, {len(refs) - len(new_refs)} skipped")

    if not new_refs:
        print("[daily] No new repos after dedup — digest only.")
        return _write_digest_and_return(date_str, [], budget, settings, 0, len(raw_repos))

    # Build dicts with metadata for scoring
    raw_by_name = {r["full_name"]: r for r in raw_repos}
    repo_dicts = []
    for ref in new_refs:
        raw = raw_by_name.get(ref.full_name, {})
        repo_dicts.append({
            "full_name": ref.full_name,
            "stargazers_count": raw.get("stars_total", 0),
            "stars_today": raw.get("stars_today", 0),
            "stars_total": raw.get("stars_total", 0),
            "topics": [],
            "description": raw.get("description", ""),
            "pushed_at": None,
            "language": raw.get("language", ""),
            "url": raw.get("url", f"https://github.com/{ref.full_name}"),
        })

    # Step 4: 10-point scoring
    print("  [score] 0-10 evaluation ...")
    scored = score_candidates(repo_dicts)

    # Print score details
    for s in scored[:8]:
        print(f"    {format_score(s)}")

    # Step 5: Similar-project dedup (pick higher score)
    print("  [dedup-similar] detecting similar projects ...")
    scored = deduplicate_similar(scored)
    print(f"  [dedup-similar] {len(scored)} candidates after similarity filter")

    # Step 6: Analyze within budget
    analyzed_count = 0
    repos_for_digest = []
    from app.task_runner import run_repo_analysis

    for i, entry in enumerate(scored):
        prio = "P1" if i < max_this_round else "P2"
        repos_for_digest.append({
            "full_name": entry["full_name"],
            "score": entry["score"],
            "score_breakdown": entry.get("score_breakdown", {}),
            "priority": prio,
        })

    for entry in repos_for_digest:
        if entry["priority"] != "P1":
            continue
        if analyzed_count >= max_this_round:
            break
        if not budget.can_add_project(entry["full_name"]):
            continue

        print(f"  [analyze] {entry['full_name']} (score={entry['score']}/10) ...")
        try:
            run_repo_analysis(entry["full_name"], settings=settings)
            budget.add_project(entry["full_name"])
            analyzed_count += 1
        except Exception as e:
            print(f"    [warn] failed: {e}")

    # Step 7: Write daily digest
    return _write_digest_and_return(
        date_str, repos_for_digest, budget, settings, analyzed_count, len(raw_repos)
    )


def _write_digest_and_return(
    date_str: str,
    repos: list[dict],
    budget: DailyBudget,
    settings: Settings,
    analyzed_count: int,
    discovered_count: int,
) -> dict:
    """Write daily digest and return result."""
    print("  [digest] writing daily note ...")
    note_path = write_daily_digest(
        date_str=date_str,
        repos=repos,
        summary=(
            f"今日第 {budget.state['rounds_used']}/{DailyBudget.MAX_ROUNDS} 轮扫描，"
            f"发现 {discovered_count} 个 trending repo，"
            f"重点分析 {analyzed_count} 个高优先级项目。"
            f"（日限额: {budget.state['projects_analyzed']}/{DailyBudget.MAX_PROJECTS}）"
        ),
        trends=f"共 {len(repos)} 个候选进入评分队列（{budget.summary()}）。",
    )
    print(f"  [digest] → {note_path}")

    result = {
        "date": date_str,
        "round": budget.state["rounds_used"],
        "discovered": discovered_count,
        "candidates": len(repos),
        "analyzed": analyzed_count,
        "daily_total": budget.state["projects_analyzed"],
        "budget_remaining": f"{budget.rounds_remaining}r/{budget.projects_remaining}p",
        "digest_note": note_path,
    }

    print(f"[daily] done: {result}")
    return result
