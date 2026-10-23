# Stage 1 — Enumerate attractions

Work with any LLM (Claude, GPT, DeepSeek, GLM, Gemini, ...). Paste this prompt:

---
List all noteworthy tourist attractions in \<CITY\>. Return ONLY a JSON object, no
commentary, no markdown fences:

```json
{
  "attractions": [
    { "id": "lowercase-slug", "name": "Official Name", "area": "District", "note": "one line" }
  ]
}
```

Rules:
- exhaust the well-known sights first, then add genuinely interesting hidden gems
- 15-40 entries
- `id` is a stable lowercase slug (it becomes a file name) — never reuse it
- no duplicates, official names only
---

Save the output as `attractions.json`, then run:

```bash
guide check attractions
```

The tool verifies: JSON validity, unique ids, slug format, duplicate names.
It does NOT verify the list is complete — a bare list cannot prove its own
completeness. That needs one of the two criteria below.

## When is enumeration "done"?

A list alone can never prove it exhausted the city. guideforge makes the
termination decidable with two mechanical criteria — configure
`coverage:` in `spec.yaml` (a `city_qid` like `Q84` for London):

1. **External oracle (coverage).** The tool fetches the city's tourist
   attractions from Wikidata, ranked by notability, and requires every one of
   the top-N to appear in your list. Missing → FAIL, with the names.
   One source is never enough — Wikidata's "tourist attraction" class misses
   food streets, neighbourhoods and viewpoints. So the oracle is pluggable:
   drop a `reference.json` (JSON array of names, most notable first) for a
   single curated list, or a `references/` folder with one JSON per source
   (wikidata.json, guidebook.json, tripadvisor-top.json, ...) — the tool
   merges, dedupes and enforces the union. Any site, any guidebook, same gate.

2. **Saturation.** Run the same enumeration prompt again in a *fresh* chat
   (ideally a different model) and save it as `attractions.pass2.json`.
   `guide check coverage` merges and compares: any name from pass 2 that the
   guide lacks → FAIL "not saturated". Zero new names → `saturated`, and the
   enumeration is done. Keep running passes until one adds nothing.

```bash
guide check coverage
```
