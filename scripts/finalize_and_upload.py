"""
finalize_and_upload.py — Merge audio into rendered video, then upload to YouTube.
Uses utils/youtube_helper.py for all YouTube API calls.

Usage: python3 scripts/finalize_and_upload.py <video_id>
"""
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from utils.youtube_helper import (
    upload_video, set_thumbnail, upload_caption,
    get_next_publish_date, update_state_after_upload
)


def merge_audio(video_id: str) -> Path | None:
    """Merge voice audio into rendered video using FFmpeg (CRF 18, high quality)."""
    out_dir = ROOT / "output" / video_id
    noaudio = out_dir / "video_noaudio.mp4"
    audio   = out_dir / "audio.mp3"
    output  = out_dir / "video.mp4"

    if not noaudio.exists():
        print(f"❌ {noaudio} not found"); return None
    if not audio.exists():
        print(f"❌ {audio} not found"); return None

    cmd = [
        "ffmpeg", "-y",
        "-i", str(noaudio),
        "-i", str(audio),
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "slow",
        "-pix_fmt", "yuv420p",
        "-maxrate", "20M",
        "-bufsize", "40M",
        "-c:a", "aac",
        "-b:a", "256k",
        "-shortest",
        str(output),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ ffmpeg error:\n{result.stderr[-500:]}")
        return None
    size_mb = output.stat().st_size // 1024 // 1024
    print(f"✅ Merged: {output.name} ({size_mb}MB)")
    return output


def upload(video_id: str) -> str | None:
    """Full upload pipeline: merge → YouTube upload → thumbnail → subtitles → state."""
    out_dir  = ROOT / "output" / video_id
    meta_file = out_dir / "metadata.json"
    is_long  = video_id.startswith("L")

    if not meta_file.exists():
        print(f"❌ metadata.json not found for {video_id}"); return None

    meta = json.loads(meta_file.read_text())
    title = meta.get("selected_title") or meta.get("title_selected") or meta.get("title", "")
    desc  = meta.get("description", "")
    tags  = meta.get("tags", [])
    cat   = meta.get("category_id", "27")

    # Determine scheduled publish date
    publish_at = get_next_publish_date("long" if is_long else "short")
    print(f"Scheduled publish: {publish_at}")

    # Upload video
    video_path = out_dir / "video.mp4"
    if not video_path.exists():
        print(f"❌ video.mp4 not found — run render first"); return None

    yt_id = upload_video(
        video_path=video_path,
        title=title,
        description=desc,
        tags=tags,
        category_id=cat,
        publish_at=publish_at,
        privacy="private",
    )
    if not yt_id:
        print("❌ Upload failed"); return None

    # Thumbnail
    thumb = out_dir / "thumbnail.jpg"
    if thumb.exists():
        ok = set_thumbnail(yt_id, thumb)
        if not ok:
            print("⚠️  Thumbnail API blocked (expected for Shorts — set manually in Studio)")
    else:
        print("⚠️  No thumbnail.jpg found")

    # Subtitles (7 languages if available)
    srt_dir = out_dir / "subtitles"
    if srt_dir.exists():
        lang_names = {"en":"English","ar":"Arabic","es":"Spanish","fr":"French",
                      "hi":"Hindi","pt":"Portuguese","tr":"Turkish"}
        for srt_file in sorted(srt_dir.glob("*.srt")):
            lang = srt_file.stem.split("_")[-1]
            if lang in lang_names:
                ok = upload_caption(yt_id, srt_file, lang, lang_names[lang])
                print(f"  {'✅' if ok else '⚠️ '} Subtitles {lang}")

    # Update state
    video_type = "long" if is_long else "short"
    update_state_after_upload(video_id, yt_id, publish_at, title, video_type)

    print(f"\n✅ {video_id} → https://youtu.be/{yt_id}  (publishes {publish_at})")
    return yt_id


if __name__ == "__main__":
    video_id = sys.argv[1] if len(sys.argv) > 1 else None
    if not video_id:
        print("Usage: python3 scripts/finalize_and_upload.py <video_id>")
        sys.exit(1)

    is_long = video_id.startswith("L")

    print(f"\n{'='*50}")
    print(f"Finalizing {video_id}")
    print(f"{'='*50}\n")

    # Merge only if video_noaudio exists (render was done separately)
    out_dir = ROOT / "output" / video_id
    if (out_dir / "video_noaudio.mp4").exists() and not (out_dir / "video.mp4").exists():
        print("[1/2] Merging audio...")
        if not merge_audio(video_id):
            sys.exit(1)

    print("[2/2] Uploading to YouTube...")
    yt_id = upload(video_id)
    if not yt_id:
        sys.exit(1)
