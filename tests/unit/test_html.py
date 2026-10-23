from guideforge.checks import html
from guideforge.spec import load_spec


def test_html_ok(project):
    rep = html.check(project, load_spec(project))
    assert rep.ok
    assert "1 image refs" in rep.stats


def test_html_class_attribute(tmp_path, make_project):
    root = make_project(
        tmp_path / "p",
        html='<html><head><title>T</title></head><body><div class="a"><img src="images/alpha.jpg"></div></body></html>',
    )
    rep = html.check(root, load_spec(root))
    assert not rep.ok
    assert any("class" in i.message for i in rep.issues)


def test_html_style_tag(tmp_path, make_project):
    root = make_project(
        tmp_path / "p",
        html='<html><head><title>T</title><style>body{}</style></head><body></body></html>',
    )
    rep = html.check(root, load_spec(root))
    assert not rep.ok
    assert any("<style>" in i.message for i in rep.issues)


def test_html_unmanaged_src(tmp_path, make_project):
    root = make_project(
        tmp_path / "p",
        html='<html><head><title>T</title></head><body><img src="assets/pic.jpg"></body></html>',
    )
    rep = html.check(root, load_spec(root))
    assert not rep.ok
    assert any("unmanaged image src" in i.message for i in rep.issues)


def test_html_remote_src_allowed(tmp_path, make_project):
    root = make_project(
        tmp_path / "p",
        html='<html><head><title>T</title></head><body><img src="https://example.com/x.jpg"></body></html>',
    )
    rep = html.check(root, load_spec(root))
    assert rep.ok


def test_html_missing_title(tmp_path, make_project):
    root = make_project(tmp_path / "p", html="<html><body></body></html>")
    rep = html.check(root, load_spec(root))
    assert not rep.ok
    assert any("<title>" in i.message for i in rep.issues)
