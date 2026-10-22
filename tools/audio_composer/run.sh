#!/usr/bin/env bash
# Launch the Rastan Audio Composer (Phase 1) — DEVELOPMENT TOOL ONLY.
# No ROM, no build, no production ASM change. Arcade captures + Lawrence's VGM are READ-ONLY.
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
PORT="${1:-8781}"
echo "Rastan Audio Composer -> open http://localhost:${PORT} in your browser (Ctrl-C to stop)."
exec python3 tools/audio_composer/server.py "$PORT"
