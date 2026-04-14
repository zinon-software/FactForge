"""
FactForge Audio Generator
Generates TTS audio + word-level timestamps using:
  - Kokoro TTS (am_echo, Apache 2.0 — commercial safe) ← DEFAULT
  - faster-whisper (base model) for word timestamps

Usage:
  python3 scripts/generate_audio.py <video_id>
  e.g.: python3 scripts/generate_audio.py S01220

Voice: am_echo (American male, Kokoro v1.0)
Model files: models/kokoro/kokoro-v1.0.onnx + voices-v1.0.bin
"""

import json, sys, shutil
from pathlib import Path
import soundfile as sf
import numpy as np

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
        print("  Loading Kokoro model...")
        _kokoro = Kokoro(str(KOKORO_MODEL), str(KOKORO_VOICES))
    return _kokoro


def get_whisper():
    global _whisper
    if _whisper is None:
        from faster_whisper import WhisperModel
        print("  Loading Whisper base model...")
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
    print(f"  Audio: {out_path.name} ({duration:.1f}s, voice={voice})")
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
    print(f"  Word timestamps: {len(words)} words, last at {words[-1]['end_ms']/1000:.1f}s")
    return words


def produce_audio(video_id: str, text: str = None, speed: float = KOKORO_SPEED) -> dict:
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
            print(f"ERROR: {script_path} not found")
            sys.exit(1)
        with open(script_path) as f:
            script = json.load(f)
        text = script.get("tts_text_final") or script.get("full_text") or script.get("tts_script", "")

    audio_path = output_dir / "audio.mp3"

    print(f"[1/3] Kokoro TTS ({KOKORO_VOICE}) for {video_id}...")
    duration = generate_tts(text, audio_path, voice=KOKORO_VOICE, speed=speed)

    print(f"[2/3] Word timestamps (Whisper base)...")
    words = get_word_timestamps(audio_path)

    ts_path = output_dir / "word_timestamps.json"
    with open(ts_path, "w") as f:
        json.dump(words, f, indent=2)

    # Copy to Remotion public
    public_dir = BASE / "video/remotion-project/public" / video_id
    public_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(audio_path, public_dir / "audio.mp3")
    print(f"  Copied to public/{video_id}/audio.mp3")

    print(f"[3/3] Done — {duration:.1f}s, {len(words)} words")
    return {"audio_path": audio_path, "words": words, "duration_seconds": duration}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    produce_audio(sys.argv[1])
