"""
repackage.py — Analyze published/scheduled videos and generate repackaging opportunities.

Modes:
    --analyze   (default) Show all opportunities without making changes
    --extract   Add Long→Short clips to state/queue.json
    --expand    Add Short→Long suggestions to state/repackage_queue.json
    --all       Run both --extract and --expand

Usage:
    python3 scripts/repackage.py
    python3 scripts/repackage.py --analyze
    python3 scripts/repackage.py --extract
    python3 scripts/repackage.py --expand
    python3 scripts/repackage.py --all
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

STATE_DIR  = ROOT / "state"
OUTPUT_DIR = ROOT / "output"
DB_DIR     = ROOT / "database"

REPACKAGE_QUEUE = STATE_DIR / "repackage_queue.json"
PENDING_FILE    = STATE_DIR / "pending_uploads.json"
QUEUE_FILE      = STATE_DIR / "queue.json"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def save_json(path: Path, data: dict | list) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def get_all_pending() -> list[dict]:
    data = load_json(PENDING_FILE)
    if not data:
        return []
    return data.get("pending", [])


def get_max_short_id() -> int:
    """Find the highest S##### ID across queue.json and database/ideas_short.json."""
    max_id = 0

    queue_data = load_json(QUEUE_FILE) or {}
    for idea in queue_data.get("ideas", []):
        vid_id = idea.get("id", "")
        if vid_id.startswith("S") and vid_id[1:].isdigit():
            max_id = max(max_id, int(vid_id[1:]))

    ideas_db = load_json(DB_DIR / "ideas_short.json") or {}
    ideas_list = ideas_db if isinstance(ideas_db, list) else ideas_db.get("ideas", [])
    for idea in ideas_list:
        vid_id = idea.get("id", "")
        if vid_id.startswith("S") and vid_id[1:].isdigit():
            max_id = max(max_id, int(vid_id[1:]))

    # Also scan output/ directory
    for d in OUTPUT_DIR.iterdir():
        if d.is_dir() and d.name.startswith("S") and d.name[1:].isdigit():
            max_id = max(max_id, int(d.name[1:]))

    return max_id


def next_short_id(base: int, offset: int) -> str:
    return f"S{(base + offset):05d}"


def load_script(vid_id: str) -> dict | None:
    return load_json(OUTPUT_DIR / vid_id / "script.json")


def load_research(vid_id: str) -> dict | None:
    return load_json(OUTPUT_DIR / vid_id / "research.json")


def load_metadata(vid_id: str) -> dict | None:
    return load_json(OUTPUT_DIR / vid_id / "metadata.json")


# ─── Priority scoring ─────────────────────────────────────────────────────────

# Topics that tend to perform well as long documentaries
HIGH_PRIORITY_TOPICS = [
    "ai", "deepfake", "fraud", "scam", "million", "billion",
    "gun", "violence", "drug", "pharmaceutical", "prison",
    "cia", "spy", "surveillance", "crypto", "climate",
    "nuclear", "quantum", "dna", "crispr",
    "wealth", "gap", "inequality", "corrupt",
]

def score_short_for_expansion(title: str, research: dict | None) -> str:
    """Return 'high', 'medium', or 'low' expansion priority based on topic signals."""
    combined = title.lower()
    if research:
        combined += " " + json.dumps(research).lower()[:500]

    hits = sum(1 for kw in HIGH_PRIORITY_TOPICS if kw in combined)
    if hits >= 3:
        return "high"
    if hits >= 1:
        return "medium"
    return "low"


# ─── Short → Long expansion ───────────────────────────────────────────────────

def build_expansion_opportunity(entry: dict) -> dict:
    vid_id = entry["id"]
    title  = entry.get("title", "")
    script = load_script(vid_id)
    research = load_research(vid_id)

    # Extract the core topic from the short title for the long doc suggestion
    # Keep it simple — derive a documentary title by expanding the short hook
    short_hook = ""
    if script:
        tts = script.get("tts_text_final", "")
        # First sentence = hook
        sentences = re.split(r"(?<=[.!?])\s+", tts.strip())
        short_hook = sentences[0] if sentences else ""

    priority = score_short_for_expansion(title, research)

    # Construct a suggested long title based on the Short's title
    suggested_long_title = f"The Complete Story: {title}"

    # Build a generic why explanation
    why_parts = [f"The Short '{title}' covers a topic that benefits from deeper context."]
    if priority == "high":
        why_parts.append(
            "Topic contains high-engagement signals (fraud, AI, geopolitics, or shocking stats) "
            "that historically drive watch-time on documentary-format content."
        )
    else:
        why_parts.append(
            "Expanding with historical context, expert quotes, and multi-angle analysis "
            "can increase session depth and subscriber conversion."
        )
    why = " ".join(why_parts)

    return {
        "type": "short_to_long",
        "source_id": vid_id,
        "source_title": title,
        "source_hook": short_hook,
        "suggested_long_title": suggested_long_title,
        "why": why,
        "priority": priority,
        "estimated_duration_min": 12,
    }


def find_expansion_opportunities(pending: list[dict]) -> list[dict]:
    """Find Short videos that could expand to Long documentaries."""
    opportunities = []
    for entry in pending:
        vid_id = entry.get("id", "")
        if not vid_id.startswith("S"):
            continue
        # Only consider videos that have been scheduled (have a youtube_id)
        if not entry.get("youtube_id"):
            continue
        opp = build_expansion_opportunity(entry)
        opportunities.append(opp)
    return opportunities


# ─── Long → Short extraction ──────────────────────────────────────────────────

def extract_short_from_chapter(chapter: dict, parent_id: str, new_id: str) -> dict:
    """Convert a single Long video chapter into a Short idea entry."""
    ch_id    = chapter.get("id", "")
    ch_title = chapter.get("title", "")
    tts      = chapter.get("tts_script", "")

    # Hook = first sentence of the chapter tts_script
    sentences = re.split(r"(?<=[.!?])\s+", tts.strip())
    hook = sentences[0] if sentences else ch_title

    # Infer category from chapter title keywords
    category = _infer_category(ch_title + " " + tts[:200])

    # Derive a punchy short title from the chapter title
    short_title = ch_title
    if len(short_title) > 80:
        short_title = short_title[:77] + "..."

    return {
        "id": new_id,
        "title": short_title,
        "hook": hook,
        "category": category,
        "angle": "historical_fact",
        "source": "repackaged",
        "parent_id": parent_id,
        "source_chapter": ch_id,
    }


def _infer_category(text: str) -> str:
    text = text.lower()
    if any(w in text for w in ["islam", "muslim", "arab", "mosque", "quran", "prophet", "caliphate"]):
        return "islamic_history"
    if any(w in text for w in ["wealth", "rich", "billion", "economy", "money", "gdp", "bank"]):
        return "economics"
    if any(w in text for w in ["war", "military", "army", "battle", "weapon", "nuclear"]):
        return "geopolitics"
    if any(w in text for w in ["science", "invention", "discovery", "technology", "ai", "research"]):
        return "science_tech"
    if any(w in text for w in ["health", "medicine", "disease", "hospital", "drug"]):
        return "health"
    return "history"


def find_extraction_opportunities(pending: list[dict]) -> list[tuple[dict, list[dict]]]:
    """
    For each Long video, return a list of (entry, chapters) tuples.
    chapters is the list of extractable chapter dicts.
    """
    results = []
    for entry in pending:
        vid_id = entry.get("id", "")
        if not vid_id.startswith("L"):
            continue
        script = load_script(vid_id)
        if not script:
            continue
        chapters = script.get("chapters", [])
        if not chapters:
            continue
        results.append((entry, chapters))
    return results


# ─── Actions ──────────────────────────────────────────────────────────────────

def do_analyze(pending: list[dict]) -> tuple[list[dict], list[tuple[dict, list[dict]]]]:
    expansions    = find_expansion_opportunities(pending)
    extractions   = find_extraction_opportunities(pending)
    return expansions, extractions


def do_expand(expansions: list[dict]) -> None:
    """Save Short→Long suggestions to state/repackage_queue.json."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    existing = load_json(REPACKAGE_QUEUE) or {"last_analyzed": today, "opportunities": []}

    # Build a set of already-recorded source IDs
    existing_ids = {o["source_id"] for o in existing.get("opportunities", [])
                    if o.get("type") == "short_to_long"}

    added = 0
    for opp in expansions:
        if opp["source_id"] not in existing_ids:
            existing["opportunities"].append(opp)
            added += 1

    existing["last_analyzed"] = today
    save_json(REPACKAGE_QUEUE, existing)
    print(f"  Saved {added} new expansion suggestions → state/repackage_queue.json")


def do_extract(extractions: list[tuple[dict, list[dict]]]) -> None:
    """Add Long→Short clips to state/queue.json as new ideas."""
    queue_data = load_json(QUEUE_FILE) or {"ideas": []}
    if not isinstance(queue_data, dict):
        queue_data = {"ideas": queue_data}

    ideas = queue_data.get("ideas", [])

    # Find the current max short ID
    base_id = get_max_short_id()
    offset  = 1
    added   = 0

    # Track source chapters already in queue to avoid duplicates
    existing_sources = {
        (idea.get("parent_id"), idea.get("source_chapter"))
        for idea in ideas
        if idea.get("source") == "repackaged"
    }

    for entry, chapters in extractions:
        parent_id = entry["id"]
        for chapter in chapters:
            ch_id = chapter.get("id", "")
            if (parent_id, ch_id) in existing_sources:
                continue  # already added

            new_id  = next_short_id(base_id, offset)
            new_idea = extract_short_from_chapter(chapter, parent_id, new_id)
            ideas.append(new_idea)
            existing_sources.add((parent_id, ch_id))
            offset += 1
            added  += 1

    queue_data["ideas"] = ideas
    save_json(QUEUE_FILE, queue_data)
    print(f"  Added {added} new Short ideas → state/queue.json")


# ─── Display ──────────────────────────────────────────────────────────────────

PRIORITY_ICON = {"high": "🔥", "medium": "➡️ ", "low": "⬇️ "}

def print_report(
    pending: list[dict],
    expansions: list[dict],
    extractions: list[tuple[dict, list[dict]]],
) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    total_chapters = sum(len(chs) for _, chs in extractions)

    print()
    print("♻️   Repackage Analysis —", today)
    print(f"  Videos analyzed: {len(pending)}")
    print()

    # Short → Long
    print(f"  Short → Long opportunities ({len(expansions)}):")
    if expansions:
        for opp in expansions:
            icon = PRIORITY_ICON.get(opp["priority"], "  ")
            title = opp["source_title"][:50]
            print(f"    🔼 {opp['source_id']} — \"{title}\" → Long doc [{opp['priority'].upper()} priority]")
    else:
        print("    (none found — no Short videos with research data available)")

    print()

    # Long → Short
    print(f"  Long → Short extractions ({total_chapters} clips from {len(extractions)} long):")
    if extractions:
        for entry, chapters in extractions:
            for ch in chapters:
                ch_title = ch.get("title", ch.get("id", ""))[:55]
                print(f"    ✂️   {entry['id']} {ch.get('id','')} → \"{ch_title}\"")
    else:
        print("    (none found — no Long videos with chapters in output/)")

    print()
    if expansions:
        print("  Run with --expand to save Long expansion suggestions to repackage_queue.json")
    if total_chapters:
        print("  Run with --extract to add Short clips to queue.json")
    if not expansions and not total_chapters:
        print("  No repackaging opportunities found. Produce more videos to unlock this feature.")
    print()


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="FactForge repackaging — convert Shorts to Long docs and Long chapters to Shorts."
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        default=False,
        help="Show opportunities without making changes (default mode)",
    )
    parser.add_argument(
        "--extract",
        action="store_true",
        help="Add Long→Short clips to state/queue.json",
    )
    parser.add_argument(
        "--expand",
        action="store_true",
        help="Save Short→Long suggestions to state/repackage_queue.json",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run both --extract and --expand",
    )
    args = parser.parse_args()

    # Default to --analyze if no action flag is given
    if not (args.extract or args.expand or args.all):
        args.analyze = True

    pending = get_all_pending()
    if not pending:
        print("No pending videos found in state/pending_uploads.json")
        sys.exit(0)

    expansions, extractions = do_analyze(pending)

    # Always print the report
    print_report(pending, expansions, extractions)

    if args.expand or args.all:
        print("  [--expand] Saving Short→Long suggestions...")
        do_expand(expansions)

    if args.extract or args.all:
        print("  [--extract] Adding Long→Short clips to queue...")
        do_extract(extractions)


if __name__ == "__main__":
    main()
