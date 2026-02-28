#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

PLUGIN_SRC="$ROOT_DIR/molkit"
PLUGIN_DST="$ROOT_DIR/pymol-open-source/data/startup/molkit"

# Init submodule if needed
if [ ! -f "$ROOT_DIR/pymol-open-source/setup.py" ]; then
    echo "Initializing pymol-open-source submodule..."
    git -C "$ROOT_DIR" submodule update --init --recursive
fi

# Create symlink
if [ -L "$PLUGIN_DST" ]; then
    echo "Symlink already exists: $PLUGIN_DST"
elif [ -d "$PLUGIN_DST" ]; then
    echo "ERROR: $PLUGIN_DST exists as a directory. Remove it first."
    exit 1
else
    ln -s "$PLUGIN_SRC" "$PLUGIN_DST"
    echo "Created symlink: $PLUGIN_DST -> $PLUGIN_SRC"
fi

echo ""
echo "Done! Build PyMOL with:"
echo "  cd pymol-open-source && pip install ."
echo ""
echo "Then run:"
echo "  pymol"
