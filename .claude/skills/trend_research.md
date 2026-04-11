# Skill: Trend Research
# Use when running trend_agent.py or refreshing the ideas database

---

## Goal

Find topics that are:
1. **Currently trending** (high search interest in last 7 days)
2. **Alignable to our 3 content pillars** (Islamic/Arab history, shocking stats, geopolitical comparisons)
3. **Factually verifiable** (can be confirmed from official sources)
4. **Evergreen-enough** to stay relevant for months

---

## Sources to Check (in order of priority)

### 1. Google Trends (pytrends)
```python
from pytrends.request import TrendReq

pytrends = TrendReq(hl='en-US', tz=360)
# Get top rising queries in last 7 days
pytrends.build_payload(kw_list=['history', 'facts', 'economy'], timeframe='now 7-d')
related = pytrends.related_queries()
# Also check: trending searches by country (US, UK, global)
trending = pytrends.trending_searches(pn='united_states')
```

### 2. Reddit (manual or via Reddit API)
Subreddits to monitor weekly:
- r/todayilearned — top 50 posts this week
- r/interestingasfuck — top 50 posts this week
- r/worldnews — top trending topics
- r/history — top posts this week
- r/dataisbeautiful — popular data visualizations

Extract: topic, upvotes, comment sentiment

### 3. YouTube Trending
Scrape trending page for:
- Education category trending videos
- News and current events with historical angles
- "Did you know" style content

### 4. Google News via Serper API
```python
# Query: recent news in categories we can angle to our pillars
categories = ["history facts", "world records broken", "economic data", 
              "military spending", "ancient civilization discovery"]
```

---

## Trend Scoring System

Score each potential topic on:

| Factor | Weight | How to Measure |
|--------|--------|----------------|
| Search volume (7-day) | 35% | Google Trends relative interest 0-100 |
| Social engagement | 25% | Reddit upvotes + comments normalized |
| Alignability to pillars | 25% | Manual: does it fit one of 3 angles? |
| Freshness | 15% | Days since first appearing in trends |

**Trending score = sum of weighted scores**

Minimum score to add to database: 60/100

---

## How to Angle Trending Topics to Our Pillars

### Example: "Saudi Arabia oil"
- Pillar 1 (Islamic/Arab): "The Arab World Controls One Third of All Global Oil Reserves"
- Pillar 2 (Shocking stats): "Saudi Arabia Earns More Per Minute From Oil Than Most Countries Earn Per Day"
- Pillar 3 (Geopolitical): "Saudi Arabia vs Russia: Who Controls More of the World's Energy"

Always generate at least 2 angle variants for each trending topic.

---

## Freshness vs Evergreen Balance

The queue should be:
- **40% trending** (high trending score, time-sensitive)
- **60% evergreen** (low trending score but high evergreen score)

This ensures:
- Content stays relevant even if trends shift
- Never runs out of ideas even in slow news weeks
- Historical facts don't expire

---

## trending_topics.json Structure

```json
{
  "last_updated": "2026-04-11T09:00:00Z",
  "topics": [
    {
      "raw_topic": "Saudi Arabia economic diversification",
      "trending_score": 78,
      "source": "google_trends",
      "first_seen": "2026-04-08",
      "angled_ideas": [
        "Saudi Arabia Is Building a City Larger Than New York With Zero Cars",
        "Saudi Arabia Plans to Earn Zero Dollars From Oil by 2030"
      ],
      "added_to_database": false
    }
  ]
}
```

---

## Weekly Refresh Process

1. Run trend_agent.py every Monday 9am UTC
2. Collect top 50 trending topics from all sources
3. Score each topic
4. Generate 2-3 idea variants for top 30 topics
5. Add best 100 new ideas to ideas_short.json
6. Re-sort queue.json by updated priority scores
7. Log refresh in state/improvement_log.md
