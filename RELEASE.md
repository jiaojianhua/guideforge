# Release runbook (maintainer)

One-time setup, then every release is a tag.

## 1. GitHub (once)

```bash
ssh-keygen -t ed25519 -C "you@example.com"        # if no key yet
cat ~/.ssh/id_ed25519.pub                          # paste into:
# github.com -> Settings -> SSH and GPG keys -> New SSH key
```

Create an empty public repo at github.com/new named `guideforge`
(no README/license — this repo already has them), then:

```bash
git remote add origin git@github.com:<your-user>/guideforge.git
git push -u origin main
```

## 2. PyPI trusted publishing (once, zero tokens)

- Register at pypi.org (verify email).
- pypi.org -> Account settings -> Publishing -> Add a new pending publisher:
  - PyPI project name: `guideforge`
  - Owner: `<your-github-user>`  Repository: `guideforge`
  - Workflow name: `pypi`  Environment: leave empty
- (Optional dry run) do the same on test.pypi.org and push a `testv*` tag.

## 3. Every release

```bash
# bump version in pyproject.toml first
git commit -am "release 0.1.1" && git tag v0.1.1 && git push --follow-tags
```

The `pypi` workflow builds sdist+wheel and uploads via OIDC — no API token
is ever stored. Verify at pypi.org/project/guideforge, then confirm the
public path works: `pip install -U guideforge && guide --help`.

## Checklist before tagging

- [ ] `pytest -q` green
- [ ] `ruff check guideforge tests` clean
- [ ] version bumped in `pyproject.toml`
- [ ] README install section already points at PyPI (it does)
