import json
from pathlib import Path

import pytest

SUMMARY = "A " + "notable " * 25 + "place worth a long, unrushed visit in good weather."

HTML = '<html><head><title>Test Guide</title></head><body><img src="images/alpha.jpg"></body></html>'

SPEC = """\
title: Test Guide
tiers:
  - {id: must, label: Must}
  - {id: worth, label: Worth}
  - {id: optional, label: Optional}
"""


@pytest.fixture
def make_project():
    def _make(root, *, attract=None, tiers=None, desc=None, html=HTML, spec=SPEC):
        attract = attract or [
            {"id": "alpha", "name": "Alpha", "area": "Center"},
            {"id": "beta", "name": "Beta", "area": "North"},
            {"id": "gamma", "name": "Gamma", "area": "South"},
        ]
        ids = [a["id"] for a in attract]
        tiers = tiers or {"must": ids[:1], "worth": ids[1:2], "optional": ids[2:]}
        desc = desc or {
            aid: {"summary": SUMMARY, "highlights": ["one", "two"], "tips": "go early"}
            for aid in ids
        }
        root = Path(root)
        root.mkdir(parents=True, exist_ok=True)
        (root / "spec.yaml").write_text(spec, encoding="utf-8")
        (root / "attractions.json").write_text(json.dumps({"attractions": attract}), encoding="utf-8")
        (root / "tiers.json").write_text(json.dumps(tiers), encoding="utf-8")
        (root / "descriptions.json").write_text(json.dumps(desc), encoding="utf-8")
        (root / "guide.html").write_text(html, encoding="utf-8")
        return root

    return _make


@pytest.fixture
def project(tmp_path, make_project):
    return make_project(tmp_path / "proj")
