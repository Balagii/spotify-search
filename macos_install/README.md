# macOS Installation and Usage

This folder contains scripts to set up and run Spotify Library Manager on macOS (and most Linux shells).

## Quick Install (clones repo and sets up)

```bash
# Creates a new 'spotify-search' folder in the current directory
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Balagii/spotify-search/HEAD/macos_install/install_from_github.sh)"
```

Or download then run locally:

```bash
curl -fsSL -o install_from_github.sh \
  https://raw.githubusercontent.com/Balagii/spotify-search/HEAD/macos_install/install_from_github.sh
bash install_from_github.sh
```

This will:
- Clone the repo
- Create a virtual environment
- Install dependencies
- Prompt for Spotify credentials and create `.env`
- Open the browser for authentication
- Run a differential sync (falls back to full sync if needed)

## Setup After Cloning (inside the repo)

```bash
# From the project root
bash macos_install/setup_macos.sh
```

This does the same as above, but assumes you already cloned the repository.

## Running the CLI (no python prefix)

Use the lightweight launcher:

```bash
./macos_install/spotify-search stats
./macos_install/spotify-search search "bohemian rhapsody"
./macos_install/spotify-search list --playlist "Discover Weekly"
```

Optional: add a symlink into your PATH so you can run `spotify-search` anywhere:

```bash
ln -sf "$(pwd)/macos_install/spotify-search" /usr/local/bin/spotify-search
# then
spotify-search stats
```

## Notes

- You must add the redirect URI you use (default `http://localhost:8888/callback`) in your Spotify Developer Dashboard app settings.
- Secrets are stored locally in `.env`, which is already `.gitignore`d.
- For faster re-syncs, prefer `sync-diff`.
