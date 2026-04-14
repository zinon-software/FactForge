"""
FactForge Asset Manager
-----------------------
- Search local library first
- Fall back to Pexels API if no good match
- Save new assets to library automatically
- All assets must be royalty-free / commercial-use licensed

Usage:
  python3 asset_manager.py search "hospital medical"
  python3 asset_manager.py download "hospital medical" scene_hospital
  python3 asset_manager.py list
"""

import json, os, sys, requests, shutil
from pathlib import Path

BASE = Path(__file__).parent.parent
LIBRARY_FILE = BASE / "assets" / "library.json"
REMOTION_PUBLIC = BASE / "video" / "remotion-project" / "public"
BG_VIDEOS_DIR = REMOTION_PUBLIC / "bg_videos"
PEXELS_KEY = os.environ.get("PEXELS_API_KEY", "")


def load_library():
    with open(LIBRARY_FILE) as f:
        return json.load(f)

def save_library(lib):
    lib["last_updated"] = "2026-04-13"
    with open(LIBRARY_FILE, "w") as f:
        json.dump(lib, f, indent=2, ensure_ascii=False)


def search_local(query: str, asset_type: str = "videos") -> list:
    """Search local library by tags. Returns ranked matches."""
    lib = load_library()
    terms = query.lower().split()
    results = []
    for asset in lib[asset_type]:
        score = sum(1 for t in terms if any(t in tag for tag in asset["tags"]))
        if score > 0:
            results.append((score, asset))
    results.sort(reverse=True, key=lambda x: x[0])
    return [r[1] for r in results]


def search_pexels_videos(query: str, per_page: int = 5, is_short: bool = True) -> list:
    """Search Pexels for royalty-free commercial videos.
    is_short=True → portrait (1080×1920), is_short=False → landscape (1920×1080)
    Falls back to no orientation filter if portrait returns 0 results.
    """
    if not PEXELS_KEY:
        print("ERROR: PEXELS_API_KEY not set")
        return []
    url = "https://api.pexels.com/videos/search"
    headers = {"Authorization": PEXELS_KEY}
    orientation = "portrait" if is_short else "landscape"
    params = {"query": query, "per_page": per_page, "size": "medium", "orientation": orientation}
    r = requests.get(url, headers=headers, params=params, timeout=15)
    if r.status_code != 200:
        print(f"Pexels error: {r.status_code}")
        return []
    videos = r.json().get("videos", [])
    # Fallback: retry without orientation filter if no results
    if not videos:
        params.pop("orientation")
        r2 = requests.get(url, headers=headers, params=params, timeout=15)
        if r2.status_code == 200:
            videos = r2.json().get("videos", [])
    return videos


def download_pexels_video(pexels_video: dict, scene_id: str) -> str:
    """Download best quality video file from Pexels result."""
    # Pick HD file preferring 1080p portrait
    files = pexels_video.get("video_files", [])
    files_sorted = sorted(files, key=lambda f: f.get("height", 0), reverse=True)
    best = next((f for f in files_sorted if f.get("height", 0) >= 720), files_sorted[0] if files_sorted else None)
    if not best:
        print("No video file found")
        return ""
    url = best["link"]
    out_path = BG_VIDEOS_DIR / f"{scene_id}.mp4"
    print(f"Downloading {url[:60]}... -> {out_path.name}")
    r = requests.get(url, stream=True, timeout=60)
    with open(out_path, "wb") as f:
        shutil.copyfileobj(r.raw, f)
    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f"Downloaded: {size_mb:.1f} MB")
    return f"bg_videos/{scene_id}.mp4"


def add_to_library(scene_id: str, file_path: str, tags: list, source: str = "pexels",
                   license: str = "pexels_free_commercial", size_mb: float = 0):
    """Register a new video asset in library.json."""
    lib = load_library()
    # Remove existing entry with same id
    lib["videos"] = [v for v in lib["videos"] if v["id"] != scene_id]
    lib["videos"].append({
        "id": scene_id,
        "file": file_path,
        "path_remotion": file_path,
        "tags": tags,
        "mood": "neutral",
        "source": source,
        "license": license,
        "size_mb": round(size_mb, 1),
        "quality": "good"
    })
    # Remove from missing_needed if present
    lib["missing_needed"] = [m for m in lib.get("missing_needed", [])
                              if scene_id not in m]
    save_library(lib)
    print(f"Added {scene_id} to library")


def find_best_video(query: str, scene_id: str = None, auto_download: bool = True) -> str:
    """
    Main function: find best video for a scene.
    1. Search local library
    2. If no match, search Pexels and download
    Returns path_remotion string.
    """
    # 1. Local search
    matches = search_local(query, "videos")
    if matches:
        best = matches[0]
        print(f"[LOCAL] Best match for '{query}': {best['id']} (tags: {best['tags'][:3]})")
        return best["path_remotion"]

    # 2. Pexels fallback
    if not auto_download or not PEXELS_KEY:
        print(f"[MISSING] No local match for '{query}' — add manually or set PEXELS_API_KEY")
        return "bg_videos/scene_cyber.mp4"  # fallback

    print(f"[PEXELS] No local match for '{query}', searching Pexels...")
    videos = search_pexels_videos(query)
    if not videos:
        return "bg_videos/scene_cyber.mp4"

    # Show options
    for i, v in enumerate(videos[:3]):
        print(f"  [{i}] id={v['id']} — {v.get('url','')}")

    chosen = videos[0]
    sid = scene_id or f"scene_{query.split()[0].lower()}"
    path = download_pexels_video(chosen, sid)
    if path:
        tags = query.lower().split() + [query.lower()]
        size = (BG_VIDEOS_DIR / f"{sid}.mp4").stat().st_size / 1024 / 1024
        add_to_library(sid, path, tags, size_mb=size)
    return path or "bg_videos/scene_cyber.mp4"


def cmd_search(query):
    print(f"\n=== Local matches for: '{query}' ===")
    matches = search_local(query, "videos")
    if not matches:
        print("No local matches found")
    for m in matches[:5]:
        print(f"  {m['id']:25s} tags: {', '.join(m['tags'][:5])}")

def cmd_list():
    lib = load_library()
    print(f"\n=== Video Library ({len(lib['videos'])} files) ===")
    for v in lib["videos"]:
        print(f"  {v['id']:25s} {v['size_mb']:5.1f}MB  {', '.join(v['tags'][:4])}")
    print(f"\n=== Images ({len(lib['images'])} files) ===")
    for img in lib["images"]:
        print(f"  {img['id']:25s} {img.get('person', '')}")
    print(f"\n=== Missing / Needed ===")
    for m in lib.get("missing_needed", []):
        print(f"  - {m}")

def cmd_download(query, scene_id):
    path = find_best_video(query, scene_id, auto_download=True)
    print(f"Result: {path}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        cmd_list()
    elif args[0] == "search" and len(args) >= 2:
        cmd_search(" ".join(args[1:]))
    elif args[0] == "list":
        cmd_list()
    elif args[0] == "download" and len(args) >= 3:
        cmd_download(args[1], args[2])
    elif args[0] == "download" and len(args) == 2:
        cmd_download(args[1], None)
    else:
        print(__doc__)
