#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 4 ]]; then
    echo "usage: $0 ROM BUILD_TAG [TRACE_DIR] [SYMBOLS]" >&2
    exit 2
fi

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
ROM=$1
BUILD_TAG=$2
TRACE_DIR=${3:-"$ROOT/states/traces/build${BUILD_TAG}_final_life_zero_input_$(date +%Y%m%d_%H%M%S)"}
SYMBOLS=${4:-"$ROOT/apps/rastan-direct/out/symbol.txt"}
SCRIPT="$ROOT/tools/mame/scripts/final_life_zero_input_regression.lua"

for required in "$ROM" "$SCRIPT" "$SYMBOLS"; do
    if [[ ! -s "$required" ]]; then
        echo "ERROR: required final-life input missing or empty: $required" >&2
        exit 1
    fi
done

mkdir -p "$TRACE_DIR"
printf '%s\n' "$TRACE_DIR" > "$ROOT/build/rastan-direct/final_life_zero_input_latest.txt"

TRACE_DIR="$TRACE_DIR" FINAL_LIFE_SYMBOLS="$SYMBOLS" \
FINAL_LIFE_MAX_FRAMES=12000 FINAL_LIFE_STALL_FRAMES=1200 \
timeout 300s mame genesis \
    -cart "$ROM" -video none -sound none -nothrottle -skip_gameinfo \
    -autoboot_script "$SCRIPT" \
    > "$TRACE_DIR/mame_stdout.txt" 2> "$TRACE_DIR/mame_stderr.txt"

SUMMARY="$TRACE_DIR/summary.txt"
if [[ ! -s "$SUMMARY" ]]; then
    echo "ERROR: final-life route produced no summary: $SUMMARY" >&2
    exit 1
fi
cat "$SUMMARY"
