"""
FactForge Audio Generator
Generates TTS audio + word-level timestamps using:
  - Edge-TTS (en-US-AndrewNeural) for audio
  - faster-whisper (tiny model) for word timestamps

Usage:
  python3 generate_audio.py <video_id>
  e.g.: python3 generate_audio.py S01062
"""

import asyncio, json, sys
from pathlib import Path
import edge_tts
from faster_whisper import WhisperModel

BASE = Path(__file__).parent.parent
_whisper_model = None

def get_whisper():
    global _whisper_model
    if _whisper_model is None:
        print("Loading Whisper tiny model...")
        _whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
    return _whisper_model


async def generate_tts(text: str, voice: str, rate: str, out_path: Path):
    """Generate audio with Edge-TTS."""
    comm = edge_tts.Communicate(text, voice=voice, rate=rate)
    await comm.save(str(out_path))
    print(f"  Audio saved: {out_path.name}")


def get_word_timestamps(audio_path: Path) -> list:
    """Extract word-level timestamps using faster-whisper."""
    model = get_whisper()
    segments, _ = model.transcribe(
        str(audio_path),
        word_timestamps=True,
        language="en",
        beam_size=1,
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
                "end_ms": round(w.end * 1000),
            })
    print(f"  Word timestamps: {len(words)} words")
    return words


def produce_audio(video_id: str):
    output_dir = BASE / "output" / video_id
    script_path = output_dir / "script.json"

    if not script_path.exists():
        print(f"ERROR: {script_path} not found")
        sys.exit(1)

    with open(script_path) as f:
        script = json.load(f)

    text  = script["full_text"]
    voice = script.get("tts_voice", "en-US-AndrewNeural")
    rate  = script.get("tts_rate", "+8%")

    audio_path = output_dir / "audio.mp3"

    print(f"[1/3] Generating TTS audio for {video_id}...")
    asyncio.run(generate_tts(text, voice, rate, audio_path))

    print(f"[2/3] Extracting word timestamps...")
    words = get_word_timestamps(audio_path)

    ts_path = output_dir / "word_timestamps.json"
    with open(ts_path, "w") as f:
        json.dump({"video_id": video_id, "words": words}, f, indent=2)
    print(f"  Saved: {ts_path.name}")

    # Also copy audio to remotion public folder
    import shutil
    remotion_audio = BASE / "video" / "remotion-project" / "public" / f"audio_{video_id}.mp3"
    shutil.copy(audio_path, remotion_audio)
    print(f"  Copied to Remotion: audio_{video_id}.mp3")

    print(f"[3/3] Done — audio duration: {words[-1]['end_ms']/1000:.1f}s")
    return words


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    produce_audio(sys.argv[1])
