# FactForge — Audio Engineering Standards

## 3-Tier Audio Architecture

Every video must have exactly these three layers:

```
┌─────────────────────────────────────────────────┐
│  TIER 1 — BGM (Background Music)                │
│  Volume: 8% | Type: ambient_documentary         │
│  Kevin MacLeod "Perspectives" CC BY 4.0         │
│  Fade in: 1s | Fade out: 2s                     │
├─────────────────────────────────────────────────┤
│  TIER 2 — Precision SFX                         │
│  Max 5 events per 40s video                     │
│  Min 3-second gap between events                │
│  Context-matched to video topic                 │
├─────────────────────────────────────────────────┤
│  TIER 3 — Ambient Bed (future)                  │
│  Topic-specific: ocean waves, city, forest...   │
└─────────────────────────────────────────────────┘
```

## Topic SFX Library

| Topic | Transition | Stat/Number | Impact | Hook |
|-------|-----------|-------------|--------|------|
| Ocean | water_transition | sonar_ping | pressure_boom | bubble_burst |
| Space | space_whoosh | sci_fi_beep | space_thud | radio_static |
| Economy | money_whoosh | coin_drop | market_crash | cash_register |
| Tech/AI | tech_whoosh | keyboard_click | system_alert | digital_glitch |
| History | parchment_rustle | typewriter_click | dramatic_sting | bell_toll |
| Universal | soft_whoosh | reveal_sting | hard_impact | tension_build |

## SFX Placement Rules

### MANDATORY
- Hook segment (i=0): ALWAYS fire hook SFX at 0ms
- Final segment: ALWAYS fire reveal_sting (universal)

### STRATEGIC (not mechanical)
- Stat SFX: fire on segments with type="stat" or "number"
- Impact SFX: fire on segments with type="impact"
- Transition SFX: MAX 3 across entire video, at ~25%/50%/75% positions

### PROHIBITED
- NEVER fire 2 SFX within 3 seconds of each other
- NEVER apply whoosh on every single transition (old broken behavior)
- NEVER use the same SFX for ocean content that you'd use for tech content

## Vocal Humanization

### TTS Pause Injection (in script writing)
Use punctuation to force natural pauses in Kokoro TTS:

| Effect | Technique |
|--------|-----------|
| Short pause (200ms) | Comma: `word, word` |
| Medium pause (300ms) | Em dash: `word — word` |
| Long dramatic pause (500ms) | Period + new sentence |
| Emphasis | Capitalize word: `ZERO percent` |

### Dramatic Pause Trigger Words
Words that should always have a pause AFTER them:
`but`, `however`, `yet`, `instead`, `actually`, `wait`, `only`, `just`

Example: `"We thought we knew everything. But — we were wrong."`

### Speed Variation
- Hook: 1.05 (slower for impact)
- Body: 1.08 (standard)
- Stats: 1.05 (let numbers land)
- CTA: 1.10 (faster energy)

## Hook Optimization (First 1.5 Seconds)

Every video MUST open with:
1. **Visual**: zoom-in Ken Burns on the most shocking/beautiful frame
2. **Verbal**: max 12 words, must contain a shock word
3. **Audio**: hook SFX fires at frame 0, 0ms

### Shock Words Checklist
The hook sentence must contain at least one of:
`never`, `impossible`, `zero`, `only`, `less than`, `more than`, `billion`, `million`,
`discovered`, `banned`, `secret`, `hidden`, `nobody`, `everybody`

### Bad Hook Examples (too generic)
- "Welcome to this video about the ocean" ❌
- "Did you know the ocean is deep?" ❌
- "Today we'll learn about marine biology" ❌

### Good Hook Examples (high retention)
- "We have better maps of Mars than our own ocean floor." ✅
- "Only 5 people have ever reached the bottom." ✅
- "Scientists discover 3,200 new species — in one year." ✅

## Visual Pacing — 2-Second Rule

For Shorts (35–60s):
- Every segment must be 2–3.5 seconds long
- 14–18 segments per 50s video = scene change every ~2.8s
- Every segment MUST have a distinct kenBurns direction
- No two consecutive segments with same kenBurns value

Pattern interrupt types:
- `zoom-in` → forces viewer focus on center
- `zoom-out` → reveals scale/context
- `pan-left` / `pan-right` → lateral movement
- `tilt-up` → reveals height/aspiration
- Cut (hard scene change) → provided by new segment background

For Long Docs (10–15 min):
- Image crossfade at 55% of each section
- ChapterTransition flash between sections (28 frames)
- BGM swell at chapter transitions

## Audio Asset Locations

```
audio_engineering/
  assets/
    sfx/
      ocean/      sonar_ping, bubble_burst, pressure_boom, water_transition, depth_tone
      space/      sci_fi_beep, space_whoosh, space_thud, radio_static
      economy/    coin_drop, cash_register, market_crash, money_whoosh
      tech/       digital_glitch, keyboard_click, system_alert, tech_whoosh
      history/    bell_toll, typewriter_click, dramatic_sting, parchment_rustle
      universal/  soft_whoosh, hard_impact, reveal_sting, tension_build
    music/
      (future: topic-specific ambient beds)
  generate_sfx.py   → regenerate all assets: python3 audio_engineering/generate_sfx.py
  sfx_config.json   → topic→SFX mapping + placement rules
  docs/
    audio_standards.md   ← this file

assets/
  ambient_documentary.mp3   → Kevin MacLeod Perspectives (BGM)
  sfx/                      → legacy SFX (ding, impact, slots, tension, whoosh)
```

## Regenerating Assets

```bash
# Generate all SFX (first time or after code changes)
python3 audio_engineering/generate_sfx.py

# Force regenerate a single topic
python3 audio_engineering/generate_sfx.py --topic ocean --force

# Force regenerate everything
python3 audio_engineering/generate_sfx.py --force
```
