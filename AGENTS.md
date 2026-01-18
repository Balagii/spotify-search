# Agent Notes

This file provides shared context for AI agents working in this repository. It
focuses on architecture, workflows, and pitfalls so small tasks can be executed
consistently.

## Repo Overview

- CLI entrypoint: `src/cli.py` (Click commands and user-facing output).
- Spotify API wrapper: `src/spotify_client.py` (Spotipy + OAuth).
- Local storage: `src/database.py` (TinyDB JSON tables).
- Configuration: `src/config.py` (loads `.env`, defines DB path).
- Local data file: `spotify_library.json` in repo root.

## Common Commands

```bash
make setup
make format
make lint
make type-check
make test
make pre-commit
```

CLI usage (after install or via `python`):

```bash
spotify-search --help
python src/cli.py --help
```

## Data Flow (High Level)

- `sync`: fetch saved tracks + playlists, store track metadata and relationships.
- `sync-diff`: skip playlists using `snapshot_id` or track counts.
- `duplicates`: counts track occurrences from playlist relationships.

## Local State and Secrets

- `.env` stores Spotify API credentials.
- `.auth-cache*` stores OAuth tokens (Spotipy cache).
- `spotify_library.json` stores the TinyDB data.

Do not commit these files.

## Testing Guidance

- Avoid network calls in tests; mock `SpotifyClient` or Spotipy.
- Use `tmp_path` for TinyDB file tests to avoid touching real data.
- Pre-commit runs pytest and a staged-clean check; on failure follow the printed
  command (formatting: `pre-commit run --all-files`, tests: `python -m pytest`).
  Hooks run in pre-commit-managed envs; venv activation is not required.
- Coverage was last reported at ~55% after adding unit tests. See `PLANNING.md`
  for remaining backlog.

## Conventions

- Formatting and linting: Black + isort + flake8, 88-char line length.
- Use type hints and docstrings for public functions.
- Keep API calls in `src/spotify_client.py` and storage logic in `src/database.py`.

## Known Gaps

- CI is green; remaining work is the post-stabilization plan in `PLANNING.md`.
- E2E tests are not yet implemented and will require GitHub secrets.
- Tooling drift exists between `Makefile` and pre-commit configuration.
