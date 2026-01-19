# FastAPI Web Conversion Plan

## Purpose

Build a simple website around the existing Spotify library CLI. The site will
support:

- Login with Spotify (OAuth)
- Init (sync the local library database)
- Search with results that include song URLs

The CLI should remain intact. The web app will reuse the current data model and
storage.

## Current State Summary

- CLI entrypoint: `src/cli.py`
- Spotify API wrapper: `src/spotify_client.py` (Spotipy + OAuth cache file)
- Storage: `src/database.py` (TinyDB JSON in `spotify_library.json`)
- Config: `src/config.py` loads `.env` and defines the redirect URI

## Goals

- Web UI with three primary flows: login, init (sync), search
- FastAPI backend
- HTML templates with minimal JS and CSS (no frontend framework)
- Reuse existing DB schema and SpotifyClient logic where possible

## Non-Goals (Initial Release)

- Multi-user support or hosted SaaS deployment
- Editing playlists or saved tracks
- Advanced stats, duplicates, or CLI parity beyond search and sync
- Background job queue or distributed workers

## Proposed Architecture

### High-Level Flow

1. User visits home page.
2. If not authenticated, user clicks "Login with Spotify".
3. OAuth callback stores token cache and marks user as logged in.
4. User clicks "Init" to sync library into TinyDB.
5. User runs searches that read from TinyDB and show results with song URLs.

### Backend Structure

Add a FastAPI app, plus small helper modules:

- `src/web_app.py` (FastAPI app, routes, dependency wiring)
- `src/web_auth.py` (Spotify OAuth helpers and session handling)
- `src/web_sync.py` (sync orchestration and progress state)
- `src/web_templates/` (Jinja2 templates)
- `src/web_static/` (CSS, optional JS)

This keeps web code isolated from the CLI, while reusing `SpotifyClient` and
`SpotifyDatabase`.

### Dependency Additions

Add to `pyproject.toml`:

- `fastapi`
- `uvicorn`
- `jinja2`
- `python-multipart` (for HTML form handling)

Optional for later:

- `itsdangerous` (if session signing is needed explicitly)
- `httpx` (only if testing external calls directly)

## OAuth and Session Plan

### Single-User Assumption

Initial web mode assumes a single local user (like the CLI). Tokens can be
stored in the Spotipy cache file (`.auth-cache`). This avoids building a full
user database or session store.

### OAuth Mechanics

- Use `SpotifyOAuth` to generate the authorize URL.
- Handle `/callback` to exchange code for token.
- Store tokens in `.auth-cache` via Spotipy cache handler.
- Maintain a lightweight session cookie to indicate "logged in" state.

### Config

Use the existing `.env` keys:

- `SPOTIPY_CLIENT_ID`
- `SPOTIPY_CLIENT_SECRET`
- `SPOTIPY_REDIRECT_URI` (set to `http://127.0.0.1:8000/callback` for local)

Add a new env for the web app:

- `APP_SECRET_KEY` for session signing

## API and Page Design

### Pages (HTML)

- `GET /`
  - Shows login status
  - Links to Init and Search

- `GET /init`
  - Simple page with "Sync library" button
  - Optional "Clear existing data" checkbox
  - Shows sync status

- `GET /search`
  - Search form (query, name, artist, album, limit)
  - Results list with external URLs

### API Endpoints (JSON)

- `POST /api/init`
  - Starts sync in background
  - Returns status payload (started, already running, error)

- `GET /api/status`
  - Returns current sync status and last run metadata

- `GET /api/search`
  - Query params mirror CLI search flags
  - Returns JSON list with fields: name, artist, album, external_url, duration

### Auth Routes

- `GET /login` -> redirect to Spotify authorize URL
- `GET /callback` -> OAuth completion and redirect to home
- `POST /logout` -> clear auth cache and session

## Sync Implementation Plan

### Reuse CLI Logic

Extract sync logic from `src/cli.py` into a shared helper so both CLI and web
can call it. The CLI wrappers remain unchanged, but call the shared function.

Proposed approach:

- Create `src/sync_service.py` with a `sync_library()` function
- Move shared logic from CLI `sync` and `sync_diff`
- Web `init` calls the shared function

### Background Execution

Sync can be slow. Use a background task that:

- runs `sync_library()`
- updates an in-memory `sync_state` dict
- prevents concurrent runs

Status fields:

- `state`: idle, running, success, error
- `started_at`, `finished_at`
- `error_message`
- `progress` (optional, coarse-grained)

## Search Implementation Plan

### Query Options

Support the same query structure as the CLI:

- general query
- name-only, artist-only, album-only
- combination query + filters
- limit parameter

### Result Payload

Return fields used by the UI:

- name
- artist
- album
- duration_ms (formatted in UI)
- external_url (Spotify track URL)
- is_local (optional, for display warnings)

## Data Model and Storage

- Keep `spotify_library.json` as the DB file by default.
- Optional: add `SPOTIFY_DB_PATH` env override later if needed.
- Ensure database connections are closed after requests.

## Testing Plan

### Unit Tests

- Web routes return expected status codes.
- Search endpoint returns filtered results from a temp TinyDB file.
- Sync endpoint rejects when not authenticated.

### Mocking Strategy

- Mock `SpotifyClient` to avoid network calls.
- Use a temp DB path for tests (TinyDB file in `tmp_path`).

### Manual Smoke Tests

1. Start server: `uvicorn src.web_app:app --reload`
2. Login with Spotify.
3. Run Init and confirm DB file updates.
4. Search and validate URLs open in Spotify.

## Risks and Mitigations

- OAuth redirect mismatch
  - Document required redirect URI and validate on startup.
- Long-running sync blocks UI
  - Run sync in background and show status.
- Concurrent sync or search during sync
  - Use a "sync in progress" flag and lock the DB while syncing.
- Token cache corruption
  - Provide logout endpoint to clear cache and re-auth.

## Milestones and Tasks

### Phase 1: Foundation

- Add FastAPI dependencies
- Create `src/web_app.py` with basic routing
- Add templates for home, init, search
- Wire static CSS for simple UI

### Phase 2: Auth

- Implement `/login` and `/callback`
- Store auth status in session
- Add logout flow

### Phase 3: Sync

- Extract shared sync logic to `src/sync_service.py`
- Implement background sync and status endpoint
- Add init page UX around sync status

### Phase 4: Search

- Implement `/api/search` and UI results
- Format duration and include external URLs

### Phase 5: Tests and Docs

- Add pytest coverage for web routes
- Update `README.md` with web usage and env setup

## Acceptance Criteria

- Web app starts with `uvicorn src.web_app:app`.
- Login flow completes and sets auth state.
- Init triggers a library sync and updates the TinyDB file.
- Search returns tracks from the local DB and displays Spotify URLs.

## Open Questions

- Should the web UI support `sync_diff` or only full sync?
- Should the web UI expose playlist listing or stats in v1?
- Do we want to allow search before init (with a warning)?
