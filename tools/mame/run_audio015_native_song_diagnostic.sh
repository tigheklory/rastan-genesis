#!/usr/bin/env bash
# AUDIO-015 native multi-song DIAGNOSTIC harness launcher (GENESIS NTSC).
# Injects the reserved diagnostic selectors 0xD0-0xD6 and confirms every authored
# stream decodes.  This is a labeled diagnostic, NOT authentic-gameplay evidence.
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
    echo "usage: $0 ROM [OUTPUT_DIR]" >&2
    exit 2
fi

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
ROM=$1
OUTPUT_DIR=${2:-"$ROOT/states/traces/audio015_native_song_diagnostic"}
SCRIPT="$ROOT/tools/mame/scripts/audio015_native_song_diagnostic.lua"
MACHINE="${MAME_GENESIS_MACHINE:-genesis}"

for required in "$ROM" "$SCRIPT"; do
    test -s "$required" || { echo "ERROR: missing required input: $required" >&2; exit 1; }
done

mkdir -p "$OUTPUT_DIR"
TRACE_DIR="$OUTPUT_DIR" timeout 300s mame "$MACHINE" \
    -cart "$ROM" -video none -sound none -nothrottle -skip_gameinfo \
    -autoboot_script "$SCRIPT" \
    > "$OUTPUT_DIR/mame_stdout.txt" 2> "$OUTPUT_DIR/mame_stderr.txt"

SUMMARY="$OUTPUT_DIR/native_song_diagnostic.tsv"
test -s "$SUMMARY" || { echo "ERROR: no diagnostic output" >&2; exit 1; }
cat "$SUMMARY"
grep -qx 'result=PASS' "$SUMMARY"
