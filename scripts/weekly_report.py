"""
weekly_report.py — Generate a weekly performance and schedule report for FactForge.

Reads:
  state/pending_uploads.json  — scheduled / uploaded videos
  state/published_videos.json — confirmed published videos
  state/analytics.json        — YouTube analytics (optional)

Writes: state/weekly_report_{YYYY-MM-DD}.md
Prints: full report to stdout

Usage: python3 scripts/weekly_report.py
"""

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT      = Path(__file__).parent.parent
STATE_DIR = ROOT / "state"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"  ⚠️  Could not read {path.name}: {exc}")
        return None


def format_date(iso_str: str) -> str:
    """Return a readable date from an ISO/RFC3339 string."""
    if not iso_str:
        return "—"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%a %d %b %Y %H:%M UTC")
    except ValueError:
        return iso_str[:19]


def week_boundaries() -> tuple[datetime, datetime]:
    """Return (start, end) for the current calendar week (Mon–Sun, UTC)."""
    now   = datetime.now(timezone.utc)
    start = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end   = start + timedelta(days=7)
    return start, end


def in_current_week(iso_str: str, week_start: datetime, week_end: datetime) -> bool:
    if not iso_str:
        return False
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return week_start <= dt < week_end
    except ValueError:
        return False


# ─── Report builder ───────────────────────────────────────────────────────────

def build_report() -> str:
    now           = datetime.now(timezone.utc)
    week_start, week_end = week_boundaries()

    pending_data   = load_json(STATE_DIR / "pending_uploads.json") or {}
    published_data = load_json(STATE_DIR / "published_videos.json") or {}
    analytics_data = load_json(STATE_DIR / "analytics.json")

    pending_list   = pending_data.get("pending", [])
    published_list = (
        published_data if isinstance(published_data, list)
        else published_data.get("videos", [])
    )

    # ── Section 1: uploaded this week ────────────────────────────────────────
    uploaded_this_week = [
        v for v in pending_list
        if v.get("status") in ("scheduled", "uploaded")
        and in_current_week(v.get("publish_at", ""), week_start, week_end)
    ]
    # Also check published_videos for this week
    published_this_week = [
        v for v in published_list
        if in_current_week(
            v.get("published_at", v.get("publish_at", "")), week_start, week_end
        )
    ]

    # ── Section 2: upcoming (scheduled, future) ───────────────────────────────
    upcoming = sorted(
        [
            v for v in pending_list
            if v.get("status") in ("scheduled", "pending")
            and not in_current_week(v.get("publish_at", ""), week_start, week_end)
        ],
        key=lambda v: v.get("publish_at", ""),
    )

    # ── Section 3: top performing video from analytics ────────────────────────
    top_video = None
    if analytics_data:
        videos_perf = analytics_data.get("videos", analytics_data.get("items", []))
        if videos_perf:
            top_video = max(
                videos_perf,
                key=lambda v: v.get("views", v.get("viewCount", 0)),
                default=None,
            )

    # ── Build markdown ────────────────────────────────────────────────────────
    lines: list[str] = []

    lines.append(f"# FactForge — Weekly Report")
    lines.append(f"Generated: {now.strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"Week: {week_start.strftime('%d %b')} – {(week_end - timedelta(days=1)).strftime('%d %b %Y')}")
    lines.append("")

    # ── Summary stats ─────────────────────────────────────────────────────────
    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Metric | Count |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Videos uploaded/scheduled this week | {len(uploaded_this_week) + len(published_this_week)} |")
    lines.append(f"| Upcoming scheduled videos | {len(upcoming)} |")
    lines.append(f"| Total in pending queue | {len(pending_list)} |")
    lines.append(f"| Total published (all time) | {len(published_list)} |")
    lines.append("")

    # ── This week ─────────────────────────────────────────────────────────────
    lines.append("## Videos This Week")
    lines.append("")

    combined_this_week = {v.get("youtube_id", v.get("id")): v for v in published_this_week}
    for v in uploaded_this_week:
        yt_id = v.get("youtube_id")
        if yt_id and yt_id not in combined_this_week:
            combined_this_week[yt_id] = v

    if combined_this_week:
        for v in sorted(combined_this_week.values(), key=lambda x: x.get("publish_at", "")):
            title    = v.get("title", "Untitled")
            yt_id    = v.get("youtube_id", "—")
            pub_at   = format_date(v.get("publish_at", v.get("published_at", "")))
            vtype    = v.get("type", "short").upper()
            url      = f"https://youtu.be/{yt_id}" if yt_id != "—" else "—"
            lines.append(f"- **[{vtype}]** {title}")
            lines.append(f"  - YouTube: {url}")
            lines.append(f"  - Publish: {pub_at}")
            lines.append("")
    else:
        lines.append("_No videos uploaded or scheduled for this week._")
        lines.append("")

    # ── Upcoming schedule ─────────────────────────────────────────────────────
    lines.append("## Upcoming Schedule")
    lines.append("")

    if upcoming:
        lines.append(f"| Date | Type | Title | YouTube |")
        lines.append(f"|------|------|-------|---------|")
        for v in upcoming[:20]:  # cap at 20 rows
            pub_at = format_date(v.get("publish_at", ""))
            vtype  = v.get("type", "short").upper()
            title  = v.get("title", "Untitled")[:50]
            yt_id  = v.get("youtube_id", "—")
            url    = f"[{yt_id}](https://youtu.be/{yt_id})" if yt_id != "—" else "—"
            lines.append(f"| {pub_at} | {vtype} | {title} | {url} |")
        lines.append("")
    else:
        lines.append("_No upcoming videos scheduled._")
        lines.append("")

    # ── Top performer ─────────────────────────────────────────────────────────
    lines.append("## Top Performing Video")
    lines.append("")
    if top_video:
        title  = top_video.get("title", "Unknown")
        yt_id  = top_video.get("youtube_id", top_video.get("id", "—"))
        views  = top_video.get("views", top_video.get("viewCount", 0))
        likes  = top_video.get("likes", top_video.get("likeCount", "—"))
        ctr    = top_video.get("ctr", top_video.get("ctr_pct", "—"))
        url    = f"https://youtu.be/{yt_id}" if yt_id != "—" else "—"

        lines.append(f"**{title}**")
        lines.append(f"- URL: {url}")
        lines.append(f"- Views: {views:,}" if isinstance(views, int) else f"- Views: {views}")
        lines.append(f"- Likes: {likes}")
        if ctr != "—":
            lines.append(f"- CTR: {ctr}%")
        lines.append("")
    else:
        lines.append("_No analytics data available. Run `python3 scripts/analytics_report.py --full` to fetch._")
        lines.append("")

    lines.append("---")
    lines.append("_FactForge Automation — auto-generated report_")

    return "\n".join(lines)


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 50)
    print("FactForge — Weekly Report")
    print("=" * 50 + "\n")

    report = build_report()
    print(report)

    # Save to state/
    today     = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_path  = STATE_DIR / f"weekly_report_{today}.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"\n✅ Report saved → {out_path}")


if __name__ == "__main__":
    main()
