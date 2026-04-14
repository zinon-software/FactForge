# Skill: Write Script
# Use this skill whenever writing a video script for any format
# ⚠️ content_psychology.md MUST be applied to every script — no exceptions

---

## ⚠️ BEFORE WRITING ANY SCRIPT — MANDATORY STEPS

1. Read `.claude/skills/content_psychology.md` completely
2. Choose ONE hook formula (A/B/C/D/E/F — rotate, don't repeat last used)
3. Plan the open loop: what question stays unanswered until the end?
4. Map 3 emotional triggers (AWE / OUTRAGE / VALIDATION / FEAR / PRIDE / DISBELIEF / NOSTALGIA)
5. Plan escalation: identify Level 1, Level 2, Level 3 facts
6. Write the script using the pacing blueprint below
7. Score script using Content Score Checklist (Part 8 of content_psychology.md)
8. Only proceed to voice generation if score >= 80
9. Save score to `output/[id]/script_score.json`

---

## SHORT VIDEO PACING BLUEPRINT (58 seconds)

```
[0-3s]   HOOK          → [SLOW] max 12 words, one of 6 hook formulas
[3-5s]   PAUSE + TEASE → [PAUSE] "Here's what most people don't know..."
[5-20s]  BUILD         → [FAST] Level 1 facts, short sentences, rising tension
[20-22s] OPEN LOOP     → mention what's coming without revealing it
[22-40s] ESCALATE      → Level 2 facts, "But here's where it gets strange..."
[40-43s] RE-HOOK       → "But the real shock is this..." (recaptures late viewers)
[43-52s] PEAK          → [SLOW] Level 3 fact, maximum weight, [PAUSE] after
[52-55s] LOOP CLOSE    → pay off the open loop promise
[55-58s] CTA           → rotate formula (never repeat last used)
```

## LONG VIDEO PACING BLUEPRINT (10–13 minutes)

```
[0:00-0:08]  COLD OPEN    → Level 3 fact first, no context, [PAUSE2]
[0:08-0:30]  RE-ESTABLISH → "Here's the full story behind that..."
[0:30-1:00]  PROMISE      → 3 open loops promised, shocking implication stated
[1:00-2:30]  CONTEXT      → Background, make audience care
[2:30-4:00]  FIRST ACT    → Facts 10-6, Level 1, close open loop 1
[4:00-4:15]  PATTERN INT  → Sudden pace change or unexpected stat
[4:15-6:00]  SECOND ACT   → Facts 5-3, Level 2, close open loop 2
[6:00-6:30]  RE-HOOK      → "We're about to get to the one that changes everything"
[6:30-8:30]  CLIMAX       → Facts 2-1, Level 3, [SLOW], [PAUSE2], close open loop 3
[8:30-9:30]  IMPLICATION  → What this means for you/the world/the future
[9:30-10:00] CTA          → Formula 5 (Continuation) preferred
```

## DOCUMENTARY CHAPTER FORMAT (for DocumentaryVideo composition)

Each chapter in script.json must have:
```json
{
  "id": "ch_[name]",
  "type": "hook|explainer|deep_dive|solution|cta",
  "chapter_num": 0,
  "title": "Chapter Title (shown on screen)",
  "image_prompt": "ultra-cinematic photorealistic AI image prompt, specific scene, dramatic lighting, 8K",
  "tts_script": "Full spoken text for this chapter. No script tags — pure spoken text."
}
```

Image prompt quality rules:
- Always include: cinematic, photorealistic, dramatic lighting, specific era/location
- Never generic: "a scene" → specific: "interior of House of Wisdom Baghdad 830 AD, scholars studying manuscripts, golden lamplight, Islamic arches"
- Add: "8K", "ultra-detailed", "volumetric light" for highest quality
- Different mood per chapter: hook=epic, darkness=bleak, climax=tragic, legacy=hopeful

## TTS TAGS
- `[SLOW]` → -20% speed: hooks, Level 3 facts
- `[FAST]` → +20% speed: lists, building tension
- `[PAUSE]` → 0.5s silence: after revelations
- `[PAUSE2]` → 1.0s silence: major transitions
- `[BREATH]` → natural breath between long sentences
- `[SCENE CHANGE]` → visual cue for video editor

## CONTENT SCORE (must be 80+)
- Hook: 30pts | Retention: 30pts | Emotion: 15pts | TTS: 15pts | CTA: 10pts
- Save: `output/[id]/script_score.json`
- Format: `{"score": 87, "approved": true, "hook_formula": "A", "emotions": ["DISBELIEF", "OUTRAGE", "AWE"]}`

---

## Core Principle

Scripts are written for TEXT-TO-SPEECH, not for reading. Every sentence must sound natural when spoken aloud by a neutral AI voice. If it would be weird to say out loud, rewrite it.

---

## TTS Optimization Rules (CRITICAL — follow every time)

### Sentence Structure
- Maximum 15 words per sentence
- One idea per sentence
- No complex subordinate clauses
- Start strong — never begin with "In this video" or "Hello everyone" or "Welcome back"

### Numbers
- Always write numbers as words: "two hundred billion" not "$200B"
- Spell out years: "nineteen eighty-four" not "1984" (unless script tag says otherwise)
- Exception: when the NUMBER IS the shock — "four hundred billion dollars" hits harder than writing out small numbers
- Percentages: "forty percent" not "40%"

### Punctuation That Gets READ ALOUD (avoid these)
- Never use: "..." — TTS reads it as a pause sound
- Never use: ";" — causes unnatural pause
- Never use: ":" — causes unnatural pause
- Never use: "&" — TTS reads "ampersand"
- Never use: "#" — TTS reads "hashtag" or "number sign"
- Use commas and periods only

### Abbreviations (always expand)
- "US" → "United States"
- "UK" → "United Kingdom"
- "GDP" → "gross domestic product"
- "CEO" → "chief executive officer"
- Exception: extremely common abbreviations spoken as words (NASA, FIFA)

### Script Tags (stripped before TTS, used for voice processing)
- `[PAUSE]` — insert 0.5 second silence here
- `[SLOW]` — next phrase spoken 20% slower for emphasis
- `[FAST]` — next section spoken 10% faster (use for list items)
- `[BREAK]` — insert 1.0 second silence (between major sections)

---

## Short Video Script Structure (45-58 seconds)

```
[HOOK — 0 to 5 seconds]
One shocking sentence. No intro. No greeting. Drop the most surprising fact immediately.
Example: "One man was so rich he crashed the entire global gold market just by traveling."

[BUILD-UP — 5 to 35 seconds]
Facts delivered fast. Three to six sentences. Each sentence builds on the last.
Each sentence must end with curiosity for the next.
[PAUSE] between each major fact reveal.

[PEAK — 35 to 50 seconds]
[SLOW] The most shocking fact saved for here. [PAUSE]
The "wait, what?" moment.
One to three sentences maximum.

[CTA — 50 to 58 seconds]
"Follow for more facts that will change how you see the world."
Or: "Like if this surprised you."
Keep it under 8 seconds.
```

**Word count target for shorts:** 120-160 words (45-58 seconds at natural speech pace)

---

## Long Video Script Structure (8-13 minutes)

```
[HOOK — 0 to 30 seconds]
Most shocking fact from the entire video. Delivered immediately.

[INTRO — 30 seconds to 2 minutes]
What we'll cover. Why it matters. Brief credibility signal.
"In the next ten minutes, you'll see data that most history books never mention."

[SECTION 1 through SECTION 5-7 — 2 minutes to 11 minutes]
Each section:
- Section title (spoken)
- Three to five facts building to a climax
- Transition to next section ("But that's not even the strangest part...")

[CONCLUSION — 11 to 12 minutes]
Callback to hook. Bigger picture. What should viewer think about now?

[CTA — 12 to 13 minutes]
Subscribe. Mention a related video.
```

---

## Style Rules

- Tone: Conversational, confident, slightly provocative. Like a smart friend who just learned something amazing.
- Avoid academic language ("Furthermore", "Moreover", "It should be noted")
- Use conversational connectors: "Here's the thing", "But wait", "And it gets worse", "Now here's where it gets crazy"
- Ask a question at the 30-second mark to re-engage viewer
- Never editorialize politically — let the facts speak
- Never say "amazing" or "incredible" — show don't tell

---

## Quality Checklist Before Saving

- [ ] Hook sentence delivered in first 5 seconds
- [ ] No sentence longer than 15 words
- [ ] All numbers written as words
- [ ] No banned punctuation (... ; :)
- [ ] All abbreviations expanded
- [ ] Script tags added ([PAUSE], [SLOW], [FAST])
- [ ] Total word count within target range
- [ ] CTA included at end
- [ ] Reads naturally when spoken aloud (read it yourself)
