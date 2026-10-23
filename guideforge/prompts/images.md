# Stage 5 — Images (fetch → machine-check → human pick)

Two ways to get candidate images.

## Option A — let the tool search (no LLM)

```bash
guide images --source wikimedia
```

Searches Wikimedia Commons per attraction name, downloads, and mechanically
validates every image: minimum width, aspect-ratio range, readable format,
exact + perceptual deduplication. Only survivors become candidates.

Two refinements:
- add an optional `"query"` field to an attraction in `attractions.json` when
  the name is ambiguous ("St Paul's Cathedral" exists in several cities —
  `"St Paul's Cathedral London dome"` finds the right one)
- failed the human review? re-fetch just that one:
  `guide images --source wikimedia --only st-pauls`

## Option B — LLM proposes, tool disposes

Paste into any LLM with `attractions.json` attached:

---
For each attraction, give 3-5 DIRECT image URLs (ending in .jpg/.jpeg/.png,
landscape, at least 800px wide). Prefer Wikimedia Commons file pages or
official tourism sites. Return ONLY JSON:

{ "<id>": ["https://...", "https://..."] }
---

Save as `images/urls.json`, then:

```bash
guide images --source urls
```

Expect a chunk of LLM-proposed URLs to be dead or undersized. That is exactly
why the tool re-validates every claim — the LLM's word is not evidence.

## The human gate (non-negotiable)

After fetching, numbered contact sheets land in `images/sheets/<id>.jpg`.
Look at them. Kill wrong-subject candidates (the tool cannot see the
subject — you can), fix the `query` field and re-fetch with
`guide images --only <id>` if needed. Then record each decision through
the tool, so it is range-validated:

```bash
guide pick <id> <candidate-number>
```

Bare `guide pick` verifies completeness; `guide finalize` gates the
release. An agent may make these proposals — the human owns the final
call. Aesthetics stay human; only the mechanics are automated.
