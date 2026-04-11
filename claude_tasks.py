"""
Claude Tasks Processor — Run this to see and process pending AI tasks.

Usage:
  python claude_tasks.py          → List all pending tasks
  python claude_tasks.py process  → Process next pending task (interactive)
  python claude_tasks.py watch    → Auto-process tasks as they arrive

Claude Code runs this and fills in the AI responses directly.
No API calls — Claude Code IS the AI.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.claude_bridge import list_pending_tasks, get_task, respond, TASKS_DIR
from utils.file_manager import load_json, save_json
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich import print as rprint

console = Console()


def show_pending():
    tasks = list_pending_tasks()
    if not tasks:
        console.print("[green]No pending tasks — all clear.[/green]")
        return

    console.print(f"\n[bold yellow]{len(tasks)} pending task(s):[/bold yellow]\n")
    for t in tasks:
        console.print(f"  [{t['task_type'].upper()}] {t['task_id']}  —  created {t['created_at'][:16]}")


def process_task(task_id: str):
    """Display a task so Claude Code can read and respond to it."""
    task = get_task(task_id)
    if not task:
        console.print(f"[red]Task {task_id} not found[/red]")
        return

    console.print(Panel.fit(
        f"[bold]Task:[/bold] {task['task_id']}\n"
        f"[bold]Type:[/bold] {task['task_type']}\n"
        f"[bold]Created:[/bold] {task['created_at']}",
        title="Claude Task",
        border_style="cyan"
    ))

    console.print("\n[bold]Payload:[/bold]")
    console.print(Syntax(
        json.dumps(task["payload"], indent=2, ensure_ascii=False),
        "json",
        theme="monokai"
    ))

    console.print("\n[dim]Claude Code should now read this task, generate the response, and write it using:[/dim]")
    console.print(f'[bold cyan]python claude_tasks.py write {task_id} \'{{...response json...}}\'[/bold cyan]')


def write_response(task_id: str, response_json: str):
    """Write Claude's response for a task."""
    try:
        data = json.loads(response_json)
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON: {e}[/red]")
        return

    respond(task_id, data)
    console.print(f"[green]✓ Response written for task {task_id}[/green]")


def watch_mode():
    """Watch for new tasks and display them as they arrive."""
    import time
    console.print("[bold cyan]Watching for tasks... (Ctrl+C to stop)[/bold cyan]")
    seen = set()

    while True:
        tasks = list_pending_tasks()
        for t in tasks:
            if t["task_id"] not in seen:
                seen.add(t["task_id"])
                console.print(f"\n[yellow]New task: {t['task_id']} ({t['task_type']})[/yellow]")
                process_task(t["task_id"])
        time.sleep(2)


# ─── Built-in task handlers ────────────────────────────────────────────────────
# These are called by main.py when running interactively with Claude Code.
# Claude Code reads the payload and writes the response directly.

def handle_research_task(idea: dict, search_results: list) -> dict:
    """
    Claude Code processes this: reads idea + search results,
    extracts and verifies facts, returns research.json structure.
    """
    return {
        "task_type": "research",
        "idea_id": idea["id"],
        "idea_title": idea["title"],
        "key_facts_to_verify": idea.get("key_facts", []),
        "search_results": search_results,
        "instructions": (
            "Read the idea and search results. "
            "Extract and verify the key facts. "
            "Return verified_facts list with sources. "
            "Mark overall publishable: true/false."
        )
    }


def handle_script_task(idea: dict, research: dict) -> dict:
    """Claude Code writes the TTS-optimized script."""
    return {
        "task_type": "script",
        "idea": idea,
        "research": research,
        "skill_file": ".claude/skills/write_script.md",
        "instructions": (
            "Read write_script.md skill. "
            "Write a TTS-optimized short video script. "
            "Return: hook, build_up, peak, cta, full_script, word_count, estimated_duration_seconds."
        )
    }


def handle_titles_task(idea: dict, script_data: dict, research: dict) -> dict:
    """Claude Code generates titles, description, tags."""
    return {
        "task_type": "titles",
        "idea": idea,
        "hook": script_data.get("hook", ""),
        "verified_facts": research.get("verified_facts", []),
        "skill_file": ".claude/skills/generate_title.md",
        "instructions": (
            "Generate 5 title variants scored per generate_title.md. "
            "Write full YouTube description with sources and CTA. "
            "Generate 30 tags. Return: title_variants, selected_title, description, tags."
        )
    }


def handle_translate_task(title: str, description: str) -> dict:
    """Claude Code translates metadata to 10 languages."""
    return {
        "task_type": "translate",
        "title": title,
        "description": description[:300],
        "languages": ["es", "fr", "de", "hi", "pt", "id", "ja", "ko", "tr", "ar"],
        "instructions": (
            "Translate title and description intro to all 10 languages. "
            "Translate meaning, not word-for-word. Keep numbers as numerals. "
            "Arabic: use Modern Standard Arabic. "
            "Return dict with language codes as keys."
        )
    }


def handle_ideas_task(batch_num: int, batch_size: int, categories: list, existing_count: int) -> dict:
    """Claude Code generates a batch of video ideas."""
    return {
        "task_type": "ideas",
        "batch_num": batch_num,
        "batch_size": batch_size,
        "categories": categories,
        "start_id": existing_count + 1,
        "skill_file": ".claude/CLAUDE.md",
        "instructions": (
            f"Generate {batch_size} unique video ideas for FactForge channel. "
            f"Focus categories: {', '.join(categories)}. "
            "Return JSON array of idea objects with all required fields."
        )
    }


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        show_pending()
    elif args[0] == "process" and len(args) >= 2:
        process_task(args[1])
    elif args[0] == "write" and len(args) >= 3:
        write_response(args[1], " ".join(args[2:]))
    elif args[0] == "watch":
        watch_mode()
    elif args[0] == "list":
        show_pending()
    else:
        console.print("Usage:")
        console.print("  python claude_tasks.py              — list pending")
        console.print("  python claude_tasks.py process <id> — show task to Claude")
        console.print("  python claude_tasks.py watch        — auto-watch mode")
        console.print('  python claude_tasks.py write <id> \'{"key": "val"}\' — write response')
