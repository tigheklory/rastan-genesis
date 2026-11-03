#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 4 || $# -gt 5 ]]; then
    echo "usage: $0 ROM SYMBOLS SCORE_AWARD_RUNTIME_PC BUILD_TAG [TRACE_DIR]" >&2
    exit 2
fi

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
ROM=$1
SYMBOLS=$2
SCORE_AWARD_PC=$3
BUILD_TAG=$4
TRACE_DIR=${5:-"$ROOT/states/traces/build${BUILD_TAG}_gameplay_hud_event_$(date +%Y%m%d_%H%M%S)"}
SCRIPT="$ROOT/tools/mame/scripts/gameplay_hud_event_regression.lua"
mkdir -p "$TRACE_DIR"

HUD_EVENT_SYMBOLS="$SYMBOLS" HUD_EVENT_SCORE_AWARD_PC="$SCORE_AWARD_PC" \
HUD_EVENT_OUTPUT="$TRACE_DIR/result.txt" timeout 120s mame genesis \
    -cart "$ROM" -video none -sound none -nothrottle -skip_gameinfo \
    -autoboot_script "$SCRIPT" \
    > "$TRACE_DIR/mame_stdout.txt" 2> "$TRACE_DIR/mame_stderr.txt"

cat "$TRACE_DIR/result.txt"
grep -qx 'result=PASS' "$TRACE_DIR/result.txt"
