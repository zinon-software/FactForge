"""
Fact Check Agent — Verifies facts via web search + Claude Code review.
Claude Code (not API) reads search results and verifies claims.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.web_search import search_web, fetch_page_text
from utils.file_manager import get_output_dir, update_progress_step, save_json, now_utc
from utils.token_optimizer import cache_get, cache_set

TIER1_DOMAINS = [
    "worldbank.org", "imf.org", "un.org", "cia.gov", "who.int", "sipri.org"
]
TIER2_DOMAINS = [
    "forbes.com", "bloomberg.com", "reuters.com", "apnews.com",
    "statista.com", "britannica.com", "worldhistory.org"
]


def _get_source_tier(url: str) -> int:
    for d in TIER1_DOMAINS:
        if d in url:
            return 1
    for d in TIER2_DOMAINS:
        if d in url:
            return 2
    return 3


def search_facts(idea: dict) -> list[dict]:
    """Web search for facts — returns raw search results for Claude Code to verify."""
    cache_key = f"search:{idea['id']}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    query = f"{idea['title']} facts statistics official data"
    results = search_web(query, num_results=5)

    enriched = []
    for r in results[:3]:
        content = fetch_page_text(r["url"], max_chars=1500)
        enriched.append({
            "url": r["url"],
            "title": r["title"],
            "snippet": r["snippet"],
            "content": content,
            "tier": _get_source_tier(r["url"]),
        })

    cache_set(cache_key, enriched, ttl_hours=24)
    return enriched


def build_research_request(idea: dict, search_results: list[dict]) -> dict:
    """
    Build a structured research request for Claude Code to process.
    Claude Code reads this, verifies facts, and writes back research.json.
    """
    return {
        "task_type": "research",
        "idea_id": idea["id"],
        "idea_title": idea["title"],
        "idea_hook": idea.get("hook", ""),
        "key_facts_to_verify": idea.get("key_facts", []),
        "search_results": [
            {
                "url": r["url"],
                "tier": r["tier"],
                "content_excerpt": r["content"][:800],
            }
            for r in search_results
        ],
        "output_schema": {
            "verified_facts": [
                {
                    "claim": "exact verified claim",
                    "sources": [{"url": "...", "tier": 1}],
                    "confidence": "high|medium|low",
                    "qualifier": "as of 2024 / historians estimate / etc."
                }
            ],
            "unverified_claims": [
                {
                    "claim": "...",
                    "reason": "why unverifiable",
                    "decision": "exclude|include_with_qualifier"
                }
            ],
            "overall_confidence": "high|medium|low",
            "publishable": True,
            "sources_searched": 0
        }
    }


def save_research(idea_id: str, research: dict) -> Path:
    output_dir = get_output_dir(idea_id)
    research_path = output_dir / "research.json"
    research.setdefault("idea_id", idea_id)
    research.setdefault("research_date", now_utc()[:10])
    save_json(research_path, research)
    update_progress_step("research_complete", idea_id)
    print(f"[fact_check] Research saved: {research_path}")
    return research_path


def is_publishable(research: dict) -> bool:
    if not research.get("publishable", True):
        return False
    verified = research.get("verified_facts", [])
    if not verified:
        return False
    good = [f for f in verified if f.get("confidence") in ("high", "medium")]
    return len(good) > 0


def run(idea: dict) -> tuple[dict, bool]:
    """
    Main entry point.
    1. Searches web for facts (automated)
    2. Writes request for Claude Code to verify
    3. Returns (research_dict, is_publishable)

    In interactive mode (main.py produce): Claude Code reads and processes the request.
    """
    print(f"[fact_check] Searching facts for: {idea['title'][:60]}")
    search_results = search_facts(idea)

    # Build and save request for Claude Code
    request = build_research_request(idea, search_results)
    output_dir = get_output_dir(idea["id"])
    request_path = output_dir / "research_request.json"
    save_json(request_path, request)

    print(f"[fact_check] Research request saved: {request_path}")
    print(f"[fact_check] Found {len(search_results)} sources (tiers: {[r['tier'] for r in search_results]})")

    return request, True  # Claude Code will complete verification interactively
