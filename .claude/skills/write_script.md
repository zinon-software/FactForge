# Skill: Write Script
# Hollywood-Level Script Writing — Human-Sounding, Suspenseful, Dramatically Delivered
# ⚠️ content_psychology.md MUST be applied to every script — no exceptions

---

## ⚠️ BEFORE WRITING ANY SCRIPT — MANDATORY STEPS

1. Read `.claude/skills/content_psychology.md` completely
2. Read `state/hook_performance.json` — use `best_formula` if set (data-driven). If null, rotate A→B→C→D→E→F and don't repeat last used
3. Identify the ONE sentence in your research that would make someone stop scrolling — that's your hook
4. Plan the open loop: what question must be answered before the viewer can leave?
5. Map 3 emotional triggers (AWE / OUTRAGE / VALIDATION / FEAR / PRIDE / DISBELIEF / NOSTALGIA)
6. Find the "slow burn" path: quiet opening → creeping dread → explosive peak
7. Write the script using the Hollywood craft rules below
8. Score script ≥ 80/100 (content_psychology.md) — revise if fails
9. Save score to `output/[id]/script_score.json`

---

## THE CORE PHILOSOPHY — READ THIS FIRST

A great script is NOT a list of facts read aloud.
It is a **story with a crime at the end** — the crime being a fact so shocking it changes how you see the world.

The viewer is not a student. They are a suspect. Pull them in as a co-conspirator.

"Here's what they never tell you."
"This number was classified for forty years."
"The man who discovered this was fired the next day."

Every sentence is a **micro-hook**. Every sentence creates a reason to hear the next one.
If a sentence doesn't earn the next sentence, cut it.

---

## THE 9 HOLLYWOOD CRAFT RULES

### Rule 1 — The Confession Tone
Write like you're leaning in and whispering something dangerous.
Not: "The United States has significant wealth inequality."
But: "The bottom fifty percent of Americans — combined — own less than one percent of the country's wealth."

Don't announce the fact. **Confess it.**

---

### Rule 2 — The Slow Burn
Start cold. Start quiet. Build dread.

BAD: "Today we're going to talk about one of the most shocking financial crimes in history."
GOOD: "It started with a normal Tuesday morning. A wire transfer. Three hundred million dollars. Gone."

Let the audience realize the scale before you tell them the scale.
The slow burn peaks at the 40-second mark (for shorts) or the 6-minute mark (for longs).

---

### Rule 3 — Micro-Cliffhangers at Every Sentence Break
The period is a cliff edge. The next sentence is the rope.

WEAK: "He became the richest person in medieval history. He owned half the gold in the world."
STRONG: "He became the richest person in medieval history. But that's not the part that should frighten you."

Techniques:
- "But here's what nobody talks about."
- "And that was just day one."
- "The number gets worse."
- "Wait until you hear what happened next."
- End a sentence on a fragment that demands completion.

---

### Rule 4 — Pattern Interrupts
Viewers tune out after 7–10 seconds of the same rhythm.
**Shatter the pattern.**

Techniques:
- Sudden short sentence after long ones. "Stop."
- A question thrown at the viewer: "Can you guess what happened next?"
- A tonal shift: from quiet to explosive, from data to personal
- A timestamp anchor: "Nineteen seventy-three. One phone call. Everything changed."

In a 58-second short: use at least 2 pattern interrupts.
In a 12-minute long: use one every 90 seconds.

---

### Rule 5 — Specificity as Weapon
Vague claims bounce off the brain. Specific claims stick like a knife.

DEAD: "An enormous amount of money was involved."
ALIVE: "Four hundred and twelve billion dollars. In one afternoon."

DEAD: "It happened a long time ago."
ALIVE: "August fourteenth, twelve sixty-eight. The last night before everything burned."

Rules:
- Names beat titles: "Ahmad ibn Fadlan" beats "a medieval traveler"
- Dates beat eras: "in the fall of 1929" beats "in the early twentieth century"
- Exact numbers beat approximations: "three million, two hundred thousand" beats "millions"
- Locations beat regions: "in a basement in São Paulo" beats "in South America"

---

### Rule 6 — The Pause as a Weapon
[PAUSE] is not punctuation. It is a **knife pressed against the skin.**

Use [PAUSE] only after the most devastating sentence. Then let it breathe.
The silence makes the viewer sit in the fact. Feel its weight. Let it expand.

Never use more than 2 pauses in a short video.
In a long video: one pause per major revelation. No more.

The pause after the peak fact is the most powerful moment in the video.

---

### Rule 7 — Human Fingerprints
AI-generated scripts are smooth. Perfectly structured. Lifeless.
Human scripts are jagged. Imperfect. Alive.

**Techniques to sound human:**

Fragments. Like this one.

Starting sentences with "And." or "But." (Grammarians would wince. Good.)

Repetition for emphasis: "He lost everything. Not some of it. Everything."

Self-interruption: "He had forty years to fix it. Forty years. He did nothing."

The rhetorical pivot: "You'd think that would be the end. It wasn't."

Collapsing to plain language at the peak: don't write "the mortality rate was catastrophic" — write "half of them died."

---

### Rule 8 — Hollywood 3-Act Compressed to 58 Seconds

**Act 1 — The World Before (0–10 seconds)**
Everything was normal. Set the scene fast. One or two sentences.

**Act 2 — The Disruption (10–45 seconds)**
Something happens. Facts escalate. Each fact is worse than the last.
This is where the slow burn lives. This is where micro-cliffhangers stack.

**Act 3 — The Aftermath (45–55 seconds)**
The peak revelation. [PAUSE]. What it means.
Not a summary. A detonation.

**CTA (55–58 seconds)**
Short. Human. Never corporate.

---

### Rule 9 — Voice Performance Direction
Beyond [SLOW] and [FAST], the script should specify emotional delivery.

Available performance tags:
- `[SLOW]` — -20% speed: use for hooks, peak facts, devastating truths
- `[FAST]` — +15% speed: lists, background context, buildup sequence
- `[PAUSE]` — 0.5s silence: after the most important fact
- `[PAUSE2]` — 1.0s silence: after the most devastating fact (use once per video)
- `[BREATH]` — natural breath pause between long sentences
- `[RISE]` — voice should feel like it's building tension (use at start of escalation)

Rhythm rules:
- Short sentences at emotional peaks (1–6 words)
- Longer sentences during context/buildup
- Never more than 3 long sentences in a row without a short sentence to punctuate
- The final peak sentence should be 8 words or less

---

## SHORT VIDEO PACING BLUEPRINT (45–58 seconds)

```
[0–3s]   COLD HOOK      [SLOW] One sentence. The worst fact. No context.
                         Not "today we'll discuss" — drop into the story mid-scene.

[3–7s]   THE PULL       "Here's what nobody tells you about this."
                         Open the loop. Don't close it.

[7–22s]  THE BUILD      [RISE] 3–4 facts, each darker than the last.
                         Short sentences. Micro-cliffhangers. One pattern interrupt.

[22–25s] OPEN LOOP PAY  "But none of that explains the number I'm about to tell you."
                         Re-commit the viewer to staying until the end.

[25–42s] THE ESCALATION Level 2 facts. Specificity. Names, dates, exact numbers.
                         "And that was just the first week."

[42–44s] PATTERN INT    One sudden short sentence. Stop the rhythm.

[44–52s] THE PEAK       [SLOW] Level 3 fact. Maximum weight.
                         8 words or less for the peak sentence.
                         [PAUSE2]

[52–55s] AFTERMATH      One sentence: what this means. No summary. A gut punch.

[55–58s] CTA            Human, not corporate. Rotate formula. Under 8 words.
```

**Word count target:** 120–155 words (45–58 seconds at Kokoro am_echo pace)

---

## LONG VIDEO PACING BLUEPRINT (10–13 minutes)

```
[0:00–0:08]  COLD OPEN   [SLOW] Level 3 fact first. No context. Drop directly in.
                          [PAUSE2]

[0:08–0:35]  THE FRAMING "Here's the full story behind that number."
                          Who was involved. What was at stake.

[0:35–1:10]  THREE LOOPS Promise three things the viewer will learn.
                          Make each promise feel dangerous.

[1:10–2:30]  CONTEXT     Make the viewer care. Give them someone to root for.
                          Or fear.

[2:30–4:30]  FIRST ACT   Level 1 facts. Rising. Close open loop 1.

[4:30–4:45]  PATTERN INT Sudden pace change. Short sentence. Tonal shift.

[4:45–6:30]  SECOND ACT  Level 2 facts. Close open loop 2.
                          "We're not halfway through yet."

[6:30–7:00]  RE-HOOK     "What I'm about to tell you is the part history books skip."

[7:00–9:30]  CLIMAX      Level 3 facts. [SLOW]. [PAUSE2]. Close open loop 3.
                          The detonation.

[9:30–10:30] AFTERMATH   Implication. What does this mean for the world now?
                          Personal. Human. Not academic.

[10:30–11:00] CTA        Subscribe ask tied to the emotion of the video.
```

---

---

## SHORT VIDEO — SEGMENT STRUCTURE (remotion_props.json)

### Scene Count Rule
**14–18 segments for a 50-second video.**
Scene change every 2.5–3.5 seconds = Hollywood cinematic pacing.
3 segments for a 50-second video = a slideshow. That is not acceptable.

### Segment Object (every field is mandatory)
```json
{
  "text": "Four hundred thousand manuscripts. In one building.",
  "startFrame": 0,
  "endFrame": 180,
  "type": "hook",
  "backgroundVideo": "[id]/bg_videos/ancient_library.mp4",
  "scene_query": "ancient library scrolls candlelight medieval scholars",
  "kenBurns": "zoom-in",
  "highlightWords": ["Four hundred thousand"]
}
```

### scene_query — The Most Important Field

`scene_query` is what gets sent to Pexels to find the actual background footage.
It must describe **exactly what should be visible on screen at this spoken moment**.

**Rules:**
- 3–6 words, all English, visual and specific
- Match the EMOTION of the narration — not just the topic
- UNIQUE per video — every segment must have a different scene_query
- No two consecutive segments share the same backgroundVideo filename
- Never use vague words: "video", "footage", "clip", "scene", "background", "content"

**scene_query by narration type:**

| What is being said | What to show | Example scene_query |
|---|---|---|
| A shocking number | Data visualization | `"digital numbers screen glowing blue"` |
| Ancient history | Historical setting | `"Roman soldiers marching burning city"` |
| Modern crime | Urban/tech environment | `"hacker dark room multiple screens"` |
| A person's action | Person in context | `"businessman running through airport panic"` |
| Fear / dread | Atmospheric visual | `"dark storm clouds empty street night"` |
| Money / wealth | Financial imagery | `"gold coins waterfall luxury mansion"` |
| War / conflict | Military imagery | `"tank smoke battlefield aerial view"` |
| Science / tech | Lab / tech visual | `"scientist laboratory experiment blue glow"` |
| Revelation / shock | Dramatic cinematic | `"cinematic reveal spotlight empty stage"` |
| CTA / ending | Engaging/hopeful | `"sunrise city skyline aerial drone"` |

**Pattern: [subject] [action/state] [location/mood]**

### kenBurns per segment type
- hook → `"zoom-in"` (pulls viewer in)
- fact → `"pan-left"` or `"pan-right"` (lateral drift = information flow)
- impact → `"zoom-out"` (expands to show full scale)
- number → `"zoom-in"` (focuses on the stat)
- cta → `"pan-right"` (forward momentum)
- Alternate directions: never same kenBurns three segments in a row

### Segment Example — Full 50-second Short (14 segments)

For a video about the 2008 financial crash:
```
Seg 1  [hook]    "It started on a Tuesday morning."           scene_query: "empty trading floor new york dawn"
Seg 2  [fact]    "Three banks. Gone in seventy-two hours."    scene_query: "bank building exterior collapsed facade"
Seg 3  [fact]    "Eight million people lost their jobs."      scene_query: "unemployed man sitting street despair"
Seg 4  [impact]  "In six weeks."                              scene_query: "calendar pages flying fast blur"
Seg 5  [fact]    "The government had one choice."             scene_query: "washington dc capitol building storm clouds"
Seg 6  [number]  "$700 billion."                              scene_query: "money printing machine close up"
Seg 7  [fact]    "Paid by people who owned nothing."          scene_query: "working class family dinner table worried"
Seg 8  [impact]  "Not a single banker went to prison."        scene_query: "courthouse empty no defendant handcuffs"
Seg 9  [fact]    "The same banks got bigger."                 scene_query: "skyscraper bank building growing upward"
Seg 10 [fact]    "Bonuses paid that same year."               scene_query: "luxury party yacht champagne celebration"
Seg 11 [impact]  "Eighteen point four billion dollars."       scene_query: "gold coins waterfall slow motion"
Seg 12 [fact]    "Handed to the people who caused it."        scene_query: "businessman smiling signing document"
Seg 13 [peak]    "The system did not fail. It worked exactly as designed." scene_query: "dark government building night fog"
Seg 14 [cta]     "Follow. There are fifty more stories like this." scene_query: "sunrise city skyline drone aerial"
```

Notice: every scene_query is unique, visually specific, and matches the emotional moment of the narration.

---

## DOCUMENTARY CHAPTER FORMAT (for Long Video script.json)

Each chapter must have this exact structure:
```json
{
  "id": "ch_[name]",
  "type": "hook|explainer|deep_dive|solution|cta",
  "chapter_num": 0,
  "title": "Chapter Title (shown on screen)",
  "image_prompt": "ultra-cinematic photorealistic scene, specific location and era, dramatic lighting, 8K",
  "tts_script": "Full spoken text. Hollywood craft rules apply. No JSON tags in text."
}
```

Image prompt rules:
- Never generic ("a scene", "a building") — always specific ("traders in the port of Lisbon 1503, torchlight, fog")
- Always include: cinematic / photorealistic / dramatic lighting / era and location
- Add: 8K, ultra-detailed, volumetric light
- Mood must match chapter emotional weight: hook=epic, escalation=dark/dread, climax=bleak, legacy=haunting

---

## TTS OPTIMIZATION RULES (CRITICAL — every script, every time)

### Sentence Structure
- Maximum 15 words per sentence (shorter at emotional peaks)
- One idea per sentence
- No complex subordinate clauses
- Never begin with "In this video", "Hello everyone", "Welcome back"
- First word of first sentence must be a name, number, or action word

### Numbers (spoken form only — never digits)
- "$412 billion" → "four hundred and twelve billion dollars"
- "1268 AD" → "twelve sixty-eight"
- "40%" → "forty percent"
- Exception: when the raw number in words IS the shock — spell it out fully

### Banned Punctuation (TTS reads them as artifacts)
- "..." → use [PAUSE] instead
- ";" → split into two sentences
- ":" → use a comma or new sentence
- "&" → "and"
- "#" → spell out "number" or remove
- Em dash "—" → use comma or period

### Abbreviations (always expand)
- US → United States | UK → United Kingdom | GDP → gross domestic product
- CEO → chief executive officer | NATO → North Atlantic Treaty Organization
- Exception: acronyms spoken as words (NASA, FIFA, UNESCO)

---

## CTA ROTATION FORMULAS

Rotate these — never repeat the same one twice in a row:

1. **Disbelief confirmation**: "Follow if this surprised you."
2. **Continuation promise**: "The next video is even darker."
3. **Community invite**: "Drop the number you remember most."
4. **Challenge**: "Bet you didn't learn this in school. Follow for more."
5. **Scale reference**: "This is one of fifty stories like this. Follow to hear them all."
6. **Simple ask**: "Like if you want more facts like this."

---

## QUALITY CHECKLIST (score before saving)

### Structure
- [ ] First sentence is a hook — drops the story mid-scene, no intro
- [ ] Open loop established by second sentence
- [ ] At least 2 micro-cliffhangers ("but here's what nobody mentions")
- [ ] At least 1 pattern interrupt (sudden rhythm break)
- [ ] Peak fact saved for 80%+ through the video
- [ ] [PAUSE2] placed after the peak fact (and nowhere else)
- [ ] CTA is under 8 words, uses rotation formula

### Craft
- [ ] No sentence longer than 15 words (except slow burn buildups)
- [ ] At least 3 specific details: name, date, or exact number
- [ ] The slow burn path is clear: quiet → dread → detonation
- [ ] Human fingerprints present: fragment, repetition, or "And."/"But." sentence start
- [ ] No academic language (Furthermore, Moreover, It should be noted)
- [ ] No AI filler ("it's important to note", "this highlights", "notably")
- [ ] No summary at the end — aftershock only

### TTS Compliance
- [ ] All numbers written as words
- [ ] No banned punctuation
- [ ] All abbreviations expanded
- [ ] [PAUSE], [SLOW], [FAST] tags placed intentionally
- [ ] Total word count: 120–155 (short) or 1,800–2,200 (long)
- [ ] Reads naturally when spoken aloud

### Score
- [ ] Content score ≥ 80/100 (run content_psychology.md checklist)
- [ ] Save to: `output/[id]/script_score.json`

Format:
```json
{"score": 87, "approved": true, "hook_formula": "A", "emotions": ["DISBELIEF", "OUTRAGE", "AWE"]}
```

---

## EXAMPLE — Before and After

### BEFORE (AI-sounding, mechanical, dead):
"The Islamic Golden Age was a period of significant scientific and cultural advancement. Many important discoveries were made during this time. Scholars from across the world came to Baghdad to study. It is estimated that the House of Wisdom contained over four hundred thousand manuscripts."

### AFTER (Hollywood-level, human, alive):
"[SLOW] Four hundred thousand manuscripts. [PAUSE] In one building. And when the Mongols arrived — [PAUSE] they threw every single one into the river. The Tigris ran black with ink for three days.

But here's what the history books almost never mention.

Those manuscripts had taken six hundred years to collect. [RISE] Mathematics. Medicine. Astronomy. Philosophy. Translations from every civilization on earth. [PAUSE]

Gone. In a single afternoon.

And we are still recovering from that loss today."

---

Notice:
- Starts with the number (specificity as weapon)
- Second sentence is a fragment (human fingerprint)
- Micro-cliffhanger after "Mongols arrived"
- Pattern interrupt: "But here's what the history books almost never mention."
- [PAUSE2] after the peak
- Short sentences at the peak ("Gone. In a single afternoon.")
- No academic language, no summary
- Final sentence is a gut punch, not a wrap-up
