"""
idea_refresh.py — Scan top YouTube educational channels and extract new video ideas.

What it does:
  1. Finds channel IDs for key competitor channels via YouTube search
  2. Fetches their top 20 videos by view count
  3. Analyzes title patterns (numbers, comparisons, "real reason", etc.)
  4. Generates FactForge-style ideas from those patterns
  5. De-duplicates against existing queue + database/ideas_short.json
  6. Appends unique ideas to database/ideas_short.json
  7. Logs results to state/idea_refresh_log.json

Usage:
  python3 scripts/idea_refresh.py              # full run, saves results
  python3 scripts/idea_refresh.py --dry-run    # show what would be added, no save
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
ROOT          = Path(__file__).parent.parent
QUEUE_PATH    = ROOT / "state" / "queue.json"
IDEAS_DB_PATH = ROOT / "database" / "ideas_short.json"
LOG_PATH      = ROOT / "state" / "idea_refresh_log.json"
sys.path.insert(0, str(ROOT))

# ─── Target channels ──────────────────────────────────────────────────────────
# (channel_name, search_query) — we search by name to resolve the channel ID
TARGET_CHANNELS = [
    ("Veritasium",           "Veritasium science education"),
    ("Kurzgesagt",           "Kurzgesagt – In a Nutshell"),
    ("RealLifeLore",         "RealLifeLore geography"),
    ("VisualPolitik EN",     "VisualPolitik EN geopolitics"),
    ("Economics Explained",  "Economics Explained channel"),
]

MIN_VIEWS_THRESHOLD = 100_000   # only analyze videos with >100K views

# ─── Category guessing ───────────────────────────────────────────────────────
CATEGORY_MAP = {
    "islam": "islamic_history",
    "muslim": "islamic_history",
    "arab": "islamic_history",
    "ottoman": "islamic_history",
    "quran": "islamic_history",
    "caliphate": "islamic_history",
    "wealth": "wealth",
    "billionaire": "wealth",
    "richest": "wealth",
    "trillion": "wealth",
    "poverty": "wealth",
    "inequality": "wealth",
    "china": "geopolitics",
    "russia": "geopolitics",
    "military": "geopolitics",
    "empire": "geopolitics",
    "war": "geopolitics",
    "nuclear": "geopolitics",
    "sanctions": "geopolitics",
    "nato": "geopolitics",
    "science": "science",
    "brain": "science",
    "space": "science",
    "physics": "science",
    "biology": "science",
    "climate": "science",
}

# ─── Title-pattern templates (FactForge voice) ────────────────────────────────
PATTERN_TRANSFORMS = [
    # Numbers/stats
    (r"\b(\d[\d,\.]*)\s+(billion|trillion|million)\b", "The $1 $2 Secret the World Ignored"),
    # "Why X" → keep (already a strong format)
    (r"^Why\s+", None),
    # "How X" → reframe as secret/mechanism
    (r"^How\s+(.*)", r"The Mechanism Behind \1"),
    # "The Real Reason" → keep
    (r"The Real Reason", None),
    # "X vs Y" → keep
    (r"\bvs\.?\b", None),
    # "X Countries That" → keep number-driven titles
    (r"^\d+\s+Countries", None),
]

# Topic-extraction heuristics (fallback)
REFRAME_TEMPLATES = [
    "The Shocking Truth About {topic}",
    "What Nobody Tells You About {topic}",
    "Why {topic} Changed Everything",
    "The Real Story Behind {topic}",
    "How {topic} Silently Shapes the World",
]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_json(path: Path) -> dict:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def existing_titles_set() -> set:
    """Build a lowercase set of all known idea titles for deduplication."""
    titles = set()
    for path in [IDEAS_DB_PATH, QUEUE_PATH]:
        data = load_json(path)
        for key in ("ideas", "queue", "items"):
            for idea in data.get(key, []):
                titles.add(idea.get("title", "").lower().strip())
    return titles


def get_next_short_id(offset: int = 0) -> str:
    """Return the next available Short video ID, with optional offset for batching."""
    db = load_json(IDEAS_DB_PATH)
    existing_ids = [idea["id"] for idea in db.get("ideas", []) if idea["id"].startswith("S")]
    queue = load_json(QUEUE_PATH)
    queue_ids = [idea["id"] for idea in queue.get("ideas", []) if idea["id"].startswith("S")]
    all_ids = existing_ids + queue_ids
    if not all_ids:
        return f"S{1500 + offset:05d}"
    max_num = max(int(i[1:]) for i in all_ids if i[1:].isdigit())
    return f"S{max_num + 1 + offset:05d}"


def guess_category(text: str) -> str:
    text_lower = text.lower()
    for keyword, category in CATEGORY_MAP.items():
        if keyword in text_lower:
            return category
    return "shocking_stats"


def title_similarity(a: str, b: str) -> float:
    """
    Rough token-overlap similarity (Jaccard on word sets).
    Returns 0.0–1.0.
    """
    words_a = set(re.findall(r"\b\w{4,}\b", a.lower()))
    words_b = set(re.findall(r"\b\w{4,}\b", b.lower()))
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def is_duplicate(new_title: str, existing: set, threshold: float = 0.55) -> bool:
    """Return True if new_title is too similar to any existing title."""
    new_lower = new_title.lower().strip()
    if new_lower in existing:
        return True
    # Full similarity check for close-but-not-identical titles
    for existing_title in existing:
        if title_similarity(new_title, existing_title) >= threshold:
            return True
    return False


# ─── YouTube helpers ──────────────────────────────────────────────────────────

def resolve_channel_id(youtube, channel_name: str, search_query: str) -> str | None:
    """Search YouTube for a channel by name and return its channel ID."""
    try:
        response = (
            youtube.search()
            .list(q=search_query, type="channel", maxResults=3, part="snippet")
            .execute()
        )
        for item in response.get("items", []):
            snippet = item["snippet"]
            title = snippet.get("title", "")
            # Match on the first word of the target name to be lenient
            if channel_name.split()[0].lower() in title.lower():
                return item["snippet"]["channelId"]
        # Fallback: return the first result's channel ID
        items = response.get("items", [])
        if items:
            return items[0]["snippet"]["channelId"]
    except Exception as exc:
        print(f"  ⚠️  Channel lookup failed for '{channel_name}': {exc}")
    return None


def fetch_top_videos(youtube, channel_id: str, channel_name: str, max_results: int = 20) -> list:
    """
    Fetch the top `max_results` videos by view count for a channel.
    Returns list of dicts with {title, view_count, video_id}.
    """
    try:
        # Get recent uploads sorted by view count
        response = (
            youtube.search()
            .list(
                channelId=channel_id,
                type="video",
                order="viewCount",
                maxResults=max_results,
                part="snippet",
            )
            .execute()
        )
        video_ids = [item["id"]["videoId"] for item in response.get("items", [])]
        if not video_ids:
            return []

        # Fetch view counts for these videos
        stats_response = (
            youtube.videos()
            .list(id=",".join(video_ids), part="statistics,snippet")
            .execute()
        )
        results = []
        for item in stats_response.get("items", []):
            view_count = int(item["statistics"].get("viewCount", 0))
            if view_count >= MIN_VIEWS_THRESHOLD:
                results.append(
                    {
                        "title": item["snippet"]["title"],
                        "view_count": view_count,
                        "video_id": item["id"],
                        "channel": channel_name,
                    }
                )
        return results
    except Exception as exc:
        print(f"  ⚠️  Video fetch failed for channel '{channel_name}': {exc}")
        return []


# ─── Title pattern analysis ───────────────────────────────────────────────────

def extract_patterns(titles: list) -> dict:
    """
    Count title patterns across all analyzed titles.
    Returns a dict with pattern names and counts.
    """
    patterns = {
        "number_lead": 0,       # "5 Countries That..."
        "dollar_amount": 0,     # "The $X Trillion..."
        "why_question": 0,      # "Why China..."
        "how_mechanism": 0,     # "How America..."
        "comparison": 0,        # "X vs Y"
        "real_reason": 0,       # "The Real Reason..."
        "shocking_reveal": 0,   # "Nobody Talks About...", "What Nobody..."
        "country_specific": 0,  # country names
        "other": 0,
    }
    for title in titles:
        lower = title.lower()
        if re.match(r"^\d", title):
            patterns["number_lead"] += 1
        elif re.search(r"\$[\d,\.]+\s*(trillion|billion|million)", lower):
            patterns["dollar_amount"] += 1
        elif lower.startswith("why "):
            patterns["why_question"] += 1
        elif lower.startswith("how "):
            patterns["how_mechanism"] += 1
        elif re.search(r"\bvs\.?\b|\bversus\b", lower):
            patterns["comparison"] += 1
        elif "real reason" in lower:
            patterns["real_reason"] += 1
        elif any(p in lower for p in ("nobody", "secret", "hidden", "untold", "truth about")):
            patterns["shocking_reveal"] += 1
        elif re.search(r"\b(china|usa|russia|india|germany|france|uk|japan|brazil)\b", lower):
            patterns["country_specific"] += 1
        else:
            patterns["other"] += 1
    return patterns


def reframe_title(raw_title: str, index: int = 0) -> str:
    """
    Transform a competitor title into a FactForge-style title.
    Uses pattern matching + topic extraction.
    """
    lower = raw_title.lower()

    # Keep strong formats as-is (just return after minor cleanup)
    keep_as_is = (
        lower.startswith("why ") or
        lower.startswith("the real reason") or
        re.search(r"\bvs\.?\b|\bversus\b", lower) or
        re.match(r"^\d+\s+", raw_title) or
        re.search(r"\$[\d,\.]+\s*(trillion|billion|million)", lower)
    )
    if keep_as_is:
        return raw_title

    # Extract core topic: remove channel-style intros like "How [Channel] discovered..."
    topic = re.sub(
        r"^(how|what|when|where|the story of|inside|meet|this is)\s+",
        "",
        raw_title,
        flags=re.IGNORECASE,
    ).strip()

    # Use rotating template to avoid repetition
    template = REFRAME_TEMPLATES[index % len(REFRAME_TEMPLATES)]
    return template.format(topic=topic)


def generate_ideas_from_videos(video_data: list) -> list:
    """
    Convert a list of competitor video dicts into FactForge-style ideas.
    Applies deduplication against existing titles.
    """
    existing = existing_titles_set()
    ideas = []
    next_id_offset = 0

    for i, video in enumerate(video_data):
        raw_title = video["title"]

        # Skip non-educational content
        skip_words = ["official", "music video", "lyrics", "remix", "reaction", "vlog", "podcast", "live stream"]
        if any(w in raw_title.lower() for w in skip_words):
            continue
        if len(raw_title) < 15:
            continue

        new_title = reframe_title(raw_title, index=i)

        if is_duplicate(new_title, existing):
            continue

        category = guess_category(new_title)
        idea_id = get_next_short_id(offset=next_id_offset)

        idea = {
            "id": idea_id,
            "title": new_title,
            "category": category,
            "hook": f"Here's what's really happening with {new_title.lower().rstrip('.')}.",
            "angle": category,
            "source": f"inspired_by_{video['channel'].lower().replace(' ', '_')}",
            "original_title": raw_title,
            "original_channel": video["channel"],
            "original_views": video["view_count"],
            "status": "pending",
            "produced_date": None,
            "youtube_id": None,
            "views": None,
        }
        ideas.append(idea)
        existing.add(new_title.lower().strip())
        next_id_offset += 1

    return ideas


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="FactForge — idea refresh from competitor channels")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be added without saving")
    args = parser.parse_args()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"💡 Idea Refresh — {today}")
    print()

    # ── Connect to YouTube API ─────────────────────────────────────────────────
    try:
        from utils.youtube_helper import get_youtube_client
        youtube = get_youtube_client()
    except FileNotFoundError:
        print("  ❌ YouTube token not found (config/youtube_token.json)")
        print("     Run the OAuth flow first to generate a token.")
        sys.exit(1)
    except Exception as exc:
        if "quota" in str(exc).lower():
            print(f"  ❌ YouTube API quota exceeded. Try again tomorrow.")
        else:
            print(f"  ❌ YouTube API error: {exc}")
        sys.exit(1)

    # ── Step 1: Resolve channel IDs ────────────────────────────────────────────
    channels = []
    print(f"  Resolving {len(TARGET_CHANNELS)} channel IDs ...")
    for channel_name, search_query in TARGET_CHANNELS:
        channel_id = resolve_channel_id(youtube, channel_name, search_query)
        if channel_id:
            channels.append((channel_name, channel_id))
        else:
            print(f"  ⚠️  Could not resolve channel ID for '{channel_name}' — skipping")

    print(f"  Channels found: {len(channels)}")

    # ── Step 2: Fetch top videos ───────────────────────────────────────────────
    all_videos = []
    for channel_name, channel_id in channels:
        videos = fetch_top_videos(youtube, channel_id, channel_name)
        all_videos.extend(videos)
        print(f"  [{channel_name}]: {len(videos)} videos ≥{MIN_VIEWS_THRESHOLD // 1000}K views")

    print(f"  Videos analyzed: {len(all_videos)}")

    # ── Step 3: Analyze title patterns ────────────────────────────────────────
    all_titles = [v["title"] for v in all_videos]
    patterns = extract_patterns(all_titles)
    pattern_count = sum(v for v in patterns.values() if v > 0)
    print(f"  Patterns extracted: {pattern_count} across {len(all_videos)} titles")

    # ── Step 4: Generate FactForge ideas ──────────────────────────────────────
    # Sort by view count so we prioritize the most successful content
    all_videos.sort(key=lambda v: v["view_count"], reverse=True)
    new_ideas = generate_ideas_from_videos(all_videos)

    print(f"  New ideas generated: {len(new_ideas)} ({len(new_ideas)} unique after dedup)")
    print()

    if args.dry_run:
        print("  [dry-run] Would add these ideas to database/ideas_short.json:")
        for idea in new_ideas[:10]:
            print(f"    [{idea['id']}] {idea['title']}")
            print(f"           (inspired by: {idea['original_channel']} — {idea['original_views']:,} views)")
        if len(new_ideas) > 10:
            print(f"    ... and {len(new_ideas) - 10} more")
        print()
        print("  [dry-run] No files written.")
        return

    if not new_ideas:
        print("  ✅ No new unique ideas found — database is already up to date.")
        return

    # ── Step 5: Append to database/ideas_short.json ───────────────────────────
    db_data = load_json(IDEAS_DB_PATH)
    if "ideas" not in db_data:
        db_data = {"created": today, "last_updated": today, "total": 0, "ideas": []}

    # Re-ID all new ideas starting from current max to avoid collisions
    existing_ids = {idea["id"] for idea in db_data.get("ideas", [])}
    max_num = max(
        (int(i[1:]) for i in existing_ids if i.startswith("S") and i[1:].isdigit()),
        default=1499,
    )
    for idx, idea in enumerate(new_ideas):
        idea["id"] = f"S{max_num + 1 + idx:05d}"

    db_data["ideas"].extend(new_ideas)
    db_data["last_updated"] = today
    db_data["total"] = len(db_data["ideas"])
    save_json(IDEAS_DB_PATH, db_data)
    print(f"  ✓ Added {len(new_ideas)} ideas → database/ideas_short.json  (total: {db_data['total']})")

    # ── Step 6: Log to state/idea_refresh_log.json ────────────────────────────
    log_data = load_json(LOG_PATH)
    if not isinstance(log_data, dict):
        log_data = {"runs": []}
    log_data.setdefault("runs", [])

    run_entry = {
        "date": today,
        "channels_scanned": len(channels),
        "videos_analyzed": len(all_videos),
        "patterns_extracted": pattern_count,
        "new_ideas_added": len(new_ideas),
        "title_patterns": patterns,
        "ideas_added": [{"id": i["id"], "title": i["title"]} for i in new_ideas],
    }
    log_data["runs"].append(run_entry)
    log_data["last_run"] = today
    log_data["total_ideas_added"] = sum(r.get("new_ideas_added", 0) for r in log_data["runs"])
    save_json(LOG_PATH, log_data)
    print(f"  ✓ Logged run → state/idea_refresh_log.json")

    print()
    print(f"  Added to database/ideas_short.json")


if __name__ == "__main__":
    main()
