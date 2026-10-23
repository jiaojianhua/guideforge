import json

from guideforge import paths
from guideforge.checks.attractions import load_attractions
from guideforge.report import Issue, Report


def iter_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for v in value:
            yield from iter_strings(v)
    elif isinstance(value, dict):
        for v in value.values():
            yield from iter_strings(v)


def check(root, spec):
    rep = Report("descriptions")
    items, issues = load_attractions(root)
    rep.issues.extend(issues)
    if items is None:
        return rep
    ids = [a.get("id") for a in items if isinstance(a, dict)]
    p = root / paths.DESCRIPTIONS
    if not p.exists():
        rep.issues.append(Issue("descriptions", f"{paths.DESCRIPTIONS} not found"))
        return rep
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        rep.issues.append(Issue("descriptions", f"invalid JSON: {e}"))
        return rep
    conf = spec["description"]
    required = conf["required_fields"]
    banned = [b.casefold() for b in conf["banned_patterns"]]
    smin = conf.get("summary_min_chars")
    smax = conf.get("summary_max_chars")
    complete = 0
    for aid in ids:
        entry = data.get(aid)
        if entry is None:
            rep.issues.append(Issue("descriptions", f"{aid}: missing entry"))
            continue
        if not isinstance(entry, dict):
            rep.issues.append(Issue("descriptions", f"{aid}: entry must be an object"))
            continue
        ok = True
        for f in required:
            v = entry.get(f)
            if v is None or v == "" or v == []:
                rep.issues.append(Issue("descriptions", f"{aid}: missing field '{f}'"))
                ok = False
        summary = entry.get("summary", "")
        if isinstance(summary, str):
            if smin and len(summary) < smin:
                rep.issues.append(Issue("descriptions", f"{aid}: summary too short ({len(summary)} < {smin})"))
                ok = False
            if smax and len(summary) > smax:
                rep.issues.append(Issue("descriptions", f"{aid}: summary too long ({len(summary)} > {smax})"))
                ok = False
        for text in iter_strings(entry):
            folded = text.casefold()
            for b in banned:
                if b in folded:
                    rep.issues.append(Issue("descriptions", f"{aid}: banned pattern '{b}'"))
                    ok = False
        if ok:
            complete += 1
    extra = set(data) - set(ids)
    if extra:
        rep.issues.append(Issue("descriptions", f"entries for unknown ids: {sorted(extra)}"))
    rep.stats = f"{complete}/{len(ids)} entries complete"
    return rep
