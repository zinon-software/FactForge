"""
utils/config.py — Central configuration for FactForge.
All paths, API keys, and constants live here.
Import: from utils.config import cfg
"""
from pathlib import Path
import os


class Config:
    # ── Paths ──────────────────────────────────────────────────────────────────
    ROOT         = Path(__file__).parent.parent
    OUTPUT_DIR   = ROOT / "output"
    PUBLIC_DIR   = ROOT / "video/remotion-project/public"
    CONFIG_DIR   = ROOT / "config"
    STATE_DIR    = ROOT / "state"
    DATABASE_DIR = ROOT / "database"
    MODELS_DIR   = ROOT / "models/kokoro"
    SCRIPTS_DIR  = ROOT / "scripts"

    # ── Kokoro TTS ─────────────────────────────────────────────────────────────
    KOKORO_MODEL  = MODELS_DIR / "kokoro-v1.0.onnx"
    KOKORO_VOICES = MODELS_DIR / "voices-v1.0.bin"
    KOKORO_VOICE  = "am_echo"   # American male, authoritative, commercial safe (Apache 2.0)
    KOKORO_SPEED  = 1.08        # Slightly faster for Shorts energy

    # ── Whisper ────────────────────────────────────────────────────────────────
    WHISPER_MODEL = "base"      # base is more accurate than tiny for word timestamps

    # ── Video ──────────────────────────────────────────────────────────────────
    SHORT_FPS            = 60
    LONG_FPS             = 30
    SHORT_MIN_DURATION   = 35
    SHORT_MAX_DURATION   = 60
    SHORT_TARGET_DURATION = 52

    # ── Remotion ───────────────────────────────────────────────────────────────
    REMOTION_DIR         = ROOT / "video/remotion-project"
    REMOTION_CONCURRENCY = 2

    # ── Lazy .env loader ───────────────────────────────────────────────────────
    _env_loaded: bool = False
    _env: dict = {}

    @classmethod
    def _load_env(cls) -> None:
        if cls._env_loaded:
            return
        env_file = cls.CONFIG_DIR / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    cls._env[k.strip()] = v.strip().strip('"').strip("'")
        cls._env_loaded = True

    @classmethod
    def get(cls, key: str, default: str = "") -> str:
        """Return env var value, falling back to config/.env, then default."""
        cls._load_env()
        return os.getenv(key) or cls._env.get(key, default)

    @classmethod
    def require(cls, key: str) -> str:
        """Return env var value or raise RuntimeError if missing."""
        val = cls.get(key)
        if not val:
            raise RuntimeError(
                f"Missing required config: {key}. Add it to config/.env"
            )
        return val

    # ── Convenience API key accessors ─────────────────────────────────────────
    @classmethod
    def pexels_key(cls) -> str:
        return cls.require("PEXELS_API_KEY")

    @classmethod
    def coverr_key(cls) -> str:
        return cls.get("COVERR_API_KEY", "1a9501ffa55e7c45a86eed2b6c6bd34a")

    @classmethod
    def coverr_app_id(cls) -> str:
        return cls.get("COVERR_APP_ID", "87FCDE58BB778CC2E9FB")

    @classmethod
    def pixabay_key(cls) -> str:
        return cls.get("PIXABAY_API_KEY", "55448442-b529cb16ef94bcaa210308891")

    # ── Files to keep after clean ──────────────────────────────────────────────
    KEEP_FILES = {
        "metadata.json",
        "script.json",
        "research.json",
        "sources.json",
        "thumbnail.jpg",
        "remotion_props.json",
        "word_timestamps.json",
        "produce_checkpoint.json",
        "DELETED.md",
    }


cfg = Config()
