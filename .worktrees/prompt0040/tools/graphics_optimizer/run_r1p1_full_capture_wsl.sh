#!/usr/bin/env bash
# ARM the ORIGINAL ARCADE full R1/P1 sprite capture, then Tighe plays R1/P1 manually.
# Reuses the established arcade MAME layout (see tools/mame/run_rastan_trace_wsl.sh). Captures the full
# PC090OJ object RAM + actor/player blocks via tools/graphics_optimizer/r1p1_full_sprite_capture.lua.
# Coin=5, Start=1 (established). Output -> analysis/graphics_optimizer/round1_phase1_corpus/full_capture/.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MACHINE="rastan"
export FD_OUT="${ROOT}/analysis/graphics_optimizer/round1_phase1_corpus/full_capture"
mkdir -p "${FD_OUT}"

if command -v mame >/dev/null 2>&1; then MAME_BIN="$(command -v mame)"
elif command -v mame64 >/dev/null 2>&1; then MAME_BIN="$(command -v mame64)"
else echo "MAME not found (apt-get install mame mame-tools)" >&2; exit 1; fi

HOMEPATH="${ROOT}/build/mame/home"; mkdir -p "${HOMEPATH}"
echo "ARMED: full R1/P1 sprite capture -> ${FD_OUT}"
echo "Play Round 1 / Phase 1: coin=5, start=1. Trigger the AXE pickup, sword/Flame Sword/Flail,"
echo "the swinging rope, and reach the cave. Close MAME when done to flush."
exec "${MAME_BIN}" "${MACHINE}" \
  -window -skip_gameinfo \
  -rompath "${ROOT}/roms" \
  -homepath "${HOMEPATH}" \
  -autoboot_script "${ROOT}/tools/graphics_optimizer/r1p1_full_sprite_capture.lua" \
  "$@"
