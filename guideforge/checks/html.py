from html.parser import HTMLParser

from guideforge import paths
from guideforge.checks.attractions import load_attractions
from guideforge.report import Issue, Report


class _Audit(HTMLParser):
    def __init__(self, inline_only):
        super().__init__()
        self.inline_only = inline_only
        self.issues = []
        self.img_srcs = []
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "style":
            self.issues.append("<style> tag found (inline-style only)")
        if tag == "link" and "stylesheet" in (a.get("rel") or "").lower():
            self.issues.append("<link rel=stylesheet> found (inline-style only)")
        if tag == "title":
            self._in_title = True
        if tag == "img" and a.get("src"):
            self.img_srcs.append(a["src"])
        if self.inline_only:
            for banned in ("class", "id"):
                if banned in a:
                    self.issues.append(f"<{tag}> has {banned}= (editors strip it)")

    def handle_data(self, data):
        if self._in_title:
            self.title += data

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False


def check(root, spec):
    rep = Report("html")
    p = root / paths.GUIDE_HTML
    if not p.exists():
        rep.issues.append(Issue("html", f"{paths.GUIDE_HTML} not found"))
        return rep
    items, issues = load_attractions(root)
    rep.issues.extend(issues)
    known = {a.get("id") for a in (items or [])}
    audit = _Audit(spec["html"].get("inline_style_only", True))
    audit.feed(p.read_text(encoding="utf-8"))
    rep.issues.extend(Issue("html", m) for m in audit.issues)
    if not audit.title.strip():
        rep.issues.append(Issue("html", "missing <title>"))
    for src in audit.img_srcs:
        if src.startswith(("http://", "https://")):
            continue
        parts = src.split("/")
        if len(parts) == 2 and parts[0] == "images" and parts[1].rsplit(".", 1)[0] in known:
            continue
        rep.issues.append(Issue("html", f"unmanaged image src: {src} (use images/<id>.jpg)"))
    rep.stats = f"{len(audit.img_srcs)} image refs"
    return rep
