#!/usr/bin/env bash
# RG-019 functional verification for starting-subround variants (GENESIS NTSC).
# Boots each variant, runs the normal credit/start sequence, latches the live STAGE INDEX
# (a5@0x1242 = 0x00FF1242) at first appearance, and checks it equals the arcade-derived
# expected index  (round-1)*23 + 22*boss + 16*castle.  The stage index -- not the round
# counter -- is the authoritative selection result (confirmed on the original arcade).
# This tests actual gameplay initialization, not merely that the ROM byte changed.
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
PREFIX=${1:-}
[ -n "$PREFIX" ] || { echo "usage: $0 <dist/.../rastan_direct_video_test_build_NNNN> [S-list]" >&2; exit 2; }
SCRIPT="$ROOT/tools/mame/scripts/subround_start_probe.lua"
MACHINE="${MAME_GENESIS_MACHINE:-genesis}"
OUTDIR="$ROOT/states/traces/subround_functional_$(basename "$PREFIX")"
mkdir -p "$OUTDIR"

# S-list: space-separated R-S pairs (default: canonical + all 18).
LIST=${2:-"0-0 1-1 1-2 1-3 2-1 2-2 2-3 3-1 3-2 3-3 4-1 4-2 4-3 5-1 5-2 5-3 6-1 6-2 6-3"}
fails=0
for rs in $LIST; do
    r=${rs%-*}; s=${rs#*-}
    if [ "$rs" = "0-0" ]; then cart="${PREFIX}.bin"; label="canonical"; exp=0
    else cart="${PREFIX}_S${r}-${s}.bin"; label="S${r}-${s}"
         exp=$(python3 -c "print((($r-1)*23)+(22 if $s==3 else 0)+(16 if $s==2 else 0))"); fi
    [ -s "$cart" ] || { echo "MISSING $cart"; fails=$((fails+1)); continue; }
    od="$OUTDIR/$label"; mkdir -p "$od"
    EXPECT_STAGE=$exp MAX_FRAMES=1400 TRACE_DIR="$od" timeout 180s "${MAME_BIN:-mame}" "$MACHINE" \
        -cart "$cart" -video none -sound none -nothrottle -skip_gameinfo \
        -autoboot_script "$SCRIPT" >"$od/o" 2>"$od/e" || true
    line=$(cat "$od/probe.tsv" 2>/dev/null || echo "NO-OUTPUT")
    printf "%-10s exp=0x%04X  %s\n" "$label" "$exp" "$line"
    echo "$line" | grep -q "result=PASS" || { [ "$label" = "canonical" ] && echo "$line" | grep -q "stage=0x0000" || fails=$((fails+1)); }
done
echo "---"
[ "$fails" -eq 0 ] && echo "SUBROUND_FUNCTIONAL_VERIFY PASS" || { echo "SUBROUND_FUNCTIONAL_VERIFY FAIL ($fails)"; exit 1; }
