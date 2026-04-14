"""
batch_finalize.py — Update state files after batch render completion
Updates progress.json, pending_uploads.json, queue.json for all 10 batch videos
"""
import json
import os
from datetime import date

BASE = "/Users/ar/Development/projects/FactForge"

BATCH_VIDEOS = [
    {"id": "S01062", "title": "EpiPen: $7 to Make. $608 to Buy."},
    {"id": "S01110", "title": "University Costs $300 in Germany. $108,000 in the US."},
    {"id": "S01155", "title": "Africa's Largest Dam — Built With Workers' Salaries"},
    {"id": "S01183", "title": "A $1 Pill That Cures Hepatitis C — Sold for $84,000"},
    {"id": "S01185", "title": "Your Face Is in a Database of 40 Billion Photos"},
    {"id": "S01190", "title": "OpenAI Is Being Sued for $9.9 Trillion"},
    {"id": "S01215", "title": "The CIA Spied on 120 Countries for 50 Years — Through a Swiss Company"},
    {"id": "S01224", "title": "American Prisoners Earn $0.23 an Hour — For the US Military"},
    {"id": "S01267", "title": "Building AGI Will Cost More Than the GDP of Most Countries"},
    {"id": "S01268", "title": "This Movie Was Made Entirely by AI — And It's Playing in 58 Cinemas"},
]

today = str(date.today())

# ── 1. Update pending_uploads.json ──────────────────────────────────────────
pending_path = f"{BASE}/state/pending_uploads.json"
with open(pending_path) as f:
    pending = json.load(f)

existing_ids = {e["id"] for e in pending["pending"]}

for v in BATCH_VIDEOS:
    vid_id = v["id"]
    if vid_id not in existing_ids:
        pending["pending"].append({
            "id": vid_id,
            "title": v["title"],
            "video_file": f"output/{vid_id}/video.mp4",
            "metadata_file": f"output/{vid_id}/metadata.json",
            "subtitles_dir": f"output/{vid_id}/subtitles",
            "ready": True,
            "blocked_reason": None,
            "queued_at": today,
        })

with open(pending_path, "w") as f:
    json.dump(pending, f, indent=2, ensure_ascii=False)

print(f"✓ pending_uploads.json — added {len(BATCH_VIDEOS)} videos")

# ── 2. Update queue.json — mark batch videos as produced ────────────────────
queue_path = f"{BASE}/state/queue.json"
with open(queue_path) as f:
    queue = json.load(f)

batch_ids = {v["id"] for v in BATCH_VIDEOS}
updated = 0
for item in queue.get("ideas", []):
    if item.get("id") in batch_ids and item.get("status") != "produced":
        item["status"] = "produced"
        item["produced_at"] = today
        updated += 1

with open(queue_path, "w") as f:
    json.dump(queue, f, indent=2, ensure_ascii=False)

print(f"✓ queue.json — marked {updated} ideas as produced")

# ── 3. Update progress.json ──────────────────────────────────────────────────
progress_path = f"{BASE}/state/progress.json"
with open(progress_path) as f:
    progress = json.load(f)

all_pending = [e["id"] for e in pending["pending"]]
progress["pending_upload_ids"] = all_pending
progress["next_action"] = f"Upload {len(all_pending)} pending videos after YouTube quota resets"

with open(progress_path, "w") as f:
    json.dump(progress, f, indent=2, ensure_ascii=False)

print(f"✓ progress.json — {len(all_pending)} videos pending upload")

# ── 4. Verify video files exist ──────────────────────────────────────────────
print()
print("=" * 52)
missing = []
for v in BATCH_VIDEOS:
    vid_path = f"{BASE}/output/{v['id']}/video.mp4"
    exists = os.path.exists(vid_path)
    size_mb = round(os.path.getsize(vid_path) / 1024 / 1024, 1) if exists else 0
    status = f"✅ {size_mb}MB" if exists else "❌ MISSING"
    print(f"  {v['id']} — {status}")
    if not exists:
        missing.append(v["id"])

print("=" * 52)
print()

if missing:
    print(f"⚠️  WARNING: {len(missing)} video files missing: {missing}")
else:
    print("🎉 رسالة نجاح — تمّ الإنتاج بنجاح!")
    print()
    print("━" * 52)
    print("✅  اكتمل إنتاج ١٠ مقاطع Short بنجاح تام")
    print()
    print("  S01062 — EpiPen: $7 to Make. $608 to Buy.")
    print("  S01110 — University Costs $300 in Germany")
    print("  S01155 — Africa's Largest Dam")
    print("  S01183 — Hepatitis C Pill: $84,000 vs $1")
    print("  S01185 — Your Face in 40B Photos Database")
    print("  S01190 — OpenAI Sued for $9.9 Trillion")
    print("  S01215 — CIA Spied via Swiss Company")
    print("  S01224 — Prison Labor: $0.23/hr for Military")
    print("  S01267 — AGI Costs More Than Most GDPs")
    print("  S01268 — AI-Made Film in 58 Cinemas")
    print()
    print("  الخطوة التالية: رفع على YouTube بعد تفعيل الحساب")
    print("━" * 52)
