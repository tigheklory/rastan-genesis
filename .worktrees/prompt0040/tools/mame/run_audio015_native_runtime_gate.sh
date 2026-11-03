#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 || $# -gt 4 ]]; then
    echo "usage: $0 ROM Z80_BIN BUILD_TAG [OUTPUT_DIR]" >&2
    exit 2
fi

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
ROM=$1
Z80_BIN=$2
BUILD_TAG=$3
OUTPUT_DIR=${4:-"$ROOT/states/traces/build${BUILD_TAG}_audio015_native_runtime"}
SCRIPT="$ROOT/tools/mame/scripts/audio015_native_runtime_gate.lua"

for required in "$ROM" "$Z80_BIN" "$SCRIPT"; do
    test -s "$required" || { echo "ERROR: missing required input: $required" >&2; exit 1; }
done

mkdir -p "$OUTPUT_DIR"
TRACE_DIR="$OUTPUT_DIR" AUDIO015_ROM="$ROM" AUDIO015_Z80_BIN="$Z80_BIN" \
AUDIO015_MAX_FRAMES="${AUDIO015_MAX_FRAMES:-1000}" \
AUDIO015_ROUTE="${AUDIO015_ROUTE:-gameplay_right}" timeout 300s mame genesis \
    -cart "$ROM" -video none -sound none -nothrottle -skip_gameinfo \
    -autoboot_script "$SCRIPT" \
    > "$OUTPUT_DIR/mame_stdout.txt" 2> "$OUTPUT_DIR/mame_stderr.txt"

SUMMARY="$OUTPUT_DIR/audio_runtime_summary.txt"
test -s "$SUMMARY" || { echo "ERROR: no audio runtime summary" >&2; exit 1; }
cat "$SUMMARY"
grep -qx 'result=PASS' "$SUMMARY"
