"""
Video Agent — Orchestrates video production using the Remotion bridge.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.web_search import get_pexels_media
from video.bridge import run as render_video


def get_background_video(idea: dict) -> str | None:
    """Search Pexels for a relevant background video."""
    # Build search query from idea content
    key_facts = idea.get("key_facts", [])
    category = idea.get("category", "")
    title = idea["title"]

    # Map category to search terms that get good Pexels results
    search_map = {
        "islamic_arab_history": "ancient architecture desert",
        "wealth_economics": "city skyline financial",
        "military_geopolitics": "world map globe",
        "science_space": "space galaxy stars",
        "ancient_civilizations": "ancient ruins stone",
        "modern_technology_ai": "technology digital data",
        "natural_world": "nature landscape aerial",
    }

    query = search_map.get(category, " ".join(title.split()[:3]))
    media = get_pexels_media(query, media_type="videos", per_page=3)

    if media:
        print(f"[video_agent] Background video: {media[0]['url'][:60]}...")
        return media[0]["url"]

    return None


def run(idea: dict, script_data: dict, audio_path: Path) -> Path | None:
    """Main entry point: get background and render video."""
    print(f"[video_agent] Starting video production for: {idea['id']}")

    bg_video_url = get_background_video(idea)
    output_path = render_video(idea, script_data, audio_path, bg_video_url)

    if output_path and output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"[video_agent] Video ready: {output_path} ({size_mb:.1f}MB)")
    else:
        print(f"[video_agent] Video render failed for {idea['id']}")

    return output_path
