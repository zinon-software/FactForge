"""
File Manager — State persistence helpers
All read/write operations go through here to ensure consistency.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Any


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path: str | Path) -> dict | list:
    path = Path(path)
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str | Path, data: dict | list, indent: int = 2) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def append_to_json_list(path: str | Path, item: dict) -> None:
    """Append an item to a JSON file that contains a list."""
    data = load_json(path)
    if isinstance(data, list):
        data.append(item)
    elif isinstance(data, dict) and "ideas" in data:
        data["ideas"].append(item)
    save_json(path, data)


def load_progress() -> dict:
    from config.settings import STATE_DIR
    return load_json(STATE_DIR / "progress.json")


def save_progress(progress: dict) -> None:
    from config.settings import STATE_DIR
    progress["last_updated"] = now_utc()
    save_json(STATE_DIR / "progress.json", progress)


def update_progress_step(step: str, idea_id: str = None) -> None:
    progress = load_progress()
    if idea_id:
        progress["current_production"]["idea_id"] = idea_id
    progress["current_production"]["step"] = step
    if step not in progress["current_production"].get("steps_completed", []):
        progress["current_production"].setdefault("steps_completed", []).append(step)
    save_progress(progress)


def load_queue() -> list:
    from config.settings import STATE_DIR
    data = load_json(STATE_DIR / "queue.json")
    return data.get("queue", [])


def save_queue(queue: list) -> None:
    from config.settings import STATE_DIR
    save_json(STATE_DIR / "queue.json", {
        "last_updated": now_utc(),
        "queue": queue
    })


def mark_idea_used(idea_id: str, youtube_id: str = None, reason: str = "produced") -> None:
    from config.settings import DATABASE_DIR
    used = load_json(DATABASE_DIR / "used_ideas.json")
    entry = {
        "id": idea_id,
        "reason": reason,
        "youtube_id": youtube_id,
        "date": now_utc()
    }
    if reason == "produced":
        used.setdefault("produced_ideas", []).append(entry)
        used["total_produced"] = len(used["produced_ideas"])
    else:
        used.setdefault("skipped_ideas", []).append(entry)
        used["total_skipped"] = len(used["skipped_ideas"])
    used["last_updated"] = now_utc()
    save_json(DATABASE_DIR / "used_ideas.json", used)


def get_output_dir(idea_id: str) -> Path:
    from config.settings import OUTPUT_DIR
    path = OUTPUT_DIR / idea_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def log_improvement(entry: str) -> None:
    from config.settings import STATE_DIR
    log_path = STATE_DIR / "improvement_log.md"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n{entry}\n")
