#!/usr/bin/env bash
set -euo pipefail
if [[ $# -ne 2 ]]; then
    echo "usage: $0 FINISH_FACING OUTPUT_DIR" >&2
    exit 2
fi
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
FACING=$1
OUT=$2
SCRIPT="$ROOT/tools/mame/scripts/round_transition_facing_arcade.lua"
mkdir -p "$OUT"
mkdir -p "$OUT/mame_cfg_default"
R1FACE_OUTDIR="$OUT" R1FACE_FINISH_FACING="$FACING" \
R1FACE_MAX_FRAMES="${R1FACE_MAX_FRAMES:-30000}" timeout 600s mame rastan \
    -rompath "$ROOT/roms" -window -sound none -skip_gameinfo \
    -cfg_directory "$OUT/mame_cfg_default" \
    -cheat -cheatpath "$ROOT/tools/mame/cheat" -plugin cheat \
    -autoboot_script "$SCRIPT" >"$OUT/mame_stdout.txt" 2>"$OUT/mame_stderr.txt"
cat "$OUT/summary.txt"
grep -qx 'result=PASS' "$OUT/summary.txt"
