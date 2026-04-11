"""
Script Agent — Prepares script request for Claude Code.
Claude Code writes the actual script (no API call needed).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.file_manager import get_output_dir, update_progress_step, save_json, now_utc
from utils.text_cleaner import prepare_for_tts, extract_pause_positions


def build_script_request(idea: dict, research: dict) -> dict:
    """
    Build structured script request for Claude Code to process.
    Claude Code reads write_script.md skill and returns the script.
    """
    verified_facts = research.get("verified_facts", [])
    if not verified_facts:
        # Fallback: use key_facts from idea directly
        verified_facts = [{"claim": f, "sources": []} for f in idea.get("key_facts", [])]

    facts_list = [f["claim"] for f in verified_facts]
    duration = idea.get("estimated_duration_seconds", 52)
    video_type = "short" if duration <= 60 else "long"

    return {
        "task_type": "script",
        "idea_id": idea["id"],
        "idea_title": idea["title"],
        "format": idea.get("format", "shocking_stat"),
        "category": idea.get("category", "general"),
        "hook": idea.get("hook", ""),
        "verified_facts": facts_list,
        "video_type": video_type,
        "target_duration_seconds": duration,
        "skill_reference": ".claude/skills/write_script.md",
        "output_schema": {
            "hook": "First shocking sentence (no greeting)",
            "build_up": "Build-up section with [PAUSE] tags",
            "peak": "[SLOW] Most shocking fact [PAUSE]",
            "cta": "Follow for more facts that will change how you see the world",
            "full_script": "Complete script with all [PAUSE][SLOW][FAST] tags",
            "word_count": 0,
            "estimated_duration_seconds": 0
        }
    }


def process_script_response(idea: dict, script_data: dict) -> dict:
    """Post-process Claude Code's script response: add TTS text and pause positions."""
    full_script = script_data.get("full_script", "")
    script_data["tts_text"] = prepare_for_tts(full_script)
    script_data["pause_positions"] = extract_pause_positions(full_script)
    script_data["idea_id"] = idea["id"]
    script_data["video_type"] = "short" if idea.get("estimated_duration_seconds", 52) <= 60 else "long"
    script_data["generated_at"] = now_utc()
    return script_data


def save_script(idea_id: str, script_data: dict) -> Path:
    output_dir = get_output_dir(idea_id)
    script_path = output_dir / "script.json"
    save_json(script_path, script_data)
    update_progress_step("script_written", idea_id)
    print(f"[script_agent] Script saved: {script_path}")
    return script_path


def save_script_request(idea_id: str, request: dict) -> Path:
    """Save the script request so Claude Code can read and fill it."""
    output_dir = get_output_dir(idea_id)
    request_path = output_dir / "script_request.json"
    save_json(request_path, request)
    print(f"[script_agent] Script request saved: {request_path}")
    return request_path


def run(idea: dict, research: dict) -> dict:
    """
    Main entry: build script request and save it.
    Claude Code processes it interactively and returns the script.
    """
    print(f"[script_agent] Building script request for: {idea['title'][:60]}")
    request = build_script_request(idea, research)
    save_script_request(idea["id"], request)
    return request  # Claude Code fills this in during produce session
