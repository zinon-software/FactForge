#!/usr/bin/env python3
"""Generate thumbnail for L00300"""
import urllib.request, urllib.parse, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io, sys

BASE = Path(__file__).parent.parent
OUT = BASE / "output/L00300"

def fetch_ai_bg():
    prompt = "ancient gold coins scattered roman denarius lydian stater bitcoin digital coin cinematic dramatic lighting rich dark background treasure history"
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&nologo=true&model=flux&seed=8421"
    print("Fetching AI background...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        data = r.read()
    print(f"  Background: {len(data)//1024}KB")
    return Image.open(io.BytesIO(data)).convert("RGB").resize((1280, 720))

def make_thumbnail():
    # Try AI bg, fallback to chapter image
    try:
        img = fetch_ai_bg()
    except Exception as e:
        print(f"  AI bg failed ({e}), using chapter image as fallback")
        fallback = OUT / "images/ch2_coins_A.jpg"
        if not fallback.exists():
            fallback = next((OUT / "images").glob("*.jpg"), None)
        if fallback:
            img = Image.open(fallback).convert("RGB").resize((1280, 720))
        else:
            img = Image.new("RGB", (1280, 720), (20, 15, 5))
    draw = ImageDraw.Draw(img)
    W, H = 1280, 720

    # Dark gradient overlay on bottom 55%
    from PIL import ImageFilter
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    grad_start = int(H * 0.40)
    for y in range(grad_start, H):
        alpha = int(210 * (y - grad_start) / (H - grad_start))
        od.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Top accent bar (gold)
    draw.rectangle([(0, 0), (W, 10)], fill="#D4AF37")
    # Bottom accent bar
    draw.rectangle([(0, H-8), (W, H)], fill="#D4AF37")

    # Category pill — top center
    pill_text = "SHOCKING HISTORY"
    try:
        pill_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
    except:
        pill_font = ImageFont.load_default()
    pw = draw.textlength(pill_text, font=pill_font)
    px, py = (W - pw) // 2 - 20, 28
    draw.rounded_rectangle([px, py, px + pw + 40, py + 36], radius=18, fill="#D4AF37")
    draw.text((px + 20, py + 8), pill_text, font=pill_font, fill="#000000")

    # Main stat — HUGE gold text
    try:
        stat_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 118)
    except:
        stat_font = ImageFont.load_default()

    stat_text = "3,000 YEARS"
    sw = draw.textlength(stat_text, font=stat_font)
    sx = (W - sw) // 2
    # Stroke
    for dx in range(-5, 6):
        for dy in range(-5, 6):
            if dx*dx + dy*dy <= 25:
                draw.text((sx+dx, 230+dy), stat_text, font=stat_font, fill="#000000")
    draw.text((sx, 230), stat_text, font=stat_font, fill="#FFD700")

    # Subtitle line 1
    try:
        sub_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 56)
    except:
        sub_font = ImageFont.load_default()

    line1 = "OF MONEY"
    l1w = draw.textlength(line1, font=sub_font)
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            if dx*dx + dy*dy <= 16:
                draw.text(((W-l1w)//2+dx, 358+dy), line1, font=sub_font, fill="#000000")
    draw.text(((W-l1w)//2, 358), line1, font=sub_font, fill="#FFFFFF")

    line2 = "FROM SHELLS TO BITCOIN"
    l2w = draw.textlength(line2, font=sub_font)
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            if dx*dx + dy*dy <= 16:
                draw.text(((W-l2w)//2+dx, 430+dy), line2, font=sub_font, fill="#000000")
    draw.text(((W-l2w)//2, 430), line2, font=sub_font, fill="#D4AF37")

    # FACTFORGE watermark — bottom center
    try:
        wm_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
    except:
        wm_font = ImageFont.load_default()
    wm = "FACTFORGE"
    wmw = draw.textlength(wm, font=wm_font)
    draw.text(((W-wmw)//2, H-50), wm, font=wm_font, fill="#888888")

    # Save as JPEG
    out_path = OUT / "thumbnail.jpg"
    img.save(str(out_path), "JPEG", quality=95)
    print(f"✅ Thumbnail saved: {out_path}")

if __name__ == "__main__":
    make_thumbnail()
