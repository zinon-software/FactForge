"""
Thumbnail Agent — Creates click-worthy thumbnails using Pillow.
Two formats: 1080×1920 for Shorts, 1280×720 for long videos.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import SHORT_DIMENSIONS, LONG_DIMENSIONS
from utils.web_search import get_pexels_media
from utils.file_manager import get_output_dir, update_progress_step


# Color themes per content category
COLOR_THEMES = {
    "islamic_arab_history":     {"bg": (10, 22, 40),   "accent": (212, 175, 55),  "text": (255, 255, 255)},
    "wealth_economics":         {"bg": (13, 13, 13),   "accent": (0, 230, 118),   "text": (255, 255, 255)},
    "military_geopolitics":     {"bg": (26, 0, 0),     "accent": (255, 50, 50),   "text": (255, 255, 255)},
    "science_space":            {"bg": (13, 0, 33),    "accent": (0, 229, 255),   "text": (255, 255, 255)},
    "human_body_medicine":      {"bg": (0, 20, 40),    "accent": (0, 200, 200),   "text": (255, 255, 255)},
    "ancient_civilizations":    {"bg": (40, 20, 0),    "accent": (255, 165, 0),   "text": (255, 255, 255)},
    "modern_technology_ai":     {"bg": (5, 15, 30),    "accent": (100, 200, 255), "text": (255, 255, 255)},
    "natural_world":            {"bg": (0, 30, 15),    "accent": (50, 205, 50),   "text": (255, 255, 255)},
    "crime_justice":            {"bg": (20, 0, 0),     "accent": (220, 50, 50),   "text": (255, 255, 255)},
    "architecture_engineering": {"bg": (20, 20, 20),   "accent": (200, 180, 150), "text": (255, 255, 255)},
    "us_vs_china":              {"bg": (10, 10, 30),   "accent": (255, 100, 0),   "text": (255, 255, 255)},
    "east_vs_west":             {"bg": (15, 0, 30),    "accent": (150, 100, 255), "text": (255, 255, 255)},
    "country_hidden_facts":     {"bg": (0, 15, 30),    "accent": (255, 200, 0),   "text": (255, 255, 255)},
    "price_reveals":            {"bg": (10, 30, 10),   "accent": (0, 255, 100),   "text": (255, 255, 255)},
}

DEFAULT_THEME = {"bg": (15, 15, 30), "accent": (255, 107, 53), "text": (255, 255, 255)}


def get_theme(category: str) -> dict:
    return COLOR_THEMES.get(category, DEFAULT_THEME)


def _get_font(size: int):
    """Load the best available bold font."""
    from PIL import ImageFont

    font_candidates = [
        "/System/Library/Fonts/Supplemental/Impact.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
    ]
    for path in font_candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def generate_short_thumbnail(
    main_text: str,
    sub_text: str,
    category: str,
    bg_image_url: str = None,
    output_path: Path = None,
) -> Path:
    """Generate 1080×1920 thumbnail for YouTube Shorts."""
    from PIL import Image, ImageDraw, ImageFilter
    import requests
    from io import BytesIO

    W, H = SHORT_DIMENSIONS  # 1080 × 1920
    theme = get_theme(category)

    # Create background
    bg = Image.new("RGB", (W, H), theme["bg"])

    # Try to add background image from Pexels
    if bg_image_url:
        try:
            resp = requests.get(bg_image_url, timeout=8)
            bg_img = Image.open(BytesIO(resp.content)).convert("RGB")
            bg_img = bg_img.resize((W, H), Image.LANCZOS)
            bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=12))
            # Dark overlay
            overlay = Image.new("RGBA", (W, H), (0, 0, 0, 180))
            bg_img = bg_img.convert("RGBA")
            bg_img.paste(overlay, (0, 0), overlay)
            # Color tint
            tint = Image.new("RGBA", (W, H), (*theme["bg"], 100))
            bg_img.paste(tint, (0, 0), tint)
            bg = bg_img.convert("RGB")
        except Exception as e:
            print(f"[thumbnail] Background image failed: {e} — using solid color")

    draw = ImageDraw.Draw(bg)

    # Main text (center of image, large)
    main_text_upper = main_text.upper()[:20]  # Cap length
    font_size = 200 if len(main_text_upper) <= 6 else (150 if len(main_text_upper) <= 12 else 110)
    font_main = _get_font(font_size)

    # Measure text for centering
    bbox = draw.textbbox((0, 0), main_text_upper, font=font_main)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (W - text_w) // 2
    y = int(H * 0.38)

    # Shadow
    draw.text((x + 5, y + 5), main_text_upper, font=font_main, fill=(0, 0, 0, 200))
    # Main text
    draw.text((x, y), main_text_upper, font=font_main, fill=theme["accent"])

    # Sub text
    if sub_text:
        font_sub = _get_font(85)
        sub_upper = sub_text.upper()[:30]
        bbox_sub = draw.textbbox((0, 0), sub_upper, font=font_sub)
        sub_w = bbox_sub[2] - bbox_sub[0]
        x_sub = (W - sub_w) // 2
        y_sub = y + text_h + 60

        draw.text((x_sub + 3, y_sub + 3), sub_upper, font=font_sub, fill=(0, 0, 0, 200))
        draw.text((x_sub, y_sub), sub_upper, font=font_sub, fill=theme["text"])

    # Accent bar at bottom
    draw.rectangle([(0, H - 20), (W, H)], fill=theme["accent"])

    if not output_path:
        output_path = Path("output/temp_thumbnail.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    bg.save(str(output_path), "PNG")
    return output_path


def generate_long_thumbnail(
    main_text: str,
    sub_text: str,
    category: str,
    bg_image_url: str = None,
    output_path: Path = None,
) -> Path:
    """Generate 1280×720 thumbnail for long videos."""
    from PIL import Image, ImageDraw, ImageFilter
    import requests
    from io import BytesIO

    W, H = LONG_DIMENSIONS  # 1280 × 720
    theme = get_theme(category)

    # Base background
    bg = Image.new("RGB", (W, H), theme["bg"])

    # Left half: image (if available)
    if bg_image_url:
        try:
            resp = requests.get(bg_image_url, timeout=8)
            img = Image.open(BytesIO(resp.content)).convert("RGB")
            img = img.resize((W // 2, H), Image.LANCZOS)
            img = img.filter(ImageFilter.GaussianBlur(radius=3))
            bg.paste(img, (0, 0))
        except Exception as e:
            print(f"[thumbnail] Image failed: {e}")

    draw = ImageDraw.Draw(bg)

    # Vertical divider line
    draw.rectangle([(W // 2 - 4, 0), (W // 2, H)], fill=theme["accent"])

    # Right half: text
    right_x = W // 2 + 30
    available_w = W // 2 - 60

    font_main = _get_font(100)
    # Wrap text if needed
    words = main_text.upper().split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font_main)
        if bbox[2] - bbox[0] > available_w and current:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)

    y = H // 4
    for line in lines[:3]:  # Max 3 lines
        draw.text((right_x + 3, y + 3), line, font=font_main, fill=(0, 0, 0, 200))
        draw.text((right_x, y), line, font=font_main, fill=theme["accent"])
        bbox = draw.textbbox((0, 0), line, font=font_main)
        y += (bbox[3] - bbox[1]) + 20

    # Sub text
    if sub_text:
        font_sub = _get_font(55)
        draw.text((right_x, y + 20), sub_text[:40], font=font_sub, fill=theme["text"])

    # Accent border
    border = 8
    draw.rectangle([(0, 0), (W - 1, H - 1)], outline=theme["accent"], width=border)

    if not output_path:
        output_path = Path("output/temp_thumbnail_long.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    bg.save(str(output_path), "PNG")
    return output_path


def run(idea: dict, metadata: dict = None) -> Path:
    """Main entry point: generate thumbnail for an idea."""
    output_dir = get_output_dir(idea["id"])
    thumbnail_path = output_dir / "thumbnail.png"

    # Get background image from Pexels
    search_query = idea.get("key_facts", [idea["title"]])[0]
    media = get_pexels_media(search_query, media_type="photos", per_page=3)
    bg_url = media[0]["url"] if media else None

    # Determine main text (shocking number or key word)
    hook = idea.get("hook", idea["title"])
    # Extract number from hook if present
    import re
    numbers = re.findall(r'\b\d+(?:[.,]\d+)?%?\b', hook)
    main_text = numbers[0] if numbers else hook.split()[-1][:10]
    sub_text = idea["title"][:40]

    category = idea.get("category", "general")
    duration = idea.get("estimated_duration_seconds", 55)

    if duration <= 60:
        path = generate_short_thumbnail(main_text, sub_text, category, bg_url, thumbnail_path)
    else:
        path = generate_long_thumbnail(main_text, sub_text, category, bg_url, thumbnail_path)

    update_progress_step("thumbnail_generated", idea["id"])
    print(f"[thumbnail_agent] Thumbnail saved: {path}")
    return path
