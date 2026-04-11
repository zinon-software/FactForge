# FactForge — System Status

## Setup Complete: 2026-04-11
## Ideas in Database: 0 / 10,000 short, 0 / 500 long
## Videos Produced: 0
## Next Video: Run `python main.py generate-ideas` then `python main.py queue`

---

## Phase Status

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 0: Environment | ✓ Complete | Python 3.11 venv, Node 18, Remotion installed |
| Phase 1: Brain & Skills | ✓ Complete | CLAUDE.md + 6 skills files |
| Phase 2: Idea Database | ⏳ Pending | Run: `python main.py generate-ideas` |
| Phase 3: Pipeline Tested | ⏳ Pending | Run: `python main.py produce` |
| Phase 4: Self-Improvement | ⏳ Pending | Activates after first 10 videos |

---

## API Keys Status

| Service | Status | Notes |
|---------|--------|-------|
| Anthropic | ⚠️ Needs key | Add ANTHROPIC_API_KEY to .env |
| YouTube | ⚠️ Needs setup | See README.md — takes 5 minutes |
| Pexels | ⚠️ Needs key | Free: pexels.com/api |
| Serper | ⚠️ Needs key | Free tier: serper.dev |

---

## How to Resume in New Session

```
1. Open Claude Code in this project folder
2. Say: "Read CLAUDE.md and show me the current status"
3. Claude will read all state files and resume automatically
```

---

## Daily Commands

```bash
# Activate environment first
source venv/bin/activate

# Check status
python main.py

# Generate ideas (do this once — takes ~30-60 minutes)
python main.py generate-ideas

# Produce a video
python main.py produce

# See what's in the queue
python main.py queue
```

---

## Weekly Automation

- Trend refresh: Run `python main.py refresh-trends` every Monday
- Analytics review: Run `python main.py improve` every Sunday
- Database backup: `git add database/ && git commit -m "weekly backup"`

---

## File Structure Quick Reference

```
.env               ← API keys (fill this in now!)
main.py            ← Entry point for all commands
database/          ← All video ideas (10,000+ once generated)
state/             ← Progress, queue, analytics
output/[id]/       ← Generated video files (gitignored)
agents/            ← Script, voice, thumbnail, video, publish agents
video/remotion-project/ ← Video renderer
.claude/CLAUDE.md  ← Brain read at start of every session
```
