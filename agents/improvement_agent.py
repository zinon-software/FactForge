"""
Improvement Agent — Analyzes YouTube analytics and updates the system.
Run weekly via: python agents/improvement_agent.py
"""

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import anthropic
from config.settings import ANTHROPIC_API_KEY, CLAUDE_MODEL_MAIN, DATABASE_DIR, STATE_DIR
from utils.file_manager import load_json, save_json, log_improvement, now_utc


def fetch_youtube_analytics(youtube_service, video_ids: list) -> list[dict]:
    """Fetch performance metrics for published videos."""
    if not video_ids:
        return []

    try:
        from googleapiclient.discovery import build

        # Get video statistics
        stats_response = youtube_service.videos().list(
            part="statistics,snippet",
            id=",".join(video_ids[:50]),
        ).execute()

        results = []
        for item in stats_response.get("items", []):
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
        print(f"[improvement_agent] Analytics fetch error: {e}")
        return []


def analyze_performance(analytics_data: list[dict]) -> dict:
    """Analyze patterns in performance data using Claude."""
    if not analytics_data:
        return {"status": "no_data", "insights": []}

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Format analytics for analysis
    videos_summary = "\n".join([
        f"- '{v['title'][:50]}': {v['views']} views, {v['likes']} likes"
        for v in sorted(analytics_data, key=lambda x: x['views'], reverse=True)[:20]
    ])

    prompt = f"""Analyze this YouTube channel performance data and identify patterns.

VIDEOS (sorted by views):
{videos_summary}

Identify:
1. What topics/formats get the most views?
2. What title patterns correlate with high performance?
3. What should we produce more of?
4. What should we do less of?

Output JSON:
{{
  "top_performing_patterns": ["pattern 1", "pattern 2"],
  "low_performing_patterns": ["pattern 1"],
  "recommended_categories": ["category 1", "category 2"],
  "title_formula_insights": ["insight 1"],
  "action_items": ["action 1", "action 2"]
}}"""

    response = client.messages.create(
        model=CLAUDE_MODEL_MAIN,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    try:
        if "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
            if raw.startswith("json"):
                raw = raw[4:].strip()
        return json.loads(raw)
    except Exception:
        return {"raw_analysis": raw, "status": "parsed_error"}


def update_idea_priorities(analysis: dict) -> None:
    """Adjust priority scores in ideas database based on analysis."""
    recommended = analysis.get("recommended_categories", [])
    if not recommended:
        return

    ideas_path = DATABASE_DIR / "ideas_short.json"
    if not ideas_path.exists():
        return

    ideas_data = load_json(ideas_path)
    ideas = ideas_data.get("ideas", [])

    boosted = 0
    for idea in ideas:
        if idea.get("status") != "pending":
            continue
        category = idea.get("category", "")
        angle = idea.get("angle", "")
        combined = f"{category} {angle}".lower()

        for rec in recommended:
            if rec.lower() in combined:
                old_score = idea.get("priority_score", 50)
                idea["priority_score"] = min(100, old_score + 10)
                boosted += 1
                break

    if boosted > 0:
        save_json(ideas_path, ideas_data)
        print(f"[improvement_agent] Boosted priority for {boosted} ideas")


def write_weekly_report(analytics_data: list, analysis: dict) -> None:
    """Append weekly report to improvement_log.md"""
    today = now_utc()[:10]
    total_views = sum(v.get("views", 0) for v in analytics_data)

    top_video = max(analytics_data, key=lambda x: x.get("views", 0)) if analytics_data else None

    report = f"""
## {today} Weekly Improvement Report

### Performance Summary
- Videos analyzed: {len(analytics_data)}
- Total views (all time): {total_views:,}
- Top video: {top_video['title'][:60] if top_video else 'N/A'} ({top_video.get('views', 0):,} views)

### What Worked
{chr(10).join(['- ' + p for p in analysis.get('top_performing_patterns', ['No data yet'])])}

### What Didn't Work
{chr(10).join(['- ' + p for p in analysis.get('low_performing_patterns', ['No data yet'])])}

### System Changes Made
{chr(10).join(['- ' + a for a in analysis.get('action_items', ['No actions taken'])])}

### Next Week Focus
- Prioritized categories: {', '.join(analysis.get('recommended_categories', ['general']))}
"""

    log_improvement(report)
    print(f"[improvement_agent] Weekly report written to improvement_log.md")


def run(youtube_service=None) -> None:
    """Main entry point: run full weekly improvement cycle."""
    print("[improvement_agent] Starting weekly improvement analysis...")

    # Load published video IDs from used_ideas.json
    used = load_json(DATABASE_DIR / "used_ideas.json")
    produced = used.get("produced_ideas", [])
    youtube_ids = [v.get("youtube_id") for v in produced if v.get("youtube_id")]

    if not youtube_ids:
        print("[improvement_agent] No published videos yet — nothing to analyze")
        return

    # Fetch analytics
    analytics_data = []
    if youtube_service:
        analytics_data = fetch_youtube_analytics(youtube_service, youtube_ids)

    # Load existing analytics and merge
    analytics_state = load_json(STATE_DIR / "analytics.json")
    existing_ids = {v["youtube_id"] for v in analytics_state.get("videos", [])}
    new_data = [v for v in analytics_data if v["youtube_id"] not in existing_ids]

    analytics_state["videos"] = analytics_state.get("videos", []) + new_data
    analytics_state["last_updated"] = now_utc()
    analytics_state["channel_totals"]["total_views"] = sum(
        v.get("views", 0) for v in analytics_state["videos"]
    )
    save_json(STATE_DIR / "analytics.json", analytics_state)

    # Analyze patterns
    all_videos = analytics_state.get("videos", [])
    analysis = analyze_performance(all_videos)

    # Update idea priorities
    update_idea_priorities(analysis)

    # Write report
    write_weekly_report(all_videos, analysis)

    print("[improvement_agent] Done.")


if __name__ == "__main__":
    run()
