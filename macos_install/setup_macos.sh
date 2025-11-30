#!/usr/bin/env bash
set -euo pipefail

# macOS setup for spotify-search (run inside the repo)
# - Creates venv, installs deps, prompts for credentials, authenticates, and runs a sync.

command -v python3 >/dev/null 2>&1 || { echo "python3 is required (brew install python)"; exit 1; }

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# 1) Create and activate virtualenv
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
source .venv/bin/activate

# 2) Install dependencies
python -m pip install -U pip
pip install -r requirements.txt

# 3) Configure credentials
if [[ -f .env ]]; then
  echo ".env already exists. Skipping credential prompts."
else
  read -p "Enter Spotify Client ID: " SPOTIPY_CLIENT_ID
  read -s -p "Enter Spotify Client Secret: " SPOTIPY_CLIENT_SECRET
  echo
  read -p "Enter Redirect URI [http://localhost:8888/callback]: " SPOTIPY_REDIRECT_URI
  SPOTIPY_REDIRECT_URI=${SPOTIPY_REDIRECT_URI:-http://localhost:8888/callback}

  cat > .env <<EOF
SPOTIPY_CLIENT_ID=$SPOTIPY_CLIENT_ID
SPOTIPY_CLIENT_SECRET=$SPOTIPY_CLIENT_SECRET
SPOTIPY_REDIRECT_URI=$SPOTIPY_REDIRECT_URI
EOF
  echo "Wrote .env. Ensure the same Redirect URI is in Spotify Dashboard."
fi

# 4) Authenticate (opens browser)
python src/cli.py auth || true

# 5) Sync (diff first, fallback to full)
python src/cli.py sync-diff || python src/cli.py sync

echo "\nSetup complete. Usage examples:"
echo "  ./macos_install/spotify-search stats"
echo "  ./macos_install/spotify-search search \"bohemian rhapsody\""
