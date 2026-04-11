"""
Trend Agent — Finds trending topics from multiple sources weekly.
Run: python agents/trend_agent.py
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import DATABASE_DIR, SERPER_API_KEY
from utils.web_search import search_web
from utils.file_manager import save_json, load_json, now_utc


CONTENT_ANGLES = [
    "islamic arab history facts",
    "shocking world records statistics",
    "country comparison facts",
    "ancient civilization discoveries",
    "wealth inequality statistics",
    "military spending world rankings",
    "surprising historical facts",
    "world records broken",
]


def search_trending_topics() -> list[dict]:
    """Search for trending factual topics across our content categories."""
    all_topics = []
    seen_titles = set()

    print("[trend_agent] Searching trending topics...")

    for query in CONTENT_ANGLES:
        print(f"  Searching: {query}")
        results = search_web(f"{query} 2025 2026", num_results=5)

        for r in results:
            title = r.get("title", "").strip()
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)

            # Score based on snippet quality
            snippet = r.get("snippet", "")
            trending_score = _score_result(title, snippet)

            topic = {
                "raw_topic": title,
                "url": r.get("url", ""),
                "snippet": snippet,
                "source_query": query,
                "trending_score": trending_score,
                "source": "serper_search",
                "first_seen": now_utc()[:10],
                "angled_ideas": _generate_angle_ideas(title, snippet),
                "added_to_database": False,
            }
            all_topics.append(topic)

        time.sleep(1)  # Rate limiting

    # Sort by trending score
    all_topics.sort(key=lambda x: x["trending_score"], reverse=True)
    print(f"[trend_agent] Found {len(all_topics)} topics")
    return all_topics


def _score_result(title: str, snippet: str) -> int:
    """Score a search result's potential as video content."""
    score = 50  # Base score
    combined = (title + " " + snippet).lower()

    # Boost for factual/statistical content
    boost_words = ["billion", "million", "percent", "largest", "richest", "most",
                   "ancient", "history", "record", "world", "times", "compared"]
    for word in boost_words:
        if word in combined:
            score += 5

    # Cap at 100
    return min(score, 100)


def _generate_angle_ideas(title: str, snippet: str) -> list[str]:
    """Generate 2 video idea angles from a trending topic."""
    # Simple template-based angle generation
    # (Full version uses Claude for smarter angles)
    ideas = []
    combined = (title + " " + snippet)[:200]

    # Islamic/Arab angle
    if any(w in combined.lower() for w in ["arab", "islam", "middle east", "saudi", "egypt"]):
        ideas.append(f"The Hidden Truth About: {title[:50]}")

    # Comparison angle
    ideas.append(f"How {title[:40]} Compares to What You Think")

    return ideas[:2]


def run_pytrends_search() -> list[dict]:
    """Get trending searches from Google Trends via pytrends."""
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl='en-US', tz=0, timeout=(10, 25))

        trending = pytrends.trending_searches(pn='united_states')
        topics = []

        for term in trending[0][:20]:  # Top 20 trending searches
            topics.append({
                "raw_topic": term,
                "source": "google_trends",
                "trending_score": 80,  # All trending searches get high score
                "first_seen": now_utc()[:10],
                "angled_ideas": [],
                "added_to_database": False,
            })
        return topics
    except Exception as e:
        print(f"[trend_agent] pytrends error: {e}")
        return []


def save_trending_topics(topics: list[dict]) -> None:
    """Save topics to database/trending_topics.json."""
    existing = load_json(DATABASE_DIR / "trending_topics.json")
    existing_topics = existing.get("topics", [])

    # Merge: add new topics, skip duplicates
    existing_titles = {t["raw_topic"] for t in existing_topics}
    new_topics = [t for t in topics if t["raw_topic"] not in existing_titles]

    all_topics = new_topics + existing_topics  # New ones first
    # Keep most recent 500 topics
    all_topics = all_topics[:500]

    save_json(DATABASE_DIR / "trending_topics.json", {
        "last_updated": now_utc(),
        "topics": all_topics,
        "total": len(all_topics),
    })
    print(f"[trend_agent] Saved {len(new_topics)} new topics ({len(all_topics)} total)")


def main():
    print("=" * 50)
    print("TREND AGENT — Weekly Topic Discovery")
    print("=" * 50)

    topics = search_trending_topics()

    # Also try pytrends
    pytrend_topics = run_pytrends_search()
    topics.extend(pytrend_topics)

    # Sort combined results
    topics.sort(key=lambda x: x["trending_score"], reverse=True)

    save_trending_topics(topics)

    print(f"\nTop 10 trending topics found:")
    for t in topics[:10]:
        print(f"  [{t['trending_score']:3d}] {t['raw_topic'][:60]}")

    print("\n[trend_agent] Done. Run idea_generator.py to convert topics to video ideas.")


if __name__ == "__main__":
    main()
