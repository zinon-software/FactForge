"""
trending_refresh.py — Fetch trending topics and inject new ideas at top of queue.

Sources:
  1. YouTube Data API  — search trending educational videos (last 7 days)
  2. pytrends          — Google Trends rising queries
  3. Hardcoded fallback — 20 evergreen high-performing topics

Usage:
  python3 scripts/trending_refresh.py              # full run, saves results
  python3 scripts/trending_refresh.py --dry-run    # show what would be added, no save
"""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
ROOT           = Path(__file__).parent.parent
QUEUE_PATH     = ROOT / "state" / "queue.json"
TRENDING_PATH  = ROOT / "database" / "trending_topics.json"
IDEAS_DB_PATH  = ROOT / "database" / "ideas_short.json"
sys.path.insert(0, str(ROOT))

# ─── Constants ────────────────────────────────────────────────────────────────
YT_SEARCH_QUERIES = [
    "shocking facts",
    "you didn't know",
    "history facts",
    "wealth gap",
    "vs comparison",
]

PYTRENDS_KEYWORDS = ["history facts", "shocking statistics", "wealth inequality"]

# Category mapping: rough keywords → FactForge category
CATEGORY_MAP = {
    "islam": "islamic_history",
    "muslim": "islamic_history",
    "arab": "islamic_history",
    "ottoman": "islamic_history",
    "caliphate": "islamic_history",
    "wealth": "wealth",
    "billionaire": "wealth",
    "richest": "wealth",
    "inequality": "wealth",
    "trillion": "wealth",
    "china": "geopolitics",
    "russia": "geopolitics",
    "us vs": "geopolitics",
    "war": "geopolitics",
    "military": "geopolitics",
    "empire": "geopolitics",
    "science": "science",
    "space": "science",
    "brain": "science",
    "statistics": "shocking_stats",
    "fact": "shocking_stats",
    "history": "shocking_stats",
}

FALLBACK_TOPICS = [
    {
        "title": "The Country That Owns More Debt Than Every Nation on Earth Combined",
        "hook": "One nation's debt is so large it could fund every other country on Earth for decades.",
        "angle": "shocking_stats",
        "category": "shocking_stats",
    },
    {
        "title": "Why 1% of the World Owns More Than the Bottom 50% Combined",
        "hook": "The 85 richest people alive own as much as the poorest 3.5 billion combined.",
        "angle": "wealth",
        "category": "wealth",
    },
    {
        "title": "The Ancient Civilization That Built Roads Better Than Modern Highways",
        "hook": "Roman roads built 2,000 years ago still carry traffic today.",
        "angle": "shocking_stats",
        "category": "shocking_stats",
    },
    {
        "title": "The Country That Sends More Oil Money Abroad Than It Keeps at Home",
        "hook": "One Gulf nation sends over $100 billion a year to foreign workers while locals earn six-figure salaries.",
        "angle": "geopolitics",
        "category": "geopolitics",
    },
    {
        "title": "What Happens to Your Body If You Don't Sleep for 11 Days",
        "hook": "The world record for sleep deprivation ended with hallucinations, paranoia, and a complete personality change.",
        "angle": "science",
        "category": "science",
    },
    {
        "title": "The Islamic Mathematician Who Invented Algebra 1,200 Years Ago",
        "hook": "Without Al-Khwarizmi's work in 9th-century Baghdad, modern computers would not exist.",
        "angle": "islamic_history",
        "category": "islamic_history",
    },
    {
        "title": "The African Country That Was Richer Than France in 1960",
        "hook": "One African nation had a higher GDP per capita than France at independence — here's what happened next.",
        "angle": "geopolitics",
        "category": "geopolitics",
    },
    {
        "title": "Why China Built 40,000 Kilometers of High-Speed Rail While America Built Zero",
        "hook": "China went from zero to the world's largest high-speed rail network in 20 years.",
        "angle": "geopolitics",
        "category": "geopolitics",
    },
    {
        "title": "The Medication That Costs $1 to Make and Sells for $750 a Pill",
        "hook": "A drug that costs pennies to manufacture was priced at $750 per dose overnight.",
        "angle": "shocking_stats",
        "category": "shocking_stats",
    },
    {
        "title": "How a 14th-Century Muslim Scholar Predicted Economic Cycles 500 Years Before Adam Smith",
        "hook": "Ibn Khaldun's 'Muqaddimah' described supply, demand, and social cycles centuries before Western economists.",
        "angle": "islamic_history",
        "category": "islamic_history",
    },
    {
        "title": "The Country Where Average People Work 3 Jobs and Still Can't Afford Rent",
        "hook": "In the world's richest economy, 40 million people cannot afford basic housing.",
        "angle": "shocking_stats",
        "category": "shocking_stats",
    },
    {
        "title": "Why Saudi Arabia Is Building a Straight-Line City With No Cars or Roads",
        "hook": "NEOM's The Line is a 170-kilometer city with no streets, no cars, and no carbon emissions.",
        "angle": "geopolitics",
        "category": "geopolitics",
    },
    {
        "title": "The Deepfake Scam That Stole $200 Million From One Company in One Call",
        "hook": "AI-generated video calls are now convincing enough to trick CFOs into wiring millions.",
        "angle": "shocking_stats",
        "category": "shocking_stats",
    },
    {
        "title": "The Forgotten Muslim Scientists Who Kept Ancient Knowledge Alive During Europe's Dark Ages",
        "hook": "While Europe burned books, Islamic scholars in Baghdad translated, preserved, and expanded Greek knowledge.",
        "angle": "islamic_history",
        "category": "islamic_history",
    },
    {
        "title": "Why Water Will Cause the Next World War",
        "hook": "By 2050, over 5 billion people will face fresh water scarcity — and wars have already started.",
        "angle": "geopolitics",
        "category": "geopolitics",
    },
    {
        "title": "The Country That Earns More From Tourists Than From Oil",
        "hook": "One tiny Gulf state earns more revenue from tourism and finance than all its oil exports combined.",
        "angle": "wealth",
        "category": "wealth",
    },
    {
        "title": "How Elon Musk's Net Worth Can Change By $50 Billion in a Single Day",
        "hook": "A single Tesla earnings call in 2021 erased $15 billion from one man's net worth in hours.",
        "angle": "wealth",
        "category": "wealth",
    },
    {
        "title": "The Island Nation That Disappeared Underwater in Living Memory",
        "hook": "Entire Pacific island nations are being swallowed by rising seas — their populations are now climate refugees.",
        "angle": "shocking_stats",
        "category": "shocking_stats",
    },
    {
        "title": "The Language Spoken by 1.8 Billion People That Has Almost No Presence Online",
        "hook": "Arabic is the 5th most spoken language but represents less than 1% of internet content.",
        "angle": "islamic_history",
        "category": "islamic_history",
    },
    {
        "title": "Why North Korea Has the World's Largest Army Per Capita and Still Can't Feed Its People",
        "hook": "25% of North Korea's GDP goes to military spending while 40% of its population is undernourished.",
        "angle": "geopolitics",
        "category": "geopolitics",
    },
]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_json(path: Path) -> dict:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_next_short_id() -> str:
    """Return the next available Short video ID (e.g. 'S01801')."""
    db = load_json(IDEAS_DB_PATH)
    existing_ids = [idea["id"] for idea in db.get("ideas", []) if idea["id"].startswith("S")]
    queue = load_json(QUEUE_PATH)
    queue_ids = [idea["id"] for idea in queue.get("ideas", []) if idea["id"].startswith("S")]
    all_ids = existing_ids + queue_ids
    if not all_ids:
        return "S01500"
    max_num = max(int(i[1:]) for i in all_ids if i[1:].isdigit())
    return f"S{max_num + 1:05d}"


def guess_category(text: str) -> str:
    text_lower = text.lower()
    for keyword, category in CATEGORY_MAP.items():
        if keyword in text_lower:
            return category
    return "shocking_stats"


def title_to_hook(title: str) -> str:
    """Generate a basic hook sentence from a title."""
    return f"Here's a fact about {title.lower().rstrip('.')} that will change how you see the world."


def titles_to_ideas(titles: list, source: str, trending_score: int = 80) -> list:
    """
    Convert a list of raw title strings into FactForge idea dicts.
    Assigns sequential IDs starting after the current max.
    """
    ideas = []
    next_id_num = int(get_next_short_id()[1:])
    for title in titles:
        category = guess_category(title)
        idea = {
            "id": f"S{next_id_num:05d}",
            "title": title,
            "category": category,
            "hook": title_to_hook(title),
            "angle": category,
            "source": source,
            "trending_score": trending_score,
            "status": "pending",
            "produced_date": None,
            "youtube_id": None,
            "views": None,
        }
        ideas.append(idea)
        next_id_num += 1
    return ideas


def existing_titles_set() -> set:
    """Return a lowercase set of all existing idea titles for deduplication."""
    titles = set()
    for path in [IDEAS_DB_PATH, QUEUE_PATH]:
        data = load_json(path)
        for key in ("ideas", "queue", "items"):
            for idea in data.get(key, []):
                titles.add(idea.get("title", "").lower().strip())
    return titles


# ─── Source 1: YouTube Data API ───────────────────────────────────────────────

def fetch_youtube_trending(youtube) -> tuple[list, list]:
    """
    Search YouTube for trending educational English videos from the last 7 days.
    Returns (titles: list[str], keywords: list[str]).
    """
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    titles = []
    for query in YT_SEARCH_QUERIES:
        try:
            response = (
                youtube.search()
                .list(
                    q=query,
                    type="video",
                    order="viewCount",
                    publishedAfter=seven_days_ago,
                    relevanceLanguage="en",
                    regionCode="US",
                    maxResults=10,
                    part="snippet",
                    videoDuration="short",  # under 4 minutes
                )
                .execute()
            )
            for item in response.get("items", []):
                title = item["snippet"]["title"]
                # Filter out music/entertainment — keep factual content
                lower = title.lower()
                skip_words = ["official", "music video", "lyrics", "remix", "reaction", "vlog"]
                if not any(w in lower for w in skip_words) and len(title) > 20:
                    titles.append(title)
        except Exception as exc:
            print(f"  ⚠️  YouTube search failed for '{query}': {exc}")

    # Extract repeating keywords as trending signals
    from collections import Counter
    words = []
    for t in titles:
        words.extend(
            w.lower().strip("\"'.,!?")
            for w in t.split()
            if len(w) > 4 and w.lower() not in {"that", "this", "with", "have", "from", "what", "when", "your", "their", "they", "would", "could", "about"}
        )
    top_keywords = [w for w, _ in Counter(words).most_common(20)]
    return titles, top_keywords


# ─── Source 2: Google Trends (pytrends) ──────────────────────────────────────

def fetch_google_trends() -> tuple[list, list]:
    """
    Fetch rising queries from Google Trends.
    Returns (topic_titles: list[str], keywords: list[str]).
    """
    try:
        from pytrends.request import TrendReq
    except ImportError:
        return [], []

    try:
        pytrends = TrendReq(hl="en-US", tz=360)
        pytrends.build_payload(PYTRENDS_KEYWORDS, timeframe="now 7-d")
        related = pytrends.related_queries()

        rising_topics = []
        keywords = []
        for kw in PYTRENDS_KEYWORDS:
            df = related.get(kw, {}).get("rising")
            if df is not None and not df.empty:
                for query_text in df["query"].head(5).tolist():
                    keywords.append(query_text)
                    # Convert raw query into a FactForge-style title
                    title = query_text.strip().title()
                    if len(title) > 10:
                        rising_topics.append(f"The Truth About {title} Nobody Is Talking About")
        return rising_topics, keywords
    except Exception as exc:
        print(f"  ⚠️  Google Trends failed: {exc}")
        return [], []


# ─── Idea generation ──────────────────────────────────────────────────────────

def generate_ideas_from_yt_titles(raw_titles: list) -> list:
    """
    Transform competitor/trending YouTube titles into FactForge-style titles.
    Extracts the core topic and reformulates with a hook-first frame.
    """
    generated = []
    seen = existing_titles_set()

    for raw in raw_titles:
        raw_lower = raw.lower()
        # Derive a reframed title
        if "how" in raw_lower:
            new_title = raw.replace("How ", "The Secret Behind ").replace("how ", "The Secret Behind ")
        elif raw_lower.startswith("why"):
            new_title = raw  # keep Why questions — they're already strong
        elif any(c.isdigit() for c in raw):
            new_title = raw  # keep number-driven titles
        elif "vs" in raw_lower or "versus" in raw_lower:
            new_title = raw  # keep comparisons
        else:
            new_title = f"The Real Story Behind {raw}"

        # Avoid duplicates
        if new_title.lower().strip() not in seen:
            generated.append(new_title)
            seen.add(new_title.lower().strip())

    return generated[:15]  # cap at 15 to avoid flooding queue


def score_idea(title: str, trending_keywords: list) -> int:
    """Assign a trending score 60–99 based on keyword overlap."""
    title_lower = title.lower()
    matches = sum(1 for kw in trending_keywords if kw in title_lower)
    base = 70
    score = min(99, base + matches * 5)
    return score


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="FactForge — trending topic refresh")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be added without saving")
    args = parser.parse_args()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"🔥 Trending refresh — {today}")
    print()

    all_titles: list[str] = []
    all_keywords: list[str] = []

    # ── Source 1: YouTube Data API ────────────────────────────────────────────
    youtube_titles: list[str] = []
    try:
        youtube = __import__("utils.youtube_helper", fromlist=["get_youtube_client"]).get_youtube_client()
        youtube_titles, yt_keywords = fetch_youtube_trending(youtube)
        all_keywords.extend(yt_keywords)
        print(f"  YouTube trending: {len(youtube_titles)} patterns found")
    except FileNotFoundError:
        print("  ⚠️  YouTube token not found — skipping YouTube source")
    except Exception as exc:
        if "quota" in str(exc).lower():
            print(f"  ⚠️  YouTube API quota exceeded — skipping YouTube source")
        else:
            print(f"  ⚠️  YouTube API error: {exc}")

    # ── Source 2: Google Trends ───────────────────────────────────────────────
    trend_titles: list[str] = []
    trend_titles, gtrend_keywords = fetch_google_trends()
    all_keywords.extend(gtrend_keywords)
    if trend_titles:
        print(f"  Google Trends: {len(trend_titles)} rising topics")
    else:
        print("  Google Trends: unavailable (pytrends not installed or request failed)")

    # ── Source 3: Fallback if both APIs failed ────────────────────────────────
    all_titles.extend(youtube_titles)
    all_titles.extend(trend_titles)
    fallback_used = False
    if not all_titles:
        print("  ⚠️  Both APIs failed — using evergreen fallback topics")
        all_titles = [t["title"] for t in FALLBACK_TOPICS]
        fallback_used = True

    # ── Generate FactForge ideas from raw titles ──────────────────────────────
    reframed = generate_ideas_from_yt_titles(all_titles)

    # If fallback, use the pre-crafted hooks; otherwise build from reframed titles
    if fallback_used:
        seen = existing_titles_set()
        ideas = []
        next_id_num = int(get_next_short_id()[1:])
        for raw in FALLBACK_TOPICS:
            if raw["title"].lower().strip() not in seen:
                idea = {
                    "id": f"S{next_id_num:05d}",
                    "title": raw["title"],
                    "category": raw["category"],
                    "hook": raw["hook"],
                    "angle": raw["angle"],
                    "source": "fallback_evergreen",
                    "trending_score": 75,
                    "status": "pending",
                    "produced_date": None,
                    "youtube_id": None,
                    "views": None,
                }
                ideas.append(idea)
                next_id_num += 1
                seen.add(raw["title"].lower().strip())
    else:
        # Score and build proper idea objects
        ideas = []
        next_id_num = int(get_next_short_id()[1:])
        seen = existing_titles_set()
        for title in reframed:
            if title.lower().strip() in seen:
                continue
            score = score_idea(title, all_keywords)
            category = guess_category(title)
            idea = {
                "id": f"S{next_id_num:05d}",
                "title": title,
                "category": category,
                "hook": title_to_hook(title),
                "angle": category,
                "source": "trending",
                "trending_score": score,
                "status": "pending",
                "produced_date": None,
                "youtube_id": None,
                "views": None,
            }
            ideas.append(idea)
            next_id_num += 1
            seen.add(title.lower().strip())

    # Sort by trending score descending
    ideas.sort(key=lambda x: x["trending_score"], reverse=True)

    # Cap at 10 new ideas
    ideas = ideas[:10]
    top5 = ideas[:5]

    print(f"  Generated {len(ideas)} new ideas → injecting top {len(top5)} at top of queue")
    if top5:
        print(f"  Top trend: \"{top5[0]['title']}\" (score: {top5[0]['trending_score']})")
    print()

    if args.dry_run:
        print("  [dry-run] Would inject these ideas:")
        for idea in top5:
            print(f"    [{idea['id']}] {idea['title']}  (score: {idea['trending_score']})")
        print()
        print("  [dry-run] No files written.")
        return

    # ── Save to database/trending_topics.json ─────────────────────────────────
    existing_trending = load_json(TRENDING_PATH)
    trending_data = {
        "last_updated": today,
        "trending_ideas": ideas,
        "trending_keywords": list(dict.fromkeys(all_keywords))[:30],  # dedup, keep order
        # preserve any existing fields that might be set
        **{k: v for k, v in existing_trending.items() if k not in ("last_updated", "trending_ideas", "trending_keywords")},
        # re-apply our new values last (overwrite)
        "last_updated": today,
        "trending_ideas": ideas,
        "trending_keywords": list(dict.fromkeys(all_keywords))[:30],
    }
    save_json(TRENDING_PATH, trending_data)
    print(f"  ✓ Saved {len(ideas)} ideas → database/trending_topics.json")

    # ── Inject top 5 at position 0 of state/queue.json ────────────────────────
    queue_data = load_json(QUEUE_PATH)
    if "ideas" not in queue_data:
        queue_data["ideas"] = []

    # Prepend — top5 goes before existing ideas
    existing_queue_ids = {idea["id"] for idea in queue_data["ideas"]}
    new_for_queue = [idea for idea in top5 if idea["id"] not in existing_queue_ids]
    queue_data["ideas"] = new_for_queue + queue_data["ideas"]
    queue_data["last_updated"] = datetime.now(timezone.utc).isoformat()
    queue_data["total"] = len(queue_data["ideas"])
    save_json(QUEUE_PATH, queue_data)
    print(f"  ✓ Injected {len(new_for_queue)} ideas at top of state/queue.json  (queue now: {queue_data['total']} total)")


if __name__ == "__main__":
    main()
