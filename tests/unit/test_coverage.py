import json

from guideforge.checks import coverage
from guideforge.spec import load_spec

REF = ["Alpha", "Beta", "Gamma"]


def with_coverage(project, extra=""):
    text = (project / "spec.yaml").read_text()
    (project / "spec.yaml").write_text(text + "\ncoverage:\n  city_qid: Q84\n" + extra)
    return load_spec(project)


def write_ref(root, names):
    (root / "reference.json").write_text(json.dumps(names))


def test_skipped_without_config(project):
    rep = coverage.check(project, load_spec(project))
    assert rep.ok
    assert "skipped" in rep.stats


def test_full_coverage_passes(project):
    write_ref(project, REF)
    rep = coverage.check(project, with_coverage(project))
    assert rep.ok
    assert "3/3" in rep.stats


def test_missing_top_reference_fails(project):
    write_ref(project, REF + ["Delta"])
    rep = coverage.check(project, with_coverage(project))
    assert not rep.ok
    assert any("Delta" in i.message for i in rep.issues)


def test_matching_normalizes_case_and_article(project):
    data = json.loads((project / "attractions.json").read_text())
    data["attractions"][1]["name"] = "The Beta"
    (project / "attractions.json").write_text(json.dumps(data))
    write_ref(project, ["beta", "Alpha", "Gamma"])
    rep = coverage.check(project, with_coverage(project))
    assert rep.ok


def test_reference_json_accepts_objects(project):
    write_ref(project, [{"name": n, "sitelinks": 9} for n in REF])
    rep = coverage.check(project, with_coverage(project))
    assert rep.ok


def test_references_folder_merges_sources(project):
    (project / "references").mkdir()
    (project / "references" / "wikidata.json").write_text(json.dumps(["Alpha", "Beta"]))
    (project / "references" / "guidebook.json").write_text(json.dumps(["Beta", "Gamma", "Delta"]))
    rep = coverage.check(project, with_coverage(project))
    assert not rep.ok
    assert any("Delta" in i.message for i in rep.issues)
    assert "2 sources" in rep.stats

    (project / "attractions.json").write_text(
        json.dumps({"attractions": [
            {"id": "alpha", "name": "Alpha"},
            {"id": "beta", "name": "Beta"},
            {"id": "gamma", "name": "Gamma"},
            {"id": "delta", "name": "Delta"},
        ]})
    )
    data = json.loads((project / "tiers.json").read_text())
    data["optional"].append("delta")
    (project / "tiers.json").write_text(json.dumps(data))
    desc = json.loads((project / "descriptions.json").read_text())
    desc["delta"] = desc["alpha"]
    (project / "descriptions.json").write_text(json.dumps(desc))
    rep = coverage.check(project, with_coverage(project))
    assert rep.ok
    assert "4/4" in rep.stats


def test_references_folder_dedupes_across_sources(project):
    (project / "references").mkdir()
    (project / "references" / "a.json").write_text(json.dumps(["Alpha", "Alpha", "Alpha"]))
    rep = coverage.check(project, with_coverage(project))
    assert rep.ok
    assert "1/1" in rep.stats


def test_reference_unavailable_is_warn(project, monkeypatch):
    def boom(*args, **kwargs):
        raise ConnectionError("no network")

    monkeypatch.setattr(coverage, "fetch_reference", boom)
    rep = coverage.check(project, with_coverage(project))
    assert rep.ok
    assert rep.stats == "unverified"
    assert any(i.level == "warn" for i in rep.issues)


def test_pass2_new_items_fails(project):
    write_ref(project, REF)
    (project / "attractions.pass2.json").write_text(
        json.dumps({"attractions": [{"id": "delta", "name": "Delta"}]})
    )
    rep = coverage.check(project, with_coverage(project))
    assert not rep.ok
    assert any("not saturated" in i.message for i in rep.issues)


def test_pass2_zero_new_is_saturated(project):
    write_ref(project, REF)
    (project / "attractions.pass2.json").write_text(
        json.dumps({"attractions": [{"id": "alpha-again", "name": "Alpha"}]})
    )
    rep = coverage.check(project, with_coverage(project))
    assert rep.ok
    assert "saturated" in rep.stats


def test_pass2_invalid_json_fails(project):
    write_ref(project, REF)
    (project / "attractions.pass2.json").write_text("{broken")
    rep = coverage.check(project, with_coverage(project))
    assert not rep.ok
    assert any("invalid attractions.pass2.json" in i.message for i in rep.issues)
