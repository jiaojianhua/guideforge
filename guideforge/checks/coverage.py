import json
import re
from difflib import SequenceMatcher

from guideforge.checks.attractions import load_attractions
from guideforge.reference import fetch_reference
from guideforge.report import Issue, Report


def norm(s):
    s = s.casefold()
    s = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", s)
    s = re.sub(r"\bthe\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def score(a, b):
    if not a or not b:
        return 0.0
    if a == b or a in b or b in a:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def load_reference(root, conf):
    p = root / "reference.json"
    if p.exists():
        raw = json.loads(p.read_text(encoding="utf-8"))
        names = [r if isinstance(r, str) else r.get("name", "") for r in raw]
        return [n for n in names if n], "reference.json"
    multi = sorted((root / "references").glob("*.json")) if (root / "references").is_dir() else []
    if multi:
        merged, seen = [], set()
        for f in multi:
            raw = json.loads(f.read_text(encoding="utf-8"))
            for r in raw:
                name = r if isinstance(r, str) else r.get("name", "")
                key = norm(name)
                if name and key not in seen:
                    seen.add(key)
                    merged.append(name)
        return merged, f"references/ ({len(multi)} sources)"
    try:
        return fetch_reference(
            conf["city_qid"], conf.get("lang", "en"), int(conf.get("top_n", 20)) * 2
        ), "wikidata"
    except Exception as e:  # noqa: BLE001 — network layer raises anything
        return None, f"reference unavailable ({e})"


def coverage_gaps(guide_names, candidate_names, threshold):
    guide_norm = [norm(n) for n in guide_names]
    missing = []
    for name in candidate_names:
        n = norm(name)
        best = max((score(n, g) for g in guide_norm), default=0.0)
        if best < threshold:
            missing.append(name)
    return missing


def check(root, spec):
    rep = Report("coverage")
    conf = spec.get("coverage") or {}
    if not conf.get("city_qid"):
        rep.stats = "skipped (set coverage.city_qid in spec.yaml)"
        return rep
    items, issues = load_attractions(root)
    rep.issues.extend(issues)
    if items is None:
        return rep
    threshold = float(conf.get("match_threshold", 0.72))
    ref, source = load_reference(root, conf)
    if ref is None:
        rep.issues.append(
            Issue("coverage", f"{source} — cache a reference.json to verify coverage", level="warn")
        )
        rep.stats = "unverified"
        return rep
    guide_names = [a.get("name", "") for a in items]
    top_n = int(conf.get("top_n", 20))
    top = ref[:top_n]
    missing = coverage_gaps(guide_names, top, threshold)
    if missing:
        rep.issues.append(Issue("coverage", f"top reference not in guide: {missing}"))
    rep.stats = f"{len(top) - len(missing)}/{len(top)} top-{len(top)} covered ({source})"

    p2 = root / "attractions.pass2.json"
    if p2.exists():
        try:
            data2 = json.loads(p2.read_text(encoding="utf-8"))
            items2 = data2.get("attractions") if isinstance(data2, dict) else data2
            names2 = [
                a.get("name", "") if isinstance(a, dict) else str(a) for a in (items2 or [])
            ]
            new = coverage_gaps(guide_names, [n for n in names2 if n], threshold)
            if new:
                rep.issues.append(
                    Issue(
                        "coverage",
                        f"pass2 discovered {len(new)} new: {new} — enumeration not saturated; "
                        "merge them and run another pass",
                    )
                )
            else:
                rep.stats += "; saturated (pass2 added 0)"
        except json.JSONDecodeError as e:
            rep.issues.append(Issue("coverage", f"invalid attractions.pass2.json: {e}"))
    return rep
