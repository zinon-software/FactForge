#!/usr/bin/env python3
"""Download bg videos for S01700 from Pexels with Coverr/Pixabay fallback."""
import json, os, sys, time, urllib.request, urllib.parse, shutil
from pathlib import Path
import logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE = Path(__file__).parent.parent
dotenv = BASE / "config/.env"
env = {}
for line in dotenv.read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()

PEXELS_KEY  = env.get("PEXELS_API_KEY", "")
PIXABAY_KEY = env.get("PIXABAY_API_KEY", "")

def pexels_search(query, orientation="portrait"):
    url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}&per_page=5&orientation={orientation}&size=medium"
    req = urllib.request.Request(url, headers={"Authorization": PEXELS_KEY})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.load(r)
        for v in data.get("videos", []):
            for f in v.get("video_files", []):
                if f.get("quality") in ("hd", "sd") and f.get("width", 0) <= 1080:
                    return f["link"]
    except Exception as e:
        logger.warning(f"Pexels failed for '{query}': {e}")
    return None

def pixabay_search(query):
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_KEY}&q={urllib.parse.quote(query)}&per_page=5&video_type=film"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            data = json.load(r)
        for hit in data.get("hits", []):
            vids = hit.get("videos", {})
            for q in ("medium", "small", "large"):
                u = vids.get(q, {}).get("url")
                if u:
                    return u
    except Exception as e:
        logger.warning(f"Pixabay failed for '{query}': {e}")
    return None

def download(url, out_path):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    out_path.write_bytes(data)
    return len(data)

def main():
    with open(BASE / "output/S01700/remotion_props.json") as f:
        props = json.load(f)

    out_dir = BASE / "output/S01700/bg_videos"
    out_dir.mkdir(exist_ok=True)
    pub_dir = BASE / "video/remotion-project/public/S01700/bg_videos"
    pub_dir.mkdir(parents=True, exist_ok=True)

    used_urls = set()
    segments = props["segments"]

    for i, seg in enumerate(segments):
        fname = f"seg_{i:02d}.mp4"
        out_path = out_dir / fname
        if out_path.exists():
            logger.info(f"  ✓ {fname} exists")
            shutil.copy(out_path, pub_dir / fname)
            continue

        query = seg["scene_query"]
        logger.info(f"[{i:02d}] {query[:50]}")

        # Try Pexels first
        url = pexels_search(query)
        if not url or url in used_urls:
            url = pexels_search(" ".join(query.split()[:3]), "landscape")
        if not url or url in used_urls:
            url = pixabay_search(query)
        if not url or url in used_urls:
            url = pixabay_search(" ".join(query.split()[:3]))

        if url and url not in used_urls:
            try:
                size = download(url, out_path)
                used_urls.add(url)
                shutil.copy(out_path, pub_dir / fname)
                logger.info(f"  ✅ {fname} ({size//1024}KB)")
            except Exception as e:
                logger.error(f"  ❌ Download failed: {e}")
        else:
            logger.warning(f"  ⚠ No video found for seg {i:02d}")

        time.sleep(0.5)

    total = len(list(out_dir.glob("*.mp4")))
    logger.info(f"\n✅ {total}/{len(segments)} videos ready")

if __name__ == "__main__":
    main()
