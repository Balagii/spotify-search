# Repo Stabilization Plan

This document captures the current assessment, prioritized technical debt, and
well-defined tasks for small agents. The goal is to stabilize the repo before
new feature work starts.

## Assessment (Current State)

- Python 3.14 is pinned across CI, tooling, and docs; verify every tool and
  workflow supports it consistently.
- Formatting/linting is simplified but still needs CI verification.
- Local `pre-commit` runs include pytest and a staged-clean check; hooks run in
  pre-commit-managed envs, so venv activation is not required. Last reported
  coverage is ~55% after adding unit tests for DB/CLI/client behavior.

## Owner Preferences (Captured)

- Use Python 3.14 only (no version matrix).
- Prefer simple tooling: pre-commit formatting/linting/tests with minimal overlap.
- Prefer simple CI; consolidate linting where possible.
- Unify venv naming if safe (avoid platform-specific venvs unless required).
- Low-effort cleanup tasks can be prioritized.

## Prioritized Technical Debt Backlog

| ID | Priority | Item | Rationale |
| --- | --- | --- | --- |
| TD-001 | P0 | Lock to Python 3.14 everywhere | Ensure CI/tooling/docs are consistent. |
| TD-002 | P0 | Restore CI to green | Required to stabilize before feature work. |
| TD-004 | P2 | Add core unit tests | Needed to prevent regressions. |
| TD-005 | P3 | Evaluate package layout (`src` package) | Optional refactor for standard structure. |

## Agent Task Breakdown

### AG-001: Align Supported Python Version (P0)

Goal: Use Python 3.14 everywhere across CI, devcontainer, tooling, and docs.

Scope:
- Update `pyproject.toml` (requires-python, Black target, mypy version).
- Update `.github/workflows/ci.yml` and remove redundant lint workflows.
- Update `.devcontainer/devcontainer.json`.
- Update `.pre-commit-config.yaml` (Black language_version).
- Update docs (`DEVELOPMENT.md`, README if needed).

Acceptance Criteria:
- CI uses the same Python version as local tooling.
- `pip install -e ".[dev]"` succeeds on the target version.
- Docs explicitly state the supported version.

Dependencies: None.

### AG-002: Restore CI to Green (P0)

Goal: Make CI pass consistently.

Scope:
- Run `pre-commit run --all-files` and `pytest` locally.
- Fix lint errors or tune configs only when justified.
- Validate `pytest` and coverage outputs.

Acceptance Criteria:
- Both GitHub Actions workflows pass without manual reruns.
- Lint and test results are reproducible locally.

Dependencies: AG-001.

### AG-004: Add Core Unit Tests (P2)

Goal: Add tests for key behavior without real Spotify API calls.

Scope:
- `SpotifyDatabase` tests (search, duplicates, playlist relationships).
- `SpotifyClient` tests using mocks for Spotipy calls.
- CLI command tests for routing and error handling (mocked).

Acceptance Criteria:
- Tests run without network access.
- Coverage meaningfully exceeds smoke-only baseline.

Dependencies: AG-002.

### AG-005: Package Layout Review (P3)

Goal: Move toward a standard Python package layout if desired.

Scope:
- Decide between keeping `src` as the package or renaming to
  `spotify_search`.
- Update `pyproject.toml` and import paths if the refactor is approved.

Acceptance Criteria:
- Packaging and imports are consistent across the repo.

Dependencies: AG-002.

## Completed This Pass

- Fixed Copilot instruction paths in `.github/settings.json`.
- Added `LICENSE` and updated README license text.
- Standardized venv naming to `.venv` and removed `.venv-win11` usage.
- Removed `src/main.py` (unused venv creation side effects).
- Simplified formatting pipeline (Black + isort) and removed pylint workflow.
- Added unit tests for database, CLI, client paging, and sync-diff behavior.
- Last reported: ran `pre-commit` and `pytest` locally; coverage ~55%.

## Medium-Long Term Plan

- Phase 0 (Stabilize CI): AG-001, AG-002.
- Phase 2 (Core Tests): AG-004.
- Phase 3 (Hygiene + Refactors): AG-005.

## Definition of Done (Stabilization)

- CI passes on the supported Python version without manual fixes.
- Local `make` commands mirror CI behavior.
- Tests cover core logic without network access.
- Documentation reflects the actual workflow and tooling.
