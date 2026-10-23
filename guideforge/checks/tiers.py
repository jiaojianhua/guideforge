import json

from guideforge import paths
from guideforge.checks.attractions import load_attractions
from guideforge.report import Issue, Report


def check(root, spec):
    rep = Report("tiers")
    items, issues = load_attractions(root)
    rep.issues.extend(issues)
    if items is None:
        return rep
    ids = [a.get("id") for a in items if isinstance(a, dict)]
    idset = set(ids)
    p = root / paths.TIERS
    if not p.exists():
        rep.issues.append(Issue("tiers", f"{paths.TIERS} not found"))
        return rep
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        rep.issues.append(Issue("tiers", f"invalid JSON: {e}"))
        return rep
    spec_ids = [t["id"] for t in spec["tiers"]]
    assigned = {}
    for tid in spec_ids:
        members = data.get(tid)
        if members is None:
            rep.issues.append(Issue("tiers", f"tier '{tid}' missing"))
            continue
        if not isinstance(members, list):
            rep.issues.append(Issue("tiers", f"tier '{tid}' must be a list"))
            continue
        for aid in members:
            if aid not in idset:
                rep.issues.append(Issue("tiers", f"unknown attraction '{aid}' in tier '{tid}'"))
            assigned.setdefault(aid, []).append(tid)
    extra = set(data) - set(spec_ids)
    if extra:
        rep.issues.append(Issue("tiers", f"unknown tiers in file: {sorted(extra)}"))
    for aid, ts in sorted(assigned.items()):
        if len(ts) > 1:
            rep.issues.append(Issue("tiers", f"'{aid}' in multiple tiers: {ts}"))
    missing = [a for a in ids if a not in assigned]
    if missing:
        rep.issues.append(Issue("tiers", f"unassigned attractions: {missing}"))
    rep.stats = f"{len(assigned)}/{len(ids)} assigned to {len(spec_ids)} tiers"
    return rep
