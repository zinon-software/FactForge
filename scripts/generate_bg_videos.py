"""
generate_bg_videos.py — AI-generated background videos for FactForge
Providers:
  - Kling AI via fal.ai  (primary — batch-friendly, pay-per-second)
  - Runway ML Gen-4      (premium — higher quality for hero shots)

Usage:
    python3 scripts/generate_bg_videos.py S01117          # one video, all scenes
    python3 scripts/generate_bg_videos.py S01117 --scene 0  # specific scene
    python3 scripts/generate_bg_videos.py --all            # all pending videos
    python3 scripts/generate_bg_videos.py --dry-run        # show prompts only

Environment variables (add to config/.env or export):
    FAL_KEY=your_fal_api_key
    RUNWAYML_API_SECRET=your_runway_api_key

Setup:
    1. Get FAL_KEY free at https://fal.ai/dashboard/keys
    2. Get RUNWAYML_API_SECRET free at https://app.runwayml.com/settings
    3. pip install fal-client runwayml
"""

import os, sys, json, time, requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

BASE = Path("/Users/ar/Development/projects/FactForge")
load_dotenv(BASE / "config/.env")

FAL_KEY       = os.environ.get("FAL_KEY", "")
RUNWAY_KEY    = os.environ.get("RUNWAYML_API_SECRET", "")

# ─── Scene duration presets ──────────────────────────────────────────────────
DEFAULT_DURATION = 5   # seconds, safe default for both providers
MAX_DURATION     = 10  # Runway max; Kling supports up to 15

# ─── Provider selector ───────────────────────────────────────────────────────
# "kling"  → fal.ai Kling AI O3 Pro  (best for volume, batch)
# "runway" → Runway ML Gen-4 Turbo   (best for single hero shots)
DEFAULT_PROVIDER = "runway"


# ═══════════════════════════════════════════════════════════════════════════════
# SCENE CONFIGS  (per video ID → list of scene dicts)
# Each scene maps to a remotion segment. Order matches script segments.
# "provider": "kling" | "runway" — override per scene
# ═══════════════════════════════════════════════════════════════════════════════
SCENES = {

    # ── Batch 1 Shorts ────────────────────────────────────────────────────────
    "S01117": [
        {"prompt": "Glowing AI robot typing on a laptop inside the US Capitol building, dramatic blue congressional lighting, cinematic 4K", "duration": 5},
        {"prompt": "Lines of code glowing green on screen being typed at superhuman speed, dark office, cinematic close-up", "duration": 5},
        {"prompt": "Politicians voting in a futuristic senate chamber with holographic displays, dramatic lighting, cinematic", "duration": 5},
        {"prompt": "AI neural network visualization pulsing with blue light, data streams flowing, dark background, cinematic", "duration": 5},
    ],
    "S01279": [
        {"prompt": "DNA double helix slowly rotating in a dark laboratory with blue bioluminescent glow, cinematic 4K", "duration": 5},
        {"prompt": "Scientist hands using CRISPR gene editing equipment in a clean laboratory, dramatic blue light, cinematic", "duration": 5},
        {"prompt": "Baby's hand close-up in soft light, hospital setting, warm emotional cinematic shot", "duration": 5},
        {"prompt": "Microscopic view of DNA being edited with laser precision, dramatic visualization, dark cinematic", "duration": 5},
    ],
    "S01062": [
        {"prompt": "EpiPen auto-injector close-up on a hospital bed with hundred dollar bills scattered around, dramatic red light, cinematic", "duration": 5},
        {"prompt": "Pharmaceutical factory production line with pills being manufactured at high speed, industrial cinematic", "duration": 5},
        {"prompt": "Hospital bill invoice close-up with shocking dollar amount, dramatic harsh fluorescent light, cinematic", "duration": 5},
        {"prompt": "Person collapsing from allergic reaction in a crowded street, dramatic emergency cinematic", "duration": 5},
    ],
    "S01110": [
        {"prompt": "Stunning German university campus Heidelberg at golden hour, students cycling, European architecture, cinematic", "duration": 5},
        {"prompt": "Beautiful medieval German university library interior, students studying, warm amber lighting, cinematic", "duration": 5},
        {"prompt": "International students celebrating graduation outdoors in Germany, joyful, sunny day, cinematic", "duration": 5},
        {"prompt": "American student drowning in debt paperwork contrast with free European university, symbolic split screen, cinematic", "duration": 5},
    ],
    "S01155": [
        {"prompt": "Grand Ethiopian Renaissance Dam aerial view, massive concrete structure, Nile river, dramatic cloudy sky, cinematic drone", "duration": 5},
        {"prompt": "Nile river flowing through Egyptian desert viewed from space, dramatic satellite perspective, cinematic", "duration": 5},
        {"prompt": "Hydroelectric turbines spinning inside a massive dam, dramatic industrial lighting, cinematic", "duration": 5},
        {"prompt": "African farmers celebrating water abundance, lush green fields by the Nile, golden hour, cinematic", "duration": 5},
    ],
    "S01183": [
        {"prompt": "Hepatitis C virus particles under electron microscope, glowing purple and red, medical visualization, cinematic", "duration": 5},
        {"prompt": "Pharmaceutical company boardroom with executives counting money, dramatic corporate power lighting, cinematic", "duration": 5},
        {"prompt": "Patient receiving medication IV drip in hospital, hopeful warm light, cinematic", "duration": 5},
        {"prompt": "Protest signs outside pharmaceutical headquarters demanding affordable medicine, dramatic, cinematic", "duration": 5},
    ],
    "S01185": [
        {"prompt": "Hundreds of surveillance cameras on city streets tracking faces with AI overlay, dystopian dark cinematic", "duration": 5},
        {"prompt": "Face recognition technology scanning crowd at airport, blue digital overlay, dramatic cinematic", "duration": 5},
        {"prompt": "Clearview AI-style database with billions of face photos scrolling, dark dramatic cinematic", "duration": 5},
        {"prompt": "Person realizing their face is in a surveillance database, shocked, dark dramatic, cinematic", "duration": 5},
    ],
    "S01190": [
        {"prompt": "OpenAI headquarters building exterior at night with dramatic blue corporate lighting, cinematic wide shot", "duration": 5},
        {"prompt": "Boardroom power struggle between tech executives and investors, dramatic lighting, cinematic", "duration": 5},
        {"prompt": "Sam Altman style CEO walking confidently through glass office building, dramatic, cinematic (no real faces)", "duration": 5},
        {"prompt": "Wall Street stock exchange floor with AI company logos on screens, dramatic financial chaos, cinematic", "duration": 5},
    ],
    "S01215": [
        {"prompt": "NSA surveillance facility aerial view at night, massive server farms glowing, dark government building, cinematic", "duration": 5},
        {"prompt": "Global map showing surveillance connections between 193 countries, dark dramatic visualization, cinematic", "duration": 5},
        {"prompt": "Government agent monitoring phone calls and emails on screens, dark surveillance room, cinematic", "duration": 5},
        {"prompt": "Person typing private messages on phone unaware of surveillance, dramatic contrast lighting, cinematic", "duration": 5},
    ],
    "S01224": [
        {"prompt": "Prison factory interior with inmates working industrial machinery for pennies, dramatic harsh lighting, cinematic", "duration": 5},
        {"prompt": "Prison cell block aerial view, overcrowded, dramatic dark American correctional facility, cinematic", "duration": 5},
        {"prompt": "Hands assembling products in prison workshop, close-up, dramatic lighting, cinematic", "duration": 5},
        {"prompt": "Corporate logo on products manufactured by prisoners, symbolic shot, dramatic, cinematic", "duration": 5},
    ],
    "S01267": [
        {"prompt": "Massive AI data center server racks glowing blue and green, representing AGI development, futuristic cinematic", "duration": 5},
        {"prompt": "Sam Altman and Demis Hassabis type figures in futuristic lab racing to build AGI (no real faces), cinematic", "duration": 5},
        {"prompt": "AI brain neural network achieving consciousness visualization, dramatic moment, dark cinematic", "duration": 5},
        {"prompt": "World map showing tech companies competing in AGI race, dramatic data visualization, cinematic", "duration": 5},
    ],
    "S01268": [
        {"prompt": "AI robot directing a Hollywood film set with cameras and actors, dramatic studio lights, cinematic behind-the-scenes", "duration": 5},
        {"prompt": "Hollywood Writers Guild strike protest outside studio gates, dramatic, cinematic documentary style", "duration": 5},
        {"prompt": "Film editing suite with AI software automatically cutting scenes, futuristic, dramatic cinematic", "duration": 5},
        {"prompt": "Movie premiere with AI-generated film credit on screen, dramatic red carpet, cinematic", "duration": 5},
    ],

    # ── Batch 2 Shorts ────────────────────────────────────────────────────────
    "S00794": [
        {"prompt": "Google DeepMind vs OpenAI headquarters buildings facing each other at night, dramatic light beams racing skyward, cinematic", "duration": 5},
        {"prompt": "AGI timeline countdown visualization, dramatic futuristic interface, dark cinematic", "duration": 5},
        {"prompt": "Superintelligent AI brain awakening moment, dramatic energy burst, dark cinematic visualization", "duration": 5},
        {"prompt": "Tech billionaires in futuristic boardroom competing for AGI dominance (no real faces), dramatic, cinematic", "duration": 5},
    ],
    "S00925": [
        {"prompt": "Exxon oil refinery at sunset with thick black smoke, dramatic red sky, internal memo documents visible, cinematic", "duration": 5},
        {"prompt": "1977 corporate boardroom scientists presenting climate change data to oil executives, retro dramatic, cinematic", "duration": 5},
        {"prompt": "Oil tanker sailing through melting arctic ice, dramatic climate change contrast, cinematic", "duration": 5},
        {"prompt": "Secret corporate documents stamped CONFIDENTIAL revealing climate suppression, dramatic, cinematic", "duration": 5},
    ],
    "S01066": [
        {"prompt": "El Salvador streets transformation: before (gang graffiti, crime) vs after (clean, peaceful), dramatic contrast, cinematic", "duration": 5},
        {"prompt": "El Salvador mega-prison CECOT exterior aerial view, massive, dramatic security, cinematic", "duration": 5},
        {"prompt": "President Bukele addressing nation with dramatic flag behind him (stylized, no real face), cinematic", "duration": 5},
        {"prompt": "El Salvador families celebrating safety on newly peaceful streets, golden hour, cinematic", "duration": 5},
    ],
    "S01080": [
        {"prompt": "AI microphone capturing voice waveform that transforms into a perfect clone, dark purple neon, futuristic cinematic", "duration": 5},
        {"prompt": "Voice deepfake fraud call visualization: victim's face shocked, scammer's AI voice waveform, dramatic cinematic", "duration": 5},
        {"prompt": "Sound waves transforming into different voices in real-time, dark dramatic AI visualization, cinematic", "duration": 5},
        {"prompt": "Phone call visualization with AI cloning indicator, dramatic dark thriller style, cinematic", "duration": 5},
    ],
    "S01084": [
        {"prompt": "Single aspirin tablet close-up next to a $40 hospital bill, dramatic harsh fluorescent light, cinematic", "duration": 5},
        {"prompt": "Hospital billing department with employees entering charges into computers, dramatic fluorescent lighting, cinematic", "duration": 5},
        {"prompt": "Patient in hospital gown shocked by itemized bill on clipboard, dramatic, cinematic", "duration": 5},
        {"prompt": "US healthcare system corruption symbolic: pharmaceutical executives in luxury office, dramatic, cinematic", "duration": 5},
    ],
    "S01097": [
        {"prompt": "Quantum computer glowing blue in dark laboratory, padlocks shattering in slow motion, encryption breaking, cinematic", "duration": 5},
        {"prompt": "Internet encryption symbols dissolving as quantum computer activates, dramatic dark visualization, cinematic", "duration": 5},
        {"prompt": "Bank vault door being unlocked by quantum algorithm, dramatic high-tech thriller, cinematic", "duration": 5},
        {"prompt": "IBM quantum processor close-up with cryogenic cooling, dramatic blue glow, cinematic 4K", "duration": 5},
    ],
    "S01113": [
        {"prompt": "Rusty corroded water pipes in Flint Michigan with brown toxic water flowing, dramatic dark documentary, cinematic", "duration": 5},
        {"prompt": "Flint Michigan residents lined up for bottled water, dramatic protest, documentary cinematic", "duration": 5},
        {"prompt": "Child drinking contaminated water unaware, dramatic public health crisis, cinematic", "duration": 5},
        {"prompt": "Government officials ignoring Flint water crisis while citizens suffer, symbolic, dramatic cinematic", "duration": 5},
    ],
    "S01128": [
        {"prompt": "Stuxnet virus code glowing green entering nuclear facility network, Iranian centrifuges spinning then exploding, dark cyber thriller cinematic", "duration": 5},
        {"prompt": "Nuclear centrifuges spinning then malfunctioning and destroying themselves, dramatic industrial failure, cinematic", "duration": 5},
        {"prompt": "Hacker in dark room launching cyberweapon on government network, dramatic green code, cinematic", "duration": 5},
        {"prompt": "Iran Natanz nuclear facility exterior at night, mysterious, dramatic, cinematic", "duration": 5},
    ],
    "S01131": [
        {"prompt": "AI bot generating fake scientific papers automatically at superhuman speed, dark dramatic laboratory, cinematic", "duration": 5},
        {"prompt": "Scientific journal editors overwhelmed by flood of AI-generated fake submissions, dramatic, cinematic", "duration": 5},
        {"prompt": "Fabricated research graphs and data being created by AI, red warning overlays, dramatic cinematic", "duration": 5},
        {"prompt": "Science community crisis: peer review system collapsing under AI paper flood, symbolic dramatic cinematic", "duration": 5},
    ],
    "S01644": [
        {"prompt": "Mansa Musa emperor of Mali seated on golden throne surrounded by mountains of gold, African medieval empire, dramatic painting style, cinematic", "duration": 5, "provider": "runway"},
        {"prompt": "Mansa Musa pilgrimage to Mecca: massive gold caravan crossing Sahara desert, thousands of followers, epic cinematic", "duration": 5, "provider": "runway"},
        {"prompt": "Cairo Egyptian market chaos as Mansa Musa distributes gold causing economic collapse, medieval dramatic, cinematic", "duration": 5},
        {"prompt": "Mali Empire gold mines at peak production, medieval African workers, dramatic golden light, cinematic", "duration": 5},
    ],

    # ── Long Videos ───────────────────────────────────────────────────────────
    "L00100": [
        {"prompt": "Elon Musk style billionaire (no real face) standing in front of rockets and Tesla factories, epic golden hour, cinematic", "duration": 10, "provider": "runway"},
        {"prompt": "World wealth distribution visualization: stacks of gold bars with 1% controlling tower, dramatic dark cinematic", "duration": 5},
        {"prompt": "Luxurious mega-yacht sailing through Mediterranean at sunset, billionaire lifestyle, cinematic drone shot", "duration": 5},
        {"prompt": "Stock market charts showing exponential wealth growth, dramatic financial visualization, cinematic", "duration": 5},
        {"prompt": "Bloomberg billionaires index top 10 visualization, dramatic data, cinematic", "duration": 5},
        {"prompt": "Tech company headquarters Silicon Valley aerial view, dramatic golden hour, cinematic", "duration": 5},
    ],
    "L00016": [
        {"prompt": "Dramatic split screen: luxury penthouse above vs poverty slum below, aerial drone view, golden hour, cinematic", "duration": 10, "provider": "runway"},
        {"prompt": "Wealth gap data visualization: 1% owning 45% of world wealth, dark dramatic infographic style, cinematic", "duration": 5},
        {"prompt": "Factory workers vs CEO contrast: assembly line workers vs boardroom meeting, dramatic cinematic", "duration": 5},
        {"prompt": "Thomas Piketty r>g formula visualization: capital return exceeding growth, dramatic academic cinematic", "duration": 5},
        {"prompt": "Nordic countries equal wealth distribution: happy citizens in beautiful Scandinavia, golden cinematic", "duration": 5},
        {"prompt": "Wealth inequality protest: occupy wall street style demonstration, dramatic documentary cinematic", "duration": 5},
        {"prompt": "Future wealth gap solution: UBI universal basic income concept visualization, hopeful cinematic", "duration": 5},
    ],
}


# ─── KLING AI (fal.ai) ──────────────────────────────────────────────────────
def generate_kling(prompt: str, duration: int, output_path: Path) -> bool:
    """Generate video via Kling AI O3 Pro on fal.ai"""
    try:
        import fal_client
        os.environ["FAL_KEY"] = FAL_KEY

        print(f"      ⏳ Kling: {prompt[:60]}...")
        result = fal_client.run(
            "fal-ai/kling-video/o3/pro/text-to-video",
            arguments={
                "prompt": prompt,
                "duration": min(duration, 10),  # O3 max 10s
                "aspect_ratio": "9:16",          # Shorts default; Long uses 16:9
            }
        )
        video_url = result["video"]["url"]
        r = requests.get(video_url, timeout=120)
        output_path.write_bytes(r.content)
        size_kb = output_path.stat().st_size // 1024
        print(f"      ✅ Kling → {output_path.name} ({size_kb}KB)")
        return True
    except Exception as e:
        print(f"      ❌ Kling error: {e}")
        return False


def generate_kling_landscape(prompt: str, duration: int, output_path: Path) -> bool:
    """Generate landscape (16:9) video for Long videos"""
    try:
        import fal_client
        os.environ["FAL_KEY"] = FAL_KEY

        print(f"      ⏳ Kling 16:9: {prompt[:60]}...")
        result = fal_client.run(
            "fal-ai/kling-video/o3/pro/text-to-video",
            arguments={
                "prompt": prompt,
                "duration": min(duration, 10),
                "aspect_ratio": "16:9",
            }
        )
        video_url = result["video"]["url"]
        r = requests.get(video_url, timeout=120)
        output_path.write_bytes(r.content)
        size_kb = output_path.stat().st_size // 1024
        print(f"      ✅ Kling → {output_path.name} ({size_kb}KB)")
        return True
    except Exception as e:
        print(f"      ❌ Kling error: {e}")
        return False


# ─── RUNWAY ML ──────────────────────────────────────────────────────────────
def generate_runway(prompt: str, duration: int, output_path: Path, is_short: bool = True) -> bool:
    """Generate video via Runway ML Gen-4.5 (text-to-video)"""
    try:
        from runwayml import RunwayML
        client = RunwayML(api_key=RUNWAY_KEY)

        ratio = "720:1280" if is_short else "1280:720"
        # Runway supports durations: 4, 6, 8 seconds
        run_duration = 8 if duration >= 8 else (6 if duration >= 6 else 4)

        print(f"      ⏳ Runway gen4.5 ({run_duration}s, {ratio}): {prompt[:55]}...")

        task = client.text_to_video.create(
            model="gen4.5",
            prompt_text=prompt,
            ratio=ratio,
            duration=run_duration,
        )

        task_id = task.id
        print(f"         task_id: {task_id}")

        # Poll until complete (typically 60-120s)
        for attempt in range(30):
            time.sleep(8)
            task = client.tasks.retrieve(task_id)
            status = task.status
            print(f"         [{attempt+1}] {status}", end="\r")
            if status == "SUCCEEDED":
                break
            if status == "FAILED":
                print(f"\n      ❌ Runway task failed: {getattr(task, 'failure_reason', 'unknown')}")
                return False

        if task.status == "SUCCEEDED" and task.output:
            video_url = task.output[0]
            r = requests.get(video_url, timeout=120)
            output_path.write_bytes(r.content)
            size_kb = output_path.stat().st_size // 1024
            print(f"\n      ✅ Runway → {output_path.name} ({size_kb}KB)")
            return True
        else:
            print(f"\n      ❌ Runway: no output (status={task.status})")
            return False
    except Exception as e:
        print(f"      ❌ Runway error: {e}")
        return False


# ─── MAIN GENERATOR ─────────────────────────────────────────────────────────
def generate_scenes_for_video(vid_id: str, scene_idx: int = None, dry_run: bool = False):
    """Generate all (or one) background video scene(s) for a video."""
    scenes = SCENES.get(vid_id)
    if not scenes:
        print(f"  ❌ No scene config for {vid_id}")
        return

    is_short = vid_id.startswith("S")
    out_dir = BASE / "output" / vid_id / "bg_videos_ai"
    out_dir.mkdir(parents=True, exist_ok=True)

    targets = [(i, s) for i, s in enumerate(scenes)]
    if scene_idx is not None:
        targets = [(scene_idx, scenes[scene_idx])]

    print(f"\n🎬 {vid_id} — {len(targets)} scene(s) to generate")

    for i, scene in targets:
        fname = f"scene_{i:02d}.mp4"
        out_path = out_dir / fname

        if out_path.exists() and out_path.stat().st_size > 50_000:
            print(f"   [{i}] ⏭️  {fname} already exists ({out_path.stat().st_size//1024}KB), skipping")
            continue

        prompt   = scene["prompt"]
        duration = scene.get("duration", DEFAULT_DURATION)
        provider = scene.get("provider", DEFAULT_PROVIDER)

        print(f"   [{i}] {provider.upper()} — {fname}")
        print(f"        prompt: {prompt[:80]}")

        if dry_run:
            continue

        if not FAL_KEY and provider == "kling":
            print("      ⚠️  FAL_KEY not set — add to config/.env")
            continue
        if not RUNWAY_KEY and provider == "runway":
            print("      ⚠️  RUNWAYML_API_SECRET not set — add to config/.env")
            continue

        success = False
        if provider == "runway":
            success = generate_runway(prompt, duration, out_path, is_short)
        elif provider == "kling":
            if is_short:
                success = generate_kling(prompt, duration, out_path)
            else:
                success = generate_kling_landscape(prompt, duration, out_path)

        # Fallback: try other provider
        if not success and provider == "runway" and FAL_KEY:
            print(f"      🔄 Fallback to Kling...")
            success = generate_kling(prompt, duration, out_path) if is_short \
                      else generate_kling_landscape(prompt, duration, out_path)
        elif not success and provider == "kling" and RUNWAY_KEY:
            print(f"      🔄 Fallback to Runway...")
            success = generate_runway(prompt, duration, out_path, is_short)

        time.sleep(2)  # polite delay

    # Update remotion_props.json to use AI videos
    if not dry_run:
        update_remotion_props(vid_id, out_dir, is_short)


def update_remotion_props(vid_id: str, ai_bg_dir: Path, is_short: bool):
    """Update remotion_props.json to use AI-generated background videos."""
    props_path = BASE / "output" / vid_id / "remotion_props.json"
    if not props_path.exists():
        return

    with open(props_path) as f:
        props = json.load(f)

    ai_files = sorted(ai_bg_dir.glob("scene_*.mp4"))
    if not ai_files:
        return

    segments = props.get("segments", [])
    for i, seg in enumerate(segments):
        if i < len(ai_files):
            rel_path = str(ai_files[i]).replace(str(BASE) + "/", "")
            seg["backgroundVideo"] = rel_path

    with open(props_path, "w") as f:
        json.dump(props, f, indent=2, ensure_ascii=False)

    print(f"   ✅ Updated remotion_props.json with {len(ai_files)} AI backgrounds")


def check_setup():
    """Check API keys and packages."""
    print("\n🔑 API Keys Status:")
    print(f"   FAL_KEY (Kling):    {'✅ set' if FAL_KEY else '❌ not set — add to config/.env'}")
    print(f"   RUNWAY_KEY:         {'✅ set' if RUNWAY_KEY else '❌ not set — add to config/.env'}")
    try:
        import fal_client
        print("   fal-client:         ✅ installed")
    except ImportError:
        print("   fal-client:         ❌ run: pip3 install fal-client")
    try:
        import runwayml
        print("   runwayml:           ✅ installed")
    except ImportError:
        print("   runwayml:           ❌ run: pip3 install runwayml")

    print("\n📦 Available configs:", ", ".join(SCENES.keys()))


def main():
    args = sys.argv[1:]

    if not args or "--setup" in args:
        check_setup()
        if not args:
            print("\nUsage:")
            print("  python3 scripts/generate_bg_videos.py S01117")
            print("  python3 scripts/generate_bg_videos.py S01117 --scene 0")
            print("  python3 scripts/generate_bg_videos.py --all")
            print("  python3 scripts/generate_bg_videos.py --dry-run S01117")
        return

    dry_run    = "--dry-run" in args
    scene_idx  = None
    if "--scene" in args:
        idx = args.index("--scene")
        scene_idx = int(args[idx + 1])

    if "--all" in args:
        # Load pending_uploads to get all video IDs
        pending_path = BASE / "state/pending_uploads.json"
        with open(pending_path) as f:
            data = json.load(f)
        ids = [e["id"] for e in data["pending"] if e["id"] in SCENES]
        print(f"🚀 Generating AI backgrounds for {len(ids)} videos...")
        for vid_id in ids:
            generate_scenes_for_video(vid_id, dry_run=dry_run)
    else:
        # Single video
        vid_id = next((a for a in args if not a.startswith("--") and a != str(scene_idx)), None)
        if vid_id:
            generate_scenes_for_video(vid_id, scene_idx=scene_idx, dry_run=dry_run)
        else:
            print("❌ Provide a video ID. Example: python3 scripts/generate_bg_videos.py S01117")


if __name__ == "__main__":
    main()
