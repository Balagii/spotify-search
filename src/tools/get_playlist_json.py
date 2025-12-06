import argparse
import json
import sys
from pathlib import Path

# Ensure imports from src work when run as module or script
from pathlib import Path as _Path
import sys as _sys
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))

import config  # noqa: E402
from spotify_client import SpotifyClient  # noqa: E402


def find_playlist_id_by_name(client: SpotifyClient, name: str, contains: bool = False):
    playlists = client.get_user_playlists()
    name_l = name.lower()
    matches = []
    for p in playlists:
        pn = p.get('name', '')
        if (pn.lower() == name_l) or (contains and name_l in pn.lower()):
            matches.append(p)
    if not matches:
        return None, []
    if len(matches) > 1 and not contains:
        # Multiple exact matches (rare) — let caller decide
        return None, matches
    return matches[0]['id'], matches


def fetch_full_playlist_json(sp, playlist_id: str) -> dict:
    base = sp.playlist(playlist_id)
    # Collect all items (tracks and episodes if present)
    items = []
    limit = 100
    offset = 0
    while True:
        page = sp.playlist_items(playlist_id, limit=limit, offset=offset)
        items.extend(page.get('items', []))
        if not page.get('next'):
            break
        offset += limit
    # Replace tracks.items with full list
    if 'tracks' not in base or not isinstance(base['tracks'], dict):
        base['tracks'] = {}
    base['tracks']['items'] = items
    base['tracks']['total'] = len(items)
    return base


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Dump full JSON for a named Spotify playlist (no filters)."
    )
    parser.add_argument("name", help="Exact playlist name (use --contains for substring match)")
    parser.add_argument("-o", "--output", help="Output file path (defaults to stdout)")
    parser.add_argument("--contains", action="store_true", help="Match substring instead of exact name")
    parser.add_argument("--compact", action="store_true", help="Compact JSON (default pretty-printed)")
    args = parser.parse_args(argv)

    if not config.validate_config():
        print("Spotify credentials not configured. Run 'spotify-search setup' first.", file=sys.stderr)
        return 2

    try:
        client = SpotifyClient()
        pid, matches = find_playlist_id_by_name(client, args.name, contains=args.contains)
        if not pid:
            if matches:
                print("Multiple playlists matched. Be more specific or use --contains:", file=sys.stderr)
                for p in matches:
                    print(f" - {p['name']} (id={p['id']}, total={p.get('tracks_total', 'n/a')})", file=sys.stderr)
                return 3
            print(f"No playlist matched name: {args.name}", file=sys.stderr)
            return 4

        data = fetch_full_playlist_json(client.sp, pid)
        indent = None if args.compact else 2
        text = json.dumps(data, ensure_ascii=False, indent=indent)

        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
        else:
            sys.stdout.write(text + "\n")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
