# memtrain
A program for better and less frustrating memorization

![memtrain screenshot](https://raw.githubusercontent.com/iandorsey00/memtrain/master/docs/img/memtrain-screenshot.png "memtrain screenshot")

## Running memtrain

From the repository root:

```bash
python3 -m memtrain --help
python3 -m memtrain animals.csv
python3 -m memtrain.gui
```

On newer macOS releases, the Apple Command Line Tools `python3` may be linked to legacy Tk 8.5 and abort before the GUI opens. If that happens, use the CLI with that Python or run the GUI with a Python from python.org or Homebrew instead.

If you want installable commands:

```bash
python3 -m pip install . --no-build-isolation
memtrain animals.csv
memtrain-gui
```

More setup and usage notes are in [docs/getting-started.md](docs/getting-started.md).

## Tests

Run the core regression tests with the built-in test runner:

```bash
python3 -m unittest discover -s tests
```
