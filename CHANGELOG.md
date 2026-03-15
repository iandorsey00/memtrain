# Changelog

All notable changes to this project should be documented in this file.

The format is intentionally lightweight and release-oriented.

## [0.4.2] - 2026-03-14

### Changed

- Refactored the adaptive engine to use typed dataclasses for session items and progress records.
- Improved core maintainability around progress handling and engine data flow.
- Added `ruff` and `black` configuration plus CI checks for lint, format, and tests.

## [0.4.1] - 2026-03-14

### Changed

- Modernized the Tk GUI with a cleaner macOS-friendly `ttk` interface.
- Added stable package/module entry points for CLI and GUI execution.
- Improved macOS GUI runtime handling and documentation.
- Reworked repository documentation and moved canonical docs into `/docs`.

## [0.4.0] - 2026-03-14

### Added

- Adaptive study sessions with persistent local learner progress.

### Changed

- Added adaptive stage progression on top of the original fixed-level model.
- Updated CLI and GUI flows to work with adaptive sessions.

## Notes

- `0.5.0` is planned as a direction milestone, not an active implementation target.
