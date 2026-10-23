import json
import re

from guideforge import paths
from guideforge.report import Issue, Report

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def load_attractions(root):
    p = root / paths.ATTRACT
    if not p.exists():
        return None, [Issue("attractions", f"{paths.ATTRACT} not found")]
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return None, [Issue("attractions", f"invalid JSON: {e}")]
    items = data.get("attractions") if isinstance(data, dict) else data
    if not isinstance(items, list):
        return None, [Issue("attractions", 'expected a list or {"attractions": [...]}')]
    return items, []


def check(root, spec):
    rep = Report("attractions")
    items, issues = load_attractions(root)
    rep.issues.extend(issues)
    if items is None:
        return rep
    seen_ids = set()
    seen_names = {}
    for item in items:
        if not isinstance(item, dict):
            rep.issues.append(Issue("attractions", f"entry is not an object: {item!r}"))
            continue
        aid = item.get("id", "")
        name = item.get("name", "")
        if not ID_RE.match(aid):
            rep.issues.append(Issue("attractions", f"bad id {aid!r} (lowercase slug required)"))
        if not name:
            rep.issues.append(Issue("attractions", f"{aid or '?'}: missing name"))
        if aid in seen_ids:
            rep.issues.append(Issue("attractions", f"duplicate id: {aid}"))
        seen_ids.add(aid)
        key = name.casefold()
        if key and key in seen_names:
            rep.issues.append(Issue("attractions", f"duplicate name: {name} (same as {seen_names[key]})"))
        seen_names.setdefault(key, aid)
    rep.stats = f"{len(items)} attractions"
    return rep
