---
name: guideforge
description: Produce mechanically-validated travel guides (or any enumerable + describable + illustrable content) through the guideforge pipeline. Use when the user asks to create a city/area guide, a curated attraction list with photos, tiered recommendations with cover images, or any content where an LLM must enumerate, describe, illustrate AND prove the work was done.
---

# Guideforge — you are the worker, the tool is the judge

`guideforge` is a CLI that turns "LLM, make me a guide" into a checked
pipeline. It never calls a model — **you** produce every artifact, and the
tool mechanically validates each one. Exit codes are the only acceptance;
your own summary is testimony, not evidence.

## Prerequisites

```bash
pip install guideforge        # or: pip install -e <repo> for development
guide --help
```

## The loop

```bash
guide init <project-dir>
cd <project-dir>
```

Then stage by stage — generate, save, check, fix until exit 0:

1. **Enumerate** — follow `prompts/attractions.md`; write `attractions.json`;
   `guide check attractions`. Termination is decidable: configure
   `coverage.city_qid` (Wikidata oracle) or drop curated lists into
   `references/` (one JSON per source — never rely on a single site), and
   run the enumeration a second time in a fresh session as
   `attractions.pass2.json`; `guide check coverage` FAILS while any pass
   still adds new names and reports `saturated` at the first zero-new pass.
2. **Tier** — `prompts/tiers.md` → `tiers.json` → `guide check tiers`.
3. **Describe** — `prompts/descriptions.md` → `descriptions.json` →
   `guide check descriptions`.
4. **Render** — `prompts/html.md` → `guide.html` → `guide check html`.
5. **Images** — `guide images --source wikimedia` (or `--source urls` with
   LLM-proposed URLs for any site). The tool downloads, validates (min
   width, aspect range, format, MD5 + perceptual dedup) and builds numbered
   contact sheets in `images/sheets/<id>.jpg`.
6. **Review and pick** — look at every sheet (you have vision). Kill
   wrong-subject candidates (Tower Bridge is not the Tower of London;
   "St Paul's" exists on four continents), fix the attraction's `query`
   field in `attractions.json`, re-fetch with
   `guide images --only <id>`, then record each decision with
   `guide pick <id> <n>` — through the tool, never by editing the manifest.
7. **Finalize** — `guide finalize` re-runs every check; only exit 0 writes
   `dist/`.

## Hard rules

- Never claim a stage is done without that stage's check exiting 0 in front
  of you.
- Never hand-edit `images/manifest.json` or fabricate check results.
- A rejected image is usually a bad query — fix the query, never lower the
  standard.
- Your picks are proposals; the human owns taste and may override. The
  mechanics belong to the tool.

## Extending

Any "enumerate → tier → describe → render → illustrate" workflow (restaurants,
books, products, exercises) reuses this shape: adjust `spec.yaml`, the
prompts, and the reference sources. Keep the engine small; keep the gate
mechanical.
