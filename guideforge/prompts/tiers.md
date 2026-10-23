# Stage 2 — Tier the attractions

Edit the tiers and labels in `spec.yaml` first (3 tiers is the sweet spot).
Then paste this prompt with your `attractions.json` attached:

---
Group these attractions into 3 tiers: must / worth / optional.

Tier definitions:
- must: a trip would feel incomplete without it
- worth: see it if you have 1+ spare day
- optional: only for special interests or bad-weather backups

Return ONLY JSON:

```json
{ "must": ["id", "id"], "worth": ["id"], "optional": ["id"] }
```

Every attraction must appear in exactly one tier.
---

Save as `tiers.json`, then run:

```bash
guide check tiers
```

The tool verifies: every tier present, every attraction assigned exactly once,
no unknown ids. It does NOT judge whether the tiering is right — read the
`must` list yourself; that is the heart of your guide.
