# Release checklist

Use this list before opening the repo for external review or telling Hermes users to add the tap.

## 1. Repository metadata

- [ ] `README.md` matches the currently tracked skills and honest support scope.
- [ ] `LICENSE` is present.
- [ ] `pyproject.toml` metadata still matches the intended release owner/version.
- [ ] `.gitignore` excludes local build, cache, and virtualenv artifacts.

## 2. Skill review

- [ ] Every tracked `skills/*/SKILL.md` has frontmatter, requirements, examples, and pitfalls.
- [ ] The README install paths match the actual tracked skill directories.
- [ ] New skills are not advertised until their docs/tests land in the same release.

## 3. Local verification

Preferred commands from the repo root:

```bash
python3 -m compileall maton_http.py skills tests
.venv/bin/pytest --collect-only
.venv/bin/pytest -q
.venv/bin/ruff check .
uv build --sdist --wheel
```

If `.venv` is missing, create one and install the dev extra or equivalent tooling first.

## 4. Packaging checks

- [ ] `uv build --sdist --wheel` succeeds.
- [ ] The source distribution contains `skills/`, `docs/`, `tests/`, and `maton_http.py`.
- [ ] The wheel contains the shared `maton_http` module and metadata.
- [ ] Temporary build outputs (`build/`, `dist/`, `*.egg-info/`) are cleaned before commit if they were generated locally.

## 5. Publish handoff

- [ ] A git remote is configured before claiming push/publish status.
- [ ] The final review note includes exact verification commands and real output summaries.
- [ ] Any still-unmerged skill work is called out explicitly instead of being implied as released.
