import argparse
import json
import sys
import sys as _sys

# Ensure imports from src work when run as module or script
from pathlib import Path
from pathlib import Path as _Path

_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))

import config  # noqa: E402
from spotify_client import SpotifyClient  # noqa: E402


def get_playlists(client: SpotifyClient):
    return client.get_user_playlists()


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Dump full JSON of Spotify playlist (no filters)."
    )
    parser.add_argument("-o", "--output", help="Output file path (defaults to stdout)")
    parser.add_argument(
        "--compact", action="store_true", help="Compact JSON (default pretty-printed)"
    )

    args = parser.parse_args(argv)

    if not config.validate_config():
        print(
            "Spotify credentials not configured. Run 'spotify-search setup' first.",
            file=sys.stderr,
        )
        return 2

    try:
        client = SpotifyClient()

        data = get_playlists(client)
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
