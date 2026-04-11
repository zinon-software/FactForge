# Skill: Fact Check
# Use before writing ANY script — no exceptions

---

## The Non-Negotiable Rule

**Never write a script for a statistic you cannot verify from at least 2 independent official sources.**

If a fact cannot be verified: mark it [UNVERIFIED], do not include it in the script, and log it to output/[id]/research.json with reason.

---

## Trusted Source Hierarchy (in order of authority)

### Tier 1 — Official Data (highest trust)
- World Bank: data.worldbank.org
- IMF: imf.org/en/Data
- United Nations: un.org/en/databases
- CIA World Factbook: cia.gov/the-world-factbook
- Official national government statistics bureaus
- SIPRI (military spending): sipri.org
- WHO (health data): who.int

### Tier 2 — Established Media & Research
- Forbes (wealth rankings)
- Bloomberg (financial data)
- Reuters, AP (news facts)
- Statista (compiled statistics — verify original source)
- Britannica (historical facts)
- World History Encyclopedia: worldhistory.org

### Tier 3 — Reference (never cite alone, always verify upstream)
- Wikipedia: find the citation, then verify the CITATION, not Wikipedia
- Google AI overviews: never trust without finding original source

### Tier 4 — Not Acceptable as Source
- Social media posts
- Unverified blogs
- Opinion pieces without cited data
- Reddit comments
- YouTube videos (even documentary ones)

---

## Verification Process

For every key statistic in a script:

```
1. State the claim: "[X] is/was [Y]"
2. Find Tier 1 or Tier 2 source that confirms it
3. Find a second independent source that confirms it
4. Record both URLs in research.json
5. Note the date the data is from (data ages — use most recent)
6. If sources conflict: use the more conservative/recent figure
7. Add context: "as of [YEAR]" or "adjusted for inflation to [YEAR]"
```

---

## Handling Estimates and Approximations

Some historical figures (like Mansa Musa's wealth) are estimates. Rules:

- Always say "estimated" or "historians estimate"
- Cite the methodology: "adjusted for inflation to 2023 dollars"
- Never present estimates as exact figures without qualification
- Give a range when there is genuine scholarly disagreement
- Example: "historians estimate his wealth at between 300 and 400 billion dollars in today's money"

---

## Red Flags — Extra Scrutiny Required

Claims that need extra verification:

- Superlatives ("the richest ever", "the largest in history")
- Comparative wealth (requires inflation adjustment methodology)
- Military rankings (political sensitivity, varies by methodology)
- Historical population figures (widely debated)
- GDP of ancient civilizations (always an estimate)
- Any "top 10" ranking (specify the ranking body and year)

---

## research.json Structure

Save this for every video before scripting:

```json
{
  "idea_id": "S00001",
  "research_date": "2026-04-11",
  "verified_facts": [
    {
      "claim": "Mansa Musa's estimated wealth was $400 billion in 2023 dollars",
      "sources": [
        {
          "url": "https://www.worldhistory.org/Mansa_Musa_I/",
          "accessed": "2026-04-11",
          "tier": 2
        },
        {
          "url": "https://www.britannica.com/biography/Mansa-Musa-I",
          "accessed": "2026-04-11",
          "tier": 2
        }
      ],
      "confidence": "high",
      "qualifier": "estimate, adjusted for inflation"
    }
  ],
  "unverified_claims": [
    {
      "claim": "He gave away so much gold the price of gold dropped for a decade",
      "reason": "Widely reported but original source unclear",
      "decision": "included with qualifier 'historians report'"
    }
  ],
  "sources_searched": 8,
  "research_duration_seconds": 45
}
```
