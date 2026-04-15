"""
analytics_report.py — Fetch YouTube analytics, score video performance,
track hook formulas, and optionally rotate A/B titles.

Usage:
    python3 scripts/analytics_report.py              # default: --report
    python3 scripts/analytics_report.py --report
    python3 scripts/analytics_report.py --rotate-titles
    python3 scripts/analytics_report.py --full       # report + rotate titles
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from utils.youtube_helper import get_youtube_client

# ─── Paths ────────────────────────────────────────────────────────────────────
STATE_DIR         = ROOT / "state"
OUTPUT_DIR        = ROOT / "output"
PENDING_PATH      = STATE_DIR / "pending_uploads.json"
PUBLISHED_PATH    = STATE_DIR / "published_videos.json"
ANALYTICS_PATH    = STATE_DIR / "analytics.json"
HOOK_PERF_PATH    = STATE_DIR / "hook_performance.json"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_json(path: Path) -> dict | list:
    if path.exists():
        return json.loads(path.read_text())
    return {}


def save_json(path: Path, data: dict | list) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def get_credentials(youtube):
    """Extract raw credentials from the YouTube API resource."""
    return youtube._http.credentials


def build_analytics_client(creds):
    """Build YouTube Analytics API v2 client."""
    return build("youtubeAnalytics", "v2", credentials=creds)


def retention_grade(avg_view_pct: float) -> str:
    if avg_view_pct >= 70:
        return "A"
    if avg_view_pct >= 50:
        return "B"
    if avg_view_pct >= 30:
        return "C"
    return "D"


def get_video_ids_to_analyze(pending: list) -> list[dict]:
    """Return all pending entries that have a youtube_id."""
    return [v for v in pending if v.get("youtube_id")]


# ─── YouTube Data API stats (CTR + impressions + basic stats) ─────────────────

def fetch_data_api_stats(youtube, youtube_ids: list[str]) -> dict[str, dict]:
    """
    Use videos().list to get statistics for a batch of video IDs.
    Returns dict keyed by youtube_id.
    """
    results = {}
    # API allows max 50 per request
    for i in range(0, len(youtube_ids), 50):
        batch = youtube_ids[i : i + 50]
        try:
            resp = youtube.videos().list(
                part="statistics",
                id=",".join(batch),
            ).execute()
            for item in resp.get("items", []):
                vid_id = item["id"]
                stats = item.get("statistics", {})
                results[vid_id] = {
                    "views":    int(stats.get("viewCount", 0)),
                    "likes":    int(stats.get("likeCount", 0)),
                    "comments": int(stats.get("commentCount", 0)),
                }
        except HttpError as e:
            print(f"⚠️  Data API error for batch: {e}")
    return results


# ─── YouTube Analytics API ────────────────────────────────────────────────────

def fetch_analytics_for_video(
    analytics,
    youtube_id: str,
    publish_at: str | None,
) -> dict:
    """
    Fetch per-video analytics from YouTube Analytics API.
    Returns dict with analytics fields or zeros on failure.
    """
    empty = {
        "avg_view_pct":         0.0,
        "avg_view_duration_sec": 0,
        "subs_gained":          0,
        "impressions":          0,
        "ctr_pct":              0.0,
        "minutes_watched":      0,
    }

    # Determine date range: from publish date to today
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if publish_at:
        try:
            pub_dt = datetime.fromisoformat(publish_at.replace("Z", "+00:00"))
            start_date = pub_dt.strftime("%Y-%m-%d")
        except ValueError:
            start_date = "2026-01-01"
    else:
        start_date = "2026-01-01"

    try:
        resp = analytics.reports().query(
            ids="channel==MINE",
            startDate=start_date,
            endDate=today,
            metrics="estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained",
            filters=f"video=={youtube_id}",
            dimensions="video",
        ).execute()

        rows = resp.get("rows", [])
        if rows:
            row = rows[0]
            # columns: video, estimatedMinutesWatched, averageViewDuration,
            #          averageViewPercentage, subscribersGained
            empty["minutes_watched"]       = int(row[1])
            empty["avg_view_duration_sec"] = int(row[2])
            empty["avg_view_pct"]          = float(row[3])
            empty["subs_gained"]           = int(row[4])

    except HttpError as e:
        code = e.resp.status if hasattr(e, "resp") else 0
        if code == 403:
            print(f"  ⚠️  Analytics API 403 for {youtube_id} — not yet available")
        else:
            print(f"  ⚠️  Analytics API error for {youtube_id}: {e}")

    return empty


# ─── Script hook formula ──────────────────────────────────────────────────────

def get_hook_formula(video_id: str) -> str | None:
    """Read hook_formula from output/[id]/script.json."""
    script_path = OUTPUT_DIR / video_id / "script.json"
    if not script_path.exists():
        return None
    try:
        data = json.loads(script_path.read_text())
        return data.get("hook_formula") or data.get("title_formula") or None
    except (json.JSONDecodeError, KeyError):
        return None


# ─── Performance scoring ──────────────────────────────────────────────────────

def compute_performance_scores(videos: list[dict]) -> list[dict]:
    """
    Compute raw score per video, then normalize 0–100 relative to batch.
    raw_score = views×0.3 + avg_view_pct×0.3 + likes×0.2 + subs_gained×0.2
    """
    for v in videos:
        s = v["stats"]
        v["_raw_score"] = (
            s["views"]        * 0.3
            + s["avg_view_pct"] * 0.3
            + s["likes"]        * 0.2
            + s["subs_gained"]  * 0.2
        )

    raw_scores = [v["_raw_score"] for v in videos]
    min_s = min(raw_scores, default=0)
    max_s = max(raw_scores, default=1)
    span  = max_s - min_s if max_s != min_s else 1

    for v in videos:
        v["performance_score"] = round((v["_raw_score"] - min_s) / span * 100)
        del v["_raw_score"]

    return videos


# ─── Hook performance aggregation ─────────────────────────────────────────────

def update_hook_performance(videos: list[dict]) -> dict:
    """
    Aggregate per-formula averages and save to state/hook_performance.json.
    """
    formula_buckets: dict[str, list] = {}
    for v in videos:
        formula = v.get("hook_formula")
        if not formula:
            continue
        formula_buckets.setdefault(formula, []).append(v)

    hook_stats = {}
    for formula, vids in formula_buckets.items():
        avg_views     = round(sum(v["stats"]["views"]       for v in vids) / len(vids))
        avg_retention = round(sum(v["stats"]["avg_view_pct"] for v in vids) / len(vids), 1)
        avg_ctr       = round(sum(v["stats"]["ctr_pct"]     for v in vids) / len(vids), 1)
        hook_stats[formula] = {
            "videos":           len(vids),
            "avg_views":        avg_views,
            "avg_retention_pct": avg_retention,
            "avg_ctr":          avg_ctr,
        }

    best_formula = None
    if hook_stats:
        best_formula = max(
            hook_stats,
            key=lambda f: hook_stats[f]["avg_views"] + hook_stats[f]["avg_retention_pct"] * 10,
        )

    result = {
        "hook_stats":    hook_stats,
        "best_formula":  best_formula,
        "last_updated":  datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }
    save_json(HOOK_PERF_PATH, result)
    return result


# ─── Recommendations ──────────────────────────────────────────────────────────

def generate_recommendations(videos: list[dict], hook_data: dict) -> list[str]:
    recs = []

    # Hook formula comparison
    stats = hook_data.get("hook_stats", {})
    formulas = sorted(stats.keys(), key=lambda f: stats[f]["avg_views"], reverse=True)
    if len(formulas) >= 2:
        best, worst = formulas[0], formulas[-1]
        best_views  = stats[best]["avg_views"]
        worst_views = stats[worst]["avg_views"]
        if worst_views > 0:
            pct_diff = round((best_views - worst_views) / worst_views * 100)
            recs.append(
                f"Hook formula {best} outperforms {worst} by {pct_diff}% — prioritize formula {best}"
            )

    # Low retention warning
    low_retention = [v for v in videos if v["stats"]["avg_view_pct"] < 40]
    if low_retention:
        recs.append(
            f"{len(low_retention)} video(s) below 40% retention — consider stronger hooks"
        )

    # Shorts retention vs YouTube average
    shorts = [v for v in videos if v.get("type", "short") == "short"]
    if shorts:
        avg_ret = sum(v["stats"]["avg_view_pct"] for v in shorts) / len(shorts)
        grade = "above" if avg_ret >= 60 else "below"
        recs.append(
            f"Shorts average {avg_ret:.0f}% retention — {grade} YouTube average (60%)"
        )

    # Low CTR
    low_ctr = [v for v in videos if 0 < v["stats"]["ctr_pct"] < 3.5]
    if low_ctr:
        recs.append(
            f"{len(low_ctr)} video(s) with CTR < 3.5% — consider A/B title rotation (--rotate-titles)"
        )

    return recs


# ─── Main analytics report ────────────────────────────────────────────────────

def run_report() -> dict:
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📊  FactForge Analytics Report")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # Load state
    pending_data = load_json(PENDING_PATH)
    pending_list = pending_data.get("pending", []) if isinstance(pending_data, dict) else []
    entries      = get_video_ids_to_analyze(pending_list)

    if not entries:
        print("⚠️  No videos with youtube_id found in pending_uploads.json")
        return {}

    print(f"✓  Found {len(entries)} videos to analyze")

    # Auth
    youtube = get_youtube_client()
    creds   = get_credentials(youtube)
    try:
        analytics = build_analytics_client(creds)
    except Exception as e:
        print(f"⚠️  Could not build Analytics client: {e}")
        analytics = None

    # Fetch Data API stats (views, likes, comments)
    youtube_ids = [e["youtube_id"] for e in entries]
    print(f"✓  Fetching Data API stats for {len(youtube_ids)} videos…")
    data_stats = fetch_data_api_stats(youtube, youtube_ids)

    # Build per-video records
    video_records = []
    for entry in entries:
        vid_id     = entry["id"]
        yt_id      = entry["youtube_id"]
        publish_at = entry.get("publish_at")
        title      = entry.get("title", "")
        vtype      = entry.get("type", "short" if vid_id.startswith("S") else "long")

        print(f"  → {vid_id} ({yt_id})")

        # Base stats from Data API
        base = data_stats.get(yt_id, {"views": 0, "likes": 0, "comments": 0})

        # Analytics API stats
        if analytics:
            an_stats = fetch_analytics_for_video(analytics, yt_id, publish_at)
        else:
            an_stats = {
                "avg_view_pct": 0.0, "avg_view_duration_sec": 0,
                "subs_gained": 0, "impressions": 0,
                "ctr_pct": 0.0, "minutes_watched": 0,
            }

        stats = {
            "views":               base["views"],
            "avg_view_pct":        an_stats["avg_view_pct"],
            "avg_view_duration_sec": an_stats["avg_view_duration_sec"],
            "likes":               base["likes"],
            "comments":            base["comments"],
            "subs_gained":         an_stats["subs_gained"],
            "ctr_pct":             an_stats["ctr_pct"],
            "impressions":         an_stats["impressions"],
        }

        hook_formula = get_hook_formula(vid_id)

        video_records.append({
            "id":           vid_id,
            "youtube_id":   yt_id,
            "title":        title,
            "type":         vtype,
            "publish_at":   publish_at,
            "stats":        stats,
            "retention_grade": retention_grade(stats["avg_view_pct"]),
            "hook_formula": hook_formula,
        })

    # Score performance
    video_records = compute_performance_scores(video_records)

    # Hook performance
    hook_data = update_hook_performance(video_records)
    print(f"✓  Hook performance updated → {HOOK_PERF_PATH.name}")

    # Totals
    total_views    = sum(v["stats"]["views"]       for v in video_records)
    total_subs     = sum(v["stats"]["subs_gained"] for v in video_records)

    # Top / worst
    sorted_by_score = sorted(video_records, key=lambda v: v["performance_score"], reverse=True)
    top     = sorted_by_score[0]  if sorted_by_score else None
    worst   = sorted_by_score[-1] if sorted_by_score else None

    recommendations = generate_recommendations(video_records, hook_data)

    analytics_out = {
        "last_fetched":          datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_videos_analyzed": len(video_records),
        "channel_totals": {
            "total_views":      total_views,
            "total_subs_gained": total_subs,
        },
        "videos":           video_records,
        "top_performer":    {"id": top["id"],   "score": top["performance_score"]}   if top   else None,
        "worst_performer":  {"id": worst["id"], "score": worst["performance_score"]} if worst else None,
        "recommendations":  recommendations,
        "title_rotations":  load_json(ANALYTICS_PATH).get("title_rotations", []) if ANALYTICS_PATH.exists() else [],
    }

    save_json(ANALYTICS_PATH, analytics_out)
    print(f"✓  Analytics saved → {ANALYTICS_PATH.name}")

    # ── Print dashboard ──────────────────────────────────────────────────────
    print()
    print(f"Videos analyzed: {len(video_records)}")
    print(f"Total views: {total_views:,}  |  Subs gained: +{total_subs}")
    print()

    print("TOP PERFORMERS:")
    for i, v in enumerate(sorted_by_score[:3], 1):
        medal = ["🥇", "🥈", "🥉"][i - 1]
        s = v["stats"]
        print(
            f"  {medal} {v['id']} — \"{v['title'][:55]}\" — "
            f"{s['views']:,} views, {s['avg_view_pct']:.0f}% retention, grade {v['retention_grade']}"
        )

    print()
    print("HOOK PERFORMANCE:")
    hook_stats = hook_data.get("hook_stats", {})
    best_f     = hook_data.get("best_formula")
    for formula, hs in sorted(hook_stats.items()):
        marker = " ← BEST" if formula == best_f else ""
        print(
            f"  Formula {formula}: avg {hs['avg_views']:,} views, "
            f"{hs['avg_retention_pct']}% retention{marker}"
        )

    if recommendations:
        print()
        print("RECOMMENDATIONS:")
        for rec in recommendations:
            print(f"  → {rec}")

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    return analytics_out


# ─── A/B Title Rotation ───────────────────────────────────────────────────────

def check_and_rotate_titles() -> None:
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🔄  A/B Title Rotation")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    pending_data = load_json(PENDING_PATH)
    pending_list = pending_data.get("pending", []) if isinstance(pending_data, dict) else []
    entries      = get_video_ids_to_analyze(pending_list)

    if not entries:
        print("⚠️  No videos with youtube_id found")
        return

    youtube          = get_youtube_client()
    now_utc          = datetime.now(timezone.utc)
    cutoff           = now_utc - timedelta(hours=48)

    # Load existing analytics for CTR data
    analytics_data   = load_json(ANALYTICS_PATH)
    video_analytics  = {v["id"]: v for v in analytics_data.get("videos", [])}

    # Load / init title_rotations log
    title_rotations  = analytics_data.get("title_rotations", [])
    already_rotated  = {r["id"] for r in title_rotations}

    rotated_count = 0

    for entry in entries:
        vid_id     = entry["id"]
        yt_id      = entry["youtube_id"]
        publish_at = entry.get("publish_at")

        # Skip if not yet 48 hours old
        if publish_at:
            try:
                pub_dt = datetime.fromisoformat(publish_at.replace("Z", "+00:00"))
                if pub_dt > cutoff:
                    continue
            except ValueError:
                pass

        # Get CTR from analytics
        va      = video_analytics.get(vid_id, {})
        ctr_pct = va.get("stats", {}).get("ctr_pct", 0.0)

        if ctr_pct >= 3.5 or ctr_pct == 0.0:
            # 0.0 means no data yet — skip
            continue

        # Load metadata.json for title list
        meta_path = OUTPUT_DIR / vid_id / "metadata.json"
        if not meta_path.exists():
            print(f"  ⚠️  {vid_id}: metadata.json not found, skipping")
            continue

        meta   = json.loads(meta_path.read_text())
        titles = meta.get("titles", [])
        current_title = entry.get("title", meta.get("title_selected", ""))

        # Find current title index
        try:
            current_idx = titles.index(current_title)
        except ValueError:
            current_idx = 0

        next_idx = current_idx + 1
        if next_idx >= len(titles):
            print(f"  ⚠️  {vid_id}: no more title variants to try")
            continue

        new_title = titles[next_idx]
        print(f"  → {vid_id}: CTR={ctr_pct:.1f}% — rotating title")
        print(f"     FROM: {current_title}")
        print(f"     TO:   {new_title}")

        # Fetch current snippet to preserve other fields
        try:
            resp    = youtube.videos().list(part="snippet", id=yt_id).execute()
            items   = resp.get("items", [])
            if not items:
                print(f"  ❌ {vid_id}: video not found on YouTube")
                continue
            snippet = items[0]["snippet"]
            snippet["title"] = new_title

            youtube.videos().update(
                part="snippet",
                body={"id": yt_id, "snippet": snippet},
            ).execute()

            print(f"  ✓  {vid_id}: title updated on YouTube")
            rotated_count += 1

            # Log rotation
            title_rotations.append({
                "id":         vid_id,
                "youtube_id": yt_id,
                "old_title":  current_title,
                "new_title":  new_title,
                "rotated_at": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "ctr_before": ctr_pct,
            })

            # Update pending_uploads.json entry title
            entry["title"] = new_title

        except HttpError as e:
            print(f"  ❌ {vid_id}: YouTube API error — {e}")

    # Save updated pending state
    if rotated_count > 0:
        save_json(PENDING_PATH, pending_data)

    # Persist rotations in analytics.json
    if ANALYTICS_PATH.exists():
        analytics_data["title_rotations"] = title_rotations
        save_json(ANALYTICS_PATH, analytics_data)
    else:
        save_json(ANALYTICS_PATH, {"title_rotations": title_rotations})

    print(f"\n✓  Rotated {rotated_count} title(s)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="FactForge analytics report and A/B title rotation"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Fetch analytics and print report (default)",
    )
    parser.add_argument(
        "--rotate-titles",
        action="store_true",
        help="Run A/B title rotation only",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run both analytics report and title rotation",
    )
    args = parser.parse_args()

    # Default: --report
    do_report = args.report or args.full or not (args.rotate_titles or args.full)
    do_rotate = args.rotate_titles or args.full

    if do_report:
        run_report()

    if do_rotate:
        check_and_rotate_titles()


if __name__ == "__main__":
    main()
