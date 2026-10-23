# AGENTS.md — the contract for LLM agents working in this repo

If you are an LLM agent (opencode, Claude Code, pi, ...), you are the
intended worker inside this pipeline. guideforge never calls a model —
**you** are the model. This file is your job description.

## Your two roles

1. **Generator.** Every stage has a prompt template in `prompts/*.md`.
   Execute it: read the prompt, produce the artifact, write it to the
   project directory, then run the matching check.

2. **Vision reviewer (images only).** You can look at
   `images/sheets/<id>.jpg` contact sheets. Review them like a picky human:
   reject wrong-subject shots (a Tower Bridge photo is not the Tower of
   London; "St Paul's Cathedral" exists on four continents), refine the
   attraction's `query` field in `attractions.json`, re-fetch with
   `guide images --source wikimedia --only <id>`, then record your proposal
   with `guide pick <id> <n>`.

## The loop, concretely

```
guide init <dir>            # scaffold
# stage 1: prompts/attractions.md  -> attractions.json  -> guide check attractions
# stage 1b: saturation — run the enumeration again in a fresh session,
#           save as attractions.pass2.json -> guide check coverage
#           (also: coverage vs references/ or Wikidata)
# stage 2: prompts/tiers.md         -> tiers.json        -> guide check tiers
# stage 3: prompts/descriptions.md  -> descriptions.json -> guide check descriptions
# stage 4: prompts/html.md          -> guide.html        -> guide check html
guide images --source wikimedia    # fetch + mechanical validation + sheets
# review sheets, fix subjects, then: guide pick <id> <n> for every attraction
guide finalize              # the only acceptance — every check re-runs
```

## Hard rules

- **Exit code is the acceptance.** Never report a stage as done without
  the check's exit 0 in front of you. Your summary is testimony; tool
  output is evidence. A generator cannot be its own judge — that applies
  to you too.
- **Never hand-edit** `images/manifest.json` candidates or claim checks you
  did not run. Set picks through `guide pick <id> <n>` so they are
  validated in range.
- **Fix causes, not symptoms.** A rejected image is usually a bad query —
  fix the `query` field and re-fetch, do not lower the standard.
- **Taste has a human owner.** Your picks are proposals. The human can
  override any of them; `guide finalize` only proves the mechanics.

## Project rules for this repository

- Python 3.9+, dependencies limited to `requests`, `Pillow`, `PyYAML`.
- After changes: `pytest -q` and `ruff check guideforge tests` must pass.
- Keep the engine comment-free and small; the README tells the story.
