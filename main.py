"""
FactForge YouTube Automation System — Main Orchestrator
Usage:
  python main.py                    → Show current status
  python main.py produce            → Produce next video in queue
  python main.py queue              → Show next 10 ideas
  python main.py generate-ideas     → Generate idea database
  python main.py refresh-trends     → Update trending topics
  python main.py improve            → Run self-improvement analysis
  python main.py add-idea "title"   → Add custom idea to queue top
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
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
from rich import print as rprint

console = Console()


# ─── Status Display ────────────────────────────────────────────────────────────

def show_status():
    """Display current system status."""
    progress = load_progress()
    queue = load_queue()

    ideas_short_path = DATABASE_DIR / "ideas_short.json"
    ideas_long_path = DATABASE_DIR / "ideas_long.json"
    used_path = DATABASE_DIR / "used_ideas.json"

    short_data = load_json(ideas_short_path)
    long_data = load_json(ideas_long_path)
    used_data = load_json(used_path)

    short_count = len(short_data.get("ideas", []))
    long_count = len(long_data.get("ideas", []))
    produced_count = used_data.get("total_produced", 0)

    console.print(Panel.fit("""
[bold cyan]FactForge YouTube Automation System[/bold cyan]
[dim]Educational facts channel — Islamic history, world stats, geopolitics[/dim]
""", border_style="cyan"))

    table = Table(show_header=False, box=None)
    table.add_column("Key", style="dim")
    table.add_column("Value", style="bold")

    table.add_row("Short ideas in DB", f"{short_count:,} / 10,000")
    table.add_row("Long ideas in DB", f"{long_count:,} / 500")
    table.add_row("Videos produced", str(produced_count))
    table.add_row("Ideas in queue", str(len(queue)))
    table.add_row("Last published", progress.get("last_published_at", "Never")[:10] if progress.get("last_published_at") else "Never")
    table.add_row("Next scheduled", progress.get("next_scheduled_publish", "Not set")[:16] if progress.get("next_scheduled_publish") else "Not set")

    current = progress.get("current_production", {})
    if current.get("idea_id"):
        table.add_row("In production", f"{current['idea_id']} — Step: {current.get('step', 'unknown')}")

    console.print(table)

    # Show phases status
    phases = progress.get("phases_completed", {})
    console.print("\n[dim]Phase completion:[/dim]")
    phase_map = {
        "phase_0_environment": "Phase 0: Environment",
        "phase_1_brain": "Phase 1: Brain & Skills",
        "phase_2_database": "Phase 2: Idea Database",
        "phase_3_pipeline_tested": "Phase 3: Pipeline Tested",
        "phase_4_self_improvement": "Phase 4: Self-Improvement",
    }
    for key, label in phase_map.items():
        status = "✓" if phases.get(key) else "○"
        color = "green" if phases.get(key) else "yellow"
        console.print(f"  [{color}]{status}[/{color}] {label}")


# ─── Queue Display ────────────────────────────────────────────────────────────

def show_queue():
    """Show next 10 ideas in the production queue."""
    queue = load_queue()

    if not queue:
        console.print("[yellow]Queue is empty. Run: python main.py generate-ideas[/yellow]")
        return

    console.print(f"\n[bold]Next {min(10, len(queue))} ideas in queue:[/bold]\n")
    table = Table()
    table.add_column("#", style="dim", width=3)
    table.add_column("ID", style="dim", width=7)
    table.add_column("Title", style="bold", width=55)
    table.add_column("Format", width=14)
    table.add_column("Priority", width=8)

    for i, idea in enumerate(queue[:10], 1):
        table.add_row(
            str(i),
            idea.get("id", "?"),
            idea.get("title", "?")[:55],
            idea.get("format", "?"),
            str(idea.get("priority_score", 0)),
        )

    console.print(table)


# ─── Production Pipeline ──────────────────────────────────────────────────────

def produce_next_video():
    """Run the full production pipeline on the next queued idea."""
    queue = load_queue()

    if not queue:
        console.print("[red]Queue is empty. Run: python main.py generate-ideas first.[/red]")
        return

    idea = queue[0]

    # Show idea and ask for confirmation
    console.print(f"\n[bold]Next idea to produce:[/bold]")
    console.print(f"  ID: {idea['id']}")
    console.print(f"  Title: {idea['title']}")
    console.print(f"  Format: {idea.get('format', 'unknown')}")
    console.print(f"  Category: {idea.get('category', 'unknown')}")
    console.print(f"  Priority: {idea.get('priority_score', 0)}")
    console.print(f"  Est. duration: {idea.get('estimated_duration_seconds', 55)}s")

    confirm = input("\nProduce this video? (yes/skip/quit): ").strip().lower()

    if confirm == "quit":
        return
    elif confirm == "skip":
        queue.pop(0)
        save_queue(queue)
        mark_idea_used(idea["id"], reason="skipped")
        console.print(f"[yellow]Skipped idea {idea['id']}[/yellow]")
        return
    elif confirm != "yes":
        console.print("[yellow]Cancelled[/yellow]")
        return

    # Run production pipeline
    _run_pipeline(idea, queue)


def _run_pipeline(idea: dict, queue: list):
    """Execute full production pipeline for one idea."""
    from agents import fact_check_agent, script_agent, voice_agent
    from agents import thumbnail_agent, video_agent, title_agent, publish_agent

    idea_id = idea["id"]
    output_dir = get_output_dir(idea_id)

    console.print(f"\n[bold cyan]Starting production pipeline for {idea_id}[/bold cyan]")
    console.print("─" * 50)

    # Step 1: Research & Fact Check
    console.print("\n[1/7] Researching and verifying facts...")
    research, publishable = fact_check_agent.run(idea)

    if not publishable:
        console.print(f"[red]SKIP: Insufficient verified facts for {idea_id}[/red]")
        queue.pop(0)
        save_queue(queue)
        mark_idea_used(idea_id, reason="skipped_unverifiable")
        return

    # Step 2: Script
    console.print("\n[2/7] Writing TTS-optimized script...")
    script_data = script_agent.run(idea, research)
    console.print(f"  Script: {script_data.get('word_count', '?')} words, ~{script_data.get('estimated_duration_seconds', '?')}s")

    # Step 3: Voice
    console.print("\n[3/7] Generating voice audio...")
    audio_path = voice_agent.run(idea, script_data)
    console.print(f"  Audio: {audio_path}")

    # Step 4: Thumbnail
    console.print("\n[4/7] Creating thumbnail...")
    thumbnail_path = thumbnail_agent.run(idea)
    console.print(f"  Thumbnail: {thumbnail_path}")

    # Step 5: Video
    console.print("\n[5/7] Rendering video...")
    video_path = video_agent.run(idea, script_data, audio_path)

    if not video_path or not video_path.exists():
        console.print("[red]Video render failed. Check Remotion logs.[/red]")
        console.print(f"[yellow]Partial output saved to: {output_dir}[/yellow]")
        return

    # Step 6: Metadata
    console.print("\n[6/7] Generating titles, descriptions, translations...")
    metadata = title_agent.run(idea, script_data, research)
    console.print(f"  Selected title: {metadata.get('selected_title', '?')[:70]}")

    # Step 7: Publish
    console.print("\n[7/7] Uploading to YouTube...")
    confirm_publish = input("Upload to YouTube now? (yes/later): ").strip().lower()

    if confirm_publish == "yes":
        youtube_id = publish_agent.run(idea, metadata)
        if youtube_id:
            console.print(f"\n[bold green]✓ Published! https://youtu.be/{youtube_id}[/bold green]")
            queue.pop(0)
            save_queue(queue)
        else:
            console.print("[red]Upload failed. Files saved locally.[/red]")
    else:
        console.print(f"\n[yellow]Video saved locally at: {output_dir}[/yellow]")
        console.print("Run again and choose 'yes' to upload when ready.")
        queue.pop(0)
        save_queue(queue)
        mark_idea_used(idea_id, reason="produced_not_published")

    console.print("\n[bold green]Production complete![/bold green]")


# ─── Idea Generation ──────────────────────────────────────────────────────────

def generate_ideas():
    """Generate the full idea database (10,000 short + 500 long)."""
    import idea_generator
    idea_generator.run()


def add_idea(title: str):
    """Add a custom idea to the top of the production queue."""
    queue = load_queue()

    # Create a minimal idea object
    idea = {
        "id": f"C{len(queue) + 1:05d}",  # Custom ideas get C prefix
        "title": title,
        "angle": "custom",
        "format": "shocking_stat",
        "hook": title,
        "controversy_score": 70,
        "trending_score": 80,
        "evergreen_score": 70,
        "priority_score": 90,  # Custom ideas get high priority
        "estimated_duration_seconds": 52,
        "key_facts": [],
        "sources": [],
        "status": "pending",
        "category": "general",
    }

    queue.insert(0, idea)
    save_queue(queue)
    console.print(f"[green]Added custom idea to top of queue: {title}[/green]")


# ─── Main Entry Point ─────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]

    if not args:
        show_status()
        return

    command = args[0].lower()

    if command == "produce":
        produce_next_video()
    elif command == "queue":
        show_queue()
    elif command == "generate-ideas":
        generate_ideas()
    elif command == "refresh-trends":
        from agents import trend_agent
        trend_agent.main()
    elif command == "improve":
        from agents import improvement_agent
        improvement_agent.run()
    elif command == "add-idea":
        if len(args) < 2:
            console.print("[red]Usage: python main.py add-idea \"Your idea title\"[/red]")
        else:
            add_idea(" ".join(args[1:]))
    elif command in ("status", "help"):
        show_status()
    else:
        console.print(f"[red]Unknown command: {command}[/red]")
        console.print("Commands: produce, queue, generate-ideas, refresh-trends, improve, add-idea")


if __name__ == "__main__":
    main()
