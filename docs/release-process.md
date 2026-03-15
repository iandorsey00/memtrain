# Release Process

This is a lightweight release checklist for memtrain.

## Before release

1. Run the automated tests:

```bash
python3 -m unittest discover -s tests
```

2. If available in your environment, run the quality checks:

```bash
ruff check memtrain tests
black --check memtrain tests
```

3. Do a quick manual smoke test:

- CLI adaptive session
- CLI fixed-level session
- GUI launch
- GUI adaptive session
- GUI fixed-level session

4. Review docs for any user-facing behavior changes.

5. Update:

- `memtrain/__init__.py`
- `setup.py`
- any visible version string in the GUI
- `CHANGELOG.md`

## Tagging

After the release commit lands on `master`:

```bash
git tag 0.4.2
git push origin 0.4.2
```

Replace `0.4.2` with the actual release version.

## Release principles

- Prefer small, coherent releases.
- Keep docs and version bumps in the same release cycle as user-facing changes.
- Treat `/docs` and `CHANGELOG.md` as the canonical release record.
