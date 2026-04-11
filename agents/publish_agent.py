"""
Publish Agent — Uploads videos to YouTube with smart scheduling.
Handles OAuth2, video upload, thumbnail upload, metadata, and translations.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import (
    YOUTUBE_CREDENTIALS_PATH, YOUTUBE_TOKEN_PATH,
    OPTIMAL_PUBLISH_WINDOWS, PUBLISH_INTERVAL_HOURS,
    YOUTUBE_CATEGORY_EDUCATION
)
from utils.file_manager import (
    get_output_dir, update_progress_step, load_progress,
    save_progress, mark_idea_used, now_utc
)


def get_youtube_service():
    """Authenticate and return YouTube API service object."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    scopes = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube",
        "https://www.googleapis.com/auth/youtubepartner",
    ]

    creds = None
    token_path = Path(YOUTUBE_TOKEN_PATH)

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(YOUTUBE_CREDENTIALS_PATH), scopes
            )
            creds = flow.run_local_server(port=0)

        # Save token for next run
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def calculate_optimal_schedule(last_published_at: str = None) -> datetime:
    """
    Calculate the next optimal publish time based on:
    - Best days/times (OPTIMAL_PUBLISH_WINDOWS)
    - Minimum gap from last published video (PUBLISH_INTERVAL_HOURS)
    """
    now = datetime.now(timezone.utc)
    min_publish_time = now + timedelta(hours=1)  # At least 1 hour from now

    if last_published_at:
        try:
            last_pub = datetime.fromisoformat(last_published_at.replace("Z", "+00:00"))
            earliest = last_pub + timedelta(hours=PUBLISH_INTERVAL_HOURS)
            if earliest > min_publish_time:
                min_publish_time = earliest
        except Exception:
            pass

    # Find next optimal window after min_publish_time
    day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

    # Check next 14 days
    for days_ahead in range(14):
        check_date = min_publish_time + timedelta(days=days_ahead)
        day_name = day_names[check_date.weekday()]

        for window in OPTIMAL_PUBLISH_WINDOWS:
            if window["day"] != day_name:
                continue

            # Parse window time (EST to UTC: EST = UTC-5)
            start_hour_est, start_min = map(int, window["start_est"].split(":"))
            start_utc = check_date.replace(
                hour=(start_hour_est + 5) % 24,
                minute=start_min,
                second=0,
                microsecond=0
            )

            if start_utc > min_publish_time:
                return start_utc

    # Fallback: schedule for tomorrow at 3pm UTC
    fallback = now + timedelta(days=1)
    return fallback.replace(hour=15, minute=0, second=0, microsecond=0)


def upload_video(
    youtube,
    video_path: Path,
    thumbnail_path: Path,
    metadata: dict,
    idea: dict,
    scheduled_time: datetime,
) -> str:
    """Upload video to YouTube and return the YouTube video ID."""
    from googleapiclient.http import MediaFileUpload

    title = metadata.get("selected_title", idea["title"])[:100]
    description = metadata.get("description", "")[:5000]
    tags = metadata.get("tags", ["facts", "history"])[:500]  # YouTube tag char limit

    # Video resource body
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": metadata.get("category_id", YOUTUBE_CATEGORY_EDUCATION),
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": scheduled_time.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "selfDeclaredMadeForKids": False,
        },
    }

    # Detect if it's a Short
    duration = idea.get("estimated_duration_seconds", 55)
    if duration <= 60:
        body["snippet"]["tags"].append("#Shorts")

    print(f"[publish_agent] Uploading video: {title[:60]}")
    print(f"[publish_agent] Scheduled for: {scheduled_time.isoformat()}")

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        resumable=True,
        chunksize=10 * 1024 * 1024,  # 10MB chunks
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  Upload progress: {int(status.progress() * 100)}%")

    youtube_id = response["id"]
    print(f"[publish_agent] Upload complete: https://youtu.be/{youtube_id}")

    # Upload thumbnail
    youtube.thumbnails().set(
        videoId=youtube_id,
        media_body=MediaFileUpload(str(thumbnail_path), mimetype="image/png")
    ).execute()
    print(f"[publish_agent] Thumbnail uploaded")

    # Add multi-language metadata
    translations = metadata.get("translations", {})
    for lang_code, trans_data in translations.items():
        try:
            youtube.videos().update(
                part="localizations",
                body={
                    "id": youtube_id,
                    "localizations": {
                        lang_code: {
                            "title": trans_data.get("title", title),
                            "description": trans_data.get("description", description),
                        }
                    }
                }
            ).execute()
        except Exception as e:
            print(f"[publish_agent] Localization {lang_code} failed: {e}")

    return youtube_id


def run(idea: dict, metadata: dict) -> str | None:
    """
    Main entry point: upload and schedule video.
    Returns YouTube video ID or None if upload fails.
    """
    output_dir = get_output_dir(idea["id"])
    video_path = output_dir / "video.mp4"
    thumbnail_path = output_dir / "thumbnail.png"

    if not video_path.exists():
        print(f"[publish_agent] ERROR: video.mp4 not found at {video_path}")
        return None

    if not thumbnail_path.exists():
        print(f"[publish_agent] WARNING: thumbnail.png not found — uploading without custom thumbnail")
        thumbnail_path = None

    if not Path(YOUTUBE_CREDENTIALS_PATH).exists():
        print(f"[publish_agent] ERROR: YouTube credentials not found at {YOUTUBE_CREDENTIALS_PATH}")
        print("Please set up YouTube API credentials. See README.md for instructions.")
        return None

    try:
        youtube = get_youtube_service()

        # Calculate optimal schedule
        progress = load_progress()
        last_published = progress.get("last_published_at")
        scheduled_time = calculate_optimal_schedule(last_published)

        # Upload
        youtube_id = upload_video(
            youtube, video_path, thumbnail_path, metadata, idea, scheduled_time
        )

        # Update state
        mark_idea_used(idea["id"], youtube_id=youtube_id, reason="produced")
        update_progress_step("published", idea["id"])

        progress = load_progress()
        progress["total_videos_published"] = progress.get("total_videos_published", 0) + 1
        progress["last_published_at"] = now_utc()
        progress["next_scheduled_publish"] = scheduled_time.isoformat()
        progress["current_production"] = {"idea_id": None, "step": None, "steps_completed": []}
        save_progress(progress)

        print(f"\n[publish_agent] SUCCESS!")
        print(f"  YouTube ID: {youtube_id}")
        print(f"  Scheduled: {scheduled_time.strftime('%A, %B %d at %I:%M %p UTC')}")
        print(f"  URL: https://youtu.be/{youtube_id}")

        return youtube_id

    except Exception as e:
        print(f"[publish_agent] Upload failed: {e}")
        return None
