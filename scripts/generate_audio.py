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

import json, sys, shutil, argparse
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
    print(f"  SFX mixed: whoosh×{len([s for s in segments[1:]])} + tick×{len([s for s in segments if s.get('type')=='number'])} + hb×{len([s for s in segments if s.get('type')=='impact'])}")


def produce_audio(video_id: str, text: str = None, speed: float = KOKORO_SPEED, sfx: bool = True) -> dict:
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

    # Mix SFX into audio (whoosh on scene changes, tick on numbers, heartbeat on impact)
    if sfx:
        props_path = output_dir / "remotion_props.json"
        if props_path.exists():
            print(f"  Mixing SFX...")
            _mix_sfx_into_audio(audio_path, props_path)
        else:
            print(f"  [SFX] No remotion_props.json yet — SFX will be applied after props are built")

    # Copy to Remotion public
    public_dir = BASE / "video/remotion-project/public" / video_id
    public_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(audio_path, public_dir / "audio.mp3")
    print(f"  Copied to public/{video_id}/audio.mp3")

    print(f"[3/3] Done — {duration:.1f}s, {len(words)} words")
    return {"audio_path": audio_path, "words": words, "duration_seconds": duration}


def apply_sfx(video_id: str) -> None:
    """Apply SFX to existing audio after remotion_props.json is ready. Call after step_props."""
    output_dir = BASE / "output" / video_id
    audio_path = output_dir / "audio.mp3"
    props_path = output_dir / "remotion_props.json"
    clean_path = output_dir / "audio_clean.mp3"

    if not audio_path.exists():
        print(f"  [SFX] audio.mp3 not found for {video_id}")
        return
    if not props_path.exists():
        print(f"  [SFX] remotion_props.json not found for {video_id}")
        return
    if clean_path.exists():
        print(f"  [SFX] Already applied (audio_clean.mp3 exists) — skipping")
        return

    print(f"  Mixing SFX into {video_id}/audio.mp3...")
    _mix_sfx_into_audio(audio_path, props_path)

    # Re-copy to Remotion public
    public_dir = BASE / "video/remotion-project/public" / video_id
    public_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(audio_path, public_dir / "audio.mp3")
    print(f"  Updated public/{video_id}/audio.mp3 with SFX")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FactForge audio generator")
    parser.add_argument("video_id", help="Video ID e.g. S01220")
    parser.add_argument("--no-sfx", action="store_true", help="Skip SFX mixing")
    parser.add_argument("--sfx-only", action="store_true", help="Apply SFX to existing audio (after props are built)")
    args = parser.parse_args()

    if args.sfx_only:
        apply_sfx(args.video_id)
    else:
        produce_audio(args.video_id, sfx=not args.no_sfx)
