import json

import pytest
from helpers import pattern_jpeg

from guideforge.cli import main

HTML = (
    "<html><head><title>T</title></head><body>"
    '<img src="images/alpha.jpg"><img src="images/beta.jpg">'
    "</body></html>"
)


def test_urls_flow_end_to_end(tmp_path, make_project, image_server):
    base = image_server(
        {
            "/a1.jpg": pattern_jpeg(seed=0),
            "/a-small.jpg": pattern_jpeg(600, 400, seed=1),
            "/a-wide.jpg": pattern_jpeg(1600, 500, seed=2),
            "/a2.jpg": pattern_jpeg(seed=3),
            "/a3.jpg": pattern_jpeg(seed=4),
            "/b1.jpg": pattern_jpeg(seed=5),
            "/b2.jpg": pattern_jpeg(seed=6),
            "/b3.jpg": pattern_jpeg(seed=7),
        }
    )
    proj = make_project(
        tmp_path / "proj",
        attract=[
            {"id": "alpha", "name": "Alpha", "area": "C"},
            {"id": "beta", "name": "Beta", "area": "N"},
        ],
        html=HTML,
    )
    (proj / "images").mkdir(exist_ok=True)
    (proj / "images" / "urls.json").write_text(
        json.dumps(
            {
                "alpha": [
                    f"{base}/a1.jpg",
                    f"{base}/a-small.jpg",
                    f"{base}/a-wide.jpg",
                    f"{base}/a2.jpg",
                    f"{base}/a3.jpg",
                    f"{base}/missing.jpg",
                ],
                "beta": [f"{base}/b1.jpg", f"{base}/b2.jpg", f"{base}/b3.jpg"],
            }
        )
    )

    assert main(["--dir", str(proj), "images", "--source", "urls"]) == 0

    manifest = json.loads((proj / "images" / "manifest.json").read_text())
    assert len(manifest["alpha"]["candidates"]) == 3
    assert manifest["alpha"]["picked"] is None
    assert len(manifest["beta"]["candidates"]) == 3
    assert (proj / "images" / "sheets" / "alpha.jpg").exists()
    assert (proj / "images" / "sheets" / "beta.jpg").exists()

    for aid, picked in (("alpha", 1), ("beta", 2)):
        manifest[aid]["picked"] = picked
    (proj / "images" / "manifest.json").write_text(json.dumps(manifest))

    assert main(["--dir", str(proj), "pick"]) == 0
    assert main(["--dir", str(proj), "finalize"]) == 0

    dist = proj / "dist"
    assert (dist / "guide.html").exists()
    assert (dist / "images" / "alpha.jpg").exists()
    assert (dist / "images" / "beta.jpg").exists()
    checklist = (dist / "checklist.md").read_text()
    assert "images/alpha.jpg" in checklist
    assert "images/beta.jpg" in checklist


def test_images_fails_when_everything_rejected(tmp_path, make_project, image_server):
    base = image_server({"/tiny.jpg": pattern_jpeg(400, 300, seed=9)})
    proj = make_project(
        tmp_path / "p",
        attract=[{"id": "solo", "name": "Solo", "area": "X"}],
        html='<html><head><title>T</title></head><body><img src="images/solo.jpg"></body></html>',
    )
    (proj / "images").mkdir(exist_ok=True)
    (proj / "images" / "urls.json").write_text(
        json.dumps({"solo": [f"{base}/tiny.jpg", f"{base}/gone.jpg"]})
    )
    with pytest.raises(SystemExit):
        main(["--dir", str(proj), "images", "--source", "urls"])
    manifest = json.loads((proj / "images" / "manifest.json").read_text())
    assert manifest["solo"]["candidates"] == []
