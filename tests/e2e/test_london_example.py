import json
import shutil
from pathlib import Path

from helpers import pattern_jpeg

from guideforge.cli import main

REPO = Path(__file__).resolve().parents[2]
LONDON = REPO / "examples" / "london"


def test_london_example_full_flow(tmp_path, image_server):
    proj = tmp_path / "london"
    shutil.copytree(LONDON, proj)
    assert main(["--dir", str(proj), "check"]) == 0

    ids = [a["id"] for a in json.loads((proj / "attractions.json").read_text())["attractions"]]
    assert len(ids) >= 5

    routes = {}
    seed = 0
    for aid in ids:
        for n in (1, 2, 3):
            routes[f"/{aid}-{n}.jpg"] = pattern_jpeg(seed=seed)
            seed += 1
    base = image_server(routes)
    (proj / "images").mkdir(exist_ok=True)
    (proj / "images" / "urls.json").write_text(
        json.dumps({aid: [f"{base}/{aid}-{n}.jpg" for n in (1, 2, 3)] for aid in ids})
    )

    assert main(["--dir", str(proj), "images", "--source", "urls"]) == 0

    manifest = json.loads((proj / "images" / "manifest.json").read_text())
    for aid in ids:
        assert len(manifest[aid]["candidates"]) == 3
        assert (proj / "images" / "sheets" / f"{aid}.jpg").exists()
        manifest[aid]["picked"] = 2
    (proj / "images" / "manifest.json").write_text(json.dumps(manifest))

    assert main(["--dir", str(proj), "pick"]) == 0
    assert main(["--dir", str(proj), "finalize"]) == 0

    dist = proj / "dist"
    assert (dist / "guide.html").exists()
    for aid in ids:
        assert (dist / "images" / f"{aid}.jpg").exists()
    checklist = (dist / "checklist.md").read_text()
    assert "(candidate #2)" in checklist
    assert "6/6 picked" in checklist
