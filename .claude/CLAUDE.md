# YouTube Automation System — Permanent Brain
# Read this file at the START of every Claude Code session.
#
# ⚡ AI ENGINE: Claude Code (this session) — NO Anthropic API key needed.
# Claude Code handles all intelligence. Python handles automation only.

---

## What This Project Is

An automated YouTube channel producing English-language educational and factual short and long videos.

**Channel concept: FactForge**
Three content angles:
1. **Islamic & Arab perspective** — underrepresented history, civilization, and achievements in English
2. **Shocking statistics and historical facts** — numbers and data that change how you see the world
3. **Geopolitical comparisons** — US vs China, East vs West, wealth gaps, power rankings

Target audience: Global English speakers curious about history, economics, and geopolitics.

---

## How to Resume Any Session

At the START of every session (or when user says "resume", "status", or opens a new chat):

1. Read `state/progress.json`
2. Read `state/pending_uploads.json`
3. Read `state/published_videos.json`
4. Read `state/queue.json` (first 3 ideas only)
4. Output EXACTLY this dashboard format — nothing else, no preamble:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📺  FactForge — لوحة التحكم
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 قيد الإنتاج
   [id] — [title]
   الخطوة: [current step] | النتيجة: [script_score if available]/100

⏳ في انتظار الإكمال  ([count] مقاطع)
   • [id] — [title]  →  [pending_tasks بالعربي]

✅ مرفوعة على يوتيوب  ([count] مقاطع)
   • [id] — [youtube_id]  |  رُفع: [published_at]  |  [إذا cleaned: "🧹 منظّف" وإلا: "📁 يمكن تنظيفه ← clean [id]"]

📋 قائمة الانتظار  ([total] فكرة جاهزة)
   التالي: "[next idea title]"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
الأوامر:
  produce      → ابدأ إنتاج المقطع التالي
  upload       → ارفع كل المقاطع الجاهزة الآن
  queue        → اعرض قائمة الأفكار كاملة
  skip         → تخطى الفكرة التالية
  clean [id]   → نظّف ملفات المقطع المرفوع ووفّر مساحة
  status       → حدّث هذه اللوحة
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Translate pending_tasks to Arabic:
- subtitles_7_languages → "ترجمات نصية (7 لغات)"
- thumbnail → "صورة مصغرة"
- upload → "رفع على يوتيوب"
- subtitles_uploaded → "✅ ترجمات مرفوعة"

Fill in real values from the state files. If nothing in progress, show "✅ Nothing in progress".
If pending_uploads is empty, show "✅ All videos uploaded".
Always suggest the next idea at the bottom — never wait to be asked.
5. Then STOP and wait for user command.

---

## Session Rules (Follow Every Time)

1. **Always read this file first** — then progress.json
2. **Never restart completed work** — check progress.json before starting anything
3. **Work one idea at a time** — never batch produce without explicit user command
4. **Ask before producing** — show the idea, ask "shall I produce this?"
5. **Save state after every major step** — script, audio, thumbnail, video, publish
6. **Verify facts before writing any script** — minimum 2 official sources
7. **If interrupted, resume from last saved checkpoint** — never start over

---

## System Architecture

```
User command → main.py (Python)
                  ↓
        ┌─────────────────────────────────┐
        │  Claude Code (THIS SESSION)     │  ← Does ALL AI work
        │  - Verifies facts               │
        │  - Writes scripts               │
        │  - Generates titles             │
        │  - Translates metadata          │
        │  - Generates video ideas        │
        │  - Analyzes performance         │
        └─────────────────────────────────┘
                  ↓
        ┌─────────────────────────────────┐
        │  Python automation              │  ← Does non-AI work
        │  - TTS audio (Kokoro/EdgeTTS)   │
        │  - Remotion video render        │
        │  - Pillow thumbnail             │
        │  - YouTube API upload           │
        │  - Web search (Serper)          │
        └─────────────────────────────────┘
                  ↓
          output/[id]/ → YouTube API
```

### How Claude Code gets tasks
Python writes request JSON files → Claude Code reads + fills responses → Python continues

### Key Files
- `state/progress.json` — what is currently being produced
- `state/queue.json` — next 100 ideas in priority order
- `state/analytics.json` — performance data from YouTube
- `database/ideas_short.json` — 10,000 short video ideas
- `database/ideas_long.json` — 500 long video ideas
- `database/used_ideas.json` — what has been produced and published
- `database/trending_topics.json` — updated weekly

---

## Content Rules (NEVER VIOLATE)

- Every statistic must come from minimum 2 official sources
- Never publish an unverified claim
- No copyright music — voice and natural sound effects only
- No personal religious rulings or fatwa content
- No attacks on specific living individuals
- Factual controversy only (prices, rankings, historical comparisons)
- YouTube Community Guidelines compliance at all times
- Always cite sources in video descriptions

---

## Pre-Publish Quality Gates (MANDATORY)

BEFORE publishing any video, ALL FOUR must pass in order:
1. `.claude/skills/fact_verification.md` → accuracy score ≥ 18/20 (runs BEFORE script is written)
2. `.claude/skills/content_psychology.md` → script score ≥ 80/100
3. `.claude/skills/visual_design.md` → visual score ≥ 14/16
4. `.claude/skills/youtube_seo.md` → SEO checklist score ≥ 18/22

If any gate fails, revise and re-score before proceeding to the next gate.
Script is written FROM verified facts — never verify after writing.

---

## Production Pipeline (Phase 3)

When user says "produce next video":
1. Read queue.json → show next idea → ask for approval
2. Research: web search → verify facts → save to output/[id]/research.json + sources.json
3. Accuracy gate: score research ≥ 18/20 (fact_verification.md) — stop if fails
4. Script: write TTS-optimized script FROM verified facts → save to output/[id]/script.json
5. Content gate: score script ≥ 80/100 (content_psychology.md) — revise if fails
6. Voice: Edge TTS (en-US-AndrewNeural +8%) → save to output/[id]/audio.mp3
7. SFX: generate_all_sfx() if not exists → calculate_sfx_timestamps(segments) → output/[id]/sfx_events.json
8. Background: fetch from Pexels by category (visual_design.md) → assign backgroundVideo per segment
9. Video: Remotion render (no audio) → ffmpeg merge voice + music + SFX → output/[id]/video.mp4
10. Visual gate: score ≥ 14/16 (visual_design.md) — revise if fails
11. Thumbnail: Pillow generation → save to output/[id]/thumbnail.png
12. Metadata: title × 5 variants + description + tags → output/[id]/metadata.json
13. SEO gate: score metadata ≥ 18/22 (youtube_seo.md) — revise if fails
14. Publish: YouTube API upload → mark as produced in database
15. Subtitles: generate SRT for 7 languages (EN/AR/ES/FR/HI/PT/TR) → upload via Captions API

---

## User Commands (Simple)

| Command | ماذا يفعل |
|---------|-----------|
| `produce` | ابدأ الإنتاج الكامل للفكرة التالية — اعرضها أولاً وانتظر الموافقة |
| `upload` | ارفع كل المقاطع + الترجمات الجاهزة الآن (يتحقق من الحصة أولاً) |
| `queue` | اعرض أفضل 10 أفكار قادمة |
| `skip` | تخطى الفكرة الحالية وانتقل للتالية |
| `add: [موضوع]` | أضف فكرة مخصصة في أعلى القائمة |
| `analytics` | اعرض تقرير أداء القناة |
| `status` | اعرض لوحة التحكم |
| `resume` | نفس status — اعرض اللوحة واستمر |
| `clean [id]` | احذف ملفات المقطع المرفوع من الكمبيوتر — احتفظ فقط بـ metadata.json و script.json و thumbnail.png |
| `clean all` | نظّف كل المقاطع المرفوعة دفعة واحدة |

### قواعد الـ clean (لا تُخالَف):
- احذف فقط إذا كان `status = uploaded` في pending_uploads.json أو youtube_id موجود في progress.json
- الملفات التي تُحذف: video*.mp4، audio*.mp3، video_noaudio*.mp4، bg_videos/، dubbed/، images/، subtitles/
- الملفات التي تُبقى دائماً: metadata.json، script.json، research.json، sources.json، thumbnail.png، remotion_props.json
- اعرض قائمة ما سيُحذف وحجمه قبل الحذف، واطلب تأكيداً

Any variation of these works: "produce next", "show me the queue", "what's next" etc.
Understand intent, not exact wording.

---

## Token Optimization Rules

- Use templates — never regenerate structure from scratch
- Cache research results — never search the same topic twice in one session
- Batch operations — generate all metadata fields in one Claude call
- Store results locally — never recompute what's already in output/
- Split large generation tasks — max 500 ideas per Claude call
- Summarize completed steps — don't carry full transcripts in context

---

## Project Created
April 2026
Channel: FactForge
Working directory: /Users/ar/Development/projects/FactForge
