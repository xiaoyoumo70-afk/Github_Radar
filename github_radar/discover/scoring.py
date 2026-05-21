"""10-point scoring for repo discovery candidates.

Score breakdown (0.0 – 10.0):
  Stars:          0–3.0  (log-scaled, 50k stars → 3.0)
  Activity:       0–2.0  (pushed today=2.0, this week=1.5, this month=1.0)
  Description:    0–2.0  (has description + quality)
  Community:      0–1.5  (has topics, readme, issues/wiki signals)
  Freshness:      0–1.5  (new repo bonus, created within 6 months)
"""

from __future__ import annotations

import math
from datetime import datetime, timezone, timedelta


def score_candidates(
    results: list[dict],
    target_topics: list[str] | None = None,
) -> list[dict]:
    """Score repos on 0-10 scale, returning enriched dicts with score breakdown.

    Each result dict gains: score, score_breakdown (stars/activity/description/community/freshness).
    """
    if not results:
        return []

    target_set = set(t.lower() for t in (target_topics or []))
    now = datetime.now(timezone.utc)

    scored = []
    for r in results:
        full_name = r.get("full_name", "")
        breakdown = {}
        score = 0.0

        # ——— Stars (0–3.0) ———
        stars = r.get("stargazers_count", 0) or 0
        stars_from_trending = r.get("stars_total", 0) or 0
        stars = max(stars, stars_from_trending)
        if stars >= 50_000:
            breakdown["stars"] = 3.0
        elif stars >= 10_000:
            breakdown["stars"] = round(2.5 + (stars - 10000) / 40000 * 0.5, 1)
        elif stars >= 1_000:
            breakdown["stars"] = round(2.0 + (stars - 1000) / 9000 * 0.5, 1)
        elif stars >= 100:
            breakdown["stars"] = round(1.0 + (stars - 100) / 900 * 1.0, 1)
        elif stars > 0:
            breakdown["stars"] = round(stars / 100 * 1.0, 1)
        else:
            breakdown["stars"] = 0.0
        score += breakdown["stars"]

        # ——— Activity (0–2.0) ———
        pushed = r.get("pushed_at")
        if pushed:
            try:
                pushed_dt = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
                days_ago = (now - pushed_dt).days
                if days_ago <= 1:
                    breakdown["activity"] = 2.0
                elif days_ago <= 7:
                    breakdown["activity"] = 1.5
                elif days_ago <= 30:
                    breakdown["activity"] = 1.0
                elif days_ago <= 90:
                    breakdown["activity"] = 0.5
                else:
                    breakdown["activity"] = 0.2
            except Exception:
                breakdown["activity"] = 0.0
        else:
            # Stars today is a proxy for activity
            stars_today = r.get("stars_today", 0) or 0
            if stars_today >= 500:
                breakdown["activity"] = 2.0
            elif stars_today >= 100:
                breakdown["activity"] = 1.5
            elif stars_today >= 10:
                breakdown["activity"] = 1.0
            elif stars_today > 0:
                breakdown["activity"] = 0.5
            else:
                breakdown["activity"] = 0.0
        score += breakdown["activity"]

        # ——— Description (0–2.0) ———
        desc = (r.get("description") or "").strip()
        topics = [t.lower() for t in r.get("topics", [])]
        if not desc and not topics:
            breakdown["description"] = 0.0
        elif not desc:
            breakdown["description"] = 0.5  # has topics but no description
        elif len(desc) >= 80:
            breakdown["description"] = 2.0
        elif len(desc) >= 40:
            breakdown["description"] = 1.5
        elif len(desc) >= 20:
            breakdown["description"] = 1.0
        else:
            breakdown["description"] = 0.5
        score += breakdown["description"]

        # ——— Community signals (0–1.5) ———
        community = 0.0
        if topics:
            community += min(len(topics), 5) * 0.15  # up to 0.75 for topics
        # Language diversity signal
        lang = r.get("language")
        if lang:
            community += 0.25
        # Forks as proxy for community engagement
        forks = r.get("forks_count", 0) or 0
        if forks >= 1000:
            community += 0.5
        elif forks >= 100:
            community += 0.25
        breakdown["community"] = round(min(community, 1.5), 1)
        score += breakdown["community"]

        # ——— Freshness bonus (0–1.5) ———
        created = r.get("created_at")
        if created:
            try:
                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                months_ago = (now - created_dt).days / 30
                if months_ago <= 1:
                    breakdown["freshness"] = 1.5
                elif months_ago <= 3:
                    breakdown["freshness"] = 1.0
                elif months_ago <= 6:
                    breakdown["freshness"] = 0.5
                else:
                    breakdown["freshness"] = 0.0
            except Exception:
                breakdown["freshness"] = 0.0
        else:
            breakdown["freshness"] = 0.0
        score += breakdown["freshness"]

        total = round(score, 1)
        scored.append({
            "full_name": full_name,
            "score": total,
            "score_breakdown": breakdown,
            "stars": stars,
            "description": desc,
            "language": r.get("language", "unknown"),
            "topics": topics,
            "url": r.get("url", f"https://github.com/{full_name}"),
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def format_score(entry: dict) -> str:
    """Human-readable score line."""
    bd = entry.get("score_breakdown", {})
    parts = [
        f"⭐{bd.get('stars', 0):.1f}",
        f"🕐{bd.get('activity', 0):.1f}",
        f"📝{bd.get('description', 0):.1f}",
        f"👥{bd.get('community', 0):.1f}",
        f"🆕{bd.get('freshness', 0):.1f}",
    ]
    return f"{entry['score']}/10  {' '.join(parts)}  {entry['full_name']}"
