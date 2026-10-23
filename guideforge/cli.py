import argparse
import shutil
import sys
from pathlib import Path

from guideforge import paths
from guideforge.checks import attractions, coverage, descriptions, html, tiers
from guideforge.finalize import finalize
from guideforge.images import fetch, report_images, report_picks
from guideforge.report import render
from guideforge.spec import load_spec

TEXT_STAGES = {
    "attractions": attractions.check,
    "coverage": coverage.check,
    "tiers": tiers.check,
    "descriptions": descriptions.check,
    "html": html.check,
}
ALL_STAGES = {**TEXT_STAGES, "images": report_images, "picks": report_picks}


def require_root(args):
    root = Path(args.dir).resolve()
    if not (root / paths.SPEC).exists():
        sys.exit(f"no {paths.SPEC} in {root} — run `guide init {root}` first")
    return root


def cmd_init(args):
    root = Path(args.dir).resolve()
    if (root / paths.SPEC).exists() and not args.force:
        sys.exit(f"{root} already has {paths.SPEC} (use --force)")
    root.mkdir(parents=True, exist_ok=True)
    pkg = Path(__file__).parent
    shutil.copy(pkg / "templates" / "spec.yaml", root / paths.SPEC)
    prompts = root / "prompts"
    prompts.mkdir(exist_ok=True)
    for md in sorted((pkg / "prompts").glob("*.md")):
        shutil.copy(md, prompts / md.name)
    (root / ".gitignore").write_text("dist/\nimages/candidates/\nimages/sheets/\nimages/.tmp/\n")
    print(f"initialized guideforge project in {root}")
    print("next:")
    print("  1. edit spec.yaml (tiers, style rules, image standards)")
    print("  2. work through prompts/*.md with any LLM, save artifacts as instructed")
    print("  3. guide check — mechanical acceptance")
    print("  4. guide images && guide pick && guide finalize")


def cmd_check(args):
    root = require_root(args)
    spec = load_spec(root)
    names = args.stages or list(TEXT_STAGES)
    reports = [ALL_STAGES[n](root, spec) for n in names]
    print(render(reports))
    bad = sum(1 for r in reports if not r.ok)
    if bad:
        sys.exit(f"\n{bad} stage(s) failed")
    print("\nall green")


def cmd_images(args):
    root = require_root(args)
    spec = load_spec(root)
    fetch(root, spec, args.source, only=args.only)
    print()
    rep = report_images(root, spec)
    print(render([rep]))
    print(f"\ncontact sheets in {paths.SHEETS}/ — review, then set \"picked\" in {paths.MANIFEST}")
    if not rep.ok:
        sys.exit(1)


def cmd_pick(args):
    root = require_root(args)
    spec = load_spec(root)
    if args.attraction:
        if args.choice is None:
            sys.exit("usage: guide pick [id choice] — set a pick, or run bare for status")
        from guideforge.images import load_manifest, save_manifest

        manifest = load_manifest(root)
        entry = manifest.get(args.attraction)
        if not entry or not entry.get("candidates"):
            sys.exit(f"{args.attraction}: no candidates — run `guide images` first")
        if args.choice not in range(1, len(entry["candidates"]) + 1):
            sys.exit(f"{args.attraction}: choice {args.choice} out of range 1..{len(entry['candidates'])}")
        entry["picked"] = args.choice
        save_manifest(root, manifest)
        print(f"{args.attraction} -> candidate #{args.choice}")
        return
    rep = report_picks(root, spec)
    print(render([rep]))
    if not rep.ok:
        sys.exit(1)


def cmd_finalize(args):
    root = require_root(args)
    spec = load_spec(root)
    if finalize(root, spec):
        sys.exit(1)


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="guide", description="mechanically-checked pipeline for AI-written travel guides"
    )
    p.add_argument("--dir", default=".", help="project directory (default: cwd)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("init", help="scaffold a new guide project")
    sp.add_argument("dir")
    sp.add_argument("--force", action="store_true")
    sp.set_defaults(fn=cmd_init)

    sp = sub.add_parser("check", help="run mechanical acceptance checks")
    sp.add_argument("stages", nargs="*", choices=sorted(ALL_STAGES))
    sp.set_defaults(fn=cmd_check)

    sp = sub.add_parser("images", help="fetch + validate candidate images")
    sp.add_argument("--source", choices=["urls", "wikimedia"], default="wikimedia")
    sp.add_argument("--only", default=None, help="re-fetch a single attraction id")
    sp.set_defaults(fn=cmd_images)

    sp = sub.add_parser("pick", help="set a pick (guide pick <id> <n>) or show pick status")
    sp.add_argument("attraction", nargs="?", default=None)
    sp.add_argument("choice", nargs="?", type=int, default=None)
    sp.set_defaults(fn=cmd_pick)

    sp = sub.add_parser("finalize", help="full gate; write release bundle")
    sp.set_defaults(fn=cmd_finalize)

    args = p.parse_args(argv)
    args.fn(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
