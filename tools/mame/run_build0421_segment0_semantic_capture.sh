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
SYMBOLS=${STAGE_CAPTURE_SYMBOLS:-"$ROOT/apps/rastan-direct/out/symbol.txt"}

symaddr() { awk -v n="$1" '$3==n { print "0x"$1; exit }' "$SYMBOLS"; }
SCENE_ADDR=$(symaddr genesistan_current_scene_id)
ACTIVE_LUT_ADDR=$(symaddr fg_boundary_active_lut)
STAGED_BG_ADDR=$(symaddr staged_bg_buffer)
STAGED_FG_ADDR=$(symaddr staged_fg_buffer)

for required in SCENE_ADDR ACTIVE_LUT_ADDR STAGED_BG_ADDR STAGED_FG_ADDR; do
    [[ -n "${!required}" ]] || { echo "missing symbol for $required in $SYMBOLS" >&2; exit 2; }
done

mkdir -p "$OUTPUT_DIR"
TRACE_DIR="$OUTPUT_DIR" SEGMENT0_CAPTURE_X="$PLAYER_X" \
SCENE_ADDR="$SCENE_ADDR" ACTIVE_LUT_ADDR="$ACTIVE_LUT_ADDR" \
STAGED_BG_ADDR="$STAGED_BG_ADDR" STAGED_FG_ADDR="$STAGED_FG_ADDR" \
timeout 120s mame genesis \
    -cart "$ROM" -video none -sound none -nothrottle -skip_gameinfo \
    -snapshot_directory "$OUTPUT_DIR" -snapname frame \
    -autoboot_script "$SCRIPT" \
    > "$OUTPUT_DIR/mame_stdout.txt" 2> "$OUTPUT_DIR/mame_stderr.txt"

test -s "$OUTPUT_DIR/state.tsv"
cat "$OUTPUT_DIR/state.tsv"
