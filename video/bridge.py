"""
Video Bridge — Python to Remotion communication.
Generates Remotion props JSON and calls npx remotion render.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.file_manager import get_output_dir, update_progress_step

REMOTION_DIR = Path(__file__).parent / "remotion-project"


def map_category_to_theme(category: str) -> str:
    """Map content category to Remotion color theme."""
    mapping = {
        "islamic_arab_history": "islamic",
        "ancient_civilizations": "ancient",
        "wealth_economics": "wealth",
        "military_geopolitics": "military",
        "science_space": "science",
        "us_vs_china": "science",
        "east_vs_west": "general",
    }
    return mapping.get(category, "general")


def build_short_props(idea: dict, script_data: dict, audio_path: Path, bg_video_url: str = None) -> dict:
    """Build Remotion props for a short video."""
    segments = []
    fps = 60

    # Build segments from script structure
    full_script = script_data.get("full_script", "")
    hook = script_data.get("hook", idea.get("hook", ""))

    # Split script into segments for visual display
    lines = [line.strip() for line in full_script.replace("[PAUSE]", "\n").split("\n") if line.strip()]
    # Remove tag lines
    lines = [l for l in lines if not l.startswith("[")]

    frame = int(fps * 3)  # Start after hook (3 seconds)
    for line in lines[:8]:  # Max 8 visible segments
        duration = max(int(fps * (len(line.split()) / 2.5)), fps * 3)  # Min 3 seconds per line
        segments.append({
            "text": line[:100],
            "startFrame": frame,
            "endFrame": frame + duration,
        })
        frame += duration + int(fps * 0.5)  # 0.5s gap

    total_frames = min(frame + int(fps * 5), fps * 58)  # Cap at 58 seconds

    return {
        "videoId": idea["id"],
        "hook": hook[:120],
        "segments": segments,
        "audioFile": str(audio_path.absolute()) if audio_path and audio_path.exists() else None,
        "backgroundVideoUrl": bg_video_url,
        "colorTheme": map_category_to_theme(idea.get("category", "general")),
        "format": idea.get("format", "shocking_stat"),
        "_total_frames": total_frames,
    }


def build_long_props(idea: dict, script_data: dict, audio_path: Path, bg_video_url: str = None) -> dict:
    """Build Remotion props for a long video from outline."""
    fps = 30
    outline = script_data.get("outline", {})
    sections_raw = outline.get("sections", [])

    sections = []
    frame = fps * 5  # 5-second intro
    for sec in sections_raw:
        duration_sec = sec.get("duration_seconds", 90)
        sections.append({
            "heading": sec.get("title", "")[:50],
            "text": sec.get("key_point", "")[:200],
            "startFrame": frame,
            "durationInFrames": fps * duration_sec,
        })
        frame += fps * duration_sec

    return {
        "videoId": idea["id"],
        "title": idea["title"],
        "sections": sections,
        "audioFile": str(audio_path.absolute()) if audio_path and audio_path.exists() else None,
        "backgroundVideoUrl": bg_video_url,
        "colorTheme": map_category_to_theme(idea.get("category", "general")),
        "_total_frames": frame + fps * 10,
    }


def render_video(idea: dict, props: dict, video_type: str = "short") -> Path:
    """
    Call Remotion CLI to render the video.
    Returns path to output video file.
    """
    output_dir = get_output_dir(idea["id"])
    output_path = output_dir / "video.mp4"
    props_path = output_dir / "remotion_props.json"

    # Extract internal meta before passing to Remotion
    total_frames = props.pop("_total_frames", 60 * 55)
    duration_frames = min(total_frames, 60 * 58 if video_type == "short" else 30 * 780)

    # Save props to JSON file
    with open(props_path, "w") as f:
        json.dump(props, f, indent=2)

    composition = "ShortVideo" if video_type == "short" else "LongVideo"

    cmd = [
        "npx", "remotion", "render",
        composition,
        str(output_path),
        "--props", str(props_path.absolute()),
        "--frames", f"0-{duration_frames - 1}",
        "--log", "error",
    ]

    print(f"[video_bridge] Rendering {composition} → {output_path.name}")
    print(f"  Duration: {duration_frames} frames")

    env = {**os.environ, "CI": "1"}  # Disable interactive prompts

    try:
        result = subprocess.run(
            cmd,
            cwd=str(REMOTION_DIR),
            capture_output=True,
            text=True,
            timeout=600,
            env=env,
        )

        if result.returncode != 0:
            print(f"[video_bridge] Render error:\n{result.stderr[-1000:]}")
            return None

        print(f"[video_bridge] Render complete: {output_path}")
        update_progress_step("video_rendered", idea["id"])
        return output_path

    except subprocess.TimeoutExpired:
        print("[video_bridge] ERROR: Render timed out after 10 minutes")
        return None
    except Exception as e:
        print(f"[video_bridge] ERROR: {e}")
        return None


def run(idea: dict, script_data: dict, audio_path: Path, bg_video_url: str = None) -> Path | None:
    """Main entry point: build props and render video."""
    duration = idea.get("estimated_duration_seconds", 55)
    video_type = "short" if duration <= 60 else "long"

    if video_type == "short":
        props = build_short_props(idea, script_data, audio_path, bg_video_url)
    else:
        props = build_long_props(idea, script_data, audio_path, bg_video_url)

    return render_video(idea, props, video_type)
