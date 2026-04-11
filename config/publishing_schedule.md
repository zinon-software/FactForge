# Publishing Schedule
# When to publish for maximum reach

---

## Optimal Upload Windows (YouTube Analytics Research)

| Day | Time (EST) | Time (UTC) | Expected Reach |
|-----|-----------|-----------|----------------|
| Tuesday | 2:00pm – 4:00pm | 19:00 – 21:00 | High |
| Wednesday | 2:00pm – 4:00pm | 19:00 – 21:00 | High |
| Thursday | 2:00pm – 4:00pm | 19:00 – 21:00 | Very High |
| Saturday | 9:00am – 11:00am | 14:00 – 16:00 | High |

## Avoid Publishing

- Monday morning (low engagement — people are starting work week)
- Friday evening (people are offline socially)
- Any major breaking news day (algorithm attention split)
- Publishing two videos within 24 hours (splits own audience)

## Minimum Gap Between Videos

**48 hours** between any two published videos. This allows YouTube to fully promote each video before the next one arrives.

## Scheduling Logic (implemented in publish_agent.py)

```
1. Get current datetime UTC
2. Find next available slot from optimal windows
3. If next slot is less than 48 hours from last publish → skip to slot after
4. Set video status to "private" on YouTube
5. Set scheduled publish time to found slot
6. YouTube automatically changes to "public" at scheduled time
```

## Initial Ramp-Up Strategy

First 4 weeks: publish one video every 3 days to build consistent algorithmic signals.
After 4 weeks: move to every 48 hours if content pipeline supports it.
After 3 months: analyze data and adjust frequency based on what the algorithm rewards.

## Shorts vs Long Video Schedule

- Shorts: can be published more frequently — target every 48 hours
- Long videos: once per week, on Thursday 2-4pm EST for best performance
- Mix: for every 3 shorts, schedule 1 long video
