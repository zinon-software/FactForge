"""
finalize_and_upload.py
Merges audio + SFX into rendered video, then uploads to YouTube.
Called automatically after render completes.
"""
import json, os, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).parent.parent

def merge_audio(video_id: str, fps: int = 60) -> str:
    """Merge voice audio + ambient music + SFX into final video."""
    out_dir = ROOT / "output" / video_id
    noaudio = out_dir / "video_noaudio.mp4"
    audio   = out_dir / "audio.mp3"
    music   = ROOT / "assets/music/dark_ambient_55s.mp3"
    output  = out_dir / "video.mp4"

    if not noaudio.exists():
        print(f"❌ {noaudio} not found"); return None
    if not audio.exists():
        print(f"❌ {audio} not found"); return None

    # Get durations
    def get_dur(path):
        r = subprocess.run(["ffprobe","-v","quiet","-show_entries","format=duration",
                            "-of","default=noprint_wrappers=1", str(path)],
                           capture_output=True, text=True)
        return float(r.stdout.strip().split("=")[-1])

    video_dur = get_dur(noaudio)
    print(f"Video: {video_dur:.1f}s  Audio: {get_dur(audio):.1f}s")

    if music.exists():
        cmd = [
            "ffmpeg", "-y",
            "-i", str(noaudio),
            "-i", str(audio),
            "-i", str(music),
            "-filter_complex",
            "[1:a]volume=1.0[voice];"
            "[2:a]volume=0.10,aloop=loop=-1:size=2e+09[music];"
            "[voice][music]amix=inputs=2:normalize=0[audio_out]",
            "-map", "0:v", "-map", "[audio_out]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest", str(output)
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-i", str(noaudio), "-i", str(audio),
            "-map", "0:v", "-map", "1:a",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest", str(output)
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ ffmpeg error:\n{result.stderr[-500:]}")
        return None
    print(f"✅ Merged: {output} ({os.path.getsize(output)//1024//1024}MB)")
    return str(output)


def upload_youtube(video_id: str):
    """Upload video to YouTube and return video ID."""
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from google.oauth2.credentials import Credentials
    except ImportError:
        print("❌ google-api-python-client not installed"); return None

    out_dir = ROOT / "output" / video_id
    video_file = out_dir / "video.mp4"
    meta_file  = out_dir / "metadata.json"

    if not video_file.exists():
        print(f"❌ {video_file} not found"); return None

    with open(ROOT / "config/youtube_token.json") as f:
        tok = json.load(f)

    creds = Credentials(
        token=tok["token"], refresh_token=tok["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=tok["client_id"], client_secret=tok["client_secret"],
        scopes=tok["scopes"]
    )

    youtube = build("youtube", "v3", credentials=creds)

    with open(meta_file) as f:
        meta = json.load(f)

    body = {
        "snippet": {
            "title": meta["title"],
            "description": meta["description"],
            "tags": meta.get("tags", []),
            "categoryId": meta.get("categoryId", "28"),
            "defaultLanguage": "en",
        },
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
    }

    media = MediaFileUpload(str(video_file), chunksize=1024*1024, resumable=True, mimetype="video/mp4")
    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = req.next_chunk()
        if status:
            print(f"Uploading {video_id}: {int(status.progress()*100)}%")

    yt_id = response["id"]
    print(f"✅ Uploaded {video_id} → https://youtu.be/{yt_id}")

    # Save youtube_id
    meta["youtube_video_id"] = yt_id
    meta["youtube_url"] = f"https://youtu.be/{yt_id}"
    with open(meta_file, "w") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    return yt_id


def upload_subtitles(video_id: str, yt_video_id: str):
    """Upload SRT subtitles for 7 languages."""
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google.oauth2.credentials import Credentials

    srt_dir = ROOT / "output" / video_id / "subtitles"
    if not srt_dir.exists():
        print(f"⚠️ No subtitles dir for {video_id}"); return

    with open(ROOT / "config/youtube_token.json") as f:
        tok = json.load(f)
    creds = Credentials(
        token=tok["token"], refresh_token=tok["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=tok["client_id"], client_secret=tok["client_secret"],
        scopes=tok["scopes"]
    )
    youtube = build("youtube", "v3", credentials=creds)

    lang_map = {"en":"English","ar":"Arabic","es":"Spanish","fr":"French",
                "hi":"Hindi","pt":"Portuguese","tr":"Turkish"}

    for srt_file in srt_dir.glob("*.srt"):
        lang = srt_file.stem.split("_")[-1]
        if lang not in lang_map: continue
        try:
            body = {"snippet": {"videoId": yt_video_id, "language": lang,
                                "name": lang_map[lang], "isDraft": False}}
            media = MediaFileUpload(str(srt_file), mimetype="application/octet-stream")
            youtube.captions().insert(part="snippet", body=body, media_body=media).execute()
            print(f"  ✅ Subtitles {lang}")
            time.sleep(1)
        except Exception as e:
            print(f"  ⚠️ Subtitles {lang}: {e}")


def update_state(video_id: str, yt_id: str, is_long: bool = False):
    """Update progress.json and published_videos.json."""
    import datetime

    # published_videos.json
    pub_file = ROOT / "state/published_videos.json"
    with open(pub_file) as f: pub = json.load(f)

    with open(ROOT / f"output/{video_id}/metadata.json") as f:
        meta = json.load(f)

    pub["videos"].append({
        "id": video_id,
        "title": meta["title"],
        "youtube_id": yt_id,
        "youtube_url": f"https://youtu.be/{yt_id}",
        "published_at": datetime.date.today().isoformat(),
        "cleaned": False
    })
    with open(pub_file, "w") as f:
        json.dump(pub, f, indent=2, ensure_ascii=False)
    print(f"✅ State updated for {video_id}")


if __name__ == "__main__":
    video_id = sys.argv[1] if len(sys.argv) > 1 else "L00100"
    is_long = video_id.startswith("L")

    print(f"\n{'='*50}")
    print(f"Finalizing {video_id}")
    print(f"{'='*50}\n")

    fps = 30 if is_long else 60
    video_path = merge_audio(video_id, fps)
    if not video_path:
        print("❌ Merge failed"); sys.exit(1)

    yt_id = upload_youtube(video_id)
    if not yt_id:
        print("❌ Upload failed"); sys.exit(1)

    upload_subtitles(video_id, yt_id)
    update_state(video_id, yt_id, is_long)

    print(f"\n✅ {video_id} complete → https://youtu.be/{yt_id}")
