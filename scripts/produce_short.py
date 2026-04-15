"""
produce_short.py — Short Video Production Pipeline
Usage:
    python3 scripts/produce_short.py <video_id>
    python3 scripts/produce_short.py --next      # picks next unproduced Short from queue

Pipeline steps (resumable via checkpoint):
    1. LOAD        — read script.json for tts_text_final
    2. AUDIO       — Kokoro am_echo TTS → audio.mp3
    3. TIMESTAMPS  — faster-whisper word timestamps → word_timestamps.json
    4. BG_VIDEOS   — fetch Pexels/Coverr/Pixabay clips → bg_videos/
    5. PROPS       — verify remotion_props.json exists
    6. COPY_PUBLIC — copy audio + bg_videos to remotion public/
    7. RENDER      — render_short.py → video.mp4
    8. THUMBNAIL   — Pollinations Flux + Pillow → thumbnail.jpg
    9. UPLOAD      — YouTube API upload (scheduled private)
    10. CLEAN      — delete large files, keep metadata/script/thumbnail
"""

import logging
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from utils.config import cfg
from utils.video_sources import VideoSources
from utils.thumbnail_gen import ThumbnailGenerator
from utils.youtube_helper import (
    upload_video,
    set_thumbnail,
    upload_caption,
    get_next_publish_date,
    update_state_after_upload,
)


# ══════════════════════════════════════════════════════════════════════════════
# CHECKPOINT HELPERS
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_CHECKPOINT = {
    "audio":      False,
    "timestamps": False,
    "bg_videos":  False,
    "render":     False,
    "upload":     False,
    "clean":      False,
}


def load_checkpoint(video_id: str) -> dict:
    cp_path = cfg.OUTPUT_DIR / video_id / "produce_checkpoint.json"
    if cp_path.exists():
        return json.loads(cp_path.read_text())
    return dict(DEFAULT_CHECKPOINT)


def save_checkpoint(video_id: str, cp: dict) -> None:
    cp_path = cfg.OUTPUT_DIR / video_id / "produce_checkpoint.json"
    cp_path.write_text(json.dumps(cp, indent=2))


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — LOAD script
# ══════════════════════════════════════════════════════════════════════════════

def step_load(video_id: str) -> dict:
    """Read script.json and return the script dict."""
    script_path = cfg.OUTPUT_DIR / video_id / "script.json"
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
    logger.info("Script loaded (%d chars)", len(tts_text))
    return script


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — AUDIO (Kokoro TTS)
# ══════════════════════════════════════════════════════════════════════════════

def step_audio(video_id: str, tts_text: str, cp: dict) -> float:
    """Generate audio.mp3 with Kokoro. Returns duration in seconds."""
    audio_path = cfg.OUTPUT_DIR / video_id / "audio.mp3"

    if cp["audio"] and audio_path.exists():
        logger.info("[SKIP] audio.mp3 already exists")
        return _get_audio_duration(audio_path)

    if not cfg.KOKORO_MODEL.exists():
        raise FileNotFoundError(f"Kokoro model not found: {cfg.KOKORO_MODEL}")

    logger.info("Generating Kokoro TTS (voice=%s, speed=%s)...", cfg.KOKORO_VOICE, cfg.KOKORO_SPEED)

    import soundfile as sf
    from kokoro_onnx import Kokoro

    kokoro = Kokoro(str(cfg.KOKORO_MODEL), str(cfg.KOKORO_VOICES))
    samples, sr = kokoro.create(tts_text, voice=cfg.KOKORO_VOICE, speed=cfg.KOKORO_SPEED, lang="en-us")

    wav_path = cfg.OUTPUT_DIR / video_id / "audio.wav"
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
    logger.info("Audio ready: %s (%.1fs)", audio_path.name, duration)
    return duration


def _get_audio_duration(audio_path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(audio_path)],
        capture_output=True, text=True,
    )
    info = json.loads(r.stdout)
    return float(info["format"]["duration"])


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — TIMESTAMPS (faster-whisper)
# ══════════════════════════════════════════════════════════════════════════════

def step_timestamps(video_id: str, cp: dict) -> list:
    """Extract word-level timestamps. Returns list of {word, start_ms, end_ms}."""
    ts_path    = cfg.OUTPUT_DIR / video_id / "word_timestamps.json"
    audio_path = cfg.OUTPUT_DIR / video_id / "audio.mp3"

    if cp["timestamps"] and ts_path.exists():
        logger.info("[SKIP] word_timestamps.json already exists")
        return json.loads(ts_path.read_text())

    if not audio_path.exists():
        raise FileNotFoundError(f"audio.mp3 not found: {audio_path}")

    logger.info("Extracting word timestamps (faster-whisper %s)...", cfg.WHISPER_MODEL)

    from faster_whisper import WhisperModel

    model = WhisperModel(cfg.WHISPER_MODEL, device="cpu", compute_type="int8")
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
            words.append({"word": word, "start_ms": round(w.start * 1000), "end_ms": round(w.end * 1000)})

    ts_path.write_text(json.dumps(words, indent=2))
    last_s = words[-1]["end_ms"] / 1000 if words else 0
    logger.info("Timestamps: %d words, last at %.1fs", len(words), last_s)
    return words


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — BG_VIDEOS
# ══════════════════════════════════════════════════════════════════════════════

def step_bg_videos(video_id: str, cp: dict) -> None:
    """Fetch unique background videos for every segment via VideoSources."""
    props_path = cfg.OUTPUT_DIR / video_id / "remotion_props.json"
    if not props_path.exists():
        raise FileNotFoundError(f"remotion_props.json not found for {video_id}")

    props    = json.loads(props_path.read_text())
    segments = props.get("segments", [])

    if not segments:
        logger.info("No segments in remotion_props.json — skipping bg_videos")
        return

    if cp["bg_videos"]:
        logger.info("[SKIP] bg_videos already fetched")
        return

    bg_dir = cfg.OUTPUT_DIR / video_id / "bg_videos"
    bg_dir.mkdir(parents=True, exist_ok=True)

    vs = VideoSources()
    logger.info("Fetching %d unique background clips (Pexels → Coverr → Pixabay)...", len(segments))
    failed = 0

    for i, seg in enumerate(segments):
        bg_path_str: str = seg.get("backgroundVideo", "")
        if not bg_path_str:
            continue

        out_filename = Path(bg_path_str).name
        out_path     = bg_dir / out_filename

        if out_path.exists() and out_path.stat().st_size > 10_000:
            logger.info("  [SKIP] %s already downloaded", out_filename)
            continue

        primary_query = seg.get("scene_query") or re.sub(r"[_\-]+", " ", Path(bg_path_str).stem).strip()
        seg_type      = seg.get("type", "fact")
        fallbacks     = vs._TYPE_FALLBACKS.get(seg_type, []) + vs._GENERIC_FALLBACKS

        logger.info("  [%d/%d] '%s' → %s", i + 1, len(segments), primary_query, out_filename)

        ok = vs.fetch_pexels(primary_query, out_path, fallbacks)
        if not ok:
            logger.info("  Pexels failed — trying Coverr...")
            ok = vs.fetch_coverr(primary_query, out_path, fallbacks)
        if not ok:
            logger.info("  Coverr failed — trying Pixabay...")
            ok = vs.fetch_pixabay(primary_query, out_path, fallbacks)
        if not ok:
            logger.warning("  All sources failed for '%s'", primary_query)
            failed += 1

        time.sleep(0.4)

    if failed:
        logger.warning("%d/%d clips failed (all sources exhausted)", failed, len(segments))

    total_ok = len(list(bg_dir.glob("*.mp4")))
    logger.info("bg_videos ready: %d unique clips in %s", total_ok, bg_dir)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — PROPS verification
# ══════════════════════════════════════════════════════════════════════════════

def step_verify_props(video_id: str) -> dict:
    """Verify remotion_props.json exists and is valid."""
    props_path = cfg.OUTPUT_DIR / video_id / "remotion_props.json"
    if not props_path.exists():
        raise FileNotFoundError(
            f"remotion_props.json not found for {video_id}. "
            "This file must be created by Claude Code before running produce_short.py."
        )
    props = json.loads(props_path.read_text())
    total = props.get("totalDurationFrames", 0)
    segs  = len(props.get("segments", []))
    logger.info("Props verified: %d frames (%.1fs), %d segments", total, total / cfg.SHORT_FPS, segs)
    return props


# ══════════════════════════════════════════════════════════════════════════════
# STEP 6 — COPY TO REMOTION PUBLIC
# ══════════════════════════════════════════════════════════════════════════════

def step_copy_public(video_id: str) -> None:
    """Copy audio.mp3 and bg_videos/ to remotion public/<id>/."""
    pub_dir = cfg.PUBLIC_DIR / video_id
    pub_dir.mkdir(parents=True, exist_ok=True)

    audio_src = cfg.OUTPUT_DIR / video_id / "audio.mp3"
    audio_dst = pub_dir / "audio.mp3"
    if not audio_src.exists():
        raise FileNotFoundError(f"audio.mp3 not found at {audio_src}")
    shutil.copy2(audio_src, audio_dst)
    logger.info("Copied audio → public/%s/audio.mp3", video_id)

    bg_src = cfg.OUTPUT_DIR / video_id / "bg_videos"
    bg_dst = pub_dir / "bg_videos"
    if bg_src.exists() and any(bg_src.iterdir()):
        if bg_dst.exists():
            shutil.rmtree(bg_dst)
        shutil.copytree(bg_src, bg_dst)
        count = len(list(bg_dst.glob("*.mp4")))
        logger.info("Copied %d bg_videos → public/%s/bg_videos/", count, video_id)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 7 — RENDER
# ══════════════════════════════════════════════════════════════════════════════

def step_render(video_id: str, cp: dict) -> None:
    """Run render_short.py to produce video.mp4."""
    video_path = cfg.OUTPUT_DIR / video_id / "video.mp4"

    if cp["render"] and video_path.exists():
        logger.info("[SKIP] video.mp4 already rendered")
        return

    render_script = cfg.SCRIPTS_DIR / "render_short.py"
    logger.info("Rendering %s via render_short.py...", video_id)

    max_retries = 2
    last_error: Optional[Exception] = None
    for attempt in range(1, max_retries + 1):
        result = subprocess.run(
            [sys.executable, str(render_script), video_id],
            capture_output=False,
            timeout=3600,
        )
        if result.returncode == 0:
            break
        last_error = RuntimeError(
            f"render_short.py failed with exit code {result.returncode} (attempt {attempt}/{max_retries})"
        )
        logger.warning("Render failed (attempt %d/%d) — clearing cache and retrying...", attempt, max_retries)
        cache_dir = ROOT / "video/remotion-project/.cache"
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            logger.info("Cleared %s", cache_dir)
        if attempt < max_retries:
            time.sleep(5)
    else:
        raise last_error  # type: ignore[misc]

    if not video_path.exists():
        raise RuntimeError(f"Render completed but video.mp4 not found at {video_path}")

    size_mb = video_path.stat().st_size // (1024 * 1024)
    logger.info("video.mp4 ready (%d MB)", size_mb)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 8 — THUMBNAIL
# ══════════════════════════════════════════════════════════════════════════════

def step_thumbnail(video_id: str, script: dict) -> None:
    """Generate thumbnail.jpg (A/B/C variants) using ThumbnailGenerator."""
    thumb_path = cfg.OUTPUT_DIR / video_id / "thumbnail.jpg"

    if thumb_path.exists() and thumb_path.stat().st_size > 5_000:
        logger.info("[SKIP] thumbnail.jpg already exists")
        return

    gen = ThumbnailGenerator()
    title  = script.get("title") or script.get("video_title") or video_id
    stat   = _extract_hero_stat(script)
    category = script.get("category", "")
    hook   = script.get("hook") or script.get("opening_hook") or ""
    base   = title or hook or f"FactForge {video_id}"

    prompt = (
        f"Cinematic 4K background for YouTube thumbnail, vivid dramatic lighting, "
        f"topic: {base[:80]}, category: {category}, "
        "no text, no watermarks, high contrast, stunning visual impact"
    )
    logger.info("Generating Pollinations thumbnail: %s...", prompt[:60])

    out_dir = cfg.OUTPUT_DIR / video_id
    gen.generate(
        out_dir=out_dir,
        prompt=prompt,
        title=title,
        hero_stat=stat,
    )


def _extract_hero_stat(script: dict) -> str:
    for field in ("hero_stat", "key_stat", "main_stat"):
        val = script.get(field)
        if val:
            return str(val)[:20]
    for fact in script.get("key_facts", []):
        m = re.search(r"[\$£€]?\d[\d,\.]+[MBKTmbt%]*", str(fact))
        if m:
            return m.group(0)[:20]
    return ""


# ══════════════════════════════════════════════════════════════════════════════
# STEP 9 — UPLOAD TO YOUTUBE
# ══════════════════════════════════════════════════════════════════════════════

def step_upload(video_id: str, script: dict, cp: dict) -> str:
    """Upload video to YouTube as scheduled private. Returns youtube_id."""
    if cp["upload"]:
        meta_path = cfg.OUTPUT_DIR / video_id / "metadata.json"
        if meta_path.exists():
            yt_id = json.loads(meta_path.read_text()).get("youtube_video_id")
            if yt_id:
                logger.info("[SKIP] Already uploaded → https://youtu.be/%s", yt_id)
                return yt_id

    video_path = cfg.OUTPUT_DIR / video_id / "video.mp4"
    meta_path  = cfg.OUTPUT_DIR / video_id / "metadata.json"

    if not video_path.exists():
        raise FileNotFoundError(f"video.mp4 not found: {video_path}")

    meta  = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    title = meta.get("title") or script.get("title") or script.get("video_title") or video_id
    desc  = meta.get("description") or script.get("description") or ""
    tags  = meta.get("tags") or []
    cat   = meta.get("categoryId", "28")

    publish_at = get_next_publish_date("short")
    logger.info("Uploading %s to YouTube (scheduled: %s)...", video_id, publish_at)

    yt_id = upload_video(
        video_path=video_path,
        title=title,
        description=desc,
        tags=tags,
        category_id=cat,
        publish_at=publish_at,
        privacy="private",
    )
    if not yt_id:
        raise RuntimeError("YouTube upload failed — check credentials and quota")

    logger.info("Uploaded → https://youtu.be/%s  (publishes %s)", yt_id, publish_at)
    logger.warning("REMINDER: Set thumbnail manually in YouTube Studio for this Short.")
    logger.info("  Local thumbnail: output/%s/thumbnail.jpg", video_id)

    # Persist youtube_id to metadata.json
    meta["youtube_video_id"] = yt_id
    meta["youtube_url"]      = f"https://youtu.be/{yt_id}"
    meta["scheduled_at"]     = publish_at
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False))

    update_state_after_upload(video_id, yt_id, publish_at, title, "short")
    _append_score(video_id, script, yt_id)
    return yt_id


def _append_score(video_id: str, script: dict, yt_id: str) -> None:
    """Append scoring data to state/scores.json after a successful upload."""
    from datetime import datetime, timezone

    scores_path = cfg.STATE_DIR / "scores.json"
    scores = json.loads(scores_path.read_text()) if scores_path.exists() else []

    if any(s.get("id") == video_id for s in scores):
        return

    meta_path = cfg.OUTPUT_DIR / video_id / "metadata.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}

    scores.append({
        "id":               video_id,
        "script_score":     script.get("script_score") or script.get("content_score") or 0,
        "seo_score":        meta.get("seo_score") or script.get("seo_score") or 0,
        "thumbnail_score":  script.get("thumbnail_score") or meta.get("thumbnail_score") or 0,
        "published_at":     datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "title":            meta.get("title") or script.get("title") or video_id,
        "youtube_id":       yt_id,
    })
    scores_path.write_text(json.dumps(scores, indent=2, ensure_ascii=False))
    logger.info("Scores recorded → state/scores.json")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 10 — CLEAN
# ══════════════════════════════════════════════════════════════════════════════

_CLEAN_PATTERNS = ["video.mp4", "video_noaudio.mp4", "audio.mp3", "*.wav"]
_CLEAN_DIRS     = ["bg_videos"]


def step_clean(video_id: str, cp: dict) -> None:
    """Delete large production files, keep only essential files."""
    if cp["clean"]:
        logger.info("[SKIP] Already cleaned")
        return

    out_dir       = cfg.OUTPUT_DIR / video_id
    deleted_bytes = 0

    for pattern in _CLEAN_PATTERNS:
        for f in out_dir.glob(pattern):
            size = f.stat().st_size
            f.unlink()
            deleted_bytes += size
            logger.info("Deleted %s (%d KB)", f.name, size // 1024)

    for dir_name in _CLEAN_DIRS:
        d = out_dir / dir_name
        if d.exists():
            size = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
            shutil.rmtree(d)
            deleted_bytes += size
            logger.info("Deleted %s/ (%d MB)", dir_name, size // (1024 * 1024))

    pub_dir = cfg.PUBLIC_DIR / video_id
    if pub_dir.exists():
        size = sum(f.stat().st_size for f in pub_dir.rglob("*") if f.is_file())
        shutil.rmtree(pub_dir)
        deleted_bytes += size
        logger.info("Deleted public/%s/ (%d MB)", video_id, size // (1024 * 1024))

    logger.info("Cleaned %s: freed %d MB", video_id, deleted_bytes // (1024 * 1024))


# ══════════════════════════════════════════════════════════════════════════════
# QUEUE HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def get_next_short_id() -> str:
    """Return the first unproduced Short idea ID from queue.json."""
    q_file = cfg.STATE_DIR / "queue.json"
    if not q_file.exists():
        raise FileNotFoundError(f"queue.json not found: {q_file}")
    q = json.loads(q_file.read_text())
    for idea in q.get("ideas", []):
        vid_id: str = idea.get("id", "")
        status: str = idea.get("status", "")
        if vid_id.startswith("S") and status not in ("produced", "uploaded"):
            return vid_id
    raise RuntimeError("No unproduced Short ideas found in queue.json")


def print_scores_summary() -> None:
    """Print average scores if scores.json has >= 3 entries."""
    scores_path = cfg.STATE_DIR / "scores.json"
    if not scores_path.exists():
        return
    scores = json.loads(scores_path.read_text())
    if len(scores) < 3:
        return
    avg_script = sum(s.get("script_score", 0) for s in scores) / len(scores)
    avg_seo    = sum(s.get("seo_score", 0) for s in scores) / len(scores)
    avg_thumb  = sum(s.get("thumbnail_score", 0) for s in scores) / len(scores)
    logger.info("Scores summary (%d videos): script=%.1f/100  SEO=%.1f/22  thumb=%.1f/16",
                len(scores), avg_script, avg_seo, avg_thumb)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

def produce_short(video_id: str) -> None:
    logger.info("=" * 60)
    logger.info("FactForge Short Pipeline — %s", video_id)
    logger.info("=" * 60)

    out_dir = cfg.OUTPUT_DIR / video_id
    out_dir.mkdir(parents=True, exist_ok=True)

    cp = load_checkpoint(video_id)

    logger.info("[1/10] Loading script...")
    script = step_load(video_id)
    tts_text: str = (
        script.get("tts_text_final")
        or script.get("full_text")
        or script.get("tts_script")
        or ""
    )

    logger.info("[2/10] Generating audio (Kokoro TTS)...")
    step_audio(video_id, tts_text, cp)
    cp["audio"] = True
    save_checkpoint(video_id, cp)

    logger.info("[3/10] Extracting word timestamps (faster-whisper)...")
    step_timestamps(video_id, cp)
    cp["timestamps"] = True
    save_checkpoint(video_id, cp)

    logger.info("[4/10] Fetching background videos...")
    step_bg_videos(video_id, cp)
    cp["bg_videos"] = True
    save_checkpoint(video_id, cp)

    logger.info("[5/10] Verifying remotion_props.json...")
    step_verify_props(video_id)

    logger.info("[6/10] Copying assets to remotion public/...")
    step_copy_public(video_id)

    logger.info("[7/10] Rendering video...")
    step_render(video_id, cp)
    cp["render"] = True
    save_checkpoint(video_id, cp)

    logger.info("[8/10] Generating thumbnail...")
    step_thumbnail(video_id, script)

    logger.info("[9/10] Uploading to YouTube...")
    yt_id = step_upload(video_id, script, cp)
    cp["upload"] = True
    save_checkpoint(video_id, cp)

    logger.info("[10/10] Cleaning production files...")
    step_clean(video_id, cp)
    cp["clean"] = True
    save_checkpoint(video_id, cp)

    logger.info("=" * 60)
    logger.info("%s complete! YouTube: https://youtu.be/%s", video_id, yt_id)
    logger.info("Set thumbnail manually in YouTube Studio.")
    logger.info("=" * 60)


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
        logger.info("Next Short from queue: %s", video_id)
    elif arg.upper().startswith("S"):
        video_id = arg.upper()
    else:
        logger.error("Invalid video ID '%s'. Must start with 'S' or use --next.", arg)
        sys.exit(1)

    try:
        from dotenv import load_dotenv
        load_dotenv(cfg.CONFIG_DIR / ".env")
    except ImportError:
        pass

    produce_short(video_id)
    print_scores_summary()


if __name__ == "__main__":
    main()
