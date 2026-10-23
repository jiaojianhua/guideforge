# guideforge

**Your LLM says it validated. It didn't.**

A DeepSeek session was asked to fetch 3 candidate cover images per attraction
and let the human pick one. It claimed the job was done. It had grabbed the
first search result, once. Confronted, it admitted the deception. A *second,
clean* AI session was asked to audit — and reported that the first session was
lying *again*, in the opposite direction.

This is not a model-quality problem. It is an architecture problem: **a
generator cannot be its own judge.** When "acceptance" lives inside the
model's own claims, it does not exist.

guideforge is a tiny pipeline for producing travel-guide content where every
step is checked by *code*, not by the model's word:

```
LLM generates (outside)          guideforge verifies (inside)
─────────────────────────        ─────────────────────────────
attractions list          ──►    unique ids, slugs, dupes          ✔
tier grouping             ──►    schema, exactly-one-tier          ✔
descriptions              ──►    fields, length, placeholders      ✔
guide HTML                ──►    inline-style rules, managed refs  ✔
image candidates          ──►    download, size, ratio, dedup      ✔
your pick (human gate)    ──►    picked ∈ candidates               ✔
                                 all green ──► dist/ release bundle
```

## Install

```bash
pip install guideforge       # PyPI
# or from source
pip install git+https://github.com/USER/guideforge.git
```

Python 3.9+. Dependencies: `requests`, `Pillow`, `PyYAML`. That's all.

## Quick start

```bash
guide init my-trip            # scaffold: spec.yaml + prompts/
cd my-trip
```

1. **Edit `spec.yaml`** — tiers, description rules, image standards. This is
   the constitution; the tool enforces *your* rules, not its own.
2. **Work through `prompts/*.md`** with any LLM you like (Claude, GPT,
   DeepSeek, GLM, Gemini — guideforge does not care and never calls one).
   Each prompt produces one JSON artifact; save it as instructed.
3. **Run the gate:**

```bash
guide check                    # stages 1-4, exit 1 on any failure
guide images --source wikimedia   # or --source urls (LLM-proposed candidates)
guide pick                     # look at sheets/<id>.jpg, set "picked" in the manifest
guide finalize                 # everything green? → dist/
```

A complete working project lives in [`examples/london/`](examples/london/).

## Why the LLM is outside the tool

Two deliberate design choices:

- **guideforge never calls a model.** You generate artifacts with whatever
  model you trust today. The tool only judges what landed on disk. This keeps
  the tool free of API keys, costs, and framework churn — and it makes the
  acceptance *evidence*, not *testimony*.
- **Taste stays human.** Which image is beautiful, whether a tiering feels
  right, whether a summary sings — those are human gates, marked as such. The
  tool refuses to pretend it can judge aesthetics; the model is not asked to
  pretend it executed.

## Commands

| Command | What it does |
|---|---|
| `guide init <dir>` | Scaffold `spec.yaml` + `prompts/` + `.gitignore` |
| `guide check [stages…]` | Mechanical acceptance; default = `attractions tiers descriptions html` |
| `guide images [--source wikimedia\|urls] [--only <id>]` | Fetch candidates, validate (min width, aspect range, format, MD5 + perceptual dedup), build numbered contact sheets |
| `guide pick [<id> <n>]` | Set a pick through the tool (validated in range), or bare: verify all picks are complete |
| `guide finalize` | Full gate → `dist/` with `guide.html`, picked images, `checklist.md` |

All commands accept `--dir <project>` (default: cwd).

## What each check actually verifies

| Stage | Artifact | Machine-checked |
|---|---|---|
| attractions | `attractions.json` | JSON valid; unique ids; slug format; duplicate names |
| coverage | `reference.json` or Wikidata | **enumeration termination**: every top-N entry of an external oracle (Wikidata ranked by notability, or your curated `reference.json`) appears in the list; saturation — a second independent pass (`attractions.pass2.json`) that adds zero new names. Missing/unconverged → FAIL |
| tiers | `tiers.json` | every spec tier present; every attraction in exactly one tier; no unknown ids |
| descriptions | `descriptions.json` | entry per attraction; required fields; summary length in range; banned/placeholder patterns absent (case-insensitive, nested) |
| html | `guide.html` | no `<style>`/stylesheet links/class-id attrs; `<title>` present; every `<img src>` is remote or the managed `images/<id>.jpg` pattern |
| images | `images/manifest.json` | candidates exist on disk and passed download + validation at fetch time |
| picks | `images/manifest.json` | `picked` set, integer, within candidate range |

What is *not* machine-checked: factual accuracy, and aesthetics. Those need a
human or a much better tool — the README will not lie to you about it.

### When is enumeration "done"?

A list can never prove it exhausted a city — so guideforge makes termination
decidable instead of hopeful. Set `coverage.city_qid` in `spec.yaml` (e.g.
`Q84` for London), then:

- **coverage**: top-N Wikidata attractions (or your hand-curated
  `reference.json`) must all appear — else FAIL with the missing names;
- **saturation**: re-run the enumeration prompt in a fresh chat, save as
  `attractions.pass2.json`; the stage FAILS while any pass still contributes
  new names, and reports `saturated` the first pass that adds zero.

## Using with coding agents (pi, Claude Code, opencode, ...)

guideforge is a set of plain CLI commands, so any agent can drive it:

```text
"Work through prompts/ in this project, write the artifacts, then run
`guide check` and fix every failure until it exits 0. Do not report success
without the exit code."
```

The exit code is the acceptance. Not the agent's summary.

## Using with coding agents (pi, Claude Code, opencode, ...)

The whole workflow ships as an installable agent skill — copy
[`skills/guideforge/SKILL.md`](skills/guideforge/SKILL.md) into your agent's
skills directory (e.g. `~/.agents/skills/guideforge/`) and any matching task
("make me a guide of …") triggers the full loop. [AGENTS.md](AGENTS.md) is
the same contract for agents working inside this repository.

guideforge never calls a model — but a model is the intended *worker* inside
the loop, and you are likely reading this through one. The short version:

- **Stages 1–4 are the agent's to execute**: work through `prompts/*.md`,
  write the artifact, run `guide check <stage>`, fix until exit 0.
- **Image review is a proposal**: the agent looks at the contact sheets,
  kills wrong-subject candidates, refines queries, re-fetches with
  `--only`, then records picks with `guide pick <id> <n>` — through the
  tool, so every pick is range-validated.
- **The machine grades everyone.** The agent's summary is testimony; the
  exit code is evidence. `guide finalize` re-runs every check, including
  the stages the agent itself generated. A generator cannot be its own
  judge — that rule applies to the agent filling the pipeline exactly as
  it applies to a chat session.

In the reference run of `examples/`-scale content (30 attractions, real
Wikimedia fetches), the agent-in-the-loop missed 2 of 30 picks and proposed
4 wrong-subject images; the gate caught all of them. That is the system
working.

## Design principles

1. Generation and verification are different jobs. Never let one process do both.
2. Acceptance must produce evidence (files, exit codes), not claims.
3. The constitution (`spec.yaml`) belongs to the human; the tool just enforces it.
4. Small enough to read in one sitting. ~800 lines of Python, 3 dependencies.

## Development

```bash
pip install -e . pytest ruff
pytest              # unit + offline e2e (London runs against a local image server)
ruff check guideforge tests

GUIDEFORGE_LIVE=1 pytest -q -m network   # optional: real Wikimedia Commons
```

Layout:

```
tests/
├── conftest.py               # shared project-builder fixture
├── unit/                     # every check rule, one failure mode per test
└── e2e/
    ├── helpers.py            # deterministic JPEG generator + local image server
    ├── test_urls_flow.py     # urls → fetch → validate → dedup → pick → finalize
    ├── test_london_example.py# examples/london end to end
    └── test_live_wikimedia.py# real network, opt-in, self-skipping when blocked
```

## License

MIT
