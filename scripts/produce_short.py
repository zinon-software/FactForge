"""
produce_short.py — Unified Short Video Production Pipeline for FactForge
Runs the full pipeline from script → audio → render → upload in one command.

Usage:
    python3 scripts/produce_short.py <video_id>
    python3 scripts/produce_short.py --next      # picks next unproduced Short from queue

Pipeline steps (resumable via checkpoint):
    1. LOAD        — read script.json for tts_text_final
    2. AUDIO       — Kokoro am_echo TTS → audio.mp3
    3. TIMESTAMPS  — faster-whisper word timestamps → word_timestamps.json
    4. BG_VIDEOS   — fetch Pexels clips from segment queries → bg_videos/
    5. PROPS       — verify remotion_props.json exists
    6. COPY_PUBLIC — copy audio + bg_videos to remotion public/
    7. RENDER      — render_short.py → video.mp4
    8. THUMBNAIL   — Pollinations Flux + Pillow → thumbnail.jpg (if missing)
    9. UPLOAD      — YouTube API upload (scheduled private)
    10. CLEAN      — delete large files, keep metadata/script/thumbnail
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import requests

# ─── Paths ────────────────────────────────────────────────────────────────────
ROOT         = Path(__file__).parent.parent
SCRIPTS_DIR  = ROOT / "scripts"
OUTPUT_DIR   = ROOT / "output"
PUBLIC_DIR   = ROOT / "video/remotion-project/public"
CONFIG_DIR   = ROOT / "config"
MODELS_DIR   = ROOT / "models/kokoro"

# ─── Kokoro config ────────────────────────────────────────────────────────────
KOKORO_MODEL  = MODELS_DIR / "kokoro-v1.0.onnx"
KOKORO_VOICES = MODELS_DIR / "voices-v1.0.bin"
KOKORO_VOICE  = "am_echo"
KOKORO_SPEED  = 1.08

# ─── Whisper config ───────────────────────────────────────────────────────────
WHISPER_MODEL = "base"

# ─── Video config ─────────────────────────────────────────────────────────────
SHORT_FPS = 60

# ─── Pexels config ────────────────────────────────────────────────────────────
PEXELS_API_KEY: Optional[str] = None  # loaded lazily


def _load_pexels_key() -> str:
    global PEXELS_API_KEY
    if PEXELS_API_KEY:
        return PEXELS_API_KEY
    # Try environment first
    key = os.getenv("PEXELS_API_KEY")
    if not key:
        env_file = CONFIG_DIR / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("PEXELS_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not key:
        raise RuntimeError(
            "PEXELS_API_KEY not found in environment or config/.env"
        )
    PEXELS_API_KEY = key
    return PEXELS_API_KEY


# ─── Files to keep after clean ───────────────────────────────────────────────
KEEP_FILES = {
    "metadata.json",
    "script.json",
    "research.json",
    "sources.json",
    "thumbnail.jpg",
    "remotion_props.json",
    "word_timestamps.json",
    "produce_checkpoint.json",
}

CLEAN_PATTERNS = [
    "video.mp4",
    "video_noaudio.mp4",
    "audio.mp3",
    "*.wav",
]

CLEAN_DIRS = ["bg_videos"]


# ══════════════════════════════════════════════════════════════════════════════
# CHECKPOINT HELPERS
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_CHECKPOINT = {
    "audio": False,
    "timestamps": False,
    "bg_videos": False,
    "render": False,
    "upload": False,
    "clean": False,
}


def load_checkpoint(video_id: str) -> dict:
    cp_path = OUTPUT_DIR / video_id / "produce_checkpoint.json"
    if cp_path.exists():
        return json.loads(cp_path.read_text())
    return dict(DEFAULT_CHECKPOINT)


def save_checkpoint(video_id: str, cp: dict) -> None:
    cp_path = OUTPUT_DIR / video_id / "produce_checkpoint.json"
    cp_path.write_text(json.dumps(cp, indent=2))


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — LOAD script
# ══════════════════════════════════════════════════════════════════════════════

def step_load(video_id: str) -> dict:
    """Read script.json and return the script dict."""
    script_path = OUTPUT_DIR / video_id / "script.json"
    if not script_path.exists():
        raise FileNotFoundError(f"script.json not found: {script_path}")
    script = json.loads(script_path.read_text())
    tts_text = (
        script.get("tts_text_final")
        or script.get("full_text")
        or script.get("tts_script")
        or ""
    )
    if not tts_text:
        raise ValueError(
            f"script.json for {video_id} has no tts_text_final / full_text / tts_script"
        )
    print(f"  Script loaded ({len(tts_text)} chars)")
    return script


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — AUDIO (Kokoro TTS)
# ══════════════════════════════════════════════════════════════════════════════

def step_audio(video_id: str, tts_text: str, cp: dict) -> float:
    """Generate audio.mp3 with Kokoro. Returns duration in seconds."""
    audio_path = OUTPUT_DIR / video_id / "audio.mp3"

    if cp["audio"] and audio_path.exists():
        print("  [SKIP] audio.mp3 already exists")
        return _get_audio_duration(audio_path)

    print(f"  Generating Kokoro TTS ({KOKORO_VOICE}, speed={KOKORO_SPEED})...")

    import soundfile as sf
    from kokoro_onnx import Kokoro

    kokoro = Kokoro(str(KOKORO_MODEL), str(KOKORO_VOICES))
    samples, sr = kokoro.create(tts_text, voice=KOKORO_VOICE, speed=KOKORO_SPEED, lang="en-us")

    wav_path = OUTPUT_DIR / video_id / "audio.wav"
    sf.write(str(wav_path), samples, sr)

    result = subprocess.run(
        ["ffmpeg", "-y", "-i", str(wav_path), "-b:a", "192k", str(audio_path)],
        capture_output=True,
        text=True,
    )
    wav_path.unlink(missing_ok=True)

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg WAV→MP3 failed:\n{result.stderr[-500:]}")

    duration = len(samples) / sr
    print(f"  Audio: {audio_path.name} ({duration:.1f}s)")
    return duration


def _get_audio_duration(audio_path: Path) -> float:
    r = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            str(audio_path),
        ],
        capture_output=True,
        text=True,
    )
    info = json.loads(r.stdout)
    return float(info["format"]["duration"])


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — TIMESTAMPS (faster-whisper)
# ══════════════════════════════════════════════════════════════════════════════

def step_timestamps(video_id: str, cp: dict) -> list:
    """Extract word-level timestamps. Returns list of {word, start_ms, end_ms}."""
    ts_path    = OUTPUT_DIR / video_id / "word_timestamps.json"
    audio_path = OUTPUT_DIR / video_id / "audio.mp3"

    if cp["timestamps"] and ts_path.exists():
        print("  [SKIP] word_timestamps.json already exists")
        return json.loads(ts_path.read_text())

    print("  Extracting word timestamps (faster-whisper base)...")

    from faster_whisper import WhisperModel

    model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(
        str(audio_path),
        word_timestamps=True,
        language="en",
        beam_size=5,
    )

    words: list = []
    for seg in segments:
        for w in seg.words:
            word = w.word.strip()
            if not word:
                continue
            words.append(
                {
                    "word": word,
                    "start_ms": round(w.start * 1000),
                    "end_ms": round(w.end * 1000),
                }
            )

    ts_path.write_text(json.dumps(words, indent=2))
    last_ms = words[-1]["end_ms"] / 1000 if words else 0
    print(f"  Timestamps: {len(words)} words, last at {last_ms:.1f}s")
    return words


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — BG_VIDEOS (Pexels)
# ══════════════════════════════════════════════════════════════════════════════

def _query_from_filename(bg_video_path: str) -> str:
    """
    Extract a human-readable Pexels search query from a segment backgroundVideo path.
    e.g. "S00893/bg_videos/mosque_dome.mp4" → "mosque dome"
    """
    name = Path(bg_video_path).stem          # "mosque_dome"
    query = re.sub(r"[_\-]+", " ", name)     # "mosque dome"
    query = re.sub(r"\s+", " ", query).strip()
    return query


def _fetch_pexels_video(
    query: str,
    out_path: Path,
    api_key: str,
    used_pexels_ids: set,
    fallback_queries: list = None,
) -> bool:
    """
    Download a unique HD Pexels video matching query.
    - Fetches per_page=15 results and skips already-used Pexels video IDs.
    - If no unused result found, tries each fallback_queries in order.
    - Returns True on success.
    """
    headers = {"Authorization": api_key}
    all_queries = [query] + (fallback_queries or [])

    for attempt_query in all_queries:
        params = {
            "query": attempt_query,
            "per_page": 15,
            "size": "medium",
            "orientation": "portrait",
        }
        r = requests.get(
            "https://api.pexels.com/videos/search",
            headers=headers,
            params=params,
            timeout=30,
        )
        if r.status_code != 200:
            print(f"    ⚠️  Pexels API error {r.status_code} for '{attempt_query}'")
            continue

        videos = r.json().get("videos", [])
        if not videos:
            print(f"    ⚠️  No Pexels results for '{attempt_query}'")
            continue

        # Pick first video NOT already used
        for vid in videos:
            pexels_id = vid["id"]
            if pexels_id in used_pexels_ids:
                continue  # skip — already used in this video

            # Find best MP4 file (prefer hd over sd)
            files = sorted(
                vid.get("video_files", []),
                key=lambda f: 1 if f.get("quality") == "hd" else 0,
                reverse=True,
            )
            video_file_url = next(
                (
                    f["link"]
                    for f in files
                    if f.get("quality") in ("hd", "sd")
                    and f.get("file_type") == "video/mp4"
                ),
                None,
            )
            if not video_file_url:
                continue

            dl = requests.get(video_file_url, timeout=120, stream=True)
            dl.raise_for_status()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "wb") as fh:
                for chunk in dl.iter_content(chunk_size=1024 * 256):
                    fh.write(chunk)

            used_pexels_ids.add(pexels_id)
            source_label = f"(query: '{attempt_query}')" if attempt_query != query else ""
            print(
                f"    ✓ {out_path.name} — pexels#{pexels_id} {source_label}"
                f" ({out_path.stat().st_size // 1024}KB)"
            )
            return True

        print(f"    ⚠️  All {len(videos)} results for '{attempt_query}' already used — trying next query")

    print(f"    ✗ Could not find unique video for '{query}' after all fallbacks")
    return False


# ─── Fallback query chains per segment type ──────────────────────────────────
# When the primary scene_query fails or produces a duplicate, these generic
# queries ensure every segment gets a visually distinct clip.
_TYPE_FALLBACKS = {
    "hook":   ["dramatic reveal", "cinematic landscape", "aerial city"],
    "fact":   ["documentary footage", "world map", "research data"],
    "impact": ["explosion effect", "shock wave", "dramatic moment"],
    "number": ["financial data", "statistics screen", "stock market"],
    "cta":    ["subscribe notification", "social media phone", "modern city"],
}
_GENERIC_FALLBACKS = ["city aerial", "nature landscape", "technology abstract", "ocean waves", "crowd people"]


def step_bg_videos(video_id: str, cp: dict) -> None:
    """
    Fetch unique Pexels background videos for every segment.
    Priority order for query:
      1. seg['scene_query']  — direct semantic description from script writing
      2. filename-derived    — fallback from backgroundVideo path
    Deduplication: tracks used Pexels video IDs so no two segments share the same clip.
    """
    props_path = OUTPUT_DIR / video_id / "remotion_props.json"
    if not props_path.exists():
        raise FileNotFoundError(f"remotion_props.json not found for {video_id}")

    props = json.loads(props_path.read_text())
    segments = props.get("segments", [])

    if not segments:
        print("  No segments in remotion_props.json — skipping bg_videos")
        return

    if cp["bg_videos"]:
        print("  [SKIP] bg_videos already fetched")
        return

    api_key = _load_pexels_key()
    bg_dir  = OUTPUT_DIR / video_id / "bg_videos"
    bg_dir.mkdir(parents=True, exist_ok=True)

    used_pexels_ids: set = set()
    print(f"  Fetching {len(segments)} unique Pexels background clips...")
    failed = 0

    for i, seg in enumerate(segments):
        bg_path_str: str = seg.get("backgroundVideo", "")
        if not bg_path_str:
            continue

        out_filename = Path(bg_path_str).name   # e.g. "mosque_dome.mp4"
        out_path     = bg_dir / out_filename

        if out_path.exists() and out_path.stat().st_size > 10_000:
            print(f"    [SKIP] {out_filename} already downloaded")
            continue

        # Prefer explicit scene_query written by Claude during script creation
        primary_query = seg.get("scene_query") or _query_from_filename(bg_path_str)
        seg_type      = seg.get("type", "fact")
        fallbacks     = _TYPE_FALLBACKS.get(seg_type, []) + _GENERIC_FALLBACKS

        print(f"    [{i+1}/{len(segments)}] '{primary_query}' → {out_filename}")

        ok = _fetch_pexels_video(primary_query, out_path, api_key, used_pexels_ids, fallbacks)
        if not ok:
            failed += 1
        # Polite rate limit
        time.sleep(0.5)

    if failed > 0:
        print(f"  ⚠️  {failed}/{len(segments)} clips failed to download")

    print(f"  bg_videos ready in {bg_dir} ({len(segments) - failed} unique clips)")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — PROPS verification
# ══════════════════════════════════════════════════════════════════════════════

def step_verify_props(video_id: str) -> dict:
    """Verify remotion_props.json exists and is valid."""
    props_path = OUTPUT_DIR / video_id / "remotion_props.json"
    if not props_path.exists():
        raise FileNotFoundError(
            f"remotion_props.json not found for {video_id}. "
            "This file must be created by Claude Code before running produce_short.py."
        )
    props = json.loads(props_path.read_text())
    total = props.get("totalDurationFrames", 0)
    segs  = len(props.get("segments", []))
    print(f"  Props verified: {total} frames ({total / SHORT_FPS:.1f}s), {segs} segments")
    return props


# ══════════════════════════════════════════════════════════════════════════════
# STEP 6 — COPY TO REMOTION PUBLIC
# ══════════════════════════════════════════════════════════════════════════════

def step_copy_public(video_id: str) -> None:
    """Copy audio.mp3 and bg_videos/ to remotion public/<id>/."""
    pub_dir = PUBLIC_DIR / video_id
    pub_dir.mkdir(parents=True, exist_ok=True)

    # Audio
    audio_src = OUTPUT_DIR / video_id / "audio.mp3"
    audio_dst = pub_dir / "audio.mp3"
    if not audio_src.exists():
        raise FileNotFoundError(f"audio.mp3 not found at {audio_src}")
    shutil.copy2(audio_src, audio_dst)
    print(f"  Copied audio → public/{video_id}/audio.mp3")

    # bg_videos
    bg_src = OUTPUT_DIR / video_id / "bg_videos"
    bg_dst = pub_dir / "bg_videos"
    if bg_src.exists() and any(bg_src.iterdir()):
        if bg_dst.exists():
            shutil.rmtree(bg_dst)
        shutil.copytree(bg_src, bg_dst)
        count = len(list(bg_dst.glob("*.mp4")))
        print(f"  Copied {count} bg_videos → public/{video_id}/bg_videos/")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 7 — RENDER
# ══════════════════════════════════════════════════════════════════════════════

def step_render(video_id: str, cp: dict) -> None:
    """Run render_short.py to produce video.mp4."""
    video_path = OUTPUT_DIR / video_id / "video.mp4"

    if cp["render"] and video_path.exists():
        print("  [SKIP] video.mp4 already rendered")
        return

    render_script = SCRIPTS_DIR / "render_short.py"
    print(f"  Rendering {video_id} via render_short.py...")

    result = subprocess.run(
        [sys.executable, str(render_script), video_id],
        capture_output=False,
        timeout=3600,
    )
    if result.returncode != 0:
        raise RuntimeError(f"render_short.py failed with exit code {result.returncode}")

    if not video_path.exists():
        raise RuntimeError(f"Render completed but video.mp4 not found at {video_path}")

    size_mb = video_path.stat().st_size // (1024 * 1024)
    print(f"  ✅ video.mp4 ready ({size_mb} MB)")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 8 — THUMBNAIL
# ══════════════════════════════════════════════════════════════════════════════

def _build_thumbnail_prompt(script: dict, video_id: str) -> str:
    """Derive a Pollinations prompt from script metadata."""
    title = script.get("title", "") or script.get("video_title", "")
    category = script.get("category", "")
    hook = script.get("hook", "") or script.get("opening_hook", "")
    base = title or hook or f"FactForge {video_id}"
    prompt = (
        f"Cinematic 4K background for YouTube thumbnail, vivid dramatic lighting, "
        f"topic: {base[:80]}, category: {category}, "
        "no text, no watermarks, high contrast, stunning visual impact"
    )
    return prompt


def step_thumbnail(video_id: str, script: dict) -> None:
    """Generate thumbnail.jpg if it doesn't exist."""
    thumb_path = OUTPUT_DIR / video_id / "thumbnail.jpg"

    if thumb_path.exists() and thumb_path.stat().st_size > 5_000:
        print("  [SKIP] thumbnail.jpg already exists")
        return

    try:
        from PIL import Image, ImageDraw, ImageFont
        from io import BytesIO
    except ImportError:
        print("  ⚠️  Pillow not installed — skipping thumbnail generation")
        return

    W, H = 1280, 720
    prompt = _build_thumbnail_prompt(script, video_id)
    title  = script.get("title") or script.get("video_title") or video_id
    stat   = _extract_hero_stat(script)

    print(f"  Generating Pollinations thumbnail: {prompt[:60]}...")

    # Fetch AI background
    url = (
        f"https://image.pollinations.ai/prompt/{quote(prompt)}"
        f"?width={W}&height={H}&nologo=true&model=flux&seed=42"
    )
    bg_img = None
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=90)
            if r.status_code == 200 and len(r.content) > 5000:
                bg_img = Image.open(BytesIO(r.content)).convert("RGB")
                bg_img = bg_img.resize((W, H), Image.Resampling.LANCZOS)
                break
            print(f"    Retry {attempt+1} (status {r.status_code})")
        except Exception as exc:
            print(f"    Retry {attempt+1} ({exc})")
        time.sleep(5)

    if bg_img is None:
        # Fallback: dark gradient
        bg_img = Image.new("RGB", (W, H), (20, 20, 30))

    draw = ImageDraw.Draw(bg_img)

    # Dark gradient overlay on bottom half
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    for y in range(H // 2, H):
        alpha = int(200 * (y - H // 2) / (H // 2))
        ov_draw.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
    bg_img = Image.alpha_composite(bg_img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(bg_img)

    # Top accent bar
    draw.rectangle([(0, 0), (W, 10)], fill=(255, 200, 0))

    # Stat (hero number)
    def get_font(size: int) -> ImageFont.FreeTypeFont:
        for p in [
            "/System/Library/Fonts/Supplemental/Impact.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]:
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    pass
        return ImageFont.load_default()

    def outline_text(
        d: ImageDraw.ImageDraw,
        xy: tuple,
        text: str,
        font: ImageFont.FreeTypeFont,
        fill: tuple,
        outline: tuple,
        width: int = 7,
    ) -> None:
        x, y = xy
        for dx in range(-width, width + 1, 2):
            for dy in range(-width, width + 1, 2):
                if dx or dy:
                    d.text((x + dx, y + dy), text, font=font, fill=outline, anchor="mm")
        d.text(xy, text, font=font, fill=fill, anchor="mm")

    if stat:
        outline_text(draw, (W // 2, H // 2 - 40), stat, get_font(120), (255, 230, 50), (0, 0, 0))

    # Title lines (max 2, all caps)
    title_upper = title.upper()[:60]
    font_title  = get_font(62)
    outline_text(draw, (W // 2, H - 120), title_upper, font_title, (255, 255, 255), (0, 0, 0))

    # Watermark
    wm_font = get_font(28)
    draw.text((W // 2, H - 30), "FACTFORGE", font=wm_font, fill=(200, 200, 200), anchor="mm")

    bg_img.save(str(thumb_path), "JPEG", quality=95)
    size_kb = thumb_path.stat().st_size // 1024
    print(f"  ✅ thumbnail.jpg saved ({size_kb} KB)")


def _extract_hero_stat(script: dict) -> str:
    """Try to pull a short numeric stat from the script for thumbnail hero text."""
    for field in ("hero_stat", "key_stat", "main_stat"):
        val = script.get(field)
        if val:
            return str(val)[:20]
    # Try scanning key_facts
    for fact in script.get("key_facts", []):
        m = re.search(r"[\$£€]?\d[\d,\.]+[MBKTmbt%]*", str(fact))
        if m:
            return m.group(0)[:20]
    return ""


# ══════════════════════════════════════════════════════════════════════════════
# STEP 9 — UPLOAD TO YOUTUBE
# ══════════════════════════════════════════════════════════════════════════════

def _build_youtube_client():
    """Build YouTube API client from token file."""
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials

    token_file = CONFIG_DIR / "youtube_token.json"
    if not token_file.exists():
        raise FileNotFoundError(f"YouTube token not found: {token_file}")

    tok = json.loads(token_file.read_text())
    creds = Credentials(
        token=tok["token"],
        refresh_token=tok["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=tok["client_id"],
        client_secret=tok["client_secret"],
        scopes=tok["scopes"],
    )
    return build("youtube", "v3", credentials=creds)


def _next_publish_time() -> str:
    """Return next available RFC3339 publish time (14:00 UTC, every 2 days)."""
    from datetime import timedelta

    # Read existing schedule to find last Short publish date
    schedule_file = ROOT / "state/upload_schedule.json"
    last_date: Optional[datetime] = None

    if schedule_file.exists():
        try:
            sched = json.loads(schedule_file.read_text())
            for entry in reversed(sched.get("schedule", [])):
                if not entry.get("id", "").startswith("L"):
                    dt_str = entry.get("publish_at", "")
                    if dt_str:
                        last_date = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                        break
        except Exception:
            pass

    now = datetime.now(timezone.utc)
    if last_date and last_date > now:
        candidate = last_date + timedelta(days=2)
    else:
        # Next occurrence of 14:00 UTC, at least 1 day from now
        candidate = now.replace(hour=14, minute=0, second=0, microsecond=0)
        if candidate <= now + timedelta(hours=2):
            candidate += timedelta(days=1)

    return candidate.strftime("%Y-%m-%dT%H:%M:%S+00:00")


def step_upload(video_id: str, script: dict, cp: dict) -> str:
    """Upload video to YouTube as scheduled private. Returns youtube_id."""
    if cp["upload"]:
        # Check if youtube_id already saved
        meta_path = OUTPUT_DIR / video_id / "metadata.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())
            yt_id = meta.get("youtube_video_id")
            if yt_id:
                print(f"  [SKIP] Already uploaded → https://youtu.be/{yt_id}")
                return yt_id

    from googleapiclient.http import MediaFileUpload

    video_path = OUTPUT_DIR / video_id / "video.mp4"
    meta_path  = OUTPUT_DIR / video_id / "metadata.json"
    thumb_path = OUTPUT_DIR / video_id / "thumbnail.jpg"

    if not video_path.exists():
        raise FileNotFoundError(f"video.mp4 not found: {video_path}")

    # Load or build metadata
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
    else:
        meta = {}

    title       = meta.get("title") or script.get("title") or script.get("video_title") or video_id
    description = meta.get("description") or script.get("description") or ""
    tags        = meta.get("tags") or []

    publish_at = _next_publish_time()
    print(f"  Uploading {video_id} to YouTube (scheduled: {publish_at})...")

    youtube = _build_youtube_client()

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": meta.get("categoryId", "28"),
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": publish_at,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        str(video_path),
        chunksize=1024 * 1024,
        resumable=True,
        mimetype="video/mp4",
    )
    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = req.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"    Uploading {video_id}: {pct}%", end="\r")

    yt_id: str = response["id"]
    print(f"\n  ✅ Uploaded → https://youtu.be/{yt_id}  (publishes {publish_at})")

    # NOTE: YouTube blocks thumbnail uploads for Shorts via API.
    # Remind user to set manually in YouTube Studio.
    print("  ⚠️  REMINDER: Set thumbnail manually in YouTube Studio for this Short.")
    print(f"     Local thumbnail: output/{video_id}/thumbnail.jpg")

    # Save youtube_id to metadata.json
    meta["youtube_video_id"] = yt_id
    meta["youtube_url"]      = f"https://youtu.be/{yt_id}"
    meta["scheduled_at"]     = publish_at
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False))

    _update_state_after_upload(video_id, yt_id, title, publish_at)
    return yt_id


def _update_state_after_upload(
    video_id: str, yt_id: str, title: str, publish_at: str
) -> None:
    """Update pending_uploads.json, queue.json, and published_videos.json."""
    # — pending_uploads.json —
    pu_file = ROOT / "state/pending_uploads.json"
    if pu_file.exists():
        pu = json.loads(pu_file.read_text())
    else:
        pu = {"pending": []}

    # Update existing entry or append
    existing = next((e for e in pu["pending"] if e["id"] == video_id), None)
    if existing:
        existing.update(
            {
                "scheduled": True,
                "youtube_id": yt_id,
                "publish_at": publish_at,
                "status": "uploaded",
                "published_at": datetime.now(timezone.utc).isoformat(),
            }
        )
    else:
        pu["pending"].append(
            {
                "id": video_id,
                "title": title,
                "video_file": f"output/{video_id}/video.mp4",
                "metadata_file": f"output/{video_id}/metadata.json",
                "ready": True,
                "scheduled": True,
                "youtube_id": yt_id,
                "publish_at": publish_at,
                "status": "uploaded",
                "published_at": datetime.now(timezone.utc).isoformat(),
            }
        )
    pu_file.write_text(json.dumps(pu, indent=2, ensure_ascii=False))

    # — queue.json — mark idea as produced
    q_file = ROOT / "state/queue.json"
    if q_file.exists():
        q = json.loads(q_file.read_text())
        for idea in q.get("ideas", []):
            if idea["id"] == video_id:
                idea["status"] = "produced"
                idea["youtube_id"] = yt_id
                break
        q_file.write_text(json.dumps(q, indent=2, ensure_ascii=False))

    # — published_videos.json —
    pub_file = ROOT / "state/published_videos.json"
    if pub_file.exists():
        pub = json.loads(pub_file.read_text())
    else:
        pub = {"videos": []}

    if not any(v["id"] == video_id for v in pub.get("videos", [])):
        pub.setdefault("videos", []).append(
            {
                "id": video_id,
                "title": title,
                "youtube_id": yt_id,
                "youtube_url": f"https://youtu.be/{yt_id}",
                "published_at": publish_at,
                "cleaned": False,
            }
        )
        pub_file.write_text(json.dumps(pub, indent=2, ensure_ascii=False))

    print(f"  State updated in pending_uploads.json + queue.json + published_videos.json")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 10 — CLEAN
# ══════════════════════════════════════════════════════════════════════════════

def step_clean(video_id: str, cp: dict) -> None:
    """Delete large production files, keep only essential files."""
    if cp["clean"]:
        print("  [SKIP] Already cleaned")
        return

    out_dir = OUTPUT_DIR / video_id
    deleted_bytes = 0

    # Delete specific files
    for pattern in CLEAN_PATTERNS:
        for f in out_dir.glob(pattern):
            size = f.stat().st_size
            f.unlink()
            deleted_bytes += size
            print(f"  🗑  Deleted {f.name} ({size // 1024} KB)")

    # Delete directories
    for dir_name in CLEAN_DIRS:
        d = out_dir / dir_name
        if d.exists():
            size = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
            shutil.rmtree(d)
            deleted_bytes += size
            print(f"  🗑  Deleted {dir_name}/ ({size // (1024*1024)} MB)")

    # Clean remotion public/<id>/
    pub_dir = PUBLIC_DIR / video_id
    if pub_dir.exists():
        size = sum(f.stat().st_size for f in pub_dir.rglob("*") if f.is_file())
        shutil.rmtree(pub_dir)
        deleted_bytes += size
        print(f"  🗑  Deleted public/{video_id}/ ({size // (1024*1024)} MB)")

    freed_mb = deleted_bytes // (1024 * 1024)
    print(f"  ✅ Cleaned {video_id}: freed {freed_mb} MB")


# ══════════════════════════════════════════════════════════════════════════════
# QUEUE HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def get_next_short_id() -> str:
    """Return the first unproduced Short idea ID from queue.json."""
    q_file = ROOT / "state/queue.json"
    if not q_file.exists():
        raise FileNotFoundError(f"queue.json not found: {q_file}")
    q = json.loads(q_file.read_text())
    for idea in q.get("ideas", []):
        vid_id: str = idea.get("id", "")
        status: str = idea.get("status", "")
        if vid_id.startswith("S") and status not in ("produced", "uploaded"):
            return vid_id
    raise RuntimeError("No unproduced Short ideas found in queue.json")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

def produce_short(video_id: str) -> None:
    print(f"\n{'='*60}")
    print(f"FactForge Short Pipeline — {video_id}")
    print(f"{'='*60}\n")

    out_dir = OUTPUT_DIR / video_id
    out_dir.mkdir(parents=True, exist_ok=True)

    cp = load_checkpoint(video_id)

    # ── Step 1: Load script ───────────────────────────────────────────────────
    print("[1/10] Loading script...")
    script = step_load(video_id)
    tts_text: str = (
        script.get("tts_text_final")
        or script.get("full_text")
        or script.get("tts_script")
        or ""
    )

    # ── Step 2: Audio ─────────────────────────────────────────────────────────
    print("\n[2/10] Generating audio (Kokoro TTS)...")
    _duration = step_audio(video_id, tts_text, cp)
    cp["audio"] = True
    save_checkpoint(video_id, cp)

    # ── Step 3: Word timestamps ───────────────────────────────────────────────
    print("\n[3/10] Extracting word timestamps (faster-whisper)...")
    _words = step_timestamps(video_id, cp)
    cp["timestamps"] = True
    save_checkpoint(video_id, cp)

    # ── Step 4: Fetch bg_videos from Pexels ──────────────────────────────────
    print("\n[4/10] Fetching Pexels background videos...")
    step_bg_videos(video_id, cp)
    cp["bg_videos"] = True
    save_checkpoint(video_id, cp)

    # ── Step 5: Verify remotion props ─────────────────────────────────────────
    print("\n[5/10] Verifying remotion_props.json...")
    _props = step_verify_props(video_id)

    # ── Step 6: Copy to remotion public ───────────────────────────────────────
    print("\n[6/10] Copying assets to remotion public/...")
    step_copy_public(video_id)

    # ── Step 7: Render ────────────────────────────────────────────────────────
    print("\n[7/10] Rendering video...")
    step_render(video_id, cp)
    cp["render"] = True
    save_checkpoint(video_id, cp)

    # ── Step 8: Thumbnail ─────────────────────────────────────────────────────
    print("\n[8/10] Generating thumbnail...")
    step_thumbnail(video_id, script)

    # ── Step 9: Upload ────────────────────────────────────────────────────────
    print("\n[9/10] Uploading to YouTube...")
    yt_id = step_upload(video_id, script, cp)
    cp["upload"] = True
    save_checkpoint(video_id, cp)

    # ── Step 10: Clean ────────────────────────────────────────────────────────
    print("\n[10/10] Cleaning production files...")
    step_clean(video_id, cp)
    cp["clean"] = True
    save_checkpoint(video_id, cp)

    print(f"\n{'='*60}")
    print(f"✅ {video_id} complete!")
    print(f"   YouTube: https://youtu.be/{yt_id}")
    print(f"   Set thumbnail manually in YouTube Studio.")
    print(f"{'='*60}\n")


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    arg = sys.argv[1]

    if arg == "--next":
        video_id = get_next_short_id()
        print(f"Next Short from queue: {video_id}")
    elif arg.startswith("S") or arg.startswith("s"):
        video_id = arg.upper()
    else:
        print(f"ERROR: Invalid video ID '{arg}'. Must start with 'S' or use --next.")
        sys.exit(1)

    # Load .env if dotenv is available
    try:
        from dotenv import load_dotenv
        load_dotenv(CONFIG_DIR / ".env")
    except ImportError:
        pass

    produce_short(video_id)


if __name__ == "__main__":
    main()
