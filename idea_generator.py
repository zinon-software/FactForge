"""
Idea Generator — Generates 10,000 short and 500 long video ideas.
Uses Claude in batches of 500 to avoid token limits.
Run: python idea_generator.py
Or called by: python main.py generate-ideas
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

import anthropic
from config.settings import (
    ANTHROPIC_API_KEY, CLAUDE_MODEL_MAIN, DATABASE_DIR,
    FORMAT_TYPES, CONTENT_CATEGORIES, TARGET_SHORT_IDEAS,
    TARGET_LONG_IDEAS, BATCH_SIZE
)
from utils.file_manager import load_json, save_json, load_progress, save_progress, now_utc
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


IDEA_EXAMPLES = """
Example ideas to inspire (do NOT copy these exactly — create new ones):
- "The Man Who Was Richer Than Today's Entire US Economy" (islamic_arab_history, shocking_stat)
- "China Built More Skyscrapers in 2 Years Than the US in 50" (us_vs_china, comparison)
- "Saudi Arabia Earns More Per Minute Than Most Countries in a Year" (wealth_economics, shocking_stat)
- "The Roman Empire Fell 1000 Years Before the Ottoman Empire" (ancient_civilizations, timeline)
- "Why One Kilogram of Anti-Matter Costs More Than All of Human History" (science_space, price_reveal)
- "The Medieval City That Was Larger Than Paris and London Combined" (islamic_arab_history, size_comparison)
"""


def generate_batch(
    batch_num: int,
    batch_size: int,
    start_id: int,
    category_focus: list[str],
    existing_titles: set,
) -> list[dict]:
    """Generate one batch of video ideas using Claude."""

    categories_str = ", ".join(category_focus)
    formats_str = ", ".join(FORMAT_TYPES)

    prompt = f"""Generate {batch_size} unique YouTube short video ideas for the channel "FactForge".

CHANNEL CONCEPT: Educational facts channel with 3 content angles:
1. Islamic & Arab civilization history (underrepresented in English content)
2. Shocking world statistics and historical comparisons
3. Geopolitical comparisons (US vs China, East vs West, etc.)

CATEGORIES TO FOCUS ON THIS BATCH: {categories_str}
AVAILABLE FORMATS: {formats_str}

{IDEA_EXAMPLES}

RULES:
- Every idea must be factually verifiable from official sources
- Each idea must have a specific hook (shocking number or surprising claim)
- Ideas must be suitable for YouTube (educational framing)
- Mix formats evenly across the batch
- Make each idea genuinely surprising or counterintuitive
- No duplicates of these existing titles (first few): {list(existing_titles)[:10]}

Generate exactly {batch_size} ideas as a JSON array. Start IDs at S{start_id:05d}.

Output ONLY valid JSON array, no other text:
[
  {{
    "id": "S{start_id:05d}",
    "title": "Compelling video title",
    "angle": "islamic_history|shocking_stats|geopolitical_comparison",
    "format": "one of the format types",
    "category": "one of the categories",
    "hook": "The single most shocking sentence about this topic",
    "controversy_score": 85,
    "trending_score": 60,
    "evergreen_score": 90,
    "priority_score": 78,
    "estimated_duration_seconds": 52,
    "key_facts": ["fact 1", "fact 2", "fact 3"],
    "sources": ["Source name 1", "Source name 2"],
    "status": "pending",
    "produced_date": null,
    "youtube_id": null,
    "views": null,
    "ctr": null
  }},
  ... ({batch_size} ideas total)
]"""

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL_MAIN,
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = response.content[0].text.strip()

        # Clean JSON
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        # Find JSON array
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start == -1 or end == 0:
            console.print(f"[red]Batch {batch_num}: No JSON array found[/red]")
            return []

        ideas = json.loads(raw[start:end])

        # Validate and clean each idea
        valid_ideas = []
        for idea in ideas:
            if not idea.get("title") or not idea.get("hook"):
                continue
            if idea["title"] in existing_titles:
                continue
            # Ensure required fields
            idea.setdefault("controversy_score", 70)
            idea.setdefault("trending_score", 60)
            idea.setdefault("evergreen_score", 80)
            priority = (
                idea["trending_score"] * 0.4 +
                idea["controversy_score"] * 0.3 +
                idea["evergreen_score"] * 0.3
            )
            idea["priority_score"] = round(priority)
            idea.setdefault("estimated_duration_seconds", 52)
            idea.setdefault("key_facts", [])
            idea.setdefault("sources", [])
            idea["status"] = "pending"
            idea["produced_date"] = None
            idea["youtube_id"] = None
            idea["views"] = None
            idea["ctr"] = None

            valid_ideas.append(idea)
            existing_titles.add(idea["title"])

        return valid_ideas

    except json.JSONDecodeError as e:
        console.print(f"[red]Batch {batch_num}: JSON parse error: {e}[/red]")
        return []
    except Exception as e:
        console.print(f"[red]Batch {batch_num}: Error: {e}[/red]")
        return []


def generate_long_ideas(existing_short_titles: set) -> list[dict]:
    """Generate 500 long video ideas (expansions of shorts)."""
    prompt = f"""Generate 50 YouTube long-form video ideas (8-15 minutes each) for "FactForge".

These should be deep dives into topics that have short videos, exploring more detail.
Categories: Islamic/Arab history, world economics, geopolitics, ancient civilizations.

Examples:
- "The Complete Rise and Fall of the Richest Man in History: Mansa Musa" (15 min)
- "How China Built a Global Economic Empire in 30 Years" (12 min)
- "The Islamic Golden Age: 500 Years of Science the West Forgot" (14 min)

Generate 50 ideas as JSON array:
[
  {{
    "id": "L00001",
    "title": "Long video title",
    "angle": "islamic_history|shocking_stats|geopolitical_comparison",
    "format": "timeline|comparison|hidden_truth|top_10_list",
    "category": "category name",
    "hook": "Opening shocking fact",
    "controversy_score": 75,
    "trending_score": 55,
    "evergreen_score": 95,
    "priority_score": 74,
    "estimated_duration_seconds": 720,
    "key_facts": ["major fact 1", "major fact 2", "major fact 3"],
    "sources": ["World Bank", "Wikipedia", "Britannica"],
    "status": "pending",
    "produced_date": null,
    "youtube_id": null,
    "views": null,
    "ctr": null
  }}
]"""

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL_MAIN,
            max_tokens=6000,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = response.content[0].text.strip()
        if "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
            if raw.startswith("json"):
                raw = raw[4:].strip()

        start = raw.find("[")
        end = raw.rfind("]") + 1
        ideas = json.loads(raw[start:end])

        # Fix IDs
        for i, idea in enumerate(ideas, 1):
            idea["id"] = f"L{i:05d}"
            idea.setdefault("estimated_duration_seconds", 720)

        return ideas

    except Exception as e:
        console.print(f"[red]Long ideas generation error: {e}[/red]")
        return []


def save_ideas_batch(ideas: list[dict], ideas_path: Path) -> None:
    """Append a batch of ideas to the ideas JSON file."""
    if ideas_path.exists():
        data = load_json(ideas_path)
    else:
        data = {"created": now_utc(), "ideas": []}

    data["ideas"].extend(ideas)
    data["total"] = len(data["ideas"])
    data["last_updated"] = now_utc()
    save_json(ideas_path, data)


def build_priority_queue(ideas: list[dict], n: int = 100) -> list[dict]:
    """Sort ideas by priority score and return top N."""
    pending = [i for i in ideas if i.get("status") == "pending"]
    sorted_ideas = sorted(pending, key=lambda x: x.get("priority_score", 0), reverse=True)
    return sorted_ideas[:n]


def run():
    """Generate full idea database."""
    console.print("\n[bold cyan]Idea Database Generator[/bold cyan]")
    console.print("=" * 50)

    ideas_short_path = DATABASE_DIR / "ideas_short.json"
    ideas_long_path = DATABASE_DIR / "ideas_long.json"
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    # Check how many ideas already exist
    existing_data = load_json(ideas_short_path)
    existing_ideas = existing_data.get("ideas", [])
    existing_count = len(existing_ideas)
    existing_titles = {i["title"] for i in existing_ideas}

    start_id = existing_count + 1
    remaining = TARGET_SHORT_IDEAS - existing_count

    if remaining <= 0:
        console.print(f"[green]Database already has {existing_count:,} short ideas — complete![/green]")
    else:
        console.print(f"Generating {remaining:,} short ideas (starting from S{start_id:05d})...")
        console.print(f"Working in batches of {BATCH_SIZE}...")

        num_batches = (remaining + BATCH_SIZE - 1) // BATCH_SIZE
        categories = CONTENT_CATEGORIES

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating ideas...", total=remaining)

            for batch_num in range(1, num_batches + 1):
                batch_remaining = min(BATCH_SIZE, remaining - (batch_num - 1) * BATCH_SIZE)
                if batch_remaining <= 0:
                    break

                # Rotate through categories to ensure good distribution
                batch_categories = categories[(batch_num - 1) % len(categories):][:3]

                console.print(f"\n[dim]Batch {batch_num}/{num_batches} ({batch_remaining} ideas)...[/dim]")

                ideas = generate_batch(
                    batch_num=batch_num,
                    batch_size=batch_remaining,
                    start_id=start_id + (batch_num - 1) * BATCH_SIZE,
                    category_focus=batch_categories,
                    existing_titles=existing_titles,
                )

                if ideas:
                    save_ideas_batch(ideas, ideas_short_path)
                    progress.update(task, advance=len(ideas))
                    console.print(f"  [green]✓ {len(ideas)} ideas saved[/green]")
                else:
                    console.print(f"  [yellow]Batch {batch_num}: 0 valid ideas — retrying next[/yellow]")

                # Rate limiting — be kind to API
                if batch_num < num_batches:
                    time.sleep(2)

    # Generate long ideas
    long_data = load_json(ideas_long_path)
    existing_long = long_data.get("ideas", [])
    long_remaining = TARGET_LONG_IDEAS - len(existing_long)

    if long_remaining > 0:
        console.print(f"\nGenerating long video ideas ({long_remaining} needed)...")
        batches_needed = (long_remaining + 49) // 50  # 50 per call

        all_long_ideas = []
        for batch in range(batches_needed):
            ideas = generate_long_ideas(existing_titles)
            # Fix IDs for continuation
            offset = len(existing_long) + len(all_long_ideas)
            for i, idea in enumerate(ideas):
                idea["id"] = f"L{offset + i + 1:05d}"
            all_long_ideas.extend(ideas)
            time.sleep(2)

        all_long_ideas = all_long_ideas[:long_remaining]
        save_ideas_batch(all_long_ideas, ideas_long_path)
        console.print(f"[green]✓ {len(all_long_ideas)} long ideas saved[/green]")

    # Build priority queue
    console.print("\nBuilding priority queue...")
    final_short = load_json(ideas_short_path)
    all_ideas = final_short.get("ideas", [])
    queue = build_priority_queue(all_ideas, n=100)

    from utils.file_manager import save_queue
    save_queue(queue)
    console.print(f"[green]✓ Priority queue built: top {len(queue)} ideas[/green]")

    # Update progress
    progress_data = load_progress()
    progress_data["phases_completed"]["phase_2_database"] = True
    progress_data["database_stats"]["short_ideas_count"] = len(all_ideas)
    progress_data["database_stats"]["long_ideas_count"] = len(load_json(ideas_long_path).get("ideas", []))
    save_progress(progress_data)

    console.print(f"\n[bold green]Database generation complete![/bold green]")
    console.print(f"  Short ideas: {len(all_ideas):,}")
    console.print(f"  Long ideas: {len(load_json(ideas_long_path).get('ideas', []))}")
    console.print(f"  Queue: top {len(queue)} ideas ready")
    console.print("\nRun: [bold]python main.py queue[/bold] to see your top ideas")
    console.print("Run: [bold]python main.py produce[/bold] to start producing")


if __name__ == "__main__":
    run()
