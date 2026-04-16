#!/usr/bin/env python3
"""Download AI images for documentary chapters from Pollinations.ai"""
import json, time, sys, urllib.request, urllib.parse, random
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE = Path(__file__).parent.parent

def download_image(prompt: str, out_path: Path, width=1920, height=1080, seed=None):
    if out_path.exists():
        logger.info(f"  ✓ already exists: {out_path.name}")
        return True
    if seed is None:
        seed = random.randint(1000, 9999)
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true&model=flux&seed={seed}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            if len(data) < 5000:
                logger.warning(f"  ⚠ Small image ({len(data)} bytes), retrying...")
                time.sleep(15)
                continue
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(data)
            logger.info(f"  ✅ {out_path.name} ({len(data)//1024}KB)")
            return True
        except Exception as e:
            logger.warning(f"  Attempt {attempt+1} failed: {e}")
            time.sleep(20)
    return False

def generate_images(video_id: str):
    output_dir = BASE / "output" / video_id
    images_dir = output_dir / "images"
    images_dir.mkdir(exist_ok=True)

    script_path = output_dir / "script.json"
    with open(script_path) as f:
        script = json.load(f)

    chapters = script.get("chapters", [])
    total = len(chapters) * 2
    done = 0

    for ch in chapters:
        ch_id = ch["id"]
        prompt_a = ch.get("image_prompt_A", "cinematic documentary scene high quality")
        prompt_b = ch.get("image_prompt_B", "cinematic wide shot dramatic lighting")

        # Image A
        path_a = images_dir / f"{ch_id}_A.jpg"
        if download_image(prompt_a + " photorealistic cinematic 4K ultra detailed", path_a, seed=hash(ch_id) % 9999):
            done += 1
        time.sleep(12)

        # Image B
        path_b = images_dir / f"{ch_id}_B.jpg"
        if download_image(prompt_b + " photorealistic cinematic 4K dramatic lighting", path_b, seed=(hash(ch_id)+100) % 9999):
            done += 1
        time.sleep(12)

        logger.info(f"Chapter '{ch_id}' done ({done}/{total})")

    # Copy all images to Remotion public
    public_images = BASE / "video/remotion-project/public" / video_id / "images"
    public_images.mkdir(parents=True, exist_ok=True)
    for img in images_dir.glob("*.jpg"):
        import shutil
        shutil.copy(img, public_images / img.name)

    logger.info(f"\n✅ {done}/{total} images ready in output/{video_id}/images/")
    logger.info(f"✅ Copied to public/{video_id}/images/")
    return done, total

if __name__ == "__main__":
    vid = sys.argv[1] if len(sys.argv) > 1 else "L00300"
    done, total = generate_images(vid)
    print(f"\n✅ Images: {done}/{total}")
