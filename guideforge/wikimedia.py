import requests

API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "guideforge/0.1 (open-source content tool)"}


def thumb_of(url, width):
    if "/thumb/" in url:
        return url
    path = url.split("?", 1)[0]
    name = path.rsplit("/", 1)[-1]
    return f"{path}/thumb/{width}px-{name}"


def search_commons(query, want, min_width):
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": 6,
        "gsrlimit": min(50, want * 5),
        "prop": "imageinfo",
        "iiprop": "url|size|mime",
        "iiurlwidth": 1600,
    }
    r = requests.get(API, params=params, headers=UA, timeout=(10, 25))
    r.raise_for_status()
    pages = (r.json().get("query") or {}).get("pages", {})
    ranked = sorted(pages.values(), key=lambda p: p.get("index", 999))
    out = []
    for page in ranked:
        infos = page.get("imageinfo") or []
        if not infos:
            continue
        info = infos[0]
        if info.get("mime") not in ("image/jpeg", "image/png"):
            continue
        if info.get("width", 0) < min_width:
            continue
        url = info.get("thumburl") or thumb_of(info.get("url", ""), 1600)
        if url:
            out.append(url)
        if len(out) >= want * 2:
            break
    return out
