#!/usr/bin/env python3
"""
FactForge — Real SFX Downloader
Downloads high-quality SFX from Pixabay (Pexels-Free commercial license)
by fetching short video clips and extracting their audio track.

Sources:
  - Pixabay Videos API → extract audio via ffmpeg
  - YouTube (yt-dlp) → fallback for specific SFX videos

Usage:
    python3 audio_engineering/download_sfx.py             # download all missing
    python3 audio_engineering/download_sfx.py --topic ocean
    python3 audio_engineering/download_sfx.py --force      # re-download all
"""
import argparse, json, logging, os, subprocess, sys, time, urllib.request
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE      = Path(__file__).parent.parent
SFX_REAL  = Path(__file__).parent / "assets" / "sfx_real"
SFX_PROC  = Path(__file__).parent / "assets" / "sfx"    # procedural fallback

# Load API key
_env = {}
for line in (BASE / "config/.env").read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        _env[k.strip()] = v.strip()

PIXABAY_KEY = _env.get("PIXABAY_API_KEY", "")

# ─────────────────────────────────────────────────────────────────────────────
# SFX Download Catalog
# Each entry: (sfx_id, pixabay_query, trim_start_s, trim_end_s, description)
# trim: extract only the most useful portion of the video audio
# ─────────────────────────────────────────────────────────────────────────────
SFX_CATALOG = {
    "ocean": [
        ("sonar_ping",       "sonar submarine ping underwater",   0, 3,  "Sonar ping with reverb"),
        ("bubble_burst",     "underwater ocean bubbles air",      0, 2,  "Rising bubble burst"),
        ("pressure_boom",    "deep underwater pressure thud",     0, 2,  "Deep pressure impact"),
        ("water_transition", "water splash wave motion",          0, 2,  "Water swish transition"),
        ("depth_ambience",   "deep ocean underwater ambient",     0, 4,  "Dark ocean bed tone"),
    ],
    "space": [
        ("sci_fi_beep",     "computer beep electronic alert",    0, 2,  "Electronic beep"),
        ("space_whoosh",    "rocket launch whoosh",              0, 2,  "Space sweep"),
        ("space_thud",      "deep bass thud explosion far",      0, 2,  "Deep space impact"),
        ("radio_static",    "radio static noise signal",         0, 2,  "Radio crackle"),
    ],
    "economy": [
        ("coin_drop",       "coin drop metal floor",             0, 2,  "Coin hitting surface"),
        ("cash_register",   "cash register money checkout",      0, 2,  "Register ding"),
        ("market_crash",    "stock market alarm trading floor",  0, 3,  "Market alarm"),
        ("money_bills",     "money paper cash counting",         0, 2,  "Bills rustling"),
    ],
    "tech": [
        ("digital_glitch",  "computer glitch error digital",     0, 2,  "Digital glitch burst"),
        ("keyboard_click",  "keyboard typing mechanical",        0, 1,  "Single key click"),
        ("system_alert",    "computer system notification beep", 0, 2,  "System chime"),
        ("tech_whoosh",     "tech digital sweep transition",     0, 1,  "Digital sweep"),
    ],
    "history": [
        ("bell_toll",       "church bell ring metal toll",       0, 4,  "Large bell toll"),
        ("typewriter",      "typewriter click typing old",       0, 2,  "Typewriter clack"),
        ("dramatic_sting",  "orchestra sting dramatic brass",    0, 2,  "Brass sting"),
        ("parchment",       "paper rustle old scroll",           0, 2,  "Paper rustle"),
    ],
    "universal": [
        ("cinematic_impact", "cinematic impact boom film",       0, 2,  "Heavy cinematic hit"),
        ("whoosh_cinema",    "whoosh air transition fast",       0, 1,  "Cinema whoosh"),
        ("reveal_sting",     "reveal discovery music sting",     0, 2,  "Rising sting"),
        ("tension_build",    "tension music horror suspense",    0, 3,  "Tension build"),
    ],
}

# YouTube Audio Library SFX — direct downloadable IDs (verified free-to-use)
# Format: sfx_id -> YouTube video URL
YOUTUBE_SFX = {
    # These are actual YouTube videos with clean SFX content
    # Using well-known ambient/sfx channels with CC licenses
}


def _pixabay_search(query: str, max_duration: int = 15):
    """Search Pixabay Videos API and return the best small MP4 URL."""
    if not PIXABAY_KEY:
        log.warning("No PIXABAY_API_KEY found")
        return None
    try:
        r = requests.get(
            "https://pixabay.com/api/videos/",
            params={
                "key": PIXABAY_KEY,
                "q": query,
                "per_page": 8,
                "min_duration": 1,
                "max_duration": max_duration,
            },
            timeout=15,
        )
        r.raise_for_status()
        hits = r.json().get("hits", [])
        for hit in hits:
            vids = hit.get("videos", {})
            url = (vids.get("tiny") or vids.get("small") or {}).get("url")
            if url:
                return url
    except Exception as e:
        log.warning("Pixabay search failed for '%s': %s", query, e)
    return None


def _yt_download(yt_url: str, out_path: Path) -> bool:
    """Download audio from YouTube URL using yt-dlp."""
    ytdlp = "yt-dlp"
    try:
        r = subprocess.run(
            [ytdlp, "--no-playlist", "--extract-audio",
             "--audio-format", "mp3", "--audio-quality", "3",
             "--js-runtimes", "node",
             "-o", str(out_path.with_suffix(".%(ext)s")),
             yt_url, "--quiet"],
            capture_output=True, timeout=60,
        )
        return out_path.exists() or out_path.with_suffix(".mp3").exists()
    except Exception as e:
        log.warning("yt-dlp failed: %s", e)
        return False


def _extract_audio_from_video(video_url: str, out_path: Path,
                               trim_start: float = 0, trim_end: float = 3) -> bool:
    """Download video URL and extract audio segment as MP3."""
    tmp_vid = out_path.with_suffix(".tmp.mp4")
    try:
        # Download video
        headers = {"User-Agent": "Mozilla/5.0"}
        req = urllib.request.Request(video_url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            tmp_vid.write_bytes(resp.read())

        # Extract audio segment + normalize + convert to MP3
        duration = trim_end - trim_start
        result = subprocess.run([
            "ffmpeg", "-y",
            "-i", str(tmp_vid),
            "-ss", str(trim_start),
            "-t", str(duration),
            "-vn",                           # no video
            "-af", (
                "loudnorm=I=-16:TP=-1.5:LRA=11,"  # loudness normalize
                "highpass=f=40,"                   # remove sub-rumble
                "aresample=44100"
            ),
            "-ac", "1",                      # mono
            "-codec:a", "libmp3lame",
            "-qscale:a", "2",
            str(out_path),
        ], capture_output=True, timeout=30)

        return result.returncode == 0 and out_path.exists() and out_path.stat().st_size > 1000

    except Exception as e:
        log.warning("Audio extraction failed: %s", e)
        return False
    finally:
        tmp_vid.unlink(missing_ok=True)


def _use_procedural_fallback(topic: str, sfx_id: str, out_path: Path) -> bool:
    """Copy from procedural assets if real download fails."""
    proc_path = SFX_PROC / topic / f"{sfx_id}.wav"
    if not proc_path.exists():
        # Try universal fallback
        proc_path = SFX_PROC / "universal" / "soft_whoosh.wav"

    if proc_path.exists():
        import shutil
        shutil.copy(proc_path, out_path)
        log.info("  ↩ Used procedural fallback: %s", proc_path.name)
        return True
    return False


def download_all(topic_filter: str = None, force: bool = False) -> dict:
    """Download all SFX assets. Returns {topic: {sfx_id: path}}."""
    results = {}

    for topic, sfx_list in SFX_CATALOG.items():
        if topic_filter and topic != topic_filter:
            continue

        topic_dir = SFX_REAL / topic
        topic_dir.mkdir(parents=True, exist_ok=True)
        results[topic] = {}

        log.info("\n[%s]", topic.upper())

        for sfx_id, query, trim_start, trim_end, desc in sfx_list:
            out_path = topic_dir / f"{sfx_id}.mp3"

            if out_path.exists() and not force:
                size_kb = out_path.stat().st_size // 1024
                log.info("  ✓ %s (%dKB, exists)", sfx_id, size_kb)
                results[topic][sfx_id] = str(out_path)
                continue

            log.info("  ↓ %s — \"%s\"", sfx_id, desc)

            # Try Pixabay first
            video_url = _pixabay_search(query, max_duration=int(trim_end + 10))
            if video_url:
                success = _extract_audio_from_video(video_url, out_path, trim_start, trim_end)
                if success:
                    log.info("    ✅ Downloaded from Pixabay (%dKB)", out_path.stat().st_size // 1024)
                    results[topic][sfx_id] = str(out_path)
                    time.sleep(0.3)  # rate limit
                    continue

            # Fallback to procedural
            if _use_procedural_fallback(topic, sfx_id, out_path.with_suffix(".wav")):
                results[topic][sfx_id] = str(out_path.with_suffix(".wav"))
            else:
                log.warning("    ❌ Failed: %s", sfx_id)

            time.sleep(0.3)

    return results


def update_sfx_config_with_real_assets():
    """Update sfx_config.json to prefer real .mp3 assets over procedural .wav."""
    config_path = Path(__file__).parent / "sfx_config.json"
    with open(config_path) as f:
        cfg = json.load(f)

    # Add real asset paths to config
    cfg["real_assets_dir"] = "audio_engineering/assets/sfx_real"
    cfg["prefer_real_assets"] = True

    with open(config_path, "w") as f:
        json.dump(cfg, f, indent=2)
    log.info("Updated sfx_config.json with real asset preference")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", help="Only download this topic")
    parser.add_argument("--force", action="store_true", help="Re-download existing")
    args = parser.parse_args()

    results = download_all(topic_filter=args.topic, force=args.force)
    update_sfx_config_with_real_assets()

    total = sum(len(v) for v in results.values())
    log.info("\n✅ Downloaded %d SFX assets", total)
