#!/usr/bin/env bash
set -euo pipefail

if [[ $# -gt 1 ]]; then
    echo "usage: $0 [OUTPUT_DIR]" >&2
    exit 2
fi

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
OUTPUT_DIR=${1:-"$ROOT/states/traces/audio015_arcade_command_timing"}
SCRIPT="$ROOT/tools/mame/scripts/audio015_arcade_command_timing.lua"
MAME_BIN=${MAME_BIN:-mame}

mkdir -p "$OUTPUT_DIR/mame_cfg_default"
TRACE_DIR="$OUTPUT_DIR" timeout 180s "$MAME_BIN" rastan \
    -rompath "$ROOT/roms" -video none -sound none -nothrottle \
    -speed 1.0 -norefreshspeed -cfg_directory "$OUTPUT_DIR/mame_cfg_default" \
    -cheat -cheatpath "$ROOT/tools/mame/cheat" -plugin cheat -skip_gameinfo \
    -autoboot_script "$SCRIPT" \
    > "$OUTPUT_DIR/mame_stdout.txt" 2> "$OUTPUT_DIR/mame_stderr.txt"

test -s "$OUTPUT_DIR/arcade_command_timing.tsv"
cat "$OUTPUT_DIR/arcade_command_timing.tsv"
