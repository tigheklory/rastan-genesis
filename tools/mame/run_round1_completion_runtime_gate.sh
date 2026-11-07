#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 || $# -gt 4 ]]; then
    echo "usage: $0 ROM SYMBOLS ROUTE [OUTPUT_DIR]" >&2
    exit 2
fi
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
ROM=$1
SYMBOLS=$2
ROUTE=$3
OUT=${4:-"$ROOT/states/traces/round1_completion_${ROUTE}"}
SCRIPT="$ROOT/tools/mame/scripts/round1_completion_runtime_gate.lua"
test -s "$ROM"; test -s "$SYMBOLS"; test -s "$SCRIPT"
mkdir -p "$OUT"
R1C_OUTDIR="$OUT" R1C_SYMBOLS="$SYMBOLS" R1C_ROUTE="$ROUTE" \
R1C_MAX_FRAMES="${R1C_MAX_FRAMES:-24000}" timeout 600s mame genesis \
    -cart "$ROM" -ctrl1 md6button -video none -sound none -nothrottle -skip_gameinfo \
    -autoboot_script "$SCRIPT" >"$OUT/mame_stdout.txt" 2>"$OUT/mame_stderr.txt"
cat "$OUT/summary.txt"
grep -qx 'result=PASS' "$OUT/summary.txt"
