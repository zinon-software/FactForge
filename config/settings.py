"""
YouTube Automation System — Configuration Constants
AI engine: Claude Code (active session) — no API key required.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─── Project Paths ────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / os.getenv("OUTPUT_DIR", "output")
DATABASE_DIR = BASE_DIR / os.getenv("DATABASE_DIR", "database")
STATE_DIR = BASE_DIR / os.getenv("STATE_DIR", "state")
CONFIG_DIR = BASE_DIR / "config"

# ─── API Keys (no Anthropic key — Claude Code handles AI) ─────────────────────
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")

# ─── YouTube ──────────────────────────────────────────────────────────────────
YOUTUBE_CREDENTIALS_PATH = BASE_DIR / os.getenv("YOUTUBE_CREDENTIALS_PATH", "config/youtube_credentials.json")
YOUTUBE_TOKEN_PATH = BASE_DIR / os.getenv("YOUTUBE_TOKEN_PATH", "config/youtube_token.json")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID", "")
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtubepartner",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

# ─── Video Settings ───────────────────────────────────────────────────────────
MAX_SHORT_DURATION = int(os.getenv("MAX_SHORT_DURATION", 58))
MAX_LONG_DURATION = int(os.getenv("MAX_LONG_DURATION", 900))
SHORT_TARGET_WORDS = (120, 160)
LONG_TARGET_WORDS = (1400, 1900)
SHORT_DIMENSIONS = (1080, 1920)
LONG_DIMENSIONS = (1920, 1080)
SHORT_FPS = 60
LONG_FPS = 30

# ─── Publishing ───────────────────────────────────────────────────────────────
PUBLISH_INTERVAL_HOURS = int(os.getenv("PUBLISH_INTERVAL_HOURS", 48))
TIMEZONE = os.getenv("TIMEZONE", "UTC")

OPTIMAL_PUBLISH_WINDOWS = [
    {"day": "tuesday",   "start_est": "14:00", "end_est": "16:00"},
    {"day": "wednesday", "start_est": "14:00", "end_est": "16:00"},
    {"day": "thursday",  "start_est": "14:00", "end_est": "16:00"},
    {"day": "saturday",  "start_est": "09:00", "end_est": "11:00"},
]

YOUTUBE_CATEGORY_EDUCATION = "27"
YOUTUBE_CATEGORY_ENTERTAINMENT = "24"

# ─── Content Settings ─────────────────────────────────────────────────────────
CONTENT_ANGLES = ["islamic_history", "shocking_stats", "geopolitical_comparison"]

FORMAT_TYPES = [
    "top_10_list", "top_5_list", "shocking_stat", "comparison",
    "timeline", "myth_vs_fact", "price_reveal", "size_comparison",
    "what_if", "hidden_truth",
]

CONTENT_CATEGORIES = [
    "islamic_arab_history",
    "wealth_economics",
    "military_geopolitics",
    "science_space",
    "human_body_medicine",
    "ancient_civilizations",
    "modern_technology_ai",
    "natural_world",
    "crime_justice",
    "architecture_engineering",
    "us_vs_china",
    "east_vs_west",
    "country_hidden_facts",
    "price_reveals",
]

TRANSLATION_LANGUAGES = ["es", "fr", "de", "hi", "pt", "id", "ja", "ko", "tr", "ar"]

# ─── TTS Settings ─────────────────────────────────────────────────────────────
TTS_VOICE_PRIMARY = "kokoro"
TTS_VOICE_FALLBACK = "am_echo"  # Kokoro only — no Edge TTS
TTS_SPEED = 1.08  # am_echo optimal speed
TTS_SILENCE_SHORT = 0.5
TTS_SILENCE_LONG = 1.0

# ─── Database ────────────────────────────────────────────────────────────────
TARGET_SHORT_IDEAS = 10000
TARGET_LONG_IDEAS = 500
QUEUE_SIZE = 100
BATCH_SIZE = 500
TREND_REFRESH_COUNT = 100
