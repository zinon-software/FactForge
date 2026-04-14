"""
generate_thumbnails.py — High-CTR YouTube thumbnails
Design principles: MrBeast/Veritasium style
- BRIGHT backgrounds (not dark)
- Huge shocking stat as hero
- Max 5 words of text
- High contrast yellow/red/white
- Correct aspect ratios: 1280x720 for Long, 1080x1920 for Shorts
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, math

BASE = "/Users/ar/Development/projects/FactForge"

def get_font(size):
    for path in [
        "/System/Library/Fonts/Supplemental/Impact.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        if os.path.exists(path):
            try: return ImageFont.truetype(path, size)
            except: pass
    return ImageFont.load_default()

def hex_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0,2,4))

def outline_text(draw, xy, text, font, fill, outline, width=6):
    x, y = xy
    for dx in range(-width, width+1, 2):
        for dy in range(-width, width+1, 2):
            if dx or dy:
                draw.text((x+dx, y+dy), text, font=font, fill=outline, anchor="mm")
    draw.text(xy, text, font=font, fill=fill, anchor="mm")

def shadow_text(draw, xy, text, font, fill, shadow=(0,0,0), dist=8):
    x, y = xy
    draw.text((x+dist, y+dist), text, font=font, fill=(*shadow,160), anchor="mm")
    draw.text(xy, text, font=font, fill=fill, anchor="mm")

def make_thumbnail(vid_id, cfg):
    is_short = vid_id.startswith("S")
    W, H = (1080, 1920) if is_short else (1280, 720)

    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)

    bg = cfg["bg"]           # main background color
    accent = cfg["accent"]   # bright accent (yellow, red, cyan...)
    text_color = cfg.get("text_color", "#FFFFFF")

    bg_rgb = hex_rgb(bg)
    acc_rgb = hex_rgb(accent)
    txt_rgb = hex_rgb(text_color)

    # ── 1. Background: solid + gradient sweep ─────────────────────
    for y in range(H):
        t = y / H
        r = int(bg_rgb[0] * (1 - t*0.35))
        g = int(bg_rgb[1] * (1 - t*0.35))
        b = int(bg_rgb[2] * (1 - t*0.35))
        draw.line([(0,y),(W,y)], fill=(r,g,b))

    # ── 2. Big accent blob (top-right glow) ───────────────────────
    blob = Image.new("RGBA", (W,H), (0,0,0,0))
    bd = ImageDraw.Draw(blob)
    for r in range(min(W,H)//2, 0, -30):
        alpha = max(0, int(60 * (1 - r/(min(W,H)//2))))
        bd.ellipse([W-r, -r, W+r, r], fill=(*acc_rgb, alpha))
    img = Image.alpha_composite(img.convert("RGBA"), blob).convert("RGB")
    draw = ImageDraw.Draw(img)

    # ── 3. Diagonal accent stripe (bottom-left) ───────────────────
    stripe = Image.new("RGBA", (W,H), (0,0,0,0))
    sd = ImageDraw.Draw(stripe)
    sd.polygon([(0,H),(int(W*0.55),H),(0,int(H*0.55))], fill=(*acc_rgb,40))
    img = Image.alpha_composite(img.convert("RGBA"), stripe).convert("RGB")
    draw = ImageDraw.Draw(img)

    # ── 4. Bold accent bar at top ─────────────────────────────────
    bar_h = int(H * 0.013)
    draw.rectangle([0,0,W,bar_h], fill=acc_rgb)

    # ── 5. MAIN STAT (hero element) ───────────────────────────────
    stat = cfg.get("stat","")
    if stat:
        stat_size = cfg.get("stat_size", int(H * 0.30))
        stat_y = cfg.get("stat_y", int(H * 0.38))
        f_stat = get_font(stat_size)
        # Yellow glow layers
        for glow_r, alpha in [(stat_size//2, 25),(stat_size//3, 40),(stat_size//4, 60)]:
            glow = Image.new("RGBA",(W,H),(0,0,0,0))
            gd = ImageDraw.Draw(glow)
            gd.text((W//2, stat_y), stat, font=f_stat, fill=(*acc_rgb, alpha), anchor="mm")
            glow = glow.filter(ImageFilter.GaussianBlur(radius=glow_r))
            img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
        draw = ImageDraw.Draw(img)
        outline_text(draw, (W//2, stat_y), stat, f_stat, acc_rgb, (0,0,0), width=8)

    # ── 6. Line 1 (white, large) ──────────────────────────────────
    line1 = cfg.get("line1","").upper()
    if line1:
        l1_size = cfg.get("l1_size", int(H * 0.075))
        l1_y = cfg.get("l1_y", int(H * 0.65))
        f1 = get_font(l1_size)
        outline_text(draw, (W//2, l1_y), line1, f1, (255,255,255), (0,0,0), width=6)

    # ── 7. Line 2 (accent color, slightly smaller) ────────────────
    line2 = cfg.get("line2","").upper()
    if line2:
        l2_size = cfg.get("l2_size", int(H * 0.065))
        l2_y = cfg.get("l2_y", int(H * 0.75))
        f2 = get_font(l2_size)
        outline_text(draw, (W//2, l2_y), line2, f2, acc_rgb, (0,0,0), width=5)

    # ── 8. Category pill ─────────────────────────────────────────
    cat = cfg.get("category","").upper()
    if cat:
        f_cat = get_font(int(H*0.028))
        bbox = draw.textbbox((0,0), cat, font=f_cat, anchor="mm")
        pw = (bbox[2]-bbox[0]) + int(W*0.05)
        ph = int(H*0.045)
        px, py = W//2, int(H*0.055)
        draw.rounded_rectangle([px-pw//2, py-ph//2, px+pw//2, py+ph//2],
                                radius=ph//2, fill=acc_rgb)
        draw.text((px, py), cat, font=f_cat, fill=(0,0,0), anchor="mm")

    # ── 9. FACTFORGE watermark ────────────────────────────────────
    f_wm = get_font(int(H*0.022))
    wm_y = H - int(H*0.025)
    draw.text((W//2, wm_y), "FACTFORGE", font=f_wm,
              fill=(*acc_rgb, 180), anchor="mm")

    # ── 10. Bottom bar ────────────────────────────────────────────
    draw.rectangle([0, H-bar_h, W, H], fill=acc_rgb)

    # Save as JPEG
    out = f"{BASE}/output/{vid_id}/thumbnail.jpg"
    os.makedirs(f"{BASE}/output/{vid_id}", exist_ok=True)
    img.save(out, "JPEG", quality=95)
    print(f"  ✓ {vid_id} ({'Short 1080×1920' if is_short else 'Long 1280×720'}) — {cfg.get('line1','')[:35]}")
    return out


# ═══════════════════════════════════════════════════════════════
# THUMBNAIL CONFIGS
# bg: bright vivid color (NOT dark black)
# accent: high-contrast color on bg
# stat: the shocking number/word (biggest element)
# ═══════════════════════════════════════════════════════════════

THUMBNAILS = {
    # ── LONG VIDEOS (1280×720) ─────────────────────────────────────
    "L00100": {
        "bg": "#1565C0",        # deep blue
        "accent": "#FFD600",    # yellow
        "stat": "#1", "stat_size": 380, "stat_y": 310,
        "line1": "Richest person", "l1_size": 72, "l1_y": 530,
        "line2": "on Earth — revealed", "l2_size": 62, "l2_y": 610,
        "category": "Wealth Ranking 2026",
    },
    "L00016": {
        "bg": "#1B5E20",        # dark green
        "accent": "#FFEB3B",    # yellow
        "stat": "45%", "stat_size": 340, "stat_y": 290,
        "line1": "Owned by 1% of people", "l1_size": 66, "l1_y": 510,
        "line2": "Bottom 50% share 2%", "l2_size": 58, "l2_y": 590,
        "category": "The Wealth Gap",
    },

    # ── SHORTS (1080×1920) ─────────────────────────────────────────
    "S01117": {
        "bg": "#1A237E",        # indigo
        "accent": "#69FF47",    # lime green
        "stat": "36", "stat_size": 520, "stat_y": 680,
        "line1": "Politicians passed", "l1_size": 94, "l1_y": 1150,
        "line2": "ChatGPT's law", "l2_size": 88, "l2_y": 1270,
        "category": "AI Wrote the Law",
    },
    "S01279": {
        "bg": "#0D47A1",        # blue
        "accent": "#FF3D00",    # red-orange
        "stat": "CRISPR", "stat_size": 240, "stat_y": 650,
        "line1": "Edited babies' DNA", "l1_size": 88, "l1_y": 1120,
        "line2": "Can't be undone", "l2_size": 82, "l2_y": 1240,
        "category": "Gene Editing Scandal",
    },
    "S01062": {
        "bg": "#B71C1C",        # deep red
        "accent": "#FFD600",    # yellow
        "stat": "$608", "stat_size": 420, "stat_y": 680,
        "line1": "EpiPen costs $7", "l1_size": 90, "l1_y": 1150,
        "line2": "to make", "l2_size": 92, "l2_y": 1270,
        "category": "Healthcare Robbery",
    },
    "S01110": {
        "bg": "#004D40",        # teal
        "accent": "#FFEB3B",    # yellow
        "stat": "$0", "stat_size": 520, "stat_y": 680,
        "line1": "University in Germany", "l1_size": 80, "l1_y": 1140,
        "line2": "$108,000 in USA", "l2_size": 84, "l2_y": 1260,
        "category": "Education Gap",
    },
    "S01155": {
        "bg": "#1B5E20",        # green
        "accent": "#FF6D00",    # orange
        "stat": "5GW", "stat_size": 420, "stat_y": 680,
        "line1": "Africa's largest dam", "l1_size": 84, "l1_y": 1150,
        "line2": "Built by the people", "l2_size": 78, "l2_y": 1265,
        "category": "GERD Dam",
    },
    "S01183": {
        "bg": "#880E4F",        # dark pink
        "accent": "#FFEB3B",    # yellow
        "stat": "$84K", "stat_size": 400, "stat_y": 680,
        "line1": "Pill that cures Hep-C", "l1_size": 80, "l1_y": 1150,
        "line2": "Costs $1 to make", "l2_size": 82, "l2_y": 1265,
        "category": "Big Pharma",
    },
    "S01185": {
        "bg": "#311B92",        # deep purple
        "accent": "#FF3D00",    # red
        "stat": "40B", "stat_size": 450, "stat_y": 680,
        "line1": "Photos of your face", "l1_size": 84, "l1_y": 1150,
        "line2": "In a database", "l2_size": 88, "l2_y": 1265,
        "category": "Facial Recognition",
    },
    "S01190": {
        "bg": "#E65100",        # burnt orange
        "accent": "#FFFF00",    # yellow
        "stat": "$9.9T", "stat_size": 350, "stat_y": 680,
        "line1": "OpenAI is being", "l1_size": 88, "l1_y": 1150,
        "line2": "sued for this", "l2_size": 88, "l2_y": 1265,
        "category": "AI Lawsuit",
    },
    "S01215": {
        "bg": "#1A237E",        # navy
        "accent": "#FF3D00",    # red
        "stat": "120", "stat_size": 460, "stat_y": 680,
        "line1": "Countries spied on", "l1_size": 84, "l1_y": 1150,
        "line2": "By the CIA", "l2_size": 90, "l2_y": 1265,
        "category": "50 Year Operation",
    },
    "S01224": {
        "bg": "#4E342E",        # brown
        "accent": "#FFD600",    # yellow
        "stat": "$0.23", "stat_size": 380, "stat_y": 680,
        "line1": "Prisoners work for", "l1_size": 86, "l1_y": 1150,
        "line2": "The US military", "l2_size": 86, "l2_y": 1265,
        "category": "Prison Labor",
    },
    "S01267": {
        "bg": "#0D47A1",        # blue
        "accent": "#FFD600",    # yellow
        "stat": "$7T", "stat_size": 460, "stat_y": 680,
        "line1": "To build AGI —", "l1_size": 88, "l1_y": 1150,
        "line2": "Sam Altman's plan", "l2_size": 80, "l2_y": 1265,
        "category": "AGI Cost",
    },
    "S01268": {
        "bg": "#4A148C",        # purple
        "accent": "#FF3D00",    # red
        "stat": "AI", "stat_size": 520, "stat_y": 680,
        "line1": "Made this film", "l1_size": 92, "l1_y": 1150,
        "line2": "58 cinemas worldwide", "l2_size": 78, "l2_y": 1265,
        "category": "AI Cinema",
    },
    "S00794": {
        "bg": "#006064",        # dark cyan
        "accent": "#FFD600",    # yellow
        "stat": "AGI", "stat_size": 450, "stat_y": 680,
        "line1": "Nobody is in charge", "l1_size": 82, "l1_y": 1150,
        "line2": "Of building it", "l2_size": 84, "l2_y": 1265,
        "category": "AGI Race",
    },
    "S00925": {
        "bg": "#1B5E20",        # green
        "accent": "#FF3D00",    # red
        "stat": "1977", "stat_size": 380, "stat_y": 680,
        "line1": "Exxon knew", "l1_size": 100, "l1_y": 1150,
        "line2": "They hid it", "l2_size": 96, "l2_y": 1265,
        "category": "Internal Documents",
    },
    "S01066": {
        "bg": "#B71C1C",        # red
        "accent": "#FFEB3B",    # yellow
        "stat": "95%", "stat_size": 460, "stat_y": 680,
        "line1": "Drop in murders", "l1_size": 90, "l1_y": 1150,
        "line2": "El Salvador — 2 years", "l2_size": 76, "l2_y": 1265,
        "category": "Crime Collapse",
    },
    "S01080": {
        "bg": "#1A237E",        # indigo
        "accent": "#FF3D00",    # red
        "stat": "3sec", "stat_size": 400, "stat_y": 680,
        "line1": "AI clones your voice", "l1_size": 82, "l1_y": 1150,
        "line2": "Scammers use it now", "l2_size": 78, "l2_y": 1265,
        "category": "Voice Cloning",
    },
    "S01084": {
        "bg": "#E65100",        # orange
        "accent": "#FFFF00",    # yellow
        "stat": "$40", "stat_size": 520, "stat_y": 680,
        "line1": "For one aspirin", "l1_size": 92, "l1_y": 1150,
        "line2": "At a US hospital", "l2_size": 86, "l2_y": 1265,
        "category": "Hospital Billing",
    },
    "S01097": {
        "bg": "#0D47A1",        # blue
        "accent": "#FF3D00",    # red
        "stat": "10yrs", "stat_size": 370, "stat_y": 680,
        "line1": "Until all passwords", "l1_size": 84, "l1_y": 1150,
        "line2": "Can be cracked", "l2_size": 86, "l2_y": 1265,
        "category": "Quantum Threat",
    },
    "S01113": {
        "bg": "#006064",        # teal
        "accent": "#FF3D00",    # red
        "stat": "100K", "stat_size": 400, "stat_y": 680,
        "line1": "People poisoned", "l1_size": 90, "l1_y": 1150,
        "line2": "To save money", "l2_size": 90, "l2_y": 1265,
        "category": "Flint Water Crisis",
    },
    "S01128": {
        "bg": "#B71C1C",        # red
        "accent": "#FFEB3B",    # yellow
        "stat": "1000", "stat_size": 430, "stat_y": 680,
        "line1": "Machines destroyed", "l1_size": 88, "l1_y": 1150,
        "line2": "By one virus", "l2_size": 92, "l2_y": 1265,
        "category": "Stuxnet",
    },
    "S01131": {
        "bg": "#1A237E",        # indigo
        "accent": "#FFD600",    # yellow
        "stat": "1000+", "stat_size": 370, "stat_y": 680,
        "line1": "Fake papers published", "l1_size": 82, "l1_y": 1150,
        "line2": "In real journals", "l2_size": 84, "l2_y": 1265,
        "category": "AI Science Fraud",
    },
    "S01644": {
        "bg": "#4E342E",        # brown
        "accent": "#FFD600",    # gold
        "stat": "$400B", "stat_size": 360, "stat_y": 680,
        "line1": "Richest human ever", "l1_size": 88, "l1_y": 1150,
        "line2": "Crashed the economy", "l2_size": 82, "l2_y": 1265,
        "category": "Mansa Musa",
    },
}


def main():
    print(f"Generating {len(THUMBNAILS)} thumbnails (correct aspect ratios)...\n")
    ok = 0
    for vid_id, cfg in THUMBNAILS.items():
        try:
            make_thumbnail(vid_id, cfg)
            ok += 1
        except Exception as e:
            print(f"  ❌ {vid_id}: {e}")
    print(f"\n✅ {ok}/{len(THUMBNAILS)} done")


if __name__ == "__main__":
    main()
