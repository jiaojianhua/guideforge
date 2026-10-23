import json
import shutil
from pathlib import Path

import pytest

from guideforge.cli import main

REPO = Path(__file__).resolve().parents[2]
LONDON = REPO / "examples" / "london"


def fresh_london(tmp_path):
    proj = tmp_path / "london"
    shutil.copytree(LONDON, proj)
    return proj


def test_london_coverage_passes_with_local_reference(tmp_path):
    proj = fresh_london(tmp_path)
    assert (proj / "reference.json").exists()
    assert main(["--dir", str(proj), "check", "coverage"]) == 0


def test_london_coverage_fails_on_missing_reference(tmp_path):
    proj = fresh_london(tmp_path)
    ref = json.loads((proj / "reference.json").read_text())
    ref.append("Westminster Abbey")
    (proj / "reference.json").write_text(json.dumps(ref))
    with pytest.raises(SystemExit):
        main(["--dir", str(proj), "check", "coverage"])


def test_london_saturation_gate(tmp_path):
    proj = fresh_london(tmp_path)
    (proj / "attractions.pass2.json").write_text(
        json.dumps({"attractions": [{"id": "kew-gardens", "name": "Kew Gardens"}]})
    )
    with pytest.raises(SystemExit):
        main(["--dir", str(proj), "check", "coverage"])

    names = json.loads((proj / "attractions.json").read_text())
    names["attractions"].append({"id": "kew-gardens", "name": "Kew Gardens", "area": "Richmond"})
    (proj / "attractions.json").write_text(json.dumps(names))
    ref = json.loads((proj / "reference.json").read_text())
    ref.append("Kew Gardens")
    (proj / "reference.json").write_text(json.dumps(ref))
    (proj / "attractions.pass2.json").write_text(
        json.dumps({"attractions": [{"id": "kew-gardens", "name": "Kew Gardens"}]})
    )
    assert main(["--dir", str(proj), "check", "coverage"]) == 0
