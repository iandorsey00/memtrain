# memtrain

memtrain is a lightweight study tool for structured recall practice.

It is designed for small-to-medium study sets where prompt wording matters: fill-in-the-blank cues, accepted synonyms, hints, tags, and staged recall from multiple choice to free response. Instead of trying to be a full flashcard ecosystem, memtrain focuses on authored prompts and simple adaptive review.

## What memtrain is for

- studying terminology, certification material, taxonomies, commands, and other structured factual recall
- practicing the same concept at different difficulty levels
- building study sets quickly in CSV instead of managing a larger flashcard system
- running short sessions in the terminal or a small desktop GUI

## What memtrain is not

- a full Anki replacement
- a sync-heavy or plugin-heavy study platform
- a rich multimedia course builder

## Current capabilities

- CSV-authored study sets
- adaptive sessions with persistent local learner progress
- fixed-level sessions for Level 1, Level 2, or Level 3 review
- multiple accepted answers via synonyms
- hints
- tags for session filtering
- `mtag` support for better multiple-choice distractors
- CLI and Tk GUI entry points

## Run memtrain

From the repository root:

```bash
python3 -m memtrain --help
python3 -m memtrain animals.csv
python3 -m memtrain.gui
```

Installed commands:

```bash
python3 -m pip install . --no-build-isolation
memtrain animals.csv
memtrain-gui
```

## Tests

```bash
python3 -m unittest discover -s tests
```

## Docs

- [Getting Started](docs/getting-started.md)
- [Project Overview](docs/overview.md)
- [Study Set Format](docs/study-set-format.md)
- [Release Process](docs/release-process.md)
- [0.5.0 Roadmap](docs/roadmap-0.5.0.md)
- [Changelog](CHANGELOG.md)

## macOS note

On newer macOS releases, the Apple Command Line Tools `python3` may be linked to legacy Tk 8.5 and abort before the GUI opens. If that happens, the CLI will still work, but the GUI should be run with a Python from python.org or Homebrew.

## Documentation direction

The repository docs in `/docs` are the canonical documentation for the project. The old wiki has been superseded by these pages.
