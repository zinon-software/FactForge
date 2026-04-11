"""
Title Agent — Generates hook titles, descriptions, tags, and translations.
Generates 5 title variants and scores them to pick the best.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import anthropic
from config.settings import ANTHROPIC_API_KEY, CLAUDE_MODEL_FAST, TRANSLATION_LANGUAGES
from utils.file_manager import get_output_dir, update_progress_step, save_json, now_utc
from utils.token_optimizer import select_model


def score_title(title: str) -> int:
    """Score a title using the generate_title.md formula."""
    import re
    score = 0

    # Contains specific number
    if re.search(r'\b\d+\b', title):
        score += 20

    # Contains power word
    power_words = ["secret", "banned", "hidden", "real", "actual", "exposed",
                   "revealed", "richer", "larger", "bigger", "times", "truth"]
    for word in power_words:
        if word.lower() in title.lower():
            score += 15
            break

    # Curiosity gap (question or "why/how/the reason")
    if any(w in title.lower() for w in ["why", "how", "the reason", "the truth", "what happened"]):
        score += 25
    elif "vs" in title.lower() or "compared" in title.lower():
        score += 20

    # Under 60 characters
    if len(title) <= 60:
        score += 10

    # Triggers debate (comparison or superlative)
    if any(w in title.lower() for w in ["entire", "combined", "all of", "more than", "larger than", "richer than"]):
        score += 20

    return score


def generate_titles_and_metadata(idea: dict, script_data: dict, research: dict) -> dict:
    """
    Generate 5 title variants, score them, pick best.
    Also generates description and tags.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    skill_path = Path(__file__).parent.parent / ".claude" / "skills" / "generate_title.md"
    skill_instructions = skill_path.read_text(encoding="utf-8") if skill_path.exists() else ""

    hook = script_data.get("hook", idea.get("hook", ""))
    verified_facts = research.get("verified_facts", [])
    sources = []
    for f in verified_facts:
        for s in f.get("sources", []):
            if s.get("url") not in sources:
                sources.append(s.get("url"))

    prompt = f"""Generate YouTube metadata for this video.

SKILL INSTRUCTIONS (title scoring):
{skill_instructions[:1500]}

VIDEO DETAILS:
- Hook: {hook}
- Title idea: {idea['title']}
- Format: {idea.get('format', 'shocking_stat')}
- Category: {idea.get('category', 'general')}

OUTPUT JSON only:
{{
  "title_variants": [
    {{"title": "Title 1", "score": 85}},
    {{"title": "Title 2", "score": 72}},
    {{"title": "Title 3", "score": 68}},
    {{"title": "Title 4", "score": 61}},
    {{"title": "Title 5", "score": 55}}
  ],
  "selected_title": "Highest scoring title",
  "description": "Full YouTube description with hook, bullet points, sources, CTA, hashtags",
  "tags": ["tag1", "tag2", ... 30 tags],
  "category_id": "27",
  "keywords": ["5 main keywords"]
}}

Description must include:
1. Hook sentence (from script)
2. "In this video:" + 3-5 bullet points
3. "Sources:" + list of verified source URLs
4. "New facts every 48 hours. Subscribe so you never miss one."
5. Relevant hashtags (#facts #history etc.)

Sources to cite: {', '.join(sources[:5]) if sources else 'See script research'}"""

    response = client.messages.create(
        model=select_model("title"),
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    try:
        if "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
            if raw.startswith("json"):
                raw = raw[4:].strip()
        metadata = json.loads(raw)
    except json.JSONDecodeError:
        metadata = {
            "title_variants": [{"title": idea["title"], "score": 50}],
            "selected_title": idea["title"],
            "description": f"{hook}\n\nSources: {', '.join(sources)}",
            "tags": ["facts", "history", "education"],
            "category_id": "27",
        }

    # Re-score titles with our scoring function
    for variant in metadata.get("title_variants", []):
        variant["score_local"] = score_title(variant.get("title", ""))

    # Pick best by combined score
    best = max(
        metadata.get("title_variants", [{"title": idea["title"], "score": 50}]),
        key=lambda t: t.get("score", 0) + t.get("score_local", 0)
    )
    metadata["selected_title"] = best["title"]
    metadata["idea_id"] = idea["id"]
    metadata["generated_at"] = now_utc()

    return metadata


def translate_metadata(metadata: dict, idea: dict) -> dict:
    """Translate title and description to all target languages."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    title = metadata.get("selected_title", "")
    description = metadata.get("description", "")[:500]  # Brief description for translation

    lang_names = {
        "es": "Spanish", "fr": "French", "de": "German",
        "hi": "Hindi", "pt": "Portuguese", "id": "Indonesian",
        "ja": "Japanese", "ko": "Korean", "tr": "Turkish", "ar": "Arabic"
    }

    prompt = f"""Translate this YouTube video title and brief description into 10 languages.
Translate the MEANING (not word-for-word). Keep numbers as numerals.
For Arabic, use Modern Standard Arabic (MSA).

TITLE: {title}
DESCRIPTION INTRO: {description[:200]}

OUTPUT JSON only — language code as key:
{{
  "es": {{"title": "...", "description": "..."}},
  "fr": {{"title": "...", "description": "..."}},
  "de": {{"title": "...", "description": "..."}},
  "hi": {{"title": "...", "description": "..."}},
  "pt": {{"title": "...", "description": "..."}},
  "id": {{"title": "...", "description": "..."}},
  "ja": {{"title": "...", "description": "..."}},
  "ko": {{"title": "...", "description": "..."}},
  "tr": {{"title": "...", "description": "..."}},
  "ar": {{"title": "...", "description": "..."}}
}}"""

    response = client.messages.create(
        model=select_model("translate"),
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    try:
        if "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
            if raw.startswith("json"):
                raw = raw[4:].strip()
        translations = json.loads(raw)
    except json.JSONDecodeError:
        print("[title_agent] Translation parsing failed — using English only")
        translations = {}

    metadata["translations"] = translations
    return metadata


def save_metadata(idea_id: str, metadata: dict) -> Path:
    """Save metadata to output/[id]/metadata.json"""
    output_dir = get_output_dir(idea_id)
    metadata_path = output_dir / "metadata.json"
    save_json(metadata_path, metadata)
    update_progress_step("metadata_generated", idea_id)
    print(f"[title_agent] Metadata saved: {metadata_path}")
    print(f"[title_agent] Selected title: {metadata.get('selected_title', 'N/A')}")
    return metadata_path


def run(idea: dict, script_data: dict, research: dict) -> dict:
    """Main entry point: generate all metadata."""
    print(f"[title_agent] Generating metadata for: {idea['id']}")
    metadata = generate_titles_and_metadata(idea, script_data, research)
    metadata = translate_metadata(metadata, idea)
    save_metadata(idea["id"], metadata)
    return metadata
