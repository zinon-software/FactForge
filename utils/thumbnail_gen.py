"""
utils/thumbnail_gen.py — AI-backed thumbnail generation for FactForge.

Fetches a Pollinations Flux AI background (1280×720) and draws a Pillow
overlay following the MrBeast/Veritasium design standard:
  - top accent bar (14 px)
  - hero stat (giant, glowing)
  - title text (all-caps, max 2 lines, outlined)
  - FACTFORGE watermark
  - JPEG output (quality=95) — NEVER PNG (causes black display on YouTube)

Generates three colour variants: gold (A), blue (B), green (C).

Usage:
    from utils.thumbnail_gen import ThumbnailGenerator
    tg = ThumbnailGenerator()
    path = tg.generate("S01234", title="The Richest 1%", stat_text="$100T")
"""

import logging
import re
import time
from io import BytesIO
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import requests

from utils.config import cfg

logger = logging.getLogger(__name__)

# ── Thumbnail dimensions (ALL video types — YouTube requires 1280×720) ───────
THUMB_W = 1280
THUMB_H = 720

# ── Colour variants: (filename, accent_rgb, stat_rgb) ────────────────────────
_VARIANTS: list[tuple[str, tuple, tuple]] = [
    ("thumbnail.jpg",   (255, 200,   0), (255, 230,  50)),   # A — gold/yellow
    ("thumbnail_b.jpg", (  0,  85, 255), (100, 180, 255)),   # B — blue
    ("thumbnail_c.jpg", (  0, 170,  68), ( 80, 230, 120)),   # C — green
]


class ThumbnailGenerator:
    """Generates AI-background thumbnails with Pillow overlay for FactForge."""

    FONT_PATHS: list[str] = [
        "/System/Library/Fonts/Supplemental/Impact.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]

    # ── Public API ─────────────────────────────────────────────────────────────

    def generate(
        self,
        video_id: str,
        title: str,
        stat_text: str = "",
        category: str = "FACTFORGE",
        force: bool = False,
    ) -> Path:
        """
        Generate the primary thumbnail (gold variant A).

        Skips generation if thumbnail.jpg already exists and is > 5 KB,
        unless ``force=True``.

        Returns the Path to output/<video_id>/thumbnail.jpg.
        """
        thumb_path = cfg.OUTPUT_DIR / video_id / "thumbnail.jpg"

        if not force and thumb_path.exists() and thumb_path.stat().st_size > 5_000:
            logger.info("[SKIP] thumbnail.jpg already exists")
            return thumb_path

        paths = self.generate_variants(video_id, title, stat_text, category)
        return paths[0] if paths else thumb_path

    def generate_variants(
        self,
        video_id: str,
        title: str,
        stat_text: str = "",
        category: str = "FACTFORGE",
    ) -> list[Path]:
        """
        Generate three colour variants (A=gold, B=blue, C=green).

        Returns a list of Paths to the saved JPEG files.
        Raises ImportError if Pillow is not installed.
        """
        try:
            from PIL import Image, ImageDraw  # noqa: F401
        except ImportError as exc:
            raise ImportError("Pillow is required for thumbnail generation") from exc

        prompt = self._build_prompt(title, category)
        logger.info("Generating Pollinations thumbnail: %s…", prompt[:70])

        bg = self._fetch_ai_background(prompt, seed=42)
        saved: list[Path] = []

        for filename, accent_rgb, stat_rgb in _VARIANTS:
            out_path = cfg.OUTPUT_DIR / video_id / filename
            img = self._draw_overlay(bg.copy(), title, stat_text, category, accent_rgb, stat_rgb)
            img.save(str(out_path), "JPEG", quality=95)
            logger.info("  ✅ %s saved (%dKB)", filename, out_path.stat().st_size // 1024)
            saved.append(out_path)

        return saved

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _fetch_ai_background(self, prompt: str, seed: int = 0):
        """
        Download a Pollinations Flux image (1280×720).

        Returns a PIL.Image.Image.  Falls back to a dark gradient on failure.
        No API key required — free & commercial use allowed.
        """
        from PIL import Image

        url = (
            f"https://image.pollinations.ai/prompt/{quote(prompt)}"
            f"?width={THUMB_W}&height={THUMB_H}&nologo=true&model=flux&seed={seed}"
        )
        for attempt in range(3):
            try:
                r = requests.get(url, timeout=90)
                if r.status_code == 200 and len(r.content) > 5_000:
                    img = Image.open(BytesIO(r.content)).convert("RGB")
                    return img.resize((THUMB_W, THUMB_H), Image.Resampling.LANCZOS)
                logger.debug("Pollinations attempt %d: status %d", attempt + 1, r.status_code)
            except Exception as exc:
                logger.debug("Pollinations attempt %d: %s", attempt + 1, exc)
            time.sleep(5)

        logger.warning("AI background fetch failed — using dark gradient fallback")
        from PIL import Image as _Image
        return _Image.new("RGB", (THUMB_W, THUMB_H), (20, 20, 30))

    def _draw_overlay(
        self,
        img,
        title: str,
        stat: str,
        category: str,
        accent_rgb: tuple,
        stat_rgb: tuple,
    ):
        """
        Draw the Pillow overlay onto ``img`` (modified in-place).

        Layout (top → bottom):
          - 10 px accent bar (top)
          - hero stat centered at vertical midpoint (if provided)
          - title (all-caps, bottom area)
          - FACTFORGE watermark at very bottom
          - 10 px bottom accent bar
        """
        from PIL import Image, ImageDraw

        W, H = THUMB_W, THUMB_H

        # Dark gradient overlay on bottom 50%
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ov_draw = ImageDraw.Draw(overlay)
        for y in range(H // 2, H):
            alpha = int(200 * (y - H // 2) / (H // 2))
            ov_draw.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)

        # Top accent bar
        draw.rectangle([(0, 0), (W, 14)], fill=accent_rgb)
        # Bottom accent bar
        draw.rectangle([(0, H - 10), (W, H)], fill=accent_rgb)

        # Hero stat (giant, centered)
        if stat:
            self._outline_text(
                draw,
                (W // 2, H // 2 - 40),
                stat[:20],
                self._font(120),
                stat_rgb,
                (0, 0, 0),
            )

        # Title (all-caps, two lines max)
        title_upper = title.upper()[:60]
        self._outline_text(
            draw,
            (W // 2, H - 120),
            title_upper,
            self._font(62),
            (255, 255, 255),
            (0, 0, 0),
        )

        # FACTFORGE watermark
        draw.text(
            (W // 2, H - 25),
            "FACTFORGE",
            font=self._font(28),
            fill=(200, 200, 200),
            anchor="mm",
        )

        return img

    def _font(self, size: int):
        """Return the first available system font at ``size``."""
        from PIL import ImageFont
        for path in self.FONT_PATHS:
            try:
                from pathlib import Path as _Path
                if _Path(path).exists():
                    return ImageFont.truetype(path, size)
            except Exception:
                pass
        return ImageFont.load_default()

    @staticmethod
    def _outline_text(
        draw,
        xy: tuple,
        text: str,
        font,
        fill: tuple,
        outline: tuple,
        width: int = 7,
    ) -> None:
        """Draw text with a solid outline for readability on any background."""
        x, y = xy
        for dx in range(-width, width + 1, 2):
            for dy in range(-width, width + 1, 2):
                if dx or dy:
                    draw.text((x + dx, y + dy), text, font=font, fill=outline, anchor="mm")
        draw.text(xy, text, font=font, fill=fill, anchor="mm")

    @staticmethod
    def _build_prompt(title: str, category: str) -> str:
        """Build a Pollinations prompt for the given title and category."""
        return (
            f"Cinematic 4K background for YouTube thumbnail, vivid dramatic lighting, "
            f"topic: {title[:80]}, category: {category}, "
            "no text, no watermarks, high contrast, stunning visual impact"
        )

    # ── Convenience class method for script.json dicts ────────────────────────

    @classmethod
    def from_script(cls, video_id: str, script: dict, force: bool = False) -> Path:
        """
        Generate a thumbnail from a ``script.json`` dict.

        Extracts title, hero stat, and category automatically.
        Returns Path to output/<video_id>/thumbnail.jpg.
        """
        title    = script.get("title") or script.get("video_title") or video_id
        category = script.get("category", "FACTFORGE")
        stat     = _extract_hero_stat(script)
        tg = cls()
        return tg.generate(video_id, title, stat_text=stat, category=category, force=force)


def _extract_hero_stat(script: dict) -> str:
    """Pull a short numeric stat from the script dict for the hero text."""
    for field in ("hero_stat", "key_stat", "main_stat"):
        val = script.get(field)
        if val:
            return str(val)[:20]
    for fact in script.get("key_facts", []):
        m = re.search(r"[\$£€]?\d[\d,\.]+[MBKTmbt%]*", str(fact))
        if m:
            return m.group(0)[:20]
    return ""
