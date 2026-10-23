import json

from guideforge.checks import attractions, descriptions, tiers
from guideforge.spec import load_spec


def spec_of(root):
    return load_spec(root)


def test_attractions_ok(project):
    rep = attractions.check(project, spec_of(project))
    assert rep.ok
    assert rep.stats == "3 attractions"


def test_attractions_duplicate_id(project):
    items = [
        {"id": "alpha", "name": "Alpha", "area": "C"},
        {"id": "beta", "name": "Beta", "area": "N"},
        {"id": "alpha", "name": "Alpha Two"},
    ]
    (project / "attractions.json").write_text(json.dumps({"attractions": items}))
    rep = attractions.check(project, spec_of(project))
    assert not rep.ok
    assert any("duplicate id" in i.message for i in rep.issues)


def test_attractions_duplicate_name(project):
    items = [
        {"id": "alpha", "name": "Same", "area": "C"},
        {"id": "beta", "name": "same", "area": "N"},
    ]
    (project / "attractions.json").write_text(json.dumps({"attractions": items}))
    rep = attractions.check(project, spec_of(project))
    assert not rep.ok
    assert any("duplicate name" in i.message for i in rep.issues)


def test_attractions_bad_slug(project):
    (project / "attractions.json").write_text(json.dumps({"attractions": [{"id": "Big Ben", "name": "X"}]}))
    rep = attractions.check(project, spec_of(project))
    assert not rep.ok
    assert any("bad id" in i.message for i in rep.issues)


def test_attractions_missing_file(project):
    (project / "attractions.json").unlink()
    rep = attractions.check(project, spec_of(project))
    assert not rep.ok


def test_tiers_ok(project):
    rep = tiers.check(project, spec_of(project))
    assert rep.ok
    assert rep.stats == "3/3 assigned to 3 tiers"


def test_tiers_missing_tier(project):
    data = {"must": ["alpha"], "worth": ["beta"]}
    (project / "tiers.json").write_text(json.dumps(data))
    rep = tiers.check(project, spec_of(project))
    assert not rep.ok
    assert any("tier 'optional' missing" in i.message for i in rep.issues)


def test_tiers_unknown_id(project):
    data = {"must": ["alpha", "ghost"], "worth": ["beta"], "optional": ["gamma"]}
    (project / "tiers.json").write_text(json.dumps(data))
    rep = tiers.check(project, spec_of(project))
    assert not rep.ok
    assert any("unknown attraction 'ghost'" in i.message for i in rep.issues)


def test_tiers_duplicate_assignment(project):
    data = {"must": ["alpha"], "worth": ["beta", "alpha"], "optional": ["gamma"]}
    (project / "tiers.json").write_text(json.dumps(data))
    rep = tiers.check(project, spec_of(project))
    assert not rep.ok
    assert any("multiple tiers" in i.message for i in rep.issues)


def test_tiers_unassigned(project):
    data = {"must": ["alpha"], "worth": ["beta"], "optional": []}
    (project / "tiers.json").write_text(json.dumps(data))
    rep = tiers.check(project, spec_of(project))
    assert not rep.ok
    assert any("unassigned" in i.message for i in rep.issues)


def test_descriptions_ok(project):
    rep = descriptions.check(project, spec_of(project))
    assert rep.ok
    assert rep.stats == "3/3 entries complete"


def test_descriptions_missing_field(project):
    data = json.loads((project / "descriptions.json").read_text())
    del data["alpha"]["tips"]
    (project / "descriptions.json").write_text(json.dumps(data))
    rep = descriptions.check(project, spec_of(project))
    assert not rep.ok
    assert any("missing field 'tips'" in i.message for i in rep.issues)


def test_descriptions_summary_too_short(project):
    data = json.loads((project / "descriptions.json").read_text())
    data["alpha"]["summary"] = "too short"
    (project / "descriptions.json").write_text(json.dumps(data))
    rep = descriptions.check(project, spec_of(project))
    assert not rep.ok
    assert any("too short" in i.message for i in rep.issues)


def test_descriptions_summary_too_long(project):
    data = json.loads((project / "descriptions.json").read_text())
    data["alpha"]["summary"] = "x" * 301
    (project / "descriptions.json").write_text(json.dumps(data))
    rep = descriptions.check(project, spec_of(project))
    assert not rep.ok
    assert any("too long" in i.message for i in rep.issues)


def test_descriptions_banned_pattern(project):
    data = json.loads((project / "descriptions.json").read_text())
    data["beta"]["tips"] = "check the TODO list before going"
    (project / "descriptions.json").write_text(json.dumps(data))
    rep = descriptions.check(project, spec_of(project))
    assert not rep.ok
    assert any("banned pattern 'todo'" in i.message for i in rep.issues)


def test_descriptions_banned_pattern_nested(project):
    data = json.loads((project / "descriptions.json").read_text())
    data["gamma"]["highlights"] = ["real one", "lorem ipsum filler"]
    (project / "descriptions.json").write_text(json.dumps(data))
    rep = descriptions.check(project, spec_of(project))
    assert not rep.ok
    assert any("banned pattern 'lorem ipsum'" in i.message for i in rep.issues)


def test_descriptions_unknown_entry(project):
    data = json.loads((project / "descriptions.json").read_text())
    data["ghost"] = {"summary": "x", "highlights": [], "tips": "y"}
    (project / "descriptions.json").write_text(json.dumps(data))
    rep = descriptions.check(project, spec_of(project))
    assert not rep.ok
    assert any("unknown ids" in i.message for i in rep.issues)
