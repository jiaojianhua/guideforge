import hashlib
import json
import shutil
import time
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

from guideforge import paths
from guideforge.checks.attractions import load_attractions
from guideforge.report import Issue, Report
from guideforge.wikimedia import search_commons

UA = {"User-Agent": "guideforge/0.1 (open-source content tool)"}


def ahash(img):
    g = img.convert("L").resize((8, 8), Image.LANCZOS)
    px = list(g.tobytes())
    avg = sum(px) / len(px)
    bits = 0
    for p in px:
        bits = (bits << 1) | (1 if p >= avg else 0)
    return bits


def hamming(a, b):
    return bin(a ^ b).count("1")


FORMAT_ALIASES = {"JPEG": ".jpg", "MPO": ".jpg", "PNG": ".png", "WEBP": ".webp"}


def validate_image(path, spec):
    conf = spec["images"]
    try:
        img = Image.open(path)
        img.load()
    except Exception:  # noqa: BLE001 — corrupt downloads raise anything
        return None, "not a readable image"
    real = FORMAT_ALIASES.get(getattr(img, "format", "") or "", "")
    if real not in conf["formats"]:
        return None, f"format {real or getattr(img, 'format', 'unknown')} not allowed"
    w, h = img.size
    if w < conf["min_width"]:
        return None, f"too small ({w}x{h}, need width >= {conf['min_width']})"
    ratio = w / h
    if not (conf["aspect_min"] <= ratio <= conf["aspect_max"]):
        return None, f"aspect {ratio:.2f} outside [{conf['aspect_min']}, {conf['aspect_max']}]"
    return img, None


def validate_batch(paths_list, spec):
    kept = []
    rejected = []
    hashes = []
    md5s = set()
    for p in paths_list:
        img, err = validate_image(p, spec)
        if err:
            rejected.append((p, err))
            continue
        digest = hashlib.md5(Path(p).read_bytes()).hexdigest()
        if digest in md5s:
            rejected.append((p, "exact duplicate"))
            continue
        h = ahash(img)
        if any(hamming(h, x) <= 5 for x in hashes):
            rejected.append((p, "near duplicate"))
            continue
        md5s.add(digest)
        hashes.append(h)
        kept.append((p, img))
    return kept, rejected


def download(url, dest):
    with requests.get(url, headers=UA, timeout=(10, 30), stream=True) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            f.writelines(r.iter_content(65536))


def load_manifest(root):
    p = root / paths.MANIFEST
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def save_manifest(root, manifest):
    p = root / paths.MANIFEST
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_sheet(root, aid, rel_paths):
    pad, thumb_w, label_h = 12, 360, 30
    thumbs = []
    for i, rel in enumerate(rel_paths, 1):
        img = Image.open(root / rel).convert("RGB")
        r = thumb_w / img.width
        img = img.resize((thumb_w, max(1, int(img.height * r))), Image.LANCZOS)
        thumbs.append((i, img))
    row_h = label_h + max(t.height for _, t in thumbs)
    sheet = Image.new("RGB", (pad + len(thumbs) * (thumb_w + pad), row_h + pad * 2), "white")
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
    except OSError:
        font = ImageFont.load_default()
    x = pad
    for i, t in thumbs:
        d.text((x + 4, pad + 2), str(i), fill="#111111", font=font)
        sheet.paste(t, (x, pad + label_h))
        x += thumb_w + pad
    out = root / paths.SHEETS / f"{aid}.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=85)
    return out


def source_urls(root, aid, item, spec, source):
    if source == "urls":
        p = root / paths.URLS
        if not p.exists():
            raise SystemExit(
                f"{paths.URLS} not found — create it (see prompts/images.md) or use --source wikimedia"
            )
        table = json.loads(p.read_text(encoding="utf-8"))
        return table.get(aid, [])
    query = item.get("query") or item.get("name") or aid
    return search_commons(query, spec["images"]["candidates_per_attraction"] + 3, spec["images"]["min_width"])


def fetch(root, spec, source, only=None):
    items, _ = load_attractions(root)
    manifest = load_manifest(root)
    want = spec["images"]["candidates_per_attraction"]
    tmp = root / "images" / ".tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    for item in items:
        aid = item["id"]
        if only and aid != only:
            continue
        urls = source_urls(root, aid, item, spec, source)
        cdir = root / paths.CANDIDATES / aid
        if cdir.exists():
            shutil.rmtree(cdir)
        cdir.mkdir(parents=True)
        kept = []
        for url in urls:
            if len(kept) >= want:
                break
            time.sleep(0.4)
            raw = tmp / f"{aid}.raw"
            try:
                download(url, raw)
                img, err = validate_image(raw, spec)
                if err:
                    print(f"  {aid}: rejected {url} ({err})")
                    continue
                h = ahash(img)
                if any(hamming(h, x) <= 5 for _, x in kept):
                    print(f"  {aid}: near duplicate skipped")
                    continue
                dest = cdir / f"{len(kept) + 1}.jpg"
                img.convert("RGB").save(dest, "JPEG", quality=88)
                kept.append((dest, h))
            except Exception as e:  # noqa: BLE001 — one bad URL must not kill the batch
                print(f"  {aid}: failed {url} ({e})")
            finally:
                raw.unlink(missing_ok=True)
        prev = manifest.get(aid, {})
        picked = prev.get("picked")
        if picked is not None and picked not in range(1, len(kept) + 1):
            picked = None
        rels = [str(p.relative_to(root)) for p, _ in kept]
        manifest[aid] = {"candidates": rels, "picked": picked}
        if kept:
            build_sheet(root, aid, rels)
        print(f"  {aid}: {len(kept)} candidate(s)")
    shutil.rmtree(tmp, ignore_errors=True)
    save_manifest(root, manifest)
    return manifest


def report_images(root, spec):
    rep = Report("images")
    items, issues = load_attractions(root)
    rep.issues.extend(issues)
    if items is None:
        return rep
    manifest = load_manifest(root)
    have = 0
    for item in items:
        aid = item["id"]
        entry = manifest.get(aid)
        if not entry or not entry.get("candidates"):
            rep.issues.append(Issue("images", f"{aid}: no candidates — run `guide images`"))
            continue
        have += 1
        for rel in entry["candidates"]:
            if not (root / rel).exists():
                rep.issues.append(Issue("images", f"{aid}: missing candidate file {rel}"))
    rep.stats = f"{have}/{len(items)} attractions with candidates"
    return rep


def report_picks(root, spec):
    rep = Report("picks")
    items, issues = load_attractions(root)
    rep.issues.extend(issues)
    if items is None:
        return rep
    manifest = load_manifest(root)
    done = 0
    for item in items:
        aid = item["id"]
        entry = manifest.get(aid) or {}
        cands = entry.get("candidates") or []
        picked = entry.get("picked")
        if not cands:
            rep.issues.append(Issue("picks", f"{aid}: no candidates yet"))
            continue
        if picked is None:
            rep.issues.append(
                Issue("picks", f"{aid}: not picked — review {paths.SHEETS}/{aid}.jpg, set \"picked\" in {paths.MANIFEST}")
            )
        elif not isinstance(picked, int) or picked not in range(1, len(cands) + 1):
            rep.issues.append(Issue("picks", f"{aid}: picked={picked!r} invalid (1..{len(cands)})"))
        else:
            done += 1
    rep.stats = f"{done}/{len(items)} picked"
    return rep
