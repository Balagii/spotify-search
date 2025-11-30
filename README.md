# Spotify Library Manager 🎵

A Python CLI application to download, store, and search your Spotify library locally.

## Features

- 🔐 OAuth authentication with Spotify
- 📥 Download all your playlists and saved tracks
- 💾 Store metadata in a local JSON database (TinyDB)
- 🔍 Fast local search across tracks, artists, and albums
- 📊 View library statistics
- 📂 Browse playlists and tracks

## Setup

### 1. Create Virtual Environment

```bash
python -m venv .venv-win11
.venv-win11\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
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
python src/cli.py setup
```

Or manually create a `.env` file:

```env
SPOTIPY_CLIENT_ID=your_client_id_here
SPOTIPY_CLIENT_SECRET=your_client_secret_here
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8000/callback
```

## Usage

On Windows, you can use the `spotify-search` launcher instead of `python src/cli.py` for all commands (e.g., `spotify-search sync`).

On macOS, see `macos_install/README.md` for a quick installer and a simple `./macos_install/spotify-search` launcher that avoids typing `python`.

Tip: running the CLI with no arguments launches the interactive shell automatically.

### Authenticate with Spotify

```bash
# Cross-platform (Python)
python src/cli.py auth

# Windows launcher
spotify-search auth
```

This will open a browser window for you to authorize the application. After authorization, you'll be redirected to localhost (which may show an error page - that's okay, the auth token is captured).

### Sync Your Library

Download all your playlists and saved tracks:

```bash
# Cross-platform (Python)
python src/cli.py sync

# Windows launcher
spotify-search sync
```

To clear existing data and start fresh:

```bash
# Cross-platform (Python)
python src/cli.py sync --clear

# Windows launcher
spotify-search sync --clear
```

### Sync Differences (Faster)

Skip playlists and saved tracks that already match counts in your local DB. This is much faster for subsequent syncs.

```bash
# Cross-platform (Python)
python src/cli.py sync-diff

# Windows launcher
spotify-search sync-diff
```

Notes:
- Playlists are skipped when their Spotify `snapshot_id` matches the one stored locally (robust change detection). If `snapshot_id` is missing, it falls back to comparing local relationship count to Spotify's `tracks_total`.
- Snapshot is recorded only after a playlist's tracks are fetched and saved successfully, so partial updates won't cause future skips.
- Saved tracks are skipped when local count equals Spotify’s saved total.
- If you suspect a mismatch (e.g., unplayable/local tracks affect totals), run a full `sync` to force refresh.

### Search for Tracks

Search across track names, artists, and albums:

```bash
# Cross-platform (Python)
python src/cli.py search "bohemian rhapsody"
python src/cli.py search "taylor swift"
python src/cli.py search "abbey road"

# Windows launcher
spotify-search search "bohemian rhapsody"
spotify-search search "taylor swift"
spotify-search search "abbey road"
```

Limit the number of results:

```bash
# Cross-platform (Python)
python src/cli.py search "love" --limit 10

# Windows launcher
spotify-search search "love" --limit 10
```

### Find Duplicates

List tracks that appear in multiple playlists, ordered by how many times they occur. Shows track info, the number of duplicates, and the playlists (with links) they’re in.

```bash
# Cross-platform (Python)
python src/cli.py duplicates           # top 5 by default
python src/cli.py duplicates --limit 10

# Windows launcher
spotify-search duplicates
spotify-search duplicates --limit 10
```

### List Playlists

View all your playlists:

```bash
# Cross-platform (Python)
python src/cli.py list

# Windows launcher
spotify-search list
```

View tracks in a specific playlist:

```bash
# Cross-platform (Python)
python src/cli.py list --playlist "Discover Weekly"

# Windows launcher
spotify-search list --playlist "Discover Weekly"
```

### View Statistics

See your library statistics:

```bash
# Cross-platform (Python)
python src/cli.py stats

# Windows launcher
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
# Cross-platform (Python)
python src/cli.py clear-auth
python src/cli.py clear-auth --dry-run  # preview only (shows files which would be removed)

# Windows launcher
spotify-search clear-auth
spotify-search clear-auth --dry-run
```

## Commands Reference

| Command | Description |
|---------|-------------|
| `setup` | Configure Spotify API credentials |
| `auth` | Authenticate with Spotify |
| `sync` | Download and sync your entire library |
| `sync-diff` | Sync only changes; skip up-to-date playlists/saved tracks |
| `search QUERY` | Search for tracks locally |
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

Database file: `spotify_library.json`

## Project Structure

```
spotify-search/
├── src/
│   ├── cli.py              # CLI commands
│   ├── config.py           # Configuration management
│   ├── database.py         # Database operations
│   ├── spotify_client.py   # Spotify API wrapper
│   └── main.py             # (Original file)
├── .env                    # Environment variables (not in git)
├── .env.example            # Example environment file
├── .gitignore             # Git ignore rules
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── spotify-search.bat     # Windows launcher
└── spotify_library.json   # Local database (created after sync)
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
- Some private or unavailable tracks may be skipped

**Search Not Working:**
- Make sure you've run `sync` at least once
- Check that `spotify_library.json` exists and has data

## Future Enhancements

Possible features to add:
- Export playlists to CSV/Excel
- Create new playlists from search results
- Audio features analysis (tempo, energy, etc.)
- Duplicate track detection
- Playlist comparison tools
- Web interface

## License

MIT License - Feel free to use and modify as needed!
