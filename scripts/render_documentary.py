"""
render_documentary.py — Render a DocumentaryVideo composition with high quality (no pixelation)
Usage: python3 scripts/render_documentary.py L00200
"""
import json, subprocess, sys, math
from pathlib import Path

ROOT = Path(__file__).parent.parent
REMOTION_DIR = ROOT / "video/remotion-project"

def render(video_id: str):
    out_dir = ROOT / "output" / video_id
    props_file = out_dir / "remotion_props.json"

    if not props_file.exists():
        print(f"❌ No remotion_props.json found for {video_id}")
        sys.exit(1)

    with open(props_file) as f:
        props = json.load(f)

    total_frames = props.get("totalDurationFrames", 18603)
    print(f"Rendering {video_id}: {total_frames} frames @ 30fps ({total_frames/30:.1f}s)")

    noaudio_path = out_dir / "video_noaudio.mp4"
    final_path   = out_dir / "video.mp4"
    audio_path   = out_dir / "audio.mp3"

    # Step 1: Remotion render (no audio, high quality)
    print("\n[1/2] Remotion render...")
    render_cmd = [
        "npx", "remotion", "render",
        "DocumentaryVideo",
        str(noaudio_path),
        f"--props={props_file}",
        f"--frames=0-{total_frames - 1}",
        "--codec=h264",
        "--crf=18",               # HIGH QUALITY — no pixelation
        "--pixel-format=yuv420p",
        "--concurrency=4",
        "--log=verbose",
    ]

    result = subprocess.run(render_cmd, cwd=REMOTION_DIR, capture_output=False, timeout=3600)
    if result.returncode != 0:
        print("❌ Remotion render failed")
        sys.exit(1)

    print("\n[2/2] FFmpeg audio merge + cinematic color grade...")
    # Cinematic color grading filter chain:
    #   eq: slight contrast boost + brightness lift
    #   curves: cinematic S-curve
    #   colorbalance: warm shadows, cool highlights (cinematic look)
    #   unsharp: subtle sharpening for clarity
    color_grade = (
        "eq=contrast=1.06:brightness=0.015:saturation=1.12,"
        "curves=r='0/0 0.2/0.18 0.8/0.82 1/1':g='0/0 0.2/0.19 0.8/0.81 1/1':b='0/0 0.2/0.20 0.8/0.80 1/0.97',"
        "colorbalance=rs=-0.03:gs=-0.01:bs=0.04:rm=0.01:gm=0:bm=-0.02:rh=-0.01:gh=0:bh=0.02,"
        "unsharp=lx=3:ly=3:la=0.4"
    )
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", str(noaudio_path),
        "-i", str(audio_path),
        "-vf", color_grade,
        "-c:v", "libx264",
        "-crf", "18",                    # HIGH QUALITY
        "-preset", "slow",               # better compression at same quality
        "-profile:v", "high",
        "-level", "4.2",
        "-pix_fmt", "yuv420p",
        "-b:v", "0",                     # CRF mode (VBR)
        "-maxrate", "20M",               # cap for streaming
        "-bufsize", "40M",
        "-c:a", "aac",
        "-b:a", "256k",
        "-shortest",
        str(final_path),
    ]

    result = subprocess.run(ffmpeg_cmd, capture_output=False, timeout=1800)
    if result.returncode != 0:
        print("❌ FFmpeg failed")
        sys.exit(1)

    # Verify output
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(final_path)],
        capture_output=True, text=True
    )
    info = json.loads(r.stdout)
    dur = float(info["format"]["duration"])
    size_mb = int(info["format"]["size"]) // (1024 * 1024)
    vstream = next(s for s in info["streams"] if s["codec_type"] == "video")
    print(f"\n✅ {final_path.name}")
    print(f"   Duration: {dur:.1f}s ({dur/60:.1f} min)")
    print(f"   Size: {size_mb} MB")
    print(f"   Resolution: {vstream['width']}×{vstream['height']}")
    print(f"   Codec: {vstream['codec_name']}, Profile: {vstream.get('profile','?')}")
    print(f"   Bitrate: {int(info['format']['bit_rate'])//1000} kbps")

if __name__ == "__main__":
    vid = sys.argv[1] if len(sys.argv) > 1 else "L00200"
    render(vid)
