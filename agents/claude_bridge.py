"""
Claude Bridge — Communication protocol between Python agents and Claude Code.

Architecture:
  Instead of calling Anthropic API programmatically, this bridge:
  1. Writes a task request to state/claude_tasks/[task_id]/request.json
  2. Signals Claude Code (prints a clear prompt to the terminal)
  3. Waits for Claude Code to write the result to response.json
  4. Returns the parsed result to the calling agent

This means Claude Code (the active session) does all AI work.
No API key required — the user's Claude subscription covers everything.
"""

import json
import os
import time
from pathlib import Path
from datetime import datetime, timezone

TASKS_DIR = Path("state/claude_tasks")
POLL_INTERVAL = 2    # seconds between checks
MAX_WAIT = 600       # 10 minutes max wait


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _task_dir(task_id: str) -> Path:
    path = TASKS_DIR / task_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def request(task_type: str, payload: dict, task_id: str = None) -> dict:
    """
    Submit a task to Claude Code and wait for the response.

    task_type: "research", "script", "titles", "translate", "ideas", "improve"
    payload: task-specific data dict
    Returns: Claude's response as a dict
    """
    if task_id is None:
        task_id = f"{task_type}_{int(time.time())}"

    tdir = _task_dir(task_id)
    request_path = tdir / "request.json"
    response_path = tdir / "response.json"
    done_path = tdir / "done.flag"

    # Remove stale done flag
    if done_path.exists():
        done_path.unlink()
    if response_path.exists():
        response_path.unlink()

    # Write request
    request_data = {
        "task_id": task_id,
        "task_type": task_type,
        "created_at": now_utc(),
        "payload": payload,
    }
    with open(request_path, "w", encoding="utf-8") as f:
        json.dump(request_data, f, indent=2, ensure_ascii=False)

    # Signal Claude Code
    print("\n" + "═" * 60)
    print(f"  📋 CLAUDE CODE TASK: {task_type.upper()}")
    print(f"  Task ID: {task_id}")
    print(f"  Request saved to: {request_path}")
    print(f"\n  ▶ Tell Claude Code:")
    print(f'    "Process task {task_id}"')
    print("═" * 60 + "\n")

    # Poll for response
    elapsed = 0
    while elapsed < MAX_WAIT:
        if done_path.exists() and response_path.exists():
            with open(response_path, "r", encoding="utf-8") as f:
                response = json.load(f)
            print(f"[claude_bridge] Task {task_id} complete.")
            return response

        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL

        if elapsed % 30 == 0:
            print(f"[claude_bridge] Waiting for Claude... ({elapsed}s elapsed)")

    raise TimeoutError(f"Task {task_id} timed out after {MAX_WAIT}s")


def respond(task_id: str, response_data: dict) -> None:
    """
    Called by Claude Code (or a helper script) to deliver the response.
    Writes response.json and done.flag so the waiting agent unblocks.
    """
    tdir = _task_dir(task_id)
    response_path = tdir / "response.json"
    done_path = tdir / "done.flag"

    response_data["task_id"] = task_id
    response_data["completed_at"] = now_utc()

    with open(response_path, "w", encoding="utf-8") as f:
        json.dump(response_data, f, indent=2, ensure_ascii=False)

    done_path.touch()
    print(f"[claude_bridge] Response written for task {task_id}")


def list_pending_tasks() -> list[dict]:
    """Return all tasks that have a request but no done.flag."""
    if not TASKS_DIR.exists():
        return []

    pending = []
    for tdir in TASKS_DIR.iterdir():
        if not tdir.is_dir():
            continue
        req = tdir / "request.json"
        done = tdir / "done.flag"
        if req.exists() and not done.exists():
            with open(req, "r", encoding="utf-8") as f:
                pending.append(json.load(f))
    return pending


def get_task(task_id: str) -> dict | None:
    """Read a specific task request."""
    req = TASKS_DIR / task_id / "request.json"
    if not req.exists():
        return None
    with open(req, "r", encoding="utf-8") as f:
        return json.load(f)
