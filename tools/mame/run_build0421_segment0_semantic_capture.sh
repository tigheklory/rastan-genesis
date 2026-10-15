#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
    echo "usage: $0 ROM OUTPUT_DIR [PLAYER_X]" >&2
    exit 2
fi

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
ROM=$1
OUTPUT_DIR=$2
PLAYER_X=${3:-0x20}
SCRIPT="$ROOT/tools/mame/scripts/build0421_segment0_semantic_capture.lua"

mkdir -p "$OUTPUT_DIR"
TRACE_DIR="$OUTPUT_DIR" SEGMENT0_CAPTURE_X="$PLAYER_X" timeout 120s mame genesis \
    -cart "$ROM" -video none -sound none -nothrottle -skip_gameinfo \
    -autoboot_script "$SCRIPT" \
    > "$OUTPUT_DIR/mame_stdout.txt" 2> "$OUTPUT_DIR/mame_stderr.txt"

test -s "$OUTPUT_DIR/state.tsv"
cat "$OUTPUT_DIR/state.tsv"
