"""
Improvement Agent — Collects analytics and prepares improvement report for Claude Code.
Claude Code reads the report and writes actionable updates.
Run: python agents/improvement_agent.py
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import DATABASE_DIR, STATE_DIR
from utils.file_manager import load_json, save_json, log_improvement, now_utc


def fetch_youtube_analytics(youtube_service, video_ids: list) -> list[dict]:
    """Fetch video statistics from YouTube API."""
    if not video_ids:
        return []
    try:
        response = youtube_service.videos().list(
            part="statistics,snippet",
            id=",".join(video_ids[:50]),
        ).execute()
        results = []
        for item in response.get("items", []):
            stats = item.get("statistics", {})
            results.append({
                "youtube_id": item["id"],
                "title": item["snippet"]["title"],
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "fetched_at": now_utc(),
            })
        return results
    except Exception as e:
        print(f"[improvement_agent] Analytics error: {e}")
        return []


def build_analysis_report(analytics_data: list[dict]) -> dict:
    """
    Build analytics report for Claude Code to analyze.
    Claude Code reads this and writes improvement recommendations.
    """
    if not analytics_data:
        return {"status": "no_data"}

    sorted_videos = sorted(analytics_data, key=lambda x: x.get("views", 0), reverse=True)
    top5 = sorted_videos[:5]
    bottom5 = sorted_videos[-5:] if len(sorted_videos) >= 5 else sorted_videos

    total_views = sum(v.get("views", 0) for v in analytics_data)
    avg_views = total_views // len(analytics_data) if analytics_data else 0

    report = {
        "generated_at": now_utc(),
        "total_videos": len(analytics_data),
        "total_views": total_views,
        "average_views": avg_views,
        "top_5_videos": [{"title": v["title"], "views": v["views"]} for v in top5],
        "bottom_5_videos": [{"title": v["title"], "views": v["views"]} for v in bottom5],
        "claude_code_task": {
            "instruction": (
                "Analyze this performance data. Identify: "
                "1) What title/topic patterns correlate with high views? "
                "2) What should be produced more of? "
                "3) What changes to make to scripts, thumbnails, titles? "
                "Write your analysis to state/improvement_analysis.json"
            ),
            "output_schema": {
                "top_performing_patterns": ["pattern"],
                "low_performing_patterns": ["pattern"],
                "recommended_categories": ["category"],
                "title_formula_insights": ["insight"],
                "action_items": ["action"],
                "priority_score_adjustments": {"category": "+10 or -5"}
            }
        }
    }

    return report


def apply_priority_adjustments(adjustments: dict) -> None:
    """Apply Claude Code's recommended priority score adjustments to ideas database."""
    ideas_path = DATABASE_DIR / "ideas_short.json"
    if not ideas_path.exists() or not adjustments:
        return

    ideas_data = load_json(ideas_path)
    ideas = ideas_data.get("ideas", [])
    updated = 0

    for idea in ideas:
        if idea.get("status") != "pending":
            continue
        category = idea.get("category", "")
        for cat_key, adjustment in adjustments.items():
            if cat_key.lower() in category.lower():
                delta = int(str(adjustment).replace("+", "").replace(" ", ""))
                idea["priority_score"] = max(0, min(100, idea.get("priority_score", 50) + delta))
                updated += 1
                break

    if updated:
        save_json(ideas_path, ideas_data)
        print(f"[improvement_agent] Updated priority scores for {updated} ideas")


def write_weekly_log(report: dict, analysis: dict = None) -> None:
    """Append weekly improvement report to log."""
    today = now_utc()[:10]
    top = report.get("top_5_videos", [])
    top_str = "\n".join([f"- '{v['title'][:50]}': {v['views']:,} views" for v in top]) or "No data"

    actions = []
    if analysis:
        actions = analysis.get("action_items", [])

    entry = f"""
## {today} Weekly Improvement Report

### Channel Stats
- Total videos: {report.get('total_videos', 0)}
- Total views: {report.get('total_views', 0):,}
- Average views per video: {report.get('average_views', 0):,}

### Top Performing Videos
{top_str}

### Actions Taken
{chr(10).join(['- ' + a for a in actions]) if actions else '- Pending Claude Code analysis'}
"""
    log_improvement(entry)


def run(youtube_service=None) -> None:
    """Main entry point."""
    print("[improvement_agent] Collecting analytics...")

    used = load_json(DATABASE_DIR / "used_ideas.json")
    youtube_ids = [v.get("youtube_id") for v in used.get("produced_ideas", []) if v.get("youtube_id")]

    analytics_data = []
    if youtube_service and youtube_ids:
        analytics_data = fetch_youtube_analytics(youtube_service, youtube_ids)

    # Load existing + merge
    state = load_json(STATE_DIR / "analytics.json")
    existing_ids = {v["youtube_id"] for v in state.get("videos", [])}
    new = [v for v in analytics_data if v["youtube_id"] not in existing_ids]
    state["videos"] = state.get("videos", []) + new
    state["last_updated"] = now_utc()
    save_json(STATE_DIR / "analytics.json", state)

    all_videos = state.get("videos", [])
    report = build_analysis_report(all_videos)

    # Save report for Claude Code to read
    report_path = STATE_DIR / "improvement_report.json"
    save_json(report_path, report)
    print(f"[improvement_agent] Report saved: {report_path}")

    # Check if Claude Code wrote an analysis
    analysis_path = STATE_DIR / "improvement_analysis.json"
    analysis = load_json(analysis_path) if analysis_path.exists() else {}

    if analysis.get("priority_score_adjustments"):
        apply_priority_adjustments(analysis["priority_score_adjustments"])

    write_weekly_log(report, analysis)

    print(f"""
[improvement_agent] Report ready.

Claude Code: Read state/improvement_report.json and write state/improvement_analysis.json
with patterns, recommendations, and priority_score_adjustments.
""")


if __name__ == "__main__":
    run()
