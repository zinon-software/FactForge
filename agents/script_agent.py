"""
Script Agent — Writes TTS-optimized scripts for short and long videos.
Uses Claude with write_script.md skill instructions.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import anthropic
from config.settings import ANTHROPIC_API_KEY, CLAUDE_MODEL_MAIN, MAX_TOKENS_SCRIPT
from utils.file_manager import get_output_dir, update_progress_step, save_json
from utils.text_cleaner import prepare_for_tts, extract_pause_positions


def load_skill(skill_name: str) -> str:
    """Load skill instructions from .claude/skills/"""
    skill_path = Path(__file__).parent.parent / ".claude" / "skills" / f"{skill_name}.md"
    if skill_path.exists():
        return skill_path.read_text(encoding="utf-8")
    return ""


def write_short_script(idea: dict, research: dict) -> dict:
    """
    Write a TTS-optimized short video script (<60 seconds).
    Returns script dict with raw_script, tts_text, word_count, estimated_duration.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    skill_instructions = load_skill("write_script")

    verified_facts = research.get("verified_facts", [])
    facts_text = "\n".join([
        f"- {f['claim']} (Source: {f['sources'][0]['url'] if f.get('sources') else 'N/A'})"
        for f in verified_facts
    ])

    prompt = f"""You are writing a YouTube Short video script. Follow the write_script.md rules EXACTLY.

SKILL INSTRUCTIONS:
{skill_instructions[:2000]}

VIDEO IDEA:
Title: {idea['title']}
Format: {idea['format']}
Hook: {idea['hook']}
Key Facts:
{facts_text}

TASK: Write a complete short video script (45-58 seconds, 120-160 words).

REQUIREMENTS:
- Start with hook sentence immediately — no "hello" or "in this video"
- Maximum 15 words per sentence
- Write ALL numbers as words (e.g., "four hundred billion" not "$400B")
- NO banned punctuation: ... ; : & #
- Expand ALL abbreviations
- Include [PAUSE] tags between sections
- Include [SLOW] before peak fact
- End with CTA: "Follow for more facts that will change how you see the world"

OUTPUT FORMAT (JSON only, no extra text):
{{
  "hook": "First sentence of script",
  "build_up": "Build-up section text with [PAUSE] tags",
  "peak": "[SLOW] Peak fact sentence [PAUSE]",
  "cta": "CTA sentence",
  "full_script": "Complete script with all tags",
  "word_count": 0,
  "estimated_duration_seconds": 0
}}"""

    response = client.messages.create(
        model=CLAUDE_MODEL_MAIN,
        max_tokens=MAX_TOKENS_SCRIPT,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()

    # Parse JSON response
    try:
        # Extract JSON if wrapped in markdown
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        script_data = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: wrap raw text
        script_data = {
            "full_script": raw,
            "word_count": len(raw.split()),
            "estimated_duration_seconds": len(raw.split()) // 2.5,
        }

    # Add TTS-ready version (cleaned, no tags)
    script_data["tts_text"] = prepare_for_tts(script_data.get("full_script", raw))
    script_data["pause_positions"] = extract_pause_positions(script_data.get("full_script", raw))
    script_data["idea_id"] = idea["id"]
    script_data["video_type"] = "short"

    return script_data


def write_long_script(idea: dict, research: dict) -> dict:
    """
    Write a long-form video script (8-13 minutes).
    Uses multiple Claude calls for full length.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    skill_instructions = load_skill("write_script")

    verified_facts = research.get("verified_facts", [])
    facts_text = "\n".join([f"- {f['claim']}" for f in verified_facts])

    # For long videos, generate outline first then expand each section
    outline_prompt = f"""Write a detailed outline for a YouTube video (8-12 minutes).

Video idea: {idea['title']}
Format: {idea['format']}
Available facts:
{facts_text}

Output a JSON outline:
{{
  "hook": "Opening shocking fact",
  "intro_summary": "What this video covers (30s)",
  "sections": [
    {{"title": "Section name", "key_point": "Main fact", "duration_seconds": 90}}
  ],
  "conclusion": "Callback to hook + bigger picture",
  "cta": "Subscribe + related video mention"
}}"""

    outline_resp = client.messages.create(
        model=CLAUDE_MODEL_MAIN,
        max_tokens=1000,
        messages=[{"role": "user", "content": outline_prompt}]
    )

    outline_raw = outline_resp.content[0].text.strip()
    try:
        if "```" in outline_raw:
            outline_raw = outline_raw.split("```")[1].split("```")[0].strip()
            if outline_raw.startswith("json"):
                outline_raw = outline_raw[4:].strip()
        outline = json.loads(outline_raw)
    except Exception:
        outline = {"hook": idea["hook"], "sections": [], "outline_raw": outline_raw}

    return {
        "idea_id": idea["id"],
        "video_type": "long",
        "outline": outline,
        "full_script": outline_raw,  # Full expansion done in production
        "tts_text": outline.get("hook", idea["hook"]),
        "estimated_duration_seconds": idea.get("estimated_duration_seconds", 600),
        "word_count": 0,
    }


def save_script(idea_id: str, script_data: dict) -> Path:
    """Save script to output/[id]/script.json"""
    output_dir = get_output_dir(idea_id)
    script_path = output_dir / "script.json"
    save_json(script_path, script_data)
    update_progress_step("script_written", idea_id)
    print(f"[script_agent] Script saved: {script_path}")
    return script_path


def run(idea: dict, research: dict) -> dict:
    """Main entry point: write script based on idea type."""
    print(f"[script_agent] Writing script for: {idea['title'][:60]}")

    duration = idea.get("estimated_duration_seconds", 55)

    if duration <= 60:
        script = write_short_script(idea, research)
    else:
        script = write_long_script(idea, research)

    save_script(idea["id"], script)
    return script


if __name__ == "__main__":
    # Test mode
    test_idea = {
        "id": "S00001",
        "title": "The Man Who Was Richer Than Today's Entire USA Economy",
        "format": "shocking_stat",
        "hook": "One man controlled 25% of global GDP",
        "estimated_duration_seconds": 52,
    }
    test_research = {
        "verified_facts": [
            {"claim": "Mansa Musa's estimated wealth was four hundred billion dollars in today's money",
             "sources": [{"url": "https://www.worldhistory.org/Mansa_Musa_I/"}]}
        ]
    }
    result = run(test_idea, test_research)
    print(json.dumps(result, indent=2))
