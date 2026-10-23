# Stage 4 — Render the guide HTML

Paste this prompt with `descriptions.json` and `tiers.json` attached:

---
Render a single-page HTML travel guide. Requirements are hard constraints:

- ONE file, all styling inline (`style="..."` attributes only)
- NO `<style>` tags, NO `<link rel=stylesheet>`, NO `class=` or `id=` attributes
- every attraction gets a section: name, summary, highlights, tips
- sections grouped by tier in this order: must, worth, optional
- each section contains exactly one image:
  `<img src="images/<id>.jpg" style="width:100%;border-radius:8px" alt="<name>">`
- return ONLY the HTML document
---

Save as `guide.html`, then run:

```bash
guide check html
```

The tool verifies: no external stylesheets or style tags, no class/id
attributes, a `<title>` exists, every `<img src>` is either a remote URL or
the managed `images/<id>.jpg` pattern for a known attraction.
