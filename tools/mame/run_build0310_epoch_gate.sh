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
TRACE_DIR=${4:-"$ROOT/states/traces/build${BUILD_TAG}_phase1_epoch_gate_$(date +%Y%m%d_%H%M%S)"}
SCRIPT="$ROOT/tools/mame/scripts/build0310_epoch_gate.lua"
CONSTANTS="$ROOT/build/pc080sn_boundary/boundary_constants.inc"

for required in "$ROM" "$SYMBOLS" "$SCRIPT" "$CONSTANTS"; do
    if [[ ! -s "$required" ]]; then
        echo "ERROR: required epoch-gate input missing or empty: $required" >&2
        exit 1
    fi
done

mkdir -p "$TRACE_DIR"
printf '%s\n' "$TRACE_DIR" > "$ROOT/build/rastan-direct/phase1_epoch_gate_latest.txt"

# One representative production handoff for each generated Phase-1 residency epoch/transition.
# Keep these package expectations synchronized with boundary_report.json's authoritative
# record_to_package array begins [0,0,0,8,9,2,2,2,2,2,2,10,3,11,4,4,5...].
# record:epoch:package
#   0 -> epoch0/pkg0 ; 3 -> epoch1/pkg8 (rope transition) ; 4 -> epoch2/pkg9 (waterfall transition) ;
#   5 -> epoch2/pkg2 (stable) ; 11 -> epoch3/pkg10 ; 13 -> epoch4/pkg11
cases=("0:0:0" "3:1:8" "4:2:9" "5:2:2" "11:3:10" "13:4:11")
for entry in "${cases[@]}"; do
    IFS=: read -r record epoch package <<< "$entry"
    case_dir="$TRACE_DIR/epoch_${epoch}_record_${record}"
    mkdir -p "$case_dir"
    TRACE_DIR="$case_dir" \
    EPOCH_GATE_SYMBOLS="$SYMBOLS" \
    EPOCH_GATE_CONSTANTS="$CONSTANTS" \
    EPOCH_GATE_TARGET_RECORD="$record" \
    EPOCH_GATE_TARGET_EPOCH="$epoch" \
    EPOCH_GATE_TARGET_PACKAGE="$package" \
    EPOCH_GATE_MAX_FRAMES=800 \
    EPOCH_GATE_SURVIVAL_FRAMES=8 \
    timeout 120s mame genesis \
        -cart "$ROM" \
        -video none -sound none -nothrottle -skip_gameinfo \
        -autoboot_script "$SCRIPT" \
        > "$case_dir/mame_stdout.txt" 2> "$case_dir/mame_stderr.txt"

    summary="$case_dir/epoch_gate_summary.txt"
    if [[ ! -s "$summary" ]]; then
        echo "ERROR: epoch $epoch produced no summary: $summary" >&2
        exit 1
    fi
    cat "$summary"
    if ! grep -qx 'result=PASS' "$summary"; then
        echo "ERROR: epoch $epoch runtime gate failed; evidence preserved in $case_dir" >&2
        exit 1
    fi
done

{
    echo "result=PASS"
    echo "round1_cases_tested=6"
    echo "records_tested=0,3,4,5,11,13"
    echo "plane_a_full_lut_checks=PASS"
    echo "plane_b_fixed_lut_checks=PASS"
} > "$TRACE_DIR/phase1_epoch_gate_summary.txt"
cat "$TRACE_DIR/phase1_epoch_gate_summary.txt"
echo "Phase-1 seven-epoch gate PASS: $TRACE_DIR"
