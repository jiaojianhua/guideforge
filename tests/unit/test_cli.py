import json

import pytest
from PIL import Image

from guideforge.cli import main


def test_init_scaffolds_project(tmp_path):
    proj = tmp_path / "demo"
    assert main(["init", str(proj)]) == 0
    assert (proj / "spec.yaml").exists()
    assert (proj / "prompts" / "images.md").exists()
    assert (proj / ".gitignore").exists()
    with pytest.raises(SystemExit):
        main(["init", str(proj)])
    assert main(["init", str(proj), "--force"]) == 0


def test_check_empty_project_fails(tmp_path):
    proj = tmp_path / "empty"
    main(["init", str(proj)])
    with pytest.raises(SystemExit):
        main(["--dir", str(proj), "check"])


def test_check_passes_on_valid_project(tmp_path, make_project):
    proj = make_project(tmp_path / "proj")
    assert main(["--dir", str(proj), "check"]) == 0


def test_check_single_stage(tmp_path, make_project):
    proj = make_project(tmp_path / "proj")
    assert main(["--dir", str(proj), "check", "tiers"]) == 0


def test_check_fails_loud(tmp_path, make_project):
    proj = make_project(tmp_path / "proj")
    data = json.loads((proj / "tiers.json").read_text())
    del data["optional"]
    (proj / "tiers.json").write_text(json.dumps(data))
    with pytest.raises(SystemExit) as e:
        main(["--dir", str(proj), "check"])
    assert e.value.code != 0


def test_finalize_full_flow(tmp_path, make_project):
    proj = make_project(tmp_path / "proj")
    with pytest.raises(SystemExit):
        main(["--dir", str(proj), "finalize"])

    manifest = {}
    for aid in ("alpha", "beta", "gamma"):
        cdir = proj / "images" / "candidates" / aid
        cdir.mkdir(parents=True)
        for i in (1, 2):
            Image.new("RGB", (1200, 800), (i * 60, 90, 30)).save(cdir / f"{i}.jpg")
        manifest[aid] = {
            "candidates": [f"images/candidates/{aid}/1.jpg", f"images/candidates/{aid}/2.jpg"],
            "picked": 1,
        }
    (proj / "images" / "manifest.json").write_text(json.dumps(manifest))

    assert main(["--dir", str(proj), "pick"]) == 0
    assert main(["--dir", str(proj), "finalize"]) == 0

    dist = proj / "dist"
    assert (dist / "guide.html").exists()
    assert (dist / "checklist.md").exists()
    for aid in ("alpha", "beta", "gamma"):
        assert (dist / "images" / f"{aid}.jpg").exists()


def test_finalize_rejects_missing_pick(tmp_path, make_project):
    proj = make_project(tmp_path / "proj")
    manifest = {}
    for aid in ("alpha", "beta", "gamma"):
        cdir = proj / "images" / "candidates" / aid
        cdir.mkdir(parents=True)
        Image.new("RGB", (1200, 800)).save(cdir / "1.jpg")
        manifest[aid] = {"candidates": [f"images/candidates/{aid}/1.jpg"], "picked": None}
    (proj / "images" / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(SystemExit):
        main(["--dir", str(proj), "finalize"])
    assert not (proj / "dist").exists()


def test_pick_set_and_range_guard(tmp_path, make_project):
    proj = make_project(tmp_path / "proj")
    cdir = proj / "images" / "candidates" / "alpha"
    cdir.mkdir(parents=True)
    Image.new("RGB", (1200, 800)).save(cdir / "1.jpg")
    Image.new("RGB", (1200, 800), (90, 30, 30)).save(cdir / "2.jpg")
    (proj / "images" / "manifest.json").write_text(json.dumps({
        "alpha": {"candidates": ["images/candidates/alpha/1.jpg", "images/candidates/alpha/2.jpg"], "picked": None},
        "beta": {"candidates": [], "picked": None},
        "gamma": {"candidates": [], "picked": None},
    }))

    assert main(["--dir", str(proj), "pick", "alpha", "2"]) == 0
    manifest = json.loads((proj / "images" / "manifest.json").read_text())
    assert manifest["alpha"]["picked"] == 2

    with pytest.raises(SystemExit):
        main(["--dir", str(proj), "pick", "alpha", "9"])
    with pytest.raises(SystemExit):
        main(["--dir", str(proj), "pick", "ghost", "1"])
    with pytest.raises(SystemExit):
        main(["--dir", str(proj), "pick", "alpha"])
    assert json.loads((proj / "images" / "manifest.json").read_text())["alpha"]["picked"] == 2


def test_finalize_rejects_out_of_range_pick(tmp_path, make_project):
    proj = make_project(tmp_path / "proj")
    manifest = {}
    for aid in ("alpha", "beta", "gamma"):
        cdir = proj / "images" / "candidates" / aid
        cdir.mkdir(parents=True)
        Image.new("RGB", (1200, 800)).save(cdir / "1.jpg")
        manifest[aid] = {"candidates": [f"images/candidates/{aid}/1.jpg"], "picked": 5}
    (proj / "images" / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(SystemExit):
        main(["--dir", str(proj), "finalize"])
