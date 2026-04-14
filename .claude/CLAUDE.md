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
  upload       → ارفع مقاطع اليوم (3 مقاطع مجدولة)
  schedule     → اعرض جدول النشر الكامل مع التواريخ
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
4. **AUTONOMOUS OPERATION** — do NOT ask for permission at each step. When user says "produce", execute the full pipeline end-to-end without stopping to ask. Only stop if a quality gate fails (score below minimum) or a hard error occurs.
5. **Save state after every major step** — script, audio, thumbnail, video, publish
6. **Verify facts before writing any script** — minimum 2 official sources
7. **If interrupted, resume from last saved checkpoint** — never start over
8. **Auto-choose publish date** — use utils/youtube_helper.get_next_publish_date() — never ask user for dates
9. **Auto-clean after upload** — delete video.mp4, audio.mp3, bg_videos/ automatically after successful upload

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
        │  - TTS audio (Kokoro am_echo)   │
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

### Short Videos (Reels/Shorts)

When user says "produce next video" (Short):
1. Read queue.json → pick next idea → announce it → proceed WITHOUT asking for permission
2. Research: web search → verify facts → save to output/[id]/research.json + sources.json
3. Accuracy gate: score research ≥ 18/20 (fact_verification.md) — stop if fails
4. Script: write TTS-optimized script FROM verified facts → save to output/[id]/script.json
5. Content gate: score script ≥ 80/100 (content_psychology.md) — revise if fails
6. Voice: **Kokoro TTS** voice=`am_echo` speed=1.08 → save to output/[id]/audio.mp3
   - Script: `python3 scripts/generate_audio.py [id]` — handles TTS + timestamps in one step
   - Model: models/kokoro/kokoro-v1.0.onnx + voices-v1.0.bin (Apache 2.0, commercial safe ✅)
   - NEVER use Edge TTS — Microsoft TOS prohibits commercial use on free tier
7. Word timestamps: faster-whisper (base model, word_timestamps=True) → saved into remotion_props.json
8. Background: fetch from Pexels by category → assign backgroundVideo per segment in remotion_props.json
9. Video: Remotion render ShortVideo composition (no audio) → ffmpeg merge audio → output/[id]/video.mp4
   - MANDATORY: totalDurationFrames = ceil(audio_seconds × 60) — Shorts run at 60fps (Root.tsx)
   - MANDATORY: segment frames must be aligned to word timestamps × 60fps (ms × 60 / 1000)
   - Shorts duration: 35–60 seconds (target 45–58s sweet spot)
10. Visual gate: score ≥ 14/16 (visual_design.md) — revise if fails
11. Thumbnail: Pollinations.ai Flux AI background + Pillow overlay → output/[id]/thumbnail.jpg (JPEG, NOT PNG)
    - ALL thumbnails (Shorts AND Long): 1280×720 (16:9) — YouTube requires this for ALL video types
    - The 1080×1920 format is for the VIDEO itself only, NEVER for thumbnails
    - AI prompt via: https://image.pollinations.ai/prompt/{prompt}?width={w}&height={h}&nologo=true&model=flux
    - No API key needed — free & commercial use allowed
12. Metadata: title × 5 variants + description + tags → output/[id]/metadata.json
13. SEO gate: score metadata ≥ 18/22 (youtube_seo.md) — revise if fails
14. Publish: `python3 scripts/finalize_and_upload.py [id]` — handles upload + thumbnail + state in one step
    - publish date: auto-calculated via utils/youtube_helper.get_next_publish_date() — never ask user
    - Thumbnail upload via API (works for Long videos, may be blocked for Shorts)
15. Auto-clean: delete video.mp4, audio.mp3, bg_videos/, public/[id]/ after successful upload
16. Subtitles: generate SRT for 7 languages (EN/AR/ES/FR/HI/PT/TR) → upload via captions().insert()

### Long Videos (Documentary Format)

When user says "produce next long video" or idea starts with L:
1. Read queue.json / database/ideas_long.json → pick next idea → announce it → proceed WITHOUT asking
2. Research: web search (min 2 official sources) → verify facts → save to output/[id]/research.json
3. Accuracy gate: score ≥ 18/20 — stop if fails
4. Script: write documentary script (10–15 min) with chapters → save to output/[id]/script.json
   - Each chapter has: id, type, chapter_num, title, tts_script, image_prompt
   - Types: hook, explainer, deep_dive, solution, cta
5. Content gate: score ≥ 80/100 — revise if fails
6. Voice: **Kokoro TTS** voice=`am_echo` speed=1.08 → output/[id]/audio.mp3
   - Script: `python3 scripts/generate_audio.py [id]` — handles TTS + timestamps in one step
   - NEVER use Edge TTS — Microsoft TOS prohibits commercial use on free tier
7. Word timestamps: faster-whisper (base model, word_timestamps=True) → output/[id]/word_timestamps.json
8. AI Images: Pollinations Flux (1920×1080) — 2 images per chapter (A + B for crossfade)
   - URL: https://image.pollinations.ai/prompt/{prompt}?width=1920&height=1080&nologo=true&model=flux&seed={seed}
   - Rate limit: 12s delay between requests — use retry with 20s wait on 429
   - Save to output/[id]/images/{chapter_id}_A.jpg and _B.jpg
   - Copy all images AND audio to video/remotion-project/public/[id]/ BEFORE rendering
9. remotion_props.json: distribute frames proportionally by chapter script length
   - totalDurationFrames = ceil(audio_seconds × 30)
   - Each section: startFrame, endFrame, imageA, imageB (paths relative to public/)
   - Include all 1,600+ wordTimestamps
10. Video: Remotion render DocumentaryVideo composition → ffmpeg merge
    - Composition: DocumentaryVideo (NOT LongVideo — that's for Wealth Gap only)
    - Script: python3 scripts/render_documentary.py [id]
    - CRF 18 + preset slow + maxrate 20M → NO PIXELATION
    - Output: output/[id]/video.mp4 (1920×1080, ~200–400 MB)
11. Visual gate: score ≥ 14/16 — revise if fails
12. Thumbnail: Pollinations Flux 1280×720 + Pillow overlay → output/[id]/thumbnail.jpg
13. Metadata: title × 5 + description + tags → output/[id]/metadata.json
14. SEO gate: score ≥ 18/22 — revise if fails
15. Publish: YouTube API upload scheduled private → save youtube_id
    - Long videos: upload thumbnail via thumbnails().set() ✅ works
    - Schedule: 7 days after previous long video, at 14:00 UTC (5 PM Riyadh)

---

## Video Design Rules (NEVER VIOLATE)

### Short Videos (Reels/Shorts):
- **NO text overlays in center of screen** — مشاهد حية تملأ الشاشة بالكامل
- **Captions ONLY at bottom** — KaraokeCaption component, word-by-word synced to audio
- **Ken Burns effect** on every background segment (zoom-in / zoom-out / pan)
- **Dark gradient overlay** at bottom 35% only — for caption readability
- **Impact flash** on "impact" segments — subtle, no text
- **Number stat badge** — small, positioned above captions (bottom 320px), NOT center screen
- Background: Pexels stock videos via SegmentBackground component
- Max 6–8 words per segment, 12–16 segments per 50s video

### Long Videos (Documentary):
- **Composition**: DocumentaryVideo.tsx — full-screen AI images + Ken Burns + crossfade
- **NO hardcoded stat cards** — pure cinematic visuals driven by images
- **Cinematic Ken Burns**: 5 modes cycling — zoom_in, zoom_out, pan_left, pan_right, tilt_up
- **Crossfade**: imageA → imageB at 55% through each section (18-frame fade)
- **Chapter badge**: animated slide-in at top-left, shows for 3s then fades
- **Karaoke captions**: bottom 90px offset, font 58px, 5 words/line
- **Progress bar**: top of screen showing overall video progress
- **Color themes**: islamic (gold), wealth (green), science (cyan), military (red), ancient (orange)
- **Image resolution**: 1920×1080 ONLY — never render images at wrong size
- **Video quality**: CRF 18 + preset slow + maxrate 20M — MANDATORY for no pixelation

### Stickman Animation (for both Shorts and Long):
- Use the `StickmanScene` Remotion component for segments that explain a concept or tell a story
- Stickman scenes replace or overlay static images when the content benefits from character motion
- Characters: walking, running, pointing, thinking, falling, celebrating — synced to audio
- Used in: explainer segments, comparison scenes, "before/after" moments, cause-effect demonstrations
- Implementation: `video/remotion-project/src/components/StickmanScene.tsx`
- Trigger words in script that suggest stickman: "imagine", "picture this", "a person", "when someone", "step by step"
- Never use stickman for: historical documentary footage, real-world statistics, breaking news topics

### Thumbnail Design (MrBeast/Veritasium standard):
- Bright vivid AI-generated background (Pollinations Flux)
- Dark overlay on bottom 50% for text readability
- Top accent bar (14px) + bottom accent bar
- Category pill badge at top center
- ONE giant shocking stat as hero (huge, glowing)
- Max 2 lines of text (all-caps, outline stroke width=7)
- FACTFORGE watermark bottom center
- Save as JPEG quality=95 (NEVER PNG — causes black display on YouTube)

### Word Timestamps (MANDATORY for every video):
- Use faster-whisper "base" model with word_timestamps=True
- Store in remotion_props.json under "wordTimestamps" array
- Format: [{word, start_ms, end_ms}, ...]
- KaraokeCaption reads these for live word-by-word sync

### Audio/Video Sync (CRITICAL):
- Always check actual audio duration: `ffprobe -v quiet -print_format json -show_format audio.mp3`
- Set totalDurationFrames = ceil(audio_duration_seconds × fps) — use 60 for Shorts, 30 for Long docs
- Align segment startFrame/endFrame to word timestamps using keyword matching
- Verify: last segment endFrame == totalDurationFrames

---

## User Commands (Simple)

| Command | ماذا يفعل |
|---------|-----------|
| `produce` | ابدأ الإنتاج الكامل للفكرة التالية — اعرضها أولاً وانتظر الموافقة |
| `upload` | ارفع مقاطع اليوم المجدولة (3 مقاطع) عبر `python3 scripts/schedule_uploads.py` |
| `schedule` | اعرض جدول النشر الكامل مع التواريخ والمواعيد — `python3 scripts/schedule_uploads.py --plan` |
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

## Publish Schedule

- **وقت النشر الثابت: الساعة 5:00 عصراً (توقيت الرياض) = 14:00 UTC**
- **Shorts (Reels):** مقطع واحد كل يومين (يوم ويوم لا) — `SHORT_EVERY_N_DAYS = 2`
- **Long videos:** مقطع واحد كل أسبوع — `LONG_EVERY_N_DAYS = 7`
- كل رفع يكون `privacyStatus: "private"` مع `publishAt` — ينشر تلقائياً في موعده

---

## Project Created
April 2026
Channel: FactForge
Working directory: /Users/ar/Development/projects/FactForge
