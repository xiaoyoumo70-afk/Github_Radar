"""GitHub Trending scraper — discover trending repos without official API."""

from __future__ import annotations

import re
import requests


def fetch_trending(since: str = "daily", language: str = "") -> list[dict]:
    """Scrape GitHub Trending page.

    Args:
        since: daily, weekly, or monthly.
        language: Optional programming language filter.

    Returns list of dicts with keys: owner, name, description, language,
    stars_total, stars_today, url.
    """
    if language:
        url = f"https://github.com/trending/{language}?since={since}"
    else:
        url = f"https://github.com/trending?since={since}"

    resp = requests.get(url, timeout=30, headers={
        "User-Agent": "github-radar/0.1.0",
        "Accept": "text/html",
    })
    resp.raise_for_status()
    html = resp.text

    # Extract articles — the actual trending repo cards
    article_pattern = re.compile(
        r'<article[^>]*class="[^"]*Box-row[^"]*"[^>]*>(.*?)</article>',
        re.DOTALL,
    )
    articles = article_pattern.findall(html)

    repos = []
    for art in articles:
        # Repo link: /owner/repo
        link_match = re.search(r'href="/([^/]+)/([^/"]+)"', art)
        if not link_match:
            continue
        owner, name = link_match.group(1), link_match.group(2)

        # Skip sponsors (they appear in articles with different structure)
        if owner in ("sponsors", "integrations", "login", "settings"):
            continue

        # Description
        desc_match = re.search(
            r'<p\s+class="[^"]*col-9[^"]*color-fg-muted[^"]*"[^>]*>\s*(.*?)\s*</p>',
            art, re.DOTALL,
        )
        desc = ""
        if desc_match:
            desc = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip()

        # Stars today / this week / this month
        stars_today = 0
        period = since
        stars_period_match = re.search(
            r'(\d[\d,]*)\s+stars?\s+(today|this week|this month)',
            art, re.IGNORECASE,
        )
        if stars_period_match:
            stars_today = int(stars_period_match.group(1).replace(",", ""))
            period = stars_period_match.group(2)

        # Total stars
        stars_total = 0
        # Total stars appear as plain "N,NNN stars" without "today" qualifier
        total_matches = re.findall(r'(\d[\d,]*)\s+stars?\b', art, re.IGNORECASE)
        for tm in total_matches:
            val = int(tm.replace(",", ""))
            if val > stars_total:
                stars_total = val

        # Language
        lang_match = re.search(r'programmingLanguage:"([^"]+)"', art)
        language_name = lang_match.group(1) if lang_match else ""

        repos.append({
            "owner": owner,
            "name": name,
            "full_name": f"{owner}/{name}",
            "url": f"https://github.com/{owner}/{name}",
            "description": desc,
            "stars_total": stars_total,
            "stars_today": stars_today,
            "language": language_name,
            "period": period,
            "since": since,
        })

    return repos


def fetch_trending_as_refs(since: str = "daily") -> list:
    """Fetch trending repos and return as RepoRef-compatible dicts."""
    from ..models.repo import RepoRef
    repos = fetch_trending(since=since)
    refs = []
    for r in repos:
        try:
            ref = RepoRef(owner=r["owner"], name=r["name"])
            refs.append(ref)
        except Exception:
            continue
    return refs
