"""
Fact Check Agent — Verifies facts against official sources before scripting.
All verification results saved to output/[id]/research.json
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import anthropic
from config.settings import ANTHROPIC_API_KEY, CLAUDE_MODEL_MAIN
from utils.web_search import search_web, fetch_page_text
from utils.file_manager import get_output_dir, update_progress_step, save_json, now_utc
from utils.token_optimizer import cache_get, cache_set


TIER1_DOMAINS = [
    "worldbank.org", "imf.org", "un.org", "cia.gov", "who.int",
    "sipri.org", "data.worldbank.org"
]
TIER2_DOMAINS = [
    "forbes.com", "bloomberg.com", "reuters.com", "apnews.com",
    "statista.com", "britannica.com", "worldhistory.org"
]


def _get_source_tier(url: str) -> int:
    for domain in TIER1_DOMAINS:
        if domain in url:
            return 1
    for domain in TIER2_DOMAINS:
        if domain in url:
            return 2
    return 3


def research_idea(idea: dict) -> dict:
    """
    Research an idea: search the web, extract facts, verify sources.
    Returns research dict with verified_facts, sources, confidence.
    """
    cache_key = f"research:{idea['id']}:{idea['title']}"
    cached = cache_get(cache_key)
    if cached:
        print(f"[fact_check] Using cached research for {idea['id']}")
        return cached

    print(f"[fact_check] Researching: {idea['title'][:60]}")

    # Search for facts
    search_query = f"{idea['title']} facts statistics official data"
    results = search_web(search_query, num_results=5)

    # Fetch content from top results
    source_texts = []
    for r in results[:3]:
        content = fetch_page_text(r["url"], max_chars=2000)
        source_texts.append({
            "url": r["url"],
            "title": r["title"],
            "content": content,
            "tier": _get_source_tier(r["url"]),
        })

    # Use Claude to extract and verify facts
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    key_facts = idea.get("key_facts", [])
    facts_to_verify = "\n".join([f"- {f}" for f in key_facts]) if key_facts else "Extract the key statistical facts"

    source_content = "\n\n".join([
        f"SOURCE [{s['tier']}] {s['url']}:\n{s['content'][:500]}"
        for s in source_texts
    ])

    prompt = f"""You are a fact-checker. Verify these claims from the provided sources.

VIDEO IDEA: {idea['title']}
CLAIMS TO VERIFY:
{facts_to_verify}

SOURCES FOUND:
{source_content}

For each claim, determine:
1. Is it supported by the sources? (yes/partial/no/unverifiable)
2. What is the exact verified wording?
3. What source(s) support it?
4. What qualifier is needed? (e.g., "as of 2023", "historians estimate", "adjusted for inflation")

Output JSON only:
{{
  "idea_id": "{idea['id']}",
  "research_date": "{now_utc()[:10]}",
  "verified_facts": [
    {{
      "claim": "exact verified claim text",
      "sources": [{{"url": "source_url", "tier": 1}}],
      "confidence": "high/medium/low",
      "qualifier": "as of 2023"
    }}
  ],
  "unverified_claims": [
    {{
      "claim": "claim text",
      "reason": "why it couldn't be verified",
      "decision": "exclude/include_with_qualifier"
    }}
  ],
  "overall_confidence": "high/medium/low",
  "sources_searched": {len(results)},
  "publishable": true
}}"""

    response = client.messages.create(
        model=CLAUDE_MODEL_MAIN,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    try:
        if "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
            if raw.startswith("json"):
                raw = raw[4:].strip()
        research = json.loads(raw)
    except json.JSONDecodeError:
        research = {
            "idea_id": idea["id"],
            "research_date": now_utc()[:10],
            "verified_facts": [],
            "unverified_claims": [],
            "overall_confidence": "low",
            "publishable": False,
            "error": "Failed to parse verification response",
            "raw_response": raw[:500],
        }

    # Cache for 24 hours
    cache_set(cache_key, research, ttl_hours=24)
    return research


def save_research(idea_id: str, research: dict) -> Path:
    """Save research results to output/[id]/research.json"""
    output_dir = get_output_dir(idea_id)
    research_path = output_dir / "research.json"
    save_json(research_path, research)
    update_progress_step("research_complete", idea_id)
    print(f"[fact_check] Research saved: {research_path}")
    return research_path


def is_publishable(research: dict) -> bool:
    """Check if idea has sufficient verified facts to produce a video."""
    if not research.get("publishable", True):
        return False
    verified = research.get("verified_facts", [])
    if len(verified) == 0:
        print("[fact_check] SKIP: No verified facts found")
        return False
    high_confidence = [f for f in verified if f.get("confidence") in ("high", "medium")]
    if len(high_confidence) == 0:
        print("[fact_check] SKIP: No medium/high confidence facts")
        return False
    return True


def run(idea: dict) -> tuple[dict, bool]:
    """
    Main entry point.
    Returns (research_dict, is_publishable)
    """
    research = research_idea(idea)
    save_research(idea["id"], research)
    publishable = is_publishable(research)

    if publishable:
        print(f"[fact_check] PASS: {len(research.get('verified_facts', []))} verified facts found")
    else:
        print(f"[fact_check] FAIL: Idea {idea['id']} cannot be published — insufficient verified facts")

    return research, publishable
