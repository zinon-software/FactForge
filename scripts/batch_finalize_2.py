"""
batch_finalize_2.py — Update state after Batch 2 render completion
"""
import json
import os
from datetime import date

BASE = "/Users/ar/Development/projects/FactForge"

BATCH2 = [
    {"id": "S00794", "title": "The Race to Build an AGI — Who Is Winning and What Happens When They Do"},
    {"id": "S00925", "title": "The Oil Companies That Knew About Climate Change in 1977"},
    {"id": "S01066", "title": "How El Salvador's Homicide Rate Dropped 95% in Two Years"},
    {"id": "S01080", "title": "The AI That Can Clone Your Voice in 3 Seconds"},
    {"id": "S01084", "title": "The $40 Aspirin: How Hospital Billing Became Legalized Robbery"},
    {"id": "S01097", "title": "Quantum Computing Will Break All Encryption Within 10 Years"},
    {"id": "S01113", "title": "The Poisoning That Killed a City: Flint Michigan's Water Crisis"},
    {"id": "S01128", "title": "Stuxnet: The Cyberweapon That Physically Destroyed Nuclear Centrifuges"},
    {"id": "S01131", "title": "The AI That Generates Fake Scientific Papers"},
    {"id": "S01644", "title": "Mansa Musa's Pilgrimage: The Day an African King Broke the Global Economy"},
]

today = str(date.today())

# Update pending_uploads.json
with open(f"{BASE}/state/pending_uploads.json") as f:
    pending = json.load(f)
existing = {e["id"] for e in pending["pending"]}
for v in BATCH2:
    if v["id"] not in existing:
        pending["pending"].append({
            "id": v["id"], "title": v["title"],
            "video_file": f"output/{v['id']}/video.mp4",
            "metadata_file": f"output/{v['id']}/metadata.json",
            "ready": True, "blocked_reason": None, "queued_at": today,
        })
with open(f"{BASE}/state/pending_uploads.json", "w") as f:
    json.dump(pending, f, indent=2, ensure_ascii=False)

# Update queue.json
with open(f"{BASE}/state/queue.json") as f:
    queue = json.load(f)
batch_ids = {v["id"] for v in BATCH2}
for item in queue.get("ideas", []):
    if item.get("id") in batch_ids:
        item["status"] = "produced"
        item["produced_at"] = today
with open(f"{BASE}/state/queue.json", "w") as f:
    json.dump(queue, f, indent=2, ensure_ascii=False)

# Verify files
print()
print("=" * 54)
missing = []
for v in BATCH2:
    path = f"{BASE}/output/{v['id']}/video.mp4"
    exists = os.path.exists(path)
    size = round(os.path.getsize(path)/1024/1024, 1) if exists else 0
    status = f"✅ {size}MB" if exists else "❌ MISSING"
    print(f"  {v['id']} — {status}")
    if not exists:
        missing.append(v["id"])
print("=" * 54)

if missing:
    print(f"⚠️  {len(missing)} files missing: {missing}")
else:
    total = len(pending["pending"])
    print()
    print("🎉 رسالة نجاح — الدفعة الثانية اكتملت!")
    print()
    print("━" * 54)
    print("✅  اكتمل إنتاج ١٠ مقاطع Short (الدفعة الثانية)")
    print()
    for v in BATCH2:
        print(f"  {v['id']} — {v['title'][:45]}")
    print()
    print(f"  إجمالي المقاطع الجاهزة للرفع: {total}")
    print("━" * 54)
