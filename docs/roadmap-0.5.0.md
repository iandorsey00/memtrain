# 0.5.0 Roadmap

This is a direction document, not a commitment.

The goal of `0.5.0` would be to sharpen memtrain as a polished structured-recall trainer without trying to turn it into a general-purpose flashcard platform.

## Theme

Stabilize the adaptive learning loop and make the product easier to understand and maintain.

## Likely focus areas

### 1. Better learner feedback

- clearer end-of-session summaries
- stronger visibility into weak, improving, and mature items
- lightweight progress views by tag or study set

### 2. Better study-set authoring support

- a stronger documented CSV format
- more example CSVs
- better validation and error messages for malformed files

### 3. Stronger test coverage

- more core-engine coverage
- CSV edge-case coverage
- persistence and progression regression tests

### 4. Internal maintainability

- more typing in the core engine
- cleaner item/progress models
- continued cleanup of legacy internal module names when low-risk

## Not planned for 0.5.0

- mobile apps
- cloud sync
- deck marketplace
- plugin system
- full Anki feature parity
- GUI framework replacement

## Success criteria

`0.5.0` would feel successful if:

- the product story is easy to explain
- the docs are self-contained in the repository
- the adaptive loop feels stable and intentional
- contributor-facing code is easier to change safely
- new regressions are caught earlier by tests
