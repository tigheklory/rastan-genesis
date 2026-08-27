#!/usr/bin/env bash
# Launch the Palette/Tile-Line Assignment Editor v0.1 (TOOLING ONLY; no ROM, Build 313 unchanged).
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
PORT="${1:-8770}"
echo "Open http://localhost:${PORT} in your browser (Ctrl-C to stop)."
exec python3 tools/graphics_editor/server.py "$PORT"
