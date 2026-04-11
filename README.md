# FactForge — YouTube Automation System

Automated YouTube channel producing educational short and long videos about Islamic/Arab history, world statistics, and geopolitical comparisons.

---

## Requirements

- macOS Apple Silicon M4 (also works on Intel/Linux)
- Python 3.11+
- Node.js 18+
- FFmpeg
- Anthropic API key (Claude)
- YouTube Data API v3 credentials
- Pexels API key (free)
- Serper API key (free tier available)

---

## Quick Setup (New Machine)

```bash
# 1. Clone the repository
git clone <repo-url>
cd FactForge

# 2. One-command setup
bash setup.sh

# 3. Activate virtual environment
source venv/bin/activate

# 4. Fill in your API keys
nano .env
```

---

## YouTube API Setup (5 minutes)

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project named `youtube-automation`
3. Go to **APIs & Services → Library**
4. Search **"YouTube Data API v3"** → Enable it
5. Go to **APIs & Services → Credentials**
6. Click **Create Credentials → OAuth 2.0 Client ID**
7. Application type: **Desktop App**
8. Download the JSON file
9. Save it as: `config/youtube_credentials.json`

---

## Getting API Keys

### Anthropic (Claude)
1. Go to [console.anthropic.com/keys](https://console.anthropic.com/keys)
2. Create a new API key
3. Add to `.env` as `ANTHROPIC_API_KEY=sk-ant-...`

### Pexels (free stock video)
1. Go to [pexels.com/api](https://www.pexels.com/api/)
2. Sign up and get your free API key
3. Add to `.env` as `PEXELS_API_KEY=...`

### Serper (Google Search API)
1. Go to [serper.dev](https://serper.dev)
2. Sign up — free tier includes 2,500 searches/month
3. Add to `.env` as `SERPER_API_KEY=...`

---

## Usage

```bash
# Activate virtual environment first
source venv/bin/activate

# Show current system status
python main.py

# Generate the full idea database (10,000 ideas)
python main.py generate-ideas

# Show next 10 ideas in production queue
python main.py queue

# Produce next video (interactive — asks for confirmation)
python main.py produce

# Add your own custom idea to top of queue
python main.py add-idea "The Reason Saudi Arabia Is Building a City With No Cars"

# Update trending topics from Google Trends
python main.py refresh-trends

# Run weekly self-improvement analysis
python main.py improve
```

---

## How to Resume After a Break

Tell Claude Code in this project folder:
> "Read CLAUDE.md and show me the current status"

Claude will read `.claude/CLAUDE.md` and `state/progress.json` and resume automatically.

---

## Project Structure

```
.claude/         → Claude brain (CLAUDE.md) and skills files
agents/          → Production pipeline agents
config/          → Settings and content rules
database/        → 10,000+ video ideas + trending topics
output/          → Generated videos (gitignored)
state/           → Production state, queue, analytics
utils/           → Shared utilities
video/           → Remotion video rendering project
main.py          → Main entry point
idea_generator.py → Generates idea database
```

---

## Content Philosophy

FactForge produces **factual, verifiable, educational** content:
- Every statistic cited from official sources (World Bank, IMF, Britannica)
- No opinions — facts and comparisons only
- YouTube Community Guidelines compliant always
- Sources cited in every video description

---

## GitHub Setup

```bash
git init
git add .
git commit -m "FactForge YouTube Automation System"
git remote add origin <your-repo-url>
git push -u origin main
```

Note: `.env` and `output/` are gitignored — never committed.
