# Spotify Library Manager 🎵

A Python CLI application to download, store, and search your Spotify library locally. Fills a shortcoming of Spotify UIs where you can't search by track name inside your library. Also adds some fun features like duplicate detection etc.

> **For Developers:** See [DEVELOPMENT.md](DEVELOPMENT.md) for setup instructions, coding standards, and contribution guidelines.

## Features

- 🔐 OAuth authentication with Spotify
- 📥 Download all your playlists and saved tracks
- 💾 Store metadata in a local JSON database (TinyDB)
- 🔍 Fast local search across tracks, artists, and albums
- 🔁 Find duplicates across playlists (ranked by occurrences)
- ⚡ Diff sync that skips unchanged playlists using `snapshot_id`
- 📊 View library statistics
- 📂 Browse playlists and tracks
- 💬 Interactive shell (run without arguments)
- 🍎 macOS quick installer and simple launcher

## Table of Contents

- [Features](#features)
- [Setup](#setup)
	- [Create Virtual Environment](#1-create-virtual-environment)
	- [Install Dependencies](#2-install-dependencies)
	- [Get Spotify API Credentials](#3-get-spotify-api-credentials)
	- [Configure the Application](#4-configure-the-application)
- [Usage](#usage)
	- [Authenticate with Spotify](#authenticate-with-spotify)
	- [Sync Your Library](#sync-your-library)
	- [Sync Differences (Faster)](#sync-differences-faster)
	- [Search for Tracks](#search-for-tracks)
	- [Find Duplicates](#find-duplicates)
	- [List Playlists](#list-playlists)
	- [View Statistics](#view-statistics)
	- [Interactive Shell (Dialog Mode)](#interactive-shell-dialog-mode)
	- [Clear Auth Cache](#clear-auth-cache)
- [Database Structure](#database-structure)
- [Project Structure](#project-structure)
- [Tips](#tips)
- [Troubleshooting](#troubleshooting)
- [Future Enhancements](#future-enhancements)
- [License](#license)

## Setup

Requires Python 3.14.

### 1. Create Virtual Environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -e .
```

### 3. Get Spotify API Credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications)
2. Log in with your Spotify account
3. Click "Create an App"
4. Fill in the app name and description
5. Once created, click on your app to view the Client ID and Client Secret
6. Click "Edit Settings" and add `http://127.0.0.1:8000/callback` to the Redirect URIs
7. Save the settings

### 4. Configure the Application

Run the setup command and enter your credentials:

```bash
spotify-search setup
```

Or manually create a `.env` file:

<!-- env-example:start -->
```env
# Spotify API Credentials
# Get these from https://developer.spotify.com/dashboard/applications
SPOTIPY_CLIENT_ID=your_client_id_here
SPOTIPY_CLIENT_SECRET=your_client_secret_here
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8000/callback
# Optional: where to store local data (default: data)
SPOTIFY_DATA_DIR=data
```
<!-- env-example:end -->

## Usage

Use the `spotify-search` command for all operations. Tip: running with no arguments launches the interactive shell automatically.

On macOS, use the [quick installer](macos_install/README.md) to set up the launcher.

### Authenticate with Spotify

```bash
spotify-search auth
```

This will open a browser window for you to authorize the application. After authorization, you'll be redirected to localhost (which may show an error page - that's okay, the auth token is captured).

### Sync Your Library


Download all your playlists and saved tracks:

```bash
spotify-search sync
```

To clear existing data and start fresh:

```bash
spotify-search sync --clear
```

#### Sync Only a Specific Playlist

You can sync just one playlist by name (case-insensitive substring match):

```bash
spotify-search sync --playlist "Discover Weekly"
```

If multiple playlists match, you'll be prompted to select one. Only the selected playlist will be synced; saved tracks and other playlists are skipped.

### Sync Differences (Faster)

Skip playlists and saved tracks that already match counts in your local DB. This is much faster for subsequent syncs.

```bash
spotify-search sync-diff
```

Notes:
- Playlists are skipped when their Spotify `snapshot_id` matches the one stored locally (robust change detection). If `snapshot_id` is missing, it falls back to comparing local relationship count to Spotify's `tracks_total`.
- Snapshot is recorded only after a playlist's tracks are fetched and saved successfully, so partial updates won't cause future skips.
- Saved tracks are skipped when local count equals Spotify's saved total.
- If you suspect a mismatch (e.g., local tracks affect totals), run a full `sync` to force refresh.

### Search for Tracks


Search across track names, artists, and albums:

```bash
spotify-search search "bohemian rhapsody"
spotify-search search "taylor swift"
spotify-search search "abbey road"
```

#### Advanced Filtering

You can filter results by track name, artist, or album using options:

```bash
spotify-search search --name "track name" --artist "artist name" --album "album name"
```

Examples:

- Search for tracks with name containing "love":
	```bash
	spotify-search search --name "love"
	```
- Search for tracks by artist "Adele":
	```bash
	spotify-search search --artist "Adele"
	```
- Search for tracks with name "Hello" by artist "Adele":
	```bash
	spotify-search search --name "Hello" --artist "Adele"
	```
- Search for tracks from album "25":
	```bash
	spotify-search search --album "25"
	```
- Search for tracks with "Christmas" in any of the 3 properties AND by artist "John williams":
	```bash
	spotify-search search "christmas" --artist "john williams"
	```

#### Limit Results

Use `--limit N` to control the number of results shown (default: 20):

```bash
spotify-search search "love" --limit 10
```

### Find Duplicates

List tracks that appear in multiple playlists, ordered by how many times they occur. Shows track info, the number of duplicates, and the playlists (with links) they’re in.

```bash
spotify-search duplicates           # top 5 by default
spotify-search duplicates --limit 10
```

### List Playlists

View all your playlists:

```bash
spotify-search list
```

View tracks in a specific playlist:

```bash
spotify-search list --playlist "Discover Weekly"
```

### View Statistics

See your library statistics:

```bash
spotify-search stats
```

### Interactive Shell (Dialog Mode)

Run a simple REPL so you don’t need to prefix each command:

```bash
# Cross-platform (Python)
python src/cli.py shell

# Or launch with no arguments (auto-shell)
python src/cli.py

# Windows launcher
spotify-search shell

# Or launch with no arguments (auto-shell)
spotify-search

# Inside the shell
spotify-search> stats
spotify-search> search "love" --limit 5
spotify-search> sync-diff
spotify-search> duplicates --limit 10
spotify-search> exit
```

### Clear Auth Cache

Remove cached Spotify OAuth tokens (useful to re-auth as a different user):

```bash
spotify-search clear-auth
spotify-search clear-auth --dry-run
```

## Commands Reference

| Command | Description |
|---------|-------------|
| `setup` | Configure Spotify API credentials |
| `auth` | Authenticate with Spotify |
| `sync` | Download and sync your entire library |
| `sync --playlist NAME` | Sync only a specific playlist by name |
| `sync-diff` | Sync only changes; skip up-to-date playlists/saved tracks |
| `search QUERY` | Search for tracks locally |
| `search QUERY --limit N` | Search for tracks with result limit |
| `search --name NAME` | Search by track name |
| `search --artist ARTIST` | Search by artist name |
| `search --album ALBUM` | Search by album name |
| `search QUERY --name N --artist A [--album AL]` | Combine multiple filters |
| `duplicates [--limit N]` | List most duplicated tracks across playlists |
| `list` | List all playlists |
| `list --playlist NAME` | Show tracks in a playlist |
| `stats` | Show library statistics |
| `clear-auth [--dry-run]` | Remove cached OAuth token files (.auth-cache*, legacy .cache*) |

## Database Structure

The application uses TinyDB (JSON-based) with the following tables:

- **tracks**: All unique tracks with metadata (name, artist, album, duration, etc.)
- **playlists**: Playlist information (name, owner, description, etc.)
- **playlist_tracks**: Many-to-many relationship between playlists and tracks
- **saved_tracks**: User's liked/saved tracks

Database file: `data/spotify_library.json` (default; configurable via `SPOTIFY_DATA_DIR`)

## Project Structure

```
spotify-search/
├── data/                   # Local data folder (created after sync)
│   └── spotify_library.json # Local database (created after sync)
├── src/
│   ├── cli.py              # CLI commands
│   ├── config.py           # Configuration management
│   ├── database.py         # Database operations
│   ├── spotify_client.py   # Spotify API wrapper
│   └── __init__.py         # Package marker
├── .env                    # Environment variables (not in git)
├── .env.example            # Example environment file
├── .gitignore              # Git ignore rules
├── pyproject.toml          # Python dependencies and project metadata
├── README.md               # This file
└── spotify-search.bat      # Windows launcher
```

## Tips

- The first sync may take a while if you have a large library
- The application caches authentication tokens in `.auth-cache` file (legacy `.cache` may exist)
- You can re-sync anytime to update your library with new tracks/playlists
- Search is performed on your local database, so it's very fast
- All data is stored locally - no external database required

## Troubleshooting

**Authentication Issues:**
- Make sure your redirect URI in Spotify Dashboard matches exactly: `http://127.0.0.1:8000/callback`
- Delete the `.auth-cache` file (or legacy `.cache`) and try authenticating again

**Sync Failures:**
- Check your internet connection
- Verify your Spotify credentials are correct
- Local tracks in your playlists will be included but cannot be played via Spotify API

**Search Not Working:**
- Make sure you've run `sync` at least once
- Check that `data/spotify_library.json` exists and has data

## Future Enhancements

Possible features to add:
- Export playlists to CSV/Excel
- Create new playlists from search results
- Audio features analysis (tempo, energy, etc.)
- Playlist comparison tools
- Web interface

## License

MIT License. See `LICENSE`.
