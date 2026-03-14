# Getting Started

## Run From Source

From the repository root:

```bash
python3 -m memtrain --help
python3 -m memtrain animals.csv
python3 -m memtrain.gui
```

`python3 -m memtrain` starts the CLI.

`python3 -m memtrain.gui` starts the GUI.

## macOS GUI Note

If `python3 -m memtrain.gui` aborts immediately on macOS with a message about the OS version, your Apple Command Line Tools Python is linked against the legacy system Tk 8.5 framework.

In that case:

- The CLI still works: `python3 -m memtrain animals.csv`
- For the GUI, use a Python from python.org or a Homebrew Python with a working Tk install

## Install Local Entry Points

Install the project locally:

```bash
python3 -m pip install . --no-build-isolation
```

Then you can run:

```bash
memtrain animals.csv
memtrain-gui
```

## Notes

- Run commands from the repository root while developing from source.
- On older macOS system Python builds, `--no-build-isolation` avoids pip trying to create a newer isolated build environment first.
- The GUI opens a file picker, so it does not need a CSV path on the command line.
- Learner progress is stored in a local `.memtrain-progress.sqlite3` file next to the CSV unless `MEMTRAIN_PROGRESS_DB` is set.
