"""
Voice Agent — Generates natural voice audio from TTS-optimized scripts.
Primary: Kokoro TTS (local, free, high quality)
Fallback: Edge TTS (edge-tts library)
"""

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import TTS_VOICE_FALLBACK, TTS_SPEED, TTS_SILENCE_SHORT, TTS_SILENCE_LONG
from utils.file_manager import get_output_dir, update_progress_step, save_json


def insert_pauses(audio_segments: list, pause_positions: list) -> bytes:
    """
    Combine audio segments with silence at pause positions.
    Uses pydub for audio manipulation.
    """
    try:
        from pydub import AudioSegment
        import io

        combined = AudioSegment.empty()
        silence_short = AudioSegment.silent(duration=int(TTS_SILENCE_SHORT * 1000))
        silence_long = AudioSegment.silent(duration=int(TTS_SILENCE_LONG * 1000))

        for i, segment_bytes in enumerate(audio_segments):
            if isinstance(segment_bytes, bytes):
                segment = AudioSegment.from_mp3(io.BytesIO(segment_bytes))
            else:
                segment = segment_bytes
            combined += segment

            # Add pause after this segment if there's a pause position here
            if i < len(pause_positions):
                duration = pause_positions[i].get("duration", TTS_SILENCE_SHORT)
                if duration >= 1.0:
                    combined += silence_long
                else:
                    combined += silence_short

        # Export as MP3
        output_buffer = io.BytesIO()
        combined.export(output_buffer, format="mp3", bitrate="192k")
        return output_buffer.getvalue()

    except ImportError:
        print("[voice_agent] pydub not available — returning first segment only")
        return audio_segments[0] if audio_segments else b""


async def generate_edge_tts(text: str, voice: str = None) -> bytes:
    """Generate audio using Edge TTS (fallback)."""
    import edge_tts

    voice = voice or TTS_VOICE_FALLBACK
    communicate = edge_tts.Communicate(
        text,
        voice=voice,
        rate=f"+{int((TTS_SPEED - 1.0) * 100)}%",
    )

    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]

    return audio_data


def generate_kokoro_tts(text: str) -> bytes | None:
    """
    Generate audio using Kokoro TTS (local, high quality).
    Returns None if Kokoro is not installed.
    """
    try:
        from kokoro_onnx import Kokoro
        import soundfile as sf
        import numpy as np
        import io

        # Use the default English model
        kokoro = Kokoro("kokoro-v0_19.onnx", "voices.bin")
        samples, sample_rate = kokoro.create(
            text,
            voice="af_sarah",  # High quality English female voice
            speed=TTS_SPEED,
            lang="en-us"
        )

        # Convert to MP3 bytes
        buffer = io.BytesIO()
        sf.write(buffer, samples, sample_rate, format="mp3")
        return buffer.getvalue()

    except ImportError:
        return None
    except Exception as e:
        print(f"[voice_agent] Kokoro error: {e}")
        return None


def split_script_for_tts(tts_text: str, max_chars: int = 500) -> list[str]:
    """
    Split long TTS text into chunks at sentence boundaries.
    Edge TTS has a character limit per call.
    """
    sentences = tts_text.replace(". ", ".|").replace("? ", "?|").replace("! ", "!|").split("|")
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_chars:
            current_chunk += sentence + " "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + " "

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks if chunks else [tts_text]


def generate_audio(script_data: dict) -> bytes:
    """
    Generate audio from script. Tries Kokoro first, falls back to Edge TTS.
    Handles pause insertion from [PAUSE] tags.
    """
    tts_text = script_data.get("tts_text", "")
    if not tts_text:
        raise ValueError("No tts_text in script_data")

    print(f"[voice_agent] Generating audio ({len(tts_text)} chars)...")

    # Try Kokoro first
    audio_bytes = generate_kokoro_tts(tts_text)
    if audio_bytes:
        print("[voice_agent] Using Kokoro TTS")
        return audio_bytes

    # Fall back to Edge TTS
    print("[voice_agent] Using Edge TTS (fallback)")
    chunks = split_script_for_tts(tts_text)
    audio_segments = []

    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i+1}/{len(chunks)}: {chunk[:50]}...")
        segment = asyncio.run(generate_edge_tts(chunk))
        audio_segments.append(segment)

    if len(audio_segments) == 1:
        return audio_segments[0]

    # Merge segments
    return insert_pauses(audio_segments, script_data.get("pause_positions", []))


def save_audio(idea_id: str, audio_bytes: bytes) -> Path:
    """Save audio to output/[id]/audio.mp3"""
    output_dir = get_output_dir(idea_id)
    audio_path = output_dir / "audio.mp3"
    audio_path.write_bytes(audio_bytes)
    update_progress_step("audio_generated", idea_id)
    print(f"[voice_agent] Audio saved: {audio_path} ({len(audio_bytes)/1024:.1f}KB)")
    return audio_path


def get_audio_duration(audio_path: Path) -> float:
    """Get audio duration in seconds."""
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_mp3(str(audio_path))
        return len(audio) / 1000.0
    except Exception:
        return 0.0


def run(idea: dict, script_data: dict) -> Path:
    """Main entry point: generate voice audio."""
    audio_bytes = generate_audio(script_data)
    audio_path = save_audio(idea["id"], audio_bytes)

    # Log duration
    duration = get_audio_duration(audio_path)
    print(f"[voice_agent] Audio duration: {duration:.1f}s")

    if duration > 58 and idea.get("estimated_duration_seconds", 55) <= 60:
        print(f"[voice_agent] WARNING: Audio {duration:.1f}s exceeds 58s target for short video")

    return audio_path
