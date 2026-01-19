# Quality Roadmap (Post-Stabilization)

This plan replaces the stabilization checklist now that CI is green. The focus
is golden-path E2E coverage plus targeted unit test growth without over-testing.

## Current Baseline

- CI is green on Python 3.14; pre-commit runs in managed envs.
- Unit coverage is ~55%; there are no E2E tests yet.
- Documentation reflects current workflows and tooling.

## Goals (Next Phase)

- Add a small set of read-only E2E tests for CLI golden paths using a real
  Spotify test account.
- Increase unit coverage to ~80% without brittle or excessive tests.
- Keep CI simple; E2E runs only when secrets are available.

## Decisions / Constraints

- Python 3.14 only.
- E2E tests must be read-only and idempotent.
- No PR-only enforcement for now; run on push.
- Pre-commit runs unit tests only (no E2E).

## Prioritized Backlog

| ID | Priority | Item | Outcome |
| --- | --- | --- | --- |
| QP-001 | P0 | CI auth bootstrap | Non-interactive Spotify auth in CI. |
| QP-002 | P0 | Configurable DB path | E2E tests avoid touching real data file. |
| QP-003 | P1 | Golden-path E2E tests | CLI works end-to-end against real account. |
| QP-004 | P2 | Unit coverage bump | Reach ~80% with focused tests. |
| QP-005 | P2 | CI test split | E2E gated by secrets/marker. |
| QP-006 | P2 | Tooling drift alignment | Make Makefile + pre-commit consistent. |

## Agent Tasks

### QP-001: CI Auth Bootstrap (P0)

Goal: run Spotify OAuth in CI without manual login.

Scope:
- Create a dedicated test Spotify account + app.
- Generate `.auth-cache` locally and store it as a GH secret (base64).
- Add CI steps to write `.auth-cache` and set:
  `SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET`, `SPOTIPY_REDIRECT_URI`.
- Document how to refresh the cache.

Acceptance:
- `SpotifyClient()` works in CI without interactive auth.
- Secrets are referenced only in CI and never committed.

Dependencies: None.

### QP-002: Configurable DB Path (P0)

Goal: allow tests to write to a temp DB file.

Scope:
- Add env override for DB path (e.g., `SPOTIFY_DATA_DIR`) in `src/config.py`.
- Update tests/CLI usage to respect the override.
- Document the override in `DEVELOPMENT.md`.

Acceptance:
- E2E tests can point DB to a temp location.
- Default behavior unchanged for users.

Dependencies: None.

### QP-003: Golden-path E2E Tests (P1)

Goal: verify core CLI flows with real data.

Scope:
- Add pytest marker `e2e`.
- Implement 2-3 tests:
  - `spotify-search sync` populates DB.
  - `spotify-search duplicates` returns output without error.
  - `spotify-search sync-diff` runs without error.
- Use the temp DB path override.
- Skip tests if secrets are missing.

Acceptance:
- Tests are read-only, deterministic, and pass in CI.
- Skipped locally unless secrets are provided.

Dependencies: QP-001, QP-002.

### QP-004: Unit Coverage Bump (P2)

Goal: raise coverage to ~80% without brittle tests.

Scope:
- Add tests for `src/config.py` validation.
- Add tests for CLI error paths and output formatting.
- Add targeted DB edge cases (empty tables, missing fields).

Acceptance:
- Coverage >= 80%.
- No new network calls.

Dependencies: None.

### QP-005: CI Test Split (P2)

Goal: keep pre-commit fast and CI reliable.

Scope:
- Update pre-commit pytest entry to run `-m "not e2e"`.
- Update CI to run unit tests and then E2E when secrets are present.

Acceptance:
- Pre-commit remains fast.
- E2E runs only on push with secrets.

Dependencies: QP-003.

### QP-006: Tooling Drift Alignment (P2)

Goal: eliminate “passes in one place, fails in another” between Makefile and
pre-commit.

Notes / Options:
- Option A (preferred): Make pre-commit the source of truth.
  - Update `make format/lint/type-check` to call
    `pre-commit run ... --all-files`.
  - Pros: exact parity with pre-commit/CI; less config drift.
  - Cons: first run slower due to hook env creation.
- Option B: Keep direct tool invocations but align scope/config.
  - Ensure flake8 reads config (add `.flake8` or `flake8-pyproject`).
  - Makefile targets all relevant code (`src/`, `tests/`, `scripts/`).
  - Remove duplicate CLI args if config is centralized.
  - Pros: faster once configured; familiar commands.
  - Cons: more moving parts; easier to drift again.

Implications:
- Expanding scope to `tests/`/`scripts/` may surface new lint issues.
- Changing lint config may require small style fixes.
- Docs should reflect whichever option is chosen.

Acceptance:
- `make` targets and `pre-commit` yield the same results on the same files.
- CI matches local behavior.

Dependencies: None.

## Definition of Done (This Phase)

- E2E golden-path tests run in CI with secrets and skip safely without them.
- Unit coverage >= 80% and unit tests have no network access.
- Docs explain how to refresh secrets and run E2E locally.
