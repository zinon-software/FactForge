# FACT VERIFICATION & 100% ACCURACY SYSTEM
# For: Claude Code
# Purpose: Guarantee every single fact in every video is verified, sourced, and true
# Apply to: ALL content before script is approved for production
# Save as: .claude/skills/fact_verification.md

---

## 🔴 MANDATORY INSTRUCTION

This system runs BEFORE any script is written — not after.
Research and verification happens FIRST. Script is written FROM verified facts.
Never write a script and then try to verify it.
If a fact cannot be verified from an official source → it is REMOVED. No exceptions.
One false fact destroys channel credibility permanently. Accuracy is the brand.

---

## 🧠 PART 1 — THE VERIFICATION PHILOSOPHY

### Why Accuracy is a Business Decision, Not Just Ethics

```
REASON 1 — YouTube penalizes misinformation
YouTube's policies explicitly remove channels that repeatedly spread
false information. One viral misinformation video can terminate the channel.

REASON 2 — Comments are your fact-checkers
Millions of viewers include experts, professors, and specialists.
A wrong fact in a history video will be caught within hours.
Comments saying "this is wrong" destroy CTR and trust permanently.

REASON 3 — Accuracy IS the competitive advantage
Most "facts" channels on YouTube are lazy — they copy each other.
A channel known for being genuinely accurate builds a loyal audience
that trusts every new video before watching it.
This trust converts to subscribers, shares, and long-term growth.

REASON 4 — Accuracy enables controversial topics
When the channel has a reputation for accuracy,
it can cover sensitive topics (organ prices, military power, wealth)
without being dismissed as clickbait.
Accuracy is the permission slip for provocative content.
```

### The Golden Rule

```
Every fact in every video must pass this test:

"Could I defend this fact in a public debate against a subject expert,
citing the exact source, publication date, and methodology?"

If the answer is NO → the fact does not go in the video.
```

---

## 🔍 PART 2 — SOURCE HIERARCHY SYSTEM

Not all sources are equal. Use this hierarchy strictly.

### Tier 1 — Primary Official Sources (always preferred)

```
ECONOMICS & WEALTH:
→ World Bank Open Data: data.worldbank.org
→ International Monetary Fund: imf.org/en/Data
→ Forbes Real-Time Billionaires: forbes.com/real-time-billionaires
→ Bloomberg Billionaires Index: bloomberg.com/billionaires
→ Federal Reserve Economic Data: fred.stlouisfed.org
→ OECD Statistics: stats.oecd.org

MILITARY & POWER:
→ Stockholm International Peace Research Institute: sipri.org
→ Global Firepower Index: globalfirepower.com
→ NATO Official Data: nato.int
→ US Department of Defense: defense.gov
→ IISS Military Balance: iiss.org

POPULATION & GEOGRAPHY:
→ UN Population Division: population.un.org
→ CIA World Factbook: cia.gov/the-world-factbook
→ Worldometer: worldometers.info (cites UN/WHO sources)

HISTORY & CIVILIZATIONS:
→ Encyclopedia Britannica: britannica.com
→ World History Encyclopedia: worldhistory.org
→ Smithsonian Institution: si.edu
→ Library of Congress: loc.gov
→ Oxford Reference: oxfordreference.com

SCIENCE & MEDICINE:
→ WHO: who.int
→ CDC: cdc.gov
→ PubMed (peer-reviewed): pubmed.ncbi.nlm.nih.gov
→ NASA: nasa.gov
→ Nature Journal: nature.com

ISLAMIC HISTORY (specialized):
→ Oxford Islamic Studies: oxfordislamicstudies.com
→ Muslim Heritage: muslimheritage.com
→ Journal of Islamic History (peer-reviewed)
→ Al-Azhar University publications
→ Encyclopedia of Islam (Brill)
```

### Tier 2 — Reputable Secondary Sources (acceptable with Tier 1 backup)

```
→ Reuters: reuters.com
→ Associated Press: apnews.com
→ BBC: bbc.com
→ The Economist: economist.com
→ National Geographic: nationalgeographic.com
→ Statista: statista.com (must cite their original source)
→ Our World in Data: ourworldindata.org (excellent sourcing)
```

### Tier 3 — Reference Only (NEVER cite as primary source)

```
→ Wikipedia: use ONLY to find primary sources, never as the source itself
→ Reddit: use ONLY for topic ideas, never as a fact source
→ YouTube videos: never use another video as a source
→ Social media posts: never acceptable as sources
→ Personal blogs: never acceptable
→ News aggregators: never acceptable
```

### Forbidden Sources

```
NEVER use these regardless of how compelling the claim:
→ Anonymous or unattributed websites
→ Sites with no "About" page or author credentials
→ Sites that regularly publish conspiracy theories
→ Any source that cannot be independently verified
→ Any source that has been flagged for misinformation
→ AI-generated content as a source (including other AI tools)
```

---

## 🔬 PART 3 — THE VERIFICATION PROTOCOL

Every fact goes through this exact process before entering a script.

### Step 3.1 — Fact Extraction

```python
def extract_facts_from_idea(video_idea):
    # Break the video idea into individual factual claims
    # Example idea: "Mansa Musa was the richest person in history"
    # Becomes these individual claims to verify:
    
    claims = [
        "Mansa Musa was a real historical figure",          # Basic existence
        "He ruled the Mali Empire",                         # Role/position
        "His reign was approximately 1312-1337",            # Date range
        "His wealth is estimated at $400 billion adjusted", # Wealth claim
        "This makes him the wealthiest person in history",  # Comparative claim
        "The Mali Empire controlled significant gold trade", # Supporting fact
        "His 1324 pilgrimage to Mecca is documented",       # Specific event
    ]
    
    return claims
    # Each claim verified separately
    # All must pass before script is written
```

### Step 3.2 — Multi-Source Verification

```python
def verify_claim(claim):
    verification = {
        "claim": claim,
        "status": "unverified",
        "sources": [],
        "confidence": 0,
        "caveats": [],
        "verdict": None
    }
    
    # Search Tier 1 sources first
    tier1_results = search_official_sources(claim)
    
    if tier1_results:
        # Must find claim confirmed in MINIMUM 2 independent Tier 1 sources
        if len(tier1_results) >= 2:
            verification["status"] = "verified"
            verification["confidence"] = 95
        elif len(tier1_results) == 1:
            # Try Tier 2 sources for second confirmation
            tier2_results = search_reputable_sources(claim)
            if tier2_results:
                verification["status"] = "verified"
                verification["confidence"] = 80
            else:
                verification["status"] = "single_source"
                verification["confidence"] = 60
                # Single source facts need special handling (see Part 4)
    else:
        verification["status"] = "unverifiable"
        verification["verdict"] = "REMOVE_FROM_SCRIPT"
    
    return verification
```

### Step 3.3 — Number Verification (Highest Risk)

Numbers are the most commonly wrong element in facts content.

```python
def verify_number(number_claim):
    
    # RULE 1: Always verify the base number AND the comparison
    # Wrong: "Mansa Musa had $400 billion" (what year's dollars?)
    # Right: "$400 billion in 2023 inflation-adjusted US dollars 
    #         according to [source] using [methodology]"
    
    # RULE 2: Always note the date of the statistic
    # Numbers change. A 2019 statistic may be wrong in 2025.
    # Always include the year of measurement.
    
    # RULE 3: Round numbers need range disclosure
    # "$400 billion" should be stated as "estimated between $300-500 billion"
    # Estimates presented as exact numbers are misleading
    
    # RULE 4: Adjusted vs nominal values
    # Historical wealth must be inflation-adjusted
    # State clearly: "in today's dollars" or "in [year] dollars"
    
    # RULE 5: Rankings change
    # "Richest person" changes daily — include the date
    # Use: "as of [date], [source] ranked..." not "is the richest"
    
    checks = {
        "base_number_verified": False,
        "date_included": False,
        "methodology_clear": False,
        "range_acknowledged": False,
        "source_url": None
    }
    
    return checks
```

### Step 3.4 — Historical Claim Verification

Historical facts require extra care due to contested narratives.

```python
def verify_historical_claim(claim):
    
    # CHECK 1: Is this claim consensus or contested?
    consensus_sources = check_academic_consensus(claim)
    
    if consensus_sources["contested"]:
        # Contested historical claims must:
        # a) Present the most widely accepted version
        # b) Acknowledge the debate exists
        # c) Cite the specific scholarly disagreement
        # Never present one side of a historical debate as absolute fact
        
        script_note = f"[CAVEAT REQUIRED: Academic debate exists — 
                        present as 'most historians believe' not 'it is a fact that']"
    
    # CHECK 2: Primary vs secondary historical sources
    # Best: contemporary accounts (written in the era)
    # Good: academic archaeological/historical analysis
    # Acceptable: established encyclopedia entries
    # Never: popular history books without citations
    
    # CHECK 3: Islamic history specific rules
    # Hadith and Islamic historical claims must be verified through:
    # - Classical Islamic historians (Al-Tabari, Ibn Khaldun, etc.)
    # - Modern peer-reviewed Islamic studies journals
    # - Never rely solely on popular Islamic content sites
    
    return verification_result
```

---

## ⚠️ PART 4 — HANDLING UNCERTAIN FACTS

When a fact cannot be fully verified, use these protocols.

### The 4 Options for Uncertain Facts

```
OPTION 1 — REMOVE IT
If a fact is central to the video's claim and cannot be verified:
Remove it. Build the video around verifiable facts only.
Never compromise accuracy to save a script.

OPTION 2 — QUALIFY IT
If a fact is partially verified, add honest qualifiers:
❌ "He owned $400 billion"
✅ "Historians estimate his wealth at around $400 billion in today's money,
    though exact figures are impossible to verify from this period"

OPTION 3 — REFRAME IT
Change the claim to what CAN be verified:
❌ "The richest person ever" (contested — hard to prove)
✅ "One of the wealthiest rulers in recorded history" (verifiable)

OPTION 4 — FLAG FOR EXPERT REVIEW
For complex scientific or highly technical claims:
Add [EXPERT_REVIEW_NEEDED] tag in script
Do not publish until reviewed
Better to delay than publish questionable content
```

### Confidence Level Tags in Scripts

```
Every factual claim in the script gets a confidence tag:

[VERIFIED_95]: Confirmed by 2+ Tier 1 official sources
[VERIFIED_80]: Confirmed by 1 Tier 1 + 1 Tier 2 source
[ESTIMATE]:    Best available estimate, acknowledged as such
[CONTESTED]:   Historical debate exists — presented with qualification
[APPROXIMATE]: Rounded figure, actual number within stated range

Scripts with more than 2 [ESTIMATE] or [CONTESTED] tags 
on core claims must be restructured around more certain facts.
```

---

## 🌐 PART 5 — REAL-TIME RESEARCH PROTOCOL

For every video, Claude Code must perform live web research.

### Research Execution Steps

```python
async def research_video_topic(video_idea):
    
    research_results = {
        "topic": video_idea["title"],
        "primary_facts": [],
        "verified_numbers": [],
        "source_urls": [],
        "confidence_map": {},
        "removed_claims": [],
        "caveats_required": []
    }
    
    # STEP 1: Search official databases directly
    official_data = await fetch_official_sources(video_idea["key_facts"])
    
    # STEP 2: Cross-reference Wikipedia for source discovery
    # (use Wikipedia to FIND sources, not AS a source)
    wiki_sources = await extract_wikipedia_citations(video_idea["title"])
    
    # STEP 3: Fetch and read actual source pages
    for source_url in wiki_sources + official_data:
        content = await web_fetch(source_url)
        extracted_facts = extract_verifiable_claims(content)
        research_results["primary_facts"].extend(extracted_facts)
    
    # STEP 4: Search for counter-evidence
    # Actively try to DISPROVE each major claim
    # If the claim survives the counter-search → high confidence
    for claim in research_results["primary_facts"]:
        counter = await search_counter_evidence(claim)
        if counter["found"]:
            research_results["caveats_required"].append({
                "claim": claim,
                "counter_evidence": counter["details"],
                "resolution": counter["consensus"]
            })
    
    # STEP 5: Generate research summary
    save_research_to_file(research_results, f"output/{video_idea['id']}/research.json")
    
    return research_results
```

### Mandatory Search Queries Per Topic Type

```python
SEARCH_QUERIES_BY_TYPE = {
    
    "wealth_ranking": [
        "{subject} net worth Forbes",
        "{subject} wealth estimate historian",
        "{subject} richest {time_period} source",
        "{subject} inflation adjusted wealth {year}",
        "critique of {subject} wealth estimate",  # counter-evidence search
    ],
    
    "military_power": [
        "{country} military budget SIPRI {year}",
        "{country} active military personnel official",
        "{country} vs {country} defense spending comparison",
        "source for {country} military ranking",
    ],
    
    "historical_fact": [
        "{event} primary source historical record",
        "{event} archaeological evidence",
        "{person} historical account contemporary",
        "historian debate {claim}",  # check for contested claims
        "{event} peer reviewed journal",
    ],
    
    "scientific_claim": [
        "{claim} peer reviewed study PubMed",
        "{claim} WHO official data",
        "{claim} scientific consensus",
        "{claim} debunked",  # counter-evidence search
    ],
    
    "price_economic": [
        "{item} price official data {year}",
        "{item} cost source",
        "{item} market value verified",
        "how much does {item} cost source",
    ]
}
```

---

## 📋 PART 6 — SCRIPT ACCURACY REVIEW

After script is written, run this final accuracy check.

```python
def final_accuracy_review(script, research_data):
    
    issues = []
    
    # CHECK 1: Every number in script has a source
    numbers_in_script = extract_all_numbers(script)
    for number in numbers_in_script:
        if not has_verified_source(number, research_data):
            issues.append(f"UNVERIFIED NUMBER: {number}")
    
    # CHECK 2: No superlatives without proof
    superlatives = extract_superlatives(script)
    # "biggest", "richest", "most powerful", "first ever", etc.
    for superlative_claim in superlatives:
        if not has_comparative_proof(superlative_claim, research_data):
            issues.append(f"UNVERIFIED SUPERLATIVE: {superlative_claim}")
            # Fix: change "the richest" to "one of the richest"
    
    # CHECK 3: Dates are accurate
    dates_in_script = extract_all_dates(script)
    for date_claim in dates_in_script:
        if not date_verified(date_claim, research_data):
            issues.append(f"UNVERIFIED DATE: {date_claim}")
    
    # CHECK 4: No misleading framing
    # Even true facts can mislead through selective presentation
    check_for_misleading_context(script, research_data)
    
    # CHECK 5: Sensitive claims have proper qualification
    sensitive_claims = identify_sensitive_claims(script)
    for claim in sensitive_claims:
        if not has_qualifier(claim):
            issues.append(f"NEEDS QUALIFIER: {claim}")
    
    if issues:
        # Return script for revision with specific issues listed
        return {"approved": False, "issues": issues}
    else:
        return {"approved": True, "accuracy_score": 100}
```

---

## 📁 PART 7 — SOURCE DOCUMENTATION SYSTEM

Every video gets a complete source file that travels with it forever.

```python
# Template for output/[video_id]/sources.json

SOURCES_TEMPLATE = {
    "video_id": "",
    "video_title": "",
    "research_date": "",
    "total_claims": 0,
    "verified_claims": 0,
    "accuracy_percentage": 0,
    
    "sources": [
        {
            "claim": "Exact claim as stated in video",
            "source_name": "World Bank",
            "source_url": "https://data.worldbank.org/...",
            "access_date": "2025-04-11",
            "publication_date": "2024",
            "tier": 1,
            "confidence": 95,
            "quote": "Exact relevant quote from source (under 15 words)",
            "notes": "Any important context or caveats"
        }
    ],
    
    "removed_claims": [
        {
            "original_claim": "Claim that was removed",
            "reason": "Could not verify from official source",
            "attempted_sources": ["source1", "source2"]
        }
    ],
    
    "caveats_in_video": [
        {
            "claim": "Contested or estimated claim",
            "caveat_used": "Exact qualifier added in script",
            "reason": "Why caveat was needed"
        }
    ]
}
```

---

## 🛡️ PART 8 — SENSITIVE TOPIC HANDLING

Special verification rules for the channel's most provocative content.

### Organ/Medical Pricing Content

```
REQUIRED SOURCES:
→ WHO official reports on organ trafficking
→ Peer-reviewed medical economics journals
→ Official transplant organization data (UNOS, Eurotransplant)
→ Academic papers on transplant economics

REQUIRED FRAMING IN SCRIPT:
→ Always frame as "illegal market estimates" not "prices"
→ Always mention legal alternatives (organ donation programs)
→ Always cite law enforcement or UN reports as context
→ Never present as "how to" — always as "this is the reality"

FORBIDDEN:
→ Any information that could be used to actually purchase organs
→ Contact information or locations
→ Content that glorifies or normalizes organ trafficking
```

### Military Power Comparisons

```
REQUIRED SOURCES:
→ SIPRI (Stockholm International Peace Research Institute) — gold standard
→ Official government defense budget documents
→ NATO/UN official reports
→ IISS Military Balance annual report

REQUIRED FRAMING:
→ Budget comparisons use official figures only
→ "Estimated" for classified capabilities
→ Never speculate about classified programs
→ Present all sides in country comparisons

FORBIDDEN:
→ Specific tactical vulnerability information
→ Claims that could incite hostility between nations
→ Unverified intelligence claims
```

### Wealth and Inequality Content

```
REQUIRED SOURCES:
→ Forbes for living billionaires (updated daily)
→ Bloomberg Billionaires Index (second verification)
→ World Bank for country-level wealth data
→ Historical wealth: academic economic history papers

REQUIRED FRAMING:
→ Note that billionaire wealth estimates are approximate
→ Note that historical wealth comparisons use specific methodologies
→ Never present wealth as inherently negative or positive
→ Present data, let viewers draw conclusions

FORBIDDEN:
→ Claiming someone is corrupt without court verdict proof
→ Speculating about undisclosed wealth
→ Personal financial information not in public record
```

### Islamic History Content

```
REQUIRED SOURCES:
→ Classical Islamic historians cited by name and work
→ Modern peer-reviewed Islamic studies academics
→ Archaeological evidence where available
→ Multiple scholarly perspectives (not single-school interpretation)

REQUIRED FRAMING:
→ Distinguish between documented historical fact and religious belief
→ Present scholarly consensus while noting debates
→ Never make theological claims — only historical ones
→ Respect for the subject — accuracy and dignity together

FORBIDDEN:
→ Sectarian framing (Sunni vs Shia framing of historical events)
→ Theological rulings or religious interpretations
→ Unverified hadith as historical fact
→ Modern political framing of classical historical events
```

---

## ✅ PART 9 — ACCURACY SCORE CHECKLIST

Minimum score to approve script for production: 18/20

```
RESEARCH QUALITY (8 points):
[ ] All major claims searched in Tier 1 sources
[ ] Minimum 2 independent sources for each core claim  
[ ] Counter-evidence search performed for controversial claims
[ ] Research saved to output/[id]/research.json
[ ] Sources saved to output/[id]/sources.json

NUMBER ACCURACY (4 points):
[ ] Every number has a named source
[ ] Dates included for all statistics
[ ] Historical values inflation-adjusted and labeled
[ ] Ranges used for estimates (not false precision)

FRAMING ACCURACY (4 points):
[ ] Superlatives qualified ("one of the" not "the")
[ ] Contested claims include honest caveats
[ ] Sensitive topics framed appropriately
[ ] No misleading omissions of important context

DOCUMENTATION (4 points):
[ ] All sources listed in video description
[ ] sources.json complete with URLs
[ ] Removed claims documented with reason
[ ] Confidence levels tagged in script file

ACCURACY SCORE: __ / 20
Minimum to produce: 18/20
```

---

## 📋 FINAL IMPLEMENTATION INSTRUCTION

The production pipeline order with all 3 quality gates:

```python
PRODUCTION_ORDER = [
    "1. select_idea()",
    "2. research_and_verify()",        # ← fact_verification.md runs here
    "3. check_accuracy_score()",       # must score 18/20 before continuing
    "4. write_script()",               # script written FROM verified facts only
    "5. check_content_score()",        # content_psychology.md — must score 80/100
    "6. generate_voice()",
    "7. generate_video()",
    "8. generate_thumbnail()",
    "9. generate_metadata()",
    "10. check_seo_score()",           # youtube_seo.md — must score 18/22
    "11. translate_metadata()",
    "12. schedule_and_publish()",
]

# All 3 quality gates must pass:
# Accuracy >= 18/20 → Content Psychology >= 80/100 → SEO >= 18/22
# This triple gate system is what separates
# a professional channel from amateur content
```

Accuracy is not a constraint — it is the product.
The channel's entire value is built on viewers trusting every word.
Protect that trust in every single video, without exception.
