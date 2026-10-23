import shutil
from datetime import date

from guideforge import paths
from guideforge.checks import attractions, coverage, descriptions, html, tiers
from guideforge.images import load_manifest, report_images, report_picks
from guideforge.report import render

TEXT_CHECKS = [attractions, coverage, tiers, descriptions, html]


def finalize(root, spec):
    reports = [c.check(root, spec) for c in TEXT_CHECKS]
    reports.append(report_images(root, spec))
    reports.append(report_picks(root, spec))
    print(render(reports))
    failed = [r for r in reports if not r.ok]
    if failed:
        print(f"\n{len(failed)} stage(s) failed — {paths.DIST}/ not written")
        return 1
    dist = root / paths.DIST
    if dist.exists():
        shutil.rmtree(dist)
    (dist / "images").mkdir(parents=True)
    manifest = load_manifest(root)
    for aid, entry in manifest.items():
        src = root / entry["candidates"][entry["picked"] - 1]
        shutil.copy(src, dist / "images" / f"{aid}.jpg")
    shutil.copy(root / paths.GUIDE_HTML, dist / paths.GUIDE_HTML)
    lines = [
        f"# release checklist — {spec.get('title', 'guide')}",
        f"date: {date.today().isoformat()}",
        "",
    ]
    for r in reports:
        lines.append(f"- [x] {r.stage}: {r.stats}")
        for i in r.issues:
            if i.level == "warn":
                lines.append(f"  - warn: {i.message}")
    lines.append("")
    for aid, entry in manifest.items():
        lines.append(f"- images/{aid}.jpg (candidate #{entry['picked']})")
    (dist / "checklist.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nrelease bundle written to {dist}/")
    return 0
