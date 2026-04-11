"""
Token Optimizer — Minimize Claude API token usage
Implements caching, context compression, and batching strategies.
"""

import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Any, Optional, Callable


CACHE_DIR = Path("output/.cache")
CACHE_TTL_HOURS = 24  # Cache research results for 24 hours


def _cache_key(data: str) -> str:
    return hashlib.md5(data.encode()).hexdigest()[:16]


def _cache_path(key: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{key}.json"


def cache_get(query: str) -> Optional[Any]:
    """Return cached result for query if it exists and isn't expired."""
    key = _cache_key(query)
    path = _cache_path(key)
    if not path.exists():
        return None
    try:
        with open(path) as f:
            entry = json.load(f)
        expires = datetime.fromisoformat(entry["expires"])
        if datetime.now(timezone.utc) > expires:
            path.unlink()  # Expired — delete
            return None
        return entry["data"]
    except Exception:
        return None


def cache_set(query: str, data: Any, ttl_hours: int = CACHE_TTL_HOURS) -> None:
    """Cache result for query."""
    key = _cache_key(query)
    path = _cache_path(key)
    expires = (datetime.now(timezone.utc) + timedelta(hours=ttl_hours)).isoformat()
    with open(path, "w") as f:
        json.dump({"query": query[:100], "expires": expires, "data": data}, f)


def cached(ttl_hours: int = CACHE_TTL_HOURS):
    """Decorator to cache function results by arguments."""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{args}:{kwargs}"
            cached_result = cache_get(key)
            if cached_result is not None:
                return cached_result
            result = func(*args, **kwargs)
            cache_set(key, result, ttl_hours)
            return result
        return wrapper
    return decorator


def compress_context(messages: list[dict], keep_last_n: int = 4) -> list[dict]:
    """
    Compress conversation context for Claude API calls.
    Keeps system message + last N messages + summarizes the rest.
    """
    if len(messages) <= keep_last_n + 1:
        return messages

    system_msg = [m for m in messages if m["role"] == "system"]
    non_system = [m for m in messages if m["role"] != "system"]

    # Keep first user message (context) and last N messages
    to_summarize = non_system[1:-keep_last_n] if len(non_system) > keep_last_n + 1 else []
    to_keep = non_system[-keep_last_n:]

    if not to_summarize:
        return messages

    # Build summary of older messages
    summary_text = "Previous conversation summary: "
    for msg in to_summarize:
        role = msg["role"]
        content = msg["content"][:200] if isinstance(msg["content"], str) else str(msg["content"])[:200]
        summary_text += f"[{role}]: {content}... "

    summary_msg = {"role": "user", "content": summary_text}
    return system_msg + [non_system[0], summary_msg] + to_keep


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token for English text."""
    return len(text) // 4


def batch_items(items: list, batch_size: int = 500) -> list[list]:
    """Split a list into batches of batch_size."""
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]


def select_model(task_type: str) -> str:
    """
    Choose the cheapest Claude model that can handle the task.

    task_type options:
    - "script"     → full writing task, needs Sonnet
    - "research"   → complex analysis, needs Sonnet
    - "title"      → simple generation, Haiku is fine
    - "translate"  → pattern task, Haiku is fine
    - "score"      → quick evaluation, Haiku is fine
    """
    from config.settings import CLAUDE_MODEL_MAIN, CLAUDE_MODEL_FAST
    simple_tasks = {"title", "translate", "score", "tags", "categorize"}
    return CLAUDE_MODEL_FAST if task_type in simple_tasks else CLAUDE_MODEL_MAIN
