# YouTube Automation System — Permanent Brain
# Read this file at the START of every Claude Code session.

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

1. Read this file (you are doing that now)
2. Read `state/progress.json` — what was last being produced
3. Read `state/queue.json` — what ideas are next
4. Report current status to user
5. Wait for user command before doing anything

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
User command → agents/ → output/[id]/ → YouTube API
                ↓
          state/ (progress, queue, analytics)
                ↓
          database/ (ideas, used_ideas, trending)
```

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

## Production Pipeline (Phase 3)

When user says "produce next video":
1. Read queue.json → show next idea → ask for approval
2. Research: web search → verify facts → save to output/[id]/research.json
3. Script: write TTS-optimized script → save to output/[id]/script.json
4. Voice: Kokoro TTS (fallback: Edge TTS) → save to output/[id]/audio.mp3
5. Thumbnail: Pillow generation → save to output/[id]/thumbnail.png
6. Video: Remotion render → save to output/[id]/video.mp4
7. Metadata: title × 5 variants + description + tags + translations → output/[id]/metadata.json
8. Schedule: calculate optimal publish time
9. Publish: YouTube API upload → mark as produced in database

---

## User Commands

- `produce next video` → runs full production pipeline on next queued idea
- `show queue` → lists next 10 ideas in priority order
- `skip this idea` → removes from queue, moves to next
- `add idea: [topic]` → adds custom idea to top of queue
- `show analytics` → displays performance report
- `refresh trends` → runs trend_agent.py and adds new ideas
- `improve system` → runs improvement_agent.py analysis
- `resume` → reads this file + progress.json and continues

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
