"""Deduplication — filter already-seen repos from candidate lists."""

from __future__ import annotations

from pathlib import Path

from ..models.repo import RepoRef


def deduplicate(
    candidates: list[RepoRef],
    artifacts_dir: Path,
    recent_days: int = 7,
) -> list[RepoRef]:
    """Remove repos that were recently analyzed.

    Checks for existing artifact directories under artifacts_dir/repos/.
    """
    repos_dir = artifacts_dir / "repos"
    seen: set[str] = set()

    if repos_dir.exists():
        for d in repos_dir.iterdir():
            if d.is_dir():
                # Directory name is safe_name (owner__repo)
                seen.add(d.name)

    result = []
    for ref in candidates:
        if ref.safe_name not in seen:
            result.append(ref)

    return result


def deduplicate_similar(
    scored: list[dict],
    similarity_threshold: float = 0.4,
) -> list[dict]:
    """Remove similar repos, keeping the higher-scored one.

    Similarity is computed as the Jaccard index of topic sets +
    keyword overlap in descriptions. If two repos exceed the threshold,
    the lower-scored one is removed.

    Args:
        scored: List of scored repo dicts (from score_candidates), sorted by score desc.
        similarity_threshold: Jaccard-like similarity above which repos are "similar".

    Returns filtered list.
    """
    from collections import Counter

    def _keyword_set(text: str) -> set[str]:
        """Extract meaningful keywords from a description."""
        if not text:
            return set()
        # Simple word extraction, skip short/common words
        stop_words = {
            "a", "an", "the", "is", "are", "was", "were", "for", "of", "in",
            "on", "at", "to", "from", "by", "with", "and", "or", "not", "it",
            "its", "be", "as", "has", "have", "can", "will", "this", "that",
            "you", "we", "they", "their", "our", "my", "your", "all", "but",
            "so", "if", "no", "up", "out", "just", "more", "also", "been",
            "into", "than", "then", "now", "very", "too", "only", "really",
            "some", "any", "each", "both", "few", "most", "much", "over",
        }
        words = text.lower().split()
        return {
            w.strip(".,;:!?()[]{}'\"") for w in words
            if len(w.strip(".,;:!?()[]{}'\"")) > 2
            and w.strip(".,;:!?()[]{}'\"") not in stop_words
        }

    def _similarity(a: dict, b: dict) -> float:
        """Compute similarity score between two repos."""
        # Topic overlap (weight: 0.6)
        topics_a = set(a.get("topics", []))
        topics_b = set(b.get("topics", []))
        if topics_a and topics_b:
            topic_sim = len(topics_a & topics_b) / max(len(topics_a | topics_b), 1)
        else:
            topic_sim = 0.0

        # Description keyword overlap (weight: 0.4)
        kw_a = _keyword_set(a.get("description", ""))
        kw_b = _keyword_set(b.get("description", ""))
        if kw_a and kw_b:
            desc_sim = len(kw_a & kw_b) / max(len(kw_a | kw_b), 1)
        else:
            desc_sim = 0.0

        # Language bonus (same language → +0.1)
        lang_bonus = 0.1 if (
            a.get("language") and b.get("language") and
            a["language"].lower() == b["language"].lower()
        ) else 0.0

        return 0.6 * topic_sim + 0.4 * desc_sim + lang_bonus

    if len(scored) <= 1:
        return scored

    kept = []
    removed = set()

    for i, repo in enumerate(scored):
        if i in removed:
            continue
        kept.append(repo)
        for j in range(i + 1, len(scored)):
            if j in removed:
                continue
            sim = _similarity(repo, scored[j])
            if sim >= similarity_threshold:
                removed.add(j)

    if removed:
        print(f"  [dedup-similar] removed {len(removed)} similar repos "
              f"(threshold={similarity_threshold})")

    return kept


def group_by_source(
    candidates: list[dict],
) -> dict[str, list[dict]]:
    """Group candidates by their discovery source."""
    groups: dict[str, list[dict]] = {}
    for c in candidates:
        source = c.get("source", "unknown")
        groups.setdefault(source, []).append(c)
    return groups
