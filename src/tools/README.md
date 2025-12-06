# Tools

Utility scripts for ad-hoc tasks.

## Dump Playlist JSON

Get the full JSON (no filters) for a named playlist, including all items across pages.

Usage:

```bash
# From repo root
python -m src.tools.get_playlist_json "My Playlist" > my_playlist.json

# Substring match
python -m src.tools.get_playlist_json "mario" --contains -o mario.json

# Compact (one-line) JSON
python -m src.tools.get_playlist_json "My Playlist" --compact
```

Notes:
- Requires Spotify credentials configured (see main README: `spotify-search setup`).
- If multiple playlists match, the script will list them and exit.
- Output is UTF-8; redirects and files are safe on Windows/macOS/Linux.