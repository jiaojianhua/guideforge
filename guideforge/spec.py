from pathlib import Path

import yaml

DEFAULT_SPEC = {
    "title": "Untitled Guide",
    "tiers": [
        {"id": "must", "label": "Must visit"},
        {"id": "worth", "label": "Worth your time"},
        {"id": "optional", "label": "If time permits"},
    ],
    "description": {
        "required_fields": ["summary", "highlights", "tips"],
        "summary_min_chars": 80,
        "summary_max_chars": 300,
        "banned_patterns": ["TODO", "TBD", "lorem ipsum", "待补充", "占位"],
    },
    "html": {"inline_style_only": True},
    "coverage": {},
    "images": {
        "candidates_per_attraction": 3,
        "min_width": 800,
        "aspect_min": 1.2,
        "aspect_max": 1.9,
        "formats": [".jpg", ".jpeg", ".png", ".webp"],
    },
}


def load_spec(root: Path) -> dict:
    raw = yaml.safe_load((root / "spec.yaml").read_text(encoding="utf-8")) or {}
    merged = {**DEFAULT_SPEC, **raw}
    for key, sub in DEFAULT_SPEC.items():
        if isinstance(sub, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**sub, **merged[key]}
    return merged
