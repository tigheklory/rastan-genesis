#!/usr/bin/env bash
set -euo pipefail

if [[ $# -gt 2 ]]; then
    echo "usage: $0 [TRIALS] [OUTPUT_DIR]" >&2
    exit 2
fi

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
TRIALS=${1:-5}
OUTPUT_DIR=${2:-"$ROOT/states/traces/arcade_rastan_rope_attach_reference"}
SCRIPT="$ROOT/tools/mame/scripts/arcade_rope_attach_reference_benchmark.lua"
MAME_BIN=${MAME_BIN:-mame}

mkdir -p "$OUTPUT_DIR"
printf 'trial\tresult\treason\tstart_frame\tattach_frame\telapsed_frames\telapsed_seconds\telapsed_milliseconds\trecord\tplayer_state\tplayer_x\tplayer_y\tfg_x\tfg_y\tlives\ta5\tp1_port\tcheat_active\tinvincibility_word\n' > "$OUTPUT_DIR/trials.tsv"

for trial in $(seq 1 "$TRIALS"); do
    trial_dir="$OUTPUT_DIR/trial_$(printf '%02d' "$trial")"
    mkdir -p "$trial_dir"
    mkdir -p "$trial_dir/mame_cfg_default"
    TRACE_DIR="$trial_dir" ROPE_BENCH_TRIAL="$trial" ROPE_BENCH_INVINCIBLE=1 \
      timeout 180s "$MAME_BIN" rastan \
        -rompath "$ROOT/roms" -video none -sound none -nothrottle \
        -speed 1.0 -norefreshspeed -cfg_directory "$trial_dir/mame_cfg_default" \
        -cheat -cheatpath "$ROOT/tools/mame/cheat" -plugin cheat -skip_gameinfo \
        -autoboot_script "$SCRIPT" \
        > "$trial_dir/mame_stdout.txt" 2> "$trial_dir/mame_stderr.txt"
    test -s "$trial_dir/trial.tsv"
    tail -n 1 "$trial_dir/trial.tsv" >> "$OUTPUT_DIR/trials.tsv"
done

if awk -F '\t' 'NR > 1 && $2 != "PASS" { failed=1 } END { exit failed }' "$OUTPUT_DIR/trials.tsv"; then
    python3 "$ROOT/tools/mame/summarize_rope_attach_benchmark.py" \
        --trials "$OUTPUT_DIR/trials.tsv" --output "$OUTPUT_DIR/summary.txt" \
        --build "arcade-rastan-world-rev1"
else
    {
        printf 'build=arcade-rastan-world-rev1\n'
        printf 'trials=%s\n' "$TRIALS"
        printf 'result=NO_VALID_ROPE_ATTACH\n'
        printf 'reason=route_failed_before_rope\n'
        printf 'silver_standard_established=NO\n'
    } > "$OUTPUT_DIR/summary.txt"
fi
cat "$OUTPUT_DIR/summary.txt"
