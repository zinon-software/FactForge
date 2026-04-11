# MASTER PROMPT — YouTube Automation System
# For: Claude Code
# Language: English
# Platform: macOS Apple Silicon M4

---

## 🔴 CRITICAL INSTRUCTIONS — READ BEFORE ANYTHING ELSE

You are building a **complete, production-grade YouTube automation system**.
You MUST implement EVERYTHING described in this document.
Do NOT skip any section.
Do NOT summarize or simplify.
Do NOT say "you can add this later."
If a step requires user input (like API keys), PAUSE, explain how to get it, wait for input, then continue.
Work ONE idea at a time when producing videos — never batch process without user command.
After completing each major phase, confirm completion and ask before proceeding.

---

## 📋 PROJECT OVERVIEW

Build an automated system that:
1. Maintains a database of 10,000 short video ideas + 500 long video ideas
2. Tracks trending topics and updates the database weekly
3. Takes one idea at a time and produces a complete YouTube-ready video
4. Generates: script → voice → video → thumbnail → title → description → tags → schedule
5. Publishes directly to YouTube via API with smart scheduling
6. Learns from performance and self-improves over time
7. Remembers all state permanently across sessions via files
8. Is fully GitHub-ready and portable to any machine

---

## 📁 COMPLETE PROJECT STRUCTURE

Build this exact structure — no shortcuts:

```
youtube-automation/
│
├── .claude/
│   ├── CLAUDE.md                  # Permanent brain — read this EVERY session
│   └── skills/
│       ├── write_script.md        # How to write perfect TTS-optimized scripts
│       ├── generate_title.md      # Hook title formula
│       ├── fact_check.md          # Verification rules
│       ├── thumbnail.md           # Thumbnail generation rules
│       ├── trend_research.md      # How to find trending topics
│       └── self_improve.md        # How to analyze and improve from results
│
├── .env                           # API keys — never commit this
├── .env.example                   # Template with empty values — commit this
├── .gitignore                     # Excludes .env, output/, __pycache__, etc.
├── README.md                      # Full setup instructions for any machine
├── requirements.txt               # All Python dependencies with versions
├── setup.sh                       # One-command setup script
│
├── config/
│   ├── settings.py                # All configuration constants
│   ├── content_rules.md           # Strict content guidelines (never violate)
│   └── publishing_schedule.md     # When to publish for maximum reach
│
├── database/
│   ├── ideas_short.json           # 10,000 short video ideas (<60 seconds)
│   ├── ideas_long.json            # 500 long video ideas (8-15 minutes)
│   ├── trending_topics.json       # Updated weekly from trend sources
│   └── used_ideas.json            # Tracks what has been produced
│
├── state/
│   ├── progress.json              # Current production state
│   ├── queue.json                 # Next ideas in production order
│   ├── analytics.json             # Performance data from YouTube
│   └── improvement_log.md         # Self-improvement notes and changes
│
├── agents/
│   ├── trend_agent.py             # Finds trending topics from multiple sources
│   ├── script_agent.py            # Writes TTS-optimized scripts
│   ├── fact_check_agent.py        # Verifies facts against official sources
│   ├── voice_agent.py             # Generates natural voice audio
│   ├── video_agent.py             # Produces video via Remotion
│   ├── thumbnail_agent.py         # Creates click-worthy thumbnails
│   ├── title_agent.py             # Generates hook titles and descriptions
│   ├── translation_agent.py       # Translates metadata to all languages
│   ├── publish_agent.py           # Uploads and schedules on YouTube
│   └── improvement_agent.py       # Analyzes results and improves system
│
├── video/
│   ├── remotion-project/          # Complete Remotion project
│   │   ├── package.json
│   │   ├── remotion.config.ts
│   │   └── src/
│   │       ├── Root.tsx
│   │       ├── compositions/
│   │       │   ├── ShortVideo.tsx      # Template for shorts (<60s)
│   │       │   └── LongVideo.tsx       # Template for long videos
│   │       └── components/
│   │           ├── ItemReveal.tsx      # Animated list item reveal
│   │           ├── CounterNumber.tsx   # Animated number counter
│   │           ├── ComparisonSplit.tsx # Side-by-side comparison
│   │           ├── ShockStat.tsx       # Shocking statistic display
│   │           ├── ProgressBar.tsx     # Countdown/progress bar
│   │           └── TextOverlay.tsx     # Styled text with RTL support
│   └── bridge.py                  # Python → Remotion communication
│
├── output/                        # Generated files (gitignored)
│   └── [video_id]/
│       ├── script.json
│       ├── audio.mp3
│       ├── thumbnail.png
│       ├── video.mp4
│       └── metadata.json
│
└── utils/
    ├── web_search.py              # Search and fetch from the web
    ├── text_cleaner.py            # Clean text for TTS
    ├── file_manager.py            # State persistence helpers
    └── token_optimizer.py         # Minimize API token usage
```

---

## 🔑 PHASE 0 — ENVIRONMENT SETUP

### Step 0.1 — Check and Install Dependencies

Check if installed, install if missing:
```bash
# Check Homebrew
brew --version || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install system dependencies
brew install ffmpeg git python@3.11 node

# Install Kokoro TTS for natural English voice
pip install kokoro-onnx soundfile numpy

# Install Python packages
pip install anthropic google-api-python-client google-auth-oauthlib \
            requests beautifulsoup4 pillow python-dotenv pytrends \
            APScheduler aiohttp asyncio edge-tts

# Install Remotion
npx create-video@latest remotion-project
cd remotion-project && npm install
```

### Step 0.2 — YouTube API Setup

PAUSE here and tell the user exactly:

```
To connect to YouTube, I need your API credentials.
Here is how to get them in 5 minutes:

1. Go to: https://console.cloud.google.com
2. Create a new project named "youtube-automation"
3. Go to "APIs & Services" → "Library"
4. Search "YouTube Data API v3" → Enable it
5. Go to "APIs & Services" → "Credentials"
6. Click "Create Credentials" → "OAuth 2.0 Client ID"
7. Application type: "Desktop App"
8. Download the JSON file
9. Save it as: config/youtube_credentials.json

Please do this now and tell me when ready.
```

Wait for confirmation before continuing.

### Step 0.3 — Create .env File

```env
# Anthropic
ANTHROPIC_API_KEY=

# YouTube
YOUTUBE_CREDENTIALS_PATH=config/youtube_credentials.json
YOUTUBE_TOKEN_PATH=config/youtube_token.json
YOUTUBE_CHANNEL_ID=

# Search APIs (free tiers)
PEXELS_API_KEY=
SERPER_API_KEY=

# Settings
OUTPUT_DIR=output
DATABASE_DIR=database
STATE_DIR=state
MAX_SHORT_DURATION=58
MAX_LONG_DURATION=900
PUBLISH_INTERVAL_HOURS=48
TIMEZONE=UTC
```

Guide the user to fill EACH key with exact instructions for each one.
Save filled values permanently. Never ask again.

---

## 🧠 PHASE 1 — BUILD THE PERMANENT BRAIN

### Step 1.1 — Create .claude/CLAUDE.md

This file is read at the START of every Claude Code session.
It must contain:

```markdown
# YouTube Automation System — Permanent Brain

## What This Project Does
Automated YouTube channel producing English-language educational/factual videos.
Three content angles:
1. Islamic & Arab perspective (underrepresented in English)
2. Shocking statistics and historical facts
3. Geopolitical comparisons (US vs China, East vs West, etc.)

## Current State
- Read state/progress.json for current production status
- Read state/queue.json for next ideas
- Read database/used_ideas.json for what's been produced

## Session Rules
1. Always read this file first
2. Never restart completed work — check progress.json
3. Work one idea at a time
4. Ask user before starting production of any idea
5. Save state after every major step
6. If interrupted, resume from last saved checkpoint

## Content Rules (NEVER VIOLATE)
- All facts must be verified from official sources
- No music — voice and natural sound effects only
- No controversial religious or political opinions
- Factual controversy only (prices, rankings, comparisons)
- YouTube-safe content at all times
- Cite sources in video description

## How to Resume
Tell me: "Read CLAUDE.md and continue from where we left off"
I will read progress.json and resume automatically.
```

### Step 1.2 — Build All Skills Files

Create each `.claude/skills/*.md` file with detailed instructions:

**write_script.md** must include:
- TTS optimization rules (short sentences, no punctuation read aloud)
- Numbers written as words
- Hook in first 3 seconds
- Engagement question at 30 seconds
- Call to action at end
- Target duration: 45-58 seconds for shorts, 8-12 minutes for long
- Style: conversational, confident, slightly provocative

**generate_title.md** must include:
- Hook formula: [Shocking fact/number] + [Emotional trigger] + [Curiosity gap]
- Examples of strong vs weak titles
- A/B testing variants (generate 5 titles per video, pick best)
- Forbidden words (clickbait that YouTube penalizes)

**fact_check.md** must include:
- Primary sources: Wikipedia, World Bank, Forbes, Statista, official government sites
- Secondary verification: cross-check 2+ sources
- Flag uncertain facts with [VERIFY] tag
- Never publish unverified statistics
- Always include source URL in metadata

**thumbnail.md** must include:
- High contrast colors (dark background, bright text)
- Maximum 3 words on thumbnail
- One shocking number or face
- 1280x720px for long videos, 1080x1920px for shorts
- Pillow generation code template

**trend_research.md** must include:
- Sources: Google Trends, YouTube trending, Reddit, Twitter/X, Google News
- How to evaluate trend strength
- How to angle trending topic into our 3 content pillars
- Freshness scoring system

**self_improve.md** must include:
- Weekly analytics review checklist
- What metrics matter (CTR, retention, shares)
- How to update title formulas based on data
- How to improve scripts based on retention dropoff points
- How to update idea priority scores

---

## 📊 PHASE 2 — BUILD THE IDEA DATABASE

### Step 2.1 — Research Trending Topics First

Before generating ideas, search these sources:
- Google Trends (pytrends): top rising queries in last 7 days
- YouTube trending page: scrape top 50 trending videos
- Reddit: r/todayilearned, r/interestingasfuck, r/worldnews — top posts this week
- Google News: top stories in categories: science, history, money, geopolitics

Store findings in `database/trending_topics.json`

### Step 2.2 — Generate 10,000 Short Video Ideas

Each idea must follow this JSON structure:
```json
{
  "id": "S00001",
  "title": "The Man Who Was Richer Than Today's Entire USA Economy",
  "angle": "islamic_history",
  "format": "shocking_stat",
  "hook": "One man controlled 25% of global GDP",
  "controversy_score": 85,
  "trending_score": 72,
  "evergreen_score": 95,
  "priority_score": 88,
  "estimated_duration_seconds": 52,
  "key_facts": ["Mansa Musa", "$400 billion adjusted", "Mali Empire 1324"],
  "sources": ["Forbes", "World History Encyclopedia"],
  "status": "pending",
  "produced_date": null,
  "youtube_id": null,
  "views": null,
  "ctr": null
}
```

**Format types** (vary across all 10,000 ideas):
- `top_10_list` — classic ranking
- `top_5_list` — faster paced
- `shocking_stat` — one mind-blowing fact expanded
- `comparison` — A vs B (country, company, person, era)
- `timeline` — how something evolved over time
- `myth_vs_fact` — debunking common beliefs
- `price_reveal` — cost of surprising things
- `size_comparison` — scale that's hard to comprehend
- `what_if` — hypothetical based on real data
- `hidden_truth` — mainstream narrative vs reality

**Content categories** (distribute evenly):
- Islamic & Arab history/civilization (angle 1)
- Shocking wealth & economics
- Military & geopolitical power
- Scientific discoveries & space
- Human body & medicine
- Ancient civilizations
- Modern technology & AI
- Natural world & animals
- Crime & justice systems
- Architecture & engineering feats
- US vs China comparisons (angle 3)
- East vs West comparisons (angle 3)
- Hidden facts about famous countries
- Price of surprising things (organs, islands, wars)

Generate ideas in batches of 500 to avoid token overload.
Save each batch immediately to `database/ideas_short.json`.
Show progress: "Generated 500/10000 ideas..."

### Step 2.3 — Generate 500 Long Video Ideas

Same structure but:
- Estimated duration: 8-15 minutes
- Deeper topics requiring research
- Each long video should correspond to a short video (expand the short)
- `id` prefix: `L00001`

### Step 2.4 — Build Priority Queue

Sort all ideas by:
```
priority_score = (trending_score × 0.4) + (controversy_score × 0.3) + (evergreen_score × 0.3)
```

Save top 100 as `state/queue.json` — these are produced first.

---

## 🎬 PHASE 3 — PRODUCTION PIPELINE

This runs ONE idea at a time when user commands: **"produce next video"**

### Step 3.1 — Select Next Idea
Read `state/queue.json`, take the highest priority pending idea.
Display to user: idea title, format, estimated duration.
Ask: "Shall I produce this idea? (yes/skip)"

### Step 3.2 — Deep Research
Search the web for the selected idea:
- Fetch top 5 search results
- Extract key facts and statistics
- Verify against at least 2 official sources
- Save verified facts + source URLs to `output/[id]/research.json`
- If facts cannot be verified → skip idea, log reason, pick next

### Step 3.3 — Write Script

**For SHORT videos (TTS-optimized):**
```
Structure:
- Hook (0-5s): One shocking sentence. No intro. No "hello".
- Build-up (5-35s): Facts delivered fast. Short sentences. 
- Peak (35-50s): The most shocking fact saved for here.
- CTA (50-58s): "Follow for more facts that will change how you see the world"

TTS Rules (CRITICAL):
- Maximum 15 words per sentence
- Write numbers as words: "two hundred billion" not "$200B"
- No punctuation that TTS reads aloud: no "..." no ";" no ":"
- No abbreviations: write "United States" not "US"
- Add [PAUSE] tag for 0.5 second pauses between sections
- Add [SLOW] tag for emphasis on key facts
- Add [FAST] tag for list items
```

**For LONG videos:**
```
Structure:
- Hook (0-30s): Most shocking fact first
- Intro (30s-2min): What we'll cover and why it matters
- Main content (2-11min): 5-7 sections with transitions
- Conclusion (11-12min): Callback to hook + bigger picture
- CTA (12-13min): Subscribe + related video mention
```

Save to `output/[id]/script.json`

### Step 3.4 — Generate Voice

Use **Kokoro TTS** (primary — local, free, natural):
```python
# Try Kokoro first (best quality, local)
# Fallback to Edge TTS en-US-AndrewNeural if Kokoro fails

# Pre-process script:
# 1. Remove all [PAUSE] tags → insert 0.5s silence
# 2. Remove all [SLOW] [FAST] tags → adjust TTS rate
# 3. Strip all punctuation that gets read aloud
# 4. Convert all numbers to spoken words
# 5. Expand all abbreviations

# Voice settings:
# - Speed: 1.05x (slightly faster than default = more engaging)
# - Pitch: neutral
# - Voice: male, clear, authoritative
```

Save to `output/[id]/audio.mp3`

### Step 3.5 — Generate Thumbnail

Use **Pillow** to create:

**Shorts thumbnail (1080×1920):**
- Dark gradient background (black to deep blue/red based on topic)
- Large shocking number or key word (max 3 words, 200px+ font)
- Subtle background image from Pexels API (blurred 80%)
- Channel watermark bottom right
- High contrast — must be readable at 100px wide

**Long video thumbnail (1280×720):**
- Split design: image left, text right
- Bright accent color border
- Face or relevant image on left
- 2-3 word hook on right in bold

Save to `output/[id]/thumbnail.png`

### Step 3.6 — Generate Video (Remotion)

Build Remotion templates for each format type:

**ShortVideo.tsx** — 1080×1920, 60fps, max 58 seconds:
- Full-screen background (video/image from Pexels, blurred slightly)
- Animated text reveals synced to audio timestamps
- Progress bar at bottom showing time remaining
- Each list item animates in with spring animation
- Numbers count up with CounterNumber component
- Smooth transitions between sections

**LongVideo.tsx** — 1920×1080, 30fps:
- Clean professional layout
- Section titles with animated underline
- Data visualizations for statistics
- Split screen for comparisons
- B-roll footage from Pexels between sections

Pass data via JSON props:
```json
{
  "script_segments": [...],
  "audio_file": "path/to/audio.mp3",
  "background_media": [...],
  "format": "top_10_list",
  "color_theme": "dark_blue"
}
```

Render with: `npx remotion render ShortVideo output/[id]/video.mp4`

Save to `output/[id]/video.mp4`

### Step 3.7 — Generate Metadata

**Title** (generate 5 variants, score each):
```
Scoring criteria:
- Contains number: +20 points
- Contains power word (secret, banned, shocking, real): +15 points  
- Creates curiosity gap: +25 points
- Under 60 characters: +10 points
- Triggers debate: +20 points
- Proven formula match: +10 points

Pick highest scoring title.
```

**Description template:**
```
[Hook sentence from script]

In this video:
[3-5 bullet points of what's covered]

Sources:
[List all verified sources with URLs]

---
New facts every 48 hours. Subscribe so you never miss one.

#facts #history #[topic_tags]
```

**Tags:** Generate 30 relevant tags mixing broad and specific.

**Translated metadata:** Use Claude to translate title + description + tags into:
Spanish, French, German, Hindi, Portuguese, Indonesian, Japanese, Korean, Turkish, Arabic
Save all translations to `output/[id]/metadata.json`

### Step 3.8 — Smart Scheduling

Calculate optimal publish time:
```python
# Best times to publish (YouTube analytics research):
# Tuesday-Thursday: 2pm-4pm EST
# Saturday: 9am-11am EST
# Never publish: Monday morning, Friday night

# Schedule next available optimal slot
# Minimum gap between videos: 48 hours
# Save scheduled time to state/queue.json
```

### Step 3.9 — Publish to YouTube

```python
# Upload video with:
# - video file
# - thumbnail
# - title (primary language: English)
# - description
# - tags
# - category: 27 (Education) or 24 (Entertainment)
# - privacy: private (until scheduled time)
# - scheduled publish time
# - multi-language metadata via YouTube API

# After upload:
# - Save YouTube video ID to database
# - Mark idea as "produced" in database
# - Update state/progress.json
# - Log success with timestamp
```

---

## 📈 PHASE 4 — SELF-IMPROVEMENT SYSTEM

### Step 4.1 — Analytics Collection (Weekly)

Every 7 days, fetch from YouTube Analytics API:
- Views, impressions, CTR, average watch duration, shares
- Save to `state/analytics.json`

### Step 4.2 — Pattern Analysis

Analyze performance and update:
```python
# Find: which title formulas get highest CTR
# Find: which topics get most shares  
# Find: at what timestamp viewers drop off (retention)
# Find: which thumbnail styles get most clicks
# Find: which posting times perform best

# Update: idea priority scores based on category performance
# Update: title formula weights in generate_title.md
# Update: script structure if retention data shows dropoff patterns
```

### Step 4.3 — Database Refresh

Every week:
- Run trend_agent.py to find new trending topics
- Add 100 new ideas based on current trends
- Reprioritize queue based on new data
- Archive ideas older than 6 months with low priority scores

### Step 4.4 — Log Improvements

Append to `state/improvement_log.md`:
```markdown
## [DATE] Weekly Improvement Report

### What Worked
- [Top performing video]: [why it worked]

### What Didn't Work  
- [Low performing video]: [why it failed]

### Changes Made
- Updated title formula: [change]
- Adjusted script structure: [change]
- Added new idea category: [change]

### Next Week Focus
- [Priority topics based on trends]
```

---

## 🛡️ CONTENT RULES — NEVER VIOLATE

Write these to `config/content_rules.md`:

```markdown
# Absolute Content Rules

## ALWAYS
- Verify every statistic from minimum 2 official sources
- Cite sources in every video description
- Use exact numbers with context ("$400B in today's money")
- Present multiple perspectives on controversial topics
- Keep content educational and informational in framing
- Follow YouTube Community Guidelines strictly

## NEVER
- Publish unverified statistics
- Make religious rulings or fatwas
- Attack specific living individuals
- Use copyrighted music (voice + natural SFX only)
- Sensationalize tragedies for views
- Make political endorsements
- Publish medical advice as fact without sources
- Use misleading thumbnails that don't match content

## SENSITIVE TOPICS (allowed with strict framing)
- Organ prices → frame as "medical economics" with WHO sources
- Military power → frame as "defense budget comparisons" with official data
- Religious history → frame as "historical facts" not theological debate
- Wealth inequality → frame as "economic data" not political agenda

## FACT-CHECK SOURCES (in order of trust)
1. World Bank, IMF, UN databases
2. Forbes, Bloomberg, Reuters, AP
3. Academic papers (Google Scholar)
4. Wikipedia (for references only, verify primary source)
5. Government official websites
```

---

## 🔧 TOKEN OPTIMIZATION RULES

Follow these to minimize Claude API costs:

```python
# 1. Use templates — never regenerate from scratch
# 2. Cache research results — don't search same topic twice
# 3. Batch similar operations — generate all metadata at once
# 4. Use smaller models for simple tasks (title generation)
# 5. Compress context — summarize old conversation history
# 6. Store results locally — never recompute what's saved
# 7. Use streaming for long outputs — process as they arrive
# 8. Split large tasks — 500 ideas per Claude call maximum
```

---

## 🐙 GITHUB SETUP

```bash
# Initialize repository
git init
git add .
git commit -m "Initial commit: YouTube Automation System"

# Create .gitignore (CRITICAL — never expose API keys)
echo ".env
output/
__pycache__/
*.pyc
config/youtube_credentials.json
config/youtube_token.json
node_modules/
.DS_Store
*.mp4
*.mp3" > .gitignore

# Create README.md with:
# - Project description
# - Requirements (Python 3.11, Node 18+, FFmpeg)  
# - Setup instructions (clone → setup.sh → add .env → run)
# - How to resume after cloning on new machine
# - How to add new API keys

# setup.sh (one-command install):
# !/bin/bash
# pip install -r requirements.txt
# cd video/remotion-project && npm install
# echo "Setup complete. Fill in .env file then run: python main.py"
```

---

## 🚀 EXECUTION ORDER

Execute phases in this exact order:

```
PHASE 0: Environment Setup
  → Install dependencies
  → Get YouTube API credentials from user  
  → Create .env with all keys
  ✓ Confirm: "Environment ready"

PHASE 1: Build Permanent Brain
  → Create CLAUDE.md
  → Create all 6 skills files
  ✓ Confirm: "Brain and skills ready"

PHASE 2: Build Idea Database
  → Research current trends
  → Generate 10,000 short ideas (in batches of 500)
  → Generate 500 long ideas
  → Build priority queue
  ✓ Confirm: "Database ready: 10,000 short + 500 long ideas"

PHASE 3: Test Production Pipeline (with idea #1)
  → Run complete pipeline on first idea
  → Show user the output before uploading
  → Ask for approval then publish
  ✓ Confirm: "First video produced and scheduled"

PHASE 4: Activate Self-Improvement
  → Schedule weekly analytics review
  → Schedule weekly database refresh
  ✓ Confirm: "System fully operational"
```

---

## 💬 HOW USER CONTROLS THE SYSTEM

After setup, user commands:

- **"produce next video"** → runs Phase 3 pipeline on next queued idea
- **"show queue"** → lists next 10 ideas in priority order
- **"skip this idea"** → removes from queue, moves to next
- **"add idea: [topic]"** → adds custom idea to top of queue
- **"show analytics"** → displays performance report
- **"refresh trends"** → runs trend research and adds new ideas
- **"improve system"** → runs self-improvement analysis
- **"resume"** → reads CLAUDE.md + progress.json and continues

---

## ⚡ FINAL REQUIREMENT

After completing ALL phases, create a summary file `SYSTEM_STATUS.md`:

```markdown
# System Status

## Setup Complete: [DATE]
## Ideas in Database: 10,000 short / 500 long
## Videos Produced: 0
## Next Video: [title of #1 in queue]
## Next Publish: [scheduled time]

## How to Resume in New Session
1. Open Claude Code in this project folder
2. Say: "Read CLAUDE.md and show me the current status"
3. Claude will read all state files and resume automatically

## API Keys Status
- Anthropic: ✓ configured
- YouTube: ✓ configured  
- Pexels: ✓ configured

## Weekly Automation
- Trend refresh: every Monday 9am
- Analytics review: every Sunday 8pm
- Database backup: every Friday 11pm
```

---

## 🔴 REMINDER TO CLAUDE CODE

You MUST complete every phase.
You MUST save state after every step.
You MUST verify facts before any script is written.
You MUST ask for API keys with clear instructions.
You MUST test the full pipeline before declaring complete.
You MUST NOT skip the database generation — all 10,000 ideas are required.
You MUST NOT produce multiple videos at once without user command.
When in doubt: save state, report status, ask user.

BEGIN WITH PHASE 0 NOW.
