# Skill: Self-Improvement
# Run weekly via improvement_agent.py — analyzes performance and updates the system

---

## When to Run

- Every Sunday at 8pm UTC (automated)
- After any video reaches 10,000 views (milestone trigger)
- Any time user commands "improve system"

---

## Metrics That Matter (in priority order)

| Metric | Why It Matters | Target |
|--------|---------------|--------|
| Click-Through Rate (CTR) | Title + thumbnail quality | >5% |
| Average View Duration % | Script quality, hook strength | >50% for shorts, >40% for long |
| Shares | Topic resonance | Track trend over time |
| Subscriber conversion | CTA effectiveness | >0.5% of viewers |
| Impressions | Algorithmic reach | Track growth trend |

**CTR and retention are the two most important metrics.** Everything else follows from these.

---

## Weekly Analytics Review Checklist

```
□ Pull analytics for all videos published in last 7 days
□ Pull analytics for all videos ever published (cumulative)
□ Identify top 5 performing videos (by CTR × retention)
□ Identify bottom 5 performing videos
□ Find common patterns in top performers
□ Find common failure patterns in bottom performers
□ Check retention graphs for drop-off points
□ Compare title formulas between high/low CTR videos
□ Compare thumbnail styles between high/low CTR videos
□ Check which content categories perform best
```

---

## Pattern Analysis Methodology

### Title Formula Analysis
1. Group all videos by title formula type (number, power word, comparison, etc.)
2. Calculate average CTR per formula type
3. Increase weight of high-CTR formulas in generate_title.md scoring
4. Retire formulas with consistently <3% CTR

### Retention Drop-Off Analysis
1. Find videos where >30% of viewers leave in first 10 seconds → hook is weak
2. Find videos where viewers leave at a specific timestamp → that section is weak
3. Update write_script.md with structural fixes

### Topic Category Analysis
1. Which of the 3 content pillars gets highest engagement?
2. Which sub-categories (Islamic history, wealth stats, etc.) perform best?
3. Adjust idea priority scores based on category performance

### Thumbnail Analysis
1. Which color themes get highest CTR?
2. Number-focused vs word-focused thumbnails?
3. Update thumbnail.md recommendations based on data

---

## How to Update the System

After analysis, make these updates:

### Update idea priority scores
```python
# In database/ideas_short.json, adjust priority_score for similar ideas
# If Islamic history videos avg CTR > 7%: bump all islamic_history ideas +10
# If comparison videos avg CTR < 3%: reduce all comparison ideas -5
```

### Update title formula weights
```python
# In generate_title.md scoring table, adjust points for each criterion
# Based on correlation between criteria and actual CTR performance
```

### Update script structure
```python
# If retention data shows viewers leave at 30s mark:
# → Move peak fact from 35-50s to 20-30s
# If viewers leave after the hook:
# → Hook needs to be stronger — update write_script.md hook guidelines
```

### Refresh idea database
```python
# Reprioritize queue based on category performance data
# Add more ideas in top-performing categories
# Reduce ideas in bottom-performing categories
```

---

## improvement_log.md Entry Template

```markdown
## [DATE] Weekly Improvement Report

### Performance Summary
- Videos published this week: [N]
- Average CTR this week: [X]%
- Average retention this week: [X]%
- Best performing video: [title] ([CTR]% CTR, [retention]% retention)
- Worst performing video: [title] ([CTR]% CTR, [retention]% retention)

### What Worked
- [Pattern observed in top performers]
- [Why it worked based on data]

### What Didn't Work
- [Pattern observed in bottom performers]
- [Why it failed based on data]

### System Changes Made
- [File changed]: [What was changed and why]

### Next Week Focus
- [Priority topic category based on performance data]
- [Title formula to test based on CTR analysis]
- [Script structure change to test based on retention data]
```
