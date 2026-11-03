#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 || $# -gt 4 ]]; then
    echo "usage: $0 ROM BUILD_TAG TRIALS [OUTPUT_DIR]" >&2
    exit 2
fi

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
ROM=$1
BUILD_TAG=$2
TRIALS=$3
OUTPUT_DIR=${4:-"$ROOT/states/traces/build${BUILD_TAG}_rope_attach_benchmark"}
SCRIPT="$ROOT/tools/mame/scripts/rope_attach_performance_benchmark.lua"

mkdir -p "$OUTPUT_DIR"
printf 'trial\tresult\treason\tstart_frame\tattach_frame\telapsed_frames\telapsed_seconds\telapsed_milliseconds\trecord\tplayer_state\tplayer_x\tplayer_y\n' > "$OUTPUT_DIR/trials.tsv"

for trial in $(seq 1 "$TRIALS"); do
    trial_dir="$OUTPUT_DIR/trial_$(printf '%02d' "$trial")"
    mkdir -p "$trial_dir"
    TRACE_DIR="$trial_dir" ROPE_BENCH_TRIAL="$trial" timeout 180s mame genesis \
        -cart "$ROM" -video none -sound none -nothrottle -skip_gameinfo \
        -autoboot_script "$SCRIPT" \
        > "$trial_dir/mame_stdout.txt" 2> "$trial_dir/mame_stderr.txt"
    test -s "$trial_dir/trial.tsv"
    tail -n 1 "$trial_dir/trial.tsv" >> "$OUTPUT_DIR/trials.tsv"
done

python3 "$ROOT/tools/mame/summarize_rope_attach_benchmark.py" \
    --trials "$OUTPUT_DIR/trials.tsv" --output "$OUTPUT_DIR/summary.txt" --build "$BUILD_TAG"
cat "$OUTPUT_DIR/summary.txt"
