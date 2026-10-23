from PIL import Image

from guideforge.images import ahash, hamming, validate_batch, validate_image
from guideforge.spec import DEFAULT_SPEC


def pattern(path, cells, size=(1200, 1000)):
    Image.frombytes("L", (8, 8), bytes(cells)).resize(size, Image.NEAREST).save(path)


def test_validate_image_ok(tmp_path):
    p = tmp_path / "ok.png"
    Image.new("RGB", (1000, 700), "red").save(p)
    img, err = validate_image(p, DEFAULT_SPEC)
    assert err is None
    assert img.size == (1000, 700)


def test_validate_image_too_small(tmp_path):
    p = tmp_path / "small.png"
    Image.new("RGB", (400, 300), "red").save(p)
    _, err = validate_image(p, DEFAULT_SPEC)
    assert err and "too small" in err


def test_validate_image_aspect(tmp_path):
    p = tmp_path / "wide.png"
    Image.new("RGB", (1600, 600), "red").save(p)
    _, err = validate_image(p, DEFAULT_SPEC)
    assert err and "aspect" in err

    p2 = tmp_path / "square.png"
    Image.new("RGB", (800, 800), "red").save(p2)
    _, err2 = validate_image(p2, DEFAULT_SPEC)
    assert err2 and "aspect" in err2


def test_validate_image_format(tmp_path):
    p = tmp_path / "x.bmp"
    Image.new("RGB", (1600, 900), "red").save(p)
    _, err = validate_image(p, DEFAULT_SPEC)
    assert err and "format" in err


def test_ahash_near_duplicate_distance(tmp_path):
    base = [0, 255] * 32
    changed = list(base)
    changed[0] = 200
    a = tmp_path / "a.png"
    b = tmp_path / "b.png"
    pattern(a, base)
    pattern(b, changed)
    d = hamming(ahash(Image.open(a)), ahash(Image.open(b)))
    assert 1 <= d <= 5


def test_validate_batch_dedup(tmp_path):
    base = [0, 255] * 32
    a = tmp_path / "a.png"
    b = tmp_path / "b.png"
    c = tmp_path / "c.jpg"
    pattern(a, base)
    pattern(b, base)
    pattern(c, base)
    kept, rejected = validate_batch([a, b, c], DEFAULT_SPEC)
    assert len(kept) == 1
    assert len(rejected) == 2
    reasons = [r for _, r in rejected]
    assert "exact duplicate" in reasons or "near duplicate" in reasons


def test_validate_batch_keeps_distinct(tmp_path):
    a = tmp_path / "a.png"
    b = tmp_path / "b.png"
    pattern(a, [0, 255] * 32)
    pattern(b, [255, 0] * 32)
    kept, rejected = validate_batch([a, b], DEFAULT_SPEC)
    assert len(kept) == 2
    assert not rejected
