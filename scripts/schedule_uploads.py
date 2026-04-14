"""
schedule_uploads.py — Build upload schedule and upload today's batch as "scheduled" on YouTube
Usage:
    python3 scripts/schedule_uploads.py           # upload today's 3 videos
    python3 scripts/schedule_uploads.py --plan     # just show the full plan, no upload
"""
import json
import sys
import time
import os
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
SCHEDULE_FILE = ROOT / "state/upload_schedule.json"

# ─── Optimal publish times (UTC) ────────────────────────────────────────────
# Targets global English audience — peaks at 12pm EST, 6pm EST, 9pm EST
# = 17:00, 23:00, 02:00 UTC (next day)
DAILY_SLOTS_UTC = ["17:00", "23:00"]   # 2 slots/day for Shorts
LONG_SLOT_UTC   = "15:00"             # Long videos: 3pm UTC (10am EST — morning discovery)

VIDEOS_PER_DAY  = 3


def load_pending() -> list:
    """Return ordered list of pending video IDs from pending_uploads.json."""
    with open(ROOT / "state/pending_uploads.json") as f:
        data = json.load(f)
    pending = [e for e in data["pending"] if not e.get("scheduled") and not e.get("youtube_id")]
    return pending


def build_schedule(pending: list, start_date: datetime) -> list:
    """Assign a publish datetime to each video."""
    schedule = []
    day = 0
    slot_idx = 0
    long_video_days = set()  # track days with a long video

    for entry in pending:
        vid_id = entry["id"]
        is_long = vid_id.startswith("L")

        # Long videos get their own day slot at LONG_SLOT_UTC
        if is_long:
            # Find next day not already used for a long video
            while day in long_video_days:
                day += 1
            pub_date = start_date + timedelta(days=day)
            pub_dt = pub_date.replace(
                hour=int(LONG_SLOT_UTC.split(":")[0]),
                minute=0, second=0, microsecond=0,
                tzinfo=timezone.utc
            )
            long_video_days.add(day)
            schedule.append({**entry, "publish_at": pub_dt.isoformat(), "day": day})
            day += 1  # Long video takes its own day
            slot_idx = 0
            continue

        # Short videos: 2 per day max (leaving room for potential long video)
        slots_this_day = DAILY_SLOTS_UTC
        if slot_idx >= len(slots_this_day):
            day += 1
            slot_idx = 0

        # Skip days reserved for long videos
        while day in long_video_days:
            day += 1

        pub_date = start_date + timedelta(days=day)
        slot_time = slots_this_day[slot_idx]
        pub_dt = pub_date.replace(
            hour=int(slot_time.split(":")[0]),
            minute=int(slot_time.split(":")[1]),
            second=0, microsecond=0,
            tzinfo=timezone.utc
        )

        schedule.append({**entry, "publish_at": pub_dt.isoformat(), "day": day})
        slot_idx += 1

    return schedule


def save_schedule(schedule: list):
    """Save schedule to state/upload_schedule.json."""
    data = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_videos": len(schedule),
        "first_publish": schedule[0]["publish_at"] if schedule else None,
        "last_publish": schedule[-1]["publish_at"] if schedule else None,
        "schedule": schedule,
    }
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ Schedule saved → state/upload_schedule.json")


def print_schedule(schedule: list):
    """Print the full schedule in a readable format."""
    print()
    print("━" * 60)
    print("📅  جدول النشر — FactForge")
    print("━" * 60)

    current_day = -1
    for entry in schedule:
        pub_dt = datetime.fromisoformat(entry["publish_at"])
        # Convert to Riyadh time (UTC+3)
        riyadh_dt = pub_dt + timedelta(hours=3)
        day_str = riyadh_dt.strftime("%Y-%m-%d")
        time_str = riyadh_dt.strftime("%H:%M")

        if entry["day"] != current_day:
            current_day = entry["day"]
            day_label = f"اليوم +{entry['day']}" if entry['day'] > 0 else "اليوم"
            print(f"\n  📆 {day_str}  ({day_label})")

        vid_type = "🎬" if entry["id"].startswith("L") else "📱"
        print(f"     {vid_type} {time_str} (توقيت الرياض) — {entry['id']} — {entry['title'][:45]}")

    if schedule:
        last_dt = datetime.fromisoformat(schedule[-1]["publish_at"]) + timedelta(hours=3)
        print()
        print(f"  ⏱️  آخر مقطع ينشر: {last_dt.strftime('%Y-%m-%d')} الساعة {last_dt.strftime('%H:%M')} (الرياض)")
    print("━" * 60)


def upload_scheduled(entry: dict, youtube):
    """Upload a single video as 'scheduled private' on YouTube."""
    from googleapiclient.http import MediaFileUpload

    vid_id = entry["id"]
    video_file = ROOT / entry["video_file"]
    meta_file = ROOT / "output" / vid_id / "metadata.json"

    if not video_file.exists():
        print(f"  ❌ {vid_id}: video file not found — {video_file}")
        return None
    if not meta_file.exists():
        print(f"  ❌ {vid_id}: metadata.json not found")
        return None

    with open(meta_file) as f:
        meta = json.load(f)

    title = meta.get("selected_title") or meta.get("titles", [""])[0]
    description = meta.get("description", "")
    tags = meta.get("tags", [])
    category_id = "27"  # Education

    # YouTube requires publishAt in RFC 3339
    pub_at = entry["publish_at"]

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:4900],
            "tags": tags[:500],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": pub_at,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        str(video_file),
        mimetype="video/mp4",
        resumable=True,
        chunksize=1024 * 1024 * 5,
    )

    print(f"  ↑ Uploading {vid_id} — scheduled {pub_at[:10]} ...")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"    {pct}%", end="\r")

    yt_id = response["id"]
    print(f"  ✅ {vid_id} → https://youtu.be/{yt_id}  (publishes {pub_at[:10]})")
    return yt_id


def mark_scheduled(vid_id: str, yt_id: str, pub_at: str):
    """Mark video as scheduled in pending_uploads.json."""
    path = ROOT / "state/pending_uploads.json"
    with open(path) as f:
        data = json.load(f)
    for entry in data["pending"]:
        if entry["id"] == vid_id:
            entry["scheduled"] = True
            entry["youtube_id"] = yt_id
            entry["publish_at"] = pub_at
            entry["blocked_reason"] = None
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_youtube_client():
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials

    token_path = ROOT / "config/youtube_token.json"
    with open(token_path) as f:
        tok = json.load(f)
    creds = Credentials(
        token=tok["token"],
        refresh_token=tok["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=tok["client_id"],
        client_secret=tok["client_secret"],
        scopes=tok["scopes"],
    )
    return build("youtube", "v3", credentials=creds)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", action="store_true", help="Show plan only, no upload")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild schedule from scratch")
    args = parser.parse_args()

    # Load or build schedule
    if SCHEDULE_FILE.exists() and not args.rebuild:
        with open(SCHEDULE_FILE) as f:
            sched_data = json.load(f)
        schedule = sched_data["schedule"]
        print(f"✓ Loaded existing schedule ({len(schedule)} videos)")
    else:
        pending = load_pending()
        print(f"✓ {len(pending)} videos to schedule")
        # Start from tomorrow 17:00 UTC if after 12:00 UTC today, else today
        now = datetime.now(timezone.utc)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if now.hour >= 14:  # past 2pm UTC, start tomorrow
            start += timedelta(days=1)
        schedule = build_schedule(pending, start)
        save_schedule(schedule)

    print_schedule(schedule)

    if args.plan:
        return

    # Find today's videos to upload (not yet scheduled, publish_at <= today+1day)
    now = datetime.now(timezone.utc)
    today_end = (now + timedelta(days=1)).replace(hour=23, minute=59)

    to_upload_today = [
        e for e in schedule
        if not e.get("scheduled") and not e.get("youtube_id")
        and datetime.fromisoformat(e["publish_at"]) <= today_end
    ][:VIDEOS_PER_DAY]

    if not to_upload_today:
        print("\n✅ لا يوجد مقاطع لرفعها اليوم — كل شيء مجدول.")
        return

    print(f"\n📤 رفع {len(to_upload_today)} مقاطع اليوم ...\n")

    youtube = get_youtube_client()

    for entry in to_upload_today:
        yt_id = upload_scheduled(entry, youtube)
        if yt_id:
            mark_scheduled(entry["id"], yt_id, entry["publish_at"])
            # Update schedule file
            for s in schedule:
                if s["id"] == entry["id"]:
                    s["scheduled"] = True
                    s["youtube_id"] = yt_id
            save_schedule(schedule)
        time.sleep(3)  # avoid rate limiting

    print(f"\n✅ تم رفع {len(to_upload_today)} مقاطع كـ scheduled على YouTube")
    print("   ستُنشر تلقائياً في المواعيد المحددة أعلاه.")


if __name__ == "__main__":
    main()
