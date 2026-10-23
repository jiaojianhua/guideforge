from pathlib import Path

SPEC = "spec.yaml"
ATTRACT = "attractions.json"
TIERS = "tiers.json"
DESCRIPTIONS = "descriptions.json"
GUIDE_HTML = "guide.html"
URLS = "images/urls.json"
MANIFEST = "images/manifest.json"
CANDIDATES = "images/candidates"
SHEETS = "images/sheets"
DIST = "dist"


def require_project(root: Path) -> Path:
    if not (root / SPEC).exists():
        raise SystemExit(f"no {SPEC} in {root} — run `guide init` first")
    return root
