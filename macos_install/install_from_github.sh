#!/usr/bin/env bash
set -euo pipefail

# One-shot installer: clones the repo and runs setup on macOS/Linux.
# Usage: bash install_from_github.sh [target-dir]

command -v git >/dev/null 2>&1 || { echo "git is required"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "python3 is required (brew install python)"; exit 1; }

REPO_URL="https://github.com/Balagii/spotify-search.git"
TARGET_DIR="${1:-spotify-search}"

if [[ -e "$TARGET_DIR" ]]; then
  echo "Target directory '$TARGET_DIR' already exists. Aborting to avoid overwriting."
  exit 1
fi

echo "Cloning $REPO_URL into $TARGET_DIR ..."
git clone "$REPO_URL" "$TARGET_DIR"
cd "$TARGET_DIR"

# Run the in-repo setup
echo "Running setup ..."
bash macos_install/setup_macos.sh
