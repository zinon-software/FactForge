"""
FactForge YouTube Automation System — Main Orchestrator

Claude Code IS the AI engine. No Anthropic API key needed.
Claude Code handles all intelligence. Python handles automation.

Usage:
  python main.py                    → Show current status
  python main.py produce            → Interactive production session with Claude Code
  python main.py queue              → Show next 10 ideas
  python main.py generate-ideas     → Start idea generation (Claude Code fills them in)
  python main.py refresh-trends     → Update trending topics
  python main.py improve            → Run self-improvement analysis
  python main.py add-idea "title"   → Add custom idea to top of queue
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from config.settings import DATABASE_DIR, STATE_DIR, OUTPUT_DIR
from utils.file_manager import (
    load_json, save_json, load_progress, save_progress,
    load_queue, save_queue, mark_idea_used, get_output_dir, now_utc
)
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich import print as rprint

console = Console()


# ─── Status ────────────────────────────────────────────────────────────────────

def show_status():
    progress = load_progress()
    queue = load_queue()

    short_data = load_json(DATABASE_DIR / "ideas_short.json")
    long_data = load_json(DATABASE_DIR / "ideas_long.json")
    used_data = load_json(DATABASE_DIR / "used_ideas.json")

    short_count = len(short_data.get("ideas", []))
    long_count = len(long_data.get("ideas", []))
    produced_count = used_data.get("total_produced", 0)

    console.print(Panel.fit("""
[bold cyan]FactForge YouTube Automation System[/bold cyan]
[dim]AI Engine: Claude Code (this session) — No API key needed[/dim]
""", border_style="cyan"))

    table = Table(show_header=False, box=None)
    table.add_column("Key", style="dim")
    table.add_column("Value", style="bold")
    table.add_row("Short ideas in DB", f"{short_count:,} / 10,000")
    table.add_row("Long ideas in DB", f"{long_count:,} / 500")
    table.add_row("Videos produced", str(produced_count))
    table.add_row("Ideas in queue", str(len(queue)))
    table.add_row("Last published", progress.get("last_published_at", "Never")[:10] if progress.get("last_published_at") else "Never")
    table.add_row("AI engine", "Claude Code (active session)")
    console.print(table)

    phases = progress.get("phases_completed", {})
    console.print("\n[dim]Phase completion:[/dim]")
    for key, label in [
        ("phase_0_environment", "Phase 0: Environment"),
        ("phase_1_brain", "Phase 1: Brain & Skills"),
        ("phase_2_database", "Phase 2: Idea Database"),
        ("phase_3_pipeline_tested", "Phase 3: Pipeline Tested"),
        ("phase_4_self_improvement", "Phase 4: Self-Improvement"),
    ]:
        icon = "✓" if phases.get(key) else "○"
        color = "green" if phases.get(key) else "yellow"
        console.print(f"  [{color}]{icon}[/{color}] {label}")


# ─── Queue ─────────────────────────────────────────────────────────────────────

def show_queue():
    queue = load_queue()
    if not queue:
        console.print("[yellow]Queue empty. Run: python main.py generate-ideas[/yellow]")
        return

    console.print(f"\n[bold]Next {min(10, len(queue))} ideas:[/bold]\n")
    table = Table()
    table.add_column("#", width=3)
    table.add_column("ID", width=8)
    table.add_column("Title", width=55)
    table.add_column("Format", width=14)
    table.add_column("Priority", width=8)
    for i, idea in enumerate(queue[:10], 1):
        table.add_row(
            str(i), idea.get("id", "?"),
            idea.get("title", "?")[:55],
            idea.get("format", "?"),
            str(idea.get("priority_score", 0))
        )
    console.print(table)


# ─── Interactive Production (Claude Code handles AI steps) ─────────────────────

def produce_next_video():
    """
    Full production session. Python does automation; Claude Code does AI.
    Claude Code reads each request file and fills in the response interactively.
    """
    queue = load_queue()
    if not queue:
        console.print("[red]Queue empty. Run: python main.py generate-ideas first.[/red]")
        return

    idea = queue[0]
    _display_idea(idea)

    confirm = input("\nProduce this video? (yes/skip/quit): ").strip().lower()
    if confirm == "quit":
        return
    elif confirm == "skip":
        queue.pop(0)
        save_queue(queue)
        mark_idea_used(idea["id"], reason="skipped")
        console.print(f"[yellow]Skipped {idea['id']}[/yellow]")
        return
    elif confirm != "yes":
        return

    _run_pipeline(idea, queue)


def _display_idea(idea: dict):
    console.print(f"\n[bold]Next idea to produce:[/bold]")
    table = Table(show_header=False, box=None)
    table.add_column("", style="dim")
    table.add_column("", style="bold")
    table.add_row("ID", idea["id"])
    table.add_row("Title", idea["title"])
    table.add_row("Format", idea.get("format", "?"))
    table.add_row("Category", idea.get("category", "?"))
    table.add_row("Hook", idea.get("hook", "?")[:70])
    table.add_row("Duration", f"{idea.get('estimated_duration_seconds', 55)}s")
    table.add_row("Priority", str(idea.get("priority_score", 0)))
    console.print(table)


def _show_request(title: str, path: Path):
    """Display a request file for Claude Code to read."""
    console.print(f"\n[bold yellow]━━ {title} ━━[/bold yellow]")
    console.print(f"[dim]File: {path}[/dim]\n")
    data = load_json(path)
    console.print(Syntax(
        json.dumps(data, indent=2, ensure_ascii=False),
        "json", theme="monokai", line_numbers=False
    ))


def _wait_for_response(prompt_msg: str, response_path: Path, schema_keys: list[str]) -> dict | None:
    """
    Show a prompt to Claude Code and wait for the user to paste/confirm the response.
    Claude Code reads the request, generates response, and we save it.
    """
    console.print(f"\n[bold cyan]━━ Claude Code Task ━━[/bold cyan]")
    console.print(f"[white]{prompt_msg}[/white]")
    console.print(f"\n[dim]Expected keys: {', '.join(schema_keys)}[/dim]")
    console.print(f"[dim]Save response to: {response_path}[/dim]\n")

    # Check if Claude Code already wrote the file
    if response_path.exists():
        data = load_json(response_path)
        if data and any(k in data for k in schema_keys):
            console.print(f"[green]✓ Response already saved[/green]")
            return data

    console.print("[dim]Press Enter once Claude Code has written the response file...[/dim]")
    input()

    if response_path.exists():
        return load_json(response_path)
    else:
        console.print(f"[red]Response file not found: {response_path}[/red]")
        return None


def _run_pipeline(idea: dict, queue: list):
    """Full production pipeline — Claude Code handles all AI steps."""
    from agents import fact_check_agent, script_agent, voice_agent
    from agents import thumbnail_agent, video_agent, title_agent, publish_agent
    from agents.script_agent import process_script_response, save_script
    from agents.title_agent import save_metadata

    idea_id = idea["id"]
    output_dir = get_output_dir(idea_id)

    console.print(f"\n[bold cyan]Production Pipeline: {idea_id}[/bold cyan]")
    console.print("─" * 55)

    # ── Step 1: Research ────────────────────────────────────────────
    console.print("\n[1/7] [bold]Fact Research[/bold] — searching web...")
    fact_check_agent.run(idea)

    request_path = output_dir / "research_request.json"
    _show_request("RESEARCH REQUEST — Claude Code: verify these facts", request_path)

    research_path = output_dir / "research.json"
    console.print(f"""
[bold yellow]Claude Code:[/bold yellow] Read the research request above.
1. Review each search result
2. Verify the key facts from official sources
3. Write [bold]output/{idea_id}/research.json[/bold] with this structure:
   {{
     "verified_facts": [{{"claim": "...", "sources": [{{"url": "..."}}], "confidence": "high"}}],
     "unverified_claims": [],
     "overall_confidence": "high",
     "publishable": true
   }}
""")

    research = _wait_for_response(
        "Write research.json with verified facts",
        research_path,
        ["verified_facts", "publishable"]
    )

    if not research or not research.get("publishable", True):
        console.print("[red]Skipping — insufficient verified facts[/red]")
        queue.pop(0)
        save_queue(queue)
        mark_idea_used(idea_id, reason="skipped_unverifiable")
        return

    console.print(f"[green]✓ {len(research.get('verified_facts', []))} facts verified[/green]")

    # ── Step 2: Script ─────────────────────────────────────────────
    console.print("\n[2/7] [bold]Script Writing[/bold]...")
    script_agent.run(idea, research)

    request_path = output_dir / "script_request.json"
    _show_request("SCRIPT REQUEST — Claude Code: write the script", request_path)

    script_path = output_dir / "script.json"
    console.print(f"""
[bold yellow]Claude Code:[/bold yellow] Read write_script.md skill, then write [bold]output/{idea_id}/script.json[/bold]:
   {{
     "hook": "First shocking sentence",
     "build_up": "Build-up with [PAUSE] tags",
     "peak": "[SLOW] Most shocking fact [PAUSE]",
     "cta": "Follow for more facts...",
     "full_script": "Complete script",
     "word_count": 140,
     "estimated_duration_seconds": 52
   }}
""")

    raw_script = _wait_for_response(
        "Write script.json",
        script_path,
        ["full_script", "hook"]
    )

    if not raw_script:
        return

    script_data = process_script_response(idea, raw_script)
    save_script(idea_id, script_data)
    console.print(f"[green]✓ Script: {script_data.get('word_count', '?')} words[/green]")

    # ── Step 3: Voice ──────────────────────────────────────────────
    console.print("\n[3/7] [bold]Voice Generation[/bold]...")
    audio_path = voice_agent.run(idea, script_data)
    console.print(f"[green]✓ Audio: {audio_path}[/green]")

    # ── Step 4: Thumbnail ──────────────────────────────────────────
    console.print("\n[4/7] [bold]Thumbnail[/bold]...")
    thumbnail_path = thumbnail_agent.run(idea)
    console.print(f"[green]✓ Thumbnail: {thumbnail_path}[/green]")

    # ── Step 5: Video ──────────────────────────────────────────────
    console.print("\n[5/7] [bold]Video Rendering[/bold] (Remotion)...")
    video_path = video_agent.run(idea, script_data, audio_path)

    if not video_path or not video_path.exists():
        console.print("[red]Video render failed. Check Remotion.[/red]")
        return

    console.print(f"[green]✓ Video: {video_path}[/green]")

    # ── Step 6: Metadata ───────────────────────────────────────────
    console.print("\n[6/7] [bold]Titles, Description & Translations[/bold]...")
    title_agent.run(idea, script_data, research)

    request_path = output_dir / "metadata_request.json"
    _show_request("METADATA REQUEST — Claude Code: generate titles + translations", request_path)

    metadata_path = output_dir / "metadata.json"
    console.print(f"""
[bold yellow]Claude Code:[/bold yellow] Read generate_title.md skill, then write [bold]output/{idea_id}/metadata.json[/bold]:
   {{
     "title_variants": [{{"title": "...", "score": 85}}],
     "selected_title": "Best title",
     "description": "Full YouTube description...",
     "tags": ["tag1", "tag2"],
     "translations": {{"es": {{"title": "...", "description": "..."}}, "ar": {{...}}, ...}},
     "category_id": "27"
   }}
Translate title+description into: Spanish, French, German, Hindi, Portuguese,
Indonesian, Japanese, Korean, Turkish, Arabic
""")

    raw_metadata = _wait_for_response(
        "Write metadata.json with titles + 10 language translations",
        metadata_path,
        ["selected_title", "description"]
    )

    if not raw_metadata:
        return

    metadata = save_metadata(idea_id, raw_metadata)
    if isinstance(metadata, Path):
        metadata = load_json(metadata)

    console.print(f"[green]✓ Title: {metadata.get('selected_title', '?')[:70]}[/green]")

    # ── Step 7: Publish ────────────────────────────────────────────
    console.print("\n[7/7] [bold]Publishing to YouTube[/bold]...")
    confirm_pub = input("Upload to YouTube now? (yes/later): ").strip().lower()

    if confirm_pub == "yes":
        youtube_id = publish_agent.run(idea, metadata)
        if youtube_id:
            console.print(f"\n[bold green]✓ Published! https://youtu.be/{youtube_id}[/bold green]")
            queue.pop(0)
            save_queue(queue)
        else:
            console.print("[red]Upload failed. Files saved locally.[/red]")
    else:
        console.print(f"[yellow]Files ready at: {output_dir}[/yellow]")
        queue.pop(0)
        save_queue(queue)
        mark_idea_used(idea_id, reason="produced_not_published")

    console.print("\n[bold green]Production complete![/bold green]")


# ─── Idea Generation ───────────────────────────────────────────────────────────

def generate_ideas():
    """
    Idea generation guided by Claude Code.
    Claude Code generates batches of ideas; Python saves them.
    """
    from config.settings import CONTENT_CATEGORIES, BATCH_SIZE, TARGET_SHORT_IDEAS

    short_data = load_json(DATABASE_DIR / "ideas_short.json")
    existing_count = len(short_data.get("ideas", []))
    remaining = TARGET_SHORT_IDEAS - existing_count

    if remaining <= 0:
        console.print(f"[green]Database complete: {existing_count:,} ideas[/green]")
        return

    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    console.print(Panel.fit(f"""
[bold]Idea Database Generation[/bold]
Target: 10,000 short + 500 long ideas
Already have: {existing_count:,}
Need: {remaining:,} more
Method: Claude Code generates in batches of {BATCH_SIZE}
""", border_style="cyan"))

    num_batches = (remaining + BATCH_SIZE - 1) // BATCH_SIZE
    categories = CONTENT_CATEGORIES

    for batch_num in range(1, num_batches + 1):
        batch_size = min(BATCH_SIZE, remaining - (batch_num - 1) * BATCH_SIZE)
        if batch_size <= 0:
            break

        start_id = existing_count + (batch_num - 1) * BATCH_SIZE + 1
        batch_categories = categories[(batch_num - 1) % len(categories):][:3]

        console.print(f"\n[bold]Batch {batch_num}/{num_batches}[/bold] — {batch_size} ideas")
        console.print(f"Categories: {', '.join(batch_categories)}")
        console.print(f"ID range: S{start_id:05d} to S{start_id + batch_size - 1:05d}")

        batch_request = {
            "task_type": "ideas",
            "batch_num": batch_num,
            "batch_size": batch_size,
            "start_id": start_id,
            "categories": batch_categories,
            "existing_count": existing_count + (batch_num - 1) * BATCH_SIZE,
        }

        batch_path = STATE_DIR / "claude_tasks" / f"ideas_batch_{batch_num:03d}" / "request.json"
        batch_path.parent.mkdir(parents=True, exist_ok=True)
        save_json(batch_path, batch_request)

        console.print(f"""
[bold yellow]Claude Code:[/bold yellow] Generate {batch_size} ideas and write them to:
  [bold]database/ideas_batch_{batch_num:03d}.json[/bold]

Format: JSON array of idea objects:
  {{
    "id": "S{start_id:05d}",
    "title": "Compelling video title",
    "angle": "islamic_history|shocking_stats|geopolitical_comparison",
    "format": "shocking_stat|comparison|top_10_list|...",
    "category": "{batch_categories[0]}",
    "hook": "Most shocking single sentence",
    "controversy_score": 80,
    "trending_score": 65,
    "evergreen_score": 90,
    "priority_score": 77,
    "estimated_duration_seconds": 52,
    "key_facts": ["fact 1", "fact 2"],
    "sources": ["World Bank", "Britannica"],
    "status": "pending",
    "produced_date": null,
    "youtube_id": null,
    "views": null,
    "ctr": null
  }}
""")

        input(f"Press Enter once batch {batch_num} is written...")

        # Load and merge the batch
        batch_file = DATABASE_DIR / f"ideas_batch_{batch_num:03d}.json"
        if batch_file.exists():
            batch_data = load_json(batch_file)
            new_ideas = batch_data if isinstance(batch_data, list) else batch_data.get("ideas", [])

            # Merge into main ideas file
            if not (DATABASE_DIR / "ideas_short.json").exists():
                save_json(DATABASE_DIR / "ideas_short.json", {"ideas": [], "created": now_utc()})

            main_data = load_json(DATABASE_DIR / "ideas_short.json")
            main_data["ideas"].extend(new_ideas)
            main_data["total"] = len(main_data["ideas"])
            main_data["last_updated"] = now_utc()
            save_json(DATABASE_DIR / "ideas_short.json", main_data)

            # Clean up batch file
            batch_file.unlink()
            console.print(f"[green]✓ Batch {batch_num}: {len(new_ideas)} ideas saved (total: {main_data['total']})[/green]")
        else:
            console.print(f"[yellow]Batch file not found — skipping batch {batch_num}[/yellow]")

    # Build priority queue
    console.print("\n[bold]Building priority queue...[/bold]")
    final_data = load_json(DATABASE_DIR / "ideas_short.json")
    all_ideas = final_data.get("ideas", [])
    pending = [i for i in all_ideas if i.get("status") == "pending"]
    queue = sorted(pending, key=lambda x: x.get("priority_score", 0), reverse=True)[:100]
    save_queue(queue)

    progress = load_progress()
    progress["phases_completed"]["phase_2_database"] = True
    progress["database_stats"]["short_ideas_count"] = len(all_ideas)
    save_progress(progress)

    console.print(f"[bold green]✓ Done! {len(all_ideas):,} ideas in database, top {len(queue)} in queue[/bold green]")


# ─── Add Custom Idea ───────────────────────────────────────────────────────────

def add_idea(title: str):
    queue = load_queue()
    idea = {
        "id": f"C{len(queue) + 1:05d}",
        "title": title,
        "angle": "custom",
        "format": "shocking_stat",
        "hook": title,
        "controversy_score": 70,
        "trending_score": 80,
        "evergreen_score": 70,
        "priority_score": 90,
        "estimated_duration_seconds": 52,
        "key_facts": [],
        "sources": [],
        "status": "pending",
        "category": "general",
    }
    queue.insert(0, idea)
    save_queue(queue)
    console.print(f"[green]Added to top of queue: {title}[/green]")


# ─── Entry Point ───────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    if not args:
        show_status()
        return

    cmd = args[0].lower()
    if cmd == "produce":
        produce_next_video()
    elif cmd == "queue":
        show_queue()
    elif cmd == "generate-ideas":
        generate_ideas()
    elif cmd == "refresh-trends":
        from agents import trend_agent
        trend_agent.main()
    elif cmd == "improve":
        from agents import improvement_agent
        improvement_agent.run()
    elif cmd == "add-idea":
        if len(args) < 2:
            console.print('[red]Usage: python main.py add-idea "Your idea title"[/red]')
        else:
            add_idea(" ".join(args[1:]))
    else:
        show_status()


if __name__ == "__main__":
    main()
