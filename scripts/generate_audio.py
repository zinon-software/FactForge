"""
FactForge Audio Generator
Generates TTS audio + word-level timestamps using:
  - Kokoro TTS (am_echo, Apache 2.0 — commercial safe) ← DEFAULT
  - faster-whisper (base model) for word timestamps
  - Procedural SFX (numpy) — whoosh, tick, heartbeat — mixed into final audio

Usage:
  python3 scripts/generate_audio.py <video_id>
  python3 scripts/generate_audio.py <video_id> --no-sfx   # skip SFX mixing
  e.g.: python3 scripts/generate_audio.py S01220

Voice: am_echo (American male, Kokoro v1.0)
Model files: models/kokoro/kokoro-v1.0.onnx + voices-v1.0.bin
"""

import json, sys, shutil, argparse, logging
from pathlib import Path
import soundfile as sf
import numpy as np
import requests

logger = logging.getLogger(__name__)

BASE = Path(__file__).parent.parent

# ── Kokoro config ─────────────────────────────────────────────────────────────
KOKORO_MODEL  = BASE / "models/kokoro/kokoro-v1.0.onnx"
KOKORO_VOICES = BASE / "models/kokoro/voices-v1.0.bin"
KOKORO_VOICE  = "am_echo"    # chosen voice — clear, authoritative, commercial safe
KOKORO_SPEED  = 1.08         # slightly faster for Shorts energy (1.0 = normal)

# ── Whisper config ────────────────────────────────────────────────────────────
WHISPER_MODEL = "base"       # base is more accurate than tiny for word timestamps

_kokoro  = None
_whisper = None


def get_kokoro():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        logger.info("Loading Kokoro model...")
        _kokoro = Kokoro(str(KOKORO_MODEL), str(KOKORO_VOICES))
    return _kokoro


def get_whisper():
    global _whisper
    if _whisper is None:
        from faster_whisper import WhisperModel
        logger.info("Loading Whisper base model...")
        _whisper = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    return _whisper


def generate_tts(text: str, out_path: Path, voice: str = KOKORO_VOICE, speed: float = KOKORO_SPEED) -> float:
    """Generate audio with Kokoro TTS. Returns duration in seconds."""
    k = get_kokoro()
    samples, sr = k.create(text, voice=voice, speed=speed, lang="en-us")

    # Save as WAV first, then convert to MP3 via ffmpeg for compatibility
    wav_path = out_path.with_suffix(".wav")
    sf.write(str(wav_path), samples, sr)

    import subprocess
    subprocess.run([
        "ffmpeg", "-y", "-i", str(wav_path),
        "-b:a", "192k", str(out_path)
    ], capture_output=True)
    wav_path.unlink()

    duration = len(samples) / sr
    logger.info("Audio: %s (%.1fs, voice=%s)", out_path.name, duration, voice)
    return duration


def get_word_timestamps(audio_path: Path) -> list:
    """Extract word-level timestamps using faster-whisper."""
    model = get_whisper()
    segments, _ = model.transcribe(
        str(audio_path),
        word_timestamps=True,
        language="en",
        beam_size=5,
    )
    words = []
    for seg in segments:
        for w in seg.words:
            word = w.word.strip()
            if not word:
                continue
            words.append({
                "word": word,
                "start_ms": round(w.start * 1000),
                "end_ms":   round(w.end   * 1000),
            })
    logger.info("Word timestamps: %d words, last at %.1fs", len(words), words[-1]['end_ms'] / 1000)
    return words


# ── Sound Effects (procedural — no external files needed) ────────────────────

def _make_whoosh(sr: int = 44100, duration: float = 0.35, volume: float = 0.18) -> np.ndarray:
    """Frequency sweep 150Hz→1200Hz — scene transition whoosh."""
    t = np.linspace(0, duration, int(sr * duration))
    freq = np.linspace(150, 1200, len(t))
    phase = np.cumsum(2 * np.pi * freq / sr)
    wave = np.sin(phase)
    # Envelope: fade in fast, fade out slow
    env = np.ones(len(t))
    fade_in  = int(0.05 * sr)
    fade_out = int(0.20 * sr)
    env[:fade_in]  = np.linspace(0, 1, fade_in)
    env[-fade_out:] = np.linspace(1, 0, fade_out)
    return (wave * env * volume).astype(np.float32)


def _make_tick(sr: int = 44100, volume: float = 0.22) -> np.ndarray:
    """Short click/tick — used on number reveals."""
    duration = 0.06
    t = np.linspace(0, duration, int(sr * duration))
    wave = np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 60)
    return (wave * volume).astype(np.float32)


def _make_heartbeat(sr: int = 44100, volume: float = 0.15) -> np.ndarray:
    """Double thump — used at peak/impact moment."""
    def thump(freq=60, dur=0.12):
        t = np.linspace(0, dur, int(sr * dur))
        wave = np.sin(2 * np.pi * freq * t) * np.exp(-t * 25)
        return wave
    beat1 = thump(60)
    gap   = np.zeros(int(sr * 0.10))
    beat2 = thump(55, 0.10)
    silence = np.zeros(int(sr * 0.05))
    full = np.concatenate([silence, beat1, gap, beat2, silence])
    return (full * volume).astype(np.float32)


def _mix_sfx_into_audio(audio_path: Path, props_path: Path, sr_target: int = 44100) -> None:
    """
    Read remotion_props.json segments, inject SFX at segment boundaries:
    - whoosh at every scene change (segment start, except first)
    - tick at "number" type segments
    - heartbeat at "impact" type segments
    Mixes SFX into the existing audio.mp3 in-place (saves backup as audio_clean.mp3).
    """
    if not props_path.exists():
        return  # no props yet — skip

    props = json.loads(props_path.read_text())
    segments = props.get("segments", [])
    fps = props.get("fps", 60)

    if not segments:
        return

    # Load main audio
    import subprocess, tempfile, os
    # Convert mp3 → wav for numpy processing
    tmp_wav = audio_path.with_suffix(".sfx_work.wav")
    subprocess.run([
        "ffmpeg", "-y", "-i", str(audio_path),
        "-ar", str(sr_target), "-ac", "1", str(tmp_wav)
    ], capture_output=True)

    if not tmp_wav.exists():
        return

    audio_data, sr = sf.read(str(tmp_wav))
    audio_data = audio_data.astype(np.float32)
    total_samples = len(audio_data)

    def frame_to_sample(frame: int) -> int:
        sec = frame / fps
        return min(int(sec * sr), total_samples - 1)

    whoosh = _make_whoosh(sr)
    tick   = _make_tick(sr)
    hb     = _make_heartbeat(sr)

    def _mix_at(sfx: np.ndarray, pos: int):
        end = min(pos + len(sfx), total_samples)
        length = end - pos
        audio_data[pos:end] += sfx[:length]

    for i, seg in enumerate(segments):
        start_frame = seg.get("startFrame", 0)
        seg_type    = seg.get("type", "fact")
        pos = frame_to_sample(start_frame)

        if i > 0:
            # Whoosh on every scene transition (not on the very first segment)
            _mix_at(whoosh, max(0, pos - int(0.05 * sr)))

        if seg_type == "number":
            _mix_at(tick, pos + int(0.05 * sr))

        if seg_type == "impact":
            _mix_at(hb, pos)

    # Normalize to prevent clipping
    peak = np.max(np.abs(audio_data))
    if peak > 0.95:
        audio_data = audio_data * (0.92 / peak)

    # Save backup of clean audio, then write mixed version
    clean_backup = audio_path.parent / "audio_clean.mp3"
    if not clean_backup.exists():
        import shutil as _shutil
        _shutil.copy(audio_path, clean_backup)

    sf.write(str(tmp_wav), audio_data, sr)
    subprocess.run([
        "ffmpeg", "-y", "-i", str(tmp_wav),
        "-b:a", "192k", str(audio_path)
    ], capture_output=True)
    tmp_wav.unlink(missing_ok=True)
    logger.info("SFX mixed: whoosh×%d + tick×%d + hb×%d",
                len(segments[1:]),
                len([s for s in segments if s.get('type') == 'number']),
                len([s for s in segments if s.get('type') == 'impact']))


def mix_background_music(video_id: str, volume: float = 0.10) -> None:
    """
    Download a CC0 instrumental track from Pixabay Music and mix it into
    audio.mp3 at `volume` (default 10%).  Saves audio_clean.mp3 as backup.
    The final file is audio.mp3 with vocals loud, music soft in the background.
    """
    import subprocess
    output_dir = BASE / "output" / video_id
    audio_path = output_dir / "audio.mp3"
    if not audio_path.exists():
        logger.warning("[music] audio.mp3 not found for %s — skipping", video_id)
        return

    PIXABAY_MUSIC_KEY = "55448442-b529cb16ef94bcaa210308891"
    music_path = output_dir / "bg_music.mp3"

    # ── Download background track ─────────────────────────────────────────────
    if not music_path.exists():
        try:
            r = requests.get(
                "https://pixabay.com/api/",
                params={
                    "key": PIXABAY_MUSIC_KEY,
                    "q": "background music instrumental",
                    "media_type": "music",
                    "per_page": 10,
                    "category": "music",
                },
                timeout=20,
            )
            r.raise_for_status()
            data = r.json()
            hits = data.get("hits", [])
            if not hits:
                logger.warning("[music] No tracks found from Pixabay Music — skipping")
                return
            # Try each hit until we get a downloadable URL
            track_url = None
            for hit in hits:
                # Pixabay music API returns audio field or previewURL
                track_url = (
                    hit.get("audio")
                    or hit.get("previewURL")
                    or hit.get("url")
                )
                if track_url:
                    break
            if not track_url:
                logger.warning("[music] No downloadable audio URL found — skipping")
                return

            logger.info("Downloading bg music: %s...", track_url[:60])
            dl = requests.get(track_url, timeout=60, stream=True)
            dl.raise_for_status()
            with open(music_path, "wb") as fh:
                for chunk in dl.iter_content(chunk_size=1024 * 256):
                    fh.write(chunk)
            logger.info("bg_music.mp3 saved (%d KB)", music_path.stat().st_size // 1024)
        except Exception as exc:
            logger.error("[music] Download failed: %s — skipping", exc)
            return

    # ── Backup clean audio ────────────────────────────────────────────────────
    clean_backup = output_dir / "audio_clean.mp3"
    if not clean_backup.exists():
        import shutil as _shutil
        _shutil.copy(audio_path, clean_backup)

    # ── Mix with ffmpeg ───────────────────────────────────────────────────────
    mixed_path = output_dir / "audio_with_music.mp3"
    result = subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(audio_path),
            "-stream_loop", "-1", "-i", str(music_path),
            "-filter_complex",
            f"[1:a]volume={volume}[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[out]",
            "-map", "[out]",
            "-codec:a", "libmp3lame", "-q:a", "2",
            str(mixed_path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error("[music] ffmpeg mix failed: %s", result.stderr[-300:])
        return

    # Replace audio.mp3 with mixed version
    import os as _os
    _os.replace(str(mixed_path), str(audio_path))
    logger.info("Background music mixed at %d%% — audio.mp3 updated", int(volume * 100))


def produce_audio(video_id: str, text: str = None, speed: float = KOKORO_SPEED, sfx: bool = True, music: bool = False) -> dict:
    """
    Full pipeline: text → Kokoro audio → whisper timestamps.
    Returns {"audio_path": Path, "words": [...], "duration_seconds": float}
    """
    output_dir = BASE / "output" / video_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get text from script.json if not provided
    if text is None:
        script_path = output_dir / "script.json"
        if not script_path.exists():
            logger.error("%s not found", script_path)
            sys.exit(1)
        with open(script_path) as f:
            script = json.load(f)
        text = script.get("tts_text_final") or script.get("full_text") or script.get("tts_script", "")

    audio_path = output_dir / "audio.mp3"

    logger.info("[1/3] Kokoro TTS (%s) for %s...", KOKORO_VOICE, video_id)
    duration = generate_tts(text, audio_path, voice=KOKORO_VOICE, speed=speed)

    logger.info("[2/3] Word timestamps (Whisper base)...")
    words = get_word_timestamps(audio_path)

    ts_path = output_dir / "word_timestamps.json"
    with open(ts_path, "w") as f:
        json.dump(words, f, indent=2)

    # Mix SFX into audio (whoosh on scene changes, tick on numbers, heartbeat on impact)
    if sfx:
        props_path = output_dir / "remotion_props.json"
        if props_path.exists():
            logger.info("Mixing SFX...")
            _mix_sfx_into_audio(audio_path, props_path)
        else:
            logger.info("[SFX] No remotion_props.json yet — SFX will be applied after props are built")

        # Mix background music after SFX (bundled with SFX pass)
        if music:
            logger.info("Mixing background music (10%)...")
            mix_background_music(video_id)

    # Copy to Remotion public
    public_dir = BASE / "video/remotion-project/public" / video_id
    public_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(audio_path, public_dir / "audio.mp3")
    logger.info("Copied to public/%s/audio.mp3", video_id)

    logger.info("[3/3] Done — %.1fs, %d words", duration, len(words))
    return {"audio_path": audio_path, "words": words, "duration_seconds": duration}


def apply_sfx(video_id: str) -> None:
    """Apply SFX to existing audio after remotion_props.json is ready. Call after step_props."""
    output_dir = BASE / "output" / video_id
    audio_path = output_dir / "audio.mp3"
    props_path = output_dir / "remotion_props.json"
    clean_path = output_dir / "audio_clean.mp3"

    if not audio_path.exists():
        logger.warning("[SFX] audio.mp3 not found for %s", video_id)
        return
    if not props_path.exists():
        logger.warning("[SFX] remotion_props.json not found for %s", video_id)
        return
    if clean_path.exists():
        logger.info("[SFX] Already applied (audio_clean.mp3 exists) — skipping")
        return

    logger.info("Mixing SFX into %s/audio.mp3...", video_id)
    _mix_sfx_into_audio(audio_path, props_path)

    # Re-copy to Remotion public
    public_dir = BASE / "video/remotion-project/public" / video_id
    public_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(audio_path, public_dir / "audio.mp3")
    logger.info("Updated public/%s/audio.mp3 with SFX", video_id)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FactForge audio generator")
    parser.add_argument("video_id", help="Video ID e.g. S01220")
    parser.add_argument("--no-sfx", action="store_true", help="Skip SFX mixing")
    parser.add_argument("--sfx-only", action="store_true", help="Apply SFX to existing audio (after props are built)")
    parser.add_argument("--music", action="store_true", help="Mix CC0 background music at 10% (bundled with SFX pass)")
    parser.add_argument("--no-music", action="store_true", help="Disable background music mixing (default)")
    args = parser.parse_args()

    use_music = args.music and not args.no_music

    if args.sfx_only:
        apply_sfx(args.video_id)
    else:
        produce_audio(args.video_id, sfx=not args.no_sfx, music=use_music)
