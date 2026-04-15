# Skill: Thumbnail Generation
# Use when generating thumbnails via Pillow (Python)

---

## Design Principles

Thumbnails must work at the smallest display size: **100px wide** on mobile.
Every thumbnail should be:
- Readable at 100px (large text only)
- High contrast (dark background, bright text or vice versa)
- Emotionally compelling at a glance
- Accurate to the video content (no misleading thumbnails)

---

## Dimensions

| Video Type | Dimensions | DPI |
|------------|-----------|-----|
| YouTube Short | 1080 × 1920 px | 72 |
| Long Video | 1280 × 720 px | 72 |

---

## Short Video Thumbnail (1080 × 1920)

### Layout
```
┌─────────────────────────┐
│                         │
│   [BACKGROUND IMAGE]    │  ← Pexels image, blurred 80%, darkened overlay
│   [blurred/darkened]    │
│                         │
│   ┌─────────────────┐   │
│   │  SHOCKING       │   │  ← Main text, max 3 words, 220px+ font
│   │  NUMBER OR      │   │
│   │  WORD           │   │
│   └─────────────────┘   │
│                         │
│   [subtitle line]       │  ← Supporting text, max 6 words, 80px font
│                         │
│              [LOGO]     │  ← Channel watermark, bottom right, 15% opacity
└─────────────────────────┘
```

### Color Themes by Topic
- Islamic/Arab history: deep navy (#0a1628) + gold (#d4af37)
- Wealth/Economics: black (#0d0d0d) + green (#00e676)
- Military/Power: dark red (#1a0000) + white (#ffffff)
- Science/Space: deep purple (#0d0021) + cyan (#00e5ff)
- General/History: charcoal (#1a1a2e) + orange (#ff6b35)

### Text Rules
- Font: Use a bold sans-serif (Arial Black, Impact, or similar)
- Maximum 3 words on main text
- No lowercase — ALL CAPS for main text
- Add text shadow: 3px blur, 50% black
- Numbers are better than words: "25%" beats "twenty-five percent"

---

## Long Video Thumbnail (1280 × 720)

### Layout
```
┌────────────────────────────────────┐
│                  │                 │
│   [BACKGROUND    │  HOOK TEXT      │
│    IMAGE or      │  2-3 WORDS      │
│    FACE]         │                 │
│                  │  [subtext]      │
│                  │                 │
│   [LEFT HALF]    │  [RIGHT HALF]   │
└────────────────────────────────────┘
```

### Color Border
- 6px accent color border on entire thumbnail
- Accent color matches topic theme

---

## Pillow Generation Code Template

```python
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests
from io import BytesIO

def generate_short_thumbnail(
    main_text: str,        # MAX 3 words, ALL CAPS
    sub_text: str,         # Max 6 words
    bg_image_url: str,     # From Pexels API
    color_theme: str,      # "islamic", "wealth", "military", "science", "general"
    output_path: str
):
    # 1. Load and prepare background
    W, H = 1080, 1920
    response = requests.get(bg_image_url)
    bg = Image.open(BytesIO(response.content)).convert("RGB")
    bg = bg.resize((W, H), Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=15))  # 80% blur

    # 2. Apply dark overlay
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 160))  # 63% dark
    bg = bg.convert("RGBA")
    bg.paste(overlay, (0, 0), overlay)

    # 3. Add color tint from theme
    themes = {
        "islamic": (10, 22, 40, 80),
        "wealth": (13, 13, 13, 60),
        "military": (26, 0, 0, 80),
        "science": (13, 0, 33, 80),
        "general": (26, 26, 46, 80),
    }
    tint = Image.new("RGBA", (W, H), themes.get(color_theme, themes["general"]))
    bg.paste(tint, (0, 0), tint)

    draw = ImageDraw.Draw(bg)

    # 4. Main text (center of image, 220px bold)
    # Load font — use system font or bundled font
    try:
        font_main = ImageFont.truetype("/System/Library/Fonts/Supplemental/Impact.ttf", 220)
        font_sub = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 90)
    except:
        font_main = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    # Center main text vertically (60% down)
    bbox = draw.textbbox((0, 0), main_text, font=font_main)
    text_w = bbox[2] - bbox[0]
    x = (W - text_w) // 2
    y = int(H * 0.4)

    # Draw shadow
    draw.text((x + 4, y + 4), main_text, font=font_main, fill=(0, 0, 0, 180))
    # Draw text
    accent_colors = {
        "islamic": "#d4af37", "wealth": "#00e676",
        "military": "#ffffff", "science": "#00e5ff", "general": "#ff6b35"
    }
    draw.text((x, y), main_text, font=font_main, fill=accent_colors.get(color_theme, "#ffffff"))

    # 5. Sub text
    bbox_sub = draw.textbbox((0, 0), sub_text, font=font_sub)
    sub_w = bbox_sub[2] - bbox_sub[0]
    draw.text(((W - sub_w) // 2, y + 280), sub_text, font=font_sub, fill="#cccccc")

    # 6. Save
    bg.convert("RGB").save(output_path, "PNG", quality=95)
    return output_path
```

---

## Quality Gate (MANDATORY — score ≥ 12/16 before proceeding)

Score each criterion. If total < 12, regenerate with different prompt/layout.
Save result to `output/[id]/thumbnail_score.json`.

### Scoring Rubric

| Criterion | 0 pts | 1 pt | 2 pts |
|---|---|---|---|
| **Text readability at 100px** | Unreadable | Partially readable | Crystal clear |
| **Single focal point** | Cluttered/confusing | Two competing elements | One clear hero element |
| **Contrast ratio** | Low contrast, text blends | Moderate contrast | High contrast, text pops |
| **Emotional impact** | Neutral, forgettable | Mildly interesting | Immediately stops the scroll |
| **Topic accuracy** | Misleading or wrong | Loosely related | Directly matches video content |
| **Color theme consistency** | Random colors | Partially matches theme | Perfect theme match |
| **Mobile legibility** | Text too small | Readable with effort | Instantly readable |
| **Uniqueness** | Generic stock photo look | Somewhat distinct | Distinctive, recognizable style |

**Minimum to proceed: 12/16**
If score 10–11: revise main text or regenerate background image
If score < 10: regenerate completely with different Pollinations prompt

### Save format:
```json
{"score": 14, "approved": true, "notes": "Strong contrast, clear number hero, Islamic gold theme matches perfectly"}
```

### Common failure modes and fixes:
- **Text unreadable**: increase font size, add heavier dark overlay (opacity 180+)
- **Cluttered**: remove subtitle text, let the number speak alone
- **Low contrast**: switch background to darker version, use white or gold text
- **Generic feel**: add the category pill badge, make the stat number 3x larger
- **Wrong emotion**: regenerate Pollinations background with stronger emotional prompt

### Pollinations prompt formula for maximum impact:
```
[dramatic adjective] [specific subject], [era/location], [lighting style], cinematic, photorealistic, 8K, ultra-detailed, no text, no watermarks
```
Examples:
- `"burning library ancient scrolls Baghdad 1258, golden firelight, cinematic, photorealistic, 8K"`
- `"empty Wall Street trading floor crash 2008, harsh fluorescent light, cinematic, photorealistic, 8K"`
- `"gold vault overflowing coins extreme closeup, dramatic rim lighting, cinematic, 8K"`
