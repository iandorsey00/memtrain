# Project Overview

## Positioning

memtrain is a study tool for structured recall training.

Its strength is not generic front/back flashcards. Its strength is authored prompts with deliberate cue wording, accepted alternate answers, hints, tags, and a progression path from recognition to recall.

That makes it a good complement to larger flashcard systems and, for some kinds of study, a better fit than generic cards.

## Learning Model

memtrain supports two session styles:

- Adaptive sessions: the app chooses prompt difficulty item by item based on stored progress.
- Fixed-level sessions: the whole session stays at one level selected by the user.

The current adaptive model uses persistent local progress to track:

- current stage
- mastery score
- streaks and failures
- average response time
- next due time

## Recall Levels

- Level 1: multiple choice
- Level 2: hint-assisted recall
- Level 3: free recall

In adaptive mode, items can move between these levels as the learner improves or struggles.

## Best-fit Use Cases

- certification prep such as CompTIA A+
- language and vocabulary drilling
- taxonomy/category memorization
- command and acronym recall
- hardware, protocol, and terminology review

## Non-Goals

memtrain is intentionally not trying to be:

- a full Anki clone
- a community deck platform
- a multimedia-rich study suite
- a cross-device sync system

## Architecture

At a high level the project is split into:

- shared core logic in `memtrain/memtrain_common`
- a CLI entry point
- a Tk GUI entry point

The core engine is responsible for:

- reading the CSV study set
- building in-memory study content
- loading and saving learner progress
- assembling manual or adaptive sessions

## Persistence

Learner progress is stored locally in a SQLite file named `.memtrain-progress.sqlite3` next to the study CSV by default.

You can override the location with the `MEMTRAIN_PROGRESS_DB` environment variable.
