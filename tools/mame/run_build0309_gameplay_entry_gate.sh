#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 || $# -gt 4 ]]; then
    echo "usage: $0 ROM SYMBOLS BUILD_TAG [TRACE_DIR]" >&2
    exit 2
fi

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
ROM=$1
SYMBOLS=$2
BUILD_TAG=$3
TRACE_DIR=${4:-"$ROOT/states/traces/build${BUILD_TAG}_gameplay_entry_gate_$(date +%Y%m%d_%H%M%S)"}
SCRIPT="$ROOT/tools/mame/scripts/build0309_gameplay_entry_gate.lua"
CONSTANTS="$ROOT/build/pc080sn_boundary/boundary_constants.inc"

for required in "$ROM" "$SYMBOLS" "$SCRIPT" "$CONSTANTS"; do
    if [[ ! -s "$required" ]]; then
        echo "ERROR: required gameplay-gate input missing or empty: $required" >&2
        exit 1
    fi
done

mkdir -p "$TRACE_DIR"
printf '%s\n' "$TRACE_DIR" > "$ROOT/build/rastan-direct/gameplay_entry_gate_latest.txt"

TRACE_DIR="$TRACE_DIR" \
GAMEPLAY_GATE_SYMBOLS="$SYMBOLS" \
GAMEPLAY_GATE_CONSTANTS="$CONSTANTS" \
GAMEPLAY_GATE_MAX_FRAMES=1000 \
GAMEPLAY_GATE_SURVIVAL_FRAMES=240 \
timeout 120s mame genesis \
    -cart "$ROM" \
    -video none -sound none -nothrottle -skip_gameinfo \
    -autoboot_script "$SCRIPT" \
    > "$TRACE_DIR/mame_stdout.txt" 2> "$TRACE_DIR/mame_stderr.txt"

SUMMARY="$TRACE_DIR/gameplay_entry_gate_summary.txt"
if [[ ! -s "$SUMMARY" ]]; then
    echo "ERROR: gameplay-entry gate produced no summary: $SUMMARY" >&2
    exit 1
fi
cat "$SUMMARY"
if ! grep -qx 'result=PASS' "$SUMMARY"; then
    echo "ERROR: gameplay-entry gate failed; evidence preserved in $TRACE_DIR" >&2
    exit 1
fi
echo "gameplay-entry gate PASS: $TRACE_DIR"

