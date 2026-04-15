"""
utils/audio_pipeline.py — Audio production pipeline for FactForge.

Wraps Kokoro TTS, faster-whisper timestamps, procedural SFX mixing, and
optional CC0 background music into a single reusable class.

Voice: am_echo (Kokoro v1.0, Apache 2.0 — commercial safe).
NEVER use Edge TTS — Microsoft TOS prohibits commercial use on the free tier.

Usage:
    from utils.audio_pipeline import AudioPipeline
    ap = AudioPipeline()
    duration = ap.produce("S01234", script_text)
"""

import json
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import numpy as np
import requests
import soundfile as sf

from utils.config import cfg

logger = logging.getLogger(__name__)

# ── Lazy model singletons ─────────────────────────────────────────────────────
_kokoro_instance  = None
_whisper_instance = None


def _get_kokoro():
    global _kokoro_instance
    if _kokoro_instance is None:
        from kokoro_onnx import Kokoro
        logger.info("Loading Kokoro model…")
        _kokoro_instance = Kokoro(str(cfg.KOKORO_MODEL), str(cfg.KOKORO_VOICES))
    return _kokoro_instance


def _get_whisper():
    global _whisper_instance
    if _whisper_instance is None:
        from faster_whisper import WhisperModel
        logger.info("Loading Whisper %s model…", cfg.WHISPER_MODEL)
        _whisper_instance = WhisperModel(
            cfg.WHISPER_MODEL, device="cpu", compute_type="int8"
        )
    return _whisper_instance


# ── Procedural SFX helpers ────────────────────────────────────────────────────

def _make_whoosh(sr: int = 44100, duration: float = 0.35, volume: float = 0.18) -> np.ndarray:
    """Frequency sweep 150 Hz → 1 200 Hz — scene-transition whoosh."""
    t    = np.linspace(0, duration, int(sr * duration))
    freq = np.linspace(150, 1200, len(t))
    phase = np.cumsum(2 * np.pi * freq / sr)
    wave = np.sin(phase)
    env  = np.ones(len(t))
    fade_in  = int(0.05 * sr)
    fade_out = int(0.20 * sr)
    env[:fade_in]   = np.linspace(0, 1, fade_in)
    env[-fade_out:] = np.linspace(1, 0, fade_out)
    return (wave * env * volume).astype(np.float32)


def _make_tick(sr: int = 44100, volume: float = 0.22) -> np.ndarray:
    """Short click/tick — used on number reveals."""
    duration = 0.06
    t = np.linspace(0, duration, int(sr * duration))
    wave = np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 60)
    return (wave * volume).astype(np.float32)


def _make_heartbeat(sr: int = 44100, volume: float = 0.15) -> np.ndarray:
    """Double thump — used at peak/impact moments."""
    def thump(freq: int = 60, dur: float = 0.12) -> np.ndarray:
        t = np.linspace(0, dur, int(sr * dur))
        return np.sin(2 * np.pi * freq * t) * np.exp(-t * 25)

    beat1   = thump(60)
    gap     = np.zeros(int(sr * 0.10))
    beat2   = thump(55, 0.10)
    silence = np.zeros(int(sr * 0.05))
    full    = np.concatenate([silence, beat1, gap, beat2, silence])
    return (full * volume).astype(np.float32)


class AudioPipeline:
    """Full audio pipeline: TTS → timestamps → SFX → optional background music."""

    # ── Public API ────────────────────────────────────────────────────────────

    def generate_tts(
        self,
        video_id: str,
        text: str,
        voice: str = cfg.KOKORO_VOICE,
        speed: float = cfg.KOKORO_SPEED,
    ) -> float:
        """
        Kokoro TTS → output/<video_id>/audio.mp3.

        Converts WAV → MP3 via ffmpeg (192 kbps) and copies the result to
        ``video/remotion-project/public/<video_id>/audio.mp3``.

        Returns duration in seconds.
        """
        output_dir = cfg.OUTPUT_DIR / video_id
        output_dir.mkdir(parents=True, exist_ok=True)
        audio_path = output_dir / "audio.mp3"
        wav_path   = output_dir / "audio.wav"

        k = _get_kokoro()
        samples, sr = k.create(text, voice=voice, speed=speed, lang="en-us")
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
        logger.info("TTS: %s (%.1fs, voice=%s)", audio_path.name, duration, voice)

        # Mirror to Remotion public/
        public_dir = cfg.PUBLIC_DIR / video_id
        public_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(audio_path, public_dir / "audio.mp3")
        logger.debug("Copied to public/%s/audio.mp3", video_id)

        return duration

    def extract_timestamps(self, video_id: str) -> list[dict]:
        """
        faster-whisper (base model, word_timestamps=True) →
        output/<video_id>/word_timestamps.json.

        Returns a list of ``{word, start_ms, end_ms}`` dicts.
        """
        output_dir = cfg.OUTPUT_DIR / video_id
        audio_path = output_dir / "audio.mp3"
        ts_path    = output_dir / "word_timestamps.json"

        if not audio_path.exists():
            raise FileNotFoundError(f"audio.mp3 not found: {audio_path}")

        model = _get_whisper()
        segments, _ = model.transcribe(
            str(audio_path),
            word_timestamps=True,
            language="en",
            beam_size=5,
        )

        words: list[dict] = []
        for seg in segments:
            for w in seg.words:
                word = w.word.strip()
                if not word:
                    continue
                words.append(
                    {
                        "word":     word,
                        "start_ms": round(w.start * 1000),
                        "end_ms":   round(w.end   * 1000),
                    }
                )

        ts_path.write_text(json.dumps(words, indent=2))
        last_ms = words[-1]["end_ms"] / 1000 if words else 0
        logger.info("Timestamps: %d words, last at %.1fs", len(words), last_ms)
        return words

    def apply_sfx(self, video_id: str) -> None:
        """
        Mix procedural SFX into output/<video_id>/audio.mp3 based on
        segment types in remotion_props.json.

        - whoosh on every scene transition (all segments except the first)
        - tick on "number" type segments
        - heartbeat on "impact" type segments

        Saves audio_clean.mp3 as a backup before modifying audio.mp3.
        Copies the updated audio to the Remotion public/ folder.
        """
        output_dir = cfg.OUTPUT_DIR / video_id
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

        props    = json.loads(props_path.read_text())
        segments = props.get("segments", [])
        fps      = props.get("fps", cfg.SHORT_FPS)

        if not segments:
            return

        sr_target = 44100
        tmp_wav   = audio_path.with_suffix(".sfx_work.wav")
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(audio_path),
             "-ar", str(sr_target), "-ac", "1", str(tmp_wav)],
            capture_output=True,
        )
        if not tmp_wav.exists():
            logger.warning("[SFX] ffmpeg mono conversion failed")
            return

        audio_data, sr = sf.read(str(tmp_wav))
        audio_data = audio_data.astype(np.float32)
        total_samples = len(audio_data)

        def frame_to_sample(frame: int) -> int:
            return min(int(frame / fps * sr), total_samples - 1)

        def mix_at(sfx: np.ndarray, pos: int) -> None:
            end = min(pos + len(sfx), total_samples)
            audio_data[pos:end] += sfx[:end - pos]

        whoosh = _make_whoosh(sr)
        tick   = _make_tick(sr)
        hb     = _make_heartbeat(sr)

        n_whoosh = n_tick = n_hb = 0
        for i, seg in enumerate(segments):
            pos      = frame_to_sample(seg.get("startFrame", 0))
            seg_type = seg.get("type", "fact")

            if i > 0:
                mix_at(whoosh, max(0, pos - int(0.05 * sr)))
                n_whoosh += 1
            if seg_type == "number":
                mix_at(tick, pos + int(0.05 * sr))
                n_tick += 1
            if seg_type == "impact":
                mix_at(hb, pos)
                n_hb += 1

        # Normalize to prevent clipping
        peak = np.max(np.abs(audio_data))
        if peak > 0.95:
            audio_data = audio_data * (0.92 / peak)

        # Backup clean version
        shutil.copy(audio_path, clean_path)

        sf.write(str(tmp_wav), audio_data, sr)
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(tmp_wav), "-b:a", "192k", str(audio_path)],
            capture_output=True,
        )
        tmp_wav.unlink(missing_ok=True)

        logger.info(
            "SFX mixed: whoosh×%d + tick×%d + heartbeat×%d",
            n_whoosh, n_tick, n_hb,
        )

        # Re-copy to Remotion public
        public_dir = cfg.PUBLIC_DIR / video_id
        public_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(audio_path, public_dir / "audio.mp3")
        logger.debug("Updated public/%s/audio.mp3 with SFX", video_id)

    def mix_background_music(self, video_id: str, volume: float = 0.10) -> None:
        """
        Download a CC0 instrumental track from Pixabay Music and mix it into
        output/<video_id>/audio.mp3 at ``volume`` (default 10%).

        Saves audio_clean.mp3 as a backup if one does not already exist.
        Replaces audio.mp3 with the mixed result.
        """
        output_dir = cfg.OUTPUT_DIR / video_id
        audio_path = output_dir / "audio.mp3"
        music_path = output_dir / "bg_music.mp3"

        if not audio_path.exists():
            logger.warning("[music] audio.mp3 not found for %s — skipping", video_id)
            return

        # ── Download background track ─────────────────────────────────────────
        if not music_path.exists():
            try:
                r = requests.get(
                    "https://pixabay.com/api/",
                    params={
                        "key":        cfg.pixabay_key(),
                        "q":          "background music instrumental",
                        "media_type": "music",
                        "per_page":   10,
                        "category":   "music",
                    },
                    timeout=20,
                )
                r.raise_for_status()
                hits = r.json().get("hits", [])
                if not hits:
                    logger.warning("[music] No tracks from Pixabay Music — skipping")
                    return

                track_url: Optional[str] = None
                for hit in hits:
                    track_url = hit.get("audio") or hit.get("previewURL") or hit.get("url")
                    if track_url:
                        break

                if not track_url:
                    logger.warning("[music] No downloadable audio URL found — skipping")
                    return

                logger.info("Downloading bg music: %s…", track_url[:60])
                dl = requests.get(track_url, timeout=60, stream=True)
                dl.raise_for_status()
                with open(music_path, "wb") as fh:
                    for chunk in dl.iter_content(chunk_size=1024 * 256):
                        fh.write(chunk)
                logger.info("bg_music.mp3 saved (%dKB)", music_path.stat().st_size // 1024)

            except Exception as exc:
                logger.warning("[music] Download failed: %s — skipping", exc)
                return

        # ── Backup clean audio ────────────────────────────────────────────────
        clean_backup = output_dir / "audio_clean.mp3"
        if not clean_backup.exists():
            shutil.copy(audio_path, clean_backup)

        # ── Mix with ffmpeg ───────────────────────────────────────────────────
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
            logger.warning("[music] ffmpeg mix failed: %s", result.stderr[-300:])
            return

        os.replace(str(mixed_path), str(audio_path))
        logger.info("Background music mixed at %d%% — audio.mp3 updated", int(volume * 100))

    def produce(
        self,
        video_id: str,
        text: str,
        sfx:   bool = True,
        music: bool = False,
    ) -> float:
        """
        Full pipeline: TTS → timestamps → (SFX) → (background music).

        SFX is applied only if remotion_props.json already exists in the
        output directory (props are built by the render pipeline after this
        step; call ``apply_sfx`` again after props are ready if needed).

        Returns audio duration in seconds.
        """
        output_dir = cfg.OUTPUT_DIR / video_id
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("[1/3] Kokoro TTS (%s) for %s…", cfg.KOKORO_VOICE, video_id)
        duration = self.generate_tts(video_id, text)

        logger.info("[2/3] Word timestamps (Whisper %s)…", cfg.WHISPER_MODEL)
        self.extract_timestamps(video_id)

        if sfx:
            props_path = output_dir / "remotion_props.json"
            if props_path.exists():
                logger.info("Mixing SFX…")
                self.apply_sfx(video_id)
            else:
                logger.info(
                    "[SFX] No remotion_props.json yet — call apply_sfx() after props are built"
                )

            if music:
                logger.info("Mixing background music (%.0f%%)…", music * 100 if isinstance(music, float) else 10)
                self.mix_background_music(video_id)

        logger.info("[3/3] Done — %.1fs audio", duration)
        return duration
