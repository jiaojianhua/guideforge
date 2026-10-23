# Stage 3 — Write descriptions

Tune `spec.yaml` first: required fields, summary length range, banned patterns.
Then paste this prompt with `attractions.json` and `tiers.json` attached:

---
Write a description for each attraction below. Return ONLY JSON:

```json
{
  "<id>": {
    "summary": "2-3 sentences, concrete and specific, no fluff",
    "highlights": ["specific detail", "specific detail"],
    "tips": "one practical visitor tip (timing, tickets, transport)"
  }
}
```

Rules:
- one entry per attraction id, exactly the same ids
- summary: be specific (names, numbers, what makes it different), never generic
- no placeholders like TODO, TBD, "to be added"
---

Save as `descriptions.json`, then run:

```bash
guide check descriptions
```

The tool verifies: entry per attraction, required fields present, summary
length in range, banned/placeholder patterns absent (case-insensitive, across
all nested strings). It does NOT verify facts — check opening hours and prices
yourself before publishing.
