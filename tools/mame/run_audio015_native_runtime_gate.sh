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
SYMBOLS=${AUDIO015_SYMBOLS:-"$ROOT/apps/rastan-direct/out/symbol.txt"}

symbol_address() {
    local name=$1
    awk -v wanted="$name" '$NF == wanted { print "0x" $1; found=1; exit } END { if (!found) exit 1 }' "$SYMBOLS"
}

for required in "$ROM" "$Z80_BIN" "$SCRIPT"; do
    test -s "$required" || { echo "ERROR: missing required input: $required" >&2; exit 1; }
done

mkdir -p "$OUTPUT_DIR"
MAME_CONTROL_ARGS=()
if [[ ${AUDIO015_ROUTE:-gameplay_right} == natural_round1_transitions ]]; then
    MAME_CONTROL_ARGS=(-ctrl1 md6button)
    export AUDIO015_SCENE_ADDR=${AUDIO015_SCENE_ADDR:-$(symbol_address genesistan_current_scene_id)}
    export AUDIO015_TILESET_ADDR=${AUDIO015_TILESET_ADDR:-$(symbol_address genesistan_current_pc080sn_tileset_id)}
    export AUDIO015_ACTIVE_RECORD_ADDR=${AUDIO015_ACTIVE_RECORD_ADDR:-$(symbol_address fg_boundary_active_record)}
    export AUDIO015_ACTIVE_PACKAGE_ADDR=${AUDIO015_ACTIVE_PACKAGE_ADDR:-$(symbol_address fg_boundary_active_package)}
    export AUDIO015_STAGED_PALETTE_ADDR=${AUDIO015_STAGED_PALETTE_ADDR:-$(symbol_address staged_palette_words)}
    export AUDIO015_TEST_LINE0=${AUDIO015_TEST_LINE0:-"$ROOT/build/rastan-direct/test_palette_line0.bin"}
    export AUDIO015_TEST_LINE1=${AUDIO015_TEST_LINE1:-"$ROOT/build/rastan-direct/test_palette_line1.bin"}
    export AUDIO015_TEST_LINE3=${AUDIO015_TEST_LINE3:-"$ROOT/build/rastan-direct/test_palette_line3.bin"}
fi
TRACE_DIR="$OUTPUT_DIR" AUDIO015_ROM="$ROM" AUDIO015_Z80_BIN="$Z80_BIN" \
AUDIO015_MAX_FRAMES="${AUDIO015_MAX_FRAMES:-1000}" \
AUDIO015_ROUTE="${AUDIO015_ROUTE:-gameplay_right}" timeout 300s mame genesis \
    -cart "$ROM" -video none -sound none -nothrottle -skip_gameinfo \
    "${MAME_CONTROL_ARGS[@]}" \
    -autoboot_script "$SCRIPT" \
    > "$OUTPUT_DIR/mame_stdout.txt" 2> "$OUTPUT_DIR/mame_stderr.txt"

SUMMARY="$OUTPUT_DIR/audio_runtime_summary.txt"
test -s "$SUMMARY" || { echo "ERROR: no audio runtime summary" >&2; exit 1; }
cat "$SUMMARY"
grep -qx 'result=PASS' "$SUMMARY"
