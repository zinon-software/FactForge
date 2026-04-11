# YouTube SEO & Algorithm Mastery System
# For: Claude Code
# Purpose: Maximize discoverability, ranking, and algorithmic push for every video
# Apply to: ALL content produced by the automation system
# Save as: .claude/skills/youtube_seo.md

---

## 🔴 MANDATORY INSTRUCTION

Every video produced MUST pass through this SEO system before publishing.
No video is uploaded without completing ALL sections of this document.
This is not optional optimization — this is the difference between
a video that gets found and a video that disappears forever.

---

## 🧠 PART 1 — HOW THE YOUTUBE ALGORITHM ACTUALLY WORKS

Understanding the algorithm is required before optimizing for it.
The algorithm has ONE goal: keep people on YouTube as long as possible.
It rewards content that achieves this. It buries content that doesn't.

### The 5 Signals YouTube Measures (in order of importance)

```
SIGNAL 1 — Click-Through Rate (CTR)
What it is: % of people who see your thumbnail and click it
Target: 6-10% for established channels, 4%+ for new channels
What kills it: misleading thumbnails, weak titles, wrong audience targeting
What helps it: curiosity gap titles, high contrast thumbnails, emotional triggers

SIGNAL 2 — Watch Time / Retention
What it is: how much of the video people actually watch
Target: 50%+ for shorts, 40%+ for long videos
What kills it: slow intros, information that doesn't deliver on the title's promise
What helps it: hooks, open loops, escalating reveals, pacing

SIGNAL 3 — Engagement Velocity
What it is: how fast likes, comments, shares happen in the first hour
Why it matters: YouTube tests every video with a small audience first
If engagement is high → algorithm pushes to larger audience
If engagement is low → video is buried within 24 hours
What helps it: asking specific questions in CTA, controversial-but-safe topics

SIGNAL 4 — Session Time
What it is: how much time viewers spend on YouTube AFTER watching your video
What helps it: end screens linking to other videos, playlists, series content

SIGNAL 5 — Re-watches
What it is: how many times the same viewer watches the same video
What helps it: information density (so much value they rewatch to catch everything)
              shorts that are perfect loops (end connects back to beginning)
```

### The Algorithm's Testing Funnel

```
Every new video goes through this funnel:

STAGE 1 (first 30 minutes):
YouTube shows video to ~200-500 of your existing subscribers
Measures: CTR + first 30 seconds retention
If CTR > 4% AND retention > 60% → advance to Stage 2
If either fails → video is suppressed

STAGE 2 (hours 1-6):
YouTube shows to broader audience similar to your subscribers
Measures: full retention + engagement
If performing well → advance to Stage 3
If not → slow death

STAGE 3 (days 1-7):
YouTube shows to cold audience (people who never heard of you)
This is where viral growth happens
This is where the channel grows

IMPLICATION FOR PRODUCTION:
The first 30 seconds of every video must be PERFECT.
The thumbnail and title must be tested before publishing.
Publishing time matters (maximize Stage 1 audience size).
```

---

## 🔍 PART 2 — KEYWORD RESEARCH SYSTEM

### Step 2.1 — Primary Keyword Selection

For every video idea, find the primary keyword using this process:

```python
def find_primary_keyword(video_idea):
    
    # Step 1: Generate 10 possible search phrases a viewer would type
    candidates = generate_keyword_candidates(video_idea)
    # Example for "richest people in history":
    # ["richest person ever", "wealthiest person in history", 
    #  "richest man who ever lived", "most wealthy person history",
    #  "richest human being ever", ...]
    
    # Step 2: Score each candidate
    for keyword in candidates:
        score = {
            "search_volume": get_search_volume(keyword),      # higher = better
            "competition": get_competition_level(keyword),    # lower = better  
            "cpc": get_cpc(keyword),                          # higher = more valuable
            "trend": get_trend_direction(keyword),            # rising = better
        }
    
    # Step 3: Calculate opportunity score
    # opportunity = (search_volume × cpc) / competition
    
    # Step 4: Pick keyword with highest opportunity score
    # that still matches the video content accurately
    
    # SOURCES FOR KEYWORD DATA (free):
    # - Google Trends (pytrends library)
    # - YouTube autocomplete (scrape suggestions)
    # - Answer The Public patterns
    # - Reddit post titles on topic (what questions people actually ask)
```

### Step 2.2 — Keyword Intent Classification

Every keyword must match the right intent:

```
INFORMATIONAL intent → "how rich was [person]" → use in educational videos
COMPARISON intent   → "[A] vs [B]" → use in comparison videos  
RANKING intent      → "top 10 / richest / most powerful" → use in list videos
SHOCKING intent     → "you won't believe / secret / hidden" → use in reveal videos
CURRENT intent      → "2024 / 2025 / today / now" → use in trend videos

RULE: The keyword intent must MATCH the video format.
Mismatch = high bounce rate = algorithm punishes the video.
```

### Step 2.3 — Keyword Placement Rules

```
PRIMARY KEYWORD must appear in:
✓ Video title (within first 40 characters if possible)
✓ First line of description
✓ File name of video: "richest-man-history-facts.mp4"
✓ File name of thumbnail: "richest-man-history-thumbnail.jpg"
✓ First 30 seconds of spoken script (YouTube indexes audio)
✓ At least 2 of the first 5 tags

SECONDARY KEYWORDS (3-5 related terms) must appear in:
✓ Description body (naturally, not stuffed)
✓ Tags list
✓ Chapter titles (for long videos)
```

---

## 📝 PART 3 — TITLE ENGINEERING SYSTEM

### The Title Formula Matrix

Every title must be engineered using this matrix:

```
COMPONENT 1 — Primary Keyword (for SEO)
COMPONENT 2 — Emotional Trigger (for CTR)  
COMPONENT 3 — Specificity Element (for credibility)
COMPONENT 4 — Curiosity Gap (for retention)

Strong title = 3 or 4 of these components combined under 60 characters.
```

### Title Templates by Content Type

**For Top 10 / Ranking videos:**
```
Template: "The [REAL/ACTUAL/HONEST] Top [N] [TOPIC] — [Surprising Qualifier]"
Examples:
✓ "The Real Top 10 Richest People Ever — History Got It Wrong"
✓ "Actual Top 5 Military Powers — The Rankings Will Shock You"
✓ "Honest Top 10 Most Dangerous Countries — Not What You Think"

Why it works: "Real/Actual/Honest" implies mainstream rankings are wrong = controversy
```

**For Comparison videos:**
```
Template: "[A] vs [B]: [Specific Metric] — [Counterintuitive Result]"
Examples:
✓ "USA vs China Military: Real Numbers Show a Clear Winner"
✓ "Ancient Rome vs Modern USA: Wealth Comparison Nobody Makes"
✓ "Islam vs West: Scientific Contributions — 500 Years of Data"

Why it works: specific metric = credibility, counterintuitive = curiosity
```

**For Shocking Fact videos:**
```
Template: "[Specific Number/Thing] That [Completely Changes Understanding of Topic]"
Examples:
✓ "One Number That Proves The Economy Is Rigged"
✓ "The $400 Billion Man History Books Refuse to Mention"
✓ "This Tiny Country Outspends 20 Nations on Military"

Why it works: specificity forces brain to verify by watching
```

**For Hidden Truth videos:**
```
Template: "Why [Common Belief] Is [Wrong/A Lie/Hiding Something]"
Examples:
✓ "Why The Richest Countries List Is Hiding Something Huge"
✓ "Why History Books Got The Islamic Golden Age Completely Wrong"
✓ "Why The Real Power in The World Isn't Where You Think"

Why it works: challenges established belief = cognitive dissonance = must watch
```

### Title A/B Testing System

```python
def generate_title_variants(video_idea, keyword, research):
    # Generate 5 title variants using different templates above
    variants = []
    
    for template in TITLE_TEMPLATES:
        title = apply_template(template, video_idea, keyword)
        
        score = 0
        score += 20 if contains_number(title) else 0
        score += 15 if contains_power_word(title) else 0
        score += 25 if creates_curiosity_gap(title) else 0
        score += 10 if under_60_chars(title) else 0
        score += 20 if triggers_debate(title) else 0
        score += 10 if contains_primary_keyword(title) else 0
        
        variants.append({"title": title, "score": score})
    
    # Sort by score, return top 3
    # Save all 5 to metadata.json for future A/B testing
    # Use highest scoring as primary title
    # Use second highest as YouTube experiment variant (if channel eligible)
    
    return sorted(variants, key=lambda x: x["score"], reverse=True)

POWER_WORDS = [
    "secret", "hidden", "real", "actual", "honest", "banned",
    "forbidden", "exposed", "revealed", "shocking", "unbelievable",
    "impossible", "proof", "truth", "lie", "wrong", "never told"
]
# Use maximum 1 power word per title — more = spam filter trigger
```

---

## 📄 PART 4 — DESCRIPTION ENGINEERING SYSTEM

### Description Architecture

```
LINE 1 (first 150 chars — shown before "show more"):
→ Must contain primary keyword
→ Must hook the reader to click "show more"
→ Must be a complete sentence that stands alone
→ This line appears in Google search results

LINES 2-4 (the expand section):
→ 2-3 sentences expanding on the hook
→ Contains secondary keywords naturally
→ Sets up what the video covers

SECTION: What You'll Learn / In This Video:
→ 4-6 bullet points
→ Each bullet is a mini-curiosity gap
→ Bullets contain secondary keywords
→ Do NOT reveal the most shocking fact here (saves it for the video)

SECTION: Sources
→ List every source with full URL
→ This builds trust AND signals authority to YouTube
→ Wikipedia is acceptable as reference, but always link the primary source too

SECTION: Timestamps (long videos only)
→ Chapter markers at every 90 seconds minimum  
→ Chapter titles must contain keywords
→ This improves SEO AND gives YouTube chapter preview cards

SECTION: Social / Subscribe prompt
→ One line maximum
→ Specific reason to subscribe (not generic "hit subscribe")

SECTION: Hashtags (bottom of description)
→ 3-5 hashtags maximum (more hurts rather than helps)
→ Format: #Facts #History #[TopicSpecific]
→ Never use irrelevant trending hashtags (YouTube penalizes this)
```

### Description Template

```python
DESCRIPTION_TEMPLATE = """
{hook_sentence_with_primary_keyword}

{2_3_expansion_sentences_with_secondary_keywords}

In this video:
• {curiosity_bullet_1}
• {curiosity_bullet_2}
• {curiosity_bullet_3}
• {curiosity_bullet_4}

Sources:
{source_1_name}: {source_1_url}
{source_2_name}: {source_2_url}
{source_3_name}: {source_3_url}

{timestamps_if_long_video}

New facts every 48 hours — subscribe to stay ahead of what most people don't know.

#{tag1} #{tag2} #{tag3}
"""
```

---

## 🏷️ PART 5 — TAG STRATEGY SYSTEM

### Tag Hierarchy (30 tags total per video)

```
TIER 1 — Exact Match Tags (5 tags):
→ Primary keyword exactly as typed
→ Title exact match (without power words)
→ Primary keyword + year (e.g., "richest people 2025")
→ Primary keyword + "facts"
→ Primary keyword + "list"

TIER 2 — Phrase Match Tags (10 tags):
→ 2-3 word variations of primary keyword
→ Related questions people search
→ Subtopics covered in the video
→ The "also searched for" terms on Google

TIER 3 — Broad Category Tags (10 tags):
→ General category: "history facts", "world facts", "shocking facts"
→ Format category: "top 10", "comparison", "ranked"
→ Channel niche: "facts you didn't know", "mind blowing facts"

TIER 4 — Long-tail Tags (5 tags):
→ Specific phrases only highly interested viewers search
→ These attract small but highly engaged audience
→ Example: "wealthiest person in islamic history" instead of "rich person"

RULES:
→ Never repeat the same word more than 3 times across all tags
→ Never use tags unrelated to the video (instant credibility damage)
→ Never use other channels' names as tags (spam trigger)
→ Mix singular and plural: "richest person" AND "richest people"
```

---

## 🖼️ PART 6 — THUMBNAIL SEO SYSTEM

Thumbnails are not just design — they are SEO signals.

### Thumbnail Technical Requirements

```
SHORTS thumbnail:
- Size: 1080 × 1920 pixels
- Format: JPG (smaller file = faster load = slight SEO boost)
- File size: under 2MB
- File name: [primary-keyword-hyphenated]-short.jpg

LONG VIDEO thumbnail:  
- Size: 1280 × 720 pixels
- Format: JPG
- File size: under 2MB
- File name: [primary-keyword-hyphenated].jpg

IMPORTANT: YouTube reads the file name as a metadata signal.
Name it with the primary keyword, not "thumbnail_001.jpg"
```

### Thumbnail CTR Optimization Rules

```
RULE 1 — THE 3-SECOND BLUR TEST
Shrink thumbnail to 100×56 pixels (YouTube sidebar size)
If the main message is still clear → good
If it's blurry and unclear → redesign

RULE 2 — THE EMOTION CONTRAST RULE
Background: dark (black, deep blue, deep red)
Text/numbers: bright white or neon yellow
Result: maximum contrast = eye catches it in feed

RULE 3 — THE SINGLE FOCUS RULE
One dominant element only:
Option A: One massive number (e.g., "$400,000,000,000")
Option B: One word in massive font (e.g., "BANNED")
Option C: One face with extreme expression (shock/disbelief)
Never: multiple competing elements

RULE 4 — THE CURIOSITY GAP VISUAL
The thumbnail should raise a question, not answer it
✓ Show the shocking number WITHOUT context
✓ Show the "after" WITHOUT showing the "before"  
✓ Show an unexpected pairing (poor man + crown, small country + huge army)

RULE 5 — BRAND CONSISTENCY
Same font family across all thumbnails
Same color palette (variations within it)
Small channel logo watermark bottom-right (builds recognition over time)
```

---

## ⏰ PART 7 — PUBLISHING SCHEDULE OPTIMIZATION

### Best Publishing Times (based on YouTube Analytics research)

```python
OPTIMAL_PUBLISH_TIMES = {
    # Times in viewer's local timezone (YouTube serves by timezone)
    # For global English audience, use EST as baseline
    
    "shorts": {
        "best_days": ["Tuesday", "Wednesday", "Thursday", "Saturday"],
        "best_hours_EST": ["7:00", "12:00", "17:00", "20:00"],
        "worst_time": "Monday before 10am, Friday after 8pm",
        "reasoning": "Shorts feed is consumed during commute and evening scroll"
    },
    
    "long_videos": {
        "best_days": ["Wednesday", "Thursday", "Saturday", "Sunday"],
        "best_hours_EST": ["14:00", "15:00", "16:00"],
        "worst_time": "Monday, late night any day",
        "reasoning": "Long videos need dedicated viewing time — afternoon/weekend"
    }
}

def calculate_next_publish_slot(content_type, last_publish_time):
    # Minimum 48 hours between videos
    # Find next optimal slot after minimum gap
    # Never publish two videos within 24 hours (algorithm splits attention)
    # Alternate: short → long → short → long (never same type twice in a row)
    
    return next_optimal_slot
```

### Upload vs Schedule Strategy

```
NEVER upload as "public" immediately.
ALWAYS upload as "private" first, then schedule.

Why:
1. Scheduled videos get indexed by YouTube's algorithm before going live
2. Allows thumbnail and title optimization window
3. YouTube notifies subscribers at the scheduled time (better spike)
4. Prevents accidental publishing of unfinished videos

Schedule minimum 4 hours AFTER upload to allow full processing.
```

---

## 🌍 PART 8 — MULTI-LANGUAGE SEO SYSTEM

### YouTube's Auto-Dubbing + Metadata Strategy

```python
def prepare_multilanguage_metadata(title, description, tags, script):
    
    languages = {
        "es": "Spanish",      # 500M speakers, high RPM Latin America
        "fr": "French",       # 300M speakers, high RPM Europe/Africa  
        "de": "German",       # 100M speakers, HIGHEST RPM in Europe
        "hi": "Hindi",        # 600M speakers, growing ad market
        "pt": "Portuguese",   # 250M speakers (Brazil = huge YouTube market)
        "id": "Indonesian",   # 270M speakers, fastest growing YouTube market
        "ja": "Japanese",     # 125M speakers, very high RPM
        "ko": "Korean",       # 77M speakers, very high RPM
        "tr": "Turkish",      # 85M speakers, growing market
        "ar": "Arabic",       # 400M speakers, our core audience
    }
    
    for lang_code, lang_name in languages.items():
        translated = {
            "title": translate_and_optimize_title(title, lang_code),
            "description": translate_description(description, lang_code),
            "tags": translate_and_localize_tags(tags, lang_code),
        }
        # Note: translate title with cultural adaptation, not just word-for-word
        # A title that works in English may need restructuring for Arabic/Japanese
        
    # Upload via YouTube API localization endpoint
    # YouTube will serve each viewer the metadata in their language
    # This multiplies discoverability by appearing in searches in all languages
    
    return multilanguage_metadata
```

### RPM by Language Market (optimize for highest value)

```
Priority tier for content angle selection:
TIER 1 (highest RPM): German ($8-15), Japanese ($7-12), Norwegian ($9-14)
TIER 2 (high RPM): English US/UK ($5-10), French ($4-8), Korean ($5-9)  
TIER 3 (volume): Spanish ($2-4), Portuguese Brazil ($2-4), Hindi ($1-3)
TIER 4 (growth): Indonesian ($1-2), Turkish ($1-3), Arabic ($0.5-1.5)

IMPLICATION:
Videos about topics that interest German/Japanese/Korean audiences
earn MORE per view than same video with only English audience.
Translate titles to appeal to specific high-RPM markets.
```

---

## 📊 PART 9 — SHORTS-SPECIFIC SEO RULES

Shorts have different algorithm rules than long videos.

```
SHORTS ALGORITHM DIFFERENCES:

1. HASHTAG #Shorts IS REQUIRED in description
   Always add #Shorts as first or last hashtag
   Without it, YouTube may not classify it as a Short

2. LOOP OPTIMIZATION
   Shorts that loop perfectly get dramatically more views
   End frame should visually connect to first frame
   Script last sentence should tease first sentence
   
3. FIRST FRAME = THUMBNAIL
   Unlike long videos, the first frame of a Short IS the thumbnail in feed
   Design the video so frame 0 is visually striking
   Add text overlay on first frame (rendered in Remotion)
   
4. AUDIO IS INDEXED
   YouTube indexes the spoken words in Shorts
   Say the primary keyword in the first 10 seconds
   This is direct SEO impact
   
5. SHARES > LIKES FOR SHORTS
   The algorithm values shares more than likes for Shorts
   End with share-bait: "Send this to someone who thinks they know everything about [topic]"
   
6. REPLY RATE MATTERS
   Videos that generate comments get pushed more
   Ask ONE specific question at end: "Which one surprised you most?"
   Specific questions get more replies than "let me know in comments"
```

---

## 🔄 PART 10 — SEO SELF-IMPROVEMENT SYSTEM

After each video reaches 500+ views, run this SEO audit:

```python
def weekly_seo_audit():
    
    # CTR AUDIT
    # If CTR < 4%: 
    #   → A/B test new thumbnail (use YouTube Studio experiments if available)
    #   → Try title variant #2 from the generated variants
    #   → Log which title formula failed for this topic type
    
    # SEARCH TRAFFIC AUDIT
    # Check YouTube Studio → Traffic Sources → YouTube Search
    # What keywords are people actually using to find this video?
    # If different from target keyword → update future videos for that keyword
    # Add those discovered keywords to the tag system
    
    # IMPRESSION AUDIT
    # If impressions are low (YouTube not showing the video):
    #   → The topic may be too niche for algorithm push
    #   → The thumbnail may be failing the CTR threshold test
    #   → Publishing time was wrong
    #   → Log finding and adjust for future videos
    
    # SUGGESTED TRAFFIC AUDIT
    # Which videos is YouTube suggesting this alongside?
    # If alongside wrong content → audience mismatch → adjust tags
    
    # UPDATE SKILLS
    # Add findings to youtube_seo.md
    # Adjust tag strategy based on what's actually working
    # Update keyword database with discovered high-performing terms
    
    # LOG EVERYTHING
    append_to_improvement_log({
        "date": today,
        "seo_findings": findings,
        "changes_made": changes,
        "expected_impact": impact_estimate
    })
```

---

## ✅ PART 11 — PRE-PUBLISH SEO CHECKLIST

Every video must pass this checklist before publishing.
Score 1 point per item. Minimum score: 18/22 to publish.

```
TITLE CHECKS:
[ ] Primary keyword in title within first 40 characters
[ ] Title under 60 characters
[ ] Contains at least 1 power word
[ ] Creates curiosity gap
[ ] Title score >= 70 from title scoring system

DESCRIPTION CHECKS:
[ ] Primary keyword in first 150 characters
[ ] Hook sentence in first line
[ ] Contains 4-6 content bullets
[ ] All sources listed with URLs
[ ] Timestamps added (long videos)
[ ] #Shorts hashtag present (short videos)
[ ] Subscribe CTA present
[ ] 3-5 hashtags at bottom

THUMBNAIL CHECKS:
[ ] Correct dimensions for content type
[ ] File named with primary keyword
[ ] Passes 3-second blur test (readable at 100px)
[ ] Single dominant element
[ ] High contrast (dark background, bright text)

TAG CHECKS:
[ ] 25-30 tags total
[ ] Primary keyword as exact-match tag
[ ] Mix of specific and broad tags
[ ] No irrelevant tags
[ ] No repeated tags

TECHNICAL CHECKS:
[ ] Video file named with primary keyword
[ ] Scheduled (not published immediately)
[ ] Scheduled at optimal time slot
[ ] Multi-language metadata uploaded
[ ] Category set correctly (27=Education or 24=Entertainment)

SCORE: __ / 22
Minimum to publish: 18/22
```

---

## 📋 FINAL IMPLEMENTATION INSTRUCTION

Save this entire document as:
`.claude/skills/youtube_seo.md`

Then update `.claude/CLAUDE.md` to include:
```
BEFORE publishing any video, run through:
1. content_psychology.md → script quality check (score >= 80)
2. youtube_seo.md → SEO checklist (score >= 18/22)

Both must pass. No exceptions.
A perfect video that nobody finds is worthless.
A found video with poor content loses viewers forever.
Both systems together = discoverability + retention = growth.
```

This skill is the engine that gets your videos found.
Content psychology keeps them watching.
SEO gets them there in the first place.
Neither works without the other.
