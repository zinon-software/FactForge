"""
auto_upload.py — Smart daily uploader with quota tracking for FactForge.

Reads state/pending_uploads.json for videos ready to upload (no youtube_id yet,
video.mp4 exists on disk), respects daily quota limits, and writes results to
state/upload_log.json.

Usage:
    python3 scripts/auto_upload.py              # upload up to quota limit
    python3 scripts/auto_upload.py --dry-run    # show what would upload, no action
    python3 scripts/auto_upload.py --limit 3    # override daily limit to 3
    python3 scripts/auto_upload.py --force      # ignore quota tracking, upload all ready
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

STATE_DIR      = ROOT / "state"
PENDING_FILE   = STATE_DIR / "pending_uploads.json"
QUOTA_FILE     = STATE_DIR / "quota_usage.json"
UPLOAD_LOG     = STATE_DIR / "upload_log.json"

DEFAULT_DAILY_LIMIT   = 6
UPLOAD_WAIT_SECONDS   = 30   # wait between uploads to avoid rate limiting
QUOTA_RESET_HOUR_UTC  = 8    # YouTube quota resets at 08:00 UTC (midnight Pacific)


# ─── Quota management ─────────────────────────────────────────────────────────

def load_quota() -> dict:
    """Load today's quota usage, resetting if the date has changed."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if QUOTA_FILE.exists():
        data = json.loads(QUOTA_FILE.read_text(encoding="utf-8"))
        if data.get("date") == today:
            return data

    # New day — reset counter
    return {
        "date": today,
        "uploads_today": 0,
        "daily_limit": DEFAULT_DAILY_LIMIT,
        "reset_hour_utc": QUOTA_RESET_HOUR_UTC,
    }


def save_quota(quota: dict) -> None:
    QUOTA_FILE.write_text(json.dumps(quota, indent=2, ensure_ascii=False), encoding="utf-8")


def quota_remaining(quota: dict) -> int:
    return max(0, quota["daily_limit"] - quota["uploads_today"])


# ─── State helpers ────────────────────────────────────────────────────────────

def load_pending() -> list[dict]:
    if not PENDING_FILE.exists():
        return []
    data = json.loads(PENDING_FILE.read_text(encoding="utf-8"))
    return data.get("pending", [])


def save_pending(pending: list[dict]) -> None:
    data = {"pending": pending}
    PENDING_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def video_file_path(entry: dict) -> Path | None:
    """
    Resolve the video file path for a pending entry.
    Checks:
      1. entry["video_file"] relative to ROOT
      2. output/<id>/video.mp4 as fallback
    """
    vid_id = entry.get("id", "")

    # Try explicit video_file field first
    vf = entry.get("video_file")
    if vf:
        p = ROOT / vf
        if p.exists():
            return p

    # Fallback: standard output location
    fallback = ROOT / "output" / vid_id / "video.mp4"
    if fallback.exists():
        return fallback

    return None


def find_uploadable(pending: list[dict]) -> list[dict]:
    """
    Return entries that are ready to upload:
    - No youtube_id (not yet uploaded)
    - video.mp4 exists on disk
    - Not blocked
    """
    ready = []
    for entry in pending:
        if entry.get("youtube_id"):
            continue  # already uploaded
        if entry.get("blocked_reason"):
            continue  # blocked
        if not entry.get("ready", True):
            continue  # not ready

        vf = video_file_path(entry)
        if vf is None:
            continue  # video file missing

        ready.append(entry)
    return ready


# ─── Upload ───────────────────────────────────────────────────────────────────

def upload_one(entry: dict) -> str | None:
    """
    Upload a single video. Returns the YouTube video ID on success, None on failure.
    Raises googleapiclient.errors.HttpError on quota exceeded (caller handles).
    """
    from utils.youtube_helper import (
        upload_video,
        set_thumbnail,
        get_next_publish_date,
        update_state_after_upload,
    )

    vid_id  = entry["id"]
    is_long = vid_id.startswith("L")

    # Load metadata
    meta_path = ROOT / "output" / vid_id / "metadata.json"
    if not meta_path.exists():
        print(f"    ⚠️  metadata.json not found for {vid_id} — skipping")
        return None

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    title   = meta.get("selected_title") or meta.get("title_selected") or meta.get("title", vid_id)
    desc    = meta.get("description", "")
    tags    = meta.get("tags", [])
    cat_id  = meta.get("category_id", "27")

    # Resolve video file
    vf = video_file_path(entry)
    if vf is None:
        print(f"    ⚠️  Video file not found for {vid_id} — skipping")
        return None

    # Calculate publish date
    video_type  = "long" if is_long else "short"
    publish_at  = get_next_publish_date(video_type)

    # Upload
    yt_id = upload_video(
        video_path=vf,
        title=title,
        description=desc,
        tags=tags,
        category_id=cat_id,
        publish_at=publish_at,
        privacy="private",
    )

    if not yt_id:
        return None

    # Thumbnail
    thumb_path = ROOT / "output" / vid_id / "thumbnail.jpg"
    if not thumb_path.exists():
        thumb_path = ROOT / "output" / vid_id / "thumbnail.png"
    if thumb_path.exists():
        ok = set_thumbnail(yt_id, thumb_path)
        if not ok:
            print(f"    ⚠️  Thumbnail upload blocked for {vid_id} (expected for Shorts)")
    else:
        print(f"    ⚠️  No thumbnail found for {vid_id}")

    # Update state
    update_state_after_upload(vid_id, yt_id, publish_at, title, video_type)

    return yt_id, publish_at


# ─── Log ──────────────────────────────────────────────────────────────────────

def write_upload_log(uploaded: list[str], failed: list[str], quota_remaining_count: int) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    existing_log = []
    if UPLOAD_LOG.exists():
        try:
            existing_log = json.loads(UPLOAD_LOG.read_text(encoding="utf-8"))
            if not isinstance(existing_log, list):
                existing_log = []
        except json.JSONDecodeError:
            existing_log = []

    entry = {
        "date": today,
        "time_utc": datetime.now(timezone.utc).strftime("%H:%M"),
        "uploaded": uploaded,
        "failed": failed,
        "quota_remaining": quota_remaining_count,
    }

    # Replace today's entry if it exists, otherwise append
    updated = [e for e in existing_log if e.get("date") != today]
    # Merge uploaded/failed from earlier runs today
    prev_today = [e for e in existing_log if e.get("date") == today]
    if prev_today:
        prev = prev_today[-1]
        entry["uploaded"] = list(dict.fromkeys(prev.get("uploaded", []) + uploaded))
        entry["failed"]   = list(dict.fromkeys(prev.get("failed", []) + failed))

    updated.append(entry)
    UPLOAD_LOG.write_text(json.dumps(updated, indent=2, ensure_ascii=False), encoding="utf-8")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="FactForge auto uploader — uploads ready videos respecting quota limits."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be uploaded without actually uploading",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Override daily upload limit (default: 6)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignore quota tracking — upload all ready videos",
    )
    args = parser.parse_args()

    now_utc = datetime.now(timezone.utc)
    now_str = now_utc.strftime("%Y-%m-%d %H:%M UTC")

    print()
    print(f"📤 Auto Upload — {now_str}")

    # Load quota
    quota = load_quota()
    if args.limit is not None:
        quota["daily_limit"] = args.limit
    if args.force:
        quota["daily_limit"] = 9999

    remaining = quota_remaining(quota)
    print(f"  Quota today: {quota['uploads_today']}/{quota['daily_limit']} used, {remaining} remaining")

    # Find uploadable videos
    pending = load_pending()
    ready   = find_uploadable(pending)

    # Report missing video files separately
    no_file_entries = []
    for entry in pending:
        if entry.get("youtube_id"):
            continue
        if entry.get("blocked_reason"):
            continue
        if video_file_path(entry) is None:
            no_file_entries.append(entry)

    print(f"  Videos ready to upload: {len(ready)}")
    if no_file_entries:
        print(f"  Videos missing video file (skipped): {len(no_file_entries)}")
        for e in no_file_entries:
            print(f"    ⚠️  {e['id']} — {e.get('title', '')[:50]} (no video.mp4)")

    if not ready:
        print()
        print("  ✅ No videos ready to upload right now.")
        print()
        return

    to_upload = ready if args.force else ready[:remaining]

    if not to_upload:
        print(f"  ⚠️  Quota exhausted for today ({quota['uploads_today']}/{quota['daily_limit']})")
        print(f"       {len(ready) - len(to_upload)} video(s) will be uploaded tomorrow.")
        print()
        return

    will_upload = len(to_upload)
    deferred    = len(ready) - will_upload
    print(f"  Will upload: {will_upload}{' (quota limited)' if deferred > 0 else ''}")
    if deferred:
        print(f"  Pending tomorrow: {deferred}")
    print()

    if args.dry_run:
        print("  [dry-run] Would upload:")
        for i, entry in enumerate(to_upload, 1):
            print(f"    [{i}/{will_upload}] {entry['id']} — \"{entry.get('title', '')[:55]}\"")
        print()
        print("  No changes made (--dry-run).")
        print()
        return

    # ── Upload loop ───────────────────────────────────────────────────────────
    uploaded_ids: list[str] = []
    failed_ids:   list[str] = []

    for i, entry in enumerate(to_upload, 1):
        vid_id = entry["id"]
        title  = entry.get("title", "")
        print(f"  [{i}/{will_upload}] Uploading {vid_id} — \"{title[:55]}\"...")

        try:
            result = upload_one(entry)
            if result is None:
                print(f"    ✗ Upload failed for {vid_id}")
                failed_ids.append(vid_id)
            else:
                yt_id, publish_at = result
                pub_date = publish_at[:10]
                print(f"    ✓ Uploaded → https://youtu.be/{yt_id}  (publishes {pub_date})")
                uploaded_ids.append(vid_id)
                quota["uploads_today"] += 1
                save_quota(quota)

        except Exception as exc:
            exc_str = str(exc)
            # Detect quota exceeded
            if "quotaExceeded" in exc_str or ("403" in exc_str and "quota" in exc_str.lower()):
                print(f"    ✗ Quota exceeded — stopping upload batch.")
                quota["quota_exceeded_at"] = now_utc.isoformat()
                save_quota(quota)
                failed_ids.append(vid_id)
                break
            else:
                print(f"    ✗ Error uploading {vid_id}: {exc_str[:120]}")
                failed_ids.append(vid_id)

        # Wait between uploads to avoid rate limiting (skip after last)
        if i < will_upload:
            print(f"    ⏳ Waiting {UPLOAD_WAIT_SECONDS}s before next upload...")
            time.sleep(UPLOAD_WAIT_SECONDS)

    # ── Summary ───────────────────────────────────────────────────────────────
    remaining_after = quota_remaining(quota)
    write_upload_log(uploaded_ids, failed_ids, remaining_after)

    print()
    if uploaded_ids:
        print(f"  ✅ Done: {len(uploaded_ids)} uploaded, {len(failed_ids)} failed, {remaining_after} quota remaining")
    else:
        print(f"  ⚠️  No videos were uploaded successfully.")

    still_pending = len(ready) - len(uploaded_ids)
    if still_pending > 0:
        print(f"     {still_pending} video(s) pending for next run")
    print()


if __name__ == "__main__":
    main()
