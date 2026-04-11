"""
Title Agent — Builds title/metadata request for Claude Code.
Claude Code generates titles, description, tags, and translations.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.file_manager import get_output_dir, update_progress_step, save_json, now_utc


def score_title(title: str) -> int:
    """Local scoring (no AI needed) — pure rule-based from generate_title.md."""
    import re
    score = 0
    if re.search(r'\b\d+\b', title):
        score += 20
    power_words = ["secret", "banned", "hidden", "real", "actual", "exposed",
                   "revealed", "richer", "larger", "bigger", "times", "truth", "entire"]
    for w in power_words:
        if w.lower() in title.lower():
            score += 15
            break
    if any(w in title.lower() for w in ["why", "how", "the reason", "the truth"]):
        score += 25
    elif "vs" in title.lower() or "combined" in title.lower():
        score += 20
    if len(title) <= 60:
        score += 10
    if any(w in title.lower() for w in ["entire", "combined", "all of", "more than", "larger than"]):
        score += 20
    return score


def build_metadata_request(idea: dict, script_data: dict, research: dict) -> dict:
    """Build metadata generation request for Claude Code."""
    hook = script_data.get("hook", idea.get("hook", ""))
    verified_facts = research.get("verified_facts", [])
    sources = []
    for f in verified_facts:
        for s in f.get("sources", []):
            url = s.get("url", "")
            if url and url not in sources:
                sources.append(url)

    return {
        "task_type": "titles",
        "idea_id": idea["id"],
        "idea_title": idea["title"],
        "hook": hook,
        "category": idea.get("category", "general"),
        "format": idea.get("format", "shocking_stat"),
        "verified_sources": sources[:5],
        "skill_reference": ".claude/skills/generate_title.md",
        "output_schema": {
            "title_variants": [
                {"title": "...", "score": 0}
            ],
            "selected_title": "Best title",
            "description": "Full YouTube description with hook, bullets, sources, CTA, hashtags",
            "tags": ["tag1", "..."],
            "translations": {
                "es": {"title": "...", "description": "..."},
                "fr": {"title": "...", "description": "..."},
                "de": {"title": "...", "description": "..."},
                "hi": {"title": "...", "description": "..."},
                "pt": {"title": "...", "description": "..."},
                "id": {"title": "...", "description": "..."},
                "ja": {"title": "...", "description": "..."},
                "ko": {"title": "...", "description": "..."},
                "tr": {"title": "...", "description": "..."},
                "ar": {"title": "...", "description": "..."}
            },
            "category_id": "27"
        }
    }


def apply_local_scoring(metadata: dict) -> dict:
    """Re-score title variants locally and pick best."""
    variants = metadata.get("title_variants", [])
    for v in variants:
        v["local_score"] = score_title(v.get("title", ""))
    if variants:
        best = max(variants, key=lambda v: v.get("score", 0) + v.get("local_score", 0))
        metadata["selected_title"] = best["title"]
    return metadata


def save_metadata_request(idea_id: str, request: dict) -> Path:
    output_dir = get_output_dir(idea_id)
    path = output_dir / "metadata_request.json"
    save_json(path, request)
    print(f"[title_agent] Metadata request saved: {path}")
    return path


def save_metadata(idea_id: str, metadata: dict) -> Path:
    metadata = apply_local_scoring(metadata)
    metadata["idea_id"] = idea_id
    metadata["generated_at"] = now_utc()
    output_dir = get_output_dir(idea_id)
    path = output_dir / "metadata.json"
    save_json(path, metadata)
    update_progress_step("metadata_generated", idea_id)
    print(f"[title_agent] Metadata saved: {path}")
    print(f"[title_agent] Selected title: {metadata.get('selected_title', 'N/A')}")
    return path


def run(idea: dict, script_data: dict, research: dict) -> dict:
    """Build and save metadata request for Claude Code to process."""
    request = build_metadata_request(idea, script_data, research)
    save_metadata_request(idea["id"], request)
    return request
