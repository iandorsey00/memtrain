# HANDOFF

## Project state

memtrain is in a stable `0.4.2` state and is intentionally at a stopping point for now.

Recent work completed:

- adaptive sessions with persistent local progress
- CLI and GUI entry-point cleanup
- macOS GUI runtime guard for unsupported Apple CLT Tk setups
- Tk GUI modernization with `ttk`
- repo-native documentation in `/docs`
- regression tests for core engine behavior
- typed/dataclass-backed engine models
- CI for lint, format, and tests
- release docs and changelog

## Current version

- `memtrain/__init__.py`: `0.4.2`
- `setup.py`: `0.4.2`

## Main commands

From the repo root:

```bash
python3 -m memtrain animals.csv
python3 -m memtrain.gui
python3 -m unittest discover -s tests
ruff check memtrain tests
black --check memtrain tests
```

Installable commands:

```bash
python3 -m pip install . --no-build-isolation
memtrain animals.csv
memtrain-gui
```

## Important docs

- `README.md`
- `CHANGELOG.md`
- `docs/getting-started.md`
- `docs/overview.md`
- `docs/study-set-format.md`
- `docs/release-process.md`
- `docs/roadmap-0.5.0.md`

## Testing and quality baseline

Local checks expected to pass:

```bash
python3 -m unittest discover -s tests
ruff check memtrain tests
black --check memtrain tests
```

GitHub Actions workflow:

- `.github/workflows/tests.yml`

It runs:

- `ruff`
- `black --check`
- `unittest`

## Packaging / runtime notes

- The GUI should be launched with `python3 -m memtrain.gui`, not `python3 memtrain_gui`.
- On newer macOS releases, Apple Command Line Tools Python may link against legacy Tk 8.5 and abort before opening a window.
- `memtrain/gui.py` detects that unsupported runtime and prints a helpful message instead.
- The CLI still works with the Apple CLT Python.

## Persistence

- learner progress is stored by default in `.memtrain-progress.sqlite3` next to the study CSV
- override with `MEMTRAIN_PROGRESS_DB`

## Known non-urgent follow-ups

These are optional polish items, not urgent stabilization work:

- add a light `mypy` pass for core modules and wire it into CI
- expand test coverage beyond the current engine/persistence smoke cases
- split `memtrain/memtrain_gui/__main__.py` into smaller modules if GUI work resumes
- add stronger example CSV study sets
- tag releases after version bumps using the release process doc

## Recommended posture

Treat the project as done for now unless one of these happens:

- a real user-facing bug appears
- `0.5.0` work is intentionally resumed
- quality work resumes specifically for `mypy`, broader tests, or GUI modularization

The project does not currently need more cleanup for cleanup's sake.
