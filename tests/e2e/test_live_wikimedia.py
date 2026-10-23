import os

import pytest

from guideforge.images import fetch
from guideforge.spec import load_spec

pytestmark = [
    pytest.mark.network,
    pytest.mark.skipif(
        os.environ.get("GUIDEFORGE_LIVE") != "1",
        reason="hits the real network — opt in with GUIDEFORGE_LIVE=1 pytest -m network",
    ),
]

HTML = '<html><head><title>L</title></head><body><img src="images/tower-bridge.jpg"></body></html>'


def test_live_wikimedia(tmp_path, make_project):
    proj = make_project(
        tmp_path / "live",
        attract=[{"id": "tower-bridge", "name": "Tower Bridge", "area": "London"}],
        html=HTML,
    )
    spec = load_spec(proj)
    manifest = fetch(proj, spec, "wikimedia")
    entry = manifest["tower-bridge"]
    if not entry["candidates"]:
        pytest.skip("wikimedia unreachable or no results from this network")
    assert len(entry["candidates"]) <= spec["images"]["candidates_per_attraction"]
    assert (proj / "images" / "sheets" / "tower-bridge.jpg").exists()


def test_live_wikidata_reference():
    from guideforge.reference import fetch_reference

    try:
        names = fetch_reference("Q84", "en", 30)
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"wikidata unreachable: {e}")
    if len(names) < 10:
        pytest.skip("unexpected sparse reference set from this network")
    joined = " | ".join(names).casefold()
    assert "museum" in joined or "bridge" in joined or "palace" in joined
